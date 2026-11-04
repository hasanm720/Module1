"""Stage 4 fit: T_i(t) = a_i + d_i t + B_i cos(w t + phi_i) over a chosen interval, then q and q'.

    python code/module8/fit_sinusoids.py RUN.csv --period 100 [--cycles 5] [--end-s T] [--sensors 3]

Fits the last --cycles whole periods of RUN records (ending at --end-s if given). The linear
term d_i absorbs slow drift, which is reported so the settling can be judged. Phases are
unwrapped along the rod. q and q' come from straight-line fits of ln B and phi against x over
the first --sensors rod sensors. kappa = w/(2 q q'); nu = kappa (q^2 - q'^2).
"""
import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
CHANNELS = ['TEC_C', 'T1_C', 'T2_C', 'T3_C', 'T4_C', 'T5_C']
TAGS = ['TEC', 'T1', 'T2', 'T3', 'T4', 'T6']  # physical wire tags (T5_C = tag T6)
COLORS = ['k', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
X_M = np.array([0, 50.30, 100.96, 150.32, 200.95])/1e3  # rod sensors, module_08_angstrom.md


def fit_channel(t, y, w):
    """Least squares for a + d t + c cos(w t) + s sin(w t); returns mean, drift, B, phi, residual sd."""
    tc = t - t.mean()
    A = np.column_stack([np.ones_like(t), tc, np.cos(w*t), np.sin(w*t)])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ coef
    return coef[0], coef[1], math.hypot(coef[2], coef[3]), math.atan2(-coef[3], coef[2]), float(res.std(ddof=4))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--period', type=float, required=True)
    parser.add_argument('--cycles', type=int, default=5)
    parser.add_argument('--end-s', type=float, help='End of the interval, Arduino seconds')
    parser.add_argument('--sensors', type=int, default=3, help='Rod sensors used for q and q\'')
    parser.add_argument('--out', type=Path, default=REPO/'docs/figures/module_08')
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['run_state'] == 'RUN']
    t = np.array([float(r['time_ms'])/1000 for r in rows])
    T = np.array([[float(r[c]) for c in CHANNELS] for r in rows])
    end = args.end_s if args.end_s else t[-1]
    win = (t > end - args.cycles*args.period) & (t <= end)
    tw, Tw = t[win], T[win]
    w = 2*math.pi/args.period

    print(f'{args.csv.name}: {args.cycles} cycles of {args.period:g} s, t = {tw[0]:.0f}–{tw[-1]:.0f} s, {len(tw)} records')
    fits = [fit_channel(tw, Tw[:, i], w) for i in range(6)]
    B = np.array([f[2] for f in fits])
    # Unwrap along the rod: each sensor lags the one before it.
    phi = np.unwrap(np.array([f[3] for f in fits]))
    for i in range(1, 6):
        while phi[i] > phi[i - 1]:
            phi[i] -= 2*math.pi
    print(f'{"sensor":>6} {"mean":>7} {"drift C/min":>11} {"B (C)":>7} {"phi (rad)":>9} {"resid sd":>8} {"B/sd":>6}')
    for i, tag in enumerate(TAGS):
        print(f'{tag:>6} {fits[i][0]:7.2f} {fits[i][1]*60:11.3f} {B[i]:7.3f} {phi[i]:9.2f} {fits[i][4]:8.3f} {B[i]/fits[i][4]:6.1f}')

    n = args.sensors
    x = X_M[:n]
    slope_b, icpt_b = np.polyfit(x, np.log(B[1:n + 1]), 1)
    slope_p, icpt_p = np.polyfit(x, phi[1:n + 1], 1)
    q, qp = -slope_b, -slope_p
    kappa = w/(2*q*qp)
    nu = kappa*(q*q - qp*qp)
    print(f'\nUsing {", ".join(TAGS[1:n + 1])}: q = {q:.2f} 1/m, q\' = {qp:.2f} rad/m')
    print(f'kappa = {kappa:.3e} m^2/s, nu = {nu:.3e} 1/s, B ratio T{n}/T1 = {B[n]/B[1]:.3f}, phase span = {phi[1] - phi[n]:.2f} rad')
    if q <= qp or nu < 0:
        print("Note: q <= q' or nu < 0. Lab-09 calls this evidence to investigate.")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), width_ratios=[1.6, 1, 1])
    for i, (tag, color) in enumerate(zip(TAGS, COLORS)):
        axes[0].plot(tw, Tw[:, i] - fits[i][0], color=color, lw=1.2, label=tag)
    axes[0].set(xlabel='Arduino time (s)', ylabel='T − fitted mean (°C)', title='Fit interval')
    axes[0].legend(fontsize=8, ncol=3); axes[0].grid(alpha=.3)
    axes[1].semilogy(X_M*1e3, B[1:], 'o', color='#1f77b4')
    axes[1].semilogy(x*1e3, np.exp(icpt_b + slope_b*x), color='#888', label=f'q = {q:.1f} m⁻¹')
    axes[1].set(xlabel='x from T1 (mm)', ylabel='Amplitude B (°C)', title='Amplitude decay'); axes[1].legend(); axes[1].grid(alpha=.3, which='both')
    axes[2].plot(X_M*1e3, phi[1:], 'o', color='#1f77b4')
    axes[2].plot(x*1e3, icpt_p + slope_p*x, color='#888', label=f"q′ = {qp:.1f} rad/m")
    axes[2].set(xlabel='x from T1 (mm)', ylabel='Unwrapped phase φ (rad)', title='Phase'); axes[2].legend(); axes[2].grid(alpha=.3)
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    figure = args.out/f'{args.csv.stem}_fit_{args.period:g}s.png'
    fig.savefig(figure, dpi=150)
    result = {'file': args.csv.name, 'period_s': args.period, 'window_s': [float(tw[0]), float(tw[-1])],
              'sensors_used': TAGS[1:n + 1], 'x_m': X_M.tolist(), 'mean_C': [f[0] for f in fits],
              'drift_C_per_min': [f[1]*60 for f in fits], 'B_C': B.tolist(), 'phi_rad': phi.tolist(),
              'resid_sd_C': [f[4] for f in fits], 'q_per_m': q, 'q_prime_rad_per_m': qp,
              'kappa_m2_per_s': kappa, 'nu_per_s': nu}
    figure.with_suffix('.json').write_text(json.dumps(result, indent=2))
    print(f'Figure: {figure}')


if __name__ == '__main__':
    main()
