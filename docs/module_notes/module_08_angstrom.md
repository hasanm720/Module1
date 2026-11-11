# Module 8 — Angstrom method: run notes

Evidence folders: `data/module_08/`, `docs/figures/module_08/`. Code: `code/module8/`.

## Carried over from Module 7

Origin at the T1 hole, channel assignments, common-bath result (spread 0.45 °C, no corrections), d = 12.705 ± 0.025 mm, L = 283.2 ± 2 mm. See `module_07_rod_instrument.md`.

## Oscillatory sensor map

Positions from Module 7 section 1; sensors not moved for Module 8 (spacing judged acceptable by eye, Nov 4).

| Tag | x (mm) | u(x) (mm) | CSV column |
|---|---|---|---|
| T1 | 0 | ±0.5 | `T1_C` |
| T2 | 50.30 | ±0.5 | `T2_C` |
| T3 | 100.96 | ±0.5 | `T3_C` |
| T4 | 150.32 | ±0.5 | `T4_C` |
| T6 | 200.95 | ±0.5 | `T5_C` |

## Run log

| Date | File | Mode | Ta / Tb (°C) | Period (s) | Kp / Ki | Room (°C) | Notes |
|---|---|---|---|---|---|---|---|
| Nov 4 | `angstrom_raw_open_40_16_100_20261104_094810.csv` | OPEN | 40 / 16 | 100 | — | 26 | ran the full 1800 s, ended DONE, no faults |
| Nov 4 | `angstrom_raw_P_40_16_100_20261104_102713.csv` | P | 40 / 16 | 100 | 16 / 0 | 26 (not re-read) | 600 s, ended DONE, no faults. Separate file from the open-loop trial because the GUI was relaunched |
| Nov 4 | `angstrom_raw_PI_40_16_100_20261104_105054.csv` | PI | 40 / 16 | 100 | 16 / 0.5 | 26 (not re-read) | 600 s, ended DONE, no faults |
| Nov 4 | `angstrom_raw_PI_settled_100_240_20261104_111340.csv` | PI | 40 / 16 | 100 then 240 | 16 / 0.5 | 26 (not re-read) | 600 s + 1200 s, shortened from 70 min at the user's request, ended DONE, no faults. Phase continuous at the switch (t = 605.5 s) |

## Trial 1: open loop, 40 ± 16 °C, 100 s (Nov 4)

Fit: last 5 cycles, t = 1305–1804 s (`code/module8/fit_sinusoids.py`). Figure and numbers: `docs/figures/module_08/angstrom_raw_open_40_16_100_20261104_094810_fit_100s.*`.

| Sensor | Mean (°C) | Drift (°C/min) | B (°C) | φ (rad) | B / residual sd |
|---|---|---|---|---|---|
| TEC | 44.59 | +0.022 | 3.582 | −3.12 | 190 |
| T1 | 41.03 | +0.053 | 1.168 | −3.90 | 47 |
| T2 | 38.45 | +0.067 | 0.401 | −4.92 | 11 |
| T3 | 36.37 | +0.078 | 0.145 | −5.94 | 3.4 |
| T4 | 35.36 | +0.085 | 0.049 | −6.76 | 1.2 |
| T6 | 34.30 | +0.092 | 0.007 | −7.24 | 0.2 |

- **Preliminary, T1–T3 only:** q = 20.7 m⁻¹, q′ = 20.2 rad/m, κ = 7.5 × 10⁻⁵ m²/s, ν = 1.35 × 10⁻³ s⁻¹. Planning values: κ = 6.90 × 10⁻⁵, ν = 1.30 × 10⁻³. No uncertainties yet.
- **Boundary tracking is poor in open loop:** requested ±16 °C about 40 °C; the TEC gave ±3.6 °C about 44.6 °C.
- **T4 looks usable, T6 does not, at this period.** Extending the T1–T3 line to T4 predicts B = 0.052 °C and φ = −6.93 rad; T4 measured 0.049 °C and −6.76 rad. Its low B/sd comes mostly from leftover slow drift, not random noise. For T6 the line predicts 0.018 °C and −7.96 rad; it measured 0.007 °C and −7.24 rad, so its signal is too small.
- **Not fully settled:** means still drifted +0.05 to +0.09 °C/min.

## Trial 2: P-only, Kp = 16, 40 ± 16 °C, 100 s (Nov 4)

Fit: 5 cycles, t = 105–605 s. Figure and numbers: `docs/figures/module_08/angstrom_raw_P_40_16_100_20261104_102713_fit_100s.*`.

| Sensor | Mean (°C) | Drift (°C/min) | B (°C) | φ (rad) |
|---|---|---|---|---|
| TEC | 38.48 | +0.021 | 12.763 | −2.25 |
| T1 | 36.00 | +0.109 | 4.251 | −3.03 |
| T2 | 34.13 | +0.163 | 1.466 | −4.04 |
| T3 | 32.57 | +0.195 | 0.502 | −5.06 |
| T4 | 31.92 | +0.208 | 0.164 | −6.03 |
| T6 | 31.12 | +0.208 | 0.051 | −7.19 |

