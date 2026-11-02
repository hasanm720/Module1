"""Phase 5: fit the final rod profile with the finite (insulated-tip) and semi-infinite fin models.

    python code/module7/stationary_fit.py RUN.csv [--avg 120]

Uses only the five rod thermistors, averaged over the last --avg seconds. The ambient
temperature is a fitted parameter, so no hand-held probe reading enters the analysis:
    finite:         T(x) = T_room + theta0 * cosh(m (L - x)) / cosh(m L)
    semi-infinite:  T(x) = T_room + theta0 * exp(-m x)
x is measured from T1; L is the T1 hole to the tip. For each trial m, T_room and theta0
are solved by linear least squares; m is found on a fine grid. u(m) comes from the SSR
curvature, scaled by the residual scatter (3 parameters, 5 points).
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


def solve(T, shape, m):
    """Best T_room, theta0 for a given m; returns (T_room, theta0, ssr, covariance scale)."""
    A = np.column_stack([np.ones_like(X), shape(X, m)])
    coef, *_ = np.linalg.lstsq(A, T, rcond=None)
    res = T - A @ coef
    return coef[0], coef[1], float(res @ res), np.linalg.inv(A.T @ A)


def fit(T, shape):
    grid = np.linspace(0.5, 15, 29001)
    ssr = np.array([solve(T, shape, m)[2] for m in grid])
    m = grid[np.argmin(ssr)]
    t_room, a, s_min, cov = solve(T, shape, m)
    h = 1e-3
    curv = (solve(T, shape, m + h)[2] - 2 * s_min + solve(T, shape, m - h)[2]) / h ** 2
    s2 = s_min / (len(X) - 3)
    um = math.sqrt(2 * s2 / curv) if curv > 0 else math.nan
    u_room = math.sqrt(s2 * cov[0, 0])  # at fixed m; a lower bound
    res = T - (t_room + a * shape(X, m))
    return m, um, t_room, u_room, a, res, grid[-1] - m < 1e-9 or m - grid[0] < 1e-9


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--avg', type=float, default=120)
    parser.add_argument('--out', type=Path, default=REPO / 'docs/figures/module_07')
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['time_s']) for r in rows])
    T = np.array([[float(r[c]) for c in ROD] for r in rows])
    win = t >= t[-1] - args.avg
    means, sds = T[win].mean(0), T[win].std(0, ddof=1)
    drift = np.array([np.polyfit(t[win], T[win][:, i], 1)[0] * 60 for i in range(5)])

    results = {'file': args.csv.name, 'window_s': [float(t[-1] - args.avg), float(t[-1])],
               'x_m': X.tolist(), 'T_mean_C': means.round(3).tolist(), 'T_sd_C': sds.round(3).tolist(),
               'drift_C_per_min': drift.round(3).tolist(), 'L_m': L, 'd_m': D,
               'note': 'T_room is fitted; hand-held probe readings (room 25 C, tip 28 C) are notes only.'}
    print(f'{args.csv.name}: last {args.avg:.0f} s (t = {t[-1] - args.avg:.0f}–{t[-1]:.0f} s)')
    for tag, x, Tm, dr in zip(TAGS, X, means, drift):
        print(f'  {tag}: x = {x * 1e3:6.2f} mm  T = {Tm:6.2f} °C  drift {dr:+.3f} °C/min')

    fig, (ax, axr) = plt.subplots(2, 1, figsize=(9, 8), sharex=True, height_ratios=[3, 1.3])
    ax.errorbar(X * 1e3, means, xerr=U_X * 1e3, yerr=sds, fmt='ko', capsize=3, zorder=5, label='measured (120 s mean)')
    xx = np.linspace(0, L, 200)
    for (name, shape), color, offset in zip(MODELS.items(), ('#1f77b4', '#d62728'), (-3, 3)):
        m, um, t_room, u_room, a, res, at_edge = fit(means, shape)
        results[name] = {'m_per_m': round(m, 3), 'u_m': round(um, 3), 'T_room_fit_C': round(t_room, 2),
                         'u_T_room_fixed_m': round(u_room, 2), 'theta0_C': round(a, 3),
                         'decay_length_m': round(1 / m, 4), 'mL': round(m * L, 3),
                         'residuals_C': res.round(3).tolist(),
                         'rms_residual_C': round(float(np.sqrt(np.mean(res ** 2))), 3), 'm_at_grid_edge': bool(at_edge)}
        print(f'\n{name}: m = {m:.2f} ± {um:.2f} 1/m, 1/m = {100 / m:.1f} cm, mL = {m * L:.2f}, '
              f'T_room(fit) = {t_room:.2f} °C, theta0 = {a:.2f} °C, rms residual = {np.sqrt(np.mean(res ** 2)):.3f} °C'
              + ('  [m at grid edge: not constrained]' if at_edge else ''))
        ax.plot(xx * 1e3, t_room + a * shape(xx, m), color=color,
                label=f'{name}: m = {m:.2f} ± {um:.2f} m⁻¹, T_room = {t_room:.1f} °C')
        axr.plot(X * 1e3 + offset, res, 'o-', color=color, label=name)
    mf, uf = results['finite']['m_per_m'], results['finite']['u_m']
    ms = results['semi-infinite']['m_per_m']
    results['shift_semi_minus_finite'] = round(ms - mf, 3)
    bi = (mf * D / 4) ** 2
    results['Bi_perp'] = [bi, 2 * bi * uf / mf]
    th_f = lambda x: np.cosh(mf * (L - x)) / np.cosh(mf * L)
    eps = np.abs(th_f(X) - np.exp(-mf * X)) / th_f(X)
    results['epsilon_T_percent'] = (eps * 100).round(1).tolist()
    print(f'\nShift (semi-infinite − finite) = {ms - mf:+.2f} 1/m vs finite uncertainty {uf:.2f} 1/m')
    print(f'Bi_perp = (m d/4)^2 = {bi:.2e} ± {2 * bi * uf / mf:.1e}')
    print('epsilon_T at sensors (%):', results['epsilon_T_percent'])

    for tag, x, Tm in zip(TAGS, X, means):
        ax.annotate(tag, (x * 1e3, Tm), textcoords='offset points', xytext=(6, 6), fontsize=9)
    ax.set_ylabel('Rod temperature T (°C)'); ax.grid(alpha=0.3); ax.legend(fontsize=8.5)
    ax.set_title('Final rod profile (not fully stationary): finite vs semi-infinite fits, T_room fitted')
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
