# Part 5: High-gain response

Setpoint: **30.0 °C**. Mean temperatures use each run’s final 60 s.

| Kp (PWM/°C) | Settles? | Mean temperature (°C) | Response shape | Amplitude (°C) | Period (s) | Frequency (Hz) | Reported PWM range | Saturation? |
|---:|---|---:|---|---|---|---|---|---|
| 10 | Yes | 28.893 | Initial overshoot; settles below target | N/A | N/A | N/A | 0–64; final minute: 11 | No |
| 20 | Yes | 29.422 | Rises to a steady plateau | N/A | N/A | N/A | 11–22; final minute: 11–12 | No |
| 30 | Yes | 29.591 | Rises to a plateau with small fluctuations | N/A | N/A | N/A | 11–17; final minute: 12–13 | No |
| 40 | Yes | 29.697 | Rises and holds near target | N/A | N/A | N/A | 12–16; final minute: 12 | No |

Settling criterion: final-minute temperature range ≤ 0.5 °C and absolute drift
≤ 0.002 °C/s. No sustained oscillations were established, so amplitude,
period, and frequency are N/A. Amplitude would be half the peak-to-peak temperature.

**Highest gain tested: 40 PWM/°C.** Compared with Part 3’s gain-5 result
(29.50 °C; screenshot droop 0.50 °C), gain 40 reached a mean of 29.697 °C with droop
0.303 °C. Gain 40 was closer to the setpoint than the gain-5 screenshot, without
sustained oscillations or PWM saturation in the observed windows.

**Control stopped; PWM zero confirmed on both outputs.**

Source: [measurement log](high_gain_20261005_110725.csv).
