# A2 — TEC Heating and Cooling Analysis

MISSING A LOT, REVIEW LIST AT THE END


**Course:** Phys 39 — Instrumentation and Thermal Physics  
**Module:** Module 4 — Open-Loop TEC Calibration and Software Safety  
**Repository:** https://github.com/hasanm720/Module1.git  
**Assignment:** A2 — Open-Loop TEC Heating and Cooling Analysis

> **Data-status note:** The existing Module 1 repository/evidence and prior work provide the Arduino/PWM framework, but the actual Module 4 heating/cooling class dataset was not available in the material used to prepare this document. Therefore, experimental temperature points, fitted slopes, and the measured slope ratio are **not fabricated**. The sections below contain the required analysis and clearly marked locations for the actual Module 4 measurements.

---

## 1. Part 4 — Temperature vs. Signed PWM

The Part 4 measurement should plot the steady-state object temperature against **signed PWM**. Heating and cooling are treated as separate datasets:

- **Positive signed PWM:** heating
- **Negative signed PWM:** cooling
- The horizontal axis is signed PWM command, \(u\), in Arduino PWM counts.
- The vertical axis is steady-state temperature, \(T\), in °C.
- Each branch should have its own fitted line over the range actually used in the experiment.

### Part 4 Graph

Replace the placeholder below with the actual Part 4 graph generated from the Module 4 class data.

![Part 4 temperature vs signed PWM](../images/module4/part4_temperature_vs_signed_pwm.png)

**Figure 1.** Steady-state temperature versus signed PWM. Heating and cooling measurements should be displayed as separate datasets with independent linear fits over their respective fitting ranges.

### Measured slopes

| Quantity | Heating | Cooling |
|---|---:|---:|
| PWM range used | `[insert class-data range]` | `[insert class-data range]` |
| Fitted slope | \(m_h =\) `[insert]` °C/PWM | \(m_c =\) `[insert]` °C/PWM |
| Slope definition | \(m_h=dT/du\) | \(m_c=dT/du\) |
| Slope ratio | \(r=m_h/m_c=\) `[insert]` | — |

The slope ratio is

\[
r=\frac{m_h}{m_c}.
\]

The ratio is useful because the common thermal conductance and PWM scaling factors cancel when the two branches are compared.

---

## 2. PWM Averaging and Steady-State Energy Balance

For a PWM signal with duty cycle

\[
D=\frac{|u|}{255},
\]

the TEC current is present only during the fraction \(D\) of each PWM period.

If the on-state current is \(I\), then over one PWM period \(\tau\),

\[
\langle I\rangle
=
\frac{1}{\tau}\int_0^\tau I(t)\,dt.
\]

Since \(I(t)=I\) for \(D\tau\) and zero otherwise,

\[
\boxed{\langle I\rangle=DI}.
\]

The average of the squared current is

\[
\langle I^2\rangle
=
\frac{1}{\tau}\int_0^\tau I^2(t)\,dt
=
DI^2.
\]

Therefore,

\[
\boxed{\langle I^2\rangle=DI^2}.
\]

Importantly,

\[
\langle I\rangle^2=D^2I^2
\]

is **not** equal to \(\langle I^2\rangle\) except at special duty cycles. This distinction matters because the Peltier contribution depends on current while Joule heating depends on current squared.

### Steady-state thermal balance

For the simple thermal model,

\[
C\frac{dT}{dt}
=
\dot Q_{\mathrm{TEC}}
-
G(T-T_0),
\]

where:

- \(C\) is the effective thermal capacitance,
- \(G\) is the thermal conductance to the surroundings,
- \(T_0\) is the ambient temperature,
- \(\dot Q_{\mathrm{TEC}}\) is the net heat transported by the TEC.

At steady state,

\[
\frac{dT}{dt}=0,
\]

so

\[
\boxed{G(T-T_0)=\dot Q_{\mathrm{TEC}}}.
\]

For heating, the Peltier and Joule contributions add at the object side:

\[
\dot Q_{\mathrm{TEC,h}}
=
D(\dot Q_P+\dot Q_J).
\]

For cooling, reversing current reverses the Peltier term while Joule heating remains positive:

\[
\dot Q_{\mathrm{TEC,c}}
=
D(\dot Q_P-\dot Q_J).
\]

Therefore,

\[
\frac{dT_h}{dD}
=
\frac{\dot Q_P+\dot Q_J}{G},
\]

