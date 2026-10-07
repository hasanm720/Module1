"""Supervised 30 °C P-only retests, with fresh logs and confirmed shutdown.

Close other serial applications. Use the matching Module 5 Arduino sketch.
Run only while supervising and within the instructor-approved gain range:
python3 run_high_gain_tests.py --port /dev/cu.usbmodem101
Default: gains 20, 40, 50, each recorded for up to 180 seconds.
Original CSVs are never overwritten. Ctrl-C requests shutdown.
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import sys
import time

import serial

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'P1_P-only_control'))
from control_logic import command_bytes, p_command, parse_sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--seconds', type=float, default=180)
    args = parser.parse_args()
    if args.seconds < 60:
        parser.error('Use at least 60 seconds per gain to observe recurring behavior.')
    path = HERE / f'high_gain_retest_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
    with serial.Serial(args.port, 115200, timeout=0.2, write_timeout=0.5) as ser:
        def read_sample():
            line = ser.readline().decode('ascii', errors='replace').strip()
            return parse_sample(line) if line.startswith('Temperature (C):') else None

        def stop():
            ser.write(command_bytes('HEAT', 0))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                sample = read_sample()
                if sample and sample.pwm9 == sample.pwm10 == sample.pwm == 0:
                    print('STOP CONFIRMED: PWM9=PWM10=0', flush=True)
                    return
            print('Shutdown command sent; zero-output telemetry NOT confirmed.', flush=True)

        try:
            # Opening the port can reset the board; wait for matching telemetry.
            deadline = time.monotonic() + 8
            sample = None
            while time.monotonic() < deadline and sample is None:
                sample = read_sample()
            if sample is None:
                raise RuntimeError('No matching Module 5 telemetry received.')
            stop()
            print(f'Fresh log: {path}', flush=True)
            with path.open('x', newline='') as log:
                writer = csv.writer(log)
                writer.writerow(['gain_elapsed_s', 'arduino_s', 'kp_pwm_per_C',
                                 'setpoint_C', 'temperature_C', 'reported_pwm',
                                 'reported_direction', 'command_pwm',
                                 'command_direction', 'safety', 'pwm9', 'pwm10'])
                for gain in (20, 40, 50):
                    started = time.monotonic()
                    last_received = started
                    next_update = 0
                    print(f'Starting Kp={gain}, setpoint=30 °C, {args.seconds:g} s', flush=True)
                    while time.monotonic() - started < args.seconds:
                        if (HERE / 'advance_gain.request').exists():
                            (HERE / 'advance_gain.request').unlink()
                            print('Observation complete; moving to next gain.', flush=True)
                            break
                        sample = read_sample()
                        now = time.monotonic()
                        if sample is None:
                            if now - last_received > 2:
                                raise RuntimeError('Telemetry stale for more than 2 seconds.')
                            continue
                        last_received = now
                        if sample.safety not in ('OK', 'TIMEOUT'):
                            raise RuntimeError(f'Arduino safety state: {sample.safety}')
                        if not 15 <= sample.temperature <= 35:
                            raise RuntimeError('Temperature outside retest bounds 15–35 °C.')
                        error, raw, direction, pwm = p_command(30, sample.temperature, gain)
                        if abs(raw) >= 255:
                            raise RuntimeError('Saturation requested; stop rather than continue this retest.')
                        ser.write(command_bytes(direction, pwm))
                        elapsed = now - started
                        writer.writerow([round(elapsed, 3), sample.time, gain, 30,
                                         sample.temperature, sample.pwm, sample.direction,
                                         pwm, direction, sample.safety, sample.pwm9, sample.pwm10])
                        log.flush()
                        if elapsed >= next_update:
                            print(f'Kp={gain} t={elapsed:.0f}s T={sample.temperature:.2f} °C '
                                  f'reported={sample.pwm} command={direction} {pwm}', flush=True)
                            next_update = elapsed + 30
            print('All retests complete.', flush=True)
        finally:
            stop()


if __name__ == '__main__':
    main()
