"""Estimate the 63% response time from recorded Module 5 data; no hardware.

P-control traces measure tau_cl, not open-loop tau. Infer tau using
tau = (1 + chi*Kp)*tau_cl under the unsaturated one-lump model.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
DEFAULT = HERE.parents[2] / 'module5/P5_high_gain_response/high_gain_20261005_110725.csv'


def crossing(times, temperatures, target, rising):
    for i, temperature in enumerate(temperatures):
        if (temperature >= target if rising else temperature <= target):
            if i == 0:
                raise ValueError('Threshold already reached at the initial sample.')
            return times[i-1], times[i]
    raise ValueError('63% threshold was not reached.')


def analyze(path, kp, chi, window):
    with path.open(newline='') as stream:
        rows = [row for row in csv.DictReader(stream)
                if float(row['kp_pwm_per_C']) == kp and row.get('phase', 'step') == 'step']
    if len(rows) < 3:
        raise ValueError('Need at least three samples at the selected gain.')
    times = [float(row['gain_elapsed_s']) for row in rows]
    temperatures = [float(row['temperature_C']) for row in rows]
    if not all(math.isfinite(x) for x in times + temperatures):
        raise ValueError('Nonfinite data.')
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Use one contiguous run with increasing time.')
    if times[-1]-times[0] <= window:
        raise ValueError('Recording must be longer than the final averaging window.')
    if any(row['safety'] != 'OK' for row in rows):
        raise ValueError('Safety trip in selected run.')
    if any(abs(float(row['command_pwm'])) >= 255 for row in rows):
        raise ValueError('Saturated P trace cannot use the linear tau correction.')
    targets = {float(row['setpoint_C']) for row in rows}
    if len(targets) != 1:
        raise ValueError('Select a run with a fixed setpoint.')
    final = [T for t, T in zip(times, temperatures) if t >= times[-1]-window]
    initial, settled = temperatures[0], statistics.mean(final)
    if abs(settled-initial) < 0.1:
        raise ValueError('Temperature change too small for a useful estimate.')
    threshold = initial + 0.63*(settled-initial)
    lo, hi = crossing(times, temperatures, threshold, settled > initial)
    dt = statistics.median(b-a for a, b in zip(times, times[1:]))
    # Use the first reached sample, as prescribed by the lab, not a fitted curve.
    tau_cl = hi-times[0]
    factor = 1+chi*kp
    result = dict(source=str(path.resolve()), kp_pwm_per_C=kp, chi_C_per_PWM=chi,
                  measurement_mode='open_loop' if rows[0].get('control_mode') == 'open_loop' else 'P',
                  final_window_s=window, sample_interval_s=dt,
                  initial_C=initial, final_mean_C=settled,
                  final_min_C=min(final), final_max_C=max(final),
                  threshold_63_C=threshold,
                  crossing_bracket_s=[lo-times[0], hi-times[0]],
                  tau_closed_loop_s=tau_cl, correction_factor=factor,
                  inferred_open_loop_tau_s=factor*tau_cl,
                  inferred_tau_bracket_s=[factor*(lo-times[0]), factor*(hi-times[0])],
                  one_sample_timing_scale_s=factor*dt)
    sensitivity = []
    for w in (30, 60, 90):
        if times[-1]-times[0] <= w:
            continue
        f = statistics.mean(T for t, T in zip(times, temperatures) if t >= times[-1]-w)
        q = initial + .63*(f-initial)
        before, reached = crossing(times, temperatures, q, f > initial)
        j = times.index(reached)
        interpolated = before + (q-temperatures[j-1]) / (temperatures[j]-temperatures[j-1]) * (reached-before)
        sensitivity.append(dict(final_window_s=w, final_mean_C=f,
                                threshold_63_C=q,
                                inferred_tau_s=factor*(reached-times[0]),
                                interpolated_tau_s=factor*(interpolated-times[0])))
    result['window_sensitivity'] = sensitivity
    return result, rows, times, temperatures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        help='CSV to analyze; defaults to latest fresh step, then historical P run')
    parser.add_argument('--kp', type=float, help='Gain filter; defaults to 0 for open-loop or 10 for P')
    parser.add_argument('--chi', type=float, default=0.5311,
                        help='Heating susceptibility from Module 4, °C/PWM')
    parser.add_argument('--window', type=float, default=60)
    parser.add_argument('--output-dir', type=Path, default=HERE / 'results')
    parser.add_argument('--export-data', action='store_true',
                        help='Also export JSON calculations and a selected-trace CSV')
    args = parser.parse_args()
    if args.input is None:
        fresh = sorted((HERE / 'data').glob('open_loop_step_*.csv'),
                       key=lambda path: path.stat().st_mtime, reverse=True)
        args.input = fresh[0] if fresh else DEFAULT
    if args.kp is None:
        with args.input.open(newline='') as stream:
            first = next(csv.DictReader(stream), {})
        args.kp = 0 if first.get('control_mode') == 'open_loop' else 10
    if (not all(math.isfinite(x) for x in (args.kp, args.chi, args.window))
            or args.kp < 0 or args.chi <= 0 or args.window <= 0):
        parser.error('Use finite nonnegative Kp and positive chi/window.')
    result, rows, times, temperatures = analyze(args.input, args.kp, args.chi, args.window)
    open_loop = result['measurement_mode'] == 'open_loop'
    if open_loop:
        from record_tau_step import stable
        if times[-1]-times[0] < 120 or not stable(list(zip(times, temperatures))):
            parser.error('Open-loop endpoint not stable; previous report retained.')
        applied = {(row['reported_pwm'], row['reported_direction']) for row in rows[1:]}
        requested = {(row['command_pwm'], row['command_direction']) for row in rows}
        if len(applied) != 1 or applied != requested:
            parser.error('Applied PWM was not a constant step; previous report retained.')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f'{args.input.stem}_kp_{args.kp:g}'
    if args.export_data:
        (args.output_dir / f'{stem}_estimate.json').write_text(json.dumps(result, indent=2)+'\n')
        with (args.output_dir / f'{stem}_selected_trace.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    elapsed = [t-times[0] for t in times]
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    ax = axes[0]
    ax.plot(elapsed, temperatures, color='red', label='Recorded temperature')
    ax.axhline(result['final_mean_C'], color='green', linestyle='--', label='Final-60-s mean' if args.window == 60 else 'Final-window mean')
    ax.axhline(result['threshold_63_C'], color='orange', linestyle=':', label='63% threshold')
    ax.axvline(result['tau_closed_loop_s'], color='purple', linestyle='--',
               label='First threshold crossing (tau)' if open_loop else 'First threshold crossing (tau_cl)')
    ax.scatter([0], [result['initial_C']], color='black', zorder=5, label='Initial temperature')
    ax.axvspan(max(0, elapsed[-1]-args.window), elapsed[-1], color='green', alpha=.08)
    ax.set_ylabel('Temperature (°C)')
    for prefix, style in [('reported', '-'), ('command', '--')]:
        pwm = [float(r[f'{prefix}_pwm'])*(1 if r[f'{prefix}_direction'] == 'HEAT' else -1) for r in rows]
        axes[1].step(elapsed, pwm, where='post', linestyle=style, label=f'{prefix.title()} signed PWM')
    axes[1].set_ylabel('PWM counts')
    axes[1].set_xlabel('Time since first pre-command sample (s)')
    for ax in axes:
        ax.grid(alpha=.3)
        ax.legend()
        ax.set_xlim(0, elapsed[-1])
    if open_loop:
        fig.suptitle(f'Module 6 Part 3: constant +{rows[-1]["command_pwm"]} PWM step\n'
                     f'Direct open-loop tau ≈ {result["inferred_open_loop_tau_s"]:.1f} s')
        footer = 'Fresh Arduino measurements; 63% method with feedback off.'
    else:
        fig.suptitle(f'Module 6 Part 3: Kp={args.kp:g}, chi={args.chi:g} °C/PWM\n'
                     f'tau_cl ≈ {result["tau_closed_loop_s"]:.2f} s; '
                     f'inferred open-loop tau ≈ {result["inferred_open_loop_tau_s"]:.1f} s')
        footer = 'P-feedback correction assumes an unsaturated one-lump model; this is not a direct open-loop measurement.'
    fig.text(.5,.015,footer,ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.94))
    fig.savefig(args.output_dir / f'{stem}_63_percent.png', dpi=200)
    plt.close(fig)
    report_path = HERE / 'PART3_RESULTS.md'
    plot_link = Path(os.path.relpath(args.output_dir / f'{stem}_63_percent.png', HERE)).as_posix()
    source_link = Path(os.path.relpath(args.input, HERE)).as_posix()
    open_loop = result['measurement_mode'] == 'open_loop'
    lower, upper = result['inferred_tau_bracket_s']
    crossing_lower, crossing_upper = result['crossing_bracket_s']
    sensitivity_rows = '\n'.join(
        f"| {entry['final_window_s']} | {entry['final_mean_C']:.4f} | {entry['threshold_63_C']:.4f} | {entry['inferred_tau_s']:.2f} | {entry['interpolated_tau_s']:.2f} |"
        for entry in result['window_sensitivity'])
    report = f'''# Module 6 Part 3 — Thermal time constant

**Estimated open-loop time constant: τ ≈ {result['inferred_open_loop_tau_s']:.1f} seconds.**

This estimate uses a recorded P-control response with Kp = {args.kp:g} PWM/°C.
The measured 63% crossing gives the closed-loop time constant; the open-loop
value is inferred using the unsaturated one-lump model.

## Recorded measurements

| Quantity | Value |
|---|---:|
| Initial temperature, Tᵢ | {result['initial_C']:.3f} °C |
| Approximate final temperature, T𝒇 | {result['final_mean_C']:.3f} °C |
| Final averaging window | {args.window:g} s |
| Final-window temperature range | {result['final_min_C']:.2f}–{result['final_max_C']:.2f} °C |
| Heating susceptibility, χ | {args.chi:g} °C/PWM |
| Proportional gain, Kp | {args.kp:g} PWM/°C |
| Median sampling interval | {result['sample_interval_s']:.3f} s |

The final-window mean approximates the settled temperature; averaging alone
does not establish that the system has settled.

## Calculation

### 1. Find the 63% temperature

T₆₃ = Tᵢ + 0.63 × (T𝒇 − Tᵢ)

T₆₃ = {result['initial_C']:.3f} + 0.63 × ({result['final_mean_C']:.3f} − {result['initial_C']:.3f})

**T₆₃ = {result['threshold_63_C']:.3f} °C**

### 2. Read the first crossing time

The temperature first reaches the threshold **{result['tau_closed_loop_s']:.3f} s**
after the initial recorded reading. The crossing lies between adjacent
measurements at {crossing_lower:.3f} and {crossing_upper:.3f} s.

Because P feedback is active, this estimates **τ_cl**, rather than τ = C/H.
The exact exponential fraction at one time constant is 1 − exp(−1) ≈ 0.632;
the lab uses the practical approximation 0.63.

### 3. Correct for P feedback

τ_cl = τ / (1 + χKp), so τ = (1 + χKp) × τ_cl.

τ ≈ [1 + ({args.chi:g}) × ({args.kp:g})] × {result['tau_closed_loop_s']:.3f}

τ ≈ {result['correction_factor']:.3f} × {result['tau_closed_loop_s']:.3f}

**τ ≈ {result['inferred_open_loop_tau_s']:.2f} s**

## Annotated measurement plot

![Recorded temperature, 63% threshold, crossing time and signed PWM]({plot_link})

The orange horizontal line marks T₆₃. The purple vertical line marks the
first crossing. The green shaded region identifies the final averaging
window. The lower panel shows the changing PWM during P feedback.
All recorded excursions are retained; no temperature points are filtered out.

## Uncertainty and limitations

| Check | Result |
|---|---:|
| Corrected adjacent-sample crossing bracket | {lower:.2f}–{upper:.2f} s |
| One sampling interval after correction | {result['one_sample_timing_scale_s']:.2f} s |

These describe sampling resolution, not a confidence interval or a complete
uncertainty budget. Command timing within a sample, susceptibility uncertainty,
thermal lag, ambient drift, and departures from a single exponential can add
systematic error. A direct constant-PWM open-loop step would avoid the
P-feedback correction. The inferred τ determines C/H; it does not determine
C and H separately.

### Sensitivity to the final averaging window

| Final window (s) | Final mean (°C) | 63% threshold (°C) | Inferred τ (s), first sample | Interpolated τ (s) |
|---:|---:|---:|---:|---:|
{sensitivity_rows}

The primary result uses the first sampled crossing, as specified in the lab.
Different thresholds can cross at exactly the same recorded sample. The last
column interpolates between the two bracketing readings to show smaller
differences; it assumes a locally linear rise and adds no measurement precision.

## Data and reproducibility

Source recording: [{args.input.name}]({source_link})

- [Annotated PNG]({plot_link})
- [Worked analysis and independent cross-check](README.md)

Re-run `estimate_tau.py` to reproduce the calculation. Use `--export-data`
only if you need an additional JSON calculation or selected-trace CSV.

The matching Module 5 Arduino sketch averages 1,000 raw ADC readings before
temperature conversion. The CSV itself does not record the firmware version
or averaging count; confirm that the matching sketch was used for this run.
'''
    report_path.write_text(report)
    if open_loop:
        report = report.replace('**Estimated open-loop time constant:', '**Directly measured open-loop time constant:')
        report = report.replace(
            f'This estimate uses a recorded P-control response with Kp = {args.kp:g} PWM/°C.\nThe measured 63% crossing gives the closed-loop time constant; the open-loop\nvalue is inferred using the unsaturated one-lump model.',
            'This is a fresh constant-PWM open-loop measurement. No P or PI feedback\nwas active, so the 63% crossing directly estimates τ = C/H.')
        report = report.replace('Because P feedback is active, this estimates **τ_cl**, rather than τ = C/H.',
                                'Because PWM is constant and feedback is off, this directly estimates **τ = C/H**.')
        start = report.index('### 3. Correct for P feedback')
        end = report.index('## Annotated measurement plot', start)
        report = report[:start] + f'### 3. Open-loop result\n\nNo feedback correction is required. **τ ≈ {result["inferred_open_loop_tau_s"]:.2f} s.**\n\n' + report[end:]
        report = report.replace('The lower panel shows the changing PWM during P feedback.',
                                'The lower panel confirms the constant applied PWM during the step.')
        report = report.replace('A direct constant-PWM open-loop step would avoid the\nP-feedback correction.',
                                'This constant-PWM run avoids a P-feedback correction.')
        report = report.replace('Inferred τ (s)', 'Measured τ (s)').replace('Corrected adjacent-sample crossing bracket','Adjacent-sample crossing bracket').replace('One sampling interval after correction','One sampling interval')
        report = report.replace(f'| Heating susceptibility, χ | {args.chi:g} °C/PWM |\n', '')
        report = report.replace(f'| Proportional gain, Kp | {args.kp:g} PWM/°C |',
                                f'| Constant applied heating command | +{rows[-1]["command_pwm"]} PWM |')
        report = report.replace('Command timing within a sample, susceptibility uncertainty,',
                                'Command timing within a sample, temperature measurement uncertainty,')
        report_path.write_text(report)
    print(f"{'Measured' if open_loop else 'Estimated'} open-loop τ: {result['inferred_open_loop_tau_s']:.1f} s "
          f"({'constant-PWM step' if open_loop else 'P-feedback-corrected'})")
    print(f'Markdown report: {report_path}')


if __name__ == '__main__':
    main()
