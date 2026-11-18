"""Lab-09 S18.3 "Compare The Simulation With Your Measurements": 100 s one-lump model vs the measured TEC.

    python code/module8/s18_3_model_vs_experiment.py RUN_100.csv --room 22 [--tau 91.69]

The one-lump model and settled readout are those in s18_3_onelump_sim.py (the course simulator's
lumped mode), here with our measured values: chi_h = 0.5311, chi_c = 0.1878 °C/PWM (Module 4 fit),
tau_th from --tau (default 91.69 s, Module 6 open-loop step), room from --room, and the initial
temperature taken from the first record of the run. PWM amplitude and period come from the run.
Both traces get the same settled-cycle analysis (mean, fundamental amplitude, lag behind PWM,
residual amplitude), and a best-fit tau is also reported as an extra.
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
CHI_H, CHI_C = 0.5311, 0.1878
H = 0.01


def model(t_out, room, initial, tau, ub, period, chi_h=CHI_H, chi_c=CHI_C):
    """RK4 one-lump TEC for u = ub sin(2 pi t / P); returns T at the times t_out (s from start)."""
    pwm = lambda t: max(-255.0, min(255.0, ub*math.sin(2*math.pi*t/period)))
    f = lambda t, T: (room + (chi_h if pwm(t) >= 0 else chi_c)*pwm(t) - T)/tau
    n = int(math.ceil(t_out[-1]/H)) + 1
    ts = np.arange(n + 1)*H
    Ts = np.empty(n + 1); Ts[0] = initial
    T = initial
    for i in range(n):
        t = ts[i]
        k1 = f(t, T); k2 = f(t + H/2, T + H*k1/2); k3 = f(t + H/2, T + H*k2/2); k4 = f(t + H, T + H*k3)
        T += H*(k1 + 2*k2 + 2*k3 + k4)/6
        Ts[i + 1] = T
    return np.interp(t_out, ts, Ts)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--room', type=float, required=True)
    parser.add_argument('--tau', type=float, default=91.69)
    args = parser.parse_args()

    rows = [r for r in csv.DictReader(open(args.csv)) if r['run_state'] == 'RUN']
    period = float(rows[0]['period_s'])
    t = np.array([float(r['time_ms'])/1000 for r in rows]); t = t - t[0]
    tec = np.array([float(r['TEC_C']) for r in rows])
    pwm = np.array([int(r['signed_pwm']) for r in rows], dtype=float)
    ub = round(0.5*(pwm.max() - pwm.min()))
    initial = tec[0]

    sim = model(t, args.room, initial, args.tau, ub, period)
    exp_s, sim_s = settled(t, tec, period), settled(t, sim, period)
    print(f'{args.csv.name}: period {period:g} s, u_b {ub}, room {args.room} °C, initial {initial:.2f} °C, '
          f'chi_h {CHI_H}, chi_c {CHI_C}, tau {args.tau:g} s; settled cycle t = {exp_s["start"]:.0f}–{exp_s["start"] + period:.0f} s')
    print('| | Mean − room (°C) | Fundamental amplitude (°C) | Lag behind PWM (°) | Residual amplitude (°C) |')
    print('|---|---|---|---|---|')
    for name, s in (('Measured', exp_s), (f'Model, τ = {args.tau:g} s', sim_s)):
        print(f'| {name} | {s["mean"] - args.room:.2f} | {s["amp"]:.2f} | {s["lag"]:.1f} | {s["res_amp"]:.2f} |')

    # Extra: tau that best matches the measured lag (same chi values).
    taus = np.arange(30, 121, 1.0)
    lags = [settled(t, model(t, args.room, initial, tau, ub, period), period)['lag'] for tau in taus]
    best = taus[int(np.argmin(np.abs(np.array(lags) - exp_s['lag'])))]
    best_s = settled(t, model(t, args.room, initial, best, ub, period), period)
    print(f'| Model, τ = {best:g} s (best lag match, extra) | {best_s["mean"] - args.room:.2f} | {best_s["amp"]:.2f} | '
          f'{best_s["lag"]:.1f} | {best_s["res_amp"]:.2f} |')

    sim_best = model(t, args.room, initial, best, ub, period)
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(11, 8.5), sharex=False, height_ratios=[2, 1, 1.3])
    a1.plot(t, tec, color='k', lw=2, label='Measured TEC')
    a1.plot(t, sim, color='#d62728', lw=1.6, label=f'One-lump model, τ = {args.tau:g} s (measured, Module 6)')
    a1.plot(t, sim_best, '--', color='#1f77b4', lw=1.4, label=f'One-lump model, τ = {best:g} s (best lag match)')
    a1.axhline(args.room, color='#888', ls=':', lw=1)
    a1.set(ylabel='TEC (°C)', title=f'S18.3, 100 s: measured vs one-lump model (χh = {CHI_H}, χc = {CHI_C}, u_b = {ub})')
    a1.legend(fontsize=8); a1.grid(alpha=.3)
    a2.plot(t, pwm, color='#555'); a2.axhline(0, color='#888', lw=.8)
    a2.set(xlabel='time since start (s)', ylabel='PWM'); a2.grid(alpha=.3)
    x = (exp_s['tt'] - exp_s['start'])/period
    a3.plot(x, exp_s['resid'], color='k', lw=2, label='measured residual')
    a3.plot(x, sim_s['resid'], color='#d62728', label=f'model residual, τ = {args.tau:g} s')
    a3.set(xlabel='fraction of the settled cycle', ylabel='T − (mean + fundamental) (°C)'); a3.legend(fontsize=8); a3.grid(alpha=.3)
    fig.tight_layout()
    out = REPO/'docs/figures/module_08/s18_3_model_vs_experiment_100s.png'
    fig.savefig(out, dpi=140)
    print(f'Figure: {out}')


if __name__ == '__main__':
    main()
