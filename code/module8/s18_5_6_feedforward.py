"""Lab-09 S18.5-S18.6: feedforward PWM command from the measured heating slope.

    python code/module8/s18_5_6_feedforward.py --feedforward

S18.5: T_set(t) = T_a + T_b sin(wt). Feedforward offset and amplitude from the Module 4 heating slope
chi_h and the room temperature measured in S18.3:  u_a = (T_a - T_room)/chi_h,  u_b = T_b/chi_h.
Plots T_set(t) and u(t) = u_a + u_b sin(wt) on aligned time axes before the command is applied, and
checks that u stays on the heating branch (u > 0) and within the allowed range (|u| <= 255).
"""
import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
CHI_H = 0.5311      # °C/PWM, Module 4 heating fit
T_ROOM = 22.0       # °C, measured in S18.3 (Nov 16)
T_A, T_B, PERIOD = 40.0, 16.0, 100.0   # lab-09 S18.5 first feedforward trial
ROD_BASE_LIMIT_C = 56.0


def feedforward(t_a=T_A, t_b=T_B, room=T_ROOM, chi_h=CHI_H):
    """Return (u_a, u_b) for the requested setpoint mean and amplitude."""
    return (t_a - room)/chi_h, t_b/chi_h


def plot_feedforward():
    u_a, u_b = feedforward()
    t = np.linspace(0, 3*PERIOD, 1201)
    w = 2*math.pi/PERIOD
    t_set = T_A + T_B*np.sin(w*t)
    u = u_a + u_b*np.sin(w*t)
    heating, in_range = u.min() > 0, np.abs(u).max() <= 255
    print(f'u_a = ({T_A:g} - {T_ROOM:g})/{CHI_H} = {u_a:.2f} PWM;  u_b = {T_B:g}/{CHI_H} = {u_b:.2f} PWM')
    print(f'u(t) from {u.min():.2f} to {u.max():.2f} PWM; heating branch (u > 0): {heating}; within ±255: {in_range}')
    print(f'Predicted mean {T_ROOM + CHI_H*u_a:.2f} °C, predicted amplitude {CHI_H*u_b:.2f} °C')

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
    a1.plot(t, t_set, color='#7f7f7f', lw=2.2, label=f'T_set(t) = {T_A:g} + {T_B:g} sin(2πt/{PERIOD:g} s)')
    a1.axhline(ROD_BASE_LIMIT_C, color='#b00020', ls='--', lw=1, label=f'{ROD_BASE_LIMIT_C:g} °C rod-base limit')
    a1.axhline(T_ROOM, color='#888', ls=':', lw=1, label=f'room {T_ROOM:g} °C')
    a1.set_ylim(18, 64)
    a1.set_ylabel('requested temperature (°C)'); a1.legend(fontsize=8, loc='upper center', ncol=3); a1.grid(alpha=.3)
    a2.plot(t, u, color='#d62728', lw=2.2, label=f'u(t) = {u_a:.1f} + {u_b:.1f} sin(ωt)')
    a2.axhline(0, color='k', lw=1, label='0: below this would be cooling')
    a2.axhline(255, color='#b00020', ls='--', lw=1, label='±255 PWM limit')
    a2.axhline(-255, color='#b00020', ls='--', lw=1)
    a2.set_ylim(-270, 270)
    a2.annotate(f'max {u.max():.1f}', (t[np.argmax(u)], u.max()), textcoords='offset points', xytext=(0, 8),
                ha='center', fontsize=9)
    a2.annotate(f'min {u.min():.1f} (> 0: heating branch ✓)', (t[np.argmin(u)], u.min()),
                textcoords='offset points', xytext=(0, -16), ha='center', fontsize=9)
    a2.set_ylabel('feedforward PWM (counts)'); a2.set_xlabel('time (s)'); a2.legend(fontsize=8, loc='lower right')
    a2.grid(alpha=.3)
    fig.suptitle(f'S18.5 feedforward command (before applying): χh = {CHI_H} °C/PWM, room {T_ROOM:g} °C', fontsize=12)
    fig.tight_layout()
    out = REPO/'docs/figures/module_08/s18_5_feedforward_command.png'
    fig.savefig(out, dpi=140)
    print(f'Figure: {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--feedforward', action='store_true', help='S18.5: compute and plot the command')
    args = parser.parse_args()
    if args.feedforward:
        plot_feedforward()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