- **Preliminary, T1–T4:** q = 21.6 m⁻¹, q′ = 20.0 rad/m, κ = 7.3 × 10⁻⁵ m²/s, ν = 4.8 × 10⁻³ s⁻¹. κ agrees with trial 1 (7.5 × 10⁻⁵). ν does not (1.35 × 10⁻³). ν depends on the small difference q² − q′², so it is very sensitive, and this run was still warming.
- **Tracking:** TEC ±12.8 °C about 38.5 °C. RMS error from the setpoint 4.7 °C, max 8.2 °C. The TEC lags the setpoint by about 0.68 rad (11 s). PWM −207 to +130, never clipped.

## Trial 3: PI, Kp = 16, Ki = 0.5, 40 ± 16 °C, 100 s (Nov 4)

Fit: 5 cycles, t = 104–604 s. Figure and numbers: `docs/figures/module_08/angstrom_raw_PI_40_16_100_20261104_105054_fit_100s.*`.

| Sensor | Mean (°C) | Drift (°C/min) | B (°C) | φ (rad) |
|---|---|---|---|---|
| TEC | 40.01 | +0.003 | 15.343 | −2.30 |
| T1 | 36.99 | +0.154 | 5.150 | −3.07 |
| T2 | 34.73 | +0.255 | 1.777 | −4.09 |
| T3 | 32.86 | +0.320 | 0.606 | −5.11 |
| T4 | 32.00 | +0.356 | 0.197 | −6.08 |
| T6 | 31.04 | +0.368 | 0.057 | −7.27 |

Preliminary, T1–T4: q = 21.65 m⁻¹, q′ = 20.01 rad/m, κ = 7.25 × 10⁻⁵ m²/s, ν = 4.96 × 10⁻³ s⁻¹. Not settled: rod means still rising 0.15–0.37 °C/min.

## Step 7: comparison of control modes (40 ± 16 °C, 100 s, last 500 s of each run)

| | Open loop | P (Kp 16) | PI (16, 0.5) |
|---|---|---|---|
| TEC mean (target 40 °C) | 44.59 | 38.48 | **40.01** |
| TEC amplitude (target 16 °C) | 3.58 | 12.76 | **15.34** |
| TEC phase lag behind setpoint (rad) | 1.55 | 0.68 | 0.73 |
| RMS / max tracking error (°C) | 11.8 / 19.9 | 4.7 / 8.2 | 4.8 / **6.9** |
| TEC peak high / low (°C) | 48.2 / 40.9 | 51.4 / 25.8 | 55.6 / 24.9 |
| 2nd harmonic / fundamental, TEC | 0.004 | 0.021 | 0.026 |
| 2nd harmonic / fundamental, T1 | 0.003 | 0.015 | 0.017 |
| T1 mean / amplitude (°C) | 41.03 / 1.17 | 36.00 / 4.25 | 36.99 / **5.15** |
| Applied PWM range | 4 to 64 | −207 to +130 | −249 to +156 |
| Samples clipped at ±255 | 0 | 0 | 0 |

**Decision: use PI.** It gives the correct mean and the largest boundary amplitude, with low distortion (about 2–3% second harmonic), and no clipping. The cost is that cooling PWM reaches −249, close to the limit. Most of the remaining tracking error is the 0.7 rad lag, which does not matter for the Angstrom fit, because the fit uses T1 as the measured boundary.

## Trial 4: PI, two periods in one run (Nov 4)

Figures and numbers: `docs/figures/module_08/angstrom_raw_PI_settled_100_240_20261104_111340_fit_*`. The `_fit_240s` files are the last-3-cycle fit.

**240 s, last 3 cycles (t = 1084–1804 s), all five rod sensors:**

| Sensor | Mean (°C) | Drift (°C/min) | B (°C) | φ (rad) | B / residual sd |
|---|---|---|---|---|---|
| TEC | 40.00 | +0.003 | 16.514 | 1.27 | 160 |
| T1 | 37.99 | +0.006 | 7.725 | 0.73 | 133 |
| T2 | 36.40 | +0.006 | 3.807 | 0.08 | 123 |
| T3 | 35.01 | +0.009 | 1.860 | −0.57 | 73 |
| T4 | 34.51 | +0.011 | 0.891 | −1.22 | 36 |
| T6 | 33.77 | +0.012 | 0.431 | −1.99 | 16 |

q = 14.39 m⁻¹, q′ = 13.44 rad/m, **κ = 6.77 × 10⁻⁵ m²/s, ν = 1.79 × 10⁻³ s⁻¹** (no uncertainties yet). Using ρ = 2700 kg/m³, c = 896 J/kg·K (Lienhard Table A.1): k = ρcκ ≈ 164 W/m·K (table 167), and h = νρcd/4 ≈ 13.8 W/m²K. m = √(q² − q′²) ≈ 5.1 m⁻¹.

