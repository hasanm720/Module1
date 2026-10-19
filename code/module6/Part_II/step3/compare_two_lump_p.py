"""Verify the assigned two-lump P damping transition using direct constants."""
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
    # Assigned demonstration settings, independent of the apparatus baseline.
    base = replace(model.ModelConfig(), ambient_c=29, initial_c=29, setpoint_c=30,
                   total_capacitance_j_per_c=91, tec_capacitance_fraction=.35,
                   coupling_w_per_c=50, heat_loss_w_per_c=1.14,
                   tec_power_w_per_pwm=.26, heating_to_cooling_ratio=2,
                   ki_pwm_per_c_s=0, pwm_limit=255, dt_s=.05)
    fig, ax = plt.subplots(figsize=(10, 5))
    zoom = ax.inset_axes([.53, .18, .43, .37])
    print('Two-lump P, direct constants; each run resets both masses to 29 °C.')
    print('| Kp | Predicted zeta | Behavior | Peak above final temperature (°C) | Saturated samples |')
    print('|---:|---:|---|---:|---:|')
    for kp, expected, behavior in [(60, 1.31, 'Overdamped'),
                                   (105, 1.00, 'Approximately critically damped'),
                                   (160, .81, 'Underdamped')]:
        config = replace(base, kp_pwm_per_c=kp)
        zeta = model.two_lump_p_damping_ratio(config)
        if abs(zeta-expected) > .015:
            raise ValueError('Damping ratio differs from the assigned prediction.')
        results = model.simulate(config, 'two_lump', 'p', 30)
        times = [0] + [r.time_s for r in results]
        temperatures = [29] + [r.measured_temperature_c for r in results]
        final = 30-model.predicted_p_droop(config)
        overshoot = max(0, max(temperatures)-final)
        saturated = sum(r.saturated for r in results)
        if saturated:
            raise ValueError('Saturation obscures the linear damping comparison.')
        print(f'| {kp} | {zeta:.3f} | {behavior} | {overshoot:.5f} | {saturated} |')
        ax.plot(times, temperatures, label=f'Kp = {kp}, ζ = {zeta:.3f}')
        zoom.plot(times, temperatures)
    ax.axhline(30, color='black', linestyle='--', linewidth=1, label='Setpoint 30 °C')
    ax.set(xlabel='Simulated time (s)', ylabel='Measured-mass temperature Tm (°C)',
           title='Step 3 — Two-lump P: overdamped to underdamped', xlim=(0, 12))
    ax.grid(alpha=.3)
    ax.legend()
    zoom.axhline(30, color='black', linestyle='--', linewidth=1)
    zoom.set(xlim=(2, 10), ylim=(29.96, 30.006), title='Zoom near final temperatures')
    zoom.grid(alpha=.3)
    zoom.tick_params(labelsize=8)
    fig.tight_layout()
    output = Path(__file__).resolve().parent / 'results' / 'two_lump_p_transition.png'
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f'Figure saved: {output}')

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    print('\nAdditional saturation comparison (same physical settings):')
    print('| Kp | Initial request | Applied range | Clipped duration (s) | Peak Tm (°C) |')
    print('|---:|---:|---|---:|---:|')
    for kp in (160, 300, 1000):
        config = replace(base, kp_pwm_per_c=kp)
        results = model.simulate(config, 'two_lump', 'p', 30)
        times = [r.time_s for r in results]
        temperatures = [r.measured_temperature_c for r in results]
        applied = [r.applied_pwm for r in results]
        clipped_s = sum(r.saturated for r in results)*config.dt_s
        if any(abs(u)>255 for u in applied):
            raise ValueError('Applied PWM exceeds its limit.')
        if kp>255 and not results[0].saturated:
            raise ValueError('Expected initial saturation was not observed.')
        print(f'| {kp} | {kp} | {min(applied):.1f} to {max(applied):.1f} | '
              f'{clipped_s:.2f} | {max(temperatures):.3f} |')
        axes[0].plot([0]+times, [29]+temperatures, label=f'Kp = {kp}')
        axes[1].plot(times, applied, label=f'Kp = {kp}')
    axes[0].axhline(30, color='black', linestyle='--', linewidth=1, label='Setpoint')
    axes[0].set_ylabel('Measured-mass temperature (°C)')
    axes[0].set_title('Step 3 — Higher Kp causes PWM saturation')
    axes[1].set(xlabel='Simulated time (s)', ylabel='Signed applied PWM',
                xlim=(0, 12), ylim=(-270, 270), yticks=[-255, 0, 255])
    for limit in (-255,255):
        axes[1].axhline(limit, color='black', linestyle='--', linewidth=1)
    for ax in axes:
        ax.grid(alpha=.3)
        ax.legend()
    fig.tight_layout()
    output = output.with_name('two_lump_p_saturation.png')
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f'Figure saved: {output}')


if __name__ == '__main__':
    main()
