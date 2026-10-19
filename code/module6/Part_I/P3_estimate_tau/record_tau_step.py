"""Supervised constant-PWM open-loop step; Module 5 firmware, 1000 ADC averages.

Hold zero output until a stable baseline, then apply +5 PWM by default.
Retain raw CSV, stop and confirm zero output, then generate the tau report.
"""
import argparse
import csv
from datetime import datetime
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'module5/P1_P-only_control'))
from control_logic import command_bytes, parse_sample


class Arduino:
    """Bounded serial reads, strict telemetry validation and confirmed stop."""
    def __init__(self, port):
        import serial
        self.ser = serial.Serial(port, 115200, timeout=.2, write_timeout=.5)
        self.buffer = bytearray()
        self.previous_time = None

    def read(self, timeout=2):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            self.buffer.extend(self.ser.read(max(1,self.ser.in_waiting)))
            if len(self.buffer) > 16384:
                raise RuntimeError('Serial backlog exceeds allowed size.')
            while b'\n' in self.buffer:
                line, _, rest = self.buffer.partition(b'\n')
                self.buffer = bytearray(rest)
                sample = parse_sample(line.decode('ascii',errors='replace').strip())
                if sample is None:
                    continue
                if self.previous_time is not None and sample.time <= self.previous_time:
                    raise RuntimeError('Arduino clock reset or telemetry did not advance.')
                self.previous_time = sample.time
                return sample
        raise RuntimeError('Fresh telemetry timed out.')

    def command(self, pwm):
        data = command_bytes('HEAT',pwm)
        if self.ser.write(data) != len(data):
            raise RuntimeError('Incomplete command write.')

    def stop(self):
        self.command(0)
        self.buffer.clear()
        self.ser.reset_input_buffer()
        deadline = time.monotonic()+3
        while time.monotonic() < deadline:
            sample = self.read(timeout=min(1,deadline-time.monotonic()))
            if sample.pwm == sample.pwm9 == sample.pwm10 == 0:
                print('STOP CONFIRMED: PWM9=PWM10=0',flush=True)
                return
        raise RuntimeError('Zero-output telemetry not confirmed.')

    def close(self):
        self.ser.close()


