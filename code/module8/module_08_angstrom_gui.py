"""Module 8 Angstrom GUI: send a schedule, watch all six temperatures live, save the raw record.

Upload module_08_angstrom_controller.ino, close Serial Monitor, then run:

    python module_08_angstrom_gui.py --label pilot --mode PI --kp 16 --ki 0.5 \
        --schedule "1800,40,16,100" [--start]

--schedule is "duration_s,Ta_C,Tb_C,period_s" steps separated by ";".
The Arduino runs the setpoint, controller, schedule and safety limits. This program sends
settings and a heartbeat, and saves every valid record unmodified to a NEW CSV in
data/module_08/. EVENT lines go to a matching .events.txt file.
"""
import argparse
from collections import deque
from datetime import datetime
import math
from pathlib import Path
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'code/module5/P1_P-only_control'))
from p_control_gui import QtWidgets, QtCore, pg, serial, find_port, BAUD_RATE
import numpy as np
sys.path.insert(0, str(HERE))
import settling as st

HEADER = ('time_ms,run_state,control_mode,step,Ta_C,Tb_C,period_s,setpoint_C,feedforward_pwm,'
          'TEC_C,T1_C,T2_C,T3_C,T4_C,T5_C,controller_pwm,heating_to_cooling_ratio,signed_pwm')
