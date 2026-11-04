"""Plot raw controller command against applied signed PWM for P and PI runs (lab-09 Stage 1).

    python code/module8/actuator_plot.py RUN_P.csv RUN_PI.csv

Reports the heating and cooling slopes of applied PWM per raw command, and clipped samples.
"""
import csv
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
fig, axes = plt.subplots(1, len(sys.argv) - 1, figsize=(6*(len(sys.argv) - 1), 4.6), squeeze=False)
for ax, path in zip(axes[0], sys.argv[1:]):
    rows = [r for r in csv.DictReader(open(path)) if r['run_state'] == 'RUN' and r['controller_pwm'] != 'nan']
    raw = np.array([float(r['controller_pwm']) for r in rows])
    pwm = np.array([int(r['signed_pwm']) for r in rows])
    ratio = float(rows[0]['heating_to_cooling_ratio'])
    heat, cool = (raw > 5) & (abs(pwm) < 255), (raw < -5) & (abs(pwm) < 255)
    slope_h, slope_c = np.polyfit(raw[heat], pwm[heat], 1)[0], np.polyfit(raw[cool], pwm[cool], 1)[0]
    print(f'{Path(path).name}: mode {rows[0]["control_mode"]}, r = {ratio}, heating slope {slope_h:.3f}, '
          f'cooling slope {slope_c:.3f}, raw {raw.min():.0f} to {raw.max():.0f}, '
          f'PWM {pwm.min()} to {pwm.max()}, clipped {int((abs(pwm) >= 255).sum())}')
    ax.plot(raw, pwm, '.', ms=3, color='#1f77b4')
    ax.axhline(0, color='#888', lw=.8); ax.axvline(0, color='#888', lw=.8)
    for limit in (255, -255):
        ax.axhline(limit, color='#b00020', ls=':', lw=1)
    ax.set(xlabel='Raw controller command (PWM)', ylabel='Applied signed PWM',
           title=f'{rows[0]["control_mode"]}: heating slope {slope_h:.2f}, cooling slope {slope_c:.2f}')
    ax.grid(alpha=.3)
fig.tight_layout()
out = REPO/'docs/figures/module_08/actuator_raw_vs_applied.png'
fig.savefig(out, dpi=150)
print(f'Figure: {out}')
