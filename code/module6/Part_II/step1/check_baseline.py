"""Load and verify the saved one-lump baseline without rerunning a study."""
import argparse
import csv
from dataclasses import replace
from pathlib import Path
import statistics

import Lab_6_7_modeling_tec as model

PART_I = Path(__file__).resolve().parents[2] / 'Part_I'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Verify without opening the GUI')
    args = parser.parse_args()
    source = PART_I / 'P3_estimate_tau/data/open_loop_step_20261013_113417_759949.csv'
    with source.open() as f:
        rows = list(csv.DictReader(f))
    ambient = statistics.mean([float(r['temperature_C']) for r in rows
                               if r['phase'] == 'baseline'][-50:])
    initial = float(next(r['temperature_C'] for r in rows if r['phase'] == 'step'))
    values = dict(ambient_c=ambient, initial_c=initial, setpoint_c=30,
                  measured_cooling_chi_c_per_pwm=.1878,
                  measured_heating_chi_c_per_pwm=.5311, measured_tau_s=91.69,
                  tec_voltage_v=12, tec_resistance_ohm=1.5,
                  kp_pwm_per_c=10, ki_pwm_per_c_s=0, pwm_limit=255, dt_s=.05)
    derived = model.constants_from_measurements(.1878, .5311, 91.69, 12, 1.5)
    config = replace(model.ModelConfig(), **values,
                     total_capacitance_j_per_c=derived.total_capacitance_j_per_c,
                     heat_loss_w_per_c=derived.heat_loss_w_per_c,
                     tec_power_w_per_pwm=derived.cooling_power_w_per_pwm,
                     heating_to_cooling_ratio=derived.heating_to_cooling_ratio)
    expected = [(model.cooling_susceptibility(config), .1878, 1e-10),
                (model.heating_susceptibility(config), .5311, 1e-10),
                (model.one_lump_time_constant(config), 91.69, 1e-8),
                (model.predicted_p_time_constant(config), 14.53, .005),
                (model.predicted_p_droop(config), .916, .0005)]
    if any(abs(actual - saved) > tolerance for actual, saved, tolerance in expected):
        raise ValueError('Baseline differs from the saved Part I results.')
    print('BASELINE CHECK PASSED', flush=True)
    print(f'Ambient / initial: {ambient:.2f} / {initial:.2f} °C', flush=True)
    print('Cooling / heating susceptibility: 0.1878 / 0.5311 °C/PWM', flush=True)
    print(f'Open-loop / P time constant: {expected[2][0]:.2f} / {expected[3][0]:.2f} s', flush=True)
    print(f'P droop: {expected[4][0]:.6f} °C (GUI rounds to 0.92 °C)', flush=True)
    if args.check_only:
        return
    root = model.tk.Tk()
    gui = model.ModelingTECGui(root)
    for name, value in values.items():
        gui.entries[name].set(value)
    gui._reset_experiment()
    print('GUI loaded in one_lump / measured / p mode, paused at t = 0.', flush=True)
    root.mainloop()


if __name__ == '__main__':
    main()
