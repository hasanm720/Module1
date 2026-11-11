"""Settling test (lab-09 S18.9) shared by the live GUI and settle_check.py.

Each complete drive cycle of one step is fitted with mean, B and phase (fit_sinusoids.fit_channel).
Successive cycles are compared. A comparison passes when, for every checked channel,
    |Δ mean| <= tol_mean,  |ΔB|/B <= tol_amp,  |Δφ| <= tol_phase.
Each channel's tolerance is the larger of the fixed limit (MEAN_TOL_C, AMP_TOL, PHASE_TOL_RAD) and
NOISE_K times the change expected from fit noise alone (lab-09 S18.9: "use the measured noise and
fit uncertainty to justify them"). With residual sd s over n samples in one cycle, white-noise fit
uncertainties are u(mean) = s/sqrt(n), u(B) = s*sqrt(2/n), u(phi) = u(B)/B; a difference of two
cycles has sqrt(2) times that.
The response counts as settled after SETTLE_PASSES consecutive passing comparisons; the next
RETAIN_CYCLES complete cycles are retained, and each must also pass.
"""
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fit_sinusoids import fit_channel

MEAN_TOL_C = 0.10
AMP_TOL = 0.05
PHASE_TOL_RAD = 0.05
NOISE_K = 3.0
SETTLE_PASSES = 2
RETAIN_CYCLES = 5
CHANNELS = ['TEC_C', 'T1_C', 'T2_C', 'T3_C', 'T4_C']  # T5_C (tag T6) added only if measurable


def cycle_fits(t, temps, start, period, channels=CHANNELS):
    """Fit every complete cycle after `start`. temps maps channel -> array. Returns a list of dicts."""
    w = 2*math.pi/period
    cycles = []
    k = 0
    # Allow one record interval (~0.7 s) of slack so a step that ends exactly on a cycle boundary counts.
    while start + (k + 1)*period <= t[-1] + 1.0:
        m = (t > start + k*period) & (t <= start + (k + 1)*period)
        if m.sum() < 10:
            break
        fits = {c: fit_channel(t[m], temps[c][m], w) for c in channels}
        cycles.append({'start': start + k*period, 'end': start + (k + 1)*period,
                       'mean': {c: f[0] for c, f in fits.items()},
                       'B': {c: f[2] for c, f in fits.items()},
                       'phi': {c: f[3] for c, f in fits.items()},
                       'sd': {c: f[4] for c, f in fits.items()}, 'n': int(m.sum())})
        k += 1
    return cycles


def tolerances(previous, current, c):
    """Per-channel (mean, relative amplitude, phase) limits: fixed floor or NOISE_K x fit noise."""
    s = (previous['sd'][c] + current['sd'][c])/2
    n = min(previous['n'], current['n'])
    b = (previous['B'][c] + current['B'][c])/2
    u_mean, u_b = s/math.sqrt(n), s*math.sqrt(2/n)
    k = NOISE_K*math.sqrt(2)
    return max(MEAN_TOL_C, k*u_mean), max(AMP_TOL, k*u_b/b), max(PHASE_TOL_RAD, k*u_b/b)


def compare(previous, current, channels=CHANNELS):
    """Return (passed, worst) between two successive cycle fits.

    worst holds the largest change of each kind and 'ratio', the largest change/limit (pass if <= 1).
    """
    worst = {'mean': 0.0, 'amp': 0.0, 'phase': 0.0, 'ratio': 0.0}
    for c in channels:
        dphi = (current['phi'][c] - previous['phi'][c] + math.pi) % (2*math.pi) - math.pi
        dmean = abs(current['mean'][c] - previous['mean'][c])
        damp = abs(current['B'][c] - previous['B'][c])/previous['B'][c]
        tol_mean, tol_amp, tol_phase = tolerances(previous, current, c)
        worst['mean'] = max(worst['mean'], dmean)
        worst['amp'] = max(worst['amp'], damp)
        worst['phase'] = max(worst['phase'], abs(dphi))
        worst['ratio'] = max(worst['ratio'], dmean/tol_mean, damp/tol_amp, abs(dphi)/tol_phase)
    return worst['ratio'] <= 1.0, worst


def settling_status(cycles, channels=CHANNELS):
    """Walk the cycles. Returns (per-cycle results, settled_from_index or None, retained index list)."""
    results, streak, settled_at, retained = [], 0, None, []
    for i in range(1, len(cycles)):
        passed, worst = compare(cycles[i - 1], cycles[i], channels)
        results.append((i, passed, worst))
        if settled_at is None:
            streak = streak + 1 if passed else 0
            if streak >= SETTLE_PASSES:
                settled_at = i + 1  # The next cycle is the first retained one.
        elif i >= settled_at:
            if passed:
                retained.append(i)
            else:
                # A failure after settling restarts the test.
                settled_at, streak, retained = None, 0, []
    return results, settled_at, retained[:RETAIN_CYCLES]


def measurable(cycles, channel='T5_C', min_b=0.1):
    """True if a channel's amplitude is large enough to include in the test."""
    return bool(cycles) and np.median([c['B'][channel] for c in cycles]) >= min_b
