"""Lab-09 S18.3 one-lump model table, reproducing the course simulator's lumped mode.

    python code/module8/s18_3_onelump_sim.py [--ub 50]

Same equations and numerics as simulators/angstrom-six-sensor/?s18=3 (read from its source):
    tau dT/dt = T_room + chi(u) u - T,  chi = chi_h for u >= 0, chi_c for u < 0,
    u(t) = clip(u_a + u_b sin(2 pi t / P), -255, 255),  RK4 with 0.01 s steps, 0.25 s chart samples.
Settled readout: the last complete cycle starting at least 5 tau after t = 0, 360 uniform samples;
mean, fundamental amplitude, phase lag atan2(-C, S); residual = T - fitted mean and fundamental,
residual amplitude = half its peak-to-peak range. Page settings: room = initial = 22 C, tau = 80 s,
chi_h = 0.46, u_a = 0; rows for P = 100, 200, 300 s and chi_c = 0.23, 0.46.
"""
import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
ROOM = INITIAL = 22.0
TAU, CHI_H, UA = 80.0, 0.46, 0.0
H, CHART_DT = 0.01, 0.25


# Cycles run in the S18.3 experiment (Nov 16), so the model figure covers the same time.
EXPERIMENT_CYCLES = {300: 6, 200: 6, 100: 8}


def simulate(period, chi_c, ub, t_end=None):
    pwm = lambda t: max(-255.0, min(255.0, UA + ub*math.sin(2*math.pi*t/period)))
    f = lambda t, T: (ROOM + (CHI_H if pwm(t) >= 0 else chi_c)*pwm(t) - T)/TAU
    if t_end is None:
        t_end = (math.ceil(5*TAU/period) + 2)*period  # two complete cycles after 5 tau
    n = int(round(t_end/H))
    every = int(round(CHART_DT/H))
    T, t = INITIAL, 0.0
    ts, Ts = [0.0], [T]
    for i in range(1, n + 1):
        k1 = f(t, T); k2 = f(t + H/2, T + H*k1/2); k3 = f(t + H/2, T + H*k2/2); k4 = f(t + H, T + H*k3)
        T += H*(k1 + 2*k2 + 2*k3 + k4)/6
        t = i*H
        if i % every == 0:
            ts.append(t); Ts.append(T)
    return np.array(ts), np.array(Ts), pwm


def settled(ts, Ts, period):
    end = math.floor(ts[-1]/period)*period
    start = end - period
    count = 360
    tt = start + np.arange(count + 1)*period/count
    temp = np.interp(tt, ts, Ts)
    ang = 2*np.pi*np.arange(count + 1)/count
    mean = temp[:-1].mean()
    s = (temp[:-1]*np.sin(ang[:-1])).sum()
    c = (temp[:-1]*np.cos(ang[:-1])).sum()
    amp = 2*math.hypot(s, c)/count
    lag = math.degrees(math.atan2(-c, s))
    fitted = mean + 2*(s*np.sin(ang) + c*np.cos(ang))/count
    resid = temp - fitted
    return dict(start=start, tt=tt, temp=temp, fitted=fitted, resid=resid, mean=mean, amp=amp, lag=lag,
                res_amp=(resid.max() - resid.min())/2)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ub', type=float, default=50.0, help='Selected PWM amplitude (counts)')
    args = parser.parse_args()
    print(f'One-lump model: room = initial = {ROOM} °C, tau = {TAU:g} s, chi_h = {CHI_H}, u_a = {UA:g}, u_b = {args.ub:g}')
    print('| Period (s) | chi_c (°C/PWM) | (1) Mean minus room (°C) | (2) Amplitude (°C) | (3) Phase lag (°) | (4) Residual amplitude (°C) |')
    print('|---|---|---|---|---|---|')
    keep = {}
    for period in (100, 200, 300):
        for chi_c in (0.23, 0.46):
            ts, Ts, pwm = simulate(period, chi_c, args.ub)
            r = settled(ts, Ts, period)
            r['pwm'] = np.array([pwm(t) for t in r['tt']])
            keep[(period, chi_c)] = r
            print(f'| {period} | {chi_c} | {r["mean"] - ROOM:.3f} | {r["amp"]:.3f} | {r["lag"]:.1f} | {r["res_amp"]:.3f} |')
    # Equal-susceptibility check against the analytical settled solution.
    for period in (100, 200, 300):
        wt = 2*math.pi*TAU/period
        print(f'  analytical (chi_c = chi_h), {period} s: amplitude {CHI_H*args.ub/math.sqrt(1 + wt*wt):.3f} °C, '
              f'lag {math.degrees(math.atan(wt)):.1f}°')

    # Same layout and length as the experiment figure: one column per period, from t = 0.
    periods = (300, 200, 100)
    fig, axes = plt.subplots(3, 3, figsize=(16.5, 9), sharex=True)  # all rows: the last settled cycle
    for col, period in enumerate(periods):
        t_end = EXPERIMENT_CYCLES[period]*period
        for chi_c, color in ((0.23, '#d62728'), (0.46, '#1f77b4')):
            ts, Ts, pwm = simulate(period, chi_c, args.ub, t_end)
            r = settled(ts, Ts, period)  # last complete cycle of this length
            x = (r['tt'] - r['start'])/period
            axes[0, col].plot(x, r['temp'], color=color, lw=1.6, label=f'model T, χc = {chi_c}')
            axes[2, col].plot(x, r['resid'], color=color, lw=1.4,
                              label=f'residual, χc = {chi_c}')
            if chi_c == 0.23:
                axes[1, col].plot(x, r['pwm'] if 'pwm' in r else [pwm(t) for t in r['tt']], color='#555', lw=1.2,
                                  label='PWM (same for both)')
        axes[0, col].axhline(ROOM, color='#888', ls=':', lw=1)
        axes[0, col].set_title(f'{period} s: last of {EXPERIMENT_CYCLES[period]} cycles (as run), '
                               f't = {t_end - period:g}–{t_end:g} s')
        axes[1, col].axhline(0, color='#888', lw=.8)
        axes[2, col].set_xlim(0, 1)
        axes[2, col].set_xlabel('fraction of the last (settled) cycle')
        for ax in axes[:, col]:
            ax.grid(alpha=.3)
    axes[0, 0].set_ylabel('model TEC (°C)'); axes[1, 0].set_ylabel('PWM (counts)')
    axes[2, 0].set_ylabel('residual (°C)')
    for ax in (axes[0, 0], axes[1, 0], axes[2, 0]):
        ax.legend(fontsize=8)
    fig.suptitle(f'S18.3 one-lump MODEL (simulation only): χh = {CHI_H}, τ = {TAU:g} s, u_b = {args.ub:g}, '
                 f'room = start = {ROOM:g} °C; last settled cycle of each run', fontsize=12)
    fig.tight_layout()
    out = REPO/'docs/figures/module_08/s18_3_onelump_model.png'
    fig.savefig(out, dpi=140)
    print(f'Figure: {out}')


if __name__ == '__main__':
    main()
