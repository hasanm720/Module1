# Part 7 — PI control and Goldilocks results

## Controller

Error e = setpoint − temperature; q_new = q + eΔt;
requested PWM = Kp e + Ki q. Δt uses actual measurement times.
Anti-windup holds q if adding error pushes the request farther beyond ±255.
Applied PWM is clamped and rounded. The Arduino shutdown and timeout remain active.

q was reset before each run, with PWM zero first. It was not reset between steps.
Temperature, error, P, I, requested PWM, and applied PWM were recorded.

## Settings

Same apparatus, **28 → 30 → 28 °C**, **PWM limit ±255**, anti-windup on.
Sample interval: **≈0.57 s**. Each run: **10 s baseline + 40 s upward + 40 s downward**.
End temperatures below average each step's final 5 s; **full settling is unconfirmed**.

| Run | Mode | Kp | Ki | End at 30 °C target | End at 28 °C target |
|---|---|---:|---:|---:|---:|
| 1 | P | 5 | 0 | 27.36 °C | 26.44 °C |
| 2 | P | 20 | 0 | 29.27 °C | 27.51 °C |
| 3 | P | 40 | 0 | 29.63 °C | 27.73 °C |
| 4 | PI | 16 | 0.1 | 29.33 °C | 27.63 °C |
| 5 | PI | 16 | 0.5 | 29.94 °C | 27.84 °C |
| 6 | PI | 16 | 2 | 29.94 °C | 27.91 °C |

Kp: PWM/°C. Ki: PWM/(°C·s).

## Answers

- **Increasing Kp:** faster P responses and smaller errors. High-gain P did not show clear overshoot or ringing.
- **Increasing Ki:** faster integral correction, then more overshoot. Run 5 was the best observed PI compromise. Run 6 overshot by **0.76 °C** upward and undershot by **0.86 °C** downward.
- **Integral contribution:** in Run 5's upward step, I grew from **3.52 to 15.46 PWM**. Final recorded error was **0.05 °C**, versus **0.70 °C** for Run 2. These are end-of-step errors, not verified steady-state errors.
- **Saturation:** none. Maximum absolute applied PWM was **90**, below **255**. Overshoot does not mean saturation.

Starting temperatures differed and were recorded:

| Run | Upward-step start (°C) | Downward-step start (°C) |
|---|---:|---:|
| 1 | 25.13 | 27.41 |
| 2 | 27.34 | 29.29 |
| 3 | 27.75 | 29.65 |
| 4 | 27.41 | 29.34 |
| 5 | 27.46 | 29.95 |
| 6 | 27.59 | 29.92 |

## Figures

Each figure shows measured temperature, setpoint, signed PWM, P, I, and error.

**Run 1 — Low-gain P**

![Run 1](results/run1.png)

**Run 2 — Intermediate-gain P**

![Run 2](results/run2.png)

**Run 3 — High-gain P**

![Run 3](results/run3.png)

**Run 4 — Low-Ki PI**

![Run 4](results/run4.png)

**Run 5 — Intermediate-Ki PI**

![Run 5](results/run5.png)

**Run 6 — High-Ki PI**

![Run 6](results/run6.png)

[Raw recordings](data/) · [Controller](pi_logic.py) · [GUI](pi_control_gui.py) · [Plotter](plot_goldilocks.py)
