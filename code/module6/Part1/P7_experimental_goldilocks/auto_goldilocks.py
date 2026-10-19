"""Run six matched experiments in the visible PI GUI; Stop cancels the sequence."""
from collections import deque
import argparse
import json
from pathlib import Path
import sys
import time

from PHYS39A_instrumentation.code.module6.Part1.P7_experimental_goldilocks.pi_control_gui import PIControlGUI, QtCore, QtWidgets, HERE

GAINS=[('P-only',5,0),('P-only',20,0),('P-only',1000,0),
       ('PI',16,.1),('PI',16,.5),('PI',16,2)]


class AutoGUI(PIControlGUI):
    def __init__(self,port=None,run=None,kp=None):
        self.auto_active=False
        self.transitioning=False
        self.stage='Waiting for telemetry'
        self.run_index=0 if run is None else run-1
        self.single_run=run
        self.kp_override=kp
        self.samples=deque()
        self.selected_logs=[]
        self.saturation_started=None
        self.envelope=deque(maxlen=3)
        self.envelope_window=[]
        self.envelope_started=None
        super().__init__(port)
        self.progress=QtWidgets.QLabel('Automatic sequence: waiting for fresh Arduino telemetry')
        self.progress.setStyleSheet('font-size: 16px; font-weight: bold;')
        self.centralWidget().layout().insertWidget(0,self.progress)
        self.auto_active=True
        self.auto_timer=QtCore.QTimer(self)
        self.auto_timer.timeout.connect(self.advance_sequence)
        self.auto_timer.start(1000)
        self.stage_started=time.monotonic()
        self.sequence_started=time.monotonic()

    def stop_control(self,reason):
        super().stop_control(reason)
        if getattr(self,'auto_active',False) and not self.transitioning:
            self.auto_active=False
            if hasattr(self,'progress'): self.progress.setText(f'Automatic sequence stopped: {reason}')
            print(f'AUTO STOP: {reason}',flush=True)

    def start_run(self):
        self.transitioning=True
        try:
            self.stop_control('Between automatic runs')
            mode,kp,ki=GAINS[self.run_index]
            if self.kp_override is not None: kp=self.kp_override
            self.run_number.setValue(self.run_index+1)
            self.mode.setCurrentText(mode)
            self.kp.setValue(kp); self.ki.setValue(ki)
            self.pwm_limit.setValue(255); self.setpoint.setValue(28)
            self.start_control()
            if not self.enabled:
                self.auto_active=False
                self.progress.setText('Could not start: '+self.status.text())
                return
            short_path=self.log_path.with_name('screening_'+self.log_path.name)
            self.log_path.rename(short_path); self.log_path=short_path
            self.selected_logs.append(str(self.log_path))
            self.set_stage('Baseline at 28 °C')
            print(f'AUTO RUN {self.run_index+1}: {mode} Kp={kp} Ki={ki}; {self.log_path}',flush=True)
        finally: self.transitioning=False

    def set_stage(self,stage):
        self.stage=stage; self.stage_started=time.monotonic(); self.samples.clear()
        self.saturation_started=None; self.envelope.clear(); self.envelope_window=[]
        self.envelope_started=None
        print(f'AUTO STAGE: run {self.run_index+1}, {stage}',flush=True)

    def handle_sample(self,sample,now):
        super().handle_sample(sample,now)
        if self.auto_active and self.enabled:
            self.samples.append((now,sample.temperature))
            while self.samples and now-self.samples[0][0]>65: self.samples.popleft()
            # Stop on prolonged saturation or clearly growing oscillation envelopes.
            if abs(sample.pwm)>=self.pwm_limit.value():
                if self.saturation_started is None: self.saturation_started=now
                if now-self.saturation_started>30:
                    self.stop_control('PWM saturated for more than 30 s')
            else: self.saturation_started=None
            if self.envelope_started is None: self.envelope_started=now
            self.envelope_window.append(sample.temperature)
            if now-self.envelope_started>=30:
                self.envelope.append(max(self.envelope_window)-min(self.envelope_window))
                self.envelope_window=[]; self.envelope_started=now
                if (len(self.envelope)==3 and self.envelope[0]>.1
                        and self.envelope[1]>1.5*self.envelope[0]
                        and self.envelope[2]>1.5*self.envelope[1]):
                    self.stop_control('Oscillation range is growing across three 30 s windows')
            if not 10<=sample.temperature<=45:
                self.stop_control('Temperature outside 10–45 °C experiment range')

    def advance_sequence(self):
        if not self.auto_active: return
        now=time.monotonic()
        if now-self.sequence_started>=570:
            self.stop_control('9.5-minute sequence deadline reached'); return
        if self.stage=='Waiting for telemetry':
            if self.sample and self.last_received and now-self.last_received<2 and self.sample.safety=='OK':
                self.start_run()
            elif now-self.stage_started>30:
                self.stop_control('No safe telemetry within 30 s')
            return
        if not self.enabled:
            self.stop_control('Control disabled'); return
        elapsed=now-self.stage_started
        settled=(len(self.samples)>2 and self.samples[-1][0]-self.samples[0][0]>=60
                 and max(t for _,t in self.samples)-min(t for _,t in self.samples)<=.1)
        minimum=10 if self.stage.startswith('Baseline') else 40
        self.progress.setText(f'Run {self.run_index+1}/6 — {self.stage} — {elapsed:.0f} s '
                              f'({minimum} s stage; nine minutes total). Stop cancels automation.')
        if elapsed<minimum: return
        print(f'AUTO END STAGE: {self.stage}; elapsed={elapsed:.1f}; settled={settled}',flush=True)
        if self.stage.startswith('Baseline'):
            self.setpoint.setValue(30); self.set_stage('Upward step to 30 °C')
        elif self.stage.startswith('Upward'):
            self.setpoint.setValue(28); self.set_stage('Downward step to 28 °C')
        else:
            self.transitioning=True
            self.stop_control('Automatic run complete')
            self.transitioning=False
            self.run_index+=1
            if self.run_index<6 and self.single_run is None: self.start_run()
            else:
                self.auto_active=False
                if self.single_run is not None:
                    self.progress.setText('Selected run complete — PWM zero. Close window when ready.')
                    print(f'AUTO COMPLETE: {self.selected_logs[-1]}',flush=True)
                    QtCore.QTimer.singleShot(1000,self.close)
                    return
                manifest=HERE/'data'/'screening_selected_logs.json'
                manifest.write_text(json.dumps(self.selected_logs,indent=2)+'\n')
                self.progress.setText('Six short screening runs complete — PWM zero. Responses may not have settled.')
                print(f'AUTO COMPLETE: {manifest}',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--port')
    parser.add_argument('--run',type=int,choices=range(1,7),help='Repeat only this run')
    parser.add_argument('--kp',type=float,help='Override Kp for a selected run (0–1000)')
    args=parser.parse_args()
    if args.kp is not None and (args.run is None or not 0<=args.kp<=1000):
        parser.error('--kp requires --run and a value from 0 to 1000')
    app=QtWidgets.QApplication(sys.argv)
    gui=AutoGUI(args.port,args.run,args.kp); gui.show()
    sys.exit(app.exec())
