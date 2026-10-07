"""Reconstruct Part 5 strip charts from the recorded CSV, without an Arduino.

Run: python3 code/module5/P5_high_gain_response/plot_strip_charts.py
Saves one PNG per recorded gain in strip_charts/ beside this script.
"""
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def main():
    runs = defaultdict(list)
    with (HERE / 'high_gain_20261005_110725.csv').open(newline='') as source:
        for row in csv.DictReader(source):
            runs[float(row['kp_pwm_per_C'])].append(row)
    output = HERE / 'strip_charts'
    output.mkdir(exist_ok=True)
    for gain, rows in sorted(runs.items()):
        time = [float(row['gain_elapsed_s']) for row in rows]
        temperature = [float(row['temperature_C']) for row in rows]
        target = [float(row['setpoint_C']) for row in rows]
        reported = [float(row['reported_pwm']) for row in rows]
        commanded = [float(row['command_pwm']) for row in rows]
        fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
        axes[0].plot(time, temperature, color='red', label='Measured temperature')
        axes[0].plot(time, target, '--', color='green', label='Setpoint')
        axes[0].set_ylabel('Temperature (°C)')
        axes[1].step(time, reported, where='post', label='Reported PWM')
        axes[1].step(time, commanded, where='post', linestyle='--',
                     alpha=0.75, label='Commanded PWM')
        axes[1].set_ylabel('PWM (counts)')
        axes[2].plot(time, [s - t for s, t in zip(target, temperature)],
                     color='#c45100', label='Setpoint − temperature')
        axes[2].axhline(0, color='gray', linewidth=0.8)
        axes[2].set_ylabel('Error (°C)')
        axes[2].set_xlabel('Elapsed time at this gain (s)')
        for ax in axes:
            ax.grid(alpha=0.3)
            ax.legend(loc='best')
            ax.set_xlim(0, time[-1])
        fig.suptitle(f'Module 5 Part 5: Kp = {gain:g} PWM/°C')
        fig.text(0.5, 0.015, 'Reconstructed from recorded CSV measurements; full recorded run',
                 ha='center', fontsize=9)
        fig.tight_layout(rect=(0, 0.035, 1, 0.96))
        fig.savefig(output / f'kp_{gain:g}_strip_chart.png', dpi=200)
        plt.close(fig)
    print(f'Saved strip charts for gains {", ".join(f"{gain:g}" for gain in sorted(runs))} to {output}')


if __name__ == '__main__':
    main()
