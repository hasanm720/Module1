"""One figure comparing the Module 8 runs: control modes (top) and drive periods (bottom).

    python code/module8/compare_runs_figure.py
"""
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
DATA = REPO/'data/module_08'
X_MM = np.array([0, 50.30, 100.96, 150.32, 200.95])
ROD = ['T1_C', 'T2_C', 'T3_C', 'T4_C', 'T5_C']
MODES = [('Open loop', 'angstrom_raw_open_40_16_100_20261104_094810.csv', '#888'),
         ('P', 'angstrom_raw_P_40_16_100_20261104_102713.csv', '#ff7f0e'),
         ('PI', 'angstrom_raw_PI_40_16_100_20261104_105054.csv', '#2ca02c')]
PERIODS = [(100, 'angstrom_raw_production_100_20261111_110713.csv', '#1f77b4'),
           (200, 'angstrom_raw_production_200_20261109_111833.csv', '#ff7f0e'),
           (500, 'angstrom_raw_production_500_20261111_092817.csv', '#d62728')]


def load(name):
    rows = [r for r in csv.DictReader(open(DATA/name)) if r['run_state'] == 'RUN']
    t = np.array([float(r['time_ms'])/1000 for r in rows])
    return t, {k: np.array([float(r[k]) for r in rows]) for k in ['setpoint_C', 'TEC_C'] + ROD}


def fit(t, y, w):
    A = np.column_stack([np.ones_like(t), t - t.mean(), np.cos(w*t), np.sin(w*t)])
    c = np.linalg.lstsq(A, y, rcond=None)[0]
    return math.hypot(c[2], c[3]), math.atan2(-c[3], c[2])


fig, axes = plt.subplots(2, 3, figsize=(16, 9))
# Top row: same 100 s drive, three controllers. Last two cycles of each run.
for ax, (name, f, color) in zip(axes[0], MODES):
    t, d = load(f)
    m = t > t[-1] - 200
    ax.plot(t[m] - t[m][0], d['setpoint_C'][m], '--', color='#555', lw=2, label='Requested (setpoint)')
    ax.plot(t[m] - t[m][0], d['TEC_C'][m], color=color, lw=3, label='TEC (rod base heater)')
    ax.plot(t[m] - t[m][0], d['T1_C'][m], color='#1f77b4', lw=1.5, label='T1 (bottom of rod)')
    ax.set(ylim=(20, 60), xlabel='time (s)', ylabel='°C', title=f'{name}, 100 s period')
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, loc='lower left')
# Bottom row: PI controller, three periods.
amp_ax, phase_ax, trace_ax = axes[1]
for period, f, color in PERIODS:
    t, d = load(f)
    w = 2*math.pi/period
    m = t > t[-1] - 5*period
    fits = [fit(t[m], d[k][m], w) for k in ROD]
    B = np.array([b for b, _ in fits])
    phi = np.unwrap([p for _, p in fits])
    for i in range(1, 5):
        while phi[i] > phi[i - 1]:
            phi[i] -= 2*math.pi
    amp_ax.semilogy(X_MM, B/B[0], 'o-', color=color, label=f'{period} s')
    phase_ax.plot(X_MM, phi - phi[0], 'o-', color=color, label=f'{period} s')
    one = t > t[-1] - period
    trace_ax.plot((t[one] - t[one][0])/period, d['T1_C'][one] - d['T1_C'][one].mean(), color=color, lw=2,
                  label=f'T1, {period} s')
    trace_ax.plot((t[one] - t[one][0])/period, d['T4_C'][one] - d['T4_C'][one].mean(), ':', color=color, lw=2,
                  label=f'T4, {period} s')
amp_ax.set(xlabel='height up the rod from T1 (mm)', ylabel='wave size / wave size at T1',
           title='PI: wave SIZE along the rod'); amp_ax.legend(); amp_ax.grid(alpha=.3, which='both')
phase_ax.set(xlabel='height up the rod from T1 (mm)', ylabel='delay relative to T1 (rad)',
             title='PI: wave DELAY along the rod'); phase_ax.legend(); phase_ax.grid(alpha=.3)
trace_ax.set(xlabel='fraction of one cycle', ylabel='°C about the mean',
             title='PI: one cycle at T1 (solid) and T4 (dotted)'); trace_ax.legend(fontsize=7, ncol=2); trace_ax.grid(alpha=.3)
fig.suptitle('Top: SAME wave, different controller.   Bottom: SAME controller (PI), different period.', fontsize=14, weight='bold')
fig.tight_layout()
out = REPO/'docs/figures/module_08/compare_runs.png'
fig.savefig(out, dpi=130)
print(out)
