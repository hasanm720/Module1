"""Lab-09 S18.4: zero-centered vs positive-only sinusoidal PWM at 100 s (experiment and one-lump model).

    python code/module8/s18_4_analysis.py ZERO_100.csv POSITIVE_100.csv --room 22 [--cycles 3]

Experiment: fit the last --cycles complete cycles of each run's TEC temperature (common time fit:
mean + drift + fundamental), report u_a, u_b, fundamental amplitude and residual amplitude (half the
residual's peak-to-peak), and plot TEC and signed PWM on aligned time axes for both runs side by side.
Simulation: the one-lump model of s18_3_model_vs_experiment.py, driven with each run's applied u_a and
u_b, using the same room temperature, chi_h = 0.5311, chi_c = 0.1878 (Module 4) and tau = 91.69 s
(Module 6) for both; settled cycle read as in the course simulator.
"""
import argparse
import csv
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from s18_3_onelump_sim import settled

REPO = HERE.parents[1]
CHI_H, CHI_C, TAU = 0.5311, 0.1878, 91.69
H = 0.01


def load(path):
    rows = [r for r in csv.DictReader(open(path)) if r['run_state'] == 'RUN']
    t = np.array([float(r['time_ms'])/1000 for r in rows]); t -= t[0]
    tec = np.array([float(r['TEC_C']) for r in rows])
    pwm = np.array([int(r['signed_pwm']) for r in rows], dtype=float)
    return float(rows[0]['period_s']), t, tec, pwm


