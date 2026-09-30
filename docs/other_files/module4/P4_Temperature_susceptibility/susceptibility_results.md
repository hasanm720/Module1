# Temperature susceptibility

Source: PWM_calibration_tables.md

Recorded temperature ranges are treated as steady-state observations; points are range midpoints and error bars show the recorded min–max range, not statistical uncertainty. The table does not document a settling-time or drift criterion.

Signed PWM is positive for heating and negative for cooling. Susceptibility is ΔT / Δ(signed PWM), in °C per PWM count.

| Direction | Endpoint finite difference (°C/count) | Linear fit (°C/count) | R² | Local slope range (°C/count) |
|---|---:|---:|---:|---:|
| Heating | 0.5357 | 0.5311 | 0.99946 | 0.4868–0.5614 |
| Cooling | 0.1891 | 0.1878 | 0.99899 | 0.1756–0.2072 |

Heating/cooling fitted slope ratio: 2.8289 (dimensionless).

Both data sets are approximately linear over the measured range, but adjacent-point slopes vary; the fitted slope is an overall approximation, not an exact constant response. The recorded ranges are not sufficient to establish measurement uncertainty.

For cooling, the slope versus signed PWM is positive: moving toward zero PWM raises temperature. Versus cooling PWM magnitude, the slope has the same size but is negative. Heating slopes have the same sign under either convention.

## Heating: adjacent-point finite differences

| Signed PWM interval | ΔT / ΔPWM (°C/count) |
|---|---:|
| 0 to 11 | 0.5614 |
| 11 to 21 | 0.5410 |
| 21 to 32 | 0.4868 |
| 32 to 43 | 0.5541 |

Maximum absolute departure from the straight-line fit: 0.250 °C.

## Cooling: adjacent-point finite differences

| Signed PWM interval | ΔT / ΔPWM (°C/count) |
|---|---:|
| -63 to -47 | 0.2072 |
| -47 to -31 | 0.1906 |
| -31 to -13 | 0.1756 |
| -13 to 0 | 0.1838 |

Maximum absolute departure from the straight-line fit: 0.179 °C.
