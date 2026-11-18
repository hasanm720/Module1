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

## Production 500 s run 2 and 100 s run (Nov 11)

- `angstrom_raw_production_500_run2_20261111_105221.csv`: a restart at 500 s, stopped by the user after about 15 min to switch to 100 s because of class time. Not usable for settling.
- `angstrom_raw_production_100_20261111_110713.csv`: PI, 40 ± 16 °C, 100 s, 18 cycles (1800 s), ended DONE, no faults, no common-mode jumps. The rod started warm from the 500 s run.
  - **Settling test (noise-scaled limits): not met.** With TEC + T1–T3 it reached "settled, 1/5 retained" at cycle 14, then reset at cycle 16 on a real 0.18 °C mean jump (not electrical).
  - T3's per-cycle fits are very clean (residual sd ≈ 0.009 °C), yet its amplitude varies ±4–6 % and its phase up to 0.12 rad from cycle to cycle with no trend. This is random physical wobble (probably room air), not drift, and not covered by fit-noise limits.
  - PWM figure: `docs/figures/module_08/angstrom_raw_production_100_20261111_110713_pwm.png`. PWM −233 to +168, never clipped.
- **Proposed:** replace the cycle-to-cycle limits with a no-trend test (linear slope of mean, B and φ over the retained cycles, compared with their scatter). Awaiting the user's decision.
- **Page changed again (Nov 11):** Stage 5 now asks for production data at all five periods (100, 200, 300, 400, 500 s); S18.3 now starts at 300 s with u_b = 50; S18.7 tests 100/200/300 s; S18.5 defines feedforward as u₀ = (T_set − T_room)/χh with negatives × r (ours used the Module 4 lookup table). A5 due Mon Nov 23, 9:05 AM (official once posted in Moodle).

## Next class (user's note, Nov 11)

