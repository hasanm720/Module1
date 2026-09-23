import sys
import csv
import re
import os

import serial
from serial.tools import list_ports
from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg


# ==============================================================================
# CONFIGURATION SETTINGS (edit these for your setup)
# ==============================================================================
SERIAL_PORT = None            # Set a port here to override automatic detection.
BAUD_RATE = 9600              # Must match Arduino Serial.begin().
WINDOW_DURATION_SEC = 60.0    # Number of recent seconds shown in each chart.
UPDATE_INTERVAL_MS = 100      # How often the GUI checks the serial port.
TEMP_MIN_C = 10.0             # Temperature chart lower limit in degrees C.
TEMP_MAX_C = 40.0             # Temperature chart upper limit in degrees C.
CSV_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'tec_manual_data.csv'
)

# This finds the fields printed by the earlier Arduino sketches.  Direction is
# parsed separately because different sketches may call it "DIR" or "Direction".
TELEMETRY_PATTERN = re.compile(
    r"Temperature \(C\):\s*([-+]?\d*\.?\d+),\s*"
    r"Time \(s\):\s*([-+]?\d*\.?\d+),\s*"
    r"PWM:\s*(\d+)",
    re.IGNORECASE,
)
DIRECTION_PATTERN = re.compile(r"(?:DIR|Direction)\s*[:=]\s*(HEAT|COOL)", re.IGNORECASE)


