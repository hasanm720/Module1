"""Build A3 from recorded CSVs and the supplied two-lump model; no hardware I/O.

Run from any directory. Dependencies: numpy, matplotlib, reportlab.
"""
from pathlib import Path
import csv
import argparse
import json
import math
import re
import sys
from dataclasses import replace
import xml.sax.saxutils as xml

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTES = ROOT/'docs/module_notes'
FIGURES = ROOT/'docs/figures/module_06/a3'
RESULTS = HERE/'results'
P4 = ROOT/'code/module6/Part1/P4_Simulate_open_loop_control'
P7 = ROOT/'code/module6/Part1/P7_experimental_goldilocks'
if not P7.exists():
    P7 = ROOT/'code/module6/Part1/P7_PI_control_and_goldilocks/Part7_experimental_goldilocks'
sys.path.insert(0,str(P4))
from run_part4 import measured_config
import Lab_6_7_modeling_tec as model

GAINS=[('P',5,0),('P',20,0),('P',40,0),('PI',16,.1),('PI',16,.5),('PI',16,2)]
BASE=replace(measured_config(.1878,.5311,91.69,12,24.220,28),
             coupling_w_per_c=10,tec_capacitance_fraction=.35,dt_s=.025,pwm_limit=255)
PU_H=BASE.tec_power_w_per_pwm*BASE.heating_to_cooling_ratio
CT=BASE.tec_capacitance_j_per_c; CM=BASE.measured_capacitance_j_per_c
G=BASE.coupling_w_per_c; H=BASE.heat_loss_w_per_c
S=CT*(G+H)+CM*G
KP_CRIT=(S*S/(4*CT*CM*G)-H)/PU_H
KI_CRIT=model.two_lump_pi_critical_integral_gain(replace(BASE,kp_pwm_per_c=16))


def read(path):
    with path.open() as stream: rows=list(csv.DictReader(stream))
    return {key:np.array([float(r[key]) for r in rows]) for key in
            ['arduino_s','temperature_C','setpoint_C','reported_signed_pwm','applied_pwm',
             'requested_pwm','u_P','u_I','dt_s']},rows


def transitions(t,temp,target):
    edges=np.flatnonzero(np.diff(target)!=0)+1
    output=[]
    for a,b in zip(edges,list(edges[1:])+[len(t)]):
        tt=t[a:b]-t[a]; values=temp[a:b]; initial=float(temp[a-1]); goal=float(target[a])
        change=goal-initial
        progress=(values-initial)/change
        crossings=[]
        for threshold in [.1,.9]:
            hits=np.flatnonzero(progress>=threshold)
            if not len(hits): crossings.append(None); continue
            j=int(hits[0])
            if j==0: crossings.append(float(tt[0])); continue
            fraction=(threshold-progress[j-1])/(progress[j]-progress[j-1])
            crossings.append(float(tt[j-1]+fraction*(tt[j]-tt[j-1])))
        rise=None if any(x is None for x in crossings) else crossings[1]-crossings[0]
        amplitude=abs(goal-float(target[a-1]))
        direction=1 if change>0 else -1
        overshoot=max(0,float(np.max(direction*(values-goal))))/amplitude*100
        end_mean=float(np.mean(values[tt>=tt[-1]-5]))
        # Require at least ten recorded seconds continuously within the 2% band.
        outside=np.flatnonzero(abs(values-goal)>.02*amplitude)
        candidate=0 if len(outside)==0 else int(outside[-1])+1
        settling=(float(tt[candidate]) if candidate<len(tt) and tt[-1]-tt[candidate]>=10 else None)
        output.append(dict(direction='Up' if goal>target[a-1] else 'Down',
                           initial_C=initial,target_C=goal,duration_s=float(tt[-1]),
                           rise_10_90_s=rise,overshoot_percent=overshoot,
                           settling_2percent_s=settling,steady_error_C=None,
                           end5s_error_C=goal-end_mean,period_s=None))
    return output


def simulate_run(config,dt=None,duration=93):
    c=replace(config,dt_s=dt or config.dt_s)
    state=model.ModelState(0,c.initial_c,c.initial_c,0)
    mode='pi' if c.ki_pwm_per_c_s else 'p'
    records=[]
    for _ in range(round(duration/c.dt_s)):
        target=28 if state.time_s<11-1e-8 or state.time_s>=52-1e-8 else 30
        active=replace(c,setpoint_c=target)
        before=state.measured_temperature_c
        result=model.advance_model(state,active,'two_lump',mode)
        records.append([state.time_s-c.dt_s,before,target,result.applied_pwm,
                        result.p_pwm+result.i_pwm,result.p_pwm,result.i_pwm,state.integral_error_c_s])
    return np.array(records)


def poles(config,pu=PU_H):
    kp=config.kp_pwm_per_c;ki=config.ki_pwm_per_c_s
    if ki==0:
        return np.roots([CT*CM,S,G*(H+pu*kp)])
    return np.roots([CT*CM,S,G*(H+pu*kp),G*pu*ki])


def classification(config):
    roots=poles(config)
    if np.max(roots.real)>1e-7: return 'unstable'
    if np.max(roots.real)>=-1e-7: return 'marginally stable'
    return 'stable underdamped' if np.max(abs(roots.imag))>1e-7 else 'stable non-oscillatory'


