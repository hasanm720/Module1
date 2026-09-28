# Module 4: manual TEC control with temperature shutdown

Upload `P1.ino`, then run `python3 code/module4/P1/P1_Manual_heat_cool_display.py`
from the repository root. Python dependencies: pyserial, PySide6, pyqtgraph.
Close Arduino Serial Monitor before opening the GUI. Set SERIAL_PORT in the
Python script if automatic port detection is ambiguous.

The sketch retains the Module 3 P6 pin assignments, thermistor equation and
SET PWM command protocol. The GUI is adapted from Module 3 P5.
Each loop averages 500 raw ADC measurements before converting to temperature.
That same temperature drives the safety check and, on reporting loops, serial
telemetry, GUI readouts and CSV recording. No Python temperature averaging is needed.
The software limit is TEMPERATURE_LIMIT_C = 60.0. Above it, both PWM outputs
are zero and commands cannot restart the TEC. After temperature falls to or
below the limit, PWM stays zero until a new command arrives.

Telemetry continues twice per second, including Safety: SHUTDOWN or OK,
Limit (C), PWM9 and PWM10. The GUI shows these fields and saves them alongside
temperature in tec_safety_data.csv in this directory. PWM fields describe the
values written by software; they are not independent electrical measurements.
The hardware thermal switch near 70 °C remains the independent final protection.

## Instructor demonstration (TEC power off)

1. Turn off the TEC power supply, keeping the Arduino powered through USB.
   Upload the normal sketch and note the averaged room temperature in the GUI.
2. Close the GUI. Temporarily change TEMPERATURE_LIMIT_C to just below that
   measured temperature and upload again. Do not heat the apparatus to 60 °C.
3. Reopen the GUI. Verify Safety: SHUTDOWN, PWM: 0, PWM9: 0 and PWM10: 0,
   with temperature and time continuing to update. With TEC power still off,
   try a nonzero command for each direction; both outputs must remain zero.
   Verify pins 9 and 10 stay LOW using the available lab measurement equipment.
4. Save the shutdown CSV rows or a screenshot for the instructor.
5. Close the GUI, restore TEMPERATURE_LIMIT_C = 60.0, upload again, and reopen
   the GUI. Verify Limit: 60.00 °C, Safety: OK at room temperature and PWM zero.
   Show the restored constant and demonstration results to the instructor.

Validation performed in software: Python syntax and a host C++ simulation of
500 ADC reads, overtemperature cutoff, blocked commands, and zero PWM after
cooldown. Arduino board compilation, GUI operation and electrical verification
require the lab setup and have not been performed here.
