"""PI command with conditional integration and signed PWM clamp."""
from dataclasses import dataclass
import math


@dataclass
class PIController:
    q: float = 0.0

    def reset(self):
        self.q = 0.0

    def update(self, target, temperature, kp, ki, dt, limit=255, anti_windup=True):
        if not all(math.isfinite(v) for v in (target,temperature,kp,ki,dt,limit,self.q)):
            raise ValueError('Control values must be finite.')
        if min(kp,ki,dt)<0 or not 0<limit<=255:
            raise ValueError('Gains/time must be nonnegative; PWM limit must be 1–255.')
        error = target-temperature
        p = kp*error
        proposed_q = self.q + error*dt if ki else 0.0
        proposed = p+ki*proposed_q
        if not all(math.isfinite(v) for v in (p,proposed_q,proposed)):
            raise ValueError('Control calculation overflowed.')
        farther = (proposed>limit and error>0) or (proposed < -limit and error<0)
        if not (anti_windup and farther):
            self.q=proposed_q
        if ki==0: self.q=0
        i=ki*self.q
        requested=p+i
        applied=int(round(max(-limit,min(limit,requested))))
        return error,p,i,requested,applied
