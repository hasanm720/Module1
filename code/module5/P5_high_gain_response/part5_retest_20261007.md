# Supervised high-gain retest — October 7, 2026

Setpoint 30 °C; gains 20 → 40 → 50, approximately 180 s each, in one continuous experiment. The user supervised the apparatus. The original October 5 data, including all 318 gain-30 readings, is retained; no original measurements were overwritten. Ambient was not independently measured.

| Gain (PWM/°C) | Final-60-s mean (°C) | Final-60-s range (°C) | Response | Approximate local amplitude (°C) | Approximate local period (s) | Frequency (Hz) | Reported PWM range |
|---:|---:|---|---|---:|---:|---:|---|
| 20 | 29.386 | 29.36–29.41 | Warming then slight drift and irregular small fluctuations; no clear coherent wave train | N/A | N/A | N/A | 0–142 |
| 40 | 29.682 | 29.57–29.76 | Repeated rapid oscillatory reversals, especially 55–100 s; varying amplitude, later diminished | ≈0.09 in selected burst | ≈1.70 in selected burst | ≈0.59 | 4–24 |
| 50 | 29.743 | 29.71–29.77 | Small repeated irregular reversals on plateau; physical oscillation versus measurement noise unresolved | ≈0.015 | ≈3.96 | ≈0.25 | 12–16 |

No reported PWM reached 255. Both outputs were confirmed zero by telemetry after completion. The highest gain now tested is 50 PWM/°C. Its final-minute dimensional droop is 0.257 °C. These runs did not establish a numerical thermal time constant or instructor approval beyond the user's requested sequence.

## Settling interpretation

The main Part 5 table marks gain 20 approximately settled, gain 40 uncertain because its burst diminishes, and gain 50 uncertain because the small reversals may be noise. The retained gain-30 run is marked No for its recurring waves in the recorded window. A bounded range or stable mean alone does not mean that an oscillating temperature has settled. Final-minute means remain valid window averages even when settling is unconfirmed.

## Wave measurements and limits

Approximate measurements use the **raw** temperature samples and a reversal detector: track a running maximum/minimum and confirm each extremum only once temperature reverses by a chosen excursion threshold. Amplitude is the median half-difference between consecutive confirmed extrema; period is the median interval between confirmed maxima; frequency is the reciprocal of that median period.

For gain 40, use 55–100 s and an excursion threshold of 0.08 °C. This produces 37 confirmed alternating extrema; peak spacings span 1.13–6.23 s, with median 1.70 s. The larger burst has repeated changes substantially above the CSV's 0.01 °C reporting increment, but timing and amplitude vary. This describes an oscillatory burst, not proof of a constant-amplitude sustained instability.

For gain 50, use 40–180.068 s and an excursion threshold of 0.025 °C. This produces 53 confirmed alternating extrema; peak spacings span 1.13–14.15 s, with median 3.964 s. These are **descriptive local reversal statistics**, not an established dominant frequency. Sampling is about 0.566 s and temperature is reported to 0.01 °C. Noise, quantization, and feedback can all contribute; small reversals alone cannot prove a thermal control oscillation. Even gain 20 produces local extrema with a low threshold, so the detector must not be interpreted as an automatic physical-oscillation classifier.

## Recorded traces

![Gain 20 retest](../../../docs/figures/module_05/retest_20261007/kp_20_strip_chart.png)

![Gain 40 retest](../../../docs/figures/module_05/retest_20261007/kp_40_strip_chart.png)

![Gain 50 retest](../../../docs/figures/module_05/retest_20261007/kp_50_strip_chart.png)

## Provenance

- Acquisition: [run_high_gain_tests.py](run_high_gain_tests.py), using the existing Module 5 control calculation and strict telemetry parser; 115200 baud on `/dev/cu.usbmodem101`.
- Raw log: [high_gain_retest_20261007_101645_660586.csv](high_gain_retest_20261007_101645_660586.csv); preserved copy in `data/module_05/`.
- Retained gain 30: [kp30_original_20261005.csv](kp30_original_20261005.csv); preserved copy in `data/module_05/`. Its approximate 20 s waves and different measurement method are described in the original Part 5 note; they are not a new gain-30 measurement.
- Plots: [plot_strip_charts.py](plot_strip_charts.py), with explicit input/output options.

```sh
python3 code/module5/P5_high_gain_response/plot_strip_charts.py --input code/module5/P5_high_gain_response/high_gain_retest_20261007_101645_660586.csv --output-dir docs/figures/module_05/retest_20261007
```
