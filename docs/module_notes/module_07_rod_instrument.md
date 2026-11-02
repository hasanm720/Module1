# Module 7 — Rod instrument: sensor map, geometry, common-bath check

Fill every `___` at the bench. Units are SI unless stated.

## 1. Sensor map and wiring (Phase 1)

Divider on each channel: measured 100 kΩ (nominal) resistor from 5 V to the analog pin, thermistor from the pin to GND. Wiring: 26 AWG paired insulated wire with heat-shrink, 22 AWG solid pigtails at the breadboard.

| Wire tag | Role | Location (from rod base) | x (mm) | u(x) (mm) | Arduino pin | CSV column | Wire color | Series R (kΩ) |
|---|---|---|---|---|---|---|---|---|
| **T5** | TEC base: feedback + 60 °C shutdown | in the TEC base | — | — | A1 | `tec_C` | ___ | ___ |
| **T1** | rod, lowest hole: **x = 0** (boundary value T(0,t)) | 16.78 mm (moved from 41.66 mm on Nov 2) | 0 | ±0.5 | A5 | `rod1_C` | ___ | ___ |
| **T2** | rod | 67.08 mm | 50.30 | ±0.5 | A4 | `rod2_C` | ___ | ___ |
| **T3** | rod | 117.74 mm | 100.96 | ±0.5 | A3 | `rod3_C` | ___ | ___ |
| **T4** | rod | 167.10 mm | 150.32 | ±0.5 | A2 | `rod4_C` | ___ | ___ |
| **T6** | rod, highest hole | 217.73 mm | 200.95 | ±0.5 | A0 | `rod5_C` | ___ | ___ |
| — | rod tip | ≈300 mm | L = 283.2 | ±2 | — | — | — | — |

- **Coordinate:** x = 0 at the T1 hole, positive toward the free tip; the tip is at x = L. The base is the rod end at the TEC.
- **Tags vs columns:** there is no rod "T5". Tag T5 is the TEC thermistor, so CSV `rod5_C` holds tag **T6**.
- **Positions:** hole centers measured with calipers. T4 was measured from T1 and T6 from T2, then converted to x. u(x) = ±0.5 mm is the estimated error in locating a hole center.
- **Check:** T3→T4 = 49.36 mm, 1.4 mm short of the nominal 2 in. Worth re-measuring.

Photo/diagram showing labels, pins, the x direction and the positions: `docs/figures/module_07/___`

## 2. Rod geometry (Phase 3, Steps 5–6)

| Quantity | Value | Uncertainty | How measured |
|---|---|---|---|
| Material | 6061-T6 aluminum | — | — |
| Diameter d | 12.705 mm (readings 12.68, 12.73; nominal 12.7) | ±0.025 mm | calipers, mean of 2 |
| Overall physical length | ≈300 mm | ±2 mm | ruler (approximate) |
| Analysis length L (T1 hole → tip) | 283.2 mm | ±2 mm | 300 − 16.78 (T1 moved; was 258.3) |
| A = πd²/4 | 1.268 × 10⁻⁴ m² | ±0.005 × 10⁻⁴ | computed |
| P = πd | 0.03991 m | ±0.00008 | computed |

## 3. Software (Phase 2, Step 2C item 5)

| File | Path | Git commit |
|---|---|---|
| Arduino sketch | `code/module7/module_07_rod_controller/module_07_rod_controller.ino` | ___ |
| Python GUI | `code/module7/module_07_rod_acquisition_gui.py` | ___ |
| Common-bath analysis | `code/module7/common_bath_check.py` | ___ |

Integration checks (TEC power off):

- [ ] Warming each sensor alone changes only its own channel in the Arduino output, the GUI and the CSV
- [ ] One Arduino DATA line, the GUI numbers and one CSV row agree (field order, values, units)
- [ ] With one rod thermistor unplugged, the fault is visible (`nan`/`FAULT`) and TEC (A1) safety still works
- [ ] After restarting both programs, PWM starts at 0 and a new CSV file is created

## 4. Common-bath check (Phase 3)

Raw CSV: `data/module_07/rod_raw_common_bath_room_20261102_094019.csv`. Analysis output: `docs/figures/module_07/rod_raw_common_bath_room_20261102_094019_common_bath.png` and `..._spread.csv`

| Arduino window (s) | Thermocouple (°C) | TEC (T5) | T1 | T2 | T3 | T4 | T6 | Spread T_max − T_min (°C) | Pass (< 1 °C)? |
|---|---|---|---|---|---|---|---|---|---|
| 0–60 (86 rows, room air, TEC off, PWM 0) | not used | 21.82 | 22.27 | 22.16 | 22.01 | 22.16 | 22.14 | 0.45 (max instantaneous 0.52) | Pass |
| ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ | ___ |

