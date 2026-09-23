

| Complete | Item | Value or Observation |
|---|---|---|
| [x] | Arduino board and port | |
| [x] | Thermistor pin | |
| [x] | H-bridge control pins | |
| [x] | PWM starts at zero? | |
| [x] | Module 2 motor test completed with TEC disconnected? | |
| [x] | High-current leads are 18 AWG? | |
| [x] | Prepared TEC and thermal-switch wiring inspected? | |
| [x] | Heat exchanger connected to 12 V and operating? | |
| [x] | Power supply voltage       | [_________12V_________] |
| [x] | Power supply current limit | [_________10A_________] |
| [x] | Thermal cutoff identified? | [_________75C________] |
| [x] | Instructor check complete? | |


| Pin 11 input | Pin 9 waveform | Pin 10 waveform | M+ waveform | M- waveform | PWM frequency | PWM duty cycle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **5V** (HEAT / clockwise) | PWM, active, 0–5 V | 0 V / low | Active PWM on M+ | 0V | ~490 Hz | ~100% |
| **0V** (COOL / counterclockwise) | 0 V / low | PWM, active, 0–5 V | 0V | Active PWM on M− | ~490 Hz | ~0% |