"""Plot the Module 4 Markdown measurements. Requires numpy and matplotlib.

Run from any directory: python3 /path/to/plot_temperature_susceptibility.py
Use --steady-state-note to supply the actual experimental selection criterion.
"""
from pathlib import Path
import argparse
import re
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TABLE = ROOT / 'docs/other_files/module4/P2_PWM_calibration table/PWM_calibration_tables.md'
DEFAULT_OUTPUT = ROOT / 'docs/other_files/module4/P4_Temperature_susceptibility'
DEFAULT_NOTE = (
    'Recorded temperature ranges are treated as steady-state observations; points '
    'are range midpoints and error bars show the recorded min–max range, not statistical '
    'uncertainty. The table does not document a settling-time or drift criterion.'
)


def read_table(path):
    groups = {'Heating': [], 'Cooling': []}
    for line in path.read_text().splitlines():
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if not cells or cells[0] not in groups:
            continue
        direction = cells[0]
        pwm = int(cells[1])
        bounds = re.fullmatch(r'([+-]?\d+(?:\.\d+)?)\s*[-–]\s*([+-]?\d+(?:\.\d+)?)', cells[2])
        if bounds:
            low, high = map(float, bounds.groups())
        else:
            low = high = float(cells[2])
        if not 0 <= pwm <= 255 or low > high:
            raise ValueError(f'Invalid measurement: {line}')
        signed_pwm = pwm if direction == 'Heating' else -pwm
        groups[direction].append((signed_pwm, (low + high) / 2, (high - low) / 2))
    for direction, rows in groups.items():
        rows.sort()
        if len(rows) < 2 or len({row[0] for row in rows}) != len(rows):
            raise ValueError(f'{direction} requires at least two distinct PWM settings.')
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', type=Path, default=DEFAULT_TABLE)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--steady-state-note', default=DEFAULT_NOTE)
    args = parser.parse_args()
    groups = read_table(args.table)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6.5))
    report = ['# Temperature susceptibility', '', f'Source: {args.table.name}', '',
              args.steady_state_note, '',
              'Signed PWM is positive for heating and negative for cooling. '
              'Susceptibility is ΔT / Δ(signed PWM), in °C per PWM count.', '',
              '| Direction | Endpoint finite difference (°C/count) | Linear fit (°C/count) | R² | Local slope range (°C/count) |',
              '|---|---:|---:|---:|---:|']
    local_sections = []
    for direction, color in [('Heating', 'red'), ('Cooling', 'blue')]:
        x, y, error = np.array(groups[direction]).T
        slope, intercept = np.polyfit(x, y, 1)
        residual = y - (slope * x + intercept)
        total = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - np.sum(residual ** 2) / total if total else float('nan')
        endpoint = (y[-1] - y[0]) / (x[-1] - x[0])
        local = np.diff(y) / np.diff(x)
        ax.errorbar(x, y, yerr=error, fmt='o', color=color, capsize=4,
                    label=f'{direction} measurements', zorder=3)
        ax.plot(x, slope * x + intercept, '--', color=color,
                label=f'{direction} fit: {slope:.3f} °C/count')
        report.append(f'| {direction} | {endpoint:.4f} | {slope:.4f} | {r_squared:.5f} | {local.min():.4f}–{local.max():.4f} |')
        local_sections.extend(['', f'## {direction}: adjacent-point finite differences', '',
                               '| Signed PWM interval | ΔT / ΔPWM (°C/count) |', '|---|---:|'])
        for start, end, value in zip(x[:-1], x[1:], local):
            local_sections.append(f'| {start:.0f} to {end:.0f} | {value:.4f} |')
        local_sections.extend(['', f'Maximum absolute departure from the straight-line fit: '
                               f'{np.max(np.abs(residual)):.3f} °C.'])
    report.extend(['', 'Both data sets are approximately linear over the measured range, '
                   'but adjacent-point slopes vary; the fitted slope is an overall approximation, '
                   'not an exact constant response. The recorded ranges are not sufficient to '
                   'establish measurement uncertainty.', '',
                   'For cooling, the slope versus signed PWM is positive: moving toward zero '
                   'PWM raises temperature. Versus cooling PWM magnitude, the slope has the '
                   'same size but is negative. Heating slopes have the same sign under either convention.'])
    report.extend(local_sections)
    ax.set(xlabel='Signed PWM (counts; negative = cooling, positive = heating)',
           ylabel='Steady-state temperature (°C)', title='TEC steady-state temperature versus signed PWM')
    ax.axvline(0, color='gray', linewidth=0.8)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.text(0.08, 0.025, textwrap.fill(args.steady_state_note, 110), fontsize=9, va='bottom')
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    for extension in ('png', 'pdf'):
        fig.savefig(args.output_dir / f'temperature_vs_signed_pwm.{extension}', dpi=200)
    plt.close(fig)
    summary = args.output_dir / 'susceptibility_results.md'
    summary.write_text('\n'.join(report) + '\n')
    print('\n'.join(report[:10]))
    print(f'\nSaved graph (PNG/PDF) and results to {args.output_dir}')


if __name__ == '__main__':
    main()
