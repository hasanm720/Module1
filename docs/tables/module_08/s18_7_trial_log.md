# S18.7 — P and PI trial log

**Lab step:** lab-09, Stage 3, S18.7 "Repeat With P And PI Control": "Use the table below as a trial log. Start with the P-only and initial PI runs at 100 s using the same K_p." "Add a row for each gain pair you test."

**Units:** K_p in PWM counts per °C; K_i in PWM counts per (°C·s). Error e = T_set − T_TEC; cooling commands × r = χh/χc = 2.83 before the ±255 clamp; anti-windup in PI.

**Requested drive:** T_set = 40 + 16 sin(2πt/τ). **Metrics:** common time fit over the last 3 complete cycles; amplitude ratio = fitted TEC amplitude / 16 °C; phase lag of the TEC behind the setpoint; RMS of T_TEC − T_set over the same interval. **Tolerances (team, also reported in S18.8):** |mean − 40| ≤ 1 °C, amplitude ratio 0.90–1.10, |phase lag| ≤ 20°.

| Period (s) | Trial | K_p | K_i | Sample interval (s) | Mean TEC (°C) | Amplitude ratio (fitted / requested) | Phase lag (°) | RMS tracking error (°C) | PWM saturation | Run link and notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | P only | 16 | 0 | 0.68 | 38.10 | 0.791 | 22.2 | 4.92 | yes: 5 samples (5 in start-up), 0–3 s | [angstrom_raw_s18_7_100_P_20261123_100206.csv](../../../data/module_08/angstrom_raw_s18_7_100_P_20261123_100206.csv); misses tolerances |
| 100 | Initial PI | 16 | 0.5 | 0.68 | 40.00 | 0.950 | 25.3 | 4.88 | yes: 2 samples (2 in start-up), 1–2 s | [angstrom_raw_s18_7_100_PI1_20261123_102111.csv](../../../data/module_08/angstrom_raw_s18_7_100_PI1_20261123_102111.csv); misses tolerances; same Kp as P only |
| 100 | PI tuning trial | 25 | 0.5 | 0.68 | 40.00 | 0.944 | 17.2 | 3.35 | yes: 6 samples (6 in start-up), 0–3 s | [angstrom_raw_s18_7_100_PI2_20261123_103545.csv](../../../data/module_08/angstrom_raw_s18_7_100_PI2_20261123_103545.csv); meets tolerances; **SELECTED for 100 s**; Kp raised 16→25 to cut the lag |

**Figure:** [s18_7_trials.png](../../../docs/figures/module_08/s18_7_trials.png)