**Settling at 240 s:** cycle-by-cycle fits show cycle 1 still carries the transient from the period change (T3 B = 1.60 °C, then 1.85–1.89 °C; T6 B = 0.61 °C, then 0.43–0.47 °C). Cycles 2–5 agree within about 3–10%, with means changing ≤ 0.1 °C per cycle. So this run has **about 4 settled cycles at 240 s, one short of the required 5**.

**100 s, 5 cycles (t = 106–606 s):** q = 21.62 m⁻¹, q′ = 20.28 rad/m, κ = 7.17 × 10⁻⁵ m²/s, ν = 4.0 × 10⁻³ s⁻¹. **Not settled:** rod means rising 0.15–0.38 °C/min, because the rod started from about 29 °C. Do not use this interval for the final ν.

Settling criterion for the production run still needs to be chosen and stated.

## Production plan (Stage 5), updated Nov 9

- Lab-09 was rewritten. S18.10: "Candidate periods are 100, 200, 300, 400, and 500 seconds." The earlier 240 s runs are not on the list and are kept as pilot data only.
- **Period 1, 200 s:** Nov 9, 10 cycles (2000 s), fixed duration. The settling test (`code/module8/settle_check.py`) is applied afterwards.
- **Period 2, 500 s (user's choice, Nov 9):** next class, the same 10 cycles, which is 5000 s ≈ 83 min. Launch with `--hold` on the new sketch (HOLD/NEXT, upload first) so the step can be extended if the settling test has not passed.
- Settling test: |Δmean| ≤ 0.10 °C, |ΔB|/B ≤ 5 %, |Δφ| ≤ 0.05 rad between successive cycles (TEC, T1–T4, plus T6 if B ≥ 0.1 °C); settled after 2 passes, then retain 5 cycles.

## Production period 1: PI, 200 s, 10 cycles (Nov 9)

File: `data/module_08/angstrom_raw_production_200_20261109_111833.csv` (2000 s, ended DONE, no faults). Room ≈ 26 °C from the six sensors at idle before the start. Earlier the same day, a 240 s attempt (`angstrom_raw_production_240_400_20261109_103824.csv`) was stopped by the user at 28 min; it is not an allowed period.

**Settling test (`settle_check.py`): NOT met.** No two consecutive cycle comparisons passed.

- **Mean:** settled by cycles 6–8 (Δmean 0.04, 0.01 °C).
- **Amplitude at T4 and T6 (±0.6 and ±0.27 °C):** scatter of 10–35 % between cycles.
- **Electrical reference shifts:** all six channels stepped about +0.4 °C together at t ≈ 1622 s and back about −0.47 °C at t ≈ 1993 s, with no change in PWM. This is likely the shared 5 V rail, not heat. It disturbs cycles 8–10. Check the breadboard 5 V wiring and the H-bridge VCC before the next run.
- **T1–T3 only:** amplitude still changed 4–11 % per cycle, so it also fails at 5 %.

**Reference fit, cycles 5–9 (t = 805–1804 s), not a settled interval:** drift ≤ 0.02 °C/min. q = 15.98 m⁻¹, q′ = 14.70 rad/m, κ = 6.69 × 10⁻⁵ m²/s, ν = 2.6 × 10⁻³ s⁻¹ (T1–T6). Figure: `docs/figures/module_08/angstrom_raw_production_200_20261109_111833_fit_200s.png`.

## Production period 2: PI, 500 s, Hold on (Nov 11)

File: `data/module_08/angstrom_raw_production_500_20261111_092817.csv`. HOLD/NEXT sketch uploaded and checked on the board before the run. Room ≈ 23 °C (sensors at idle). The 5 V wiring was re-seated before the run.

- **Ended unexpectedly after 62.4 min (7.5 cycles)**, when the Claude Code session ended and closed the GUI. The Arduino's 2 s heartbeat timeout turned the TEC off. The log's last record is still RUN.
- **No common-mode jumps** this time (none > 0.25 °C), so the Nov 9 reference shifts were most likely the 5 V wiring.
- **Settling test:**
  - The mean passed from cycle 6 (0.098, then 0.062 °C).
  - With TEC + T1–T4, cycles 6 and 7 passed, so it was **settled after cycle 7 with 0/5 retained** when the run ended.
  - With T6 included it never passed: T6 cycle-to-cycle ΔB 4–6 %, Δφ up to 0.075 rad.
- **Open decision:** whether the settling test uses TEC + T1–T4 (≥ 3 rod sensors, as the page requires) with T6 kept in the fits.
- **Reference fit, cycles 3–7 (t = 1005–3504 s), not a settled interval:** drift ≤ 0.015 °C/min, all six channels B/sd ≥ 11. q = 9.95 m⁻¹, q′ = 9.85 rad/m, κ = 6.41 × 10⁻⁵ m²/s, ν = 1.3 × 10⁻⁴ s⁻¹. Fitting only the last 2 cycles gives q′ ≥ q (ν ≈ −1 × 10⁻⁵), which lab-09 calls "evidence to investigate". At 500 s, ν is poorly determined from q and q′ alone. Figure: `docs/figures/module_08/angstrom_raw_production_500_20261111_092817_fit_500s.png` (cycles 3–7).
