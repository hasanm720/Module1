# A3 — Feedback Data and Lumped Modeling

Assignment code: A3
Module: PHYS39 Module 6
Team members: Kyle Chen and Muhammad Hasan

## 1. One-lump model and P-control predictions

The block stores heat while the TEC supplies power and the surroundings remove it:

$$
C\frac{dT}{dt}=P_u u-H(T-T_{amb})\quad\Rightarrow\quad\tau\frac{dT}{dt}=T_{amb}+\chi u-T
$$

$$
\tau=C/H=91.69\ \mathrm{s},\qquad\chi=P_u/H;\quad\chi_h=0.5311,\ \chi_c=0.1878\ \mathrm{^{\circ}C/PWM}
$$

Use χ_h for positive PWM and χ_c for negative PWM. For P control, u = Kp(Tset − T). At steady state:

$$
0=\chi K_p(T_{set}-T_{ss})-(T_{ss}-T_{amb})
$$

$$
e_{ss}=\frac{T_{set}-T_{amb}}{1+\chi K_p},\qquad\tau_{cl}=\frac{\tau}{1+\chi K_p},\qquad L=\chi K_p
$$

Subtracting the steady-state balance gives τ d(T − Tss)/dt = −(1 + L)(T − Tss). **L = χKp is the dimensionless loop gain.**

**Higher Kp:** smaller droop and faster response. P still needs nonzero error to replace heat lost to the room.

### Measured comparison: +5 PWM open loop

Part 3 used ambient 24.220 °C and τ = 91.69 s. Prediction: Tss = 24.220 + 0.5311(5).

| Predicted temperature | Measured final-minute mean | Prediction error |
| --- | --- | --- |
| 26.875 °C | 26.366 °C | +0.510 °C |

The model captures warming but predicts too high a temperature. This trace also supplied τ, so its response time is not an independent check.

### Module 5 interpretation

• **Better insulation:** lower H, higher χ, less droop.
• **Double C:** double response time; same steady temperature.
• **Kp = 1:** L = 0.5311 is not much smaller than one. The crossover is Kp = 1.883 PWM/°C.

## 2. Experimental Goldilocks plots and metrics

All runs used one apparatus, setpoints **28 → 30 → 28 °C**, PWM limit **±255**, anti-windup on, and sample interval ≈0.57 s. Each run lasted ≈93 s: ≈11 s baseline and ≈41 s per step. The integral was reset before each run. Initial temperatures are recorded below; they were not matched.

![Figure 1. Experimental P, Kp = 5 PWM/°C, Ki = 0. Up/down step starts: 25.09/27.40 °C. Slow response and large error.](../figures/module_06/a3/experiment_1.png)

*Figure 1. Experimental P, Kp = 5 PWM/°C, Ki = 0. Up/down step starts: 25.09/27.40 °C. Slow response and large error.*

![Figure 2. Experimental P, Kp = 20 PWM/°C, Ki = 0. Up/down step starts: 27.30/29.30 °C. Faster response with remaining droop.](../figures/module_06/a3/experiment_2.png)

*Figure 2. Experimental P, Kp = 20 PWM/°C, Ki = 0. Up/down step starts: 27.30/29.30 °C. Faster response with remaining droop.*

### Experimental runs 3–4

![Figure 3. Experimental P, Kp = 40 PWM/°C, Ki = 0. Up/down step starts: 27.76/29.64 °C. Small peak below target; no clear ringing.](../figures/module_06/a3/experiment_3.png)

*Figure 3. Experimental P, Kp = 40 PWM/°C, Ki = 0. Up/down step starts: 27.76/29.64 °C. Small peak below target; no clear ringing.*

![Figure 4. Experimental PI, Kp = 16 PWM/°C, Ki = 0.1 PWM/(°C·s). Up/down starts: 27.43/29.33 °C. Slow integral correction.](../figures/module_06/a3/experiment_4.png)