FIELDS = HEADER.split(',')
LABELS = ['TEC tag T5 (A1)', 'T1 (A5)', 'T2 (A4)', 'T3 (A3)', 'T4 (A2)', 'T6 (A0)']  # physical wire tags
COLORS = ['k', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
RUN_STATES = ('IDLE', 'RUN', 'DONE', 'STOPPED', 'SHUTDOWN', 'SENSOR_FAULT', 'ROD_LIMIT', 'TIMEOUT')
MODES = ('OPEN', 'P', 'PI')
# Same limits as the sketch; the Arduino checks them again.
MIN_PERIOD_S, MAX_SETPOINT_C, MIN_SETPOINT_C, MAX_STEPS = 100.0, 56.0, 10.0, 8
HEARTBEAT_S = 0.5
COMMAND_SPACING_S = 0.15  # Keeps bursts inside the Arduino's 64-byte serial buffer.
MISSING_GAP_S = 2.0       # A record normally arrives every ~0.7 s.


def parse_record(line):
    """Return a dict for a valid record, None for the header/blank lines; raise ValueError otherwise."""
    if not line or line == HEADER:
        return None
    parts = line.split(',')
    if len(parts) != len(FIELDS):
        raise ValueError('wrong field count')
    record = dict(zip(FIELDS, parts))
    try:
        record['time_ms'] = int(parts[0])
        record['step'] = int(parts[3])
        record['signed_pwm'] = int(parts[17])
        for name in FIELDS[4:17]:
            record[name] = float(record[name])
    except ValueError as error:
        raise ValueError('non-numeric field') from error
    if record['time_ms'] < 0 or record['run_state'] not in RUN_STATES or record['control_mode'] not in MODES:
        raise ValueError('unknown state or mode')
    if any(math.isinf(record[name]) for name in FIELDS[4:17]) or abs(record['signed_pwm']) > 255:
        raise ValueError('value out of range')
    if record['run_state'] != 'RUN' and record['signed_pwm'] != 0:
        raise ValueError('nonzero PWM outside a run')
    return record


def parse_schedule(text):
    """'dur,Ta,Tb,period;...' -> list of float tuples."""
    steps = []
    for item in text.split(';'):
        if item.strip():
            values = [float(v) for v in item.split(',')]
            if len(values) != 4:
                raise ValueError(f'Step needs duration,Ta,Tb,period: {item}')
            steps.append(tuple(values))
    return steps


def check_schedule(steps):
    """Return an error message, or None if the schedule is allowed."""
    if not 1 <= len(steps) <= MAX_STEPS:
        return f'Need 1–{MAX_STEPS} steps.'
    for number, (duration, ta, tb, period) in enumerate(steps, 1):
        if duration <= 0 or tb < 0:
            return f'Step {number}: duration must be positive and Tb nonnegative.'
        if period < MIN_PERIOD_S:
            return f'Step {number}: period must be at least {MIN_PERIOD_S:g} s.'
        if ta + tb > MAX_SETPOINT_C or ta - tb < MIN_SETPOINT_C:
            return f'Step {number}: setpoint must stay within {MIN_SETPOINT_C:g}–{MAX_SETPOINT_C:g} °C.'
    return None


class AngstromGUI(QtWidgets.QMainWindow):
    def __init__(self, port=None, label=None):
        super().__init__()
        self.setWindowTitle('Module 8 — Angstrom drive: six-thermistor acquisition')
        self.resize(1250, 950)
        self.ser = None
        self.lock = threading.Lock()  # Heartbeat thread and GUI thread share the port.
        self.buffer = bytearray()
        self.history = deque(maxlen=30000)
        self.commands = deque()
        self.next_command = 0.0
        self.last_record = None
        self.accepted = self.rejected = self.missing = 0
        self.last_rejected = ''
        self.autostart = False
        self.step_key = None      # (step, period) of the step being checked for settling
        self.step_rows = []       # (t, {channel: value}) for that step
        self.cycles_checked = 0
        self.reported_ready = False
        self.build_ui()

        folder = REPO / 'data/module_08'
        folder.mkdir(parents=True, exist_ok=True)
        stem = f'angstrom_raw_{label + "_" if label else ""}{datetime.now():%Y%m%d_%H%M%S}'
        self.log_path = folder / f'{stem}.csv'
        self.log_file = self.log_path.open('x', newline='')  # 'x' never overwrites a run.
        self.log_file.write(HEADER + '\n')
        self.log_file.flush()
        self.events_file = (folder / f'{stem}.events.txt').open('x')
        self.log_label.setText(f'Raw CSV: {self.log_path.relative_to(REPO)}')
        print(f'CSV log: {self.log_path}')

        try:
            name = find_port(port)
            self.ser = serial.Serial(name, BAUD_RATE, timeout=0, write_timeout=0.2)
            self.status.setText(f'{name}: waiting for telemetry; output off')
            self.note_event(f'GUI connected to {name}')
        except (ValueError, OSError, serial.SerialException) as error:
            self.status.setText(str(error))
        self.heartbeat_on = True
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(50)

    # ---------- layout ----------
    def build_ui(self):
        pg.setConfigOptions(background='w', foreground='k')
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        controls = QtWidgets.QGridLayout()
        layout.addLayout(controls)
        self.mode = QtWidgets.QComboBox(); self.mode.addItems(MODES); self.mode.setCurrentText('PI')
        self.kp = QtWidgets.QDoubleSpinBox(); self.kp.setRange(0, 1000); self.kp.setSingleStep(0.5); self.kp.setValue(16)
        self.ki = QtWidgets.QDoubleSpinBox(); self.ki.setDecimals(4); self.ki.setRange(0, 10)
        self.ki.setSingleStep(.01); self.ki.setValue(.5)
        self.ratio = QtWidgets.QDoubleSpinBox(); self.ratio.setDecimals(3); self.ratio.setRange(.1, 10); self.ratio.setValue(2.83)
        self.pwm_limit = QtWidgets.QSpinBox(); self.pwm_limit.setRange(1, 255); self.pwm_limit.setValue(255)
        self.window = QtWidgets.QSpinBox(); self.window.setRange(30, 14400); self.window.setValue(600)
        for col, (label, widget) in enumerate([
                ('Mode', self.mode), ('Kp (PWM/°C)', self.kp), ('Ki (PWM/°C/s)', self.ki),
                ('Cooling ratio r', self.ratio), ('PWM limit', self.pwm_limit), ('Plot window (s)', self.window)]):
            controls.addWidget(QtWidgets.QLabel(label), 0, col)
            controls.addWidget(widget, 1, col)

        self.schedule = QtWidgets.QTableWidget(1, 4)
        self.schedule.setHorizontalHeaderLabels(['Duration (s)', 'Ta (°C)', 'Tb (°C)', 'Period (s)'])
        self.schedule.setMaximumHeight(120)
        self.schedule.horizontalHeader().setStretchLastSection(True)
        self.set_schedule([(1800, 40, 16, 100)])
        layout.addWidget(self.schedule)
        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        self.add_row = QtWidgets.QPushButton('Add step'); self.remove_row = QtWidgets.QPushButton('Remove step')
        self.start_button = QtWidgets.QPushButton('Send schedule and START'); self.start_button.setMinimumHeight(36)
        self.stop_button = QtWidgets.QPushButton('STOP / PWM 0'); self.stop_button.setMinimumHeight(36)
        # Hold: a step only ends when the operator presses Next (after the settling test passes).
        self.hold = QtWidgets.QCheckBox('Hold period until Next'); self.hold.setChecked(False)
        self.next_button = QtWidgets.QPushButton('Next period →'); self.next_button.setMinimumHeight(36)
        for button in (self.add_row, self.remove_row, self.start_button, self.hold, self.next_button, self.stop_button):
            buttons.addWidget(button)

        self.status = QtWidgets.QLabel('Waiting for connection'); self.status.setWordWrap(True)
        self.status.setStyleSheet('font-size: 14px; font-weight: bold;')
        self.readout = QtWidgets.QLabel('State: — | Mode: — | Setpoint: — | PWM: 0')
        self.counts = QtWidgets.QLabel('Accepted lines: 0 | Rejected lines: 0 | Missing-record gaps: 0')
        self.log_label = QtWidgets.QLabel()
        self.settle_label = QtWidgets.QLabel(
            f'Settling test (per cycle): |Δmean| ≤ {st.MEAN_TOL_C} °C, |ΔB|/B ≤ {100*st.AMP_TOL:g}%, '
            f'|Δφ| ≤ {st.PHASE_TOL_RAD} rad; settled after {st.SETTLE_PASSES} passes, then keep {st.RETAIN_CYCLES} cycles')
        self.settle_label.setWordWrap(True)
        self.settle_label.setStyleSheet('font-size: 13px; font-weight: bold;')
        for widget in (self.status, self.readout, self.counts, self.settle_label, self.log_label):
            layout.addWidget(widget)

        numbers = QtWidgets.QGridLayout()
        layout.addLayout(numbers)
        self.value_labels, self.show_boxes = [], []
        for col, (name, color) in enumerate(zip(LABELS, COLORS)):
            box = QtWidgets.QCheckBox(name); box.setChecked(True)
            box.setStyleSheet(f'color: {color}; font-weight: bold;')
            value = QtWidgets.QLabel('—')
            value.setStyleSheet(f'color: {color}; font-size: 22px; font-weight: bold;')
            numbers.addWidget(box, 0, col); numbers.addWidget(value, 1, col)
            self.show_boxes.append(box); self.value_labels.append(value)

        self.plots, self.curves = [], {}
        temp_plot = pg.PlotWidget(title='Six raw temperatures vs. Arduino time')
        temp_plot.setLabel('left', 'Temperature', units='°C')
        temp_plot.addLegend(offset=(10, 10))
        for key, name, color in zip(FIELDS[9:15], LABELS, COLORS):
            width = 4 if key == 'TEC_C' else 2
            self.curves[key] = temp_plot.plot(pen=pg.mkPen(color, width=width), name=name, connect='finite')
        self.curves['setpoint_C'] = temp_plot.plot(
            pen=pg.mkPen('#7f7f7f', width=2, style=QtCore.Qt.PenStyle.DashLine), name='Setpoint', connect='finite')
        pwm_plot = pg.PlotWidget(title='Applied signed PWM (+HEAT / −COOL)')
        pwm_plot.setLabel('left', 'PWM', units='counts')
        self.curves['signed_pwm'] = pwm_plot.plot(pen=pg.mkPen('r', width=2))
        for plot, stretch in ((temp_plot, 3), (pwm_plot, 1)):
            plot.setLabel('bottom', 'Arduino time', units='s')
            plot.showGrid(x=True, y=True)
            layout.addWidget(plot, stretch)
            self.plots.append(plot)

        for key, box in zip(FIELDS[9:15], self.show_boxes):
            box.toggled.connect(self.curves[key].setVisible)
        self.add_row.clicked.connect(lambda: self.schedule.insertRow(self.schedule.rowCount()))
        self.remove_row.clicked.connect(lambda: self.schedule.removeRow(self.schedule.rowCount() - 1))
        self.start_button.clicked.connect(self.start_run)
        self.stop_button.clicked.connect(self.stop_run)
        self.hold.toggled.connect(self.send_hold)
        self.next_button.clicked.connect(self.next_period)

    def set_schedule(self, steps):
        self.schedule.setRowCount(len(steps))
        for row, step in enumerate(steps):
            for col, value in enumerate(step):
                self.schedule.setItem(row, col, QtWidgets.QTableWidgetItem(f'{value:g}'))

    def read_schedule(self):
        steps = []
        for row in range(self.schedule.rowCount()):
            items = [self.schedule.item(row, col) for col in range(4)]
            steps.append(tuple(float(item.text()) if item else math.nan for item in items))
        return steps

    # ---------- commands ----------
    def write(self, text):
        if self.ser and self.ser.is_open:
            with self.lock:
                self.ser.write((text + '\n').encode('ascii'))

    def heartbeat(self):
        # A separate thread, so a brief pause of the window (e.g. macOS App Nap) does not
        # starve the Arduino's 2 s command timeout. If this program dies, the TEC still stops.
        while self.heartbeat_on:
            try:
                self.write('PING')
            except (OSError, serial.SerialException):
                pass
            time.sleep(HEARTBEAT_S)

    def start_run(self):
        try:
            steps = self.read_schedule()
        except ValueError:
            self.status.setText('Schedule cells must be numbers.'); return
        problem = 'Schedule has an empty cell.' if any(math.isnan(v) for s in steps for v in s) else check_schedule(steps)
        if problem:
            self.status.setText(problem); return
        if self.last_record is None:
            self.status.setText('Need telemetry from the Module 8 sketch before starting.'); return
        if self.last_record['run_state'] == 'RUN':
            self.status.setText('Already running. Press STOP first.'); return
        self.commands.clear()
        self.commands.extend([f'MODE {self.mode.currentText()}',
                              f'GAINS {self.kp.value():.3f} {self.ki.value():.4f}',
                              f'RATIO {self.ratio.value():.3f}', f'LIMIT {self.pwm_limit.value()}', 'CLEAR'])
        self.commands.extend('STEP {:g} {:g} {:g} {:g}'.format(*step) for step in steps)
        self.commands.append('HOLD ON' if self.hold.isChecked() else 'HOLD OFF')
        self.commands.append('START')
        self.note_event(f'GUI start request: mode {self.mode.currentText()}, Kp {self.kp.value():g}, '
                        f'Ki {self.ki.value():g}, r {self.ratio.value():g}, schedule {steps}')
        self.status.setText('Sending schedule…')

    def stop_run(self):
        self.commands.clear()  # STOP goes straight out, ahead of anything queued.
        try:
            self.write('STOP')
        except (OSError, serial.SerialException) as error:
            self.status.setText(f'Cannot send STOP: {error}')
        self.note_event('GUI STOP pressed')

    def send_hold(self, on):
        try:
            self.write('HOLD ON' if on else 'HOLD OFF')
        except (OSError, serial.SerialException) as error:
            self.status.setText(f'Cannot send HOLD: {error}')
        self.note_event(f'GUI hold {"ON" if on else "OFF"}')

    def next_period(self):
        try:
            self.write('NEXT')
        except (OSError, serial.SerialException) as error:
            self.status.setText(f'Cannot send NEXT: {error}')
        self.note_event('GUI Next period pressed')

    def check_settling(self, record):
        """Run the settling test after each complete cycle of the active step."""
        if record['run_state'] != 'RUN':
            return
        key = (record['step'], record['period_s'])
        if key != self.step_key:
            self.step_key, self.step_rows, self.cycles_checked, self.reported_ready = key, [], 0, False
        self.step_rows.append((record['time_ms']/1000, {c: record[c] for c in st.CHANNELS + ['T5_C']}))
        period = record['period_s']
        t = np.array([row[0] for row in self.step_rows])
        complete = int((t[-1] - t[0] + 1.0) // period)
        if complete == self.cycles_checked or complete < 2:
            if complete < 2:
                self.settle_label.setText(f'Step {key[0]} ({period:g} s): waiting for 2 complete cycles '
                                          f'({t[-1] - t[0]:.0f}/{2*period:g} s)')
            return
        self.cycles_checked = complete
        temps = {c: np.array([row[1][c] for row in self.step_rows]) for c in st.CHANNELS + ['T5_C']}
        cycles = st.cycle_fits(t, temps, t[0], period, st.CHANNELS + ['T5_C'])
        channels = st.CHANNELS + (['T5_C'] if st.measurable(cycles) else [])
        results, settled_at, retained = st.settling_status(cycles, channels)
        i, passed, worst = results[-1]
        text = (f'Step {key[0]} ({period:g} s), cycle {i + 1}: Δmean {worst["mean"]:.3f} °C, '
                f'ΔB/B {100*worst["amp"]:.1f}%, Δφ {worst["phase"]:.3f} rad → {"pass" if passed else "FAIL"} | ')
        if settled_at is None:
            text += 'NOT settled yet'
            color = '#a34b00'
        elif len(retained) < st.RETAIN_CYCLES:
            text += f'settled; retained {len(retained)}/{st.RETAIN_CYCLES} cycles'
            color = '#1565c0'
        else:
            first, last = cycles[retained[0]], cycles[retained[-1]]
            text += f'READY: {st.RETAIN_CYCLES} settled cycles, t = {first["start"]:.0f}–{last["end"]:.0f} s. Press Next period.'
            color = 'green'
            if not self.reported_ready:
                self.reported_ready = True
                self.note_event(f'GUI settled: step {key[0]} period {period:g} s retained t = '
                                f'{first["start"]:.1f}-{last["end"]:.1f} s, channels {",".join(channels)}')
        self.settle_label.setText(text)
        self.settle_label.setStyleSheet(f'font-size: 13px; font-weight: bold; color: {color};')

    def note_event(self, text):
        self.events_file.write(f'{datetime.now().isoformat(timespec="seconds")} {text}\n')
        self.events_file.flush()

    # ---------- serial ----------
    def update_loop(self):
        now = time.monotonic()
        if not self.ser or not self.ser.is_open:
            return
        try:
            with self.lock:
                self.buffer.extend(self.ser.read(min(self.ser.in_waiting, 8192)))
            if self.commands and now >= self.next_command:
                self.write(self.commands.popleft())
                self.next_command = now + COMMAND_SPACING_S
            newest = None
            while b'\n' in self.buffer:
                line, _, rest = self.buffer.partition(b'\n')
                self.buffer = bytearray(rest)
                text = line.decode('ascii', errors='replace').strip()
                if text.startswith('EVENT,'):
                    self.handle_event(text)
                    continue
                try:
                    record = parse_record(text)
                except ValueError as error:
                    # Malformed lines are counted and skipped; they never stop the program.
                    self.rejected += 1
                    self.last_rejected = f'{error}: {text[:70]!r}'
                    continue
                if record is None:
                    continue
                self.accepted += 1
                self.log_file.write(text + '\n')  # Unmodified, as received.
                self.log_file.flush()
                if self.last_record and (record['time_ms'] - self.last_record['time_ms'])/1000 > MISSING_GAP_S:
                    self.missing += 1
                self.last_record = newest = record
                self.check_settling(record)
            self.counts.setText(f'Accepted lines: {self.accepted} | Rejected lines: {self.rejected} | '
                                f'Missing-record gaps: {self.missing}'
                                + (f' | last rejected: {self.last_rejected}' if self.rejected else ''))
            if newest:
                self.show_record(newest)
            if self.autostart and self.accepted >= 5:
                self.autostart = False
                self.start_run()
        except (OSError, serial.SerialException) as error:
            self.status.setText(f'Serial connection failed: {error}. The Arduino stops the TEC within 2 s.')
            self.ser.close()

    def handle_event(self, text):
        self.note_event(text)
        if ',REJECT,' in text:
            self.commands.clear()  # Never start from a partly loaded schedule.
            self.status.setText(f'Arduino rejected a command: {text}')
        elif ',END,' in text or ',STEP,' in text or ',START,' in text:
            self.status.setText(text)

    def show_record(self, record):
        state = record['run_state']
        running = state == 'RUN'
        for widget in (self.mode, self.kp, self.ki, self.ratio, self.pwm_limit, self.schedule, self.start_button):
            widget.setEnabled(not running)
        color = 'green' if running else ('#b00020' if state in ('SHUTDOWN', 'SENSOR_FAULT', 'ROD_LIMIT', 'TIMEOUT') else '#a34b00')
        self.readout.setStyleSheet(f'color: {color}; font-weight: bold;')
        self.readout.setText(f'State: {state} | Mode: {record["control_mode"]} | Step: {record["step"]} | '
                             f'Setpoint: {record["setpoint_C"]:.2f} °C | PWM: {record["signed_pwm"]:+d} | '
                             f't = {record["time_ms"] / 1000:.1f} s')
        temps = [record[key] for key in FIELDS[9:15]]
        for label, value in zip(self.value_labels, temps):
            label.setText(f'{value:.2f} °C' if math.isfinite(value) else 'FAULT (nan)')
        t = record['time_ms'] / 1000
        self.history.append((t, temps, record['setpoint_C'], record['signed_pwm']))
        window = self.window.value()
        while self.history and t - self.history[0][0] > window:
            self.history.popleft()
        times = [row[0] for row in self.history]
        for index, key in enumerate(FIELDS[9:15]):
            self.curves[key].setData(times, [row[1][index] for row in self.history])
        self.curves['setpoint_C'].setData(times, [row[2] for row in self.history])
        self.curves['signed_pwm'].setData(times, [row[3] for row in self.history])
        for plot in self.plots:
            plot.setXRange(max(0, t - window), max(window, t), padding=0)

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.write('STOP')
        except (OSError, serial.SerialException):
            pass
        self.heartbeat_on = False
        if self.ser:
            with self.lock:
                self.ser.close()
        self.log_file.close()
        self.events_file.close()
        event.accept()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', help='Explicit serial device; otherwise auto-detect USB')
    parser.add_argument('--label', help='Optional tag in the CSV filename, e.g. pilot')
    parser.add_argument('--mode', choices=MODES, help='Preset control mode')
    parser.add_argument('--kp', type=float, help='Preset Kp (PWM/°C)')
    parser.add_argument('--ki', type=float, help='Preset Ki (PWM/°C/s)')
    parser.add_argument('--ratio', type=float, help='Preset cooling ratio r = chi_h/chi_c')
    parser.add_argument('--schedule', help='Steps "duration,Ta,Tb,period;..."')
    parser.add_argument('--window', type=int, help='Preset plot window (s)')
    parser.add_argument('--start', action='store_true', help='Send the schedule and START once telemetry is up')
    parser.add_argument('--hold', action='store_true', help='Hold each period until Next is pressed')
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    gui = AngstromGUI(args.port, args.label)
    if args.mode: gui.mode.setCurrentText(args.mode)
    if args.kp is not None: gui.kp.setValue(args.kp)
    if args.ki is not None: gui.ki.setValue(args.ki)
    if args.ratio is not None: gui.ratio.setValue(args.ratio)
    if args.window: gui.window.setValue(args.window)
    if args.schedule: gui.set_schedule(parse_schedule(args.schedule))
    if args.hold:
        gui.hold.blockSignals(True); gui.hold.setChecked(True); gui.hold.blockSignals(False)
    gui.autostart = args.start
    gui.show()
    sys.exit(app.exec())
