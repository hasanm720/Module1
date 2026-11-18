# S18.4 — Experiment table: zero-centered vs positive-only PWM (100 s drive)

**Lab step:** lab-09, Stage 2, S18.4 "Apply Positive-Only Sinusoidal PWM": "Fill in the table using your S18.3 baseline and S18.4 trial. Take residual amplitude as half the residual's peak-to-peak range."

**Data:** 100 s drive period (one wave every 100 s). Common time fit (mean + drift + fundamental) over the last 3 complete cycles of each run. The u_a and u_b values are fitted from the recorded PWM.

| 100 s drive | u_a (PWM) | u_b (PWM) | Fundamental amplitude (°C) | Residual amplitude (°C) |
|---|---|---|---|---|
| Zero-centered | 0 | 50 | 4.24 | 0.54 |
| Positive-only | 34 | 30 | 3.53 | 0.07 |

- u_b was lowered from 50 to 30 for the positive-only run (user's choice, Nov 18). With PWM kept positive and u_b = 50, the TEC mean would have been about 49 °C, not near 40 °C. The measured positive-only TEC mean was **40.27 °C**.
- Room 22 °C (S18.3); about 23 °C from the idle sensors on Nov 18.

**Raw data:** `data/module_08/angstrom_raw_s18_3_zero_100_20261116_110514.csv` (zero-centered), `data/module_08/angstrom_raw_s18_4_positive_100_20261118_101610.csv` (positive-only)
**Figure:** `docs/figures/module_08/s18_4_experiment.png`
