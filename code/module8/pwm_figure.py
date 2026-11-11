"""Plot setpoint, TEC and T1 temperature, raw controller command and applied PWM for one run.

    python code/module8/pwm_figure.py RUN.csv [--last-s 400]
"""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('csv', type=Path)
parser.add_argument('--last-s', type=float, default=400, help='Seconds shown, ending at the last record')
args = parser.parse_args()

rows = [r for r in csv.DictReader(open(args.csv)) if r['run_state'] == 'RUN']
t = np.array([float(r['time_ms'])/1000 for r in rows])
m = t >= t[-1] - args.last_s
get = lambda k: np.array([float(r[k]) for r in rows])[m]
tm = t[m]
raw, pwm = get('controller_pwm'), get('signed_pwm')

fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
a1.plot(tm, get('setpoint_C'), '--', color='#7f7f7f', lw=2, label='Setpoint (requested)')
a1.plot(tm, get('TEC_C'), color='k', lw=2.5, label='TEC thermistor (feedback)')
a1.plot(tm, get('T1_C'), color='#1f77b4', lw=2, label='T1, rod base x = 0')
a1.set_ylabel('Temperature (°C)'); a1.legend(fontsize=9); a1.grid(alpha=.3)
a1.set_title(f'{args.csv.name}: PI, period {rows[0]["period_s"]} s')
a2.plot(tm, raw, color='#7b2cbf', lw=1.5, label='Raw PI command (before r)')
a2.plot(tm, pwm, color='#d62728', lw=2, label='Applied signed PWM (negative × r = 2.83)')
a2.fill_between(tm, 0, pwm, where=pwm > 0, color='#d62728', alpha=.15, label='HEAT (pin 9)')
a2.fill_between(tm, 0, pwm, where=pwm < 0, color='#1f77b4', alpha=.15, label='COOL (pin 10)')
for lim in (255, -255):
    a2.axhline(lim, color='#b00020', ls=':', lw=1)
a2.axhline(0, color='#888', lw=.8)
a2.set_ylabel('PWM (counts)'); a2.set_xlabel('Arduino time (s)'); a2.legend(fontsize=8, ncol=2); a2.grid(alpha=.3)
fig.tight_layout()
out = REPO/'docs/figures/module_08'/f'{args.csv.stem}_pwm.png'
fig.savefig(out, dpi=150)
print(f'Figure: {out}')
heat, cool = pwm > 0, pwm < 0
print(f'PWM {pwm.min()} to {pwm.max()}; heating {100*heat.mean():.0f}% of the time, cooling {100*cool.mean():.0f}%; '
      f'raw command {raw.min():.0f} to {raw.max():.0f}; clipped {int((abs(pwm) >= 255).sum())}')
