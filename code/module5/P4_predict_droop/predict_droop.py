"""Predict Part 4 droop and overlay the Part 3 measurements.

Run: python3 predict_droop.py --ambient 27
The default ambient is the provisional value in Part 3, not a verified measurement.
Requires matplotlib. Outputs are saved beside this script.
"""
import argparse
import csv
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TABLE = HERE.parent / 'P3_measure_droop_vs_gain/part3_table.md'
SUSCEPTIBILITY = ROOT / 'docs/other_files/module4/P4_Temperature_susceptibility/susceptibility_results.md'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ambient', type=float, default=27.0,
                        help='Module 5 ambient temperature in °C (default 27 is provisional)')
    args = parser.parse_args()
    if not float('-inf') < args.ambient < float('inf'):
        parser.error('Ambient temperature must be finite.')
    # Read the measured Module 4 linear-fit slopes, rather than Part 3's placeholder.
    slopes = {}
    for line in SUSCEPTIBILITY.read_text().splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] in ('Heating', 'Cooling'):
            slopes[cells[0]] = abs(float(cells[2]))
    rows = []
    for line in TABLE.read_text().splitlines():
        cells = [c.strip().replace('**', '') for c in line.strip('|').split('|')]
        if not re.fullmatch(r'\d+(?:\.\d+)?', cells[0]):
            continue
        gain, target, settled = float(cells[0]), float(cells[2]), float(cells[3])
        direction = 'Heating' if target > args.ambient else 'Cooling'
        chi = slopes[direction]
        loop_gain = chi * gain
        initial_error = target - args.ambient
        predicted = initial_error / (1 + loop_gain)
        measured = target - settled
        rows.append((gain, target, settled, direction, chi, loop_gain, predicted,
                     measured, target - predicted,
                     measured / initial_error if initial_error else None,
                     1 / (1 + loop_gain) if initial_error else None))
    if not rows:
        raise ValueError('No measurements found in Part 3 table.')
    with (HERE / 'droop_predictions.csv').open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['Kp_PWM_per_C', 'setpoint_C', 'measured_Tss_C', 'direction',
                         'chi_C_per_PWM', 'L', 'predicted_signed_droop_C',
                         'measured_signed_droop_C', 'predicted_Tss_C',
                         'measured_fractional_droop', 'predicted_fractional_droop'])
        writer.writerows(rows)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot([r[0] for r in rows], [r[7] for r in rows], 'o-', label='Measured (Part 3)')
    ax.plot([r[0] for r in rows], [r[6] for r in rows], 's--', label='Predicted (Module 4 model)')
    ax.set(xlabel='Proportional gain Kp (PWM counts/°C)',
           ylabel='Signed droop: Tset − Tss (°C)', title='Predicted and measured steady-state droop')
    ax.grid(alpha=0.25)
    ax.legend()
    fig.text(0.5, 0.02, f'Ambient = {args.ambient:g} °C (verify Module 5 measurement); '
             f'heating χ = {slopes["Heating"]:.4f} °C/PWM count', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    for extension in ('png', 'pdf'):
        fig.savefig(HERE / f'droop_vs_gain.{extension}', dpi=200)
    plt.close(fig)

    report = [
        '# Part 4: Predict droop from Module 4', '',
        '## Inputs and assumptions', '',
        f'- Module 5 ambient: **{args.ambient:g} °C**. The default 27 °C is explicitly marked '
        'as a placeholder in Part 3; verify it before treating this comparison as final.',
        '- Setpoint and settled temperatures are read from `../P3_measure_droop_vs_gain/part3_table.md`.',
        f'- Module 4 heating linear-fit susceptibility: **{slopes["Heating"]:.4f} °C/PWM count**.',
        f'- Cooling susceptibility magnitude: **{slopes["Cooling"]:.4f} °C/PWM count** '
        '(used automatically for a setpoint below ambient).',
        '- PWM counts are the model input P, not electrical power in watts.', '',
        '## Derivation', '',
        r'$$T_{ss}=T_{amb}+\chi_{T,h}P,\qquad P=K_p(T_{set}-T_{ss}).$$', '',
        r'$$T_{set}-T_{ss}=\frac{T_{set}-T_{amb}}{1+\chi_{T,h}K_p},\qquad L=\chi_{T,h}K_p.$$', '',
        r'The product $L$ is dimensionless: $(\mathrm{°C/PWM})(\mathrm{PWM/°C})=1$.', '',
        r'$$\frac{T_{set}-T_{ss}}{T_{set}-T_{amb}}=\frac{1}{1+L}.$$', '',
        'For cooling, use |χ| with the same signed formula, or compare the magnitudes '
        'of numerator and denominator. Fractional droop is undefined for an ambient setpoint.', '',
        '## Predictions and measurements', '',
        '| Kp (PWM/°C) | L | Predicted droop (°C) | Measured droop (°C) | Predicted Tss (°C) | Predicted fraction | Measured fraction |',
        '|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for r in rows:
        fractions = [f'{value:.3f}' if value is not None else 'undefined' for value in r[10:11] + r[9:10]]
        report.append(f'| {r[0]:g} | {r[5]:.4f} | {r[6]:.3f} | {r[7]:.3f} | {r[8]:.3f} | {fractions[0]} | {fractions[1]} |')
    report.extend(['', '![Predicted and measured droop](droop_vs_gain.png)', '',
                   '## Interpretation and data checks', '',
                   'Both the model and the measurements show decreasing droop as gain increases. '
                   'For L ≪ 1, nearly all initial error remains; at L = 1, half remains; '
                   'for L ≫ 1, the fraction approaches 1/L.', '',
                   'The model assumes a steady state, a linear response, a consistent ambient '
                   'temperature, and no PWM saturation. Rounded integer PWM and experimental '
                   'drift can cause deviations. Module 4 recorded temperature ranges do not '
                   'establish statistical uncertainty or a settling criterion.', '',
                   'Part 3 still contains placeholder χ = 0.10. Its stated required PWM of 80 '
                   'is inconsistent with its stated 3 °C initial error and that susceptibility '
                   '(which imply 30 counts). With the measured heating slope and a 3 °C '
                   f'initial error, the model requires {3 / slopes["Heating"]:.2f} counts to reach the setpoint.', '',
                   'Part 3’s initial PWM column also disagrees with Kp × 3 for gains 4 and 5 '
                   '(expected 12 and 15). Predictions here use the gains and temperatures directly.', ''])
    if any(r[3] == 'Heating' and r[2] < args.ambient for r in rows):
        report.extend(['Some measured heating temperatures are below the assumed ambient. '
                       'The positive heating-susceptibility model cannot explain those points; '
                       'verify the actual Module 5 ambient, settled readings, and output direction. '
                       'Do not substitute Module 4’s ambient for an unmeasured Module 5 ambient.', ''])
    report.extend(['## Regenerate', '', '```sh', 'python3 predict_droop.py --ambient 27',
                   '```', '', 'Replace 27 with the actual Module 5 ambient. Outputs: this report, '
                   '`droop_predictions.csv`, and `droop_vs_gain.png` / `.pdf`.', ''])
    (HERE / 'PART4_PREDICTED_DROOP.md').write_text('\n'.join(report))
    print(f'Saved Part 4 predictions, report, and PNG/PDF plot to {HERE}')


if __name__ == '__main__':
    main()
