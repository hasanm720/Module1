"""Make six experimental plots from six selected, matched GUI logs."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def load(path,number):
    with path.open() as f: rows=list(csv.DictReader(f))
    if len(rows)<3: raise ValueError(f'{path}: too few samples')
    for key in ['run','kp_pwm_per_C','ki_pwm_per_C_s','pwm_limit','anti_windup','mode']:
        if len({r[key] for r in rows})!=1: raise ValueError(f'{path}: {key} changed during the run')
    if int(rows[0]['run'])!=number: raise ValueError(f'{path}: expected run {number}')
    if any(r['safety']!='OK' or r['enabled']!='True' for r in rows):
        raise ValueError(f'{path}: stopped/unsafe samples')
    if rows[0]['anti_windup']!='True': raise ValueError('Anti-windup must be enabled')
    t=np.array([float(r['arduino_s']) for r in rows])
    if np.any(np.diff(t)<=0): raise ValueError(f'{path}: time must increase')
    targets=np.array([float(r['setpoint_C']) for r in rows])
    if len(set(targets))!=2 or not (np.any(np.diff(targets)>0) and np.any(np.diff(targets)<0)):
        raise ValueError(f'{path}: need the same two setpoints and both up/down steps')
    ki=float(rows[0]['ki_pwm_per_C_s'])
    if (number<=3 and ki!=0) or (number>3 and ki<=0): raise ValueError('Runs 1–3 must be P; 4–6 must be PI')
    if abs(float(rows[0]['q_C_s']))>abs(float(rows[0]['error_C'])*float(rows[0]['dt_s']))+1e-8:
        raise ValueError(f'{path}: integral was not reset')
    return rows,tuple(sorted(set(targets)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs',type=Path,nargs=6,help='Selected logs in run 1–6 order')
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'results')
    args=parser.parse_args()
    datasets=[load(p,i) for i,p in enumerate(args.logs,1)]
    if len({targets for _,targets in datasets})!=1: raise ValueError('All six runs must use the same two setpoints')
    if len({rows[0]['pwm_limit'] for rows,_ in datasets})!=1: raise ValueError('PWM limits must match')
    kp=[float(rows[0]['kp_pwm_per_C']) for rows,_ in datasets]
    ki=[float(rows[0]['ki_pwm_per_C_s']) for rows,_ in datasets]
    if not kp[0]<kp[1]<kp[2]: raise ValueError('P gains must increase from low to high')
    if not kp[3]==kp[4]==kp[5] or not 0<kp[3]<kp[1]: raise ValueError('PI Kp must be fixed below intermediate P Kp')
    if not 0<ki[3]<ki[4]<ki[5]: raise ValueError('PI Ki must increase from low to high')
    args.output.mkdir(exist_ok=True,parents=True)
    for number,(rows,_) in enumerate(datasets,1):
        t=np.array([float(r['arduino_s']) for r in rows]); t-=t[0]
        fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
        for ax,keys in zip(axes,[['temperature_C','setpoint_C'],['reported_signed_pwm','applied_pwm','requested_pwm','u_P','u_I'],['error_C']]):
            for key in keys: ax.plot(t,[float(r[key]) for r in rows],label=key)
            ax.legend(); ax.grid(alpha=.3)
        for ax,label in zip(axes,['Temperature (°C)','Signed PWM','Error (°C)']): ax.set_ylabel(label)
        axes[-1].set_xlabel('Elapsed time (s)')
        interval=np.median([float(r['dt_s']) for r in rows])
        fig.suptitle(f'Experimental run {number}: Kp={kp[number-1]:g}, Ki={ki[number-1]:g}; '
                     f'initial {rows[0]["initial_temperature_C"]} °C; PWM ±{rows[0]["pwm_limit"]}; '
                     f'median Δt={interval:.3f} s; anti-windup on')
        fig.tight_layout(); fig.savefig(args.output/f'run{number}.png',dpi=180); plt.close(fig)
    print('Six experimental plots saved. Check settling and response quality from the traces.')

if __name__=='__main__': main()
