"""Pure P-control calculation and the matching Arduino telemetry parser."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Sample:
    time: float
    temperature: float
    pwm: int
    direction: str
    safety: str
    limit: float
    pwm9: int
    pwm10: int


def p_command(setpoint, temperature, kp):
    """Return error, unclamped signed u, direction, and rounded/clamped PWM."""
    if not all(math.isfinite(v) for v in (setpoint, temperature, kp)) or kp < 0:
        raise ValueError('Temperature, setpoint and nonnegative gain must be finite.')
    error = setpoint - temperature
    u = kp * error  # No bias, feedforward, integral or derivative term.
    if not math.isfinite(u):
        raise ValueError('Control output is not finite.')
    return error, u, 'HEAT' if u >= 0 else 'COOL', min(255, int(round(abs(u))))


def command_bytes(direction, pwm):
    if direction not in ('HEAT', 'COOL') or not isinstance(pwm, int) or not 0 <= pwm <= 255:
        raise ValueError('Command requires HEAT/COOL and integer PWM 0–255.')
    return f'SET PWM {pwm} DIR {direction}\n'.encode('ascii')


def parse_sample(line):
    """Ignore messages; reject incomplete or inconsistent telemetry."""
    if not line.startswith('Temperature (C):'):
        return None
    fields = dict(part.strip().split(':', 1) for part in line.split(','))
    fields = {key: value.strip() for key, value in fields.items()}
    try:
        sample = Sample(float(fields['Time (s)']), float(fields['Temperature (C)']),
                        int(fields['PWM']), fields['DIR'], fields['Safety'],
                        float(fields['Limit (C)']), int(fields['PWM9']), int(fields['PWM10']))
    except (KeyError, ValueError) as error:
        raise ValueError('Incomplete Module 5 telemetry; upload the matching sketch.') from error
    if (not math.isfinite(sample.time) or sample.time < 0 or not math.isfinite(sample.limit)
            or sample.direction not in ('HEAT', 'COOL')
            or sample.safety not in ('OK', 'SHUTDOWN', 'SENSOR_FAULT', 'TIMEOUT')
            or not all(0 <= p <= 255 for p in (sample.pwm, sample.pwm9, sample.pwm10))):
        raise ValueError('Invalid telemetry values.')
    if sample.safety != 'SENSOR_FAULT' and not math.isfinite(sample.temperature):
        raise ValueError('Invalid measured temperature.')
    if sample.safety == 'OK':
        expected = (sample.pwm, 0) if sample.direction == 'HEAT' else (0, sample.pwm)
        if sample.temperature > sample.limit or (sample.pwm9, sample.pwm10) != expected:
            raise ValueError('Telemetry disagrees with temperature limit or output pins.')
    elif any((sample.pwm, sample.pwm9, sample.pwm10)):
        raise ValueError('Nonzero reported output during shutdown.')
    return sample