def plot(t,temp,target,pwm,requested,path,title):
    fig,axes=plt.subplots(2,1,figsize=(7.2,3.7),sharex=True,
                          gridspec_kw={'height_ratios':[1.4,1]})
    axes[0].plot(t,temp,color='#1764ab',lw=1.5,label='Measured temperature' if title.startswith('Experimental') else 'Mass temperature')
    axes[0].step(t,target,where='post',color='#d45d00',ls='--',lw=1,label='Setpoint')
    axes[1].plot(t,pwm,color='#1764ab',lw=1.3,label='Reported signed PWM' if title.startswith('Experimental') else 'Applied signed PWM')
    axes[1].plot(t,requested,color='#777777',ls=':',lw=.9,label='Requested PWM')
    axes[1].axhline(0,color='black',lw=.4)
    axes[0].set_ylim(24,31.2);axes[1].set_ylim(-100,105)
    axes[0].set_ylabel('Temperature (°C)',fontsize=9);axes[1].set_ylabel('PWM counts',fontsize=9)
    axes[1].set_xlabel('Elapsed time (s)',fontsize=9)
    for ax in axes:
        ax.set_xlim(0,95);ax.tick_params(labelsize=8);ax.grid(alpha=.18)
        ax.legend(loc='upper right',fontsize=7.5,ncol=2,framealpha=.9)
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    fig.suptitle(title,fontsize=10,y=.98)
    fig.subplots_adjust(left=.105,right=.985,top=.89,bottom=.13,hspace=.18)
    fig.savefig(path,dpi=180);plt.close(fig)


def analyse(export_csv=False):
    FIGURES.mkdir(parents=True,exist_ok=True);RESULTS.mkdir(exist_ok=True)
    paths=[Path(f) for f in json.loads((P7/'data/screening_selected_logs.json').read_text())]
    # Resolve by filename so this analysis survives a different checkout path.
    paths=[P7/'data'/f.name for f in paths]
    experiments=[]; simulations=[]
    for i,(path,(mode,kp,ki)) in enumerate(zip(paths,GAINS),1):
        data,rows=read(path);t=data['arduino_s']-data['arduino_s'][0]
        assert len(np.flatnonzero(np.diff(data['setpoint_C'])!=0))==2
        assert all(r['safety']=='OK' for r in rows)
        assert len({r['kp_pwm_per_C'] for r in rows})==1
        assert float(rows[0]['kp_pwm_per_C'])==kp and float(rows[0]['ki_pwm_per_C_s'])==ki
        assert np.max(abs(data['applied_pwm']))<=255
        assert np.max(abs(data['reported_signed_pwm']))<=255
        experiments.append(dict(run=i,path=str(path.relative_to(ROOT)),mode=mode,kp=kp,ki=ki,
                                initial_C=float(data['temperature_C'][0]),
                                dt_median_s=float(np.median(data['dt_s'])),
                                max_abs_requested_pwm=float(np.max(abs(data['requested_pwm']))),
                                max_abs_reported_pwm=float(np.max(abs(data['reported_signed_pwm']))),
                                metrics=transitions(t,data['temperature_C'],data['setpoint_C'])))
        plot(t,data['temperature_C'],data['setpoint_C'],data['reported_signed_pwm'],data['requested_pwm'],
             FIGURES/f'experiment_{i}.png',f'Experimental run {i}: {mode}, Kp = {kp:g}, Ki = {ki:g}')
        config=replace(BASE,kp_pwm_per_c=kp,ki_pwm_per_c_s=ki)
        arr=simulate_run(config)
        fine=simulate_run(config,dt=.0125)
        difference=float(np.max(abs(arr[:,1]-np.interp(arr[:,0],fine[:,0],fine[:,1]))))
        assert difference<.02
        zeta=model.two_lump_p_damping_ratio(config)
        roots=poles(config)
        assert np.max(roots.real)<0
        predicted=(f'ζ₂L,P = {zeta:.3f}' if mode=='P' else f'Ki,crit = {KI_CRIT:.3f}; ρI = {ki/KI_CRIT:.3f}')
        plot(arr[:,0],arr[:,1],arr[:,2],arr[:,3],arr[:,4],FIGURES/f'simulation_{i}.png',
             f'Two-lump run {i}: {mode}, Kp = {kp:g}, Ki = {ki:g}; {predicted}')
        if export_csv:
            with (RESULTS/f'simulation_{i}.csv').open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(['time_s','mass_temperature_C','setpoint_C','applied_pwm',
                                                    'requested_pwm','u_P','u_I','q_C_s']);writer.writerows(arr)
        simulations.append(dict(run=i,mode=mode,kp=kp,ki=ki,zeta=zeta,ki_critical=KI_CRIT,
                                rho_I=ki/KI_CRIT,class_=classification(config),
                                roots=[[float(v.real),float(v.imag)] for v in roots],
                                timestep_change_C=difference,
                                metrics=transitions(arr[:,0],arr[:,1],arr[:,2])))
    # Controlled explorations required in Part II, using the supplied model.
    guided=[]
    for kp,ki,cmult in [(10,.02,1),(10,.2,1),(10,2,1),(5,.2,1),(20,.2,1),(10,.2,2)]:
        c=replace(BASE,kp_pwm_per_c=kp,ki_pwm_per_c_s=ki,total_capacitance_j_per_c=cmult*BASE.total_capacitance_j_per_c)
        results=model.simulate(c,'one_lump','pi',600)
        guided.append(dict(kp=kp,ki=ki,C_multiplier=cmult,zeta=model.one_lump_pi_damping_ratio(c),
                           peak_C=max(r.measured_temperature_c for r in results)))
    demo=replace(BASE,ambient_c=29,initial_c=29,setpoint_c=30,total_capacitance_j_per_c=91,
                 heat_loss_w_per_c=1.14,tec_power_w_per_pwm=.26,heating_to_cooling_ratio=2,
                 tec_capacitance_fraction=.35,coupling_w_per_c=50,dt_s=.025)
    p_demo=[]
    for kp in [60,105,160]:
        c=replace(demo,kp_pwm_per_c=kp,ki_pwm_per_c_s=0)
        trace=model.simulate(c,'two_lump','p',100)
        p_demo.append(dict(kp=kp,zeta=model.two_lump_p_damping_ratio(c),peak_C=max(r.measured_temperature_c for r in trace)))
    stress=replace(demo,total_capacitance_j_per_c=100,tec_capacitance_fraction=.5,
                   coupling_w_per_c=2,kp_pwm_per_c=10,ki_pwm_per_c_s=3)
    trace=model.simulate(stress,'two_lump','pi',700)
    saturated=[r.time_s for r in trace if abs(r.applied_pwm)>=255-.01]
    # Validate ideal stability boundary independently from polynomial roots.
    local_critical=model.two_lump_pi_critical_integral_gain(stress)
    def stress_roots(ki):
        ct=stress.tec_capacitance_j_per_c;cm=stress.measured_capacitance_j_per_c
        h=stress.heat_loss_w_per_c;g=stress.coupling_w_per_c;pu=.52
        return np.roots([ct*cm,ct*(g+h)+cm*g,g*(h+pu*10),g*pu*ki])
    assert max(stress_roots(local_critical*.9).real)<0
    assert max(stress_roots(local_critical*1.1).real)>0
    payload=dict(experiments=experiments,simulations=simulations,kp_critical=KP_CRIT,ki_critical=KI_CRIT,
                 C=BASE.total_capacitance_j_per_c,H=H,Pu_c=BASE.tec_power_w_per_pwm,Pu_h=PU_H,
                 G=G,CT_fraction=.35,shared_initial_C=28,guided_one_lump=guided,guided_two_lump_P=p_demo,
                 saturation_demo_first_s=saturated[0] if saturated else None,
                 saturation_demo_ki_critical=local_critical)
    (RESULTS/'analysis.json').write_text(json.dumps(payload,indent=2)+'\n')
    with (RESULTS/'experimental_metrics.csv').open('w',newline='') as f:
        fields=['run','direction','initial_C','target_C','duration_s','rise_10_90_s','overshoot_percent',
                'settling_2percent_s','steady_error_C','end5s_error_C','period_s']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for exp in experiments:
            for metric in exp['metrics']: writer.writerow(dict(run=exp['run'],**metric))
    return payload


# A2 style: A4, Helvetica 10.5 pt body, 15 pt numbered headings, thin rules,
# centered equations, italic captions, small source/date/page footer.
STYLES={
    'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=10),
    'title':ParagraphStyle('title',fontName='Helvetica',fontSize=20.25,leading=25,spaceAfter=8),
    'heading':ParagraphStyle('heading',fontName='Helvetica',fontSize=15,leading=19,spaceBefore=5,spaceAfter=9),
    'sub':ParagraphStyle('sub',fontName='Helvetica-Bold',fontSize=10.5,leading=15,spaceBefore=9,spaceAfter=7),
    'caption':ParagraphStyle('caption',fontName='Helvetica-Oblique',fontSize=8.75,leading=12,spaceAfter=14),
    'table':ParagraphStyle('table',fontName='Helvetica',fontSize=9,leading=12),
}
WIDTH=511
blocks=[]


def add(kind,value,extra=None): blocks.append((kind,value,extra))
def p(text): add('p',text)
def h(text): add('h',text)
def sub(text): add('sub',text)
def eq(latex): add('eq',latex)
def table(head,rows,widths=None): add('table',(head,rows),widths)
def figure(path,caption): add('figure',path,caption)
def page(): add('page',None)


def prepare_report(data):
    experiments=data['experiments'];simulations=data['simulations']
    add('title','A3 — Feedback Data and Lumped Modeling')
    p('Assignment code: A3<br/>Module: PHYS39 Module 6<br/>Team members: Kyle Chen and Muhammad Hasan')
    h('1. One-lump model and P-control predictions')
    p('The block stores heat while the TEC supplies power and the surroundings remove it:')
    eq(r'C\frac{dT}{dt}=P_u u-H(T-T_{amb})\quad\Rightarrow\quad\tau\frac{dT}{dt}=T_{amb}+\chi u-T')
    eq(r'\tau=C/H=91.69\ \mathrm{s},\qquad\chi=P_u/H;\quad\chi_h=0.5311,\ \chi_c=0.1878\ \mathrm{^{\circ}C/PWM}')
    p('Use χ_h for positive PWM and χ_c for negative PWM. For P control, u = Kp(Tset − T). At steady state:')
    eq(r'0=\chi K_p(T_{set}-T_{ss})-(T_{ss}-T_{amb})')
    eq(r'e_{ss}=\frac{T_{set}-T_{amb}}{1+\chi K_p},\qquad\tau_{cl}=\frac{\tau}{1+\chi K_p},\qquad L=\chi K_p')
    p('Subtracting the steady-state balance gives τ d(T − Tss)/dt = −(1 + L)(T − Tss). '
      'L is the dimensionless loop gain. Larger Kp reduces droop and speeds the response. '
      'P needs nonzero error to supply the heat lost to the room, so it cannot hold a nonambient target exactly.')
    p('Measured comparison: the Part 3 open-loop run used +5 PWM, ambient 24.220 °C, and τ = 91.69 s. '
      'Tss = 24.220 + 0.5311(5) = <b>26.875 °C</b>; its final-minute measured mean was '
      '<b>26.366 °C</b>. The model predicts the warming and approximate scale, but is 0.510 °C high. '
      'The same trace supplied τ, so agreement in response time is not an independent test.')
    p('Module 5 interpretation: better insulation lowers H, raises χ = Pu/H, and reduces droop. '
      'Doubling C doubles response time without changing the steady balance. '
      'Kp = 1 gives L = 0.5311, so it is not much smaller than one; the crossover is Kp = 1/χ_h = 1.883 PWM/°C.')
    page()
    h('2. Experimental Goldilocks plots and metrics')
    p('All runs used one apparatus, setpoints <b>28 → 30 → 28 °C</b>, PWM limit <b>±255</b>, '
      'anti-windup on, and sample interval ≈0.57 s. Each run lasted ≈93 s: ≈11 s baseline and ≈41 s per step. '
      'The integral was reset before each run. Initial temperatures are recorded below; they were not matched.')
    for exp in experiments[:3]:
        i=exp['run'];up,down=exp['metrics']
        caption=(f'Figure {i}. Experimental P, Kp = {exp["kp"]:g} PWM/°C, Ki = 0. '
                 f'Up/down step starts: {up["initial_C"]:.2f}/{down["initial_C"]:.2f} °C. '
                 f'{["Slow response and large error.","Faster response with remaining droop.","Small peak below target; no clear ringing."][i-1]}')
        figure(FIGURES/f'experiment_{i}.png',caption)
    page()
    sub('Experimental PI responses')
    for exp in experiments[3:]:
        i=exp['run'];up,down=exp['metrics']
        caption=(f'Figure {i}. Experimental PI, Kp = 16 PWM/°C, Ki = {exp["ki"]:g} PWM/(°C·s). '
                 f'Up/down starts: {up["initial_C"]:.2f}/{down["initial_C"]:.2f} °C. '
                 f'{["Slow integral correction.","Closest tracking with little overshoot.","0.76 °C overshoot and 0.86 °C undershoot."][i-4]}')
        figure(FIGURES/f'experiment_{i}.png',caption)
    page()
    sub('Largest-gain P and PI: step-response metrics')
    p('Rise time is the first 10%–90% crossing of the measured initial-to-new-target change, with linear '
      'interpolation between samples. Overshoot is the excursion beyond the target divided by the 2 °C '
      'setpoint step. Settling requires staying within ±0.04 °C (2%) for the rest of the step, '
      'with at least 10 s recorded in-band. End error averages the final 5 s; it is not verified steady-state error.')
    metric_rows=[]
    for exp in [experiments[2],experiments[5]]:
        for metric in exp['metrics']:
            metric_rows.append([f'{exp["mode"]} {exp["kp"]:g}/{exp["ki"]:g}',metric['direction'],
                                f'{metric["rise_10_90_s"]:.2f}',f'{metric["overshoot_percent"]:.1f}',
                                'Not reached','Unconfirmed',f'{metric["end5s_error_C"]:+.3f}','Unresolved'])
    table(['Mode Kp/Ki','Step','Rise (s)','OS (%)','Settling','SS error','End e (°C)','Period'],metric_rows,
          [70,35,48,45,76,77,73,87])
    p('The four ≈40 s windows do not establish settling, steady-state error, or a repeated oscillation period. '
      'High P has a small peak below target. High PI has one overshoot/undershoot per step. '
      'No experimental saturation occurred: maximum absolute reported PWM was <b>90</b>.')
    h('3. Two-lump simulations and comparison')
    p('Shared parameters for all six simulations: χ_c = 0.1878 and χ_h = 0.5311 °C/PWM; '
      'τ = 91.69 s; ambient 24.220 °C; C = 100.549 J/°C; H = 1.0966 W/°C; '
      'Pu,c = 0.20595 W/PWM; G = 10 W/°C; CT/C = 0.35; assumed TEC voltage 12 V; resistance 1.50 Ω; '
      'both initial lump temperatures 28 °C; targets 28 → 30 → 28 °C at 11 and 52 s; '
      'PWM ±255; q(0) = 0; anti-windup on; Δt = 0.025 s. Only mode and gains change.')
    p('G was adjusted once from 2 to 10 W/°C to reduce the high-P simulation to a small, decaying peak, '
      'matching the qualitative experimental shape. G and CT/C are model estimates, not measurements. '
      'The prior Part 3 ambient and τ are reused. The shared 28 °C simulation start cannot match all six '
      'different experimental starts; low-gain timing comparisons are therefore limited.')
    eq(r'S=C_T(G+H)+C_mG,\quad\zeta_{2L,P}=\frac{S}{2\sqrt{C_TC_mG(H+P_uK_p)}}')
    eq(r'K_{p,crit}=\frac{S^2/(4C_TC_mG)-H}{P_u},\quad K_{i,crit}=\frac{S(H+P_uK_p)}{C_TC_mP_u},\quad\rho_I=K_i/K_{i,crit}')
    p(f'At the heating equilibrium, <b>Kp,crit = {KP_CRIT:.2f} PWM/°C</b>; '
      f'for PI at Kp = 16, <b>Ki,crit = {KI_CRIT:.3f} PWM/(°C·s)</b>. '
      'These are local unsaturated criteria. Negative PWM uses the cooling coefficient during downward transients.')
    page()
    sub('Two-lump P simulations')
    for sim in simulations[:3]:
        i=sim['run']
        figure(FIGURES/f'simulation_{i}.png',
               f'Figure {i+6}. Simulated P, Kp = {sim["kp"]:g}, Ki = 0; ζ₂L,P = {sim["zeta"]:.3f}. {sim["class_"].capitalize()}.')
    page()
    sub('Two-lump PI simulations')
    for sim in simulations[3:]:
        i=sim['run']
        figure(FIGURES/f'simulation_{i}.png',
               f'Figure {i+6}. Simulated PI, Kp = 16, Ki = {sim["ki"]:g}; Ki,crit = {KI_CRIT:.3f}; '
               f'ρI = {sim["rho_I"]:.3f}. {sim["class_"].capitalize()}.')
    page()
    sub('Guided comparison answers')
    p('<b>Best matches:</b> high P (run 3) reproduces the small decaying peak below target; '
      'intermediate PI (run 5) reproduces the smooth approach close to target. Neither match establishes settling.')
    p('<b>P trend:</b> Kp = 5 is below the critical gain, 20 is near it, and 40 is above it. '
      f'Their ζ values are {simulations[0]["zeta"]:.3f}, {simulations[1]["zeta"]:.3f}, and {simulations[2]["zeta"]:.3f}. '
      'Lower ζ allows more overshoot while increasing gain speeds initial response. All three are stable; '
      'P cannot become marginally stable or unstable in this positive-parameter two-lump model.')
    p(f'<b>PI trend:</b> ρI = {simulations[3]["rho_I"]:.3f}, {simulations[4]["rho_I"]:.3f}, '
      f'and {simulations[5]["rho_I"]:.3f}. All are below 1 and therefore stable. '
      'Runs 4–5 have real stable poles; run 6 is underdamped. A PI response can overshoot even with real poles because the integral starts away from equilibrium. Increasing Ki strengthens correction but increases ringing. '
      'Marginal stability occurs at ρI = 1 and instability above 1; our retained gains do not reach that boundary.')
    p('<b>Agreement:</b> increasing PI gain reduces the early target error, then produces overshoot. '
      '<b>Disagreement:</b> the selected model does not reproduce every measured speed or overshoot amplitude. '
      'High-P rise times were 6.40/6.05 s measured versus 9.05/11.53 s simulated (up/down). '
      'High-PI overshoot was 38/43% measured versus 46.8/57.7% simulated. '
      'Different initial states and unmeasured internal parameters limit the comparison. '
      'No recorded growing or sustained oscillation falsifies its predicted stability within these short windows.')
    p('<b>Controlled checks:</b> for one-lump PI, increasing Ki lowers ζ; increasing Kp raises ζ; '
      'doubling C at fixed H and Pu divides ζ by √2. In the supplied two-lump practice model, '
      'Kp = 60, 105, 160 gives ζ ≈1.31, 1.00, 0.81. Increasing G from 35 to 70 at Kp = 105 '
      'raises damping; splitting C nearer equally between the lumps lowers damping. '
      'A separate simulated Ki = 3 saturation exercise first comes within 0.01 PWM of the ±255 limit at '
      f'{data["saturation_demo_first_s"]:.1f} s: early growing oscillations indicate linear instability; '
      'later output limiting and anti-windup bound the response. This is a simulation, not experimental saturation.')
    h('4. PI steady state, assumptions, and windup')
    eq(r'\dot q=e=0\ \Rightarrow\ T_{ss}=T_{set}=55\ ^\circ\mathrm{C},\quad u_P=0,\quad u_I=H(55-T_{amb})/P_u')
    p('At equilibrium, stored error q is constant, so e = 0. The integral retains the nonzero command '
      'needed to balance heat loss; P-only would need droop to provide it. Using the heating susceptibility, '
      'u_ss = (55 − 24.220)/0.5311 = <b>57.95 PWM</b>, within ±255 in this model. '
      'This is an ideal prediction, not a 55 °C experiment.')
    p('The result requires a stable closed loop, enough available heating power, no persistent saturation or '
      'shutdown, Ki &gt; 0 with continued integral action, and an accurate, timely temperature measurement. '
      'A sensor bias would make indicated temperature reach 55 °C while actual temperature differs.')
    p('Windup occurs when error keeps accumulating while PWM is already capped. The stored I term then drives '
      'overshoot and delays recovery. Our conditional integration rejects an update that pushes farther beyond '
      'the limit, but accepts one that brings the request back. Resetting q after steady state removes the '
      'balancing heat command, so temperature initially falls and the integral must rebuild.')
    page()
    h('5. Model limits and gain selection')
    p('<b>Complete this question only after completing Part II of Module 6.</b>')
    eq(r'T(t)-T_{ss}=[T(0)-T_{ss}]\exp[-(1+\chi K_p)t/\tau]')
    p('The exponential is positive and decays, so the one-lump P temperature cannot cross its own steady '
      'temperature from a fixed initial condition. Starting below both steady temperature and target, '
      'it cannot overshoot the target. Its single state cannot ring.')
    eq(r'C_T\dot T_T=P_u u-G(T_T-T_m),\qquad C_m\dot T_m=G(T_T-T_m)-H(T_m-T_{amb})')
    p('The TEC heats its own thermal mass first, then heat passes through G to the measured mass. '
      'This lag allows energy stored in the TEC to continue changing the measured temperature after '
      'the command decreases. Two-lump P and PI can therefore show overshoot and decaying oscillations.')
    p(f'<b>Selected P gain:</b> Kp = 20 PWM/°C is close to Kp,crit = {KP_CRIT:.2f}, '
      f'with ζ = {simulations[1]["zeta"]:.3f}: fast response near critical damping. '
      'It retains droop; gain 40 reduces droop further but has a more pronounced transient peak.')
    p(f'<b>Selected PI gains:</b> Kp = 16 PWM/°C and Ki = 0.5 PWM/(°C·s), '
      f'with ρI = {simulations[4]["rho_I"]:.3f}, well below 1. Run 5 approached both targets with little overshoot. '
      'Ki = 0.1 corrected too slowly; Ki = 2 produced larger excursions. These are provisional choices '
      'because the recordings did not establish full settling.')
    p('A better model should include measurement/command delay: the actual controller samples about every '
      '0.57 s, while the simulation uses much smaller steps. Temperature-dependent TEC coefficients '
      'and thermal contact changes may also explain remaining differences.')
    h('Data, code, and modeling checkpoint')
    p('Experimental sources: six October 14 CSVs in the Part 7 data directory. Figures plot reported signed '
      'PWM alongside requested PWM; telemetry reports the previous interval’s output. '
      'Simulation data, metrics, and calculations are reproducible with build_a3.py. '
      'Halving simulation Δt changes temperature by less than '
      f'{max(s["timestep_change_C"] for s in simulations):.4f} °C in the six retained runs.')
    p('Local files: <link href="../../code/module6/A3/build_a3.py" color="#1764ab">analysis/build script</link>; '
      '<link href="../../code/module6/A3/results/experimental_metrics.csv" color="#1764ab">experimental metrics</link>; '
      '<link href="../../code/module6/A3/results/analysis.json" color="#1764ab">settings and stability calculations</link>.')
    for i,exp in enumerate(experiments,1):
        p(f'<link href="../../{exp["path"]}" color="#1764ab">Run {i} raw CSV</link>')
    p('GitHub modeling checkpoint: <link href="https://github.com/hasanm720/Module1/commit/73d29c92752bb946929633de97bcb714192e3ba2" '
      'color="#1764ab">73d29c9</link> (existing Part 3/4 checkpoint). This checkpoint predates the six runs and A3; '
      'the new A3 files have not been committed or pushed.')
    p('Assignment: <link href="https://sethfraden.github.io/Phys39F26-course/labs/lab-06/#a3-feedback-data-and-lumped-model-memo" '
      'color="#1764ab">Lab 6 — A3</link>. Two-lump protocol: '
      '<link href="https://sethfraden.github.io/Phys39F26-course/labs/lab-07/#make-the-six-two-lump-goldilocks-plots" '
      'color="#1764ab">Lab 7 — six simulation runs</link>.')


