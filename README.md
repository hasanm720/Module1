# Module1

PHYS39 Module 1 — Instrumentation team repository.

### Team members
Kyle Chen, Muhammad Hasan

### Team repository
https://github.com/hasanm720/Module1/tree/mainv2

## Module 1 sketches (`code/module1/`)

| Folder | Sketch | What it does / measures |
| --- | --- | --- |
| `P1_Blink` | `P1_Blink.ino` | Standard Arduino Blink example; toggles the on-board LED (pin `LED_BUILTIN`) on/off every second to confirm the board and IDE upload workflow. |
| `P2_analog_read_serial` | `P2_analog_read_serial.ino` | Reads the raw 10-bit ADC value from a trim potentiometer on `A0` and prints it to the Serial Monitor/Plotter. Post-class notes record the trim pot's measured range (`min ≈ 55`, `max ≈ 1018`, midpoint ≈ 500). |
| `P3_averaging_vs_unaveraging/3a_analog_read_serial` | `3a_analog_read_serial.ino` | Baseline raw ADC read of the trim pot on `A0` (same as P2), used as the starting point for the averaging comparison in Part 3. |
| `P3_averaging_vs_unaveraging/3b_trim_pot_analog_read_serial` | `3b_trim_pot_analog_read_serial.ino` | Converts the trim pot's raw ADC reading to a voltage (`Vref = 5.00 V`, 10-bit conversion) and prints it, to observe thermal-noise fluctuations in the un-averaged signal. |
| `P3_averaging_vs_unaveraging/3c` | `3c_trim_pot_average_vs_unaveraged.ino` | Collects 100 single (un-averaged) voltage readings, then 100 readings each averaged over 1000 ADC samples, to compare noise between raw and averaged measurements. |
| `P3_averaging_vs_unaveraging/3c` | `3c_trim_pot_STDEV.ino` | Repeats the averaged-vs-unaveraged measurement and computes the mean and standard deviation of both sets, then checks the noise-reduction ratio `s1000/s1` against the expected `1/sqrt(1000)` scaling. |
| `P3_averaging_vs_unaveraging/3d_trim_pot_micros` | `3d_trim_pot_micros.ino` | Same averaged-vs-unaveraged statistics as 3c, plus timing via `micros()` to measure the elapsed time and throughput (conversions/sec) of 1000 `analogRead()` calls. |
| `P4_trim_pot_DutyCycle` | `P4_trim_pot_DutyCycle.ino` | Uses the averaged trim-pot voltage to drive a PWM output (`analogWrite`, pin 9) controlling LED brightness/duty cycle; prints averaged ADC value, voltage, and PWM value. Duty cycle was verified on an oscilloscope at high and low trim-pot settings (see `docs/images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/`). |

Supporting circuit photos, serial monitor/plotter screenshots, and oscilloscope captures for each measurement above are in `docs/images/module1/`.

## Module 2 sketches (`code/module2/`)

| Folder | Sketch | What it does / measures |
| --- | --- | --- |
| `P1_serial_monitor` | `P1_serial_monitor.ino` | Reads 100 thermistor ADC samples from `A0`, averages them, converts the result through the voltage-divider and Beta-model equations, and prints time, ADC value, voltage, resistance, and temperature to the Serial Monitor once per second. |
| `P2_serial_plotter` | `part2_thermistor.ino` | Averages 500 thermistor readings from `A0`, calculates temperature using the Beta model, and prints one numeric temperature value per line for Arduino Serial Plotter. |
| `P3_Hbridge/P3_Hbridge` | `P3_Hbridge.ino` | Averages 100 trim-pot readings from `A1` to set a PWM command. A mode input on pin 11 selects HEAT (PWM on pin 9) or COOL (PWM on pin 10), while the other H-bridge input is held at zero; prints mode, averaged ADC value, and PWM command. |

## Module 3 sketches and display programs (`code/module3/`)