*Figure 4. Experimental PI, Kp = 16 PWM/°C, Ki = 0.1 PWM/(°C·s). Up/down starts: 27.43/29.33 °C. Slow integral correction.*

### Experimental runs 5–6

![Figure 5. Experimental PI, Kp = 16 PWM/°C, Ki = 0.5 PWM/(°C·s). Up/down starts: 27.45/29.95 °C. Closest tracking with little overshoot.](../figures/module_06/a3/experiment_5.png)

*Figure 5. Experimental PI, Kp = 16 PWM/°C, Ki = 0.5 PWM/(°C·s). Up/down starts: 27.45/29.95 °C. Closest tracking with little overshoot.*

![Figure 6. Experimental PI, Kp = 16 PWM/°C, Ki = 2 PWM/(°C·s). Up/down starts: 27.58/29.92 °C. 0.76 °C overshoot and 0.86 °C undershoot.](../figures/module_06/a3/experiment_6.png)

*Figure 6. Experimental PI, Kp = 16 PWM/°C, Ki = 2 PWM/(°C·s). Up/down starts: 27.58/29.92 °C. 0.76 °C overshoot and 0.86 °C undershoot.*

### Largest-gain P and PI: step-response metrics

**Rise:** first 10%–90% crossing from measured initial temperature toward the new target; linearly interpolated.

**Overshoot:** excursion beyond the target ÷ 2 °C step × 100%. **Settling:** remain within ±0.04 °C for the rest of the step, with at least 10 s recorded in-band.

| Mode Kp/Ki | Step | Rise (s) | Overshoot (%) | End error (°C) |
| --- | --- | --- | --- | --- |
| P 40/0 | Up | 6.40 | 0.0 | +0.373 |
| P 40/0 | Down | 6.05 | 16.5 | +0.268 |
| PI 16/2 | Up | 7.01 | 38.0 | +0.058 |
| PI 16/2 | Down | 9.03 | 43.0 | +0.088 |

**Not established in any of the four windows:** settling time, steady-state error, and oscillation period. End error averages the final 5 s; it is not steady-state error.

**Saturation:** none experimentally; maximum absolute reported PWM was 90. High PI showed one overshoot/undershoot per step.

## 3. Two-lump simulations and comparison

**One shared plant:** χc = 0.1878 and χh = 0.5311 °C/PWM; τ = 91.69 s; ambient 24.220 °C; C = 100.549 J/°C; H = 1.0966 W/°C; Pu,c = 0.20595 W/PWM; G = 10 W/°C; CT/C = 0.35; assumed voltage 12 V; resistance 1.50 Ω.

**One shared protocol:** both lumps initially 28 °C; targets 28 → 30 → 28 °C at 11 and 52 s; PWM ±255; q(0) = 0; anti-windup on; Δt = 0.025 s. Only mode and gains change.

**Model choice:** G was adjusted once from 2 to 10 W/°C to reproduce the small high-P peak. G and CT/C are estimates; ambient and τ are reused from Part 3.

**Comparison limit:** the common 28 °C simulation start differs from the experimental starts, especially at low gain.

$$
S=C_T(G+H)+C_mG,\quad\zeta_{2L,P}=\frac{S}{2\sqrt{C_TC_mG(H+P_uK_p)}}
$$

$$
K_{p,crit}=\frac{S^2/(4C_TC_mG)-H}{P_u},\quad K_{i,crit}=\frac{S(H+P_uK_p)}{C_TC_mP_u},\quad\rho_I=K_i/K_{i,crit}
$$

At the heating equilibrium, **Kp,crit = 18.46 PWM/°C**; for PI at Kp = 16, **Ki,crit = 8.118 PWM/(°C·s)**. These are local unsaturated criteria. Negative PWM uses the cooling coefficient during downward transients.

### Two-lump P simulations

![Figure 7. Simulated P, Kp = 5, Ki = 0; ζ₂L,P = 1.719. Stable non-oscillatory.](../figures/module_06/a3/simulation_1.png)

