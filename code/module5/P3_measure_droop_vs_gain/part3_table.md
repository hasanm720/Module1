# Module 5 - Part 3: Droop Versus Gain

### Experimental Parameters
- **Ambient temperature:** 27.0 °C *(provisional; verify actual lab ambient)*
- **Setpoint:** 30.00 °C
- **Assumed initial error from ambient:** 3.0 °C

### Data Collection Table

Temperatures, reported PWM, and next commanded PWM are transcribed from each screenshot's live readout. These are individual observations, not averages or independently verified steady states. Predicted initial PWM uses the assumed 3 °C initial error; screenshots do not establish actual starting temperatures.

| $K_p$ (PWM/°C) | Predicted $P_0$ (counts, assumed ambient) | Setpoint (°C) | Screenshot temperature (°C) | Measured droop (°C) | Reported PWM (counts) | Next command PWM (counts) | Source |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 3 | 30.00 | 28.49 | 1.51 | 1 | 2 | [p=1.png](../../../docs/images/module5/P3_measure_droop_vs_gain/p=1.png) |
| 2 | 6 | 30.00 | 29.46 | 0.54 | 1 | 1 | [p=2.png](../../../docs/images/module5/P3_measure_droop_vs_gain/p=2.png) |
| 3 | 9 | 30.00 | 29.57 | 0.43 | 1 | 1 | [p=3.png](../../../docs/images/module5/P3_measure_droop_vs_gain/p=3.png) |
| 4 | 12 | 30.00 | 29.52 | 0.48 | 2 | 2 | [p=4.png](../../../docs/images/module5/P3_measure_droop_vs_gain/p=4.png) |
| 5 | 15 | 30.00 | 29.50 | 0.50 | 2 | 2 | [p=5.png](../../../docs/images/module5/P3_measure_droop_vs_gain/p=5.png) |

All screenshots show HEAT. At gain 1 the reported PWM is 1 while the next command is 2; the screenshot captures a command update. Droop falls from gain 1 to 3, then rises slightly at gains 4 and 5. Preserve this variation rather than forcing a monotonic trend.
