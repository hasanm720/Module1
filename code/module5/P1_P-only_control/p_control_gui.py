"""Module 5 P-only GUI. Upload the accompanying sketch, then run this file.

Dependencies: pyserial, PySide6, pyqtgraph. Optional: --port /dev/cu.usbmodem...
The Arduino averages 1000 ADC readings before converting to temperature;
Python computes u = Kp*(setpoint-temperature) once per fresh measurement.
"""
import argparse
import csv
from collections import deque
from datetime import datetime
import math
from pathlib import Path
import sys
import time

import serial
from serial.tools import list_ports
from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg

from control_logic import command_bytes, p_command, parse_sample

SERIAL_PORT = None  # Override here, or pass --port; otherwise auto-detect USB.
BAUD_RATE = 115200  # Must match the Module 5 sketch.
STALE_SECONDS = 2.0
WINDOW_SECONDS = 60  # Match the Module 4 rolling display.


def find_port(explicit=None):
    if explicit:
        return explicit
    ports = list(list_ports.comports())
    candidates = [p.device for p in ports if p.vid is not None or any(
        word in f'{p.device} {p.description}'.lower()
        for word in ('arduino', 'usbmodem', 'usbserial', 'ch340'))]
    if len(candidates) == 1:
        return candidates[0]
    found = ', '.join(p.device for p in ports) or 'none'
    raise ValueError(f'Cannot identify one Arduino. Ports: {found}. Use --port PORT.')


