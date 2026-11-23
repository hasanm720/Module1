"""Lab-09 S18.7: trial log for P-only and PI tracking of T_set = 40 + 16 sin(wt).

    python code/module8/s18_7_analysis.py --trial "RUN.csv|P only|notes" --trial "RUN2.csv|Initial PI|notes" ...

Each trial is fitted over its last --cycles complete cycles (common time fit: mean + drift + fundamental):
mean TEC, amplitude ratio = fitted TEC amplitude / requested amplitude, phase lag of the TEC behind the
setpoint, and RMS of T_TEC - T_set over the same interval. Also the median controller sample interval
and PWM saturation (|PWM| >= limit), including during start-up (the first cycle). Kp and Ki are read from
the run's START event. Writes the page's trial-log table and one figure (TEC vs setpoint, last 2 cycles).
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
TOL_MEAN, TOL_RATIO, TOL_LAG = 1.0, (0.90, 1.10), 20.0   # team tolerances (user, Nov 18), also used in S18.8


def gains(csv_path):
    """Kp, Ki and PWM limit from the START event line: EVENT,ms,START,mode,kp,ki,r,limit."""
    for line in open(Path(csv_path).with_suffix('.events.txt')):
        if ',START,' in line:
            parts = line.strip().split('EVENT,', 1)[1].split(',')
            return parts[2], float(parts[3]), float(parts[4]), int(parts[6])
    raise ValueError(f'No START event for {csv_path}')


def fit(t, y, w):
    A = np.column_stack([np.ones_like(t), t - t.mean(), np.cos(w*t), np.sin(w*t)])
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return c[0], math.hypot(c[2], c[3]), math.atan2(-c[3], c[2])


def analyse(csv_path, cycles):
    rows = [r for r in csv.DictReader(open(csv_path)) if r['run_state'] == 'RUN']
    period = float(rows[0]['period_s']); tb = float(rows[0]['Tb_C'])
    t = np.array([float(r['time_ms'])/1000 for r in rows]); t -= t[0]
    tec = np.array([float(r['TEC_C']) for r in rows])
    sp = np.array([float(r['setpoint_C']) for r in rows])
    pwm = np.array([int(r['signed_pwm']) for r in rows])
    mode, kp, ki, limit = gains(csv_path)
    n = int((t[-1] + 1.0)//period)
    out = dict(path=Path(csv_path), period=period, mode=mode, kp=kp, ki=ki, n=n, t=t, tec=tec, sp=sp,
               dt=float(np.median(np.diff(t))),
               sat_total=int((np.abs(pwm) >= limit).sum()),
               sat_startup=int((np.abs(pwm[t <= period]) >= limit).sum()))
    sat_t = t[np.abs(pwm) >= limit]
    out['sat_when'] = f'{sat_t[0]:.0f}–{sat_t[-1]:.0f} s' if sat_t.size else ''
    if n < cycles:
        out['settled'] = False
        return out
    m = (t > (n - cycles)*period) & (t <= n*period)
    w = 2*math.pi/period
    mean, amp, phi = fit(t[m], tec[m], w)
    _, _, phi_sp = fit(t[m], sp[m], w)
    out.update(settled=True, m=m, mean=mean, ratio=amp/tb,
               lag=(math.degrees(phi_sp - phi) + 180) % 360 - 180,
               rms=float(np.sqrt(np.mean((tec[m] - sp[m])**2))))
    out['meets'] = (abs(mean - 40) <= TOL_MEAN and TOL_RATIO[0] <= out['ratio'] <= TOL_RATIO[1]
                    and abs(out['lag']) <= TOL_LAG)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--trial', action='append', required=True, help='"csv|trial name|notes"')
    parser.add_argument('--cycles', type=int, default=3)
    args = parser.parse_args()

    trials = []
    for spec in args.trial:
        path, name, *note = spec.split('|')
        r = analyse(path, args.cycles)
        r.update(name=name, note=note[0] if note else '')
        trials.append(r)

    lines = [
        '# S18.7 — P and PI trial log',
        '',
        '**Lab step:** lab-09, Stage 3, S18.7 "Repeat With P And PI Control": "Use the table below as a trial log. '
        'Start with the P-only and initial PI runs at 100 s using the same K_p." "Add a row for each gain pair you test."',
        '',
        '**Units:** K_p in PWM counts per °C; K_i in PWM counts per (°C·s). Error e = T_set − T_TEC; cooling commands '
        '× r = χh/χc = 2.83 before the ±255 clamp; anti-windup in PI.',
        '',
        f'**Requested drive:** T_set = 40 + 16 sin(2πt/τ). **Metrics:** common time fit over the last {args.cycles} complete '
        'cycles; amplitude ratio = fitted TEC amplitude / 16 °C; phase lag of the TEC behind the setpoint; RMS of '
        'T_TEC − T_set over the same interval. **Tolerances (team, also reported in S18.8):** |mean − 40| ≤ 1 °C, '
        'amplitude ratio 0.90–1.10, |phase lag| ≤ 20°.',
        '',
        '| Period (s) | Trial | K_p | K_i | Sample interval (s) | Mean TEC (°C) | Amplitude ratio (fitted / requested) '
        '| Phase lag (°) | RMS tracking error (°C) | PWM saturation | Run link and notes |',
        '|---|---|---|---|---|---|---|---|---|---|---|',
    ]
    for r in trials:
        rel = '../../../' + r['path'].as_posix().split('PHYS39A_instrumentation/')[-1]
        link = f'[{r["path"].name}]({rel})'
        sat = (f'yes: {r["sat_total"]} samples ({r["sat_startup"]} in start-up), {r["sat_when"]}'
               if r['sat_total'] else 'no')
        if r['settled']:
            met = 'meets tolerances' if r['meets'] else 'misses tolerances'
            cells = [f'{r["mean"]:.2f}', f'{r["ratio"]:.3f}', f'{r["lag"]:.1f}', f'{r["rms"]:.2f}']
        else:
            met = f'stopped before {args.cycles} complete cycles'
            cells = ['', '', '', '']
        notes = '; '.join(x for x in (link, met, r['note']) if x)
        lines.append(f'| {r["period"]:g} | {r["name"]} | {r["kp"]:g} | {r["ki"]:g} | {r["dt"]:.2f} | '
                     + ' | '.join(cells) + f' | {sat} | {notes} |')
    lines += ['', '**Figure:** [s18_7_trials.png](../../../docs/figures/module_08/s18_7_trials.png)', '']
    out_md = REPO/'docs/tables/module_08/s18_7_trial_log.md'
    out_md.write_text('\n'.join(lines))
    print('\n'.join(lines[9:]))
    print(f'Table: {out_md}')

    n = len(trials)
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.6*n), squeeze=False)
    for ax, r in zip(axes[:, 0], trials):
        keep = r['t'] >= r['t'][-1] - 2*r['period']
        ax.plot(r['t'][keep], r['sp'][keep], '--', color='#7f7f7f', lw=2, label='setpoint')
        ax.plot(r['t'][keep], r['tec'][keep], color='k', lw=2, label='measured TEC')
        title = f'{r["period"]:g} s, {r["name"]}: Kp {r["kp"]:g}, Ki {r["ki"]:g}'
        if r['settled']:
            title += f' — mean {r["mean"]:.1f} °C, ratio {r["ratio"]:.2f}, lag {r["lag"]:.0f}°, RMS {r["rms"]:.1f} °C'
        ax.set_title(title, fontsize=10); ax.set_ylabel('°C'); ax.grid(alpha=.3)
    axes[0, 0].legend(fontsize=8, loc='upper right'); axes[-1, 0].set_xlabel('time since start (s)')
    fig.suptitle('S18.7 P and PI trials: TEC vs setpoint, last 2 cycles of each run', fontsize=12)
    fig.tight_layout()
    out_png = REPO/'docs/figures/module_08/s18_7_trials.png'
    fig.savefig(out_png, dpi=130)
    print(f'Figure: {out_png}')


if __name__ == '__main__':
    main()
