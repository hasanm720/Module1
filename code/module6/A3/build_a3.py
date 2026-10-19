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
P4 = ROOT/'code/module6/Part_I/P4_Simulate_open_loop_control'
P7 = ROOT/'code/module6/Part_I/P7_experimental_goldilocks'
sys.path.insert(0,str(P4))
from run_part4 import measured_config
import Lab_6_7_modeling_tec as model

BASE=replace(measured_config(.1878,.5311,91.69,12,24.220,28),
             coupling_w_per_c=2,tec_capacitance_fraction=.35,dt_s=.01,pwm_limit=255)
PU_H=BASE.tec_power_w_per_pwm*BASE.heating_to_cooling_ratio
CT=BASE.tec_capacitance_j_per_c; CM=BASE.measured_capacitance_j_per_c
G=BASE.coupling_w_per_c; H=BASE.heat_loss_w_per_c
S=CT*(G+H)+CM*G
KP_CRIT=(S*S/(4*CT*CM*G)-H)/PU_H


def read(path):
    with path.open() as stream: rows=list(csv.DictReader(stream))
    keys=['arduino_s','temperature_C','setpoint_C','reported_signed_pwm','applied_pwm',
          'requested_pwm','u_P','u_I','dt_s']
    return {key:np.array([float(r[key]) for r in rows]) for key in keys},rows


def oscillation_period(t,values):
    # Confirm alternating extrema only after a 0.20 C reversal; avoid quantization peaks.
    peaks=[]; direction=1; high=low=float(values[0]); high_t=float(t[0])
    for time,value in zip(t[1:],values[1:]):
        if direction==1:
            if value>high: high=float(value); high_t=float(time)
            if high-value>=.20:
                peaks.append(high_t);direction=-1;low=float(value)
        else:
            low=min(low,float(value))
            if value-low>=.20: direction=1;high=float(value);high_t=float(time)
    return float(np.median(np.diff(peaks))) if len(peaks)>=3 else None


def transitions(t,temp,target):
    edges=np.flatnonzero(np.diff(target)!=0)+1
    output=[]
    for a,b in zip(edges,list(edges[1:])+[len(t)]):
        tt=t[a:b]-t[a]; values=temp[a:b]; initial=float(temp[a-1]);goal=float(target[a])
        change=goal-initial; progress=(values-initial)/change
        crossings=[]
        for threshold in [.1,.9]:
            hits=np.flatnonzero(progress>=threshold)
            if not len(hits):crossings.append(None);continue
            j=int(hits[0])
            if j==0:crossings.append(float(tt[0]));continue
            fraction=(threshold-progress[j-1])/(progress[j]-progress[j-1])
            crossings.append(float(tt[j-1]+fraction*(tt[j]-tt[j-1])))
        rise=None if any(x is None for x in crossings) else crossings[1]-crossings[0]
        amplitude=abs(goal-float(target[a-1]));direction=1 if goal>target[a-1] else -1
        overshoot=max(0,float(np.max(direction*(values-goal))))/amplitude*100
        end_mean=float(np.mean(values[tt>=tt[-1]-5]))
        outside=np.flatnonzero(abs(values-goal)>.02*amplitude)
        candidate=0 if len(outside)==0 else int(outside[-1])+1
        settling=float(tt[candidate]) if candidate<len(tt) and tt[-1]-tt[candidate]>=10 else None
        output.append(dict(direction='Up' if direction>0 else 'Down',initial_C=initial,target_C=goal,
            duration_s=float(tt[-1]),rise_10_90_s=rise,overshoot_percent=overshoot,
            settling_2percent_s=settling,steady_error_C=None,end5s_error_C=goal-end_mean,
            period_s=oscillation_period(tt,values)))
    return output


