# Module1

PHYS39 Module 1 — Instrumentation team repository.

**Team members:** _[TEAM MEMBER 1 NAME]_, _[TEAM MEMBER 2 NAME]_
**Team repository:** _[TEAM REPOSITORY URL]_

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

## Repository layout

- `code/module1/` — Module 1 Arduino sketches (see table above)
- `code/module2/` — Module 2 Arduino sketches
- `docs/images/` — Circuit photos and measurement screenshots, organized by module/part
- `docs/module_notes/` — Written module notes/evidence