def fit_run(t, tec, pwm, period, cycles):
    """Common time fit over the last complete cycles: a + d t + c cos(wt) + s sin(wt)."""
    n = int((t[-1] + 1.0)//period)
    m = (t > (n - cycles)*period) & (t <= n*period)
    w = 2*math.pi/period
    A = np.column_stack([np.ones(m.sum()), t[m] - t[m].mean(), np.cos(w*t[m]), np.sin(w*t[m])])
    c, *_ = np.linalg.lstsq(A, tec[m], rcond=None)
    res = tec[m] - A @ c
    cu, *_ = np.linalg.lstsq(A, pwm[m], rcond=None)
    return dict(m=m, mean=c[0], amp=math.hypot(c[2], c[3]), res=(res.max() - res.min())/2,
                ua=cu[0], ub=math.hypot(cu[2], cu[3]), drift=c[1]*60)


def model(t_end, room, initial, ua, ub, period):
    pwm = lambda t: max(-255.0, min(255.0, ua + ub*math.sin(2*math.pi*t/period)))
    f = lambda t, T: (room + (CHI_H if pwm(t) >= 0 else CHI_C)*pwm(t) - T)/TAU
    n = int(round(t_end/H))
    ts = np.arange(n + 1)*H
    Ts = np.empty(n + 1); Ts[0] = initial
    T = initial
    for i in range(n):
        t = ts[i]
        k1 = f(t, T); k2 = f(t + H/2, T + H*k1/2); k3 = f(t + H/2, T + H*k2/2); k4 = f(t + H, T + H*k3)
        T += H*(k1 + 2*k2 + 2*k3 + k4)/6
        Ts[i + 1] = T
    return ts, Ts, np.array([pwm(t) for t in ts])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('zero', type=Path)
    parser.add_argument('positive', type=Path)
    parser.add_argument('--room', type=float, required=True)
    parser.add_argument('--cycles', type=int, default=3)
    args = parser.parse_args()

    runs = []
    for name, path in (('Zero-centered', args.zero), ('Positive-only', args.positive)):
        period, t, tec, pwm = load(path)
        f = fit_run(t, tec, pwm, period, args.cycles)
        runs.append(dict(name=name, period=period, t=t, tec=tec, pwm=pwm, **f))

    print(f'Experiment, 100 s, fit of the last {args.cycles} complete cycles:')
    print('| Run | u_a (PWM) | u_b (PWM) | Fundamental amplitude (°C) | Residual amplitude (°C) |')
    print('|---|---|---|---|---|')
    for r in runs:
        print(f'| {r["name"]} | {abs(round(r["ua"])):.0f} | {r["ub"]:.0f} | {r["amp"]:.2f} | {r["res"]:.2f} |')
    for r in runs:
        print(f'  {r["name"]}: TEC mean {r["mean"]:.2f} °C, residual/amplitude {r["res"]/r["amp"]:.3f}, '
              f'drift {r["drift"]:+.3f} °C/min over the fit')

    print(f'\nSimulation (one-lump, room {args.room} °C, chi_h {CHI_H}, chi_c {CHI_C}, tau {TAU} s, start at room):')
    print('| Run | u_a (PWM) | u_b (PWM) | Fundamental amplitude (°C) | Residual amplitude (°C) |')
    print('|---|---|---|---|---|')
    sims = []
    for r in runs:
        ua, ub = round(r['ua']), round(r['ub'])
        t_end = (math.ceil(5*TAU/r['period']) + 2)*r['period']
        ts, Ts, pw = model(t_end, args.room, args.room, ua, ub, r['period'])
        s = settled(ts, Ts, r['period'])
        s['pwm'] = np.interp(s['tt'], ts, pw)
        sims.append(dict(name=r['name'], ua=ua, ub=ub, **s))
        print(f'| {r["name"]} | {ua} | {ub} | {s["amp"]:.2f} | {s["res_amp"]:.2f} |')
    for s in sims:
        print(f'  {s["name"]}: residual/amplitude {s["res_amp"]/s["amp"]:.3f}')

    # Experiment: TEC and signed PWM on aligned time axes, the two runs side by side.
    fig, axes = plt.subplots(2, 2, figsize=(13, 6.5), sharex=True)
    for col, r in enumerate(runs):
        axes[0, col].plot(r['t'], r['tec'], color='k', lw=1.8)
        axes[1, col].plot(r['t'], r['pwm'], color='#d62728', lw=1.5)
        axes[1, col].axhline(0, color='#888', lw=.8)
        for ax in axes[:, col]:
            ax.axvspan(r['t'][r['m']][0], r['t'][r['m']][-1], color='#ffd54f', alpha=.25, lw=0)
            ax.grid(alpha=.3)
        axes[0, col].set_title(f'{r["name"]}: u = {r["ua"]:.0f} + {r["ub"]:.0f} sin ωt; amp {r["amp"]:.2f} °C, '
                               f'residual {r["res"]:.2f} °C')
        axes[1, col].set_xlabel('time since start (s)')
    axes[0, 0].set_ylabel('measured TEC (°C)'); axes[1, 0].set_ylabel('signed PWM')
    fig.suptitle('S18.4 EXPERIMENT, 100 s: zero-centered vs positive-only PWM (shaded = fitted cycles)')
    fig.tight_layout()
    out = REPO/'docs/figures/module_08/s18_4_experiment.png'
    fig.savefig(out, dpi=140); print(f'Figure: {out}')

    # Simulation: aligned settled-cycle plots for both drives.
    fig, axes = plt.subplots(3, 2, figsize=(13, 8), sharex=True)
    for col, s in enumerate(sims):
        x = (s['tt'] - s['start'])/100.0
        axes[0, col].plot(x, s['pwm'], color='#555'); axes[0, col].axhline(0, color='#888', lw=.8)
        axes[1, col].plot(x, s['temp'], color='#1f77b4', lw=1.8, label='model T')
        axes[1, col].plot(x, s['fitted'], '--', color='#ff7f0e', lw=1.2, label='mean + fundamental')
        axes[2, col].plot(x, s['resid'], color='#d62728')
        axes[0, col].set_title(f'{s["name"]}: u = {s["ua"]} + {s["ub"]} sin ωt; amp {s["amp"]:.2f} °C, '
                               f'residual {s["res_amp"]:.2f} °C')
        axes[2, col].set_xlabel('fraction of one settled cycle')
        for ax in axes[:, col]:
            ax.grid(alpha=.3)
    axes[0, 0].set_ylabel('PWM'); axes[1, 0].set_ylabel('model TEC (°C)'); axes[2, 0].set_ylabel('residual (°C)')
    axes[1, 0].legend(fontsize=8)
    fig.suptitle(f'S18.4 SIMULATION (one-lump), 100 s: χh = {CHI_H}, χc = {CHI_C}, τ = {TAU} s, room {args.room:g} °C')
    fig.tight_layout()
    out = REPO/'docs/figures/module_08/s18_4_simulation.png'
    fig.savefig(out, dpi=140); print(f'Figure: {out}')


if __name__ == '__main__':
    main()
