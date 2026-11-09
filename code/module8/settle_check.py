"""Apply the lab-09 settling test to every period in a raw Module 8 CSV, then fit the retained cycles.

    python code/module8/settle_check.py RUN.csv

For each schedule step (period), prints the cycle-to-cycle changes against the thresholds in
settling.py, the settled point, and the retained 5-cycle interval. If one is found, it runs the
fit_sinusoids.py analysis on exactly that interval.
"""
import argparse
import csv
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import settling as st


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['run_state'] == 'RUN']
    if not rows:
        raise SystemExit('No RUN records.')
    t = np.array([float(r['time_ms'])/1000 for r in rows])
    step = np.array([int(r['step']) for r in rows])
    print(f'{args.csv.name}: criterion |Δmean| ≤ {st.MEAN_TOL_C} °C, |ΔB|/B ≤ {100*st.AMP_TOL:g}%, '
          f'|Δφ| ≤ {st.PHASE_TOL_RAD} rad; settled after {st.SETTLE_PASSES} passes; retain {st.RETAIN_CYCLES}')
    for s in sorted(set(step)):
        m = step == s
        period = float(rows[np.argmax(m)]['period_s'])
        temps = {c: np.array([float(r[c]) for r in rows])[m] for c in st.CHANNELS + ['T5_C']}
        cycles = st.cycle_fits(t[m], temps, t[m][0], period, st.CHANNELS + ['T5_C'])
        channels = st.CHANNELS + (['T5_C'] if st.measurable(cycles) else [])
        results, settled_at, retained = st.settling_status(cycles, channels)
        print(f'\nStep {s}: period {period:g} s, {len(cycles)} complete cycles, '
              f'channels {", ".join(c[:-2] if c != "T5_C" else "T6" for c in channels)}')
        for i, passed, worst in results:
            print(f'  cycle {i} vs {i + 1}: Δmean {worst["mean"]:.3f} °C, ΔB/B {100*worst["amp"]:.1f}%, '
                  f'Δφ {worst["phase"]:.3f} rad  {"pass" if passed else "FAIL"}')
        if settled_at is None:
            print('  Not settled.')
            continue
        print(f'  Settled from cycle {settled_at + 1}; retained {len(retained)}/{st.RETAIN_CYCLES} cycles')
        if len(retained) >= st.RETAIN_CYCLES:
            first, last = cycles[retained[0]], cycles[retained[-1]]
            print(f'  Retained interval: t = {first["start"]:.1f}–{last["end"]:.1f} s')
            subprocess.run([sys.executable, str(HERE/'fit_sinusoids.py'), str(args.csv), '--period', f'{period:g}',
                            '--cycles', str(st.RETAIN_CYCLES), '--end-s', f'{last["end"]:.3f}',
                            '--sensors', '5' if 'T5_C' in channels else '4'], check=False)
        else:
            print('  Fewer than 5 settled cycles: not usable yet.')


if __name__ == '__main__':
    main()