*Figure 7. Simulated P, Kp = 5, Ki = 0; ζ₂L,P = 1.719. Stable non-oscillatory.*

![Figure 8. Simulated P, Kp = 20, Ki = 0; ζ₂L,P = 0.964. Stable underdamped.](../figures/module_06/a3/simulation_2.png)

*Figure 8. Simulated P, Kp = 20, Ki = 0; ζ₂L,P = 0.964. Stable underdamped.*

### Two-lump simulations 3–4

![Figure 9. Simulated P, Kp = 40, Ki = 0; ζ₂L,P = 0.697. Stable underdamped.](../figures/module_06/a3/simulation_3.png)

*Figure 9. Simulated P, Kp = 40, Ki = 0; ζ₂L,P = 0.697. Stable underdamped.*

![Figure 10. Simulated PI, Kp = 16, Ki = 0.1; Ki,crit = 8.118; ρI = 0.012. Stable non-oscillatory.](../figures/module_06/a3/simulation_4.png)

*Figure 10. Simulated PI, Kp = 16, Ki = 0.1; Ki,crit = 8.118; ρI = 0.012. Stable non-oscillatory.*

### Two-lump simulations 5–6

![Figure 11. Simulated PI, Kp = 16, Ki = 0.5; Ki,crit = 8.118; ρI = 0.062. Stable non-oscillatory.](../figures/module_06/a3/simulation_5.png)

*Figure 11. Simulated PI, Kp = 16, Ki = 0.5; Ki,crit = 8.118; ρI = 0.062. Stable non-oscillatory.*

![Figure 12. Simulated PI, Kp = 16, Ki = 2; Ki,crit = 8.118; ρI = 0.246. Stable underdamped.](../figures/module_06/a3/simulation_6.png)

*Figure 12. Simulated PI, Kp = 16, Ki = 2; Ki,crit = 8.118; ρI = 0.246. Stable underdamped.*

### Guided comparison answers

**Best matches:** high P (run 3) reproduces the small decaying peak below target; intermediate PI (run 5) reproduces the smooth approach close to target. Neither match establishes settling.

**P:** Kp = 5, 20, 40 lie below, near, and above Kp,crit. Their ζ values are 1.719, 0.964, and 0.697. Higher gain speeds response and lowers damping. All are stable; positive-parameter two-lump P cannot become marginally stable or unstable.

**PI:** ρI = 0.012, 0.062, 0.246: all stable. Runs 4–5 have real poles; run 6 is underdamped. Real-pole PI can still overshoot because q starts away from equilibrium.

Increasing Ki strengthens correction but increases ringing. Marginal stability is at ρI = 1; instability is above 1. Our retained gains stay below this boundary.

**Agreement:** stronger PI correction reduces early error, then produces overshoot.

| Comparison (up/down) | Experiment | Simulation |
| --- | --- | --- |
| High-P rise time | 6.40 / 6.05 s | 9.05 / 11.53 s |
| High-PI overshoot | 38 / 43% | 46.8 / 57.7% |

**Disagreement:** exact speed and overshoot do not match. Different starting states and estimated internal parameters limit agreement. No recorded growing or sustained oscillation contradicts the predicted stability in these windows.

### Controlled checks

• **One-lump PI:** higher Ki lowers ζ; higher Kp raises ζ; doubling C divides ζ by √2.
• **Two-lump practice:** Kp = 60, 105, 160 gives ζ ≈1.31, 1.00, 0.81. Raising G from 35 to 70 increases damping; a more equal mass split lowers damping.

**Simulated saturation:** the Ki = 3 practice run comes within 0.01 PWM of ±255 at 191.8 s. Early growth shows linear instability; later output limiting and anti-windup bound the response. This was not experimental saturation.

## Data, code, and modeling checkpoint

Experimental sources: six October 14 CSVs in the Part 7 data directory. Figures plot reported signed PWM alongside requested PWM; telemetry reports the previous interval’s output. Simulation data, metrics, and calculations are reproducible with build_a3.py. Halving simulation Δt changes temperature by less than 0.0022 °C in the six retained runs.