def simulate_run(config,dt=None,duration=93):
    c=replace(config,dt_s=dt or config.dt_s)
    state=model.ModelState(0,c.initial_c,c.initial_c,0);records=[]
    for _ in range(round(duration/c.dt_s)):
        target=28 if state.time_s<11-1e-8 or state.time_s>=52-1e-8 else 30
        active=replace(c,setpoint_c=target);before=state.measured_temperature_c
        result=model.advance_model(state,active,'two_lump','pi' if c.ki_pwm_per_c_s else 'p')
        records.append([state.time_s-c.dt_s,before,target,result.applied_pwm,
                        result.p_pwm+result.i_pwm,result.p_pwm,result.i_pwm,state.integral_error_c_s])
    return np.array(records)


def poles(config,pu=PU_H):
    kp=config.kp_pwm_per_c;ki=config.ki_pwm_per_c_s
    coeff=[CT*CM,S,G*(H+pu*kp)]
    if ki:coeff.append(G*pu*ki)
    return np.roots(coeff)


def classification(config):
    roots=poles(config)
    if np.max(roots.real)>1e-7:return 'unstable'
    if np.max(roots.real)>=-1e-7:return 'marginally stable'
    return 'stable underdamped' if np.max(abs(roots.imag))>1e-7 else 'stable non-oscillatory'


def plot(t,temp,target,pwm,requested,path,title):
    fig,axes=plt.subplots(2,1,figsize=(7.2,3.7),sharex=True,gridspec_kw={'height_ratios':[1.4,1]})
    axes[0].plot(t,temp,color='#1764ab',lw=1.3,label='Temperature')
    axes[0].step(t,target,where='post',color='#d45d00',ls='--',lw=1,label='Setpoint')
    axes[1].plot(t,pwm,color='#1764ab',lw=1.1,label='Signed applied PWM')
    for boundary in (-255,255):axes[1].axhline(boundary,color='gray',ls='--',lw=.6)
    axes[0].set_ylim(19,33);axes[1].set_ylim(-270,270);axes[1].set_yticks([-255,0,255])
    axes[0].set_ylabel('Temperature (°C)',fontsize=9);axes[1].set_ylabel('Signed PWM',fontsize=9)
    axes[1].set_xlabel('Elapsed time (s)',fontsize=9)
    for ax in axes:
        ax.set_xlim(0,95);ax.tick_params(labelsize=8);ax.grid(alpha=.18)
        ax.legend(loc='upper right',fontsize=7,ncol=2)
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    fig.suptitle(title,fontsize=9.5,y=.98)
    fig.subplots_adjust(left=.105,right=.985,top=.89,bottom=.13,hspace=.18)
    fig.savefig(path,dpi=180);plt.close(fig)


