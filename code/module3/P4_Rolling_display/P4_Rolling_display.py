import sys
import csv
import re
import os
import serial
from serial.tools import list_ports
from PySide6 import QtWidgets, QtCore
import pyqtgraph as pg

# ==============================================================================
# CONFIGURATION SETTINGS (Edit these parameters for your setup)
# ==============================================================================
SERIAL_PORT = None            # Set a port here to override automatic detection
BAUD_RATE = 9600              # Serial baud rate matching Arduino Serial.begin()
WINDOW_DURATION_SEC = 60.0    # Rolling window size in seconds
UPDATE_INTERVAL_MS = 100      # GUI plot update interval in milliseconds
TEMP_MIN_C = 10.0             # Y-axis minimum temperature limit (°C)
TEMP_MAX_C = 40.0             # Y-axis maximum temperature limit (°C)
CSV_FILENAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'tec_data.csv'
)  # Save beside this script

# Regular expression to match the shared fields in the Arduino output.
# The text after PWM varies between the Arduino sketches, so it is optional.
LINE_PATTERN = re.compile(
    r"Temperature \(C\):\s*([-+]?\d*\.?\d+),\s*"
    r"Time \(s\):\s*([-+]?\d*\.?\d+),\s*"
    r"PWM:\s*(\d+)"
)


# ==============================================================================
# MAIN APPLICATION WINDOW
# ==============================================================================
class StripChartWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEC Temperature Strip Chart (Display-Only)")
        self.resize(800, 600)

        # Data buffers
        self.time_data = []
        self.temp_data = []

        # Initialize CSV File & Header
        self.init_csv()

        # Initialize Serial Connection
        self.init_serial()

        # Build PySide6 / pyqtgraph Plot UI
        self.init_ui()

        # Setup Timer for Continuous Serial Reading & Plot Updating
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(UPDATE_INTERVAL_MS)

    def init_csv(self):
        """Creates the CSV file and writes column headers if it doesn't exist."""
        file_exists = os.path.exists(CSV_FILENAME)
        with open(CSV_FILENAME, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['time_s', 'temperature_C', 'pwm', 'heat_cool'])

    def init_serial(self):
        """Opens the serial port to communicate with the Arduino."""
        available_ports = list(list_ports.comports())
        if SERIAL_PORT:
            port_name = SERIAL_PORT
        else:
            usb_ports = [
                port for port in available_ports
                if any(
                    keyword in f'{port.device} {port.description} {port.manufacturer}'.lower()
                    for keyword in ('arduino', 'usbmodem', 'usbserial', 'wchusbserial', 'ch340')
                )
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
            print(f"Successfully connected to serial port: {port_name}")
        except Exception as e:
            print(f"ERROR: Could not open serial port {port_name}: {e}")
            sys.exit(1)

    def init_ui(self):
        """Sets up the pyqtgraph widget layout."""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Create Plot Widget
        self.plot_widget = pg.PlotWidget(title="Live TEC Temperature vs. Time")
        layout.addWidget(self.plot_widget)

        # Configure Axes and Grid
        self.plot_widget.setLabel('left', 'Temperature', units='°C')
        self.plot_widget.setLabel('bottom', 'Arduino Time', units='s')
        self.plot_widget.setYRange(TEMP_MIN_C, TEMP_MAX_C)
        self.plot_widget.showGrid(x=True, y=True)

        # Plot Line Curve (Yellow Line)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='y', width=2))

    def update_loop(self):
        """Reads serial lines, parses valid data, logs to CSV, and updates the graph."""
        while self.ser and self.ser.in_waiting > 0:
            try:
                # Read line from serial and decode
                line_bytes = self.ser.readline()
                line_str = line_bytes.decode('utf-8', errors='ignore').strip()

                if not line_str:
                    continue

                # Echo complete line directly to VS Code terminal
                print(f"RAW: {line_str}")

                # Parse line using Regular Expression
                match = LINE_PATTERN.search(line_str)
                if match:
                    temp_c = float(match.group(1))
                    time_s = float(match.group(2))
                    pwm = int(match.group(3))
                    heat_cool = 0

                    # 1. Store in data buffers for plotting
                    self.time_data.append(time_s)
                    self.temp_data.append(temp_c)

                    # 2. Append accepted reading to CSV file
                    with open(CSV_FILENAME, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([time_s, temp_c, pwm, heat_cool])

            except Exception as err:
                # Silently ignore malformed or corrupted serial lines
                pass

        # Update Rolling Window Plot
        if self.time_data:
            current_time = self.time_data[-1]
            min_time = current_time - WINDOW_DURATION_SEC

            # Filter data points within the rolling window
            filtered_times = []
            filtered_temps = []
            for t, temp in zip(self.time_data, self.temp_data):
                if t >= min_time:
                    filtered_times.append(t)
                    filtered_temps.append(temp)

            # Update Plot Curve Data and X-Axis Limits
            self.curve.setData(filtered_times, filtered_temps)
            self.plot_widget.setXRange(max(0, min_time), max(WINDOW_DURATION_SEC, current_time))

    def closeEvent(self, event):
        """Cleanly closes serial port when the window is closed."""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")
        event.accept()


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = StripChartWindow()
    window.show()
    sys.exit(app.exec())