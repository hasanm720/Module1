"""Reproduce Part 4 with the prepared one-lump Euler simulation; no Arduino.

Saves PART4_RESULTS.md and four plots. Optional --voltage sets the ON-state
TEC voltage; it remains assumed unless --voltage-confirmed is also supplied.
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
    parser.add_argument('--voltage', type=float, default=12.0,
                        help='ON-state TEC voltage, V (default: 12; assumed unless confirmed)')
    parser.add_argument('--voltage-confirmed', action='store_true',
                        help='Use only when the supplied voltage was actually measured across the TEC')
    args = parser.parse_args()
    voltage = args.voltage
    if not math.isfinite(voltage) or not 0 < voltage <= 12:
        parser.error('TEC voltage must be finite, positive and at most 12 V.')
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
                       f'time constant {p_tau:.2f} s, and final temperature {endpoint:.3f} °C.')
        ax.plot(t,T,label=f'Kp={kp:g}: τ_cl={p_tau:.2f} s, droop={droop:.3f} °C')
    ax.axhline(30,color='green',linestyle='--',label='Setpoint 30 °C')
    decorate(ax); ax.set_title('P control: unchanged one-lump physical parameters')
    save(fig,'04_p_control.png')
    assert max_exact_error < .01 and dt_error < .01
    voltage_note=(f'Measured TEC voltage: **{voltage:g} V**.' if args.voltage_confirmed else
                  f'TEC voltage: **{voltage:g} V** (assumed ON-state value).')
    report=fr'''# Module 6 Part 4 — Results

## 1. Heating and cooling

Resistive heat is produced in both directions. It helps heating but reduces
cooling, so +25 PWM heats more than −25 PWM cools.

Default settings: measured mode, ambient/initial temperature 22 °C,
τ = 80 s, Δt = 0.05 s. Predict T_ss = T_amb + χu.

| PWM | Predicted T_ss (°C) | Simulated at 1200 s (°C) | χ (°C/PWM) |
|---:|---:|---:|---:|
{chr(10).join(default_lines)}

Calculate χ = (T_ss − T_amb)/u:

- χ_h = (33.5 − 22)/25 = **0.46 °C/PWM**.
- χ_c = (16.25 − 22)/(−25) = **0.23 °C/PWM**.
- At −50 PWM: χ_c = (10.5 − 22)/(−50) = **0.23 °C/PWM**.
- Ratio r = 0.46/0.23 = **2**.

These agree with the simulation's displayed susceptibilities.

![Open-loop cases](results/01_default_open_loop.png)

## 2. Double thermal capacitance

Keep **+25 PWM** fixed. Select `direct constants` and double C from
**{base.total_capacitance_j_per_c:.3f} to {doubled.total_capacitance_j_per_c:.3f} J/°C**.
Leave H, P_u,c, and r unchanged.

**Prediction:** T_ss stays at **33.5 °C**; τ = C/H doubles from **80 to 160 s**.
**Simulation:** both predictions agree.

More thermal mass needs more energy to change temperature, so the response is
slower. At steady state, heat entering equals heat leaving; C does not change
that balance or the final temperature.

Return to `measured` for the following runs.

![Double thermal capacitance](results/02_double_thermal_mass.png)

## 3. Experimental settings

Use **+{u:g} PWM heating** and **−47 PWM cooling**, matching the recordings.
{voltage_note} TEC resistance: **1.50 Ω**.

| Setting | Heating | Cooling |
|---|---:|---:|
| Ambient | {ambient:.3f} °C | 21.965 °C |
| Initial temperature | {initial:.3f} °C | {cT[0]:.3f} °C |
| χ | 0.5311 °C/PWM | 0.1878 °C/PWM |

| Parameter | Value |
|---|---:|
| C | {measured.total_capacitance_j_per_c:.3f} J/°C |
| H | {measured.heat_loss_w_per_c:.4f} W/°C |
| P_u,c | {measured.tec_power_w_per_pwm:.5f} W/PWM |
| r | {measured.heating_to_cooling_ratio:.4f} (dimensionless) |
| τ | {tau:.2f} s |
| Δt | {measured.dt_s:.2f} s |

χ comes from Module 4; τ comes from Part 3 heating and is used for both directions.
The physical constants use the voltage above.

## 4. Simulation versus experiment

| Run | Predicted T_ss | Measured final-60-s mean |
|---|---:|---:|
| Heating, +{u:g} PWM | {heating_prediction:.3f} °C | {final:.3f} °C |
| Cooling, −47 PWM | {cooling_prediction:.3f} °C | {cooling_final:.3f} °C |

Heating is predicted {heating_prediction-final:.3f} °C too high; full-trace RMSE
is {heating_rmse:.3f} °C. The heating trace supplied τ, so its response-time
agreement is not an independent test.

The cooling trace warms because it starts below the steady temperature for
−47 PWM. Heat entering from the surroundings initially exceeds TEC cooling.

The model assumes uniform temperature and constant conditions. Temperature
gradients, changing ambient temperature, and changing thermal contact or TEC
performance can explain the differences; these data do not identify the main cause.

![Simulation and measured traces](results/03_experiment_comparison.png)

## 5. Time-step check

**Δt = 0.05 s ≪ τ = {tau:.2f} s.** Halving Δt to 0.025 s changes the heating
prediction by at most **{dt_error:.6f} °C**, well below the 0.01 °C reporting
increment. The result does not appreciably change.

## 6. P control

Select `p`; keep the measured parameters, initial temperature, and **30 °C** target.
Use **Kp = 10 from Module 5**, then **Kp = 20**; Ki = 0.

Before each run, predict:

$$\mathrm{{droop}}=\frac{{T_{{set}}-T_{{amb}}}}{{1+\chi_hK_p}},
\qquad \tau_{{cl}}=\frac{{\tau}}{{1+\chi_hK_p}}.$$

{chr(10).join(p_notes)}

**Both predictions agree with the simulation:** final temperatures agree within
0.00001 °C, and the simulated curves differ from the predicted exponential by
less than 0.01 °C. Increasing Kp reduces both droop and response time.
Droop is the final temperature shortfall below the target.

![P-control comparison](results/04_p_control.png)

## Reproduce

```sh
python PHYS39A_instrumentation/code/module6/Part1/P4_Simulate_open_loop_control/run_part4.py --voltage {voltage:g}
```

- [Simulation](Lab_6_7_modeling_tec.py) · [Runner](run_part4.py)
- [Heating data](../P3_estimate_tau/data/{source.name})
- [Cooling data](../../../module4/P1_Shutdown_Control/tec_safety_data.csv)
- [Module 4 fits](../../../../docs/other_files/module4/P4_Temperature_susceptibility/susceptibility_results.md)
'''
    (HERE/'PART4_RESULTS.md').write_text(report)
    print(f'Report: {HERE / "PART4_RESULTS.md"}')
    print(f'Fresh τ={tau:.2f} s; heating prediction={heating_prediction:.3f} °C; measured={final:.3f} °C')
    print('Four plots saved; analytic and time-step checks passed.')


if __name__=='__main__':
    main()
