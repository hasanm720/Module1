# S18.6 — Feedforward prediction vs measured response (100 s drive)

**Lab step:** lab-09, Stage 3, S18.6 "Apply the Feedforward Command": "Record the calculated and applied PWM settings and compare the measured mean and amplitude with the predictions from the steady-state calibration."

**Data:** u = 33.9 + 30.1 sin(ωt), 100 s period, no P or I feedback, 10 cycles. Common time fit (mean + drift + fundamental) over the last 3 complete cycles (t = 700–1000 s, TEC drift +0.04 °C/min). The phase lag is the TEC's lag behind the setpoint.

| 100 s case | u_a (PWM) | u_b (PWM) | Mean TEC temperature (°C) | Oscillation amplitude (°C) | Phase lag relative to setpoint (°) |
|---|---|---|---|---|---|
| S18.5 steady-state prediction | 33.9 | 30.1 | 40.00 | 16.00 | 0 |
| S18.6 measured response | 33.9 | 30.1 | 41.49 | 3.67 | 71.4 |

**Raw data:** [angstrom_raw_s18_6_feedforward_100_20261118_110221.csv](../../../data/module_08/angstrom_raw_s18_6_feedforward_100_20261118_110221.csv)
**Figure:** [s18_6_feedforward_response.png](../../../docs/figures/module_08/s18_6_feedforward_response.png)
