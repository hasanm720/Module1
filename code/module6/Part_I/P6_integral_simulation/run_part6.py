"""Reproduce the Part 6 one-lump PI exercises without hardware."""
from pathlib import Path
import sys
import csv
import argparse
from dataclasses import replace
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'P4_Simulate_open_loop_control'))
from run_part4 import measured_config
import Lab_6_7_modeling_tec as model

CONFIG = measured_config(.1878, .5311, 91.69, 12, 24.220, 24.210)
CONFIG = replace(CONFIG, kp_pwm_per_c=10, ki_pwm_per_c_s=.08, setpoint_c=30)
FIELDS = ['time_s', 'temperature_C', 'setpoint_C', 'error_C', 'u_P', 'u_I',
          'requested_pwm', 'applied_pwm', 'q_C_s', 'stage']


def segment(state, config, mode, duration, stage, rows):
    for _ in range(round(duration/config.dt_s)):
        # Record temperature/error at the same instant as the controller terms.
        before = state.tec_temperature_c
        r = model.advance_model(state, config, 'one_lump', mode)
        rows.append([state.time_s-config.dt_s, before, config.setpoint_c,
                     config.setpoint_c-before, r.p_pwm, r.i_pwm,
                     r.p_pwm+r.i_pwm, r.applied_pwm, state.integral_error_c_s, stage])


def save(rows, name, export_csv=False):
    if export_csv:
        with (HERE/'results'/f'{name}.csv').open('w', newline='') as f:
            writer = csv.writer(f); writer.writerow(FIELDS); writer.writerows(rows)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    t = [r[0] for r in rows]
    for ax, indices, labels in zip(axes, [(1,2), (3,), (4,5,7)],
                                  [('Temperature','Setpoint'), ('Error',), ('P','I','Applied PWM')]):
        for i,label in zip(indices,labels): ax.plot(t,[r[i] for r in rows],label=label)
        ax.legend(); ax.grid(alpha=.3)
    for ax,label in zip(axes,['Temperature (°C)','Error (°C)','PWM counts']): ax.set_ylabel(label)
    axes[-1].set_xlabel('Time (s)'); fig.tight_layout()
    fig.savefig(HERE/'results'/f'{name}.png', dpi=160); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save-csv', action='store_true', help='Export simulation time series')
    args = parser.parse_args()
    (HERE/'results').mkdir(exist_ok=True)
    state = model.ModelState(0, CONFIG.initial_c, CONFIG.initial_c)
    rows=[]
    segment(state,CONFIG,'p',600,'P',rows)
    p_temperature=state.tec_temperature_c
    state.integral_error_c_s=0
    segment(state,CONFIG,'pi',1800,'PI',rows)
    pi_temperature=state.tec_temperature_c
    i_steady=CONFIG.ki_pwm_per_c_s*state.integral_error_c_s
    assert abs(pi_temperature-30)<.001
    state.integral_error_c_s=0
    segment(state,CONFIG,'pi',300,'Integral reset',rows)
    save(rows,'01_p_to_pi_and_reset',args.save_csv)
    notes=[]
    for ki in (.02,.2,2):
        c=replace(CONFIG,ki_pwm_per_c_s=ki)
        state=model.ModelState(0,c.initial_c,c.initial_c); rows=[]
        segment(state,c,'pi',1800,'PI',rows)
        save(rows,f'gain_ki_{ki:g}',args.save_csv)
        notes.append(f'- Ki = {ki:g} PWM/(°C·s): damping ratio ζ = {model.one_lump_pi_damping_ratio(c):.3f}.')
    for aw in (False,True):
        c=replace(CONFIG,pwm_limit=8,ki_pwm_per_c_s=.2,anti_windup=aw)
        state=model.ModelState(0,c.initial_c,c.initial_c); rows=[]
        segment(state,c,'pi',300,'Limited output, target 30 °C',rows)
        segment(state,replace(c,setpoint_c=26),'pi',600,'Target lowered to 26 °C',rows)
        save(rows,f'windup_{"on" if aw else "off"}',args.save_csv)
    (HERE/'PART6_RESULTS.md').write_text(f'''# Part 6 — Integral action in simulation

Settings: one lump, 12 V, χ_h = 0.5311 °C/PWM, χ_c = 0.1878 °C/PWM,
τ = 91.69 s, Δt = 0.05 s, ambient 24.220 °C, target 30 °C,
Kp = 10 PWM/°C, Ki = 0.08 PWM/(°C·s), PWM limit ±255, anti-windup on.

Start with P control, let it settle, then switch to PI with q = 0.
P settles at **{p_temperature:.3f} °C**; PI reaches **{pi_temperature:.3f} °C**.

## Guided answers

1. **Why does u_I grow while e > 0?** Each step adds eΔt to the stored error q. Since u_I = Ki q, the integral contribution grows.
2. **Why does u_P approach zero at the target?** u_P = Kp e, and the error approaches zero.
3. **Why can u_I remain nonzero when e = 0?** Zero error stops adding to q; it does not erase q. Here u_I remains about **{i_steady:.3f} PWM**, supplying the heat lost to the room.
4. **Why does resetting the integral move temperature away from the target?** Resetting q removes that heating command. The block initially cools; the controller then rebuilds the required output.

![P to PI, then integral reset](results/01_p_to_pi_and_reset.png)

## Changing Ki

Keep Kp = 10 and reset q before each run.

{chr(10).join(notes)}

Larger Ki corrects the stored error more strongly and lowers damping. The high-Ki
case overshoots and rings, but the oscillations decay. Underdamped does not mean unstable.

![Low Ki](results/gain_ki_0.02.png)
![Intermediate Ki](results/gain_ki_0.2.png)
![High Ki](results/gain_ki_2.png)

## Windup and anti-windup

For this demonstration only, limit PWM to ±8, use Ki = 0.2, and lower the target
from 30 to 26 °C at 300 s. The 30 °C target requires more than 8 PWM.

Without anti-windup, q keeps growing while PWM is capped. The stored error delays
recovery after the target drops. With anti-windup, q is held when adding error
would push the request farther beyond the limit. Error that brings it back is allowed.
The PWM clamp limits output; anti-windup limits stored error; reset clears stored error.

![Without anti-windup](results/windup_off.png)
![With anti-windup](results/windup_on.png)

Add `--save-csv` to export simulation time series if needed.
Reproduce with `python3 run_part6.py` from this directory.
''')
    print('Part 6 report and six plots saved; PI steady-state check passed.')

if __name__=='__main__': main()