Local files: [analysis/build script](../../code/module6/A3/build_a3.py); [experimental metrics](../../code/module6/A3/results/experimental_metrics.csv); [settings and stability calculations](../../code/module6/A3/results/analysis.json).

**Raw recordings:** [Run 1 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run1_20261014_105029_872226.csv) · [Run 2 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run2_20261014_105202_883449.csv) · [Run 3 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run3_20261014_105335_877556.csv) · [Run 4 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run4_20261014_105508_891380.csv) · [Run 5 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run5_20261014_105641_882344.csv) · [Run 6 raw CSV](../../code/module6/Part1/P7_experimental_goldilocks/data/screening_run6_20261014_105814_945122.csv)

GitHub modeling checkpoint: [73d29c9](https://github.com/hasanm720/Module1/commit/73d29c92752bb946929633de97bcb714192e3ba2) (existing Part 3/4 checkpoint). This checkpoint predates the six runs and A3; the new A3 files have not been committed or pushed.

Assignment: [Lab 6 — A3](https://sethfraden.github.io/Phys39F26-course/labs/lab-06/#a3-feedback-data-and-lumped-model-memo). Two-lump protocol: [Lab 7 — six simulation runs](https://sethfraden.github.io/Phys39F26-course/labs/lab-07/#make-the-six-two-lump-goldilocks-plots).

## 4. PI steady state, assumptions, and windup

$$
\dot q=e=0\ \Rightarrow\ T_{ss}=T_{set}=55\ ^\circ\mathrm{C},\quad u_P=0,\quad u_I=H(55-T_{amb})/P_u
$$

**Ideal result: 55 °C.** At equilibrium q is constant, so e = 0. The integral retains the heat-loss-balancing output while P becomes zero.

Required heating command: (55 − 24.220)/0.5311 = **57.95 PWM**, within ±255 in this model. This is a prediction, not a 55 °C experiment.

**Conditions:** stable feedback, sufficient heating power, no persistent saturation or shutdown, Ki > 0 with continued integration, and accurate/timely measurement. Sensor bias shifts the actual temperature away from the indicated 55 °C.

**Windup:** stored error keeps growing while PWM is capped, causing overshoot and slow recovery.

**Anti-windup:** reject updates that push farther beyond the limit; accept updates that bring the request back.

**Reset:** clearing q removes the balancing heat command. Temperature initially falls while I rebuilds.

## 5. Model limits and gain selection

**Complete this question only after completing Part II of Module 6.**

$$
T(t)-T_{ss}=[T(0)-T_{ss}]\exp[-(1+\chi K_p)t/\tau]
$$

**One-lump limit:** the positive, decaying exponential cannot cross its own steady temperature. From below the steady temperature and target, P cannot overshoot the target or ring.

$$
C_T\dot T_T=P_u u-G(T_T-T_m),\qquad C_m\dot T_m=G(T_T-T_m)-H(T_m-T_{amb})
$$

**Two-lump lag:** the TEC heats its own mass first; G then transfers heat to the measured mass. Stored TEC energy keeps changing Tm after the command falls, allowing overshoot and decaying oscillations.

**Selected P gain:** Kp = 20 PWM/°C is close to Kp,crit = 18.46, with ζ = 0.964: fast response near critical damping. It retains droop; gain 40 reduces droop further but has a more pronounced transient peak.

**Selected PI gains:** Kp = 16 PWM/°C and Ki = 0.5 PWM/(°C·s), with ρI = 0.062, well below 1. Run 5 approached both targets with little overshoot. Ki = 0.1 corrected too slowly; Ki = 2 produced larger excursions. These are provisional choices because the recordings did not establish full settling.

**Next model improvement:** include the ≈0.57 s measurement/command delay. Temperature-dependent TEC coefficients and thermal contact changes may also matter.

