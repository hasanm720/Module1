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
    fig.savefig(HERE / 'droop_vs_gain.png', dpi=200)
    plt.close(fig)

    print(f'Saved Part 4 predictions and PNG plot to {HERE}')


if __name__ == '__main__':
    main()
