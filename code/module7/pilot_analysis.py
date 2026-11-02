"""Placement pilot (Phase 4, Steps 2-3): theta = T - T_room at each rod sensor.

    python code/module7/pilot_analysis.py PILOT.csv --room 23.5 [--avg 120]

Averages the last --avg seconds of controlled data, reports theta(T6)/theta(T1)
against the 1/e placement target, the late drift rate, and plots the time history
and ln(theta) vs x.
"""
import argparse
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
CHANNELS = ['tec_C', 'rod1_C', 'rod2_C', 'rod3_C', 'rod4_C', 'rod5_C']
LABELS = ['TEC tag T5 (A1)', 'T1 (A5)', 'T2 (A4)', 'T3 (A3)', 'T4 (A2)', 'T6 (A0)']  # physical wire tags
COLORS = ['k', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
X_MM = np.array([0, 50.30, 100.96, 150.32, 200.95])  # rod sensor x from T1 (sensor map, Nov 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--room', type=float, required=True, help='Room/ambient temperature (°C)')
    parser.add_argument('--avg', type=float, default=120, help='Averaging window at the end (s)')
    parser.add_argument('--out', type=Path, default=REPO / 'docs/figures/module_07')
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['time_s']) for r in rows])
    temps = np.array([[float(r[c]) for c in CHANNELS] for r in rows])
    on = np.array([r['setpoint_C'] != 'nan' for r in rows])

    end = t[on][-1]
    window = on & (t >= end - args.avg)
    means = temps[window].mean(axis=0)
    sds = temps[window].std(axis=0, ddof=1)
    # Drift: slope of a straight-line fit over the window, in °C/min.
    drift = [np.polyfit(t[window], temps[window][:, i], 1)[0] * 60 for i in range(6)]
    theta = means[1:] - args.room
    ratio = theta[-1] / theta[0]

    print(f'{args.csv.name}: averaging {args.avg:.0f} s ending at t = {end:.0f} s, room = {args.room} °C')
    print(f'{"sensor":>16} {"x (mm)":>8} {"T (°C)":>8} {"sd":>6} {"theta":>7} {"theta/theta1":>12} {"drift °C/min":>12}')
    print(f'{LABELS[0]:>16} {"—":>8} {means[0]:8.2f} {sds[0]:6.3f} {"":>7} {"":>12} {drift[0]:12.3f}')
    for i in range(5):
        print(f'{LABELS[i + 1]:>16} {X_MM[i]:8.2f} {means[i + 1]:8.2f} {sds[i + 1]:6.3f} {theta[i]:7.2f} '
              f'{theta[i] / theta[0]:12.3f} {drift[i + 1]:12.3f}')
    print(f'\ntheta(T6)/theta(T1) = {ratio:.3f}; 1/e target = {1 / math.e:.3f} -> '
          f'{"MET" if 0 < ratio <= 1 / math.e else "NOT met"}')
    slope = np.polyfit(X_MM / 1e3, np.log(theta), 1)[0]
    print(f'Straight-line ln(theta) slope = {slope:.2f} 1/m (rough semi-infinite m = {-slope:.2f} 1/m)')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), width_ratios=[1.6, 1])
    for label, color, column in zip(LABELS, COLORS, temps.T):
        ax1.plot(t, column, color=color, lw=2.5 if color == 'k' else 1.4, label=label)
    ax1.axvspan(end - args.avg, end, color='#888', alpha=0.12, lw=0, label=f'averaged ({args.avg:.0f} s)')
    ax1.axhline(args.room, color='#888', ls='--', lw=1, label=f'room {args.room} °C')
    ax1.set_xlabel('Arduino time (s)'); ax1.set_ylabel('Temperature (°C)')
    ax1.set_title('Pilot: TEC held at 45 °C (PI)'); ax1.grid(alpha=0.3); ax1.legend(fontsize=8, ncol=2)
    ax2.errorbar(X_MM, np.log(theta), xerr=0.5, yerr=sds[1:] / theta, fmt='o', color='#1f77b4', capsize=3,
                 label='measured')
    ax2.axhline(np.log(theta[0] / math.e), color='#b00020', ls='--', label='θ(T1)/e target')
    xx = np.linspace(0, X_MM[-1], 50)
    ax2.plot(xx, np.polyval(np.polyfit(X_MM, np.log(theta), 1), xx), color='#888', lw=1, label='straight-line guide')
    for x, y, name in zip(X_MM, np.log(theta), LABELS[1:]):
        ax2.annotate(name.split()[0], (x, y), textcoords='offset points', xytext=(6, 4), fontsize=9)
    ax2.set_xlabel('x from T1 (mm)'); ax2.set_ylabel('ln θ   (θ = T − T_room, °C)')
    ax2.set_title(f'Semilog profile: θ(T6)/θ(T1) = {ratio:.2f}'); ax2.grid(alpha=0.3); ax2.legend(fontsize=8)
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    figure = args.out / f'{args.csv.stem}_pilot.png'
    fig.savefig(figure, dpi=150)
    print(f'Figure: {figure}')


if __name__ == '__main__':
    main()