and

\[
\frac{dT_c}{dD}
=
\frac{\dot Q_P-\dot Q_J}{G}.
\]

Because

\[
u=255D,
\]

the measured slopes with respect to PWM counts are

\[
m_h
=
\frac{\dot Q_P+\dot Q_J}{255G}
\]

and

\[
m_c
=
\frac{\dot Q_P-\dot Q_J}{255G}.
\]

Taking their ratio gives

\[
r
=
\frac{m_h}{m_c}
=
\frac{\dot Q_P+\dot Q_J}
{\dot Q_P-\dot Q_J}.
\]

Solving for the Joule-to-Peltier ratio,

\[
r(\dot Q_P-\dot Q_J)
=
\dot Q_P+\dot Q_J,
\]

so

\[
(r-1)\dot Q_P
=
(r+1)\dot Q_J.
\]

Thus,

\[
\boxed{
\frac{\dot Q_J}{\dot Q_P}
=
\frac{r-1}{r+1}
}.
\]

### Experimental result

Using the actual fitted slopes,

\[
r=\frac{m_h}{m_c}
=
\boxed{\text{[insert measured ratio]}}.
\]

Therefore,

\[
\boxed{
\frac{\dot Q_J}{\dot Q_P}
=
\frac{r-1}{r+1}
=
\text{[insert numerical result]}
}.
\]

---

## 3. Laird Data-Sheet Values and Predicted Ratio

The Laird/Tark **CP14-127-045-L1-W4.5** thermoelectric module provides the manufacturer reference values needed for comparison.

For the relevant data-sheet condition of approximately \(T_\mathrm{hot}=27^\circ\mathrm C\):

| Parameter | Data-sheet value | Meaning |
|---|---:|---|
| \(R_M\) | \(1.50\,\Omega\) | Module electrical resistance at the specified condition |
| \(I_\mathrm{max}\) | \(8.6\,A\) | Maximum specified current |
| \(Q_{c,\mathrm{max}}\) | \(71.3\,W\) | Maximum cold-side heat pumping at \(\Delta T=0\) |
| \(\Delta T_\mathrm{max}\) | \(70.5^\circ\mathrm C\) | Maximum temperature difference at \(Q_c=0\) |

### Joule heating at \(I_\mathrm{max}\)

The electrical Joule heating generated in the TEC is

\[
\dot Q_{J,\mathrm{total}}
=
I_\mathrm{max}^2R_M.
\]

Using the maximum-current data,

\[
I_\mathrm{max}^2R_M
=
(8.6\,A)^2(1.50\,\Omega)
=
110.94\,W.
\]

For the simplified symmetric model, half of this Joule heat is assigned to the object/cold-side face:

\[
\dot Q_{J,\mathrm{max}}
=
\frac12 I_\mathrm{max}^2R_M
=
\boxed{55.47\,W}.
\]

At \(\Delta T=0\),

\[
Q_{c,\mathrm{max}}
=
\dot Q_{P,\mathrm{max}}
-
\dot Q_{J,\mathrm{max}}.
\]

Therefore,

\[
\dot Q_{P,\mathrm{max}}
=
Q_{c,\mathrm{max}}
+
\dot Q_{J,\mathrm{max}},
\]

giving

\[
\dot Q_{P,\mathrm{max}}
=
71.3\,W+55.47\,W
=
\boxed{126.77\,W}.
\]

The predicted heating/cooling ratio is then

\[
r_\mathrm{Laird}
=
\frac{\dot Q_P+\dot Q_J}
{\dot Q_P-\dot Q_J}.
\]

Substituting the values above,

\[
r_\mathrm{Laird}
=
\frac{126.77+55.47}
{126.77-55.47}
\]

\[
\boxed{r_\mathrm{Laird}\approx2.556}.
\]

The corresponding Joule-to-Peltier ratio is

\[
\frac{\dot Q_J}{\dot Q_P}
=
\frac{55.47}{126.77}
\approx
\boxed{0.437}.
\]

### Important operating-condition limitation

The data-sheet value \(I_\mathrm{max}=8.6\,A\) is a **maximum-current specification**, not a statement that the experimental TEC actually operated at 8.6 A.

A PWM command of \(D=1\) means the H-bridge is continuously on; it does **not** automatically mean that the TEC current equals \(I_\mathrm{max}\). Actual current depends on the supply voltage, H-bridge voltage drop, wiring resistance, TEC resistance, current limiting, and the TEC's temperature-dependent operating condition.

