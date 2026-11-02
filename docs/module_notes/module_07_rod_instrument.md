# Module 7 — Rod instrument: sensor map, geometry, common-bath check

Fill every `___` at the bench. Units are SI unless stated.

## 1. Sensor map and wiring (Phase 1)

Divider on each channel: measured 100 kΩ (nominal) resistor from 5 V to the analog pin, thermistor from the pin to GND. Wiring: 26 AWG paired insulated wire with heat-shrink, 22 AWG solid pigtails at the breadboard.

| Label | Arduino pin | Location | Wire colors | Measured series R (kΩ) | x (mm) | u(x) (mm) |
|---|---|---|---|---|---|---|
| TEC (tag T5) | A1 | TEC base (feedback + 60 °C shutdown) | ___ | ___ | — | — |
| T1 | A5 | 41.66 mm from base (**x = 0**) | ___ | ___ | 0 | ±0.5 |
| T2 | A4 | 67.08 mm from base | ___ | ___ | 25.42 | ±0.5 |
| T3 | A3 | 117.74 mm from base | ___ | ___ | 76.08 | ±0.5 |
| T4 | A2 | 167.10 mm from base | ___ | ___ | 125.44 | ±0.5 |
| T6 | A0 | 217.73 mm from base | ___ | ___ | 176.07 | ±0.5 |

Wire tags: the TEC thermistor is tagged **T5**; rod sensors are tagged T1 (lowest hole) … T4, **T6** (highest hole). CSV `rod5_C` = tag T6.

Coordinate: x = 0 at the first thermistor hole (T1), positive toward the free tip. The tip is at x = L. Base = rod end at the TEC. Positions were measured with calipers (T4 measured from T1 and T5 from T2, then converted). u(x) = ±0.5 mm for locating the hole center (estimate). T3→T4 = 49.36 mm, 1.4 mm short of the nominal 2 in; worth re-checking.

Photo/diagram showing labels, pins, the x direction and the positions: `docs/figures/module_07/___`

## 2. Rod geometry (Phase 3, Steps 5–6)

| Quantity | Value | Uncertainty | How measured |
|---|---|---|---|
| Material | 6061-T6 aluminum | — | — |
| Diameter d | 12.705 mm (readings 12.68, 12.73; nominal 12.7) | ±0.025 mm | calipers, mean of 2 |
| Overall physical length | ≈300 mm | ±2 mm | ruler (approximate) |
| Analysis length L (T1 hole → tip) | 258.3 mm | ±2 mm | 300 − 41.66 |
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

## 5. Prediction record (before heating, Nov 2, 2026)

Inputs: d = 12.705 mm, L = 258.3 mm, provisional h = 10 W m⁻² K⁻¹ (still air), k = 150–170 W m⁻¹ K⁻¹ (6061-T6 literature range).

| | k = 150 | k = 170 |
|---|---|---|
| m = √(4h/(kd)) (1/m) | 4.58 | 4.30 |
| Decay length 1/m (cm) | 21.8 | 23.2 |
| mL | 1.18 | 1.11 |
| Bi⊥ = hd/(4k) | 2.1 × 10⁻⁴ | 1.9 × 10⁻⁴ |
| θ(T6)/θ(T1), finite model | 0.60 | 0.63 |

ε_T(x) = |Θ_finite − Θ_inf| / |Θ_finite| at each sensor (both k give about the same):

| Sensor | T1 | T2 | T3 | T4 | T6 |
|---|---|---|---|---|---|
| x (mm) | 0 | 25.42 | 76.08 | 125.44 | 176.07 |
| ε_T (%) | 0 | 2.2 | 8.0–8.3 | 15.6–16.0 | 25.6–25.8 |

- Radius: Bi⊥ ≪ 0.1, so one temperature per cross-section is fine.
- Length: ε_T > 5% from T3 on, so the rod is **not** semi-infinite over the measured region; the finite tip should be visible.
- With h = 10, θ(T6) ≈ 0.6 θ(T1), which does not reach the placement target θ5 ≤ θ1/e ≈ 0.37. The placement pilot will test this.

Qualitative predictions:
1. Response order after a base step: T1 → T2 → T3 → T4 → T6 (nearest the TEC first).
2. Amplitude: the temperature rise shrinks with distance from the base.
3. Stationary profile: a monotonic decay from T1, flattening toward the tip (cosh shape, zero slope at the insulated tip).
4. Finite tip: yes, it should be visible (mL ≈ 1.1–1.2).