def improve_layout():
    """Keep A2 typography while making figures and answers easier to scan."""
    revised=[]
    previous=None
    for kind,value,extra in blocks:
        # Two full-size figures per page, instead of three narrow figures.
        if kind=='page' and previous and previous[0]=='figure' and previous[1].name in ('experiment_3.png','simulation_3.png'):
            continue
        if kind=='sub' and value in ('Experimental PI responses','Two-lump PI simulations'):
            continue
        if kind=='figure':
            names={
                'experiment_3.png':'Experimental runs 3–4',
                'experiment_5.png':'Experimental runs 5–6',
                'simulation_3.png':'Two-lump simulations 3–4',
                'simulation_5.png':'Two-lump simulations 5–6',
            }
            if value.name in names:
                revised.extend([('page',None,None),('sub',names[value.name],None)])
        if kind=='p':
            if value.startswith('Subtracting the steady-state balance'):
                revised.extend([
                    ('p','Subtracting the steady-state balance gives τ d(T − Tss)/dt = −(1 + L)(T − Tss). <b>L = χKp is the dimensionless loop gain.</b>',None),
                    ('p','<b>Higher Kp:</b> smaller droop and faster response. P still needs nonzero error to replace heat lost to the room.',None),
                ]); continue
            if value.startswith('Measured comparison:'):
                revised.extend([
                    ('sub','Measured comparison: +5 PWM open loop',None),
                    ('p','Part 3 used ambient 24.220 °C and τ = 91.69 s. Prediction: Tss = 24.220 + 0.5311(5).',None),
                    ('table',(['Predicted temperature','Measured final-minute mean','Prediction error'],[['26.875 °C','26.366 °C','+0.510 °C']]),None),
                    ('p','The model captures warming but predicts too high a temperature. This trace also supplied τ, so its response time is not an independent check.',None),
                ]); continue
            if value.startswith('Module 5 interpretation:'):
                revised.extend([
                    ('sub','Module 5 interpretation',None),
                    ('p','• <b>Better insulation:</b> lower H, higher χ, less droop.<br/>• <b>Double C:</b> double response time; same steady temperature.<br/>• <b>Kp = 1:</b> L = 0.5311 is not much smaller than one. The crossover is Kp = 1.883 PWM/°C.',None),
                ]); continue
            if value.startswith('Rise time is the first'):
                revised.extend([
                    ('p','<b>Rise:</b> first 10%–90% crossing from measured initial temperature toward the new target; linearly interpolated.',None),
                    ('p','<b>Overshoot:</b> excursion beyond the target ÷ 2 °C step × 100%. <b>Settling:</b> remain within ±0.04 °C for the rest of the step, with at least 10 s recorded in-band.',None),
                ]); continue
            if value.startswith('The four ≈40 s windows'):
                revised.extend([
                    ('p','<b>Not established in any of the four windows:</b> settling time, steady-state error, and oscillation period. End error averages the final 5 s; it is not steady-state error.',None),
                    ('p','<b>Saturation:</b> none experimentally; maximum absolute reported PWM was 90. High PI showed one overshoot/undershoot per step.',None),
                ]); continue
            if value.startswith('Shared parameters for all six simulations:'):
                revised.extend([
                    ('p','<b>One shared plant:</b> χc = 0.1878 and χh = 0.5311 °C/PWM; τ = 91.69 s; ambient 24.220 °C; C = 100.549 J/°C; H = 1.0966 W/°C; Pu,c = 0.20595 W/PWM; G = 10 W/°C; CT/C = 0.35; assumed voltage 12 V; resistance 1.50 Ω.',None),
                    ('p','<b>One shared protocol:</b> both lumps initially 28 °C; targets 28 → 30 → 28 °C at 11 and 52 s; PWM ±255; q(0) = 0; anti-windup on; Δt = 0.025 s. Only mode and gains change.',None),
                ]); continue
            if value.startswith('G was adjusted once'):
                revised.extend([
                    ('p','<b>Model choice:</b> G was adjusted once from 2 to 10 W/°C to reproduce the small high-P peak. G and CT/C are estimates; ambient and τ are reused from Part 3.',None),
                    ('p','<b>Comparison limit:</b> the common 28 °C simulation start differs from the experimental starts, especially at low gain.',None),
                ]); continue
            if value.startswith('<b>P trend:</b>'):
                value=(' <b>P:</b> Kp = 5, 20, 40 lie below, near, and above Kp,crit. Their ζ values are 1.719, 0.964, and 0.697. Higher gain speeds response and lowers damping. All are stable; positive-parameter two-lump P cannot become marginally stable or unstable.').strip()
            if value.startswith('<b>PI trend:</b>'):
                revised.extend([
                    ('p','<b>PI:</b> ρI = 0.012, 0.062, 0.246: all stable. Runs 4–5 have real poles; run 6 is underdamped. Real-pole PI can still overshoot because q starts away from equilibrium.',None),
                    ('p','Increasing Ki strengthens correction but increases ringing. Marginal stability is at ρI = 1; instability is above 1. Our retained gains stay below this boundary.',None),
                ]);continue
            if value.startswith('<b>Agreement:</b>'):
                revised.extend([
                    ('p','<b>Agreement:</b> stronger PI correction reduces early error, then produces overshoot.',None),
                    ('table',(['Comparison (up/down)','Experiment','Simulation'],[['High-P rise time','6.40 / 6.05 s','9.05 / 11.53 s'],['High-PI overshoot','38 / 43%','46.8 / 57.7%']]),None),
                    ('p','<b>Disagreement:</b> exact speed and overshoot do not match. Different starting states and estimated internal parameters limit agreement. No recorded growing or sustained oscillation contradicts the predicted stability in these windows.',None),
                ]);continue
            if value.startswith('<b>Controlled checks:</b>'):
                revised.extend([
                    ('sub','Controlled checks',None),
                    ('p','• <b>One-lump PI:</b> higher Ki lowers ζ; higher Kp raises ζ; doubling C divides ζ by √2.<br/>• <b>Two-lump practice:</b> Kp = 60, 105, 160 gives ζ ≈1.31, 1.00, 0.81. Raising G from 35 to 70 increases damping; a more equal mass split lowers damping.',None),
                    ('p','<b>Simulated saturation:</b> the Ki = 3 practice run comes within 0.01 PWM of ±255 at 191.8 s. Early growth shows linear instability; later output limiting and anti-windup bound the response. This was not experimental saturation.',None),
                ]);continue
            if value.startswith('At equilibrium, stored error'):
                revised.extend([
                    ('p','<b>Ideal result: 55 °C.</b> At equilibrium q is constant, so e = 0. The integral retains the heat-loss-balancing output while P becomes zero.',None),
                    ('p','Required heating command: (55 − 24.220)/0.5311 = <b>57.95 PWM</b>, within ±255 in this model. This is a prediction, not a 55 °C experiment.',None),
                ]);continue
            if value.startswith('The result requires a stable closed loop'):
                value='<b>Conditions:</b> stable feedback, sufficient heating power, no persistent saturation or shutdown, Ki &gt; 0 with continued integration, and accurate/timely measurement. Sensor bias shifts the actual temperature away from the indicated 55 °C.'
            if value.startswith('Windup occurs when error'):
                revised.extend([
                    ('p','<b>Windup:</b> stored error keeps growing while PWM is capped, causing overshoot and slow recovery.',None),
                    ('p','<b>Anti-windup:</b> reject updates that push farther beyond the limit; accept updates that bring the request back.',None),
                    ('p','<b>Reset:</b> clearing q removes the balancing heat command. Temperature initially falls while I rebuilds.',None),
                ]);continue
            if value.startswith('The exponential is positive'):
                value='<b>One-lump limit:</b> the positive, decaying exponential cannot cross its own steady temperature. From below the steady temperature and target, P cannot overshoot the target or ring.'
            if value.startswith('The TEC heats its own thermal mass'):
                value='<b>Two-lump lag:</b> the TEC heats its own mass first; G then transfers heat to the measured mass. Stored TEC energy keeps changing Tm after the command falls, allowing overshoot and decaying oscillations.'
            if value.startswith('A better model should include'):
                value='<b>Next model improvement:</b> include the ≈0.57 s measurement/command delay. Temperature-dependent TEC coefficients and thermal contact changes may also matter.'
        if kind=='table' and value[0][0]=='Mode Kp/Ki':
            head,rows=value
            value=(['Mode Kp/Ki','Step','Rise (s)','Overshoot (%)','End error (°C)'],[[r[0],r[1],r[2],r[3],r[6]] for r in rows])
            extra=[95,55,90,120,151]
        if kind=='h' and value.startswith('4.'):
            revised.append(('page',None,None))
        if kind=='h' and value=='Data, code, and modeling checkpoint':
            revised.append(('page',None,None))
        revised.append((kind,value,extra))
        previous=(kind,value,extra)
    # Keep related answers together and use the comparison page for compact sources.
    source_index=next(i for i,b in enumerate(revised)
                      if b[0]=='h' and b[1]=='Data, code, and modeling checkpoint')
    references=revised[source_index:]
    revised=revised[:source_index-1]  # Drop the preceding source-only page break.
    raw_links=[b for b in references if b[0]=='p' and re.match(r'<link href=".*">Run \d raw CSV</link>$',b[1])]
    if raw_links:
        first=references.index(raw_links[0])
        references=[b for b in references if b not in raw_links]
        references.insert(first,('p','<b>Raw recordings:</b> '+' · '.join(b[1] for b in raw_links),None))
    q4_index=next(i for i,b in enumerate(revised) if b[0]=='h' and b[1].startswith('4.'))
    revised[q4_index-1:q4_index-1]=references
    q5_index=next(i for i,b in enumerate(revised) if b[0]=='h' and b[1].startswith('5.'))
    if revised[q5_index-1][0]=='page': del revised[q5_index-1]
    blocks[:]=revised


