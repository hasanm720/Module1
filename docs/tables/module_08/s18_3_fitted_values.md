# S18.3 — Table of fitted values (measured)

**Lab step:** lab-09, Stage 2, S18.3 "Apply Zero-Centered Sinusoidal PWM": "Make a table of the fitted values."

**Data:** zero-centered sinusoidal PWM, u = 50 sin(ωt), room 22 °C, Nov 16, 2026. The TEC temperature is fitted with a sine over the last 3 complete cycles of each run. The phase lag is how far the TEC temperature trails the PWM.

| Period (s) | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag (°) |
|---|---|---|---|
| 100 | 5.81 | 4.24 | 71.4 |
| 200 | 5.56 | 7.07 | 59.3 |
| 300 | 5.43 | 9.07 | 50.4 |

**Raw data:** `data/module_08/angstrom_raw_s18_3_zero_100_20261116_110514.csv`, `..._zero_200_20261116_104018.csv`, `..._zero_300_20261116_100920.csv`
**Code:** `python code/module8/s18_3_analysis.py --room 22 <300 s> <200 s> <100 s>`
**Figure:** `docs/figures/module_08/s18_3_zero_centered_pwm.png`