1. **Read the text parts of lab-09** (instructions, what to produce, what to save). The math derivations can be skipped for now.
2. **First bench step: Stage 2, S18.3, zero-centered sinusoidal PWM.** u(t) = u_a + u_b sin(ωt) with u_a = 0, u_b = 50 PWM counts (page's initial value), PWM limits −255 to +255. Start at **300 s**, then keep the same u_b for **300, 200 and 100 s**. Record PWM and all six temperatures. The page asks: "Plot the measured TEC temperature and signed PWM on aligned time axes."
   - **Software needed first:** the sketch has no direct sinusoidal-PWM mode yet (OPEN uses the temperature lookup table). Add a `PWM` mode with u_a and u_b, then sim-test it before the run.
3. Then S18.4, positive-only PWM at 100 s (choose u_a for a TEC mean near 40 °C, same u_b).

## Stage 2, S18.3: zero-centered sinusoidal PWM (Nov 16)

- Room temperature **22 °C** (user's measurement). All six sensors read 22.0–22.3 °C before the start.
- New sketch with `MODE PWM` uploaded and checked on the board. The board's port is now `/dev/cu.usbmodem1101`.
- **Run 1:** u_a = 0, u_b = 50, period 300 s, 8 cycles (2400 s). File: `data/module_08/angstrom_raw_s18_3_zero_300_20261116_100920.csv`.
- **Run 2:** 200 s, 6 cycles: `data/module_08/angstrom_raw_s18_3_zero_200_20261116_104018.csv` (ended DONE).
- **Run 3:** 100 s, 8 cycles: `data/module_08/angstrom_raw_s18_3_zero_100_20261116_110514.csv` (ended DONE).
- Run 1 (300 s) was shortened to 6 cycles; the TEC cycle was already repeating after cycle 3.

**S18.3 table** (room 22 °C; fit of the last 3 complete cycles; `code/module8/s18_3_analysis.py`; figure `docs/figures/module_08/s18_3_zero_centered_pwm.png`):

| Period (s) | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag behind PWM (°) | Residual amplitude (°C) |
|---|---|---|---|---|
| 300 | 5.43 | 9.07 | 50.4 | 1.19 |
| 200 | 5.56 | 7.07 | 59.3 | 0.93 |
| 100 | 5.81 | 4.24 | 71.4 | 0.54 |

- The mean sits about 5.5 °C above room even though the PWM averages zero. Heating is stronger than cooling (χh > χc), so the "absolute-value" term in the page's decomposition shifts the mean up.
- Faster drive gives a smaller amplitude and a larger lag, as the one-lump low-pass model predicts. tan(lag)/ω gives τ_th ≈ 57 s (300 s), 54 s (200 s), 47 s (100 s).
- The TEC waveform is lopsided: tall, narrow peaks and flat troughs. The residual is largest at 300 s.

**S18.3 one-lump model table** (`code/module8/s18_3_onelump_sim.py`). The simulator's lumped mode was reproduced from its page source: same equation, RK4 at 0.01 s, settled-cycle readout after 5τ. Settings from the page: room = initial = 22 °C, τ = 80 s, χh = 0.46, u_a = 0, u_b = 50. The browser simulator itself was not clicked.

| Period (s) | χc | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag (°) | (4) Residual amplitude (°C) |
|---|---|---|---|---|---|
| 100 | 0.23 | 3.660 | 3.366 | 78.8 | 0.240 |
| 100 | 0.46 | 0.005 | 4.488 | 78.7 | 0.003 |
| 200 | 0.23 | 3.661 | 6.377 | 68.3 | 0.473 |
| 200 | 0.46 | 0.002 | 8.503 | 68.3 | 0.002 |
| 300 | 0.23 | 3.661 | 8.840 | 59.2 | 0.695 |
| 300 | 0.46 | 0.000 | 11.787 | 59.2 | 0.000 |

- **Equal χ:** amplitude and lag match the analytical solution exactly (4.488/8.503/11.787 °C; 78.7/68.3/59.2°), and the residual is 0 as the page says it should be.
- **Fixed period, χc halved:** the mean rises by (u_b/2)(χh − χc)(2/π) = 3.66 °C, the amplitude drops by 25 %, the lag is unchanged, and a residual appears at 2ω (two bumps per PWM cycle).
- **Fixed χc, longer period:** larger amplitude and smaller lag; the mean shift is unchanged.
- **Against our measurement:** measured mean − room 5.4–5.8 °C, consistent with our χh − χc = 0.53 − 0.19 = 0.34 → 25 × 0.34 × 2/π ≈ 5.4 °C. Measured lags (50/59/71°) are about 8–9° smaller than the τ = 80 s model, which implies τ_th ≈ 50–57 s.
- Aligned plot of both χ settings at 100 s: `docs/figures/module_08/s18_3_onelump_model.png`.

**S18.3 "Compare The Simulation With Your Measurements"** (`code/module8/s18_3_model_vs_experiment.py`; figure `docs/figures/module_08/s18_3_model_vs_experiment_100s.png`)

- **Fixed PWM amplitude, three periods:** the temperature amplitude was **not** the same: 9.07 / 7.07 / 4.24 °C at 300 / 200 / 100 s.
- **100 s overlay** with our measured values: χh = 0.5311, χc = 0.1878 (Module 4), τ = 91.69 s (Module 6), room 22 °C, initial 22.81 °C, u_b = 50. Settled cycle t = 600–700 s.

| | Mean − room (°C) | Fundamental amplitude (°C) | Lag behind PWM (°) | Residual amplitude (°C) |
|---|---|---|---|---|
| Measured | 5.92 | 4.23 | 69.9 | 0.45 |
| Model, τ = 91.69 s | 5.46 | 3.07 | 80.2 | 0.31 |
| Model, τ = 43 s (best lag match, extra) | 5.46 | 6.24 | 69.7 | 0.66 |

- **Reproduced:** the upward mean shift (5.5 vs 5.9 °C) and the 2ω residual shape (two bumps per cycle, at the same phase).
- **Falls short:** with the measured τ the model is too slow (amplitude 27 % low, lag 10° too large). Matching the lag needs τ ≈ 43 s, but then the amplitude is 48 % too high. **No single τ fits both**, so the one-lump model is missing something; with the rod attached, heat also flows into the rod, which acts like an extra path and a second time constant. The measured residual is also about 45 % larger than the model's.

## Data removed (Nov 18, user's request)

All runs from steps after S18.4 were deleted, because those steps have not been reached in page order. They will be redone in order. That covers the Nov 4 open/P/PI trials and two-period pilot, and the Nov 9–11 production runs at 200, 240/400, 500 and 100 s, plus every figure and fit made from them. The notes above that describe those runs are kept as history only. The files are still in git history at commit `df93e5b` (`git show df93e5b:data/module_08/<file>`).

### S18.3 Check The Derivation

**Item 1 — substitute the solution into Eq. (S18.3.1) and verify T(0) = T_room.**

Let θ = T − T_room and r = ωτ_th. Eq. (S18.3.1): τ_th dθ/dt + θ = χ u_b sin(ωt).
Trial solution: θ = A sin(ωt − δ) + C e^(−t/τ_th), with A = χ u_b / √(1 + r²), tan δ = r, and C = χ u_b r / (1 + r²).

- Derivative: τ_th dθ/dt = A r cos(ωt − δ) − C e^(−t/τ_th).
- Left side: τ_th dθ/dt + θ = A[sin(ωt − δ) + r cos(ωt − δ)] + (C − C) e^(−t/τ_th). The exponential terms cancel.
- Using tan δ = r: sin x + r cos x = √(1 + r²) sin(x + δ). With x = ωt − δ this gives A √(1 + r²) sin(ωt) = χ u_b sin(ωt), which is the right side. ✓
- At t = 0: θ(0) = A sin(−δ) + C = −A sin δ + C. Since sin δ = r/√(1 + r²), A sin δ = χ u_b r/(1 + r²) = C, so θ(0) = 0, i.e. **T(0) = T_room**. ✓
- **What the exponential contributes:** the steady sinusoid alone would start at −A sin δ, below room, rather than at room. The term C e^(−t/τ_th) supplies exactly that offset at t = 0, so the start matches the initial condition. It then decays with time constant τ_th (< 1 % after 5τ_th). It only shapes the start-up and leaves the settled wave unchanged, which is why the settled readout waits 5τ.

**Item 2 — equal-susceptibility 300 s run: numerical vs analytical overlay, start-up and one settled cycle.** Figure: `docs/figures/module_08/s18_3_derivation_check_300s.png` (from `code/module8/s18_3_onelump_sim.py`). Settings: χh = χc = 0.46, τ = 80 s, u_b = 50, T(0) = T_room = 22 °C. The numerical RK4 trace and the boxed solution agree to **2 × 10⁻¹³ °C** over 0–1800 s, which is computer rounding. The green curve shows the exponential term alone: it starts at C = 10.1 °C above room and is gone by about 400 s. The browser simulator's dashed overlay matched as well (user screenshot, Nov 16).

### S18.3 prediction (written Nov 18, *after* the runs — not recorded beforehand as the page asks)

At fixed PWM amplitude, a longer period should give a larger TEC swing and a smaller phase lag (the low-pass response of a first-order system), and unequal heating and cooling should shift the mean above room and distort the wave at 2ω. Every one of these appeared in the measurement and the model.

## Stage 2, S18.4: positive-only sinusoidal PWM (Nov 18)

- Run: u = 34 + 30 sin(ωt), 100 s period, 8 cycles (800 s), ended DONE. PWM stayed at +4 to +64 (positive, unclipped). File: `data/module_08/angstrom_raw_s18_4_positive_100_20261118_101610.csv`. Room ≈ 23 °C (idle sensors).
- Tables: `docs/tables/module_08/s18_4_experiment.md` and `s18_4_simulation.md`. Figures: `docs/figures/module_08/s18_4_experiment.png` and `s18_4_simulation.png`.
- **Did positive-only PWM produce a more sinusoidal temperature response? Yes.** The residual fell from 0.54 to 0.07 °C (residual/amplitude 13 % → 2 %); the model gives 0.31 → 0.01 °C (10 % → 0.3 %). Heating only means one susceptibility (χh) for the whole cycle, so the |sin| distortion term disappears.
- **Remaining distortion:** the measured 0.07 °C is larger than the model's 0.01 °C. The one-lump model leaves out the rod, the χh nonlinearity (Module 4 local slopes 0.49–0.56) and sensor noise. The run was also still drifting +0.08 °C/min over the fit.
- The amplitude ratio is consistent: measured 3.53 °C at u_b = 30 vs 4.24 °C at u_b = 50. Per PWM count, heating only gives a larger swing (0.118 vs 0.085 °C/count), because χh > χc.
