# S18.3 — Model–experiment comparison at 100 s

**Lab step:** lab-09, Stage 2, S18.3 "Compare The Simulation With Your Measurements": "Compare their settled means, fundamental amplitudes, and phase lags relative to PWM. Use sinusoidal-fit residuals to assess waveform distortion."

**Model inputs (measured):** room 22 °C, initial 22.81 °C (first record of the run), χh = 0.5311 and χc = 0.1878 °C/PWM (Module 4), τ = 91.69 s (Module 6), u_b = 50, period 100 s. Settled cycle t = 600–700 s.

| | Mean − room (°C) | Fundamental amplitude (°C) | Phase lag behind PWM (°) | Residual amplitude (°C) |
|---|---|---|---|---|
| Measured | 5.92 | 4.23 | 69.9 | 0.45 |
| Model, τ = 91.69 s | 5.46 | 3.07 | 80.2 | 0.31 |
| Model, τ = 43 s (best lag match, extra) | 5.46 | 6.24 | 69.7 | 0.66 |

**Code:** `python code/module8/s18_3_model_vs_experiment.py <100 s run> --room 22`
**Figure:** `docs/figures/module_08/s18_3_model_vs_experiment_100s.png`
