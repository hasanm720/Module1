"""Part 5 guided analysis. Run with python3 analysis.py; no packages needed.

Inputs below are transcribed from the supplied graph legend and Laird PDF,
not extracted automatically. Update them if those source files change.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE.parents[2] / 'docs/other_files/module4/P4_Temperature_susceptibility/temperature_vs_signed_pwm.png'
DATASHEET = HERE / 'laird-tec-cp14-127-045.pdf'

# Graph legend: both slopes are positive versus SIGNED PWM.
HEATING_SLOPE = 0.531  # degrees C per PWM count; fit from 0 to +43
COOLING_SLOPE = 0.188  # degrees C per signed PWM count; fit from -63 to 0

# Laird CP14-127-045-L2-W4.5, part 58910-501, page 3, 27 C column.
R_EL = 1.50       # ohms
I_MAX = 8.6       # amperes
Q_C_MAX = 71.3    # watts, at Delta T = 0
DELTA_T_MAX = 70.5  # kelvin, at Qc = 0


def main():
    for source in (GRAPH, DATASHEET):
        if not source.is_file():
            raise SystemExit(f'Missing source file: {source}')

    ratio = HEATING_SLOPE / abs(COOLING_SLOPE)
    joule_fraction = (ratio - 1) / (ratio + 1)
    q_j_max = 0.5 * I_MAX**2 * R_EL
    # Use the maximum-current construction specified in Part 5.
    q_p_max = Q_C_MAX + q_j_max
    laird_ratio = (q_p_max + q_j_max) / (q_p_max - q_j_max)
    difference = 100 * (ratio / laird_ratio - 1)

    report = f"""PART 5: GUIDED HEATING/COOLING ENERGY-BALANCE ANALYSIS

Sources
Graph: {GRAPH}
Data sheet: {DATASHEET}
Laird CP14-127-045-L2-W4.5, part 58910-501, revision 00 (2022-06-01), p. 3.
Inputs are transcribed from these sources; the graph legend rounds its slopes.

1. MEASURE THE TWO SLOPES
Heating: m_h = +{HEATING_SLOPE:.3f} degrees C/PWM count, PWM 0 to 43.
Cooling: m_c = -{COOLING_SLOPE:.3f} degrees C/PWM count versus cooling PWM
magnitude (0 to 63). On the supplied signed-PWM graph (-63 to 0), its slope
is positive: +{COOLING_SLOPE:.3f} degrees C/count. The magnitude is the same.
r = m_h / |m_c| = {ratio:.4f}, approximately {ratio:.2f}.
Both branches are approximately straight over these ranges, with small
point-to-line deviations and slight variation of local slope, rather than
strong curvature. The plotted min-max bars are not statistical uncertainties.

2. USE STEADY-STATE ENERGY BALANCE
Let T_o be object temperature, T_0 the zero-PWM temperature, C its thermal
capacitance, and G the effective passive thermal conductance. Include TEC
conduction and other passive heat leaks in G, once only; Q_TEC below contains
only the current-dependent Peltier and object-face Joule terms.

C dT_o/dt = Q_TEC - G(T_o - T_0).
At steady state dT_o/dt = 0, so G(T_o - T_0) = Q_TEC.
The individual heat flows need not be zero; their sum is zero.

PWM proof: let one period be tau, with current I for D*tau and zero otherwise.
<i> = (1/tau) integral_0^tau i(t) dt = I*(D*tau)/tau = D*I.
<i^2> = (1/tau) integral_0^tau i(t)^2 dt = I^2*(D*tau)/tau = D*I^2.
But <i>^2 = D^2*I^2, so <i^2> - <i>^2 = D*(1-D)*I^2.
Thus the mean square differs from the square of the mean for 0 < D < 1.
Peltier transport is proportional to <i>; Joule heating to <i^2>. At fixed
ON-current, both therefore scale linearly with D. Replacing the pulses with
DC current D*I would incorrectly make Joule heating quadratic in D and
predict a duty-dependent slope. The approximately linear graph is consistent
with the pulsed model, though it does not independently prove the waveform.

Let Q_P > 0 and Q_J > 0 be the ON-state Peltier and object-face Joule powers.
Q_TEC,h = D*(Q_P + Q_J); Q_TEC,c = D*(-Q_P + Q_J).
T_o,h - T_0 = D*(Q_P + Q_J)/G.
T_o,c - T_0 = D*(-Q_P + Q_J)/G.
dT_o,h/dD = (Q_P + Q_J)/G; |dT_o,c/dD| = (Q_P - Q_J)/G.
Since D = PWM/255, both PWM slopes gain the same factor 1/255, which cancels:
r = (Q_P + Q_J)/(Q_P - Q_J).
r*(Q_P - Q_J) = Q_P + Q_J implies (r-1)*Q_P = (r+1)*Q_J.
Therefore Q_J/Q_P = (r-1)/(r+1) = {joule_fraction:.4f}.
Check: r = 2 gives Q_J/Q_P = 1/3.
This inference assumes comparable ON-current and G in both directions and
approximately constant properties; it is not an absolute heat-flow measurement.

