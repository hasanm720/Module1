"""Three controlled one-lump PI comparisons; no additional A3 plots."""
from dataclasses import replace
from pathlib import Path
import sys
import os

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/phys39-part7-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'step1'))
import Lab_6_7_modeling_tec as model


def main():
    # Direct constants allow C to change independently of H and TEC power.
    derived = model.constants_from_measurements(.1878, .5311, 91.69, 12, 1.5)
    base = replace(model.ModelConfig(), ambient_c=24.22, initial_c=24.21,
                   setpoint_c=30, kp_pwm_per_c=10, ki_pwm_per_c_s=.5,
                   dt_s=.05, pwm_limit=255, anti_windup=True,
                   measured_cooling_chi_c_per_pwm=.1878,
                   measured_heating_chi_c_per_pwm=.5311, measured_tau_s=91.69,
                   total_capacitance_j_per_c=derived.total_capacitance_j_per_c,
                   heat_loss_w_per_c=derived.heat_loss_w_per_c,
                   tec_power_w_per_pwm=derived.cooling_power_w_per_pwm,
                   heating_to_cooling_ratio=derived.heating_to_cooling_ratio)
    cases = [('Low Ki', replace(base, ki_pwm_per_c_s=.1)),
             ('Reference', base),
             ('Higher Kp', replace(base, kp_pwm_per_c=20)),
             ('Double C', replace(base, total_capacitance_j_per_c=2*base.total_capacitance_j_per_c))]
    print('Prediction: increasing Ki or C lowers zeta; increasing Kp raises zeta.')
    print('All cases: one_lump / PI, direct constants, 24.21 → 30 °C, ambient 24.22 °C, PWM ±255.')
    print('Each case resets temperature and integral; duration 1200 s, dt 0.05 s.')
    print('| Case | Kp | Ki | C (J/K) | zeta | Overshoot (°C) | Target crossings | Saturated samples |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|')
    traces = {}
    for name, config in cases:
        results = model.simulate(config, 'one_lump', 'pi', 1200)
        temperatures = [config.initial_c] + [r.measured_temperature_c for r in results]
        traces[name] = ([0] + [r.time_s for r in results], temperatures)
        crossings = sum((a-30)*(b-30)<0 for a,b in zip(temperatures, temperatures[1:]))
        overshoot = max(0, max(temperatures)-30)
        saturated = sum(r.saturated for r in results)
        print(f'| {name} | {config.kp_pwm_per_c:g} | {config.ki_pwm_per_c_s:g} | '
              f'{config.total_capacitance_j_per_c:.3f} | '
              f'{model.one_lump_pi_damping_ratio(config):.3f} | '
              f'{overshoot:.3f} | {crossings} | {saturated} |')
    # Configurations are immutable: the measured baseline is never overwritten.
    print('Measured physical parameters retained; Double C is an isolated comparison.')
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True, sharey=True)
    comparisons = [
        ('Increase Ki; Kp = 10, C = 100.549 J/K',
         [('Low Ki', 'Ki = 0.1, ζ = 1.430'), ('Reference', 'Ki = 0.5, ζ = 0.639')]),
        ('Increase Kp; Ki = 0.5, C = 100.549 J/K',
         [('Reference', 'Kp = 10, ζ = 0.639'), ('Higher Kp', 'Kp = 20, ζ = 1.178')]),
        ('Double C; Kp = 10, Ki = 0.5; H and TEC power fixed',
         [('Reference', 'C = 100.549 J/K, ζ = 0.639'), ('Double C', 'C = 201.099 J/K, ζ = 0.452')])]
    for ax, (title, curves) in zip(axes, comparisons):
        for name, label in curves:
            ax.plot(*traces[name], label=label)
        ax.axhline(30, color='black', linestyle='--', linewidth=1, label='Setpoint 30 °C')
        ax.set_title(title)
        ax.set_ylabel('Temperature (°C)')
        ax.grid(alpha=.3)
        ax.legend(fontsize=9)
    axes[-1].set_xlabel('Simulated time (s)')
    axes[-1].set_xlim(0, 400)
    fig.suptitle('Step 2 — One-lump PI comparisons\nSame initial temperature, setpoint and PWM limit; no saturation')
    fig.tight_layout()
    output = Path(__file__).resolve().parent / 'results' / 'one_lump_pi_comparisons.png'
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f'Figure saved: {output}')


if __name__ == '__main__':
    main()
