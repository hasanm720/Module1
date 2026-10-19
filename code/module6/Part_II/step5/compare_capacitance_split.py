"""Vary only the capacitance split in the assigned two-lump P model."""
from dataclasses import replace
import os
from pathlib import Path
import sys

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/phys39-part7-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'step1'))
import Lab_6_7_modeling_tec as model


def main():
    base = replace(model.ModelConfig(), ambient_c=29, initial_c=29, setpoint_c=30,
                   total_capacitance_j_per_c=91, tec_capacitance_fraction=.35,
                   coupling_w_per_c=50, heat_loss_w_per_c=1.14, tec_power_w_per_pwm=.26,
                   heating_to_cooling_ratio=2, kp_pwm_per_c=105,
                   ki_pwm_per_c_s=0, pwm_limit=255, dt_s=.05)
    fig, ax = plt.subplots(figsize=(10, 5))
    zoom = ax.inset_axes([.53, .18, .43, .37])
    final = 30-model.predicted_p_droop(base)
    print('Only CT/C changes; total C stays 91 J/K; both masses reset to 29 °C.')
    print('| CT/C | Predicted zeta | Peak above equilibrium (°C) | Saturated samples |')
    print('|---:|---:|---:|---:|')
    for fraction, expected in [(.20, 1.19), (.35, 1.00), (.50, .96), (.80, 1.21)]:
        config = replace(base, tec_capacitance_fraction=fraction)
        zeta = model.two_lump_p_damping_ratio(config)
        if abs(zeta-expected)>.015:
            raise ValueError('Damping prediction does not match the assignment.')
        results = model.simulate(config, 'two_lump', 'p', 30)
        times = [0]+[r.time_s for r in results]
        temperatures = [29]+[r.measured_temperature_c for r in results]
        saturation = sum(r.saturated for r in results)
        if saturation:
            raise ValueError('Unexpected saturation in the capacitance-split comparison.')
        print(f'| {fraction:.2f} | {zeta:.3f} | {max(0,max(temperatures)-final):.5f} | {saturation} |')
        ax.plot(times, temperatures, label=f'CT/C = {fraction:.2f}, ζ = {zeta:.3f}')
        zoom.plot(times, temperatures)
    ax.axhline(30, color='black', linestyle='--', linewidth=1, label='Setpoint 30 °C')
    ax.set(xlabel='Simulated time (s)', ylabel='Measured-mass temperature Tm (°C)',
           title='Step 5 — Capacitance split changes damping (Kp = 105, G = 50 W/K)',
           xlim=(0, 12))
    ax.grid(alpha=.3)
    ax.legend()
    zoom.axhline(final, color='black', linestyle=':', linewidth=1)
    zoom.set(xlim=(2, 10), ylim=(29.95, 30.002), title='Zoom; dotted line = equilibrium')
    zoom.grid(alpha=.3)
    zoom.tick_params(labelsize=8)
    fig.tight_layout()
    output = Path(__file__).resolve().parent/'results'/'capacitance_split_comparison.png'
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f'Figure saved: {output}')


if __name__ == '__main__':
    main()