Conclusion: All six channels agree within 0.45 °C (< 1 °C) at room temperature (Nov 2, 2026). The instructor approved a room-temperature check instead of a hot bath. Raw readings are used; no correction is applied. (If every spread is < 1 °C, the raw readings are used and no correction is applied. Otherwise continue to the Record/Pause calibration.)

Notes (noisy channel, connection fixed, bath handling): ___

## 5. Prediction record (before heating, Nov 2, 2026; updated after T1 moved to 16.78 mm)

Inputs: d = 12.705 mm, L = 283.2 mm, provisional h = 10 W m⁻² K⁻¹ (still air), k = 150–170 W m⁻¹ K⁻¹ (6061-T6 literature range).

| | k = 150 | k = 170 |
|---|---|---|
| m = √(4h/(kd)) (1/m) | 4.58 | 4.30 |
| Decay length 1/m (cm) | 21.8 | 23.2 |
| mL | 1.30 | 1.22 |
| Bi⊥ = hd/(4k) | 2.1 × 10⁻⁴ | 1.9 × 10⁻⁴ |
| θ(T6)/θ(T1), finite model | 0.55 | 0.58 |
| θ(tip)/θ(T1) = 1/cosh(mL) | 0.51 | 0.54 |

ε_T(x) = |Θ_finite − Θ_inf| / |Θ_finite| at each sensor:

| Sensor | T1 | T2 | T3 | T4 | T6 |
|---|---|---|---|---|---|
| x (mm) | 0 | 50.30 | 100.96 | 150.32 | 200.95 |
| ε_T (%) | 0 | 3.9–4.2 | 9.6–10.0 | 17.1–17.5 | 26.9–27.1 |

- Radius: Bi⊥ ≪ 0.1, so one temperature per cross-section is fine.
- Length: ε_T > 5% from T3 on, so the rod is **not** semi-infinite over the measured region; the finite tip should be visible.
- Placement target θ(T6) ≤ θ(T1)/e ≈ 0.37 θ(T1): not reachable anywhere on this rod if h ≈ 10, because even the tip gives 0.51–0.54. The pilot tests this.
- Superseded first version (T1 at 41.66 mm): L = 258.3 mm, mL = 1.11–1.18, ε_T(T6) ≈ 26%.

Qualitative predictions:
1. Response order after a base step: T1 → T2 → T3 → T4 → T6 (nearest the TEC first).
2. Amplitude: the temperature rise shrinks with distance from the base.
3. Stationary profile: a monotonic decay from T1, flattening toward the tip (cosh shape, zero slope at the insulated tip).
4. Finite tip: yes, it should be visible (mL ≈ 1.2–1.3).

## 6. Placement pilot (Phase 4, Steps 2–3; Nov 2, 2026)

TEC held at 45 °C by PI (Kp = 16, Ki = 0.5) for about 11 min, with the sensors in the holes from section 1. Room was 23.5 ± 0.5 °C (mean of the rod channels just before heating). Averages are over the last 120 s.

| Sensor | x (mm) | T (°C) | θ = T − T_room (°C) | θ/θ(T1) | Drift (°C/min) |
|---|---|---|---|---|---|
| TEC (T5) | — | 44.99 | — | — | −0.016 |
| T1 | 0 | 39.96 | 16.46 | 1.000 | −0.031 |
| T2 | 50.30 | 36.17 | 12.67 | 0.770 | −0.011 |
| T3 | 100.96 | 33.14 | 9.64 | 0.585 | +0.018 |
| T4 | 150.32 | 31.36 | 7.86 | 0.477 | +0.047 |
| T6 | 200.95 | 29.99 | 6.49 | **0.394** | +0.066 |

- **Placement criterion θ(T6) ≤ θ(T1)/e = 0.368: not met, but close (0.39).** T6 is already in the highest hole, so the holes are kept. A ±0.5 °C error in room temperature moves the ratio between 0.36 and 0.43.
- **Compared with the prediction:** the measured decay is stronger than predicted (0.39 vs 0.55–0.58). The rough semilog slope gives m ≈ 4.7 m⁻¹, which suggests h is larger than the provisional 10 W m⁻² K⁻¹.
- **Not fully stationary:** T4 and T6 were still rising (+0.05 to +0.07 °C/min, above the 0.02 °C/min criterion), so the final ratio will be slightly higher. The stationary run (Phase 4, Steps 5–9) settles this.
- **Semilog spacing:** the five points are evenly spread and well separated in ln θ, so no position is indistinguishable from noise.
- A small dip on all channels at t ≈ 470 s is a brief disturbance (air or touch), not a sensor fault.
- **Files:** `data/module_07/rod_raw_pilot_45C_run3_20261102_110341.csv` and `docs/figures/module_07/rod_raw_pilot_45C_run3_20261102_110341_pilot.png`. Earlier attempts (`..._pilot_45C_*`, `..._run2_*`) failed because of a loose TEC contact and GUI stops.
