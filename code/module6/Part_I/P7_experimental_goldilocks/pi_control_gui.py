"""Module 5 GUI extended with PI, integral reset, and per-run Goldilocks logs."""
import csv
from datetime import datetime
import math
from pathlib import Path
import sys
import time
import argparse

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'module5/P1_P-only_control'))
from p_control_gui import PControlGUI, QtWidgets, QtCore, serial, STALE_SECONDS, WINDOW_SECONDS
from PHYS39A_instrumentation.code.module6.Part1.P7_experimental_goldilocks.pi_logic import PIController

FIELDS=['elapsed_s','arduino_s','temperature_C','setpoint_C','kp_pwm_per_C',
        'ki_pwm_per_C_s','dt_s','error_C','u_P','u_I','requested_pwm','applied_pwm',
        'reported_signed_pwm','q_C_s','mode','enabled','safety','limit_C','pwm_limit',
        'anti_windup','run','initial_temperature_C']


class PIControlGUI(PControlGUI):
    def __init__(self,port=None):
        self.controller=PIController()
        self.previous_time=None
        self.run_initial=None
        super().__init__(port)
        # The base opens a P-only log; no measurements have been handled yet.
        self.log_file.close()
        self.log_path.unlink()
        self.log_file=None
        self.writer=None
        self.setWindowTitle('Module 6 — P / PI Goldilocks control')

    def build_ui(self):
        super().build_ui()
        self.kp.setMaximum(1000)
        self.mode.addItem('PI')
        panel=QtWidgets.QWidget(); grid=QtWidgets.QGridLayout(panel)
        self.ki=QtWidgets.QDoubleSpinBox(); self.ki.setDecimals(4)
        self.ki.setRange(0,10); self.ki.setSingleStep(.01); self.ki.setValue(.02)
        self.pwm_limit=QtWidgets.QSpinBox(); self.pwm_limit.setRange(1,255); self.pwm_limit.setValue(255)
        self.anti_windup=QtWidgets.QCheckBox('Anti-windup'); self.anti_windup.setChecked(True)
        self.anti_windup.setEnabled(False)
        self.run_number=QtWidgets.QSpinBox(); self.run_number.setRange(1,6)
        self.zero=QtWidgets.QPushButton('Stop / Zero integral')
        for col,(label,widget) in enumerate([('Ki (PWM/°C/s)',self.ki),('PWM limit',self.pwm_limit),
                                           ('Run number',self.run_number)]):
            grid.addWidget(QtWidgets.QLabel(label),0,col); grid.addWidget(widget,1,col)
        grid.addWidget(self.anti_windup,1,3); grid.addWidget(self.zero,1,4)
        self.centralWidget().layout().insertWidget(1,panel)
        self.zero.clicked.connect(self.zero_integral)
        for widget in (self.kp,self.ki,self.pwm_limit,self.run_number):
            widget.valueChanged.connect(lambda _: self.stop_control('Settings changed — stopped'))
        self.setpoint.valueChanged.connect(self.target_changed)
        self.manual_pwm.setEnabled(False)

    def target_changed(self):
        # Keep up/down steps within the same run. Do not reset q between steps.
        if self.sample and self.setpoint.value()>=self.sample.limit:
            self.stop_control('Setpoint must be below Arduino shutdown temperature')

    def zero_integral(self):
        self.stop_control('Integral reset — output off')
        self.controller.reset(); self.previous_time=None

    def mode_changed(self):
        super().mode_changed()
        self.controller.reset(); self.previous_time=None

    def stop_control(self,reason):
        super().stop_control(reason)
        if getattr(self,'log_file',None):
            self.log_file.close(); self.log_file=None; self.writer=None

    def start_control(self):
        if self.mode.currentText()=='Manual':
            self.status.setText('Select P-only or PI for Goldilocks runs'); return
        if not self.sample or self.setpoint.value()>=self.sample.limit:
            self.status.setText('Need safe telemetry and a setpoint below the shutdown temperature'); return
        self.zero_integral()
        super().start_control()
        if not self.enabled: return
        self.run_initial=self.sample.temperature
        self.previous_time=self.sample.time
        self.started=time.monotonic(); self.history.clear()
        folder=HERE/'data'; folder.mkdir(exist_ok=True)
        self.log_path=folder/f'run{self.run_number.value()}_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
        try:
            self.log_file=self.log_path.open('w',newline='')
            self.writer=csv.writer(self.log_file); self.writer.writerow(FIELDS)
        except OSError as exc:
            self.stop_control(f'Cannot open log: {exc}')

    def handle_sample(self,sample,now):
        dt=0 if self.previous_time is None else sample.time-self.previous_time
        if self.previous_time is not None and not 0<dt<=STALE_SECONDS:
            self.stop_control('Invalid sample interval — stopped')
        self.previous_time=sample.time
        self.sample,self.last_received=sample,now
        if sample.safety!='OK': self.stop_control(f'Arduino {sample.safety}')
        target,kp=self.setpoint.value(),self.kp.value()
        ki=self.ki.value() if self.mode.currentText()=='PI' else 0
        values=(math.nan,0,0,0,0)
        if self.enabled:
            if not math.isfinite(sample.temperature): self.stop_control('Invalid temperature')
            else:
                try:
                    values=self.controller.update(target,sample.temperature,kp,ki,dt,
                                                  self.pwm_limit.value(),True)
                except ValueError as exc: self.stop_control(str(exc))
        error,p,i,requested,applied=values
        if not self.enabled: applied=0
        self.send('HEAT' if applied>=0 else 'COOL',abs(applied))
        reported=sample.pwm if sample.direction=='HEAT' else -sample.pwm
        elapsed=now-self.started
        self.update_output_notice()
        self.readout.setText(f'T {sample.temperature:.2f} °C | e {error:+.2f} °C | '
                             f'P {p:+.2f} | I {i:+.2f} | request {requested:+.2f} | '
                             f'applied {applied:+d} | reported {reported:+d} PWM')
        self.history.append((elapsed,sample.temperature,target,error,reported,applied,
                             0 if reported==0 else (1 if reported>0 else -1),sample.direction))
        while self.history and elapsed-self.history[0][0]>WINDOW_SECONDS: self.history.popleft()
        times=[r[0] for r in self.history]
        for suffix,direction in [('heat','HEAT'),('cool','COOL')]:
            for prefix,index in [('temperature',1),('pwm',4)]:
                self.curves[f'{prefix}_{suffix}'].setData(times,[r[index] if r[7]==direction else math.nan for r in self.history])
        for key,index in [('setpoint',2),('error',3),('command_pwm',5),('direction',6)]:
            self.curves[key].setData(times,[r[index] for r in self.history])
        for plot in self.plots: plot.setXRange(max(0,elapsed-WINDOW_SECONDS),max(WINDOW_SECONDS,elapsed),padding=0)
        if self.enabled and self.writer:
            try:
                self.writer.writerow([elapsed,sample.time,sample.temperature,target,kp,ki,dt,
                                      error,p,i,requested,applied,reported,self.controller.q,
                                      self.mode.currentText(),True,sample.safety,sample.limit,
                                      self.pwm_limit.value(),True,self.run_number.value(),self.run_initial])
                self.log_file.flush()
            except OSError as exc: self.stop_control(f'Logging failed: {exc}')

    def closeEvent(self,event):
        self.timer.stop(); self.stop_control('Closing')
        if self.ser: self.ser.close()
        event.accept()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port'); args=parser.parse_args()
    app=QtWidgets.QApplication(sys.argv)
    gui=PIControlGUI(args.port); gui.show(); sys.exit(app.exec())