Signed-duty formulation: let s be signed PWM, u = s/255, and D = |u|.
Q_TEC = u*Q_P + |u|*Q_J.
For u >= 0: T_o,h - T_0 = u*(Q_P + Q_J)/G.
For u <= 0: T_o,c - T_0 = u*(Q_P - Q_J)/G.
dT_o,h/du = (Q_P + Q_J)/G; dT_o,c/du = (Q_P - Q_J)/G.
Both are positive when Q_P > Q_J. Each signed-PWM slope includes 1/255,
so their ratio is the same r calculated above.

3. FIND AND USE THE LAIRD MAXIMUM-CURRENT DATA
All four entries below come from page 3's hot-side temperature 27 degrees C column:
- R_el = {R_EL:.2f} ohms: module electrical resistance at the listed temperature.
- I_max = {I_MAX:.1f} A: the sheet labels this as current at Delta T_max.
- Q_c,max = {Q_C_MAX:.1f} W: maximum cold-side heat removal at Delta T = 0.
- Delta T_max = {DELTA_T_MAX:.1f} K: maximum face-to-face temperature difference
  at Qc = 0 (zero cold-side heat load), not an absolute operating temperature.

Following the simplified maximum-current construction requested in Part 5,
Delta T = 0 removes passive TEC conduction and half the Joule power reaches
the object face:
Q_J,max = (1/2)*I_max^2*R_el
        = (1/2)*{I_MAX:.1f}^2*{R_EL:.2f} = {q_j_max:.2f} W.
Q_c,max = Q_P,max - Q_J,max, hence
Q_P,max = {Q_C_MAX:.1f} + {q_j_max:.2f} = {q_p_max:.2f} W.
r_Laird,max = (Q_P,max + Q_J,max)/(Q_P,max - Q_J,max)
            = {q_p_max + q_j_max:.2f}/{Q_C_MAX:.2f} = {laird_ratio:.4f}.
These are thermal powers in watts. This is the assignment's simplified
rating-based prediction, not a claim that all listed maxima share one test
condition or that the lab operates at I_max.

4. INTERPRET THE COMPARISON
Measured r = {ratio:.4f}; Laird maximum-current prediction = {laird_ratio:.4f}.
The measured ratio is {difference:.1f}% higher relative to that prediction.
Agreement is not required: D = 1 means the H-bridge is continuously ON, not
that current equals I_max. Current depends on supply voltage/current limit,
bridge voltage drop, wiring, and TEC resistance. The data-sheet conditions
also differ from PWM operation; finite face-temperature differences, passive
heat paths, changing material properties, and slight graph curvature can
change the measured ratio. The graph alone does not isolate their contributions.

When the object is hotter than room temperature, passive heat flows outward;
when colder, heat flows inward. Approximately symmetric conduction therefore
opposes both heating and cooling and limits both temperature excursions.
It cancels from the ratio when G is the same for both directions, so it cannot
by itself explain unequal slope magnitudes. Peltier transport reverses with
current, while Joule heating always adds heat: it assists heating and opposes
cooling. No additional physical measurements are required for this analysis.

5. CONCLUSION
The measured heating slope is 0.531 °C per PWM count, while the cooling slope versus signed PWM is 0.188 °C per count, giving a ratio of 2.82. Under the symmetric, fixed-current model, this implies that object-face Joule heating is about 47.7% of the Peltier heat-transfer magnitude. Peltier transport reverses with current, whereas Joule heating always adds heat, assisting heating and opposing cooling. PWM makes both contributions proportional to duty cycle, consistent with the approximately linear measured branches. Passive conduction opposes both temperature excursions and cancels from the ratio when its conductance is equal in both directions. The measured ratio is about 10.5% higher than the manufacturer-based prediction of 2.56. Different operating currents, face temperatures, and thermal conditions limit this comparison; the result is a model-based inference rather than a direct heat-flow measurement.
"""
    output = HERE / 'part5_answers.txt'
    output.write_text(report, encoding='utf-8')
    print(report)
    print(f'Saved answers to: {output}')


if __name__ == '__main__':
    main()