| Folder | Sketch / program | What it does / measures |
| --- | --- | --- |
| `P2_First_Manual_Sketch` | `P2_First_Manual_Sketch.ino` | Reads the thermistor on `A0` and a trim pot on `A1`; maps the trim-pot value to PWM on H-bridge pin 10 while pin 9 remains LOW, then prints temperature, elapsed time, PWM, and active output pin. |
| `P3_SPDT_switch` | `P3_SPDT_switch.ino` | Extends P2 with an SPDT direction switch on pin 11. The trim pot still sets PWM, while the switch selects whether H-bridge pin 9 or pin 10 receives the PWM signal. |
| `P4_Rolling_display` | `P4_Rolling_display.py` | PySide6/pyqtgraph display-only rolling strip chart. It reads Arduino temperature telemetry, shows the most recent 60 seconds of temperature data, prints raw serial text to the terminal, and logs readings to CSV. |
| `P5_Manual_controls` | `P5_Manual_heat_cool_display.py` | PySide6/pyqtgraph manual-control GUI with Heat/Cool buttons, synchronized slider and text-entry PWM control, live readouts, red/blue temperature and PWM strip charts, terminal output, and CSV logging. It sends `SET PWM <0-255> DIR HEAT\|COOL` commands. |
| `P6_Arduino_Serial-Command` | `P6_Arduino_Serial-Command.ino` | Serial-command replacement for the manual trim-pot and SPDT controls. It averages thermistor readings on `A0`, applies GUI PWM/direction commands to H-bridge pins 9 and 10, clamps valid PWM values to `0-255`, and safely sets PWM to zero for malformed or unknown commands. It reports temperature, time, PWM, and `Heat/Cool` direction state. |

### Module 3 project purpose

Module 3 is a manual thermoelectric-cooler (TEC) instrumentation project. The Arduino measures the thermistor temperature, drives the TEC H-bridge, and reports telemetry over USB serial. The Python programs either display that telemetry as a rolling strip chart (P4) or provide manual PWM and Heat/Cool commands while displaying temperature and PWM histories (P5, paired with the P6 Arduino sketch). There is no temperature-feedback control loop: the user selects PWM and direction manually.

### Hardware connections

The current serial-command configuration is P6. The P2/P3 sketches retain the earlier trim-pot and physical-switch controls for comparison.

| Arduino connection | Purpose | Used by |
| --- | --- | --- |
| `A0` | Thermistor voltage-divider measurement node. The fixed 100 kOhm resistor connects to 5 V and the 100 kOhm thermistor connects to GND. | P2, P3, and P6 Arduino sketches |
| `D9` | H-bridge input for the experimentally verified HEAT direction; receives PWM in HEAT mode while `D10` is LOW. | P2, P3, and P6 Arduino sketches |
| `D10` | H-bridge input for the experimentally verified COOL direction; receives PWM in COOL mode while `D9` is LOW. | P2, P3, and P6 Arduino sketches |
| `A1` | Trim-pot input used to choose manual PWM before serial control was added. Not used by P6. | P2-P3 only |
| `D11` | SPDT Heat/Cool direction-switch input. Not used by P6. | P3 only |
| USB serial | 9600-baud connection between the Arduino and the Python program. | P4-P6 |

### Arduino/Python program pairs

| Arduino sketch | Python program | Use |
| --- | --- | --- |
| `P2_First_Manual_Sketch.ino` or `P3_SPDT_switch.ino` | `P4_Rolling_display.py` | Display-only temperature strip chart using the telemetry produced by the earlier manual-control sketches. |
| `P6_Arduino_Serial-Command.ino` | `P5_Manual_heat_cool_display.py` | Manual GUI control. The GUI sends PWM/direction commands and plots the Arduino telemetry. |

### Upload and run the P6 manual-control pair

1. Connect the Arduino by USB and verify that the thermistor and H-bridge wiring matches the table above.
2. Open `code/module3/P6_Arduino_Serial-Command/P6_Arduino_Serial-Command.ino` in Arduino IDE, select the correct board and port, and upload it.
3. Close Arduino Serial Monitor and Serial Plotter after uploading. They cannot share the serial port with Python.
4. Install the Python packages once, if needed:

   ```bash
   python3 -m pip install PySide6 pyqtgraph pyserial
   ```

