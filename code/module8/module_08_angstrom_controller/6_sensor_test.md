# Sensor-Test Analysis

## The Three Dimensionless Lengths

With κ = 6.90×10⁻⁵ m²/s and ν = 1.30×10⁻³ s⁻¹, the mean-profile numbers are m = 4.34 m⁻¹, mL = 1.30, and ℓ_mean = 230 mm. These don’t depend on the period.

| τ (s) | Ω = ω/ν | q (m⁻¹) | q′ (m⁻¹) | ℓ_amp = 1/q | ℓ_phase = 1/q′ | qL | q′L (rad) | 2π cycles | e^(−qL) | (q−q′)/q |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 48 | 21.6 | 21.1 | 46 mm | 47 mm | 6.47 | 6.33 | 1.01 | 0.0016 | 2.1% |
| 200 | 24 | 15.4 | 14.8 | 65 mm | 68 mm | 4.62 | 4.43 | 0.71 | 0.0099 | 4.1% |
| 400 | 12 | 11.1 | 10.2 | 90 mm | 98 mm | 3.34 | 3.07 | 0.49 | 0.036 | 7.9% |

Amplitude versus mean decay: qL > mL at every period, so the oscillation decays 3–5× faster than the mean. Your traces show this: the mean profile looks the same in all three runs (T1 ≈ 38, T2 ≈ 35, T3 ≈ 33 °C), while the amplitudes change a lot with period.

Fitted q matched the ideal: I measured about 20.9, 15.4, and 11.6 m⁻¹ against 21.6, 15.4, and 11.1.

q ≈ q′ when Ω ≫ 1: this is the no-loss limit q = q′ = √(ω/2κ), which gives 21.3 m⁻¹ at 100 s. It is why the sim’s ν was hard to extract. The ratio (q−q′)/q grows from 2% to 8% as the period lengthens, so longer periods constrain ν better.

## The Four Features, Revisited

Mean temperature: it falls steadily with distance and is the same at every period. I need to correct my earlier remark that its slope was near −m. The rod holds only 1.3 mean-decay lengths, so the profile is cosh-shaped, not exponential. The ln(T̄ − T∞) slope is about −3.2 m⁻¹ over T0–T3 and −2.4 m⁻¹ over all six sensors, not −4.34. At T5 the mean excess is still 51% of the base value, against 29% for a pure exponential. Fit it with the cosh form to get mL, as Stage 6 says.

Amplitude: it falls close to exponentially, and much faster than the mean. The ln B slope gives −q, about 4–8× steeper than the apparent mean slope. The only departure is at the tip: the finite-rod amplitude at T5 is 1.5–1.7× the semi-infinite value at all three periods, while T4 is within about 6%. So exclude T5 from semi-infinite fits.

Phase lag: it grows monotonically downstream, and the sensor-to-sensor delay in seconds grows with period (T3 at about 48, 67, and 94 s for 100, 200, and 400 s). The phase per unit length (q′) shrinks as the period grows.

PWM: it swings from about −3% to +45%, so it is mostly heating. It peaks about 15–20 s before T0, and T0 itself trails the setpoint by about 5–10 s, so the PWM leads the setpoint by roughly 10 s. T0 also tracks better at longer periods: about 90% of the commanded amplitude at 100 and 200 s, and about 97% at 400 s. The PWM–setpoint relationship depends on the controller gains, so don’t treat it as universal.

## Which Sensors Give a Measurable Signal

I took about 0.5 K as the practical resolution limit. The ideal amplitudes below assume T0 = 14.5 K.

### Simulator Positions (up to 285 mm)

| τ (s) | T1 | T2 | T3 | T4 | T5 | Usable |
|---:|---:|---:|---:|---:|---:|---|
| 100 | 6.7 | 2.4 | 0.65 | 0.13 | 0.05 | T0–T3 (T3 marginal) |
| 200 | 8.3 | 4.0 | 1.6 | 0.49 | 0.29 | T0–T3 (T4 borderline) |
| 400 | 9.7 | 5.7 | 2.8 | 1.3 | 1.0 | All six |

This matches what you saw: T4 and T5 were flat at 100 s and clearly visible at 400 s.

### Physical Layout

T1 is at the first hole, with 1-inch spacing and x = 0 to 102 mm.

| τ (s) | B5/B1 | T1→T5 lag (rad) | T5 amplitude (K) |
|---:|---:|---:|---:|
| 100 | 0.11 | 2.15 | 1.6 |
| 200 | 0.21 | 1.50 | 3.0 |
| 400 | 0.32 | 1.03 | 4.7 |

The page’s targets are B5 ≈ B1/e ≈ 0.37 and a 0.5–2 rad phase lag from first to last sensor. The 400 s period hits both, 200 s hits the phase target with a slightly small far amplitude, and 100 s is just past the phase target with the weakest far signal. The finite-to-semi-infinite amplitude ratio is within 1% at all five sensors for every period, so a 1-inch layout is safely semi-infinite. The simulator’s wide spacing is why its far sensors lose signal while the physical layout keeps all five.

## Qualitative Prediction

The simulator confirmed the sketch: the temperature has the same frequency everywhere, but farther from the TEC it has a smaller amplitude, a later peak, and an unchanged mean offset. A shorter period gives stronger attenuation and more phase lag per unit length, and a weaker far signal.

The practical choices for the experiment are a 200–240 s period as the main run and 400 s only if time allows, since five settled cycles at 400 s is about 33 minutes. A 100 s run is still useful as a frequency-consistency check.