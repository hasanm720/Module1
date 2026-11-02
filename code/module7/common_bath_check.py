"""Common-bath check: six-channel spread T_max - T_min from a raw Module 7 CSV.

Step 1 (no windows) — plot the whole record and the instantaneous spread so you
can pick settled intervals:
    python common_bath_check.py ../../data/module_07/rod_raw_common_bath_....csv

Step 2 — give one settled interval per bath temperature (Arduino time, s) and
the thermocouple reading for each:
    python common_bath_check.py FILE --window 120 180 --window 600 660 --tc 52.1 --tc 41.8

Pass (default criterion): spread of the six interval means < 1 °C at every
temperature. Raw data are only read, never modified.
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
LABELS = ['TEC tag T5 (A1)', 'T1 (A5)', 'T2 (A4)', 'T3 (A3)', 'T4 (A2)', 'T6 (A0)']  # physical wire tags; CSV column rod5_C = tag T6
COLORS = ['k', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
SPREAD_PASS_C = 1.0


def load(path):
    with open(path, newline='') as f:
        rows = list(csv.DictReader(f))
    t = np.array([float(r['time_s']) for r in rows])
    temps = np.array([[float(r[c]) for c in CHANNELS] for r in rows])
    return t, temps


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--window', nargs=2, type=float, action='append', default=[],
                        metavar=('START_S', 'END_S'), help='Settled interval in Arduino time')
    parser.add_argument('--tc', type=float, action='append', default=[],
                        help='Thermocouple reading (°C) for each window, in order')
    parser.add_argument('--out', type=Path, default=REPO / 'docs/figures/module_07')
    args = parser.parse_args()
    if args.tc and len(args.tc) != len(args.window):
        parser.error('Give one --tc per --window.')

    t, temps = load(args.csv)
    inst_spread = np.nanmax(temps, axis=1) - np.nanmin(temps, axis=1)
    print(f'{args.csv.name}: {len(t)} rows, Arduino time {t[0]:.1f}–{t[-1]:.1f} s')
    for label, column in zip(LABELS, temps.T):
        bad = np.count_nonzero(~np.isfinite(column))
        if bad:
            print(f'  WARNING: {label} has {bad} nan rows (fault or disconnected)')

    results = []
    for k, (start, end) in enumerate(args.window):
        inside = (t >= start) & (t <= end)
        if not inside.any():
            raise SystemExit(f'No rows in window {start}–{end} s')
        block = temps[inside]
        means = np.nanmean(block, axis=0)
        sds = np.nanstd(block, axis=0, ddof=1)
        width = means.max() - means.min()
        tc = args.tc[k] if args.tc else math.nan
        results.append(dict(start_s=start, end_s=end, n_rows=int(inside.sum()),
                            **{f'{c}_mean': round(m, 3) for c, m in zip(CHANNELS, means)},
                            **{f'{c}_sd': round(s, 3) for c, s in zip(CHANNELS, sds)},
                            spread_of_means_C=round(width, 3),
                            max_instant_spread_C=round(float(np.nanmax(inst_spread[inside])), 3),
                            thermocouple_C=tc, tec_minus_tc_C=round(means[0] - tc, 3),
                            hottest=LABELS[int(np.argmax(means))], coldest=LABELS[int(np.argmin(means))],
                            passed=bool(width < SPREAD_PASS_C)))

    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.csv.stem
    if results:
        print(f'\n{"window (s)":>14} {"n":>4} ' + ' '.join(f'{l:>9}' for l in LABELS)
              + f' {"spread":>7} {"max inst":>8} {"TC":>6}  result')
        for r in results:
            means = ' '.join(f'{r[c + "_mean"]:9.2f}' for c in CHANNELS)
            print(f'{r["start_s"]:6.0f}–{r["end_s"]:<6.0f} {r["n_rows"]:4d} {means} '
                  f'{r["spread_of_means_C"]:7.2f} {r["max_instant_spread_C"]:8.2f} {r["thermocouple_C"]:6.1f}  '
                  f'{"PASS" if r["passed"] else "FAIL"} (hot {r["hottest"]}, cold {r["coldest"]})')
        verdict = all(r['passed'] for r in results)
        print(f'\nOverall: {"PASS — no correction needed" if verdict else "FAIL — continue to Record/Pause calibration"}'
              f' (criterion: spread < {SPREAD_PASS_C} °C at every temperature)')
        table = args.out / f'{stem}_spread.csv'
        with open(table, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0]))
            writer.writeheader(); writer.writerows(results)
        print(f'Table: {table}')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, height_ratios=[3, 1])
    for label, color, column in zip(LABELS, COLORS, temps.T):
        ax1.plot(t, column, color=color, lw=2.5 if label.startswith('TEC') else 1.2, label=label)
    ax2.plot(t, inst_spread, color='#444')
    ax2.axhline(SPREAD_PASS_C, color='#b00020', ls='--', label=f'{SPREAD_PASS_C:g} °C criterion')
    for k, (start, end) in enumerate(args.window):
        # Mark the averaging window by its edges only, so a window covering the whole record stays readable.
        for ax in (ax1, ax2):
            for edge in (start, end):
                if t[0] < edge < t[-1]:
                    ax.axvline(edge, color='#888', ls=':', lw=1)
        if args.tc:
            ax1.plot([start, end], [args.tc[k]] * 2, color='#00897b', lw=3,
                     label='Thermocouple' if k == 0 else None)
    # Pad the y range so the highest and lowest traces are not pressed against the frame.
    low, high = np.nanmin(temps), np.nanmax(temps)
    pad = max(1.0, 0.5 * (high - low))
    ax1.set_ylim(low - pad, high + pad)
    ax2.set_ylim(0, max(1.5 * SPREAD_PASS_C, 1.2 * np.nanmax(inst_spread)))
    ax1.set_ylabel('Raw temperature (°C)'); ax1.legend(ncol=4, fontsize=8); ax1.grid(alpha=0.3)
    ax1.set_title(f'Common-bath check — {args.csv.name}')
    ax2.set_ylabel('T_max − T_min (°C)'); ax2.set_xlabel('Arduino time (s)')
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    fig.tight_layout()
    figure = args.out / f'{stem}_common_bath.png'
    fig.savefig(figure, dpi=150)
    print(f'Figure: {figure}')


if __name__ == '__main__':
    main()