class PControlGUI(QtWidgets.QMainWindow):
    def __init__(self, port=None):
        super().__init__()
        self.setWindowTitle('Module 5 — Manual / P-only TEC control')
        self.resize(1000, 900)
        self.ser = None
        self.enabled = False
        self.stop_reason = 'Control has not been started'
        self.sample = None
        self.last_received = None
        self.started = time.monotonic()
        self.buffer = bytearray()
        self.history = deque(maxlen=2000)
        self.build_ui()
        log_dir = Path(__file__).resolve().parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        self.log_path = log_dir / f'p_control_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
        self.log_file = self.log_path.open('w', newline='')
        self.writer = csv.writer(self.log_file)
        self.writer.writerow(['elapsed_s', 'arduino_s', 'temperature_C', 'setpoint_C',
                              'kp_pwm_per_C', 'error_C', 'u_raw', 'command_pwm',
                              'command_direction', 'reported_pwm', 'reported_direction',
                              'mode', 'enabled', 'safety', 'limit_C', 'pwm9', 'pwm10'])
        try:
            name = find_port(port or SERIAL_PORT)
            self.ser = serial.Serial(name, BAUD_RATE, timeout=0, write_timeout=0.2)
            self.status.setText(f'{name}: waiting for telemetry; output disabled')
        except (ValueError, OSError, serial.SerialException) as error:
            self.status.setText(str(error))
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(50)
        print(f'CSV log: {self.log_path}')

    def build_ui(self):
        pg.setConfigOptions(background='w', foreground='k')
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        controls = QtWidgets.QGridLayout()
        layout.addLayout(controls)
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(['P-only', 'Manual'])
        self.setpoint = QtWidgets.QDoubleSpinBox()
        self.setpoint.setRange(10, 45)
        self.setpoint.setValue(32)
        self.kp = QtWidgets.QDoubleSpinBox()
        self.kp.setRange(0, 100)
        self.kp.setSingleStep(0.1)
        self.kp.setValue(1.0)
        self.manual_pwm = QtWidgets.QSpinBox()
        self.manual_pwm.setRange(0, 255)
        self.manual_direction = QtWidgets.QComboBox()
        self.manual_direction.addItems(['HEAT', 'COOL'])
        for col, (label, widget) in enumerate([
                ('Mode', self.mode), ('Setpoint (°C)', self.setpoint),
                ('Kp (PWM/°C)', self.kp), ('Manual PWM', self.manual_pwm),
                ('Manual direction', self.manual_direction)]):
            controls.addWidget(QtWidgets.QLabel(label), 0, col)
            controls.addWidget(widget, 1, col)
        self.start_button = QtWidgets.QPushButton('Start P-only control')
        self.start_button.setMinimumHeight(36)
        self.stop_button = QtWidgets.QPushButton('Stop / PWM 0')
        controls.addWidget(self.start_button, 2, 0, 1, 2)
        controls.addWidget(self.stop_button, 2, 2, 1, 3)
        self.status = QtWidgets.QLabel('Waiting for connection')
        self.status.setWordWrap(True)
        self.status.setStyleSheet('font-size: 14px; font-weight: bold;')
        self.output_notice = QtWidgets.QLabel(
            'OUTPUT OFF — changing the setpoint does not start control; click Start P-only control.')
        self.output_notice.setWordWrap(True)
        self.readout = QtWidgets.QLabel('Temperature: — | Error: — | PWM: 0')
        layout.addWidget(self.status)
        layout.addWidget(self.output_notice)
        layout.addWidget(self.readout)
        self.plots, self.curves = [], {}
        curve_names = {'temperature_heat': 'Measured temperature — HEAT',
                       'temperature_cool': 'Measured temperature — COOL',
                       'setpoint': 'Setpoint (target temperature)',
                       'error': 'Error = setpoint − measured temperature',
                       'pwm_heat': 'Reported PWM — HEAT',
                       'pwm_cool': 'Reported PWM — COOL',
                       'command_pwm': 'Next commanded PWM',
                       'direction': 'Reported output: HEAT / OFF / COOL'}
        for title, label, units, series in [
            ('Live TEC Temperature vs. Time', 'Temperature', '°C',
             [('temperature_heat', 'r'), ('temperature_cool', 'b'), ('setpoint', '#006400')]),
            ('Live PWM vs. Time', 'PWM', 'counts',
             [('pwm_heat', 'r'), ('pwm_cool', 'b'), ('command_pwm', '#7b2cbf')]),
            ('Error: setpoint − temperature', 'Error', '°C', [('error', '#c45100')]),
            ('Output direction', 'Direction', '', [('direction', 'c')])]:
            plot = pg.PlotWidget(title=title)
            plot.setLabel('left', label, units=units)
            plot.setLabel('bottom', 'Elapsed time', units='s')
            plot.showGrid(x=True, y=True)
            plot.enableAutoRange(axis='y', enable=True)
            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(14)
            legend_widget = pg.GraphicsLayoutWidget()
            legend_widget.setBackground('w')
            legend_widget.setMinimumWidth(220)
            legend_widget.setMaximumWidth(250)
            legend = pg.LegendItem(labelTextColor='k', labelTextSize='9pt',
                                   brush=(255, 255, 255, 235), pen=(150, 150, 150))
            legend_widget.addItem(legend, row=0, col=0)
            for key, color in series:
                reference = key in ('setpoint', 'command_pwm')
                pen = pg.mkPen(color, width=4 if reference else 5,
                               style=QtCore.Qt.PenStyle.DashLine if reference
                               else QtCore.Qt.PenStyle.SolidLine)
                curve = plot.plot(pen=pen, connect='finite')
                legend.addItem(curve, curve_names[key])
                self.curves[key] = curve
            row_layout.addWidget(plot, 1)
            row_layout.addWidget(legend_widget)
            layout.addWidget(row, 1)
            self.plots.append(plot)
        self.plots[3].getAxis('left').setTicks([[(-1, 'COOL'), (0, 'OFF'), (1, 'HEAT')]])
        self.plots[3].setYRange(-1.2, 1.2)
        self.start_button.clicked.connect(self.start_control)
        self.stop_button.clicked.connect(lambda: self.stop_control('Stopped'))
        self.mode.currentTextChanged.connect(self.mode_changed)
        self.mode_changed()

    def mode_changed(self):
        self.stop_control('Stopped — press Start to enable the selected mode')
        manual = self.mode.currentText() == 'Manual'
        self.manual_pwm.setEnabled(manual)
        self.manual_direction.setEnabled(manual)
        self.kp.setEnabled(not manual)

    def update_output_notice(self):
        mode = self.mode.currentText()
        self.start_button.setText(f'{mode} control running' if self.enabled else f'Start {mode} control')
        self.start_button.setEnabled(not self.enabled)
        if self.enabled:
            self.output_notice.setText('OUTPUT ENABLED — each fresh measurement updates the command.')
            self.output_notice.setStyleSheet('color: green; font-weight: bold;')
        else:
            self.output_notice.setText(
                f'OUTPUT OFF — {self.stop_reason}. Click Start {mode} control when Arduino is OK. '
                'Changing the setpoint alone does not enable output.')
            self.output_notice.setStyleSheet('color: #a34b00; font-weight: bold;')

    def send(self, direction, pwm):
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException('Serial connection is unavailable.')
        data = command_bytes(direction, pwm)
        if self.ser.write(data) != len(data):
            raise serial.SerialException('Incomplete serial write.')

    def stop_control(self, reason):
        self.enabled = False
        self.stop_reason = reason
        self.update_output_notice()
        self.status.setText(reason)
        if self.ser and self.ser.is_open:
            try:
                self.send('HEAT', 0)
            except (OSError, serial.SerialException) as error:
                self.status.setText(f'{reason}; cannot send stop: {error}')

    def start_control(self):
        if (not self.ser or not self.ser.is_open or self.sample is None
                or self.last_received is None or time.monotonic() - self.last_received > STALE_SECONDS
                or self.sample.safety != 'OK'):
            self.status.setText('Cannot start: need fresh, safe telemetry from the Module 5 sketch.')
            return
        self.enabled = True
        self.update_output_notice()
        self.status.setText('Running — next fresh measurement will update the output')

    def update_loop(self):
        now = time.monotonic()
        if self.last_received is not None and now - self.last_received > STALE_SECONDS:
            if self.enabled:
                self.stop_control('Telemetry timed out — stopped; press Start after recovery')
            else:
                self.status.setText('No fresh telemetry — check Arduino connection')
        if not self.ser or not self.ser.is_open:
            return
        try:
            self.buffer.extend(self.ser.read(min(self.ser.in_waiting, 8192)))
            if len(self.buffer) > 8192:
                self.buffer.clear()
                self.stop_control('Serial backlog or invalid framing — stopped')
                return
            samples = []
            while b'\n' in self.buffer:
                line, _, rest = self.buffer.partition(b'\n')
                self.buffer = bytearray(rest)
                try:
                    sample = parse_sample(line.decode('ascii', errors='replace').strip())
                except ValueError as error:
                    self.stop_control(str(error))
                    continue
                if sample is not None:
                    if sample.safety != 'OK':
                        self.stop_control(f'Arduino {sample.safety} — stopped')
                    samples.append(sample)
            # Act only on the newest complete measurement, never replay a burst
            # of stale control commands after the GUI has fallen behind.
            if samples:
                self.handle_sample(samples[-1], now)
        except (OSError, serial.SerialException) as error:
            self.stop_control(f'Serial connection failed: {error}')
            self.ser.close()

    def handle_sample(self, sample, now):
        if self.sample is not None and sample.time <= self.sample.time:
            self.stop_control('Arduino time restarted/repeated — stopped; press Start to resume')
        self.sample, self.last_received = sample, now
        target, kp = self.setpoint.value(), self.kp.value()
        if math.isfinite(sample.temperature):
            error, u, direction, pwm = p_command(target, sample.temperature, kp)
        else:
            error, u, direction, pwm = math.nan, math.nan, 'HEAT', 0
        if sample.safety != 'OK':
            self.enabled = False
            self.stop_reason = f'Arduino {sample.safety}'
        if self.mode.currentText() == 'Manual':
            direction, pwm = self.manual_direction.currentText(), self.manual_pwm.value()
            u = math.nan  # No P-controller output is used in manual mode.
        if not self.enabled:
            direction, pwm = 'HEAT', 0
        self.send(direction, pwm)
        self.update_output_notice()
        state = 'Running' if self.enabled else 'Stopped'
        self.status.setText(f'{state} | {self.mode.currentText()} | Arduino: {sample.safety} | limit {sample.limit:g} °C')
        self.readout.setText(f'T: {sample.temperature:.2f} °C | Setpoint: {target:.2f} °C | '
                             f'Error: {error:+.2f} °C | Reported: {sample.direction} {sample.pwm} | '
                             f'Next command: {direction} {pwm}')
        elapsed = now - self.started
        self.history.append((elapsed, sample.temperature, target, error, sample.pwm, pwm,
                             0 if sample.pwm == 0 else (1 if sample.direction == 'HEAT' else -1),
                             sample.direction))
        while self.history and elapsed - self.history[0][0] > WINDOW_SECONDS:
            self.history.popleft()
        columns = list(zip(*self.history))
        times = list(columns[0])
        # Match Module 4: use reported direction and NaN gaps so a heating
        # trace never bridges across a cooling interval (or vice versa).
        for suffix, reported_direction in (('heat', 'HEAT'), ('cool', 'COOL')):
            for prefix, index in (('temperature', 1), ('pwm', 4)):
                values = [row[index] if row[7] == reported_direction else math.nan
                          for row in self.history]
                self.curves[f'{prefix}_{suffix}'].setData(times, values)
        for key, index in (('setpoint', 2), ('error', 3), ('command_pwm', 5), ('direction', 6)):
            self.curves[key].setData(times, list(columns[index]))
        for plot in self.plots:
            plot.setXRange(max(0, elapsed - WINDOW_SECONDS), max(WINDOW_SECONDS, elapsed), padding=0)
        try:
            self.writer.writerow([elapsed, sample.time, sample.temperature, target, kp, error, u,
                                  pwm, direction, sample.pwm, sample.direction,
                                  self.mode.currentText(), self.enabled, sample.safety,
                                  sample.limit, sample.pwm9, sample.pwm10])
            self.log_file.flush()
        except OSError as error:
            self.stop_control(f'CSV logging failed: {error}')

    def closeEvent(self, event):
        self.timer.stop()
        self.stop_control('Closing')
        if self.ser:
            self.ser.close()
        self.log_file.close()
        event.accept()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', help='Explicit serial device; otherwise auto-detect USB')
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    gui = PControlGUI(args.port)
    gui.show()
    sys.exit(app.exec())
