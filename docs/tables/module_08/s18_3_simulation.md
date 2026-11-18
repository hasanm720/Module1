# S18.3 — Simulate the time-varying temperature (one-lump model)

**Lab step:** lab-09, Stage 2, S18.3 "Simulate the time-varying temperature": for each row, "set the period and χc, click Apply / Reset, then Run", and read the "Settled response".

**Model settings (page):** room = initial = 22 °C, τ thermal = 80 s, χh = 0.46 °C/PWM, u_a = 0, u_b = 50 (our selected amplitude). Residual = simulated T minus its fitted mean and fundamental; residual amplitude = half its peak-to-peak range.

| Period (s) | χc (°C/PWM) | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag (°) | (4) Residual amplitude (°C) |
|---|---|---|---|---|---|
| 100 | 0.23 | 3.660 | 3.366 | 78.8 | 0.240 |
| 100 | 0.46 | 0.005 | 4.488 | 78.7 | 0.003 |
| 200 | 0.23 | 3.661 | 6.377 | 68.3 | 0.473 |
| 200 | 0.46 | 0.002 | 8.503 | 68.3 | 0.002 |
| 300 | 0.23 | 3.661 | 8.840 | 59.2 | 0.695 |
| 300 | 0.46 | 0.000 | 11.787 | 59.2 | 0.000 |

**How it was run:** the simulator's lumped mode, reproduced from its page source (same equation, RK4 at 0.01 s, settled cycle after 5τ). The 300 s, χc = 0.46 row was checked against the browser simulator: 11.787 °C and 59.2°, an exact match.
**Code:** [s18_3_onelump_sim.py](../../../code/module8/s18_3_onelump_sim.py) — run: `python code/module8/s18_3_onelump_sim.py --ub 50`
**Figure:** [s18_3_onelump_model.png](../../../docs/figures/module_08/s18_3_onelump_model.png)