class ManualTecWindow(QtWidgets.QMainWindow):
    """A manual TEC controller: it sends commands but does not use feedback control."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TEC Manual Heat/Cool Strip Chart')
        self.resize(920, 820)

        # Lists hold every accepted temperature reading for the rolling plots.
        self.time_data = []
        self.temp_data = []
        self.pwm_data = []
        self.direction_data = []

        # These are the values the user is manually sending to the Arduino.
        self.commanded_pwm = 0
        self.commanded_direction = 'HEAT'
        self.last_reported_direction = 'HEAT'

        self.init_csv()
        self.init_serial()
        self.init_ui()

        # The timer repeatedly reads new serial text and refreshes the plots.
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(UPDATE_INTERVAL_MS)

    def init_csv(self):
        """Create the log file once, then append one row per telemetry reading."""
        file_exists = os.path.exists(CSV_FILENAME)
        with open(CSV_FILENAME, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(['time_s', 'temperature_C', 'pwm', 'direction'])

    def init_serial(self):
        """Open the Arduino serial port using the same detection as the display script."""
        available_ports = list(list_ports.comports())
        if SERIAL_PORT:
            port_name = SERIAL_PORT
        else:
            usb_ports = [
                port for port in available_ports
                if any(keyword in f'{port.device} {port.description} {port.manufacturer}'.lower()
                       for keyword in ('arduino', 'usbmodem', 'usbserial', 'wchusbserial', 'ch340'))
            ]
            if len(usb_ports) == 1:
                port_name = usb_ports[0].device
            elif len(available_ports) == 1:
                port_name = available_ports[0].device
            else:
                detected = ', '.join(port.device for port in available_ports) or 'none'
                print(f'ERROR: Could not identify one Arduino serial port. Found: {detected}')
                sys.exit(1)

        try:
            self.ser = serial.Serial(port_name, BAUD_RATE, timeout=0.1)
            print(f'Successfully connected to serial port: {port_name}')
        except Exception as error:
            print(f'ERROR: Could not open serial port {port_name}: {error}')
            sys.exit(1)

    def init_ui(self):
        """Build the buttons, readouts, and pyqtgraph charts."""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # This group contains the manual widgets that choose the command sent.
        controls = QtWidgets.QGroupBox('Manual TEC command (no feedback control)')
        controls_layout = QtWidgets.QGridLayout(controls)
        layout.addWidget(controls)

        # Two checkable buttons act as a heat/cool switch; only one can be active.
        controls_layout.addWidget(QtWidgets.QLabel('Direction:'), 0, 0)
        self.heat_button = QtWidgets.QRadioButton('Heat')
        self.cool_button = QtWidgets.QRadioButton('Cool')
        self.heat_button.setChecked(True)
        direction_group = QtWidgets.QButtonGroup(self)
        direction_group.addButton(self.heat_button)
        direction_group.addButton(self.cool_button)
        controls_layout.addWidget(self.heat_button, 0, 1)
        controls_layout.addWidget(self.cool_button, 0, 2)
        self.heat_button.toggled.connect(self.on_direction_changed)
        self.cool_button.toggled.connect(self.on_direction_changed)

        # The slider gives quick adjustment; its range is exactly Arduino PWM's 0-255.
        controls_layout.addWidget(QtWidgets.QLabel('PWM:'), 1, 0)
        self.pwm_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.pwm_slider.setRange(0, 255)
        self.pwm_slider.setValue(self.commanded_pwm)
        self.pwm_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.pwm_slider.setTickInterval(25)
        controls_layout.addWidget(self.pwm_slider, 1, 1, 1, 3)
        self.pwm_slider.valueChanged.connect(self.on_slider_changed)

        # The editable box mirrors the slider and allows an exact PWM number.
        self.pwm_edit = QtWidgets.QLineEdit(str(self.commanded_pwm))
        self.pwm_edit.setValidator(QtGui.QIntValidator(0, 255, self))
        self.pwm_edit.setMaximumWidth(70)
        self.pwm_edit.setToolTip('Enter a whole number from 0 to 255, then press Enter.')
        controls_layout.addWidget(self.pwm_edit, 1, 4)
        self.pwm_edit.editingFinished.connect(self.on_pwm_text_finished)

        # These labels show the newest received measurement and current manual command.
        readouts = QtWidgets.QGroupBox('Live readouts')
        readout_layout = QtWidgets.QGridLayout(readouts)
        layout.addWidget(readouts)
        self.temperature_label = QtWidgets.QLabel('-- °C')
        self.live_pwm_label = QtWidgets.QLabel('0')
        self.direction_label = QtWidgets.QLabel('HEAT')
        self.time_label = QtWidgets.QLabel('-- s')
        for label in (self.temperature_label, self.live_pwm_label,
                      self.direction_label, self.time_label):
            label.setStyleSheet('font-weight: bold;')
        for column, (name, value) in enumerate((
            ('Temperature', self.temperature_label), ('PWM', self.live_pwm_label),
            ('Direction', self.direction_label), ('Arduino time', self.time_label),
        )):
            readout_layout.addWidget(QtWidgets.QLabel(name + ':'), 0, column)
            readout_layout.addWidget(value, 1, column)

        # The temperature chart uses red points from heat mode and blue points from cool mode.
        self.temperature_plot = pg.PlotWidget(title='Live TEC Temperature vs. Time')
        self.temperature_plot.setLabel('left', 'Temperature', units='°C')
        self.temperature_plot.setLabel('bottom', 'Arduino Time', units='s')
        self.temperature_plot.setYRange(TEMP_MIN_C, TEMP_MAX_C)
        self.temperature_plot.showGrid(x=True, y=True)
        self.temperature_heat_curve = self.temperature_plot.plot(
            pen=pg.mkPen('r', width=2), name='Heating')
        self.temperature_cool_curve = self.temperature_plot.plot(
            pen=pg.mkPen('b', width=2), name='Cooling')
        self.temperature_plot.addLegend()
        layout.addWidget(self.temperature_plot)

        # A second strip chart shows the actual PWM value received from telemetry.
        self.pwm_plot = pg.PlotWidget(title='Live PWM vs. Time')
        self.pwm_plot.setLabel('left', 'PWM')
        self.pwm_plot.setLabel('bottom', 'Arduino Time', units='s')
        self.pwm_plot.setYRange(0, 255)
        self.pwm_plot.showGrid(x=True, y=True)
        self.pwm_heat_curve = self.pwm_plot.plot(pen=pg.mkPen('r', width=2), name='Heating')
        self.pwm_cool_curve = self.pwm_plot.plot(pen=pg.mkPen('b', width=2), name='Cooling')
        self.pwm_plot.addLegend()
        layout.addWidget(self.pwm_plot)

    def on_slider_changed(self, value):
        """Copy a slider change to the text box and send one new manual command."""
        self.commanded_pwm = value
        self.pwm_edit.setText(str(value))
        self.send_command()

    def on_pwm_text_finished(self):
        """Clamp typed PWM to 0-255, synchronize the slider, and send the command."""
        try:
            typed_value = int(self.pwm_edit.text())
        except ValueError:
            typed_value = self.commanded_pwm
        clamped_value = max(0, min(255, typed_value))

        # Blocking the signal prevents setValue() from sending the same command twice.
        self.pwm_slider.blockSignals(True)
        self.pwm_slider.setValue(clamped_value)
        self.pwm_slider.blockSignals(False)
        self.commanded_pwm = clamped_value
        self.pwm_edit.setText(str(clamped_value))
        self.send_command()

    def on_direction_changed(self):
        """Send the current PWM again whenever the user selects Heat or Cool."""
        if not self.heat_button.isChecked() and not self.cool_button.isChecked():
            return
        self.commanded_direction = 'HEAT' if self.heat_button.isChecked() else 'COOL'
        self.send_command()

    def send_command(self):
        """Send the Arduino's required manual command format, followed by a newline."""
        if not hasattr(self, 'ser') or not self.ser or not self.ser.is_open:
            return
        command = f'SET PWM {self.commanded_pwm} DIR {self.commanded_direction}\n'
        try:
            self.ser.write(command.encode('utf-8'))
            self.ser.flush()
            print(f'TX: {command.strip()}')
        except serial.SerialException as error:
            print(f'ERROR: Could not send command: {error}')

    def update_loop(self):
        """Read serial lines, keep terminal/CSV output, and refresh both rolling plots."""
        while self.ser and self.ser.in_waiting > 0:
            try:
                line_str = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not line_str:
                    continue

                # Keep every complete serial line visible in the terminal.
                print(f'RAW: {line_str}')
                telemetry = TELEMETRY_PATTERN.search(line_str)
                if not telemetry:
                    continue

                temp_c = float(telemetry.group(1))
                time_s = float(telemetry.group(2))
                pwm = max(0, min(255, int(telemetry.group(3))))
                direction_match = DIRECTION_PATTERN.search(line_str)
                direction = (direction_match.group(1).upper() if direction_match
                             else self.commanded_direction)
                self.last_reported_direction = direction

                # Save the sample for the plots and append the same information to CSV.
                self.time_data.append(time_s)
                self.temp_data.append(temp_c)
                self.pwm_data.append(pwm)
                self.direction_data.append(direction)
                with open(CSV_FILENAME, mode='a', newline='') as csv_file:
                    csv.writer(csv_file).writerow([time_s, temp_c, pwm, direction])

                # Update the on-screen values immediately with this newest reading.
                self.temperature_label.setText(f'{temp_c:.2f} °C')
                self.live_pwm_label.setText(str(pwm))
                self.direction_label.setText(direction)
                self.time_label.setText(f'{time_s:.2f} s')
            except (ValueError, OSError, serial.SerialException) as error:
                print(f'WARNING: Ignoring serial line: {error}')

        self.update_plots()

    def update_plots(self):
        """Split recent data by direction so heating is red and cooling is blue."""
        if not self.time_data:
            return
        current_time = self.time_data[-1]
        min_time = current_time - WINDOW_DURATION_SEC
        recent_times = []
        heat_temps, heat_pwms = [], []
        cool_temps, cool_pwms = [], []

        # NaN makes pyqtgraph leave a gap.  This prevents a red heat line from
        # drawing across a period where the TEC was actually cooling, and vice versa.
        for time_s, temp_c, pwm, direction in zip(
                self.time_data, self.temp_data, self.pwm_data, self.direction_data):
            if time_s < min_time:
                continue
            recent_times.append(time_s)
            if direction == 'HEAT':
                heat_temps.append(temp_c)
                heat_pwms.append(pwm)
                cool_temps.append(float('nan'))
                cool_pwms.append(float('nan'))
            else:
                heat_temps.append(float('nan'))
                heat_pwms.append(float('nan'))
                cool_temps.append(temp_c)
                cool_pwms.append(pwm)

        # setData() redraws each solid line using the latest rolling-window samples.
        self.temperature_heat_curve.setData(recent_times, heat_temps)
        self.temperature_cool_curve.setData(recent_times, cool_temps)
        self.pwm_heat_curve.setData(recent_times, heat_pwms)
        self.pwm_cool_curve.setData(recent_times, cool_pwms)
        x_min, x_max = max(0, min_time), max(WINDOW_DURATION_SEC, current_time)
        self.temperature_plot.setXRange(x_min, x_max)
        self.pwm_plot.setXRange(x_min, x_max)

    def closeEvent(self, event):
        """Close the serial port when the window closes."""
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
            print('Serial connection closed.')
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ManualTecWindow()
    window.show()
    sys.exit(app.exec())
