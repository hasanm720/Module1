"""Phase 5: fit the final rod profile with the finite (insulated-tip) and semi-infinite fin models.

    python code/module7/stationary_fit.py RUN.csv --room 25 [--avg 120] [--u-room 0.5]

theta = T - T_room, averaged over the last --avg seconds. Models (x from T1, L = T1 hole to tip):
    finite:         theta0 * cosh(m (L - x)) / cosh(m L)
    semi-infinite:  theta0 * exp(-m x)
For each trial m, theta0 is solved by linear least squares; m is found on a fine grid.
u(m) is the fit uncertainty (from SSR curvature, scaled by the residual scatter);
the room-temperature shift of ±u-room is reported separately as a systematic.
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
ROD = ['rod1_C', 'rod2_C', 'rod3_C', 'rod4_C', 'rod5_C']
TAGS = ['T1', 'T2', 'T3', 'T4', 'T6']  # physical wire tags (rod5_C = T6)
X = np.array([0, 50.30, 100.96, 150.32, 200.95]) / 1e3  # m, sensor map Nov 2
U_X = 0.5e-3
L, D = 0.2832, 12.705e-3  # m
MODELS = {'finite': lambda x, m: np.cosh(m * (L - x)) / np.cosh(m * L),
          'semi-infinite': lambda x, m: np.exp(-m * x)}


def fit(theta, shape):
    grid = np.linspace(0.5, 15, 29001)
    best = None
    for m in grid:
        f = shape(X, m)
        a = f @ theta / (f @ f)
        ssr = np.sum((theta - a * f) ** 2)
        if best is None or ssr < best[2]:
            best = (m, a, ssr)
    m, a, ssr = best
    # Fit uncertainty from SSR curvature near the minimum (2 free parameters).
    h = 1e-3
    def s(mm):
        f = shape(X, mm); return np.sum((theta - (f @ theta / (f @ f)) * f) ** 2)
    curv = (s(m + h) - 2 * s(m) + s(m - h)) / h ** 2
    s2 = ssr / (len(X) - 2)
    return m, a, math.sqrt(2 * s2 / curv) if curv > 0 else math.nan, theta - a * shape(X, m)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--room', type=float, required=True)
    parser.add_argument('--u-room', type=float, default=0.5)
    parser.add_argument('--avg', type=float, default=120)
    parser.add_argument('--tip', type=float, help='Measured tip temperature (°C), shown for comparison only')
    parser.add_argument('--out', type=Path, default=REPO / 'docs/figures/module_07')
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['time_s']) for r in rows])
    T = np.array([[float(r[c]) for c in ROD] for r in rows])
    win = t >= t[-1] - args.avg
    means, sds = T[win].mean(0), T[win].std(0, ddof=1)
    drift = np.array([np.polyfit(t[win], T[win][:, i], 1)[0] * 60 for i in range(5)])
    theta = means - args.room

    results = {'file': args.csv.name, 'window_s': [float(t[-1] - args.avg), float(t[-1])], 'room_C': args.room,
               'x_m': X.tolist(), 'T_mean_C': means.round(3).tolist(), 'T_sd_C': sds.round(3).tolist(),
               'theta_C': theta.round(3).tolist(), 'drift_C_per_min': drift.round(3).tolist(), 'L_m': L, 'd_m': D}
    print(f'{args.csv.name}: last {args.avg:.0f} s (t = {t[-1] - args.avg:.0f}–{t[-1]:.0f} s), room {args.room} °C')
    for tag, x, Tm, th, dr in zip(TAGS, X, means, theta, drift):
        print(f'  {tag}: x = {x * 1e3:6.2f} mm  T = {Tm:6.2f} °C  theta = {th:6.2f} °C  drift {dr:+.3f} °C/min')

    fig, (ax, axr) = plt.subplots(2, 1, figsize=(9, 8), sharex=True, height_ratios=[3, 1.3])
    ax.errorbar(X * 1e3, theta, xerr=U_X * 1e3, yerr=args.u_room, fmt='ko', capsize=3, zorder=5,
                label=f'measured (y error = room ±{args.u_room} °C)')
    xx = np.linspace(0, L, 200)
    for (name, shape), color, offset in zip(MODELS.items(), ('#1f77b4', '#d62728'), (-3, 3)):
        m, a, um, res = fit(theta, shape)
        m_lo = fit(means - (args.room + args.u_room), shape)[0]
        m_hi = fit(means - (args.room - args.u_room), shape)[0]
        sys_m = (abs(m_hi - m_lo)) / 2
        results[name] = {'m_per_m': round(m, 3), 'u_fit': round(um, 3), 'u_room_sys': round(sys_m, 3),
                         'theta0_C': round(a, 3), 'decay_length_m': round(1 / m, 4), 'mL': round(m * L, 3),
                         'residuals_C': res.round(3).tolist(), 'rms_residual_C': round(float(np.sqrt(np.mean(res ** 2))), 3)}
        print(f'\n{name}: m = {m:.2f} ± {um:.2f} (fit) ± {sys_m:.2f} (room) 1/m, 1/m = {100 / m:.1f} cm, '
              f'mL = {m * L:.2f}, theta0 = {a:.2f} °C, rms residual = {np.sqrt(np.mean(res ** 2)):.3f} °C')
        ax.plot(xx * 1e3, a * shape(xx, m), color=color, label=f'{name}: m = {m:.2f} ± {um:.2f} m⁻¹')
        axr.plot(X * 1e3 + offset, res, 'o-', color=color, label=name)
    mf, ms = results['finite']['m_per_m'], results['semi-infinite']['m_per_m']
    uf = math.hypot(results['finite']['u_fit'], results['finite']['u_room_sys'])
    results['shift_semi_minus_finite'] = round(ms - mf, 3)
    bi = (mf * D / 4) ** 2
    u_bi = 2 * bi * uf / mf
    results['Bi_perp'] = [bi, u_bi]
    th_f = lambda x: np.cosh(mf * (L - x)) / np.cosh(mf * L)
    eps = np.abs(th_f(X) - np.exp(-mf * X)) / th_f(X)
    results['epsilon_T_percent'] = (eps * 100).round(1).tolist()
    print(f'\nShift (semi-infinite − finite) = {ms - mf:+.2f} 1/m vs finite uncertainty {uf:.2f} 1/m')
    print(f'Bi_perp = (m d/4)^2 = {bi:.2e} ± {u_bi:.1e}')
    print('epsilon_T at sensors (%):', results['epsilon_T_percent'])
    if args.tip is not None:
        pred = results['finite']['theta0_C'] / np.cosh(mf * L)
        results['tip'] = {'measured_theta_C': args.tip - args.room, 'finite_model_theta_C': round(float(pred), 2)}
        print(f'Tip: measured theta = {args.tip - args.room:.1f} °C, finite model predicts {pred:.1f} °C')
        ax.plot([L * 1e3], [args.tip - args.room], 's', color='#2e7d32', ms=8, label='tip, measured by hand (not fitted)')

    for tag, x, th in zip(TAGS, X, theta):
        ax.annotate(tag, (x * 1e3, th), textcoords='offset points', xytext=(6, 6), fontsize=9)
    ax.set_ylabel('θ = T − T_room (°C)'); ax.grid(alpha=0.3); ax.legend(fontsize=9)
    ax.set_title('Final rod profile (not fully stationary): finite vs semi-infinite fin fits')
    axr.axhline(0, color='#888', lw=1); axr.set_ylabel('residual (°C)'); axr.set_xlabel('x from T1 (mm)')
    axr.grid(alpha=0.3); axr.legend(fontsize=8)
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    figure = args.out / f'{args.csv.stem}_fin_fits.png'
    fig.savefig(figure, dpi=150)
    (args.out / f'{args.csv.stem}_fin_fits.json').write_text(json.dumps(results, indent=2))
    print(f'Figure: {figure}')


if __name__ == '__main__':
    main()
