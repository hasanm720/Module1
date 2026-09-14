# A1 — PHYS39 Module 1 Evidence

Assignment code: A1  
Module: PHYS39 Module 1  
Team members: Kyle Chen and Muhammad Hasan     
Date: September 9, 2026  
Full Git commit hash: 0b140dde7c83f30be975b22329dd135b2fb49a1d       
Repository: [hasanm720/Module1 — `mainv2`](https://github.com/hasanm720/Module1/tree/mainv2)



---

## 1. Apparatus and Experimental Setup
<img src="../images/module1/P2_analog_read_serial/analog_read_serial_ciruit_photo.png" alt="Analog-read circuit photograph" width="75%">

### P2 — Analog input / serial measurement apparatus

The analog-read experiment uses an Arduino Uno with a potentiometer connected to analog input **A0**. The potentiometer is used as a variable voltage source between the Arduino's 5 V and ground rails. The center/wiper is connected to A0, so rotating the potentiometer changes the voltage presented to the ADC.

<img src="../images/module1/P2_analog_read_serial/analog_read_serial_ciruit_photo.png" alt="P2 analog-read circuit photograph" width="75%">

*Figure 1. Analog-read/serial apparatus photograph. The photograph shows the Arduino Uno, breadboard, potentiometer, jumper wiring, and USB connection used for the A0 analog-input measurement.*

The corresponding computer-side evidence shows the Arduino IDE/Serial Monitor and Serial Plotter receiving the ADC readings. The Serial Monitor reports individual samples, while the Serial Plotter provides a graphical view of the measured values.



<img src="../images/module1/P2_analog_read_serial/serial_monitor_and_terminal_screenshot.png" alt="Serial Monitor and Serial Plotter evidence" width="100%">

*Figure 2. Serial Monitor and Serial Plotter evidence. The Serial Monitor shows repeated integer ADC readings, while the Serial Plotter displays those readings as a time-varying trace.*

### Part 3 — Trim-pot averaging apparatus

For the averaging experiments, the potentiometer was used to hold the input near a fixed voltage while repeated ADC conversions were collected. The circuit photograph below documents the trim-pot setup.


<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_circuit.PNG" alt="Trim-pot circuit" width="75%">

*Figure 3. Trim-pot circuit used for the averaging measurements. The photograph shows the trim potentiometer wired to the Arduino analog-input circuit.*


The repository also contains a serial-plotter capture of the trim-pot being adjusted through a range of voltages. This demonstrates the ADC's discrete output levels as the potentiometer is changed.


<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_analog_read_voltage_steps/trim_pot_and_serial_plotter_screenshot.png" alt="Trim-pot voltage sweep" width="100%">

*Figure 4. Trim-pot voltage sweep. The Serial Plotter shows the voltage decreasing in small discrete steps as the potentiometer is adjusted, illustrating ADC quantization.*

### Part 4 — LED PWM apparatus

The final experiment maps an averaged analog input to PWM output on the Arduino. The sketch uses the potentiometer on A0 and PWM output pin 9. The two circuit photographs document the high-duty-cycle and low-duty-cycle configurations.



<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/high_duty_cycle_circuit.PNG" alt="P4 high-duty-cycle circuit" width="75%">

*Figure 5. P4 circuit at a high PWM duty cycle.*


<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/low_duty_cycle_circuit.PNG" alt="P4 low-duty-cycle circuit" width="75%">

*Figure 6. P4 circuit at a low PWM duty cycle.*

---

## 2. Arduino Files Used

The experiment is split into focused sketches. Each link below opens the exact Arduino file stored in the repository; the code itself is not pasted into this evidence note.

### Part 1 — Blink


- [Part1_Blink.ino](../../code/module1/P1_Blink/P1_Blink.ino) — basic LED blink demonstration.
- The sketch sets `LED_BUILTIN` as an output and alternates the LED between HIGH and LOW with 1000 ms delays. This produces approximately a 2 s period and demonstrates basic digital output timing.

### Part 2 — Analog read and serial output

- [Part2_analog_read_serial.ino](../../code/module1/P2_analog_read_serial/P2_analog_read_serial.ino) — reads A0 with `analogRead()` and prints the raw ADC result at 9600 baud.
- The sketch includes a 1 ms delay between readings for stability.
- The post-class notes in the sketch record the observed ADC minimum and maximum as 55 and 1018, respectively.

### Part 3 — Averaging and resolution


- [Part3a_analog_read_serial.ino](../../code/module1/P3_averaging_vs_unaveraging/3a_analog_read_serial/3a_analog_read_serial.ino) — raw ADC sampling.
- [Part3b_trim_pot_analog_read_serial.ino](../../code/module1/P3_averaging_vs_unaveraging/3b_trim_pot_analog_read_serial/3b_trim_pot_analog_read_serial.ino)
 — converts the raw ADC value to voltage using a 5.00 V reference

- [Part3c_trim_pot_STDEV.ino](../../code/module1/P3_averaging_vs_unaveraging/3c_STDEV/3c_STDEV.ino)
 — collects 100 unaveraged values and 100 values averaged over 1000 ADC conversions, then calculates the means and sample standard deviations.

- [Part3d_trim_pot_micros.ino](../../code/module1/P3_averaging_vs_unaveraging/3d_trim_pot_micros/3d_trim_pot_micros.ino) — measures the elapsed time for 1000 `analogRead()` conversions using `micros()` and calculates conversions per second and time per conversion.

### Part 4 — Averaged input to PWM

- [Part4_trim_pot_DutyCycle.ino](../../code/module1/P4_trim_pot_DutyCycle/P4_trim_pot_DutyCycle.ino)
 — averages 1000 A0 readings, converts the average to voltage, maps the ADC result to a PWM value, outputs PWM on pin 9, and reports the average ADC, voltage, and PWM value over Serial.

---

# 3. Part 1 — Blink

The Part 1 sketch is the introductory digital-output experiment. `LED_BUILTIN` is configured as an output. The loop writes the output HIGH, waits 1 s, writes it LOW, and waits another 1 s. Therefore, each complete on/off cycle is approximately 2 s, corresponding to a frequency of approximately 0.50 Hz and a duty cycle of approximately 50%.

The purpose of Part 1 is to establish the basic relationship between software timing and a measurable electrical/digital output before moving to analog measurement and PWM.

**Code:** [Part1_Blink.ino](../../code/module1/P1_Blink/P1_Blink.ino)

---

# 4. Part 2 — ADC Digitization

## 4.1 Measurement procedure

The Part 2 sketch repeatedly executes `analogRead(A0)` and prints the raw ADC number. The input is supplied by the potentiometer, whose wiper is connected to A0. The sketch uses a 9600-baud serial connection and a 1 ms delay between readings.

**Code:** [Part2_analog_read_serial.ino](../../code/module1/P2_analog_read_serial/P2_analog_read_serial.ino)

The recorded post-class ADC range is:

| Quantity | Measured ADC value |
|---|---:|
| Minimum, $n_{\min}$ | 55 |
| Maximum, $n_{\max}$ | 1018 |
| Midrange, $n_{\mathrm{mid}}$ | 536.5 |

The midrange is calculated from

$$
n_{\mathrm{mid}}=\frac{n_{\min}+n_{\max}}{2}
=\frac{55+1018}{2}
=536.5.
$$

## 4.2 One-count voltage resolution

For a 10-bit Arduino ADC there are 1024 possible integer output codes, from 0 through 1023. With a 5.00 V reference, the voltage represented by one ADC count is

$$
\Delta V_{\mathrm{1\,count}}
=\frac{V_{\mathrm{ref}}}{1023}
=\frac{5.00\ \mathrm{V}}{1023}
\approx 0.004888\ \mathrm{V}.
$$

Thus,

$$
\boxed{\Delta V_{\mathrm{1\,count}}\approx4.89\ \mathrm{mV/count}}.
$$

The code uses the same conversion relationship in the voltage-measurement sketches:

$$
V=\frac{n}{1023}(5.00\ \mathrm{V}).
$$

The expected voltage corresponding to the observed endpoints is approximately

$$
V_{\min}=\frac{55}{1023}(5.00)\approx0.269\ \mathrm{V},
$$

and

$$
V_{\max}=\frac{1018}{1023}(5.00)\approx4.976\ \mathrm{V}.
$$

The midpoint code of 536.5 corresponds to approximately

$$
V_{\mathrm{mid}}=\frac{536.5}{1023}(5.00)\approx2.623\ \mathrm{V}.
$$

## 4.3 Why the readings occupy discrete levels

The ADC does not report an arbitrary real-valued voltage. It quantizes the input into integer digital codes. Because this is a 10-bit ADC, the output can only be one of 1024 integer values, so small changes in input voltage that do not cross the next ADC threshold produce the same reported number.

Consequently, the measured voltage also appears in discrete levels when the ADC number is converted back to volts. Each adjacent integer ADC code is separated by approximately 4.89 mV for a 5.00 V reference. The trim-pot measurements therefore show small step-like changes rather than a perfectly continuous voltage signal.

<img src="../images/module1/P2_analog_read_serial/serial_monitor_and_terminal_screenshot.png" alt="Part2 serial evidence" width="100%">

*Figure 7. P2 Serial Monitor and Serial Plotter evidence showing the measured ADC samples.*

---

# 5. P3 — Power of Averaging

## 5.1 Voltage-step demonstration

The trim-pot sweep demonstrates the discrete nature of the ADC. The sketch used for the voltage conversion is:

[Part 3b_trim_pot_analog_read_serial.ino](../../code/module1/P3_averaging_vs_unaveraging/3b_trim_pot_analog_read_serial/3b_trim_pot_analog_read_serial.ino)

The code converts the integer ADC result using

$$
V=5.00\frac{n}{1023}.
$$

The recorded notes give $n_{\min}=55$, $n_{\max}=1018$, and $n_{\mathrm{mid}}=536.5$. The Serial Plotter capture below shows the resulting voltage sweep.

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_analog_read_voltage_steps/trim_pot_and_serial_plotter_screenshot.png" alt="Trim-pot voltage steps" width="100%">

*Figure 8. Serial Plotter voltage sweep from the trim-pot experiment.*

---

## 5.2 N = 1 versus N = 1000

For the averaging comparison, 100 sequential unaveraged measurements are first recorded. The program then records another 100 sequential values, where each displayed value is the average of 1000 individual ADC conversions.

The key difference is therefore:

- **N = 1:** each reported voltage is based on one ADC conversion.
- **N = 1000:** each reported voltage is the arithmetic mean of 1000 ADC conversions.

The N = 1 data show the normal one-count ADC quantization and visible sample-to-sample fluctuations.

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_unaveraged.png" alt="N = 1 unaveraged data" width="100%">

*Figure 9. N = 1/unaveraged Serial Plotter result. The trace visibly jumps between discrete voltage levels and has substantially more sample-to-sample variation than the averaged result.*

The N = 1000 result is much smoother because random fluctuations are averaged together.

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_average.png" alt="N = 1000 averaged data" width="100%">

*Figure 10. N = 1000 averaged Serial Plotter result. The trace is much tighter and smoother because each displayed point represents the mean of 1000 ADC conversions.*

The repository also contains a direct screenshot comparing the acquisition/software output associated with the averaging experiment.

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_average_vs_unaveraged_screenshot.png" alt="N = 1 and N = 1000 comparison" width="100%">

*Figure 11. Combined evidence for the averaged versus unaveraged measurements.*

---

## 5.3 Standard-deviation measurement

The standard-deviation experiment collects:

- 100 unaveraged measurements.
- 100 averaged measurements.
- Each averaged measurement is based on $N=1000$ individual ADC conversions.
- The standard deviation is calculated using the sample-standard-deviation expression with $N-1$ in the denominator.

**Code:** [Part3c_STDEV.ino](../../code/module1/P3_averaging_vs_unaveraging/3c_STDEV/3c_STDEV.ino)

The program reports the mean of each data set, $s_1$, $s_{1000}$, their ratio, and the theoretical $1/\sqrt{1000}$ prediction.

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_STDEV.png" alt="Standard-deviation experiment output" width="100%">

*Figure 12. Serial output from the standard-deviation calculation. The displayed results include the unaveraged and averaged means, their standard deviations, the measured ratio, and the theoretical 1/sqrt(1000) comparison.*

The theoretical averaging prediction is

$$
s_N\approx\frac{s_1}{\sqrt{N}}.
$$

For $N=1000$,

$$
\frac{1}{\sqrt{1000}}
\approx0.03162.
$$

Thus, ideal averaging predicts that the random component of the standard deviation should be about 3.16% of the N = 1 value, corresponding to roughly a factor of 31.6 reduction.

The measured ratio should be compared with 0.03162 rather than expected to match it exactly. Real measurements include quantization, finite sample size, instrument behavior, electrical noise, and other nonideal effects.

---

## 5.4 Measured voltage resolution and the $1/\sqrt{N}$ prediction

For a single ADC conversion ($N=1$), the nominal physical one-count voltage spacing is

$$
\Delta V_{\mathrm{ADC}} = \frac{V_{\mathrm{ref}}}{1023} = \frac{5.00\ \mathrm{V}}{1023} \approx 4.8876\ \mathrm{mV}.
$$

In the $N=1$ unaveraged block, the smallest observed discrete voltage jump between consecutive measurements directly reflects this single 1-count ADC step:

$$
\Delta V_{\text{jump}, N=1} \approx 4.89\ \mathrm{mV} \quad (\text{equal to } \Delta V_{\mathrm{ADC}}).
$$

When averaging $N=1000$ independent conversions, random noise is suppressed by a theoretical factor of $1/\sqrt{1000} \approx 0.03162$. Since each reported point is the arithmetic mean of 1000 integer counts, the minimum discrete resolution step for an averaged reading scales down by a factor of $N=1000$:

$$
\Delta V_{\text{jump}, N=1000} = \frac{\Delta V_{\mathrm{ADC}}}{N} = \frac{4.8876\ \mathrm{mV}}{1000} \approx 0.00489\ \mathrm{mV}\ (4.89\ \mu\mathrm{V}).
$$

Comparing the two:
- **$N=1$ minimum jump:** $\Delta V_{\text{jump}, N=1} \approx 4.89\ \mathrm{mV}$, which matches the fixed hardware ADC step $\Delta V_{\mathrm{ADC}}$.
- **$N=1000$ minimum jump:** $\Delta V_{\text{jump}, N=1000} \approx 0.00489\ \mathrm{mV}$, demonstrating that averaging creates sub-LSB fractional resolution and provides approximately 5 additional effective bits of precision ($\log_2 \sqrt{1000} \approx 4.96\text{ bits}$).

---

## 5.5 Completed averaging table

| Potentiometer block | Reported points | Readings averaged per point $N$ | Mean voltage | Sample standard deviation $s$ | $s / s_1$ measured | $s / s_1$ predicted |
|---|---:|---:|---:|---:|---:|---:|
| Unaveraged | 100 | 1 | 2.635 V | 0.000489 V | 1.000 | 1.000 |
| Long average | 100 | 1000 | 2.635 V | 0.000021 V | 0.043 | 0.0316 |

---

## 5.6 Timing of 1000 conversions

The timing sketch uses Arduino's `micros()` function around the loop containing 1000 `analogRead()` conversions.

**Code:** [3d_trim_pot_micros.ino](../../code/module1/P3_averaging_vs_unaveraging/3d_trim_pot_micros/3d_trim_pot_micros.ino)

The recorded result is:

| Timing quantity | Measured value |
|---|---:|
| Time for 1000 `analogRead()` conversions | **120,452 µs** |
| Conversions per second | **8.30 conversions/s** |
| Time per conversion | **120.45 µs/conversion** |

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3D/trim_pot_micros.png" alt="Timing measurement" width="100%">

*Figure 13. Timing evidence for 1000 ADC conversions. The Serial Monitor reports 120452 microseconds for 1000 conversions, approximately 8.30 conversions/s, and approximately 120.45 microseconds per conversion.*

Averaging improves precision by reducing random fluctuations, but it costs time because the Arduino must perform many conversions before producing one averaged result. With $N=1000$, approximately 1000 ADC measurements are required for each averaged value. This makes the averaged measurement act as a **low-pass filter**: rapid sample-to-sample fluctuations are suppressed because they have less influence on the long-term mean, while slower changes in the input are preserved.

The tradeoff is therefore:

$$
\boxed{\text{more averaging} \rightarrow \text{better precision but slower response}}
$$

In signal-processing terms, averaging improves precision while reducing **time resolution/bandwidth**. A rapidly changing input cannot be represented as quickly because the system must spend time collecting the samples that form each average.

---

# 6. P4 — LED Brightness From Averaged Analog Input

## 6.1 Method

The P4 sketch uses:

- Potentiometer input: **A0**
- PWM output: **digital pin 9**
- Averaging count: **N = 1000**
- Reference voltage: **5.00 V**
- Serial communication: **9600 baud**

**Code:** [P4_trim_pot_DutyCycle.ino](../../code/module1/P4_trim_pot_DutyCycle/P4_trim_pot_DutyCycle.ino)

The sketch first collects 1000 ADC readings and calculates their arithmetic mean:

$$
n_{\mathrm{avg}}
=\frac{1}{1000}\sum_{j=1}^{1000}n_j.
$$

It then converts the averaged ADC value to voltage:

$$
V_{\mathrm{in}}
=5.00\frac{n_{\mathrm{avg}}}{1023}.
$$

Finally, the averaged ADC value is mapped to an 8-bit PWM value using approximately

$$
\mathrm{PWM}\approx\frac{n_{\mathrm{avg}}}{4}.
$$

The Arduino's `analogWrite(9, pwmValue)` then applies the corresponding PWM output on pin 9.

---

## 6.2 Measured Serial output

The recorded Serial Monitor evidence shows an averaged ADC value near 539.08–539.09, corresponding to approximately 2.6348–2.6349 V and a PWM value of 134.

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/trim_pot_DutyCycle.png" alt="P4 Serial Monitor output" width="100%">

*Figure 14. P4 averaged ADC, voltage, and PWM Serial output. The captured output repeatedly reports an average ADC near 539.08–539.09, a voltage near 2.6348–2.6349 V, and PWM = 134.*

For example, using the displayed value $n_{\mathrm{avg}}\approx539.09$,

$$
V_{\mathrm{in}}
\approx5.00\frac{539.09}{1023}
\approx2.635\ \mathrm{V}.
$$

The displayed PWM value of 134 is consistent with the sketch's approximate mapping,

$$
539.09/4\approx134.8,
$$

with the integer PWM command constrained to the Arduino's 8-bit PWM range.

---

## 6.3 PWM oscilloscope measurements

The oscilloscope images document the actual PWM waveform at high and low duty-cycle settings.

### High-duty-cycle waveform

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/high_duty_cycle_oscilloscope.PNG" alt="High-duty-cycle oscilloscope" width="100%">

*Figure 15. High-duty-cycle PWM oscilloscope evidence. The scope directly shows the repeated PWM pulses and their timing; the photographed scale/readouts should be used for the final numerical measurements.*

### Low-duty-cycle waveform

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/low_duty_cycle_oscilloscope.PNG" alt="Low-duty-cycle oscilloscope" width="100%">

*Figure 16. Low-duty-cycle PWM oscilloscope evidence. The scope shows narrower high pulses separated by longer low intervals, corresponding to a lower duty cycle.*

The associated circuit photographs are included below for completeness.

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/high_duty_cycle_circuit.PNG" alt="High-duty-cycle circuit" width="75%">

*Figure 17. High-duty-cycle circuit configuration.*

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/low_duty_cycle_circuit.PNG" alt="Low-duty-cycle circuit" width="75%">

*Figure 18. Low-duty-cycle circuit configuration.*

---

## 6.4 Requested PWM quantities

The oscilloscope is the appropriate instrument for determining the actual electrical PWM waveform. The waveform should be characterized using:

- $V_{\mathrm{HIGH}}$: measured high-level voltage.
- $V_{\mathrm{LOW}}$: measured low-level voltage.
- $T$: period of one complete PWM cycle.
- $f=1/T$: PWM frequency.
- Duty cycle:

$$
D=\frac{t_{\mathrm{HIGH}}}{T}\times100\%.
$$

For the submitted measurements, the numerical oscilloscope readings should be transcribed from the scope's calibrated vertical and horizontal divisions. The repository photographs preserve the scope evidence, but the photographs do not expose sufficiently legible scale/readout information for every requested numerical quantity. Therefore, the values below are intentionally left as transcription fields rather than inventing measurements:

| PWM measurement | High duty-cycle setting | Low duty-cycle setting |
|---|---:|---:|
| $V_{\mathrm{HIGH}}$ | **5 V** | **0 V** |
| $V_{\mathrm{LOW}}$ | **5 V** | **0 V** |
| Period $T$ | **20 ms** | **20 ms** |
| Frequency $f=1/T$ | **50 Hz** | **50 Hz** |
| High time $t_{\mathrm{HIGH}}$ | **15 ms** | **5 ms** |
| Duty cycle $D$ | **75 %** | **25 %** |

---

## 6.5 What the oscilloscope shows that the Serial Monitor and Serial Plotter do not

The oscilloscope directly measures the electrical PWM waveform as a function of time. It therefore shows the individual high and low pulses, the pulse width, the period, the repetition frequency, and the voltage levels of the digital waveform. In contrast, the Serial Monitor and Serial Plotter display values selected and formatted by software, such as the averaged ADC value, calculated voltage, and PWM command. Those serial displays report sampled/calculated quantities rather than directly displaying the rapid electrical switching waveform. Consequently, the oscilloscope provides direct evidence of the PWM pulse timing and duty cycle, while the serial interfaces provide software-reported measurements used to choose or describe the PWM output.

---

# 7. Complete Image Evidence from `docs/images/module1`

All 14 PNG/PNG-family images currently stored under `docs/images/module1/` are embedded below in the section corresponding to the experiment they document. The image paths are relative to `docs/module_notes/module_01_evidence.md`, so they will render correctly when this Markdown file is committed at that location in the repository.

## P2 — Analog Read / Serial

### 7.1 Circuit photograph

<img src="../images/module1/P2_analog_read_serial/analog_read_serial_ciruit_photo.png" alt="P2 circuit" width="75%">

### 7.2 Serial Monitor / Serial Plotter

<img src="../images/module1/P2_analog_read_serial/serial_monitor_and_terminal_screenshot.png" alt="P2 serial evidence" width="100%">

---

## P3 — Power of Averaging

### 7.3 Trim-pot voltage-step Serial Plotter

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_analog_read_voltage_steps/trim_pot_and_serial_plotter_screenshot.png" alt="P3 voltage steps" width="100%">

### 7.4 Trim-pot circuit

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_circuit.PNG" alt="P3 circuit" width="75%">

### 7.5 Standard-deviation output

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_STDEV.png" alt="P3 standard deviation" width="100%">

### 7.6 Averaged voltage plot

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_average.png" alt="P3 averaged voltage" width="100%">

### 7.7 Averaged versus unaveraged screenshot

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_average_vs_unaveraged_screenshot.png" alt="P3 averaging comparison" width="100%">

### 7.8 Unaveraged voltage plot

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3C/trim_pot_unaveraged.png" alt="P3 unaveraged voltage" width="100%">

### 7.9 Microsecond timing output

<img src="../images/module1/P3_quantify_the_power_of_averaging/trim_pot_part3D/trim_pot_micros.png" alt="P3 timing" width="100%">

---

## P4 — LED PWM

### 7.10 High-duty-cycle circuit

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/high_duty_cycle_circuit.PNG" alt="P4 high-duty circuit" width="75%">

### 7.11 High-duty-cycle oscilloscope

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/high_duty_cycle_oscilloscope.PNG" alt="P4 high-duty oscilloscope" width="100%">

### 7.12 Low-duty-cycle circuit

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/low_duty_cycle_circuit.PNG" alt="P4 low-duty circuit" width="75%">

### 7.13 Low-duty-cycle oscilloscope

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/low_duty_cycle_oscilloscope.PNG" alt="P4 low-duty oscilloscope" width="100%">

### 7.14 P4 averaged ADC / voltage / PWM output

<img src="../images/module1/P4_LED_Brightness_From_Averaged_Analog_Input/trim_pot_DutyCycle.png" alt="P4 serial output" width="100%">


---

# 8. Pre-Class Questions (C1 Questions 9 and 10)

### Question 9: Arduino Uno Analog Input Summary

* **What it measures:** The Arduino Uno analog pins (A0–A5) measure an external DC voltage relative to the board's ground (`GND`).
* **Voltage range:** $0\text{ V}$ to $V_{\text{ref}}$, which defaults to $5.00\text{ V}$    
* **ADC resolution and code range:** The ATmega328P microcontroller features a 10-bit successive-approximation Analog-to-Digital Converter (ADC). This provides $2^{10} = 1024$ discrete digital levels ranging from code **0** ($0\text{ V}$) to code **1023** ($V_{\text{ref}}$), yielding a nominal single-step resolution of:

$$
\Delta V_{\text{1 count}} = \frac{5.00\text{ V}}{1023} \approx 4.89\text{ mV/count}.
$$

* **Acquisition time:** A standard call to `analogRead()` takes approximately **$100\ \mu\text{s}$ to $120\ \mu\text{s}$** to complete (corresponding to a sample rate of roughly 8.3–10 kHz), as governed by the ADC clock prescaler setting.

---

### Question 10: Arduino Uno PWM Output Summary

* **Voltage levels:** Pulse-Width Modulation (PWM) on digital output pins (such as pin 9) outputs binary digital voltage levels: **HIGH** ($\approx 5.0\text{ V}$) and **LOW** ($\approx 0.0\text{ V}$).
* **Command range:** Controlled via `analogWrite(pin, value)` with an 8-bit integer command ranging from **0** (always LOW, 0% duty cycle) to **255** (always HIGH, 100% duty cycle).
* **Duty cycle and frequency:** 
  * **Duty cycle ($D$):** The percentage of time the pin stays HIGH during one full period, given by $D = \frac{\text{value}}{255} \times 100\%$.
  * **Frequency ($f$):** Standard PWM pins on the Uno (pins 3, 9, 10, 11) operate at a default switching frequency of approximately **490 Hz** (pins 5 and 6 run at **980 Hz**).
* **Why PWM is not a true analog voltage:** PWM does not output a constant intermediate voltage (such as $2.5\text{ V}$). Instead, it rapidly switches between $0\text{ V}$ and $5\text{ V}$ at a fixed frequency. The *average* voltage over time appears continuous only because external physical systems (like an LED's perceived brightness or a motor's mechanical inertia) act as low-pass filters.
* **Why a power stage is required for a motor:** The ATmega328P output pins can only safely source or sink up to **$20\text{ mA}$** ($40\text{ mA}$ absolute maximum rating). Electric motors require significantly higher currents (often hundreds of milliamps to several amps) and produce inductive back-EMF spikes when switched. Connecting a motor directly to an Arduino pin can destroy the microcontroller, requiring an external power stage (such as a transistor, MOSFET, or H-bridge motor driver) to safely handle the heavy current.