Consequently, the calculated

\[
r_\mathrm{Laird}=2.556
\]

is a manufacturer-based reference prediction under the stated assumptions, not necessarily the expected experimental ratio.

---

## 4. Comparison of Measured and Data-Sheet Ratios

The required comparison is:

\[
r_\mathrm{measured}
=
\boxed{\text{[insert measured }m_h/m_c\text{]}}
\]

versus

\[
r_\mathrm{Laird}
=
\boxed{2.556}.
\]

A numerical percent difference can be calculated as

\[
\%\text{ difference}
=
\frac{|r_\mathrm{measured}-r_\mathrm{Laird}|}
{r_\mathrm{Laird}}
\times100\%.
\]

Thus,

\[
\%\text{ difference}
=
\boxed{\text{[insert calculated percentage]}}.
\]

The comparison should be interpreted in light of the different operating conditions. The data-sheet calculation uses manufacturer maximum-current values at a specified hot-side temperature and the simplified assumption that Joule heat is divided symmetrically between the two sides. The experiment instead uses PWM control, finite temperature differences, a particular thermal mounting arrangement, passive heat conduction, and the actual current delivered by the H-bridge.

---

## 5. Passive Conduction

Passive thermal conduction always transfers heat from the hotter region toward the cooler region.

For an object at temperature \(T\) in an environment at \(T_0\), the simplified passive-conduction term is

\[
\boxed{
\dot Q_\mathrm{cond}=-G(T-T_0)
}.
\]

### During heating

When

\[
T>T_0,
\]

the object loses heat to the surroundings. Passive conduction therefore **opposes heating**.

### During cooling

When

\[
T<T_0,
\]

the surroundings transfer heat toward the colder object. Passive conduction therefore **opposes cooling**.

Passive conduction alone does not explain why the heating and cooling slopes have different magnitudes. In the simplified TEC model, the important asymmetry comes from the fact that reversing current reverses the Peltier contribution but leaves Joule heating positive. Real apparatus effects—thermal contact resistance, heat leakage, temperature-dependent material properties, mounting geometry, and imperfect current control—can further change the measured slopes.

---

## 6. Conclusion

The open-loop TEC calibration relates steady-state block temperature to signed PWM and separates the heating and cooling responses. PWM averaging shows that the cycle-averaged current and squared current are both proportional to duty cycle, allowing the Peltier and Joule contributions to produce an approximately linear temperature response when the on-state current is approximately fixed. Reversing current changes the sign of Peltier transport but does not change the sign of Joule heating, so the heating and cooling branches need not have equal slopes. Passive conduction opposes both heating and cooling by carrying heat toward the surroundings, but it is not by itself an explanation for unequal branch magnitudes. The Laird maximum-current calculation gives a reference ratio of \(r=2.556\) under the stated assumptions. The experimental comparison should use the measured slope ratio and account for the actual current, finite temperature differences, PWM operation, passive heat paths, and any curvature in the measured response.

---

## References

1. Seth Fraden, **Phys 39 | Instrumentation and Thermal Physics — Module 4: Open-Loop TEC Calibration and Software Safety**.  
   https://sethfraden.github.io/Phys39F26-course/labs/lab-04/

2. Laird Thermal Systems, **CP14-127-045-L1-W4.5 Thermoelectric Module Data Sheet**.  
   https://lairdthermal.com/datasheets/datasheet-CP14-127-045-L1-W4.5.pdf

3. Existing course repository and Module 1 evidence:  
   https://github.com/hasanm720/Module1.git

---

## Final Submission Checklist

- [ ] Insert the actual Part 4 heating measurements.
- [ ] Insert the actual Part 4 cooling measurements.
- [ ] Generate and insert the heating/cooling graph with separate fitted lines.
- [ ] Insert the heating slope \(m_h\), including units.
- [ ] Insert the cooling slope \(m_c\), including units.
- [ ] Calculate and insert \(r=m_h/m_c\).
- [ ] Calculate and insert \(\dot Q_J/\dot Q_P=(r-1)/(r+1)\).
- [x] Include the Laird data-sheet values and operating conditions.
- [x] Include the Laird reference calculation \(r_\mathrm{Laird}\approx2.556\).
- [x] Explain passive conduction.
- [x] Include a concise conclusion.
- [ ] Verify all image paths after placing the Markdown file in the repository.