def analyse(export_csv=False):
    FIGURES.mkdir(parents=True,exist_ok=True);RESULTS.mkdir(exist_ok=True)
    paths=[P7/'data'/Path(f).name for f in json.loads((P7/'data/screening_selected_logs.json').read_text())]
    experiments=[];simulations=[]
    for i,path in enumerate(paths,1):
        data,rows=read(path);t=data['arduino_s']-data['arduino_s'][0]
        kp=float(rows[0]['kp_pwm_per_C']);ki=float(rows[0]['ki_pwm_per_C_s']);mode='PI' if ki else 'P'
        assert all(r['safety']=='OK' and int(r['run'])==i for r in rows)
        assert len({(r['kp_pwm_per_C'],r['ki_pwm_per_C_s']) for r in rows})==1
        assert np.max(abs(data['applied_pwm']))<=255 and np.max(abs(data['reported_signed_pwm']))<=255
        assert len(np.flatnonzero(np.diff(data['setpoint_C'])!=0))==2
        experiments.append(dict(run=i,path=str(path.relative_to(ROOT)),mode=mode,kp=kp,ki=ki,
            initial_C=float(data['temperature_C'][0]),dt_median_s=float(np.median(data['dt_s'])),
            saturated_samples=int(np.sum(abs(data['applied_pwm'])==255)),samples=len(rows),
            metrics=transitions(t,data['temperature_C'],data['setpoint_C'])))
        plot(t,data['temperature_C'],data['setpoint_C'],data['applied_pwm'],data['requested_pwm'],
             FIGURES/f'experiment_{i}.png',f'Experimental run {i}: {mode}, Kp = {kp:g}, Ki = {ki:g}')
        config=replace(BASE,kp_pwm_per_c=kp,ki_pwm_per_c_s=ki)
        arr=simulate_run(config);fine=simulate_run(config,dt=.005)
        difference=float(np.max(abs(arr[:,1]-np.interp(arr[:,0],fine[:,0],fine[:,1]))))
        assert difference<.05
        critical=model.two_lump_pi_critical_integral_gain(config)
        zeta=model.two_lump_p_damping_ratio(config)
        predicted=f'zeta = {zeta:.3f}' if not ki else f'Ki,crit = {critical:.3f}; rhoI = {ki/critical:.3f}'
        plot(arr[:,0],arr[:,1],arr[:,2],arr[:,3],arr[:,4],FIGURES/f'simulation_{i}.png',
             f'Two-lump run {i}: Kp = {kp:g}, Ki = {ki:g}; {predicted}')
        if export_csv:
            with (RESULTS/f'simulation_{i}.csv').open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['time_s','mass_temperature_C','setpoint_C','applied_pwm',
                    'requested_pwm','u_P','u_I','q_C_s']);w.writerows(arr)
        simulations.append(dict(run=i,kp=kp,ki=ki,mode=mode,zeta=zeta,ki_critical=critical,
            rho_I=ki/critical,class_=classification(config),
            roots=[[float(v.real),float(v.imag)] for v in poles(config)],
            timestep_change_C=difference,saturated_samples=int(np.sum(abs(arr[:,3])==255)),
            metrics=transitions(arr[:,0],arr[:,1],arr[:,2])))
    payload=dict(experiments=experiments,simulations=simulations,kp_critical=KP_CRIT,
        C=BASE.total_capacitance_j_per_c,H=H,Pu_c=BASE.tec_power_w_per_pwm,Pu_h=PU_H,
        G=G,CT_fraction=.35,shared_initial_C=28)
    (RESULTS/'analysis.json').write_text(json.dumps(payload,indent=2)+'\n')
    with (RESULTS/'experimental_metrics.csv').open('w',newline='') as f:
        fields=['run',*experiments[0]['metrics'][0]];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for exp in experiments:
            for metric in exp['metrics']:w.writerow(dict(run=exp['run'],**metric))
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
    def fmt(value, digits=2): return 'Not established' if value is None else f'{value:.{digits}f}'
    add('title','A3 — Feedback Data and Lumped Modeling')
    p('PHYS 39 · Module 6 · Kyle Chen and Muhammad Hasan · October 19, 2026')
    h('1. One-lump model and P-control predictions')
    p('The First Law gives storage = TEC heat input − heat loss to the room. With C = mc_p, constant thermal properties, and signed applied command u:')
    eq(r'C\frac{dT}{dt}=P_u u-H(T-T_{amb})')
    p('C is in J/K, Pu in W/PWM, and H in W/K; each term has units W. At constant command, the steady balance gives Tss = Tamb + (Pu/H)u. Comparing with measured susceptibility identifies χ = Pu/H. Subtracting steady state gives C d(T − Tss)/dt = −H(T − Tss), so τ = C/H.')
    eq(r'\frac{dT}{dt}=\frac{T_{amb}+\chi u-T}{\tau},\qquad\tau=91.69\ \mathrm{s}')
    p('Measured χh = 0.5311 and χc = 0.1878 °C/PWM. Heating and cooling coefficients differ because resistive heating aids heating and opposes cooling. The 63% heating crossing estimates τ to about one 0.57 s sampling interval; ambient drift and incomplete settling add unquantified uncertainty.')
    p('Substitute P control u = Kp(Tset − T). At steady state, (1 + χKp)Tss = Tamb + χKpTset. Subtract the steady balance to obtain the transient:')
    eq(r'e_{ss}=\frac{T_{set}-T_{amb}}{1+\chi K_p},\quad L=\chi K_p,\quad\tau_{cl}=\frac{\tau}{1+L}')
    p('L is dimensionless. Increasing Kp reduces both droop and response time by 1 + L. P requires nonzero error to replace heat lost to the room. At Kp = 10 and target 30 °C, the saved baseline predicts droop 0.916 °C and τcl = 14.53 s.')
    p('<b>Measured check:</b> for +5 PWM and Tamb = 24.220 °C, predicted Tss = 26.875 °C versus a measured final-minute mean of 26.366 °C. Warming and approximate scale agree; the 0.510 °C discrepancy exposes model/calibration limits. The same trace supplied τ, so timing agreement is not independent evidence.')
    p('<b>Module 5 interpretation:</b> insulation lowers H and droop; doubling C slows the transient without changing the steady balance. Kp = 1 gives L = 0.5311, not much smaller than one; L = 1 at Kp = 1.883 PWM/°C. Module 5 gain 20 approximately settled at 29.386 °C (droop 0.614 °C), while higher gains showed increasingly ambiguous or recurring waves. Different ambient conditions limit quantitative cross-day comparisons.')
    page()
    h('2. Experimental Goldilocks plots and metrics')
    p('Six recorded runs use the same apparatus, 28 → 30 → 28 °C setpoints, PWM limit ±255, anti-windup, and ≈0.57 s sampling. Each has about 10 s baseline and 40 s per step. The integral was reset before each run. Runs 3 and 6 are the October 19 Kp = 1000 reruns; the others are October 14 recordings.')
    p('<b>Protocol limitation:</b> starting temperatures differ, and selected PI gains are 16/0.1, 16/0.5, and 1000/2 (Kp/Ki). Thus Run 6 does not isolate increasing Ki at fixed Kp. We preserve and disclose the actual recordings rather than presenting them as a matched Ki sweep.')
    for exp in experiments:
        i=exp['run']
        if i in (3,5):page()
        figure(FIGURES/f'experiment_{i}.png',
            f'Figure {i}. Experimental {exp["mode"]}: Kp = {exp["kp"]:g} PWM/°C; Ki = {exp["ki"]:g} PWM/(°C·s). '
            f'Initial T = {exp["initial_C"]:.2f} °C; {exp["saturated_samples"]}/{exp["samples"]} applied commands at ±255. '
            'Only actual applied PWM is shown; controller requests are not PWM output.')
    page()
    sub('Largest-gain P and PI: both step directions')
    p('Rise time is the first 10%–90% crossing from the last pre-step measured temperature toward the new target, interpolated between samples. Overshoot is excursion beyond the target divided by the commanded 2 °C step. Settling requires remaining within ±0.04 °C through the end of the step, with at least 10 s observed in-band.')
    rows=[]
    for exp in (experiments[2],experiments[5]):
        for m in exp['metrics']:
            rows.append([f'{exp["mode"]} {exp["kp"]:g}/{exp["ki"]:g}',m['direction'],fmt(m['rise_10_90_s']),
                         fmt(m['overshoot_percent'],1),fmt(m['period_s']),fmt(m['end5s_error_C'],3)])
    table(['Mode Kp/Ki','Step','Rise (s)','Overshoot (%)','Period (s)','End error (°C)'],rows,
          [95,40,70,95,85,100])
    p('For all four high-gain steps, settling time and steady-state error are <b>not established</b>. End error is target minus the final 5 s mean, not steady-state error. The 0.54 s PI upward rise spans approximately one sample interval and is poorly resolved. Period is the median peak-to-peak spacing, requiring at least three peaks confirmed by reversals ≥0.20 °C; sampling limits timing resolution to roughly 0.57 s.')
    p('Both high-gain recordings have recurring, bounded oscillations over the observed window. This is consistent with a nonlinear limit cycle, but does not prove ideal marginal stability or long-term boundedness. P run 3 reaches 31.43 °C / 27.30 °C on the up/down steps; PI run 6 reaches 31.32 °C / 27.27 °C. Applied PWM saturates on 133/163 and 132/164 samples, respectively.')
    page()
    h('3. Two-lump simulation and experiment comparison')
    p('One shared physical parameter set for all six simulations: χc = 0.1878 and χh = 0.5311 °C/PWM; τ = 91.69 s; Tamb = 24.220 °C; C = 100.549 J/K; H = 1.0966 W/K; Pu,c = 0.20595 W/PWM; r = 2.8280; G = 2 W/K; CT/C = 0.35; TEC voltage 12 V (assumed ON-state value), resistance 1.50 Ω; both masses initially 28 °C; targets 28 → 30 → 28 °C at 11 and 52 s; PWM ±255; q(0) = 0; anti-windup on; Δt = 0.01 s.')
    p('G and CT/C are unresolved internal estimates, retained at the assignment starting values. The high-P model reproduces overshoot and decay qualitatively, but cannot reproduce the measured persistent wave train. Exact fitting is not claimed. All simulations keep the same initial state as required; their 28 °C start differs from the recorded starts, and the common switching times differ slightly from individual host-timed experiments.')
    eq(r'C_T\dot T=P_u u-G(T-T_m),\qquad C_m\dot T_m=G(T-T_m)-H(T_m-T_{amb})')
    p('The controller measures Tm. With perturbations θT and θm about equilibrium and unsaturated P feedback, GθT = Cm dθm/dt + (G + H)θm. Differentiate this expression and substitute the TEC balance to eliminate θT:')
    eq(r'C_TC_m\ddot\theta_m+S\dot\theta_m+G(H+P_uK_p)\theta_m=0,\quad S=C_T(G+H)+C_mG')
    eq(r'\zeta_{2L,P}=\frac{S}{2\sqrt{C_TC_mG(H+P_uK_p)}},\quad K_{p,crit}=\frac{S^2/(4C_TC_mG)-H}{P_u}')
    p(f'For this shared plant, heating-direction Kp,crit = <b>{KP_CRIT:.3f} PWM/°C</b>. The three gains 5, 20, and 1000 are all above it, with progressively smaller damping. This shared model therefore does not reproduce a monotonic low-gain-to-critical-to-underdamped progression for these selected experimental gains.')
    eq(r'C_TC_m s^3+S s^2+G(H+P_uK_p)s+GP_uK_i=0')
    p('For positive coefficients, Routh–Hurwitz requires S·G(H + PuKp) > CT·Cm·G·Pu·Ki. This yields:')
    eq(r'K_{i,crit}=\frac{S(H+P_uK_p)}{C_TC_mP_u},\qquad\rho_I=K_i/K_{i,crit}')
    p('The unsaturated local PI model is stable for 0 < ρI < 1, marginal at ρI = 1, and unstable for ρI > 1. These heating-equilibrium classifications do not describe actuator clipping or the complete heating/cooling switching transient.')
    page()
    sub('Six simulations using the same plant and protocol')
    for sim in simulations:
        i=sim['run']
        if i in (3,5):page()
        if not sim['ki']:
            detail=f'ζ₂L,P = {sim["zeta"]:.3f}'
        else:
            detail=f'Ki,crit = {sim["ki_critical"]:.3f}; ρI = {sim["rho_I"]:.3f}'
        figure(FIGURES/f'simulation_{i}.png',
            f'Figure {i+6}. Two-lump {sim["mode"]}: Kp = {sim["kp"]:g}, Ki = {sim["ki"]:g}; '
            f'{detail}. Local classification: {sim["class_"]}. '
            'Applied PWM is clipped at ±255; nonlinear portions are not classified by the linear criterion alone.')
    page()
    sub('Guided comparison answers')
    rows=[]
    for exp,sim in zip(experiments,simulations):
        rows.append([str(sim['run']),f'{sim["kp"]:g}/{sim["ki"]:g}',
                     f'{sim["zeta"]:.3f}' if not sim['ki'] else f'ρI = {sim["rho_I"]:.3f}',sim['class_']])
    table(['Run','Kp/Ki','Stability measure','Local model class'],rows,[35,70,100,210])
    p('<b>1. Best correspondence:</b> low/intermediate P simulations reproduce slow approach and remaining droop qualitatively; intermediate PI (Run 5) reproduces reduced target error. None reproduces the complete high-gain speed, persistent oscillation, and settling behavior. Initial conditions prevent a fair numerical ranking by rise time alone.')
    p(f'<b>2. P organization:</b> ζ decreases from {simulations[0]["zeta"]:.3f} to {simulations[1]["zeta"]:.3f} to {simulations[2]["zeta"]:.3f}; all gains exceed Kp,crit. Linear P poles remain negative, so ringing decays. The simulation can clip at high gain, requiring the nonlinear time trace as well as the pole calculation.')
    p(f'<b>3. PI organization:</b> Runs 4–5 share Kp = 16 and increase ρI from {simulations[3]["rho_I"]:.3f} to {simulations[4]["rho_I"]:.3f}, making integral correction more aggressive. Run 6 changes Kp to 1000, raising Ki,crit to {simulations[5]["ki_critical"]:.3f} and reducing ρI to {simulations[5]["rho_I"]:.3f} despite its higher Ki. The retained sequence is not an increasing-ρI study. All three local linear models are stable underdamped; none is marginal or unstable.')
    rows=[]
    for exp,sim in [(experiments[2],simulations[2]),(experiments[5],simulations[5])]:
        for em,sm in zip(exp['metrics'],sim['metrics']):
            rows.append([f'{exp["mode"]} {em["direction"]}',fmt(em['rise_10_90_s']),fmt(sm['rise_10_90_s']),
                         fmt(em['overshoot_percent'],1),fmt(sm['overshoot_percent'],1)])
    table(['High-gain case','Measured rise (s)','Model rise (s)','Measured OS (%)','Model OS (%)'],rows,[85,100,100,110,110])
    p('<b>4. Agreement and disagreement:</b> both model and experiment show overshoot and PWM clipping at high gain. The measured high-gain period is about 5.7–6.2 s, whereas the shared model has slower, decaying oscillations. Persistent measured ringing contradicts the ideal unsaturated, continuous-time prediction of decay if that model is used to explain the full experiment. It does not prove the apparatus is linearly marginal: saturation, sampled control, additional thermal states, and changing parameters are omitted effects.')
    p('The high-gain simulations are model tests rather than fitted predictions. Halving Δt to 0.005 s changes temperature by at most '
      f'{max(s["timestep_change_C"] for s in simulations):.4f} °C across the six runs, much smaller than their main experimental discrepancies.')
    p('<b>Controlled parameter checks:</b> one-lump PI comparisons show higher Ki and C lower damping, while higher Kp raises it. The assigned two-lump P cases give ζ ≈1.31, 1.00, 0.81 at Kp = 60, 105, 160. At Kp = 105, G = 35, 50, 70 W/K gives ζ ≈0.84, 1.00, 1.18. An approximately equal capacitance split gives the weakest damping among the tested splits. These practice figures remain in Part_II/RESULTS.md, separate from the twelve Goldilocks figures.')
    page()
    h('4. PI steady state, assumptions, and windup')
    eq(r'u=K_pe+K_iq,\quad\dot q=e,\quad e=T_{set}-T')
    p('At a stable, unsaturated PI equilibrium, q is constant, so dq/dt = e = 0. Therefore <b>Tss = Tset = 55 °C</b>. The P term becomes zero, while the stored I term supplies the heat-loss-balancing command:')
    eq(r'u_{ss}=u_I=\frac{H(55-T_{amb})}{P_{u,h}}=\frac{55-24.220}{0.5311}=57.95\ \mathrm{PWM}')
    p('This is an ideal calculation, not a 55 °C hardware run. It requires stable feedback, enough heating power within ±255, no active shutdown, continued integral action with Ki > 0, and accurate, timely measurement. Sensor bias would make indicated rather than actual temperature equal 55 °C.')
    p('<b>Windup:</b> while applied PWM is capped, persistent error can keep increasing q. The excessive stored command then continues heating after the target is crossed, causing overshoot and delayed recovery. Conditional anti-windup holds q when the proposed integral update pushes the request farther past the limit, and permits updates that bring it back. The clamp and shutdown remain separate protections.')
    p('<b>Reset thought experiment:</b> at equilibrium P = 0 and I provides the balancing heat. Clearing q removes that command; temperature initially falls, then P responds and I rebuilds. Integral reset does not preserve the former equilibrium output.')
    h('5. Model limits and final gain choice')
    eq(r'T(t)-T_{ss}=[T(0)-T_{ss}]\exp[-(1+\chi K_p)t/\tau]')
    p('In the ideal continuous-time one-lump P model, the exponential is positive and decays: temperature approaches its equilibrium monotonically and cannot ring. This statement assumes instantaneous feedback; it is not a claim that every physical P controller is non-oscillatory. The observed Kp = 1000 P oscillation is direct evidence that this simplest model is inadequate.')
    p('The two-lump balances add a second stored-energy state. Heat first changes the TEC-side temperature, then passes through G to the measured mass. Tm can continue rising after the command falls because the TEC-side mass remains hotter. This lag permits P overshoot and ringing; the twelve figures show what the model captures and where it fails.')
    p(f'<b>Selected P:</b> Kp = 20 PWM/°C is a provisional measured compromise: it reduces the large error of Kp = 5 and avoids the large oscillations and saturation of Kp = 1000. The selected shared model gives ζ = {simulations[1]["zeta"]:.3f} and Kp,crit = {KP_CRIT:.3f}, predicting an underdamped response rather than critical damping. Selection is based on the measured tradeoff, not a claim that this gain is theoretically optimal.')
    p(f'<b>Selected PI:</b> Kp = 16 PWM/°C and Ki = 0.5 PWM/(°C·s), with ρI = {simulations[4]["rho_I"]:.3f}, combines relatively small final target error with limited overshoot in Run 5. Ki = 0.1 corrects more slowly; Kp = 1000, Ki = 2 produces persistent large excursions and clipping. Since the high-PI rerun changes both gains, it cannot establish the isolated effect of Ki. Neither selected gain pair has a verified long-term settling result.')
    p('<b>Next physical effect:</b> include the actual ≈0.57 s sampled controller and measurement/command delay. The present continuous-feedback simulation updates much faster. Further thermal states, sensor placement, and temperature-dependent TEC coefficients may also matter; these data do not identify a unique cause of the persistent oscillation.')
    page()
    h('Data, code, and reproduction')
    p('Build command from the repository root (phys39a environment):<br/>/opt/anaconda3/envs/phys39a/bin/python code/module6/A3/build_a3.py --save-csv')
    p('<link href="../../code/module6/A3/build_a3.py" color="#1764ab">Analysis and report builder</link> · '
      '<link href="../../code/module6/A3/results/experimental_metrics.csv" color="#1764ab">Experimental metrics</link> · '
      '<link href="../../code/module6/A3/results/analysis.json" color="#1764ab">Shared settings and stability calculations</link> · '
      '<link href="../../code/module6/Part_II/RESULTS.md" color="#1764ab">Controlled comparison results</link>')
    for exp in experiments:
        p(f'<link href="../../{exp["path"]}" color="#1764ab">Experimental Run {exp["run"]} raw recording</link> · '
          f'<link href="../../code/module6/A3/results/simulation_{exp["run"]}.csv" color="#1764ab">Simulation Run {exp["run"]} data</link>')
    p('GitHub modeling/data checkpoint: <link href="https://github.com/hasanm720/Module1/commit/ff2f524b009e5d64936f1dcef9125ed07551ceb1" color="#1764ab">ff2f524 — Part 7 data with saturation reruns</link>. This report is a later local build; the checkpoint is not claimed to include the finished PDF.')
    p('Assignment: <link href="https://sethfraden.github.io/Phys39F26-course/labs/lab-06/#a3-questions" color="#1764ab">A3 Questions 1–5</link>. Simulation protocol: <link href="https://sethfraden.github.io/Phys39F26-course/labs/lab-07/" color="#1764ab">Module 6 Part II</link>.')



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
            self.drawRightString(553,824,'2026-10-19')
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
    data=analyse(args.save_csv);prepare_report(data);render()
    print(f'Kp,crit={KP_CRIT:.4f}; numerical checks passed.')