5. From the repository root, run:

   ```bash
   python3 code/module3/P5_Manual_controls/P5_Manual_heat_cool_display.py
   ```

6. If automatic port detection cannot find the board, set `SERIAL_PORT` near the top of the Python program to the Arduino port (for example, `/dev/cu.usbmodem1101` on macOS). Use the GUI Heat/Cool buttons and PWM slider or text box to send commands. The Arduino starts at PWM `0`.

### Serial telemetry format

P6 prints lines in this form:

```text
Temperature (C): 27.73, Time (s): 645.06, PWM: 120, Heat/Cool: 1
```

| Field | Meaning |
| --- | --- |
| `Temperature (C)` | Averaged thermistor temperature in degrees Celsius. |
| `Time (s)` | Arduino elapsed time in seconds since startup. |
| `PWM` | Applied 8-bit H-bridge PWM command, from `0` to `255`. |
| `Heat/Cool` | Selected H-bridge direction: `1` is HEAT on pin 9 and `0` is COOL on pin 10. |

The GUI sends newline-terminated commands in this form:

```text
SET PWM 120 DIR HEAT
SET PWM 45 DIR COOL
```

P6 clamps a valid numeric PWM value to `0-255`. A malformed, unknown, or overlong command sets PWM to `0` as a safety action.

### Python serial and data flow

In `P5_Manual_heat_cool_display.py`:

| Task | Where it happens |
| --- | --- |
| Opens the Arduino serial port | `init_serial()` detects one Arduino-compatible port and opens it at 9600 baud. |
| Sends commands | `on_slider_changed()`, `on_pwm_text_finished()`, and `on_direction_changed()` call `send_command()`, which writes `SET PWM <value> DIR <HEAT/Cool>` followed by a newline. |
| Reads and parses telemetry | The timer calls `update_loop()` every 100 ms. It uses `self.ser.readline()` and `TELEMETRY_PATTERN` to extract temperature, time, and PWM from each complete line. |
| Saves readings | `init_csv()` creates `tec_manual_data.csv`; `update_loop()` appends time, temperature, PWM, and direction for every accepted telemetry line. The P5/P6 log is saved beside the Python program at `code/module3/P5_Manual_controls/tec_manual_data.csv`. The display-only P4 program separately saves `code/module3/P4_Rolling_display/tec_data.csv`. |
| Plots readings | `update_plots()` keeps the most recent 60 seconds and updates red HEAT and blue COOL temperature/PWM traces. |

### Testing evidence

The screenshots in `docs/images/module3/` document the following completed checks:

- P2: Arduino Serial Monitor output shows repeated temperature, time, PWM, and active-pin telemetry with PWM on pin 10.
- P3: Serial Monitor screenshots show both pin-11 states: 5 V selects active PWM pin 9 and 0 V selects active PWM pin 10. Breadboard/circuit photos and an oscilloscope PWM waveform are also included.
- P4: Two Python rolling-display screenshots show live temperature traces, including rising and falling temperature runs.
- Manual GUI: `slider+plot_screenshot.png` shows the Cool selection, PWM text/slider value of 212, live temperature/PWM/direction/time readouts, and red/blue temperature and PWM histories.

The stored screenshots do not directly document P6 upload/run completion, malformed-command shutdown, PWM-clamping boundary tests, or inspection of the CSV file. Those checks should be performed and captured before claiming them as completed.

## Repository layout

- `code/module1/` — Module 1 Arduino sketches (see table above)
- `code/module2/` — Module 2 Arduino sketches
- `code/module3/` — Module 3 Arduino sketches and Python display/control programs
- `docs/images/` — Circuit photos and measurement screenshots, organized by module/part
- `docs/module_notes/` — Written module notes/evidence
