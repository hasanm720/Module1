# Module 8 — Angstrom method

Open [module_08_angstrom_controller.ino](module_08_angstrom_controller/module_08_angstrom_controller.ino) in Arduino IDE (or use the CLI in AGENTS.md), upload to the Uno, then close Serial Monitor.

```bash
/opt/anaconda3/envs/phys39a/bin/python code/module8/module_08_angstrom_gui.py --label pilot --mode OPEN --schedule "1800,40,16,100"
```

**Wiring is unchanged from Module 7:** TEC tag T5 = A1; rod T1, T2, T3, T4, T6 = A5, A4, A3, A2, A0. H-bridge D9 = HEAT, D10 = COOL.

## Who does what

| Arduino | Python GUI |
|---|---|
| Setpoint T_set = Ta + Tb sin(phase), one continuous phase across period changes | Edits and sends the schedule and settings |
| OPEN (Module 4 lookup table), P, or PI on the TEC thermistor | Live plot of all six temperatures, setpoint and PWM |
| Cooling multiplier r on negative commands, then PWM saturation, anti-windup | Saves every valid record unmodified to `data/module_08/angstrom_raw_[label_]<timestamp>.csv` |
| Schedule validation and execution; ends at zero output | Saves `EVENT` lines to the matching `.events.txt` |
| All safety limits | Heartbeat (`PING` every 0.5 s) on its own thread |

## Settling and period changes (lab-09 S18.9–S18.10)

- **Test** (`settling.py`, shared by the GUI and `settle_check.py`): between successive complete cycles, |Δmean| ≤ 0.10 °C, |ΔB|/B ≤ 5 %, |Δφ| ≤ 0.05 rad, or 3 × each sensor's own fit noise if that is larger (S18.9: tolerances justified by measured noise and fit uncertainty), for TEC and T1–T4 (T6 added when its amplitude is ≥ 0.1 °C). Settled after 2 consecutive passes; then 5 cycles are retained, and each must also pass.
- **Live:** the GUI shows this after every cycle. Tick **Hold period until Next** (or launch with `--hold`); when it reads **READY**, press **Next period →**. Arduino commands: `HOLD ON|OFF`, `NEXT` (phase stays continuous; the last step ends the run at zero output).
- **Offline:** `python code/module8/settle_check.py RUN.csv` prints the same test per period and fits the retained cycles.

## Record format

```text
time_ms,run_state,control_mode,step,Ta_C,Tb_C,period_s,setpoint_C,feedforward_pwm,TEC_C,T1_C,T2_C,T3_C,T4_C,T5_C,controller_pwm,heating_to_cooling_ratio,signed_pwm
```

- `T1_C`…`T5_C` are the rod sensors in hole order, so `T5_C` is the sensor with wire tag **T6**.
- `nan` is the placeholder for fields that do not apply: no run active, `feedforward_pwm` in P/PI, `controller_pwm` and the ratio in OPEN.
- `controller_pwm` is the raw command before r. `signed_pwm` is the applied output.
- `run_state`: IDLE, RUN, DONE, STOPPED, SHUTDOWN, SENSOR_FAULT, ROD_LIMIT, TIMEOUT. `control_mode`: OPEN, P, PI.

## Safety

| Condition | Result |
|---|---|
| TEC thermistor > 60 °C, or invalid | SHUTDOWN / SENSOR_FAULT, output zero; needs a new START |
| Rod base T1 > 56 °C, or invalid (lab-09 limit) | ROD_LIMIT, output zero |
| No command or `PING` for 2 s | TIMEOUT, output zero |
| Malformed command, or a settings change during a run | Run stops, output zero |
| Step with period < 100 s, or setpoint outside 10–56 °C | Rejected before the run |

Output is zero at startup and when the schedule ends. HEAT and COOL are never on together. T1 can only end a run; it never enters feedback.

The open-loop table is the Module 4 steady-state curve (10–45 °C), extended to 56 °C with χh = 0.5311 °C/count. r = 2.83 is the Module 4 fit ratio.

## Verification

`sh code/module8/sim_test/run_sim_test.sh` compiles the real sketch against a fake Arduino and checks startup, schedule validation, phase continuity across a period change, the multiplier before saturation, and every safety path above. All pass. Upload compiles for the Uno. **Real-board behavior remains to be verified at the bench.**
