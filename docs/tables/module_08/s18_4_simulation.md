# S18.4 — Simulation table: zero-centered vs positive-only PWM (100 s drive)

**Lab step:** lab-09, Stage 2, S18.4: "Simulate both 100 s drives using the applied u_a and u_b from the experimental table. Use the same measured room temperature, susceptibilities, and thermal time constant for both simulations."

**Model:** one-lump TEC (the course simulator's lumped mode), room = start = 22 °C, χh = 0.5311 and χc = 0.1878 °C/PWM (Module 4), τ = 91.69 s (Module 6), the same for both runs. Settled cycle read after 5τ.

| 100 s drive | u_a (PWM) | u_b (PWM) | Fundamental amplitude (°C) | Residual amplitude (°C) |
|---|---|---|---|---|
| Zero-centered | 0 | 50 | 3.07 | 0.31 |
| Positive-only | 34 | 30 | 2.72 | 0.01 |

**Figure:** `docs/figures/module_08/s18_4_simulation.png`
