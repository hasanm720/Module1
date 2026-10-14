# Module 6 Part 4 — Results

## 1. Heating and cooling

Resistive heat is produced in both directions. It helps heating but reduces
cooling, so +25 PWM heats more than −25 PWM cools.

Default settings: measured mode, ambient/initial temperature 22 °C,
τ = 80 s, Δt = 0.05 s. Predict T_ss = T_amb + χu.

| PWM | Predicted T_ss (°C) | Simulated at 1200 s (°C) | χ (°C/PWM) |
|---:|---:|---:|---:|
| +25 | 33.500 | 33.500 | 0.46000 |
| -25 | 16.250 | 16.250 | 0.23000 |
| -50 | 10.500 | 10.500 | 0.23000 |

Calculate χ = (T_ss − T_amb)/u:

- χ_h = (33.5 − 22)/25 = **0.46 °C/PWM**.
- χ_c = (16.25 − 22)/(−25) = **0.23 °C/PWM**.
- At −50 PWM: χ_c = (10.5 − 22)/(−50) = **0.23 °C/PWM**.
- Ratio r = 0.46/0.23 = **2**.

These agree with the simulation's displayed susceptibilities.

![Open-loop cases](results/01_default_open_loop.png)

## 2. Double thermal capacitance

Keep **+25 PWM** fixed. Select `direct constants` and double C from
**130.946 to 261.893 J/°C**.
Leave H, P_u,c, and r unchanged.

**Prediction:** T_ss stays at **33.5 °C**; τ = C/H doubles from **80 to 160 s**.
**Simulation:** both predictions agree.

More thermal mass needs more energy to change temperature, so the response is
slower. At steady state, heat entering equals heat leaving; C does not change
that balance or the final temperature.

Return to `measured` for the following runs.

![Double thermal capacitance](results/02_double_thermal_mass.png)

## 3. Experimental settings

Use **+5 PWM heating** and **−47 PWM cooling**, matching the recordings.
TEC voltage: **12 V** (assumed ON-state value). TEC resistance: **1.50 Ω**.

| Setting | Heating | Cooling |
|---|---:|---:|
| Ambient | 24.220 °C | 21.965 °C |
| Initial temperature | 24.210 °C | 9.940 °C |
| χ | 0.5311 °C/PWM | 0.1878 °C/PWM |

| Parameter | Value |
|---|---:|
| C | 100.549 J/°C |
| H | 1.0966 W/°C |
| P_u,c | 0.20595 W/PWM |
| r | 2.8280 (dimensionless) |
| τ | 91.69 s |
| Δt | 0.05 s |

χ comes from Module 4; τ comes from Part 3 heating and is used for both directions.
The physical constants use the voltage above.

## 4. Simulation versus experiment

| Run | Predicted T_ss | Measured final-60-s mean |
|---|---:|---:|
| Heating, +5 PWM | 26.875 °C | 26.366 °C |
| Cooling, −47 PWM | 13.138 °C | 13.472 °C |

Heating is predicted 0.510 °C too high; full-trace RMSE
is 0.498 °C. The heating trace supplied τ, so its response-time
agreement is not an independent test.

The cooling trace warms because it starts below the steady temperature for
−47 PWM. Heat entering from the surroundings initially exceeds TEC cooling.

The model assumes uniform temperature and constant conditions. Temperature
gradients, changing ambient temperature, and changing thermal contact or TEC
performance can explain the differences; these data do not identify the main cause.

![Simulation and measured traces](results/03_experiment_comparison.png)

## 5. Time-step check

**Δt = 0.05 s ≪ τ = 91.69 s.** Halving Δt to 0.025 s changes the heating
prediction by at most **0.000134 °C**, well below the 0.01 °C reporting
increment. The result does not appreciably change.

## 6. P control

Select `p`; keep the measured parameters, initial temperature, and **30 °C** target.
Use **Kp = 10 from Module 5**, then **Kp = 20**; Ki = 0.

Before each run, predict:

$$\mathrm{droop}=\frac{T_{set}-T_{amb}}{1+\chi_hK_p},
\qquad \tau_{cl}=\frac{\tau}{1+\chi_hK_p}.$$

- **Kp=10, Ki=0:** predicted droop 0.916 °C, time constant 14.53 s, and final temperature 29.084 °C.
- **Kp=20, Ki=0:** predicted droop 0.497 °C, time constant 7.89 s, and final temperature 29.503 °C.

**Both predictions agree with the simulation:** final temperatures agree within
0.00001 °C, and the simulated curves differ from the predicted exponential by
less than 0.01 °C. Increasing Kp reduces both droop and response time.
Droop is the final temperature shortfall below the target.

![P-control comparison](results/04_p_control.png)

## Reproduce

```sh
python PHYS39A_instrumentation/code/module6/Part1/P4_Simulate_open_loop_control/run_part4.py --voltage 12
```

- [Simulation](Lab_6_7_modeling_tec.py) · [Runner](run_part4.py)
- [Heating data](../P3_estimate_tau/data/open_loop_step_20261013_113417_759949.csv)
- [Cooling data](../../../module4/P1_Shutdown_Control/tec_safety_data.csv)
- [Module 4 fits](../../../../docs/other_files/module4/P4_Temperature_susceptibility/susceptibility_results.md)
