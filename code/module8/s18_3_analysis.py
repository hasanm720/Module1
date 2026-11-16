"""Lab-09 S18.3: zero-centered sinusoidal PWM. Aligned TEC/PWM plots and the fit table.

    python code/module8/s18_3_analysis.py --room 22 RUN_300.csv RUN_200.csv RUN_100.csv [--cycles 3]

For each run, fits the last --cycles complete cycles of the TEC temperature and the signed PWM to
a + d t + B cos(w t + phi). Reports mean minus room, TEC amplitude, the phase lag of the TEC behind
the PWM (degrees), and the residual amplitude (half the peak-to-peak of TEC minus its fit), which
shows the distortion from unequal heating and cooling.
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


def fit(t, y, w):
    A = np.column_stack([np.ones_like(t), t - t.mean(), np.cos(w*t), np.sin(w*t)])
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return c[0], math.hypot(c[2], c[3]), math.atan2(-c[3], c[2]), y - A @ c


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path, nargs='+')
    parser.add_argument('--room', type=float, required=True)
    parser.add_argument('--cycles', type=int, default=3)
    parser.add_argument('--out', type=Path, default=REPO/'docs/figures/module_08')
    args = parser.parse_args()

    runs = []
    for path in args.csv:
        rows = [r for r in csv.DictReader(open(path)) if r['run_state'] == 'RUN']
        period = float(rows[0]['period_s'])
        t = np.array([float(r['time_ms'])/1000 for r in rows])
        tec = np.array([float(r['TEC_C']) for r in rows])
        pwm = np.array([int(r['signed_pwm']) for r in rows], dtype=float)
        n = int((t[-1] - t[0] + 1.0)//period)          # complete cycles in the run
        start = t[0] + (n - args.cycles)*period
        m = (t > start) & (t <= t[0] + n*period)
        w = 2*math.pi/period
        mean, amp, phi_t, res = fit(t[m], tec[m], w)
        _, amp_u, phi_u, _ = fit(t[m], pwm[m], w)
        lag = math.degrees((phi_u - phi_t) % (2*math.pi))
        runs.append(dict(path=path, period=period, t=t, tec=tec, pwm=pwm, m=m, start=start,
                         mean=mean, amp=amp, lag=lag, res=(res.max() - res.min())/2, ub=amp_u, n=n))

    print(f'Room {args.room} °C; fits use the last {args.cycles} complete cycles of each run')
    print('| Period (s) | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag (°) | Residual amplitude (°C) | PWM u_b (fit) |')
    print('|---|---|---|---|---|---|')
    for r in sorted(runs, key=lambda r: -r['period']):
        print(f'| {r["period"]:g} | {r["mean"] - args.room:.2f} | {r["amp"]:.2f} | {r["lag"]:.1f} | {r["res"]:.2f} | {r["ub"]:.1f} |')

    # Aligned TEC and PWM axes, one column per period, fitted window shaded.
    runs.sort(key=lambda r: -r['period'])
    fig, axes = plt.subplots(2, len(runs), figsize=(5.5*len(runs), 6.5), sharex='col', squeeze=False)
    for col, r in enumerate(runs):
        tt = r['t'] - r['t'][0]
        top, bottom = axes[0, col], axes[1, col]
        top.plot(tt, r['tec'], color='k', lw=1.8, label='TEC temperature')
        top.axhline(args.room, color='#888', ls='--', lw=1, label=f'room {args.room:g} °C')
        bottom.plot(tt, r['pwm'], color='#d62728', lw=1.5, label='signed PWM')
        bottom.axhline(0, color='#888', lw=.8)
        for ax in (top, bottom):
            ax.axvspan(r['start'] - r['t'][0], r['n']*r['period'], color='#ffd54f', alpha=.25, lw=0)
            ax.grid(alpha=.3)
        top.set_title(f'{r["period"]:g} s: mean−room {r["mean"] - args.room:.1f} °C, amp {r["amp"]:.1f} °C, lag {r["lag"]:.0f}°')
        top.set_ylabel('TEC (°C)'); bottom.set_ylabel('PWM (counts)'); bottom.set_xlabel('time since start (s)')
        if col == 0:
            top.legend(fontsize=8); bottom.legend(fontsize=8)
    fig.suptitle('S18.3 zero-centered sinusoidal PWM (u = 50 sin ωt): TEC and PWM on aligned time axes '
                 '(shaded = fitted cycles)', fontsize=12)
    fig.tight_layout()
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out/'s18_3_zero_centered_pwm.png'
    fig.savefig(out, dpi=140)
    print(f'Figure: {out}')


if __name__ == '__main__':
    main()
