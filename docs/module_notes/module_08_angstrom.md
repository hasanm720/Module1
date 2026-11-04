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
