"""Reproduce Part 4 with the prepared one-lump Euler simulation; no Arduino.

Saves PART4_RESULTS.md and four plots. Optional --voltage is the measured
ON-state voltage across the TEC; without it, 12 V is explicitly provisional.
"""
import argparse
import csv
from dataclasses import replace
import math
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import Lab_6_7_modeling_tec as model

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[2]


def measured_config(chi_c, chi_h, tau, voltage, ambient, initial):
    derived = model.constants_from_measurements(chi_c, chi_h, tau, voltage, 1.5)
    return model.ModelConfig(
        ambient_c=ambient, initial_c=initial,
        measured_cooling_chi_c_per_pwm=chi_c,
        measured_heating_chi_c_per_pwm=chi_h, measured_tau_s=tau,
        tec_voltage_v=voltage, tec_resistance_ohm=1.5,
        total_capacitance_j_per_c=derived.total_capacitance_j_per_c,
        heat_loss_w_per_c=derived.heat_loss_w_per_c,
        tec_power_w_per_pwm=derived.cooling_power_w_per_pwm,
        heating_to_cooling_ratio=derived.heating_to_cooling_ratio,
        dt_s=.05, ki_pwm_per_c_s=0)


def curve(config, mode, duration):
    results = model.simulate(config, 'one_lump', mode, duration)
    times = np.array([0]+[r.time_s for r in results])
    temperatures = np.array([config.initial_c]+[r.measured_temperature_c for r in results])
    return times, temperatures


def decorate(ax, ylabel='Temperature (°C)'):
    ax.set_xlabel('Elapsed time (s)')
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.3)
    ax.legend()