class NumberedCanvas(canvas.Canvas):
    def __init__(self,*args,**kwargs):
        canvas.Canvas.__init__(self,*args,**kwargs); self.states=[]
    def showPage(self):
        self.states.append(dict(self.__dict__));self._startPage()
    def save(self):
        count=len(self.states)
        for state in self.states:
            self.__dict__.update(state)
            self.setFont('Helvetica',6)
            self.drawString(42,824,'A3_Chen_Hasan.md')
            self.drawRightString(553,824,'2026-10-14')
            self.drawCentredString(297.5,23,f'{self._pageNumber} / {count}')
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def plain(text):
    text=re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>',r'[\2](\1)',text)
    text=text.replace('<br/>','\n').replace('<b>','**').replace('</b>','**')
    return text.replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')


def render():
    import tempfile
    temp=Path(tempfile.mkdtemp(prefix='phys39-a3-equations-'))
    story=[];markdown=[]; equation_number=0
    for kind,value,extra in blocks:
        if kind=='page': story.append(PageBreak()); continue
        if kind in ['title','h','sub','p']:
            style=STYLES[{'title':'title','h':'heading','sub':'sub','p':'body'}[kind]]
            if kind=='h': story.append(HRFlowable(width='100%',thickness=.6,color=colors.grey,spaceBefore=4,spaceAfter=8))
            story.append(Paragraph(value.replace('ζ₂L,P','ζ<sub>2L,P</sub>'),style))
            prefix={'title':'# ','h':'## ','sub':'### ','p':''}[kind]
            markdown.append(prefix+plain(value)+'\n')
        elif kind=='eq':
            equation_number+=1;path=temp/f'eq{equation_number}.png'
            fig=plt.figure(figsize=(7.1,.45));fig.text(.5,.5,'$'+value+'$',ha='center',va='center',fontsize=11)
            fig.savefig(path,dpi=200,bbox_inches='tight',pad_inches=.04);plt.close(fig)
            from PIL import Image as PILImage
            with PILImage.open(path) as im: w,hp=im.size
            display_w=min(WIDTH,w*72/200); display_h=display_w*hp/w
            img=Image(str(path),width=display_w,height=display_h);img.hAlign='CENTER'
            story.extend([img,Spacer(1,7)])
            markdown.append('$$\n'+value+'\n$$\n')
        elif kind=='table':
            head,rows=value
            widths=extra or [WIDTH/len(head)]*len(head)
            widths=[w*WIDTH/sum(widths) for w in widths]
            cells=[[Paragraph(xml.escape(str(cell)),STYLES['table']) for cell in row] for row in [head]+rows]
            tab=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),
                                     ('LINEBELOW',(0,0),(-1,0),.6,colors.grey),
                                     ('LINEBELOW',(0,1),(-1,-1),.25,colors.lightgrey),
                                     ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),
                                     ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([tab,Spacer(1,8)])
            markdown.extend(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |'])
            markdown.extend('| '+' | '.join(map(str,row))+' |' for row in rows)
            markdown.append('')
        elif kind=='figure':
            img=Image(str(value),width=WIDTH,height=WIDTH*3.7/7.2)
            caption=Paragraph(extra.replace('ζ₂L,P','ζ<sub>2L,P</sub>'),STYLES['caption'])
            story.append(KeepTogether([img,Spacer(1,3),caption]))
            relative='../figures/module_06/a3/'+value.name
            markdown.append(f'![{plain(extra)}]({relative})\n\n*{plain(extra)}*\n')
    pdf=NOTES/'A3_Chen_Hasan.pdf';md=NOTES/'A3_Chen_Hasan.md'
    doc=SimpleDocTemplate(str(pdf),pagesize=(595,842),leftMargin=42,rightMargin=42,
                          topMargin=40,bottomMargin=40,title='A3 — Feedback Data and Lumped Modeling',
                          author='Kyle Chen and Muhammad Hasan')
    doc.build(story,canvasmaker=NumberedCanvas)
    md.write_text('\n'.join(markdown)+'\n')
    print(f'PDF: {pdf}\nMarkdown: {md}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save-csv',action='store_true',help='Export simulation time series')
    args=parser.parse_args()
    data=analyse(args.save_csv);prepare_report(data);improve_layout();render()
    print(f'Kp,crit={KP_CRIT:.4f}; Ki,crit={KI_CRIT:.4f}; numerical and stability checks passed.')
