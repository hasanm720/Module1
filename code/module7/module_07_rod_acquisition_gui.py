"""Module 7 six-thermistor acquisition GUI with the Module 6 P / PI TEC controls.

Copy of the Module 6 GUI (the Module 6 file is unchanged). Upload
module_07_rod_controller.ino, close Serial Monitor, then run:

    python module_07_rod_acquisition_gui.py [--port /dev/cu.usbmodem...] [--label common_bath]

Only the TEC thermistor (A1) enters the PI law. Rod channels are measured and logged;
the sketch reports them in physical order T1, T2, T3, T4, T6 (pins A5, A4, A3, A2, A0).
Every accepted DATA record is written, raw and uncalibrated, to a NEW CSV in
data/module_07/ whether or not control is running.
"""
import argparse
from collections import deque
import csv
from dataclasses import dataclass
from datetime import datetime
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'code/module5/P1_P-only_control'))
sys.path.insert(0, str(REPO / 'code/module6/Part_I/P7_experimental_goldilocks'))
from p_control_gui import PControlGUI, QtWidgets, QtCore, pg, serial, find_port, BAUD_RATE, STALE_SECONDS
from pi_logic import PIController

HEADER = 'DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,setpoint_C,safety'
FIELDS = HEADER.split(',')[1:]
CHANNELS = ['tec_C', 'rod1_C', 'rod2_C', 'rod3_C', 'rod4_C', 'rod5_C']
LABELS = ['TEC tag T5 (A1)', 'T1 (A5)', 'T2 (A4)', 'T3 (A3)', 'T4 (A2)', 'T6 (A0)']  # physical wire tags; CSV column rod5_C = tag T6
COLORS = ['k', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
SAFETY_STATES = ('OK', 'SHUTDOWN', 'SENSOR_FAULT', 'TIMEOUT')
LIMIT_C = 60.0  # TEMPERATURE_LIMIT_C in the sketch; not transmitted in DATA.
SPREAD_PASS_C = 1.0  # Common-bath default criterion: T_max - T_min < 1 °C.
MAX_DT_S = 5.0  # Largest Arduino-time step between handled records before control stops.


@dataclass(frozen=True)
class RodSample:
    time: float
    temperatures: tuple  # Six raw °C values, TEC first; nan marks an invalid channel.
    signed_pwm: int
    heat_cool: int
    setpoint: float
    safety: str
    limit: float = LIMIT_C

    # Names used by the Module 5/6 base class.
    @property
    def temperature(self):
        return self.temperatures[0]

    @property
    def pwm(self):
        return abs(self.signed_pwm)

    @property
    def direction(self):
        return 'HEAT' if self.heat_cool == 1 else 'COOL'


def parse_rod_line(line):
    """Return a RodSample, None for the header/blank lines; raise ValueError otherwise."""
    if not line or line == HEADER:
        return None
    parts = line.split(',')
    if parts[0] != 'DATA' or len(parts) != len(FIELDS) + 1:
        raise ValueError('not a complete DATA record')
    try:
        t = float(parts[1])
        temps = tuple(float(v) for v in parts[2:8])
        signed_pwm, heat_cool = int(parts[8]), int(parts[9])
        setpoint = float(parts[10])
    except ValueError as error:
        raise ValueError('non-numeric field') from error
    safety = parts[11]
    if not math.isfinite(t) or t < 0:
        raise ValueError('bad Arduino time')
    if any(math.isinf(v) for v in temps):
        raise ValueError('infinite temperature')
    if heat_cool not in (1, -1) or not -255 <= signed_pwm <= 255 or signed_pwm * heat_cool < 0:
        raise ValueError('inconsistent PWM / direction')
    if safety not in SAFETY_STATES:
        raise ValueError('unknown safety state')
    if safety == 'OK' and not math.isfinite(temps[0]):
        raise ValueError('OK reported without a valid TEC temperature')
    if safety != 'OK' and signed_pwm != 0:
        raise ValueError('nonzero PWM during shutdown')
    return RodSample(t, temps, signed_pwm, heat_cool, setpoint, safety)


def spread(temperatures):
    """Full spread T_max - T_min over the valid channels, and how many were valid."""
    valid = [v for v in temperatures if math.isfinite(v)]
    return (max(valid) - min(valid) if valid else math.nan), len(valid)


class RodAcquisitionGUI(PControlGUI):
    def __init__(self, port=None, label=None):
        # Do not call PControlGUI.__init__: it would open a Module 5 log.
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle('Module 7 — Six-thermistor rod acquisition / P-PI TEC control')
        self.resize(1250, 950)
        self.ser = None
        self.enabled = False
        self.stop_reason = 'Control has not been started'
        self.sample = None
        self.last_received = None
        self.buffer = bytearray()
        self.history = deque(maxlen=20000)
        self.controller = PIController()
        self.previous_time = None
        self.accepted = self.rejected = 0
        self.last_rejected = ''
        self.build_ui()

        folder = REPO / 'data/module_07'
        folder.mkdir(parents=True, exist_ok=True)
        name = f'rod_raw_{label + "_" if label else ""}{datetime.now():%Y%m%d_%H%M%S}.csv'
        self.log_path = folder / name
        self.log_file = self.log_path.open('x', newline='')  # 'x' never overwrites a run.
        self.writer = csv.writer(self.log_file)
        self.writer.writerow(FIELDS)
        self.log_file.flush()
        self.log_label.setText(f'Raw CSV: {self.log_path.relative_to(REPO)}')
        print(f'CSV log: {self.log_path}')

        try:
            name = find_port(port)
            self.ser = serial.Serial(name, BAUD_RATE, timeout=0, write_timeout=0.2)
            self.status.setText(f'{name}: waiting for telemetry; output disabled')
        except (ValueError, OSError, serial.SerialException) as error:
            self.status.setText(str(error))
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(50)

    # ---------- layout ----------
    def build_ui(self):
        pg.setConfigOptions(background='w', foreground='k')
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Module 6 controller panel (Manual mode removed, as in Module 6 Goldilocks runs).
        controls = QtWidgets.QGridLayout()
        layout.addLayout(controls)
        self.mode = QtWidgets.QComboBox(); self.mode.addItems(['P-only', 'PI'])
        self.setpoint = QtWidgets.QDoubleSpinBox(); self.setpoint.setRange(10, 45); self.setpoint.setValue(32)
        self.kp = QtWidgets.QDoubleSpinBox(); self.kp.setRange(0, 1000); self.kp.setSingleStep(0.1); self.kp.setValue(1.0)
        self.ki = QtWidgets.QDoubleSpinBox(); self.ki.setDecimals(4); self.ki.setRange(0, 10)
        self.ki.setSingleStep(.01); self.ki.setValue(.02)
        self.pwm_limit = QtWidgets.QSpinBox(); self.pwm_limit.setRange(1, 255); self.pwm_limit.setValue(255)
        self.window = QtWidgets.QSpinBox(); self.window.setRange(30, 7200); self.window.setValue(60)
        for col, (label, widget) in enumerate([
                ('Mode', self.mode), ('Setpoint (°C)', self.setpoint), ('Kp (PWM/°C)', self.kp),
                ('Ki (PWM/°C/s)', self.ki), ('PWM limit', self.pwm_limit), ('Plot window (s)', self.window)]):
            controls.addWidget(QtWidgets.QLabel(label), 0, col)
            controls.addWidget(widget, 1, col)
        self.start_button = QtWidgets.QPushButton('Start control'); self.start_button.setMinimumHeight(36)
        self.stop_button = QtWidgets.QPushButton('Stop / PWM 0 / Zero integral')
        controls.addWidget(self.start_button, 2, 0, 1, 3)
        controls.addWidget(self.stop_button, 2, 3, 1, 3)

        self.status = QtWidgets.QLabel('Waiting for connection'); self.status.setWordWrap(True)
        self.status.setStyleSheet('font-size: 14px; font-weight: bold;')
        self.output_notice = QtWidgets.QLabel(); self.output_notice.setWordWrap(True)
        self.readout = QtWidgets.QLabel('TEC: — | Error: — | PWM: 0')
        self.counts = QtWidgets.QLabel('Accepted lines: 0 | Rejected lines: 0')
        self.log_label = QtWidgets.QLabel()
        for widget in (self.status, self.output_notice, self.readout, self.counts, self.log_label):
            layout.addWidget(widget)

        # Live numerical readings for all six channels, plus the common-bath spread.
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
        self.spread_label = QtWidgets.QLabel('Spread —')
        self.spread_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        numbers.addWidget(QtWidgets.QLabel('T_max − T_min (6 ch)'), 0, 6)
        numbers.addWidget(self.spread_label, 1, 6)

        # Plots against Arduino time: six temperatures (TEC thicker), PWM, error.
        self.plots, self.curves = [], {}
        temp_plot = pg.PlotWidget(title='Six raw temperatures vs. Arduino time')
        temp_plot.setLabel('left', 'Temperature', units='°C')
        legend = temp_plot.addLegend(offset=(10, 10))
        for key, name, color in zip(CHANNELS, LABELS, COLORS):
            width = 5 if key == 'tec_C' else 2
            self.curves[key] = temp_plot.plot(pen=pg.mkPen(color, width=width), name=name, connect='finite')
        self.curves['setpoint'] = temp_plot.plot(
            pen=pg.mkPen('#7f7f7f', width=2, style=QtCore.Qt.PenStyle.DashLine), name='Setpoint (GUI)')
        pwm_plot = pg.PlotWidget(title='Signed PWM (+HEAT / −COOL)')
        pwm_plot.setLabel('left', 'PWM', units='counts'); pwm_plot.addLegend(offset=(10, 10))
        self.curves['reported_pwm'] = pwm_plot.plot(pen=pg.mkPen('r', width=3), name='Reported by Arduino')
        self.curves['command_pwm'] = pwm_plot.plot(
            pen=pg.mkPen('#7b2cbf', width=2, style=QtCore.Qt.PenStyle.DashLine), name='Next command')
        error_plot = pg.PlotWidget(title='Error: setpoint − TEC temperature')
        error_plot.setLabel('left', 'Error', units='°C')
        self.curves['error'] = error_plot.plot(pen=pg.mkPen('#c45100', width=3), connect='finite')
        for plot, stretch in ((temp_plot, 3), (pwm_plot, 1), (error_plot, 1)):
            plot.setLabel('bottom', 'Arduino time', units='s')
            plot.showGrid(x=True, y=True)
            layout.addWidget(plot, stretch)
            self.plots.append(plot)

        for key, box in zip(CHANNELS, self.show_boxes):
            box.toggled.connect(self.curves[key].setVisible)
        self.start_button.clicked.connect(self.start_control)
        self.stop_button.clicked.connect(self.zero_integral)
        self.mode.currentTextChanged.connect(self.mode_changed)
        for widget in (self.kp, self.ki, self.pwm_limit):
            widget.valueChanged.connect(lambda _: self.stop_control('Settings changed — stopped'))
        self.setpoint.valueChanged.connect(self.target_changed)
        self.mode_changed()

    # ---------- control (unchanged Module 6 behaviour) ----------
    def mode_changed(self):
        self.stop_control('Stopped — press Start to enable the selected mode')
        self.ki.setEnabled(self.mode.currentText() == 'PI')
        self.controller.reset(); self.previous_time = None

    def target_changed(self):
        if self.sample and self.setpoint.value() >= self.sample.limit:
            self.stop_control('Setpoint must be below Arduino shutdown temperature')

    def zero_integral(self):
        self.stop_control('Stopped — output off, integral reset')
        self.controller.reset(); self.previous_time = None

    def start_control(self):
        if not self.sample or self.setpoint.value() >= self.sample.limit:
            self.status.setText('Need safe telemetry and a setpoint below the shutdown temperature'); return
        self.zero_integral()
        super().start_control()
        if self.enabled:
            self.previous_time = self.sample.time

    # ---------- serial ----------
    def update_loop(self):
        now = time.monotonic()
        if not self.ser or not self.ser.is_open:
            return
        try:
            self.buffer.extend(self.ser.read(min(self.ser.in_waiting, 8192)))
            if len(self.buffer) > 8192:
                self.buffer.clear()
                self.stop_control('Serial backlog or invalid framing — stopped')
                return
            newest = None
            while b'\n' in self.buffer:
                line, _, rest = self.buffer.partition(b'\n')
                self.buffer = bytearray(rest)
                text = line.decode('ascii', errors='replace').strip()
                try:
                    sample = parse_rod_line(text)
                except ValueError as error:
                    # Malformed lines are counted and skipped; they never stop the program.
                    self.rejected += 1
                    self.last_rejected = f'{error}: {text[:70]!r}'
                    continue
                if sample is None:
                    continue
                self.accepted += 1
                self.record(sample)
                newest = sample
            self.counts.setText(f'Accepted lines: {self.accepted} | Rejected lines: {self.rejected}'
                                + (f' | last rejected: {self.last_rejected}' if self.rejected else ''))
            # Control acts on the newest measurement only (never replays a stale burst).
            if newest:
                self.handle_sample(newest, now)
            # Stale only if nothing new arrived. Checked after reading, so a brief GUI
            # pause (e.g. macOS App Nap) with data waiting in the buffer is not a timeout.
            # The Arduino's own 2 s command timeout still zeroes the TEC if the GUI freezes.
            elif self.last_received is not None and now - self.last_received > STALE_SECONDS:
                if self.enabled:
                    self.stop_control('Telemetry timed out — stopped; press Start after recovery')
                else:
                    self.status.setText('No fresh telemetry — check Arduino connection')
        except (OSError, serial.SerialException) as error:
            self.stop_control(f'Serial connection failed: {error}')
            self.ser.close()

    def record(self, sample):
        """Write one accepted record, raw, to the CSV and flush it."""
        setpoint = self.setpoint.value() if self.enabled else math.nan
        try:
            self.writer.writerow([sample.time, *sample.temperatures, sample.signed_pwm,
                                  sample.heat_cool, setpoint, sample.safety])
            self.log_file.flush()
        except OSError as error:
            self.stop_control(f'CSV logging failed: {error}')

    def handle_sample(self, sample, now):
        dt = 0 if self.previous_time is None else sample.time - self.previous_time
        # dt <= 0 means the Arduino restarted. Up to MAX_DT_S allows skipped buffered records.
        if self.previous_time is not None and not 0 < dt <= MAX_DT_S:
            self.stop_control('Invalid sample interval (Arduino restarted?) — stopped')
        self.previous_time = sample.time
        self.sample, self.last_received = sample, now
        if sample.safety != 'OK':
            self.stop_control(f'Arduino {sample.safety}')
        # --start: begin control once, after the window has settled (5 records, ~3 s),
        # so a slow first draw cannot trip the stale-telemetry stop.
        if (getattr(self, 'autostart', False) and self.accepted >= 5
                and sample.safety == 'OK' and not self.enabled):
            self.autostart = False
            self.start_control()
        target, kp = self.setpoint.value(), self.kp.value()
        ki = self.ki.value() if self.mode.currentText() == 'PI' else 0
        error, p, i, requested, applied = math.nan, 0, 0, 0, 0
        if self.enabled:
            try:
                error, p, i, requested, applied = self.controller.update(
                    target, sample.temperature, kp, ki, dt, self.pwm_limit.value(), True)
            except ValueError as exc:
                self.stop_control(str(exc))
        if not self.enabled:
            applied = 0
        try:
            self.send('HEAT' if applied >= 0 else 'COOL', abs(applied))
        except (OSError, serial.SerialException) as exc:
            self.status.setText(f'Cannot send command: {exc}')
        self.update_output_notice()
        if self.enabled:
            self.status.setText(f'Running {self.mode.currentText()} | Arduino: {sample.safety}')
        self.readout.setText(f'TEC {sample.temperature:.2f} °C | e {error:+.2f} °C | P {p:+.2f} | '
                             f'I {i:+.2f} | request {requested:+.2f} | applied {applied:+d} | '
                             f'reported {sample.signed_pwm:+d} PWM ({sample.direction}) | '
                             f'Arduino {sample.safety} | t = {sample.time:.2f} s')

        for label, value in zip(self.value_labels, sample.temperatures):
            label.setText(f'{value:.2f} °C' if math.isfinite(value) else 'FAULT (nan)')
        width, n_valid = spread(sample.temperatures)
        passed = n_valid == 6 and width < SPREAD_PASS_C
        self.spread_label.setText(f'{width:.2f} °C' + ('' if n_valid == 6 else f' ({n_valid}/6 valid)'))
        self.spread_label.setStyleSheet('font-size: 18px; font-weight: bold; color: '
                                        + ('green;' if passed else '#b00020;'))

        self.history.append((sample.time, sample.temperatures,
                             target if self.enabled else math.nan, error, sample.signed_pwm, applied))
        window = self.window.value()
        while self.history and sample.time - self.history[0][0] > window:
            self.history.popleft()
        times = [row[0] for row in self.history]
        for index, key in enumerate(CHANNELS):
            self.curves[key].setData(times, [row[1][index] for row in self.history])
        for key, index in (('setpoint', 2), ('error', 3), ('reported_pwm', 4), ('command_pwm', 5)):
            self.curves[key].setData(times, [row[index] for row in self.history])
        for plot in self.plots:
            plot.setXRange(max(0, sample.time - window), max(window, sample.time), padding=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--port', help='Explicit serial device; otherwise auto-detect USB')
    parser.add_argument('--label', help='Optional tag in the CSV filename, e.g. common_bath')
    parser.add_argument('--mode', choices=['P-only', 'PI'], help='Preset controller mode')
    parser.add_argument('--setpoint', type=float, help='Preset setpoint (°C, 10–45)')
    parser.add_argument('--kp', type=float, help='Preset Kp (PWM/°C)')
    parser.add_argument('--ki', type=float, help='Preset Ki (PWM/°C/s)')
    parser.add_argument('--window', type=int, help='Preset plot window (s)')
    parser.add_argument('--start', action='store_true', help='Start control on the first safe measurement')
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    gui = RodAcquisitionGUI(args.port, args.label)
    # Mode first: changing it resets the controller. Every change leaves output stopped.
    if args.mode: gui.mode.setCurrentText(args.mode)
    if args.setpoint is not None: gui.setpoint.setValue(args.setpoint)
    if args.kp is not None: gui.kp.setValue(args.kp)
    if args.ki is not None: gui.ki.setValue(args.ki)
    if args.window: gui.window.setValue(args.window)
    gui.autostart = args.start
    gui.show()
    sys.exit(app.exec())