def save(fig, name):
    fig.tight_layout()
    fig.savefig(HERE/'results'/name, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--voltage', type=float, help='Measured ON-state TEC voltage, V')
    args = parser.parse_args()
    voltage = 12 if args.voltage is None else args.voltage
    if not math.isfinite(voltage) or not 0 < voltage <= 12:
        parser.error('Measured voltage must be finite, positive and at most 12 V.')
    (HERE/'results').mkdir(exist_ok=True)
    # Fresh Part 3 data: use first pre-command sample as time zero; final 60 s.
    paths = sorted((HERE.parent/'P3_estimate_tau/data').glob('open_loop_step_*.csv'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not paths:
        raise ValueError('Need the fresh Part 3 recording.')
    source = paths[0]
    rows = [r for r in csv.DictReader(source.open()) if r['phase']=='step']
    t0 = float(rows[0]['gain_elapsed_s'])
    experiment_t = np.array([float(r['gain_elapsed_s'])-t0 for r in rows])
    experiment_T = np.array([float(r['temperature_C']) for r in rows])
    command_values = {float(r['command_pwm']) for r in rows}
    if len(command_values)!=1:
        raise ValueError('Part 3 command is not constant.')
    final = float(np.mean(experiment_T[experiment_t>=experiment_t[-1]-60]))
    initial = float(experiment_T[0])
    threshold = initial+.63*(final-initial)
    tau = float(experiment_t[np.flatnonzero(experiment_T>=threshold)[0]])
    baseline = [float(r['temperature_C']) for r in csv.DictReader(source.open())
                if r['phase']=='baseline']
    ambient = statistics.mean(baseline[-50:])
    measured = measured_config(.1878,.5311,tau,voltage,ambient,initial)
    defaults = measured_config(.23,.46,80,12,22,22)

    # Required default cases and independent analytic checks.
    fig, ax = plt.subplots(figsize=(10,5))
    default_lines = []
    max_exact_error = 0
    for u in (25,-25,-50):
        c = replace(defaults,open_loop_pwm=u)
        predicted = model.predicted_open_loop_steady_temperature(c)
        t,T = curve(c,'open_loop',1200)
        exact = predicted+(c.initial_c-predicted)*np.exp(-t/80)
        max_exact_error=max(max_exact_error,float(np.max(np.abs(T-exact))))
        recovered=(T[-1]-22)/u
        default_lines.append(f'| {u:+g} | {predicted:.3f} | {T[-1]:.3f} | {recovered:.5f} |')
        ax.plot(t,T,label=f'{u:+g} PWM → {predicted:g} °C')
    decorate(ax); ax.set_title('Guided defaults: one-lump open-loop simulation')
    save(fig,'01_default_open_loop.png')

    # Double only C, with the same constant +25 command.
    base = replace(defaults,open_loop_pwm=25)
    doubled = replace(base,total_capacitance_j_per_c=2*base.total_capacitance_j_per_c)
    fig,ax=plt.subplots(figsize=(10,5))
    for c,label in [(base,'Original C: τ=80 s'),(doubled,'Double C: τ=160 s')]:
        t,T=curve(c,'open_loop',2400)
        ax.plot(t,T,label=label)
    decorate(ax); ax.set_title('Double thermal capacitance: same endpoint, slower response')
    save(fig,'02_double_thermal_mass.png')

    # Match fresh heating command and initial condition, without fitting chi.
    u = next(iter(command_values))
    heat = replace(measured,open_loop_pwm=u)
    ht,hT=curve(heat,'open_loop',float(experiment_t[-1]))
    heating_prediction=model.predicted_open_loop_steady_temperature(heat)
    heating_rmse=float(np.sqrt(np.mean((np.interp(experiment_t,ht,hT)-experiment_T)**2)))
    fine = replace(heat,dt_s=.025)
    ft,fT=curve(fine,'open_loop',float(experiment_t[-1]))
    dt_error=float(np.max(np.abs(hT-np.interp(ht,ft,fT))))
    # Archived constant -47 PWM section, selected by command/time continuity.
    cooling_source=CODE/'module4/P1_Shutdown_Control/tec_safety_data.csv'
    archived=list(csv.DictReader(cooling_source.open()))
    segments=[]; group=[]
    for r in archived:
        valid=r['direction']=='COOL' and r['pwm']=='47' and r['safety']=='OK'
        if valid and (not group or float(r['time_s'])>float(group[-1]['time_s'])):
            group.append(r)
        else:
            if group: segments.append(group)
            group=[r] if valid else []
    if group: segments.append(group)
    cooling=max(segments,key=len)
    ct=np.array([float(r['time_s'])-float(cooling[0]['time_s']) for r in cooling])
    cT=np.array([float(r['temperature_C']) for r in cooling])
    cool=replace(measured,ambient_c=21.965,initial_c=float(cT[0]),open_loop_pwm=-47)
    st,sT=curve(cool,'open_loop',float(ct[-1]))
    cooling_prediction=model.predicted_open_loop_steady_temperature(cool)
    cooling_final=float(np.mean(cT[ct>=ct[-1]-60]))
    fig,axes=plt.subplots(2,1,figsize=(11,8))
    axes[0].plot(experiment_t,experiment_T,'r',label='Fresh +5 PWM measurement')
    axes[0].plot(ht,hT,'--',label='One-lump prediction (Module 4 χ, fresh τ)')
    axes[0].axhline(heating_prediction,color='gray',linestyle=':',label='Predicted equilibrium')
    axes[1].plot(ct,cT,'b',label='Archived −47 PWM: 500-reading averaging')
    axes[1].plot(st,sT,'--',label='One-lump prediction; historical ambient')
    for ax in axes: decorate(ax)
    axes[0].set_title('Heating: independent susceptibility, τ estimated from this same trace')
    axes[1].set_title('Cooling comparison: limited acquisition provenance; exploratory')
    save(fig,'03_experiment_comparison.png')

    # P comparisons: retain physical constants, initial condition and target.
    fig,ax=plt.subplots(figsize=(10,5))
    p_notes=[]
    for kp in (10,20):
        c=replace(measured,kp_pwm_per_c=kp,setpoint_c=30)
        droop=model.predicted_p_droop(c)
        p_tau=model.predicted_p_time_constant(c)
        t,T=curve(c,'p',600)
        endpoint=30-droop
        assert abs(T[-1]-endpoint)<1e-5
        exact=endpoint+(initial-endpoint)*np.exp(-t/p_tau)
        analytic_error=float(np.max(np.abs(T-exact)))
        assert analytic_error < .01
        p_notes.append(f'- **Kp={kp:g}, Ki=0:** predicted droop {droop:.3f} °C, '
                       f'τ_cl={p_tau:.2f} s and T_ss={endpoint:.3f} °C. '
                       f'Euler endpoint agrees within 0.00001 °C; maximum transient '
                       f'difference from the analytic exponential is {analytic_error:.4f} °C.')
        ax.plot(t,T,label=f'Kp={kp:g}: τ_cl={p_tau:.2f} s, droop={droop:.3f} °C')
    ax.axhline(30,color='green',linestyle='--',label='Setpoint 30 °C')
    decorate(ax); ax.set_title('P control: unchanged one-lump physical parameters')
    save(fig,'04_p_control.png')
    assert max_exact_error < .01 and dt_error < .01
    voltage_note=(f'Measured ON-state voltage supplied: **{voltage:g} V**.' if args.voltage is not None else
                  '**ON-state voltage has not been supplied.** The 12 V program default is provisional, '
                  'not a measurement. The temperature predictions remain defined by measured χ and τ; '
                  'absolute C, H and P_u values require the actual voltage.')
    report=fr'''# Module 6 Part 4 — One-lump open-loop and P simulations

**Completed the numerical guided exercises using the provided simulation's
`simulate()` and `advance_model()` functions. No Arduino power is used.**

## 1. Equations and implementation

The prepared model advances temperature with forward Euler:

$$T_{{n+1}}=T_n+\frac{{\Delta t}}{{C}}[P_u u-H(T_n-T_{{amb}})]
=T_n+\frac{{\Delta t}}{{\tau}}(T_{{amb}}+\chi u-T_n).$$

`advance_model()` computes applied TEC power, subtracts passive heat loss,
divides by C, then multiplies by dt. `active_tec_coefficient()` chooses the
heating or cooling coefficient according to signed u. This analysis imports
that implementation rather than replacing its physics.

## 2. Required default open-loop cases

Settings: one_lump, measured, open_loop; ambient/initial 22 °C,
χ_h=0.46 °C/PWM, χ_c=0.23 °C/PWM, τ=80 s, dt=0.05 s, PWM limit ±255.
Predictions use **T_ss=T_amb+χu** before numerical integration.

| Signed PWM | Predicted equilibrium (°C) | Simulated at 1200 s (°C) | Recovered χ (°C/PWM) |
|---:|---:|---:|---:|
{chr(10).join(default_lines)}

The recovered slopes agree with χ_h=0.46 and χ_c=0.23, giving r=2.
Equal positive/negative PWM produce unequal excursions because reversible
Peltier transport changes sign while Joule heating contributes in both
directions: it aids heating and offsets cooling. The maximum Euler departure
from the exact open-loop exponential is {max_exact_error:.4f} °C.

![Default open-loop cases](results/01_default_open_loop.png)

## 3. Double thermal capacitance only

Hold +25 PWM and keep H, P_u,c and r fixed. The default measured-parameter
inversion gives C={base.total_capacitance_j_per_c:.3f} J/°C. Switch to direct
constants and double C to {doubled.total_capacitance_j_per_c:.3f} J/°C.

**Prediction and numerical result:** equilibrium stays at 33.5 °C, while
τ=C/H doubles from 80 to 160 s. More heat capacity requires more energy to
change temperature; it does not change the final zero-storage heat balance.
Return to measured parameters for the following comparisons.

![Thermal mass comparison](results/02_double_thermal_mass.png)

## 4. Measured-parameter simulation settings

| Parameter | Value and source |
|---|---|
| χ_h | 0.5311 °C/PWM; Module 4 heating fit |
| χ_c | 0.1878 °C/PWM; Module 4 cooling fit |
| Ratio r | {measured.heating_to_cooling_ratio:.4f} |
| τ | {tau:.2f} s; fresh Part 3 63% measurement |
| Heating ambient | {ambient:.3f} °C; late zero-PWM baseline mean |
| Heating initial temperature | {initial:.3f} °C |
| Heating command | +{u:g} PWM; matches the fresh measurement |
| Cooling ambient | 21.965 °C; Module 4 zero-PWM range midpoint |
| Cooling initial temperature | {cT[0]:.3f} °C; first recorded sample |
| Cooling command | −47 PWM; matches the archived segment |
| dt | 0.05 s; checked again at 0.025 s |
| TEC module resistance | 1.50 Ω; supplied Laird datasheet |
| PWM clamp | ±255 counts |

{voltage_note}

Temperature dynamics use P_u/H=χ and C/H=τ. At fixed χ and τ, changing the
voltage used in the inversion rescales dimensional constants together and
does not change these one-lump temperature trajectories. It does affect
the inferred physical power and capacitance.

## 5. Experiment versus model

**Fresh heating:** predicted T_ss={heating_prediction:.3f} °C; recorded
final-60-s mean={final:.3f} °C, so the prediction is
{heating_prediction-final:+.3f} °C relative to the measurement. Full-trace
RMSE is {heating_rmse:.3f} °C. The same heating trace supplied τ, so transient
agreement is not an independent validation. The susceptibility comes from
the earlier Module 4 measurement and has not been refitted here.

**Archived cooling:** predicted T_ss={cooling_prediction:.3f} °C; final-60-s
mean={cooling_final:.3f} °C. This segment runs from Arduino time
{cooling[0]['time_s']} to {cooling[-1]['time_s']} s. Although u is negative,
temperature rises because the initial block is colder than the equilibrium
for −47 PWM after a stronger cooling command. Command direction alone does
not determine the sign of dT/dt.

**Cooling evidence limitation:** the current Module 4 sketch averages 500 raw
readings. This archived trace is an exploratory comparison, not a verified
1,000-reading measurement. A qualifying cooling trace is still needed if
the instructor requires that acquisition rule for the Part 4 comparison.
The newly measured τ is also being carried across dates and directions as
a one-lump approximation. No fresh cooling run was performed here.

The model assumes one uniform thermal temperature, fixed ambient and constant
susceptibility. The fresh recording shows local deviations and a lower final
heating temperature; heat transport, changing ambient/contact conditions and
direction/temperature dependence of effective TEC power can explain departures.
These data do not independently identify which mechanism dominates.

![Measured traces and model predictions](results/03_experiment_comparison.png)

## 6. Numerical time-step check

dt/τ={measured.dt_s/tau:.6f}. Halving dt from 0.05 to 0.025 s changes the fresh
heating prediction by at most **{dt_error:.6f} °C** at common sample times.
That is below the recorded 0.01 °C reporting increment. Numerical integration
error is small compared with the experiment/model disagreement.

## 7. Continue with P control

Keep the measured physical parameters, initial temperature and 30 °C target;
use Kp=10 from Module 5 and the larger Kp=20. Predictions are

$$\mathrm{{droop}}=\frac{{T_{{set}}-T_{{amb}}}}{{1+\chi_hK_p}},
\qquad \tau_{{cl}}=\frac{{\tau}}{{1+\chi_hK_p}}.$$

{chr(10).join(p_notes)}

Increasing Kp reduces both droop and response time. These simulated traces
are monotonic and remain unsaturated; they do not reproduce high-gain
experimental ringing. Settings and agreement are recorded here without
creating another P-control data table.

![P-control gain comparison](results/04_p_control.png)

## Files and how to reproduce

- [Prepared interactive simulation](Lab_6_7_modeling_tec.py)
- [Analysis runner](run_part4.py)
- [Fresh heating CSV](../P3_estimate_tau/data/{source.name})
- [Module 4 susceptibility results](../../../../docs/other_files/module4/P4_Temperature_susceptibility/susceptibility_results.md)
- [Archived cooling CSV](../../../module4/P1_Shutdown_Control/tec_safety_data.csv)

From the PHYS 39a workspace:

```sh
python PHYS39A_instrumentation/code/module6/Part1/P4_Simulate_open_loop_control/run_part4.py
```

Supply `--voltage YOUR_MEASURED_VALUE` to replace the provisional voltage.
For the interactive prepared GUI, run the same path with
`Lab_6_7_modeling_tec.py` instead of `run_part4.py`; select one_lump and measured
and enter the values above. The GUI still starts with its original defaults.
All curves in this report are explicitly simulations or labeled recordings.
'''
    (HERE/'PART4_RESULTS.md').write_text(report)
    print(f'Report: {HERE / "PART4_RESULTS.md"}')
    print(f'Fresh τ={tau:.2f} s; heating prediction={heating_prediction:.3f} °C; measured={final:.3f} °C')
    print('Four plots saved; analytic and time-step checks passed.')


if __name__=='__main__':
    main()
