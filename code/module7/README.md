# Module 7 — Six-channel Arduino measurement

Open [module_07_rod_controller.ino](module_07_rod_controller/module_07_rod_controller.ino) in Arduino IDE. Select **Arduino Uno** and the correct USB port.

| Input | Sensor |
|---|---|
| A1 | TEC-base thermistor; sole feedback and temperature-shutdown sensor |
| A5, A4, A3, A2, A0 | Rod thermistors T1 (nearest TEC) … T5; measurements only |

The pins follow the bench wiring rather than the lab page's A0–A5 order. `THERMISTOR_PINS` = `{A1, A5, A4, A3, A2, A0}`, so the DATA/CSV columns are always TEC, rod1 … rod5 in physical order.

Use the same thermistor divider as before for each channel: fixed 100 kΩ to 5 V, thermistor to GND, and their junction to its analog input. Keep sensor/channel labels attached. H-bridge pins remain **D9 = HEAT**, **D10 = COOL**.

## What changed

Each acquisition averages **1,000 ADC readings per channel** using the original thermistor conversion. One extra conversion is discarded after switching inputs. One complete CSV line is sent after all six measurements, with Arduino elapsed time in seconds:

```text
DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,setpoint_C,safety
```

The header appears once at startup. Temperatures are °C; `pwm` is signed applied PWM (−255…+255); `heat_cool` is +1 for HEAT and −1 for COOL. Invalid temperature readings appear as `nan`. Every completed acquisition is reported, including during shutdown; measure the actual cycle time rather than assuming the old sample rate.

**PI still runs in Python.** The Arduino accepts the original commands, which contain PWM and direction but no setpoint. Consequently `setpoint_C` is `nan`; the later Module 7 GUI must retain its own commanded setpoint. The old GUI's telemetry parser does not understand this new format and must be extended in Stage 2.

## What stayed the same

The source is the [Arduino sketch used with Module 6](../module5/P1_P-only_control/P1_arduino_control/P1_arduino_control.ino). Its `stopOutput`, `applyOutput`, `checkSafety`, `processCommand`, and `readCommands` functions are unchanged: zero-output startup, opposite-pin clearing before direction changes, strict PWM validation, TEC-channel (A1) fault/60 °C shutdown, zero-output recovery, and the 2 s command timeout are preserved. Python PI and anti-windup code are unchanged. Commands and timeout checks are serviced between rod-channel measurements.

## Verify at the bench — TEC power disconnected

1. Upload the sketch, then open Serial Monitor at **115200 baud**, with **Newline** selected.
2. Confirm the header followed by one six-temperature `DATA` record per cycle. Startup `pwm` must be **0**.
3. Warm one sensor at a time with your fingers. Only its corresponding temperature should change appreciably. Repeat for all six.
4. Send `SET PWM 0 DIR HEAT`. Confirm reported PWM stays zero.
5. With TEC power still disconnected, send `SET PWM 20 DIR HEAT`, then stop sending commands. Within approximately 2 s plus an acquisition interval, PWM must return to zero and safety report `TIMEOUT`. Send the zero command again.
6. Restart the Arduino and confirm PWM starts at zero. Close Serial Monitor before opening any Python serial program.

Rod-channel faults do not disable or replace TEC-channel (A1) safety. A rail reading reports `nan`; a floating disconnected input can produce plausible readings, so the channel-identification check still matters.

## Stage 2 — Python acquisition GUI

```bash
/opt/anaconda3/envs/phys39a/bin/python code/module7/module_07_rod_acquisition_gui.py --label common_bath
```

[module_07_rod_acquisition_gui.py](module_07_rod_acquisition_gui.py) is a copy of the Module 6 P/PI GUI. The Module 6 file is unchanged. It reuses the Module 5 window and serial helpers and the Module 6 `PIController`.

- Parses only complete `DATA` lines. The header is ignored. Other or malformed lines are counted as rejected and never stop the program.
- Shows one combined plot of all six raw temperatures against Arduino time. The TEC trace is thick black, and a checkbox hides each trace. It also shows live numbers for all six channels and the live spread T_max − T_min, which turns green below 1 °C.
- Only the TEC channel (A1) enters the PI law. All Module 6 controls, the PWM limit, stop/zero-integral and zero-output stopping are kept.
- Every accepted record is written raw to a **new** `data/module_07/rod_raw_[label_]YYYYmmdd_HHMMSS.csv` (opened with `'x'`, never overwritten) and flushed each line. Columns: `time_s,tec_C,rod1_C..rod5_C,pwm,heat_cool,setpoint_C,safety`. `setpoint_C` is the GUI setpoint while control runs, otherwise `nan`.

## Stage 3 — Common-bath check

Keep TEC power **off**. Put all six sensing ends together in hot water in a Styrofoam cup, kept below about 60 °C. Do not let them touch the walls or bottom, and keep the thermocouple nearby. Log continuously with the GUI. At each of several temperatures as the water cools: stir, let it settle, note the time window and the thermocouple reading. Then run:

```bash
python code/module7/common_bath_check.py data/module_07/rod_raw_common_bath_....csv              # pick windows
python code/module7/common_bath_check.py FILE --window 120 180 --window 600 660 --tc 52.1 --tc 41.8
```

It prints the six window means and their spread with PASS/FAIL against 1 °C. It saves a table and a figure to `docs/figures/module_07/`. If every spread is < 1 °C, use the raw data and add no Record/Pause code. Record results in [module_07_rod_instrument.md](../../docs/module_notes/module_07_rod_instrument.md).

**Verified in software:** Uno compilation passed (6,714 bytes flash; 304 bytes static RAM). Simulated-I/O checks passed for record format, startup, commands, pin direction, A0 overheat/fault/recovery, rod-only faults, timeout, and zero command. The original sketch is unchanged. **Upload, wiring, sensor identity, and real-board safety checks remain to be verified at the bench.**