def stable(samples, window=60):
    if not samples or samples[-1][0]-samples[0][0] < window:
        return False
    recent = [(t, T) for t, T in samples if t >= samples[-1][0]-window]
    t, temp = zip(*recent)
    first = statistics.mean(T for tm, T in recent if tm <= t[0]+window/2)
    last = statistics.mean(T for tm, T in recent if tm > t[0]+window/2)
    return max(temp)-min(temp) <= .15 and abs(last-first) <= .05


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', default='/dev/cu.usbmodem101')
    p.add_argument('--pwm', type=int, default=5)
    p.add_argument('--baseline-timeout', type=float, default=120)
    p.add_argument('--seconds', type=float, default=240,
                   help='Maximum step duration; five-minute total limit takes priority')
    a = p.parse_args()
    if (not 1 <= a.pwm <= 10 or not math.isfinite(a.baseline_timeout)
            or a.baseline_timeout < 60 or not math.isfinite(a.seconds) or a.seconds < 120):
        p.error('Use PWM 1–10, baseline timeout at least 60 s and step duration at least 120 s.')
    total_deadline = time.monotonic()+300
    # Reserve ten seconds for confirmed shutdown and bounded report generation.
    acquisition_deadline = total_deadline-10
    folder = HERE/'data'
    folder.mkdir(exist_ok=True)
    path = folder/f'open_loop_step_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
    device = Arduino(a.port)
    completed = False
    stopped = False
    columns = ['phase','control_mode','gain_elapsed_s','arduino_s','kp_pwm_per_C',
               'setpoint_C','temperature_C','reported_pwm','reported_direction',
               'command_pwm','command_direction','safety','pwm9','pwm10']
    try:
        device.read(timeout=8)
        device.stop()
        with path.open('x', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(columns)
            def read():
                remaining = acquisition_deadline-time.monotonic()
                if remaining <= 0:
                    raise RuntimeError('Five-minute budget reached; raw data retained.')
                sample = device.read(timeout=min(2,remaining))
                if sample.safety != 'OK' or not 15 <= sample.temperature <= 35:
                    raise RuntimeError(f'Unsafe telemetry: {sample.safety}, T={sample.temperature}')
                return sample
            def log(sample, phase, elapsed, pwm, reference):
                writer.writerow([phase,'open_loop',elapsed,sample.time,0,reference,
                                 sample.temperature,sample.pwm,sample.direction,
                                 pwm,'HEAT',sample.safety,sample.pwm9,sample.pwm10])
                stream.flush()
            print(f'Fresh data: {path}', flush=True)
            print('Baseline: holding PWM=0 until the final 60 seconds are stable.', flush=True)
            baseline = []
            started = time.monotonic()
            next_print = 0
            while True:
                sample = read()
                device.command(0)
                elapsed = time.monotonic()-started
                baseline.append((elapsed,sample.temperature))
                log(sample,'baseline',elapsed,0,sample.temperature)
                if elapsed >= next_print:
                    print(f'Baseline {elapsed:.0f}s: T={sample.temperature:.2f} °C', flush=True)
                    next_print = elapsed+30
                if stable(baseline):
                    break
                if elapsed >= a.baseline_timeout:
                    raise RuntimeError('Baseline did not settle; no heating step applied.')
            reference = sample.temperature
            if acquisition_deadline-time.monotonic() < 120:
                raise RuntimeError('Not enough time left for a valid step; no heating applied.')
            if reference + .5311*a.pwm > 34:
                raise RuntimeError('Predicted heating endpoint too close to the trial limit.')
            step_start = sample.time
            temperatures = [(0,reference)]
            log(sample,'step',0,a.pwm,reference)
            device.command(a.pwm)
            print(f'STEP: constant +{a.pwm} PWM, initial {reference:.2f} °C.', flush=True)
            next_print = 30
            while True:
                if time.monotonic() >= acquisition_deadline-2:
                    print('Total time limit reached; stopping the step.',flush=True)
                    break
                sample = read()
                elapsed = sample.time-step_start
                if sample.direction != 'HEAT' or sample.pwm != a.pwm:
                    raise RuntimeError('Arduino applied output differs from constant step.')
                device.command(a.pwm)
                temperatures.append((elapsed,sample.temperature))
                log(sample,'step',elapsed,a.pwm,reference)
                if elapsed >= next_print:
                    print(f'Step {elapsed:.0f}s: T={sample.temperature:.2f} °C, PWM={sample.pwm}',flush=True)
                    next_print = elapsed+30
                if elapsed > 120 and sample.temperature < reference-.2:
                    raise RuntimeError('Temperature moving opposite to requested heating.')
                if elapsed >= a.seconds:
                    break
            device.stop()
            stopped = True
            if not stable(temperatures):
                raise RuntimeError('Final 60 seconds not stable; raw data retained, report not replaced.')
            if temperatures[-1][1]-reference < .5:
                raise RuntimeError('Step too small to estimate tau reliably; raw data retained.')
            completed = True
    finally:
        try:
            if not stopped:
                device.stop()
        finally:
            device.close()
    if completed:
        remaining = total_deadline-time.monotonic()
        if remaining <= 0:
            print('Raw recording saved; time budget exhausted before report generation.')
            return
        subprocess.run([sys.executable,str(HERE/'estimate_tau.py'),'--input',str(path),'--kp','0'],
                       check=True,timeout=remaining)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted; requested shutdown.',file=sys.stderr)
        sys.exit(130)
    except (ValueError,RuntimeError,OSError,subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
        print(f'ERROR: {error}',file=sys.stderr)
        sys.exit(1)
