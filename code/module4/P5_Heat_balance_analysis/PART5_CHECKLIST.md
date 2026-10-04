# Part 5 completion checklist

Reviewed October 4, 2026 against the local Module 4 assignment PDF, Part 5 (pages 7–10) and A2 submission requirements (page 11). Checked the existing answers against the Part 4 graph and the supplied Laird PDF.

**Status: Part 5 revisions and the two-page A2 PDF are complete. Moodle upload remains.**

Final file: [A2_Chen_Hasan.pdf](../../../docs/module_notes/A2_Chen_Hasan.pdf). Editable layout: [A2_Chen_Hasan.html](../../../docs/module_notes/A2_Chen_Hasan.html). Rebuild with [build_a2_pdf.py](build_a2_pdf.py), which requires PySide6.

## Completed analysis

- [x] Existing Part 4 graph has separate heating/cooling measurements, fitted lines, labeled axes, and units. It is embedded in [part5_answers.md](part5_answers.md).
- [x] Report slopes and fit ranges: heating +0.531 °C/count over 0 to +43; cooling +0.188 °C/count versus signed PWM over −63 to 0.
- [x] Explain that cooling has slope −0.188 °C/count when expressed versus increasing cooling PWM magnitude instead.
- [x] Calculate the measured slope-magnitude ratio: r = 2.8245, approximately 2.82.
- [x] Discuss approximate linearity, small deviations, and the meaning of the plotted min–max bars.
- [x] Derive cycle averages ⟨i⟩ = DI and ⟨i²⟩ = DI² and distinguish ⟨i²⟩ from ⟨i⟩².
- [x] Explain why ideal PWM gives linear Peltier and Joule contributions in duty cycle and connect this to the measured graph.
- [x] Write the thermal energy balance and impose steady state; include passive TEC conduction in G only once.
- [x] Derive the heating/cooling temperatures and slope magnitudes.
- [x] Derive Q_J/Q_P = (r − 1)/(r + 1) = 0.4771 and check that r = 2 gives 1/3.
- [x] Cite the supplied Laird CP14-127-045-L2-W4.5 sheet, page 3, 27 °C column; explain values and conditions: R = 1.50 Ω, I_max = 8.6 A, Q_c,max = 71.3 W, ΔT_max = 70.5 K.
- [x] Calculate object-face Joule heat: Q_J,max = 55.47 W.
- [x] Calculate Peltier heat: Q_P,max = 126.77 W.
- [x] Calculate the assignment's simplified manufacturer prediction: r_Laird = 2.5560.
- [x] Compare ratios: the measured value is about 10.5% higher than the prediction.
- [x] Explain why full duty cycle does not guarantee the rated maximum current; discuss PWM, temperature differences, material properties, passive paths, and fit curvature.
- [x] Explain passive heat-flow directions and why symmetric conduction alone does not explain unequal slope magnitudes.
- [x] Provide a calculation script and matching text output. Checked [analysis.py](analysis.py) with file writing intercepted: its generated report exactly matches [part5_answers.txt](part5_answers.txt), and both source paths exist.

## Part 5 adjustment before submission

- [x] Express the slope derivation explicitly using the assignment's **signed duty cycle** u = signed PWM/255. The answers now include the signed-duty derivation alongside the equivalent nonnegative-magnitude derivation: Q_TEC = u Q_P + |u| Q_J; then T_h − T_0 = u(Q_P + Q_J)/G for u ≥ 0 and T_c − T_0 = u(Q_P − Q_J)/G for u ≤ 0. Thus dT_h/du = (Q_P + Q_J)/G and dT_c/du = (Q_P − Q_J)/G. Use positive signed-PWM slopes in the final report, keeping the existing sign-convention explanation.

## Remaining A2 submission work (Part 6)

- [x] Assemble the graph and condensed Part 5 analysis into a legible **one-to-two-page PDF**. Created A2_Chen_Hasan.pdf and visually checked both pages, including the graph, equations, table, conclusion, and references.
- [x] Add a **100–150-word conclusion** using the measured results. A standalone conclusion is now included in the Markdown, generated text, updated evidence document, and PDF.
- [x] If reusing [module_04_evidence.md](../../../docs/module_notes/module_04_evidence.md), replace its obsolete missing-data statements, placeholders, broken graph path, and L1 data-sheet reference with the existing results and supplied L2 reference. The older draft has been replaced with the complete current working analysis and corrected relative links.
- [x] Include an accurate note on how steady state was selected. The current graph honestly states that the source table does not document a settling-time/drift criterion. The final PDF retains this limitation; the available table does not establish the assignment's three-time-constant plus one-minute check.
- [x] Name the final file `A2_Lastname_Lastname.pdf` and check page count, equation rendering, graph readability, citations, and consistency of numerical precision.
- [ ] Each teammate uploads the team PDF separately to Moodle. The supplied assignment lists October 5 at 6:00 PM as the deadline. Upload status was not checked.

## Precision note

Part 5 deliberately uses rounded graph labels, giving r = 2.8245. The [Part 4 results](../../../docs/other_files/module4/P4_Temperature_susceptibility/susceptibility_results.md) use unrounded fit coefficients and report r = 2.8289. This is a rounding difference, not a missing calculation. Use one convention consistently in the final PDF.

No additional physical measurements are required by Part 5. The answers, script output, older submission draft, and final PDF now incorporate the completed revisions. Physical steady-state validation cannot be established from the existing table alone.
