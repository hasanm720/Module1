"""Build A4 (finite-length and Biot-number predictions for the course rod); no hardware I/O.

    /opt/anaconda3/envs/phys39a/bin/python code/module7/A4/build_a4.py [--commit HASH]

Writes docs/assessments/a4_finite_length_biot.md and docs/assessments/A4_Chen.pdf.
Dependencies: numpy, matplotlib, reportlab (same as A3).
"""
from pathlib import Path
import argparse
import math
import re
import subprocess
import tempfile
import xml.sax.saxutils as xml

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak, HRFlowable, KeepTogether)
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'docs/assessments'
FIGURES = ROOT/'docs/figures/module_07/a4'
DATE = 'November 2, 2026'
REPO = 'https://github.com/hasanm720/Module1'

# Measured course rod (docs/module_notes/module_07_rod_instrument.md, sections 1-2).
D, U_D = 12.705e-3, 0.025e-3          # m
L, U_L = 0.2832, 0.002                # m, T1 hole to tip
X = np.array([0, 50.30, 100.96, 150.32, 200.95])/1e3  # m, T1, T2, T3, T4, T6
TAGS = ['T1', 'T2', 'T3', 'T4', 'T6']
H = 10.0                              # W m^-2 K^-1, provisional still air (lab-08)
K_RANGE = (166.0, 172.0)              # W m^-1 K^-1, 6061-T6, Lienhard Table A.1, 0-100 C
EPS_CRIT = 0.05

# Problem 1.3: q = 5000 W/m^2 through 1 cm, cold side -40 C. k from Lienhard Tables A.1/A.2.
Q13, L13, TC13 = 5000.0, 0.01, -40.0
MATERIALS = [('Pure silver (99.99+%)', 427, 'Table A.1, 20 °C'),
             ('Pure aluminum', 237, 'Table A.1, 20 °C'),
             ('Mild steel (0.5% C)', 54, 'Table A.1, 20 °C'),
             ('Ice', 2.215, 'Table A.2, 0 °C'),
             ('Spruce', 0.11, 'Table A.2, 20 °C'),
             ('Insulation (85% magnesia)', 0.067, 'Table A.2, 38 °C'),
             ('Silica aerogel', 0.024, 'Table A.2, 0 °C')]


def fin_m(h, k): return math.sqrt(4*h/(k*D))          # m = sqrt(hP/(kA)), P/A = 4/d
def theta_fin(x, m): return np.cosh(m*(L - x))/np.cosh(m*L)
def theta_inf(x, m): return np.exp(-m*x)
def eps_t(x, m): return np.abs(theta_fin(x, m) - theta_inf(x, m))/np.abs(theta_fin(x, m))


def span(a, b, fmt):
    lo, hi = sorted((a, b))
    return f'{lo:{fmt}}–{hi:{fmt}}'


def sci(v):
    e = math.floor(math.log10(abs(v)))
    return f'{v/10**e:.2f} × 10<super>{e}</super>'


STYLES = {
    'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=10),
    'title': ParagraphStyle('title', fontName='Helvetica', fontSize=20.25, leading=25, spaceAfter=8),
    'heading': ParagraphStyle('heading', fontName='Helvetica', fontSize=15, leading=19, spaceBefore=5, spaceAfter=9),
    'sub': ParagraphStyle('sub', fontName='Helvetica-Bold', fontSize=10.5, leading=15, spaceBefore=9, spaceAfter=7),
    'caption': ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=8.75, leading=12, spaceAfter=14),
    'table': ParagraphStyle('table', fontName='Helvetica', fontSize=9, leading=12),
}
WIDTH = 511
blocks = []


def add(kind, value, extra=None): blocks.append((kind, value, extra))
def p(text): add('p', text)
def h(text): add('h', text)
def sub(text): add('sub', text)
def eq(latex): add('eq', latex)
def table(head, rows, widths=None): add('table', (head, rows), widths)
def figure(path, caption): add('figure', path, caption)
def page(): add('page', None)


def make_figure(m_lo, m_hi):
    FIGURES.mkdir(parents=True, exist_ok=True)
    xx = np.linspace(0, L, 300)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.9))
    for m, ls in ((m_lo, '-'), (m_hi, '--')):
        a1.plot(xx*1e3, theta_fin(xx, m), color='#1f77b4', ls=ls, label=f'finite, m = {m:.2f} m⁻¹')
        a1.plot(xx*1e3, theta_inf(xx, m), color='#d62728', ls=ls, label=f'semi-infinite, m = {m:.2f} m⁻¹')
        a2.plot(xx*1e3, 100*eps_t(xx, m), color='#444', ls=ls, label=f'm = {m:.2f} m⁻¹')
    for x, tag in zip(X, TAGS):
        for ax in (a1, a2):
            ax.axvline(x*1e3, color='#bbb', lw=0.8, zorder=0)
        a1.text(x*1e3, 1.02, tag, ha='center', fontsize=8)
    a2.axhline(100*EPS_CRIT, color='#b00020', ls=':', label='5% criterion')
    a1.set(xlabel='x from T1 (mm)', ylabel='Θ = (T − T∞)/(T₀ − T∞)', ylim=(0, 1.08), xlim=(0, L*1e3))
    a2.set(xlabel='x from T1 (mm)', ylabel='ε_T (%)', xlim=(0, L*1e3))
    a1.legend(fontsize=7.5); a2.legend(fontsize=7.5)
    a1.set_title('Predicted profiles (h = 10 W m⁻² K⁻¹)', fontsize=10)
    a2.set_title('Finite-length error of the semi-infinite model', fontsize=10)
    for ax in (a1, a2): ax.grid(alpha=0.3)
    fig.tight_layout()
    path = FIGURES/'a4_profiles.png'
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def prepare_report(commit):
    # ---------- numbers ----------
    m_hi, m_lo = fin_m(H, K_RANGE[0]), fin_m(H, K_RANGE[1])   # smaller k -> larger m
    rel = 0.5*U_D/D   # m ∝ d^-1/2
    bi_lo, bi_hi = H*D/(4*K_RANGE[1]), H*D/(4*K_RANGE[0])
    fig_path = make_figure(m_lo, m_hi)

    add('title', 'A4 — Finite Length and Biot Number for the Course Rod')
    p(f'PHYS 39 · Module 7 · <b>Kyle Chen</b> (individual) · Assignment A4 · {DATE}<br/>'
      f'Repository: <link href="{REPO}" color="#1764ab">{REPO}</link> (branch mainv2) · '
      f'Git commit: <b>{commit}</b>')
    p('Inputs are the measured rod geometry and sensor positions recorded before heating '
      '(docs/module_notes/module_07_rod_instrument.md), a literature range for k, and the provisional '
      'still-air coefficient h = 10 W m<super>−2</super> K<super>−1</super>. All values below are predictions; '
      'A4 does not use the Part III temperature-profile data.')

    # ---------- Part 1 ----------
    h('Part 1 — Apply Fourier\'s law (Lienhard Problem 1.3)')
    p('<b>Problem.</b> A slab 1 cm thick carries a steady heat flux q = 5000 W/m² and its cold side is at '
      '−40 °C. Find the temperature rise to the hot side for seven materials and identify unreasonable cases.')
    p('<b>Method.</b> In steady one-dimensional conduction with no heat generation, the flux is the same at every '
      'plane, so Fourier\'s law integrates across the slab with constant k:')
    eq(r'q=-k\frac{dT}{dx}\;\Rightarrow\;q=k\frac{\Delta T}{L}\;\Rightarrow\;\Delta T=\frac{qL}{k}')
    p('Units: (W m<super>−2</super>)(m)/(W m<super>−1</super> K<super>−1</super>) = K, so ΔT is in kelvin '
      '(equivalently °C for a difference). <b>Sample calculation (silver):</b> '
      'ΔT = (5000 W/m²)(0.01 m)/(427 W/m·K) = <b>0.117 K</b>, matching the textbook check value.')
    rows = []
    for name, k, src in MATERIALS:
        dT = Q13*L13/k
        rows.append([name, f'{k:g}', src, f'{dT:.3g}' if dT < 1000 else f'{dT:.0f}', f'{TC13 + dT:.1f}'])
    table(['Material', 'k (W/m·K)', 'Source (Lienhard)', 'ΔT (K)', 'Hot side (°C)'], rows, [140, 60, 105, 60, 70])
    p('<b>Physical judgment.</b> The metals need well under 1 K, and ice warms to about −17 °C, still frozen, so '
      'those four cases are reasonable. The last three are not:')
    p('• <b>Spruce:</b> the hot face would reach about 415 °C, far above the temperature at which wood chars and '
      'ignites. The slab could not survive this flux.<br/>'
      '• <b>85% magnesia:</b> the hot face would reach about 706 °C, beyond the service temperature of this '
      'insulation, which is intended for moderate-temperature pipe lagging.<br/>'
      '• <b>Silica aerogel:</b> a rise of about 2080 K puts the hot face above 2000 °C, past the melting point of '
      'silica; the aerogel structure would collapse long before.')
    p('These cases also break the calculation\'s own assumption: k was taken as constant, at one tabulated '
      'temperature, but over rises of hundreds of kelvin k changes and the material itself changes. The lesson is '
      'the one we apply to our TEC: a large heat flux can only be removed through a good conductor. If the path '
      'from a heat source to its sink conducts poorly, the source temperature must climb until it fails, which is '
      'why the TEC is protected with a heat sink and an overtemperature shutdown.')

    # ---------- Part 2 ----------
    page()
    h('Part 2 — Stationary finite-rod model (Lienhard §4.5)')
    p('<b>Assumptions.</b> Steady state; constant k and h; uniform cross section A and perimeter P; no internal '
      'heat generation; uniform ambient temperature T∞; and a transverse Biot number Bi⊥ = h(A/P)/k ≪ 1, so each '
      'cross section has a single temperature T(x) (Lienhard eqn. 4.27; checked in Part 4).')
    p('<b>Energy balance on a slice</b> of length δx: heat conducted in at x equals heat conducted out at x + δx '
      'plus heat convected from the side area Pδx (eqn. 4.28):')
    eq(r'-kA\left.\frac{dT}{dx}\right|_{x}=-kA\left.\frac{dT}{dx}\right|_{x+\delta x}+h(P\,\delta x)(T-T_\infty)')
    p('Divide by kA δx and let δx → 0. The difference quotient becomes the second derivative, and since T∞ is '
      'constant, d²T/dx² = d²(T − T∞)/dx² (eqns. 4.29–4.30). With θ = T − T∞:')
    eq(r'\frac{d^2\theta}{dx^2}=m^2\theta,\qquad m^2=\frac{hP}{kA}\quad[\mathrm{m^{-2}}]')
    p('Dimension check: hP/(kA) has units (W m<super>−2</super> K<super>−1</super>)(m)/'
      '[(W m<super>−1</super> K<super>−1</super>)(m²)] = m<super>−2</super>, so m is an inverse length and mL is '
      'dimensionless. For a round rod, P/A = 4/d, so m² = 4h/(kd).')
    p('<b>Dimensionless form.</b> With Θ = θ/θ₀ (θ₀ = T₀ − T∞) and ξ = x/L, the equation becomes '
      'd²Θ/dξ² = (mL)²Θ (eqn. 4.34), whose general solution is (eqn. 4.35):')
    eq(r'\Theta=C_1e^{mL\xi}+C_2e^{-mL\xi}')
    p('<b>Boundary conditions.</b><br/>'
      '1. <b>Base, ξ = 0: Θ = 1</b> (fixed temperature, Dirichlet). Physically the base is held at T₀; for our rod '
      'this is the temperature measured by the T1 thermistor at x = 0, not the TEC.<br/>'
      '2. <b>Tip, ξ = 1: dΘ/dξ = 0</b> (insulated tip, Neumann). No heat crosses the end face, because its area '
      'A is small compared with the side area PL and its heat loss is neglected.')
    p('Substituting the general solution into both conditions gives C₁ + C₂ = 1 and C₁e<super>mL</super> − '
      'C₂e<super>−mL</super> = 0 (eqn. 4.37). Solving:')
    eq(r'C_1=\frac{e^{-mL}}{2\cosh mL},\qquad C_2=\frac{e^{mL}}{2\cosh mL}')
    p('Inserting the constants and using cosh z = (e<super>z</super> + e<super>−z</super>)/2 gives the finite, '
      'insulated-tip profile (eqn. 4.41), its tip value (eqn. 4.45), and the base heat flow (eqns. 4.42–4.43):')
    eq(r'\Theta=\frac{\cosh[mL(1-\xi)]}{\cosh mL}=\frac{\cosh[m(L-x)]}{\cosh mL},\quad\Theta_{tip}=\frac{1}{\cosh mL},\quad Q_0=\sqrt{kAhP}\,\theta_0\tanh mL')

    # ---------- Part 3 ----------
    page()
    h('Part 3 — Semi-infinite limit and the provisional finite-length prediction')
    sub('Lienhard Problem 4.12: the semi-infinite limit')
    p('Use the general solution θ = C₁e<super>mx</super> + C₂e<super>−mx</super> (eqn. 4.35, dimensional) with '
      'T(0) = T₀ and T(L) = T∞, i.e. θ(0) = θ₀ and θ(L) = 0:')
    eq(r'C_1+C_2=\theta_0,\quad C_1e^{mL}+C_2e^{-mL}=0\;\Rightarrow\;\frac{\theta}{\theta_0}=\frac{\sinh[m(L-x)]}{\sinh mL}')
    p('For fixed x and L → ∞, sinh[m(L − x)]/sinh(mL) → e<super>m(L−x)</super>/e<super>mL</super>, so')
    eq(r'\lim_{L\to\infty}\Theta=e^{-mx}\qquad(\mathrm{eqn.\ 4.50})')
    p('The insulated-tip profile reaches the same limit, since cosh[m(L − x)]/cosh(mL) → e<super>−mx</super> when '
      'mL ≫ 1. The semi-infinite model keeps the base condition but <b>loses the tip condition</b>; the rod is '
      'assumed so long that the tip has fallen to T∞. Lienhard recommends mL ≳ 5 for temperatures and mL ≳ 3 '
      'for Q₀.')
    sub('Example 4.8 and Problem 4.20: the cost of approximating the tip')
    ml8, bi8 = 0.8656, 0.0468
    tip_exact = (1)/(math.cosh(ml8) + (bi8/ml8)*math.sinh(ml8))
    tip_ins = 1/math.cosh(ml8)
    q_ins = math.tanh(ml8)
    q_exact = (bi8/ml8 + math.tanh(ml8))/(1 + (bi8/ml8)*math.tanh(ml8))
    p(f'Example 4.8 (2 cm aluminum rod, 8 cm long, k = 205 W/m·K, h ≈ h<sub>L</sub> = 120 W/m²K) has mL = {ml8} '
      f'and tip Biot number Bi<sub>ax</sub> = h<sub>L</sub>L/k = {bi8}. A convecting tip (eqn. 4.48) gives '
      f'Θ<sub>tip</sub> = {tip_exact:.4f}; the insulated-tip approximation gives {tip_ins:.4f}, about 4% high. '
      f'For the heat flow (Problem 4.20), the insulated tip gives Q₀/(√(kAhP)θ₀) = tanh mL = {q_ins:.4f}, while '
      f'eqn. 4.49 gives (Bi<sub>ax</sub>/mL + tanh mL)/(1 + (Bi<sub>ax</sub>/mL) tanh mL) = {q_exact:.4f}. '
      f'The approximation underestimates Q₀ by <b>{100*(q_exact - q_ins)/q_exact:.2f}%</b> (book: 3.67%).')
    bi_ax = H*L/((K_RANGE[0] + K_RANGE[1])/2)
    mm = (m_lo + m_hi)/2
    tip_ins_r = 1/math.cosh(mm*L)
    tip_conv_r = 1/(math.cosh(mm*L) + (bi_ax/(mm*L))*math.sinh(mm*L))
    p(f'For <b>our rod</b> with h<sub>L</sub> ≈ h = 10 W/m²K, Bi<sub>ax</sub> = hL/k ≈ {bi_ax:.4f} and '
      f'Bi<sub>ax</sub>/mL ≈ {bi_ax/(mm*L):.3f}, so the insulated tip predicts Θ<sub>tip</sub> = {tip_ins_r:.3f} '
      f'compared with {tip_conv_r:.3f} for a convecting tip, a {100*(tip_ins_r - tip_conv_r)/tip_conv_r:.1f}% '
      'difference. The insulated-tip model is adequate for our rod at this h.')
    sub('Provisional prediction for the course rod')
    p(f'<b>Inputs:</b> d = {D*1e3:.3f} ± {U_D*1e3:.3f} mm; L = {L*1e3:.1f} ± {U_L*1e3:.0f} mm (T1 hole to tip); '
      f'sensor positions x = {", ".join(f"{x*1e3:.2f}" for x in X)} mm (± 0.5 mm) for '
      f'{", ".join(TAGS)}; h = {H:g} W/m²K (provisional, still air); k = {K_RANGE[0]:g}–{K_RANGE[1]:g} W/m·K '
      '(6061-T6, Lienhard Table A.1, 0–100 °C, which spans our 20–45 °C operating range); error criterion '
      'ε<sub>T</sub> &lt; 5% at every sensor.')
    eq(r'm=\sqrt{\frac{4h}{kd}},\qquad \varepsilon_T(x)=\frac{|\Theta_{finite}-\Theta_\infty|}{|\Theta_{finite}|}')
    p(f'<b>m = {m_lo:.2f}–{m_hi:.2f} m<super>−1</super></b> (decay length 1/m = {100/m_hi:.1f}–{100/m_lo:.1f} cm; '
      f'the ±{U_D*1e3:.3f} mm diameter uncertainty adds only ±{100*rel:.1f}% to m). '
      f'<b>mL = {m_lo*L:.2f}–{m_hi*L:.2f}</b>, far below Lienhard\'s mL ≳ 5.')
    rows = []
    for tag, x in zip(TAGS, X):
        rows.append([tag, f'{x*1e3:.2f}', span(theta_fin(x, m_lo), theta_fin(x, m_hi), '.3f'),
                     span(theta_inf(x, m_hi), theta_inf(x, m_lo), '.3f'),
                     span(100*eps_t(x, m_lo), 100*eps_t(x, m_hi), '.1f'),
                     'yes' if eps_t(x, m_lo) < EPS_CRIT and eps_t(x, m_hi) < EPS_CRIT else 'no'])
    rows.append(['tip', f'{L*1e3:.1f}', span(1/math.cosh(m_hi*L), 1/math.cosh(m_lo*L), '.3f'),
                 span(theta_inf(L, m_hi), theta_inf(L, m_lo), '.3f'),
                 span(100*eps_t(L, m_lo), 100*eps_t(L, m_hi), '.1f'), 'no'])
    table(['Sensor', 'x (mm)', 'Θ finite', 'Θ semi-infinite', 'ε_T (%)', 'ε_T < 5%?'], rows, [50, 60, 95, 105, 80, 70])
    figure(fig_path, 'Figure 1. Predicted finite (insulated-tip) and semi-infinite profiles for the course rod '
           f'at the two ends of the k range (left), and the finite-length error ε_T(x) (right). '
           'Vertical lines mark the five rod sensors.')
    p('<b>Conclusion (length):</b> the course rod is <b>not</b> adequately semi-infinite over the measured region. '
      'ε<sub>T</sub> stays below 5% only at T1 and T2; it reaches about 10% at T3, 17% at T4 and 27% at T6, and the '
      f'semi-infinite model would put the tip at Θ ≈ {theta_inf(L, mm):.2f} instead of {1/math.cosh(mm*L):.2f} '
      f'(ε<sub>T</sub> ≈ {100*eps_t(L, mm):.0f}%). The stationary data '
      'should therefore be fitted with the finite-length model. This conclusion depends on the measured L and '
      'sensor positions, the provisional h, the k range, and the 5% criterion. Because mL ∝ √h, a larger true h '
      f'would make the rod look longer: mL would need to grow by a factor of about {5/(mm*L):.1f} '
      f'(h about {(5/(mm*L))**2:.0f} times larger) to reach mL ≈ 5.')

    # ---------- Part 4 ----------
    page()
    h('Part 4 — Provisional one-dimensional (radius) prediction')
    p('The transverse Biot number compares conduction resistance across the radius with convection resistance at '
      'the surface (eqn. 4.27). For a circular rod A/P = R/2 = d/4:')
    eq(r'Bi_\perp=\frac{h(A/P)}{k}=\frac{hR}{2k}=\frac{hd}{4k}')
    p(f'With h = 10 W/m²K, d = {D*1e3:.3f} mm and k = {K_RANGE[0]:g}–{K_RANGE[1]:g} W/m·K: '
      f'<b>Bi⊥ = {sci(bi_lo)} – {sci(bi_hi)}</b> (dimensionless: (W m<super>−2</super> K<super>−1</super>)(m)/'
      '(W m<super>−1</super> K<super>−1</super>)).')
    p(f'<b>Conclusion (radius):</b> Bi⊥ is about 500 times smaller than the usual 0.1 threshold, so the '
      'temperature across any cross section is uniform to within a fraction of a percent of the local '
      'rod-to-air difference. <b>Each cross section is adequately represented by one temperature.</b> This is a '
      'separate question from Part 3: the rod is thin enough to be one-dimensional, but not long enough to be '
      'semi-infinite.')
    sub('Application: a heat sink in still air vs forced airflow')
    m10, m100 = fin_m(10, 169), fin_m(100, 169)
    p('Forced airflow thins the thermal boundary layer at the fin surface, so <b>forced flow has the larger '
      'convective coefficient h</b>; still air relies only on buoyancy-driven natural convection. Since '
      'm = √(hP/(kA)), the decay length scales as')
    eq(r'\frac{1}{m}=\sqrt{\frac{kA}{hP}}\;\propto\;h^{-1/2}')
    p(f'so a larger h <b>shortens</b> the decay length: heat leaves the fin closer to its base, and the far part of '
      f'the fin runs nearer the air temperature. For our rod, 1/m ≈ {100/m10:.0f} cm at h = 10 W/m²K but only '
      f'≈ {100/m100:.0f} cm at h = 100 W/m²K (a 10× increase in h shortens 1/m by √10 ≈ 3.2). The same heat sink '
      'therefore removes more heat with a fan, but a long fin gains less, because its outer part contributes '
      'little once 1/m is short. Bi⊥ also grows in proportion to h, yet even at 100 W/m²K it is only about '
      f'{sci(100*D/(4*169))}, so the one-dimensional assumption still holds.')
    T_mean = 273.15 + 32.5
    h_rad_bb = 4*5.670e-8*T_mean**3
    p(f'<b>Convection vs radiation (brief).</b> Linearizing radiation about a mean surface temperature of about '
      f'32 °C gives h<sub>rad</sub> = 4εσT̄³ ≈ {h_rad_bb:.1f}ε W/m²K. Bare machined aluminum has a low emissivity '
      f'(roughly ε ≈ 0.05–0.1), so h<sub>rad</sub> ≈ {0.05*h_rad_bb:.1f}–{0.1*h_rad_bb:.1f} W/m²K, small '
      'compared with h ≈ 10 W/m²K for natural convection. Radiation is a minor correction for this rod, but it '
      'would be comparable to natural convection for a black-anodized heat sink (ε ≈ 0.8–0.9), and negligible '
      'compared with forced airflow.')

    h('Sources and reproduction')
    p('Lienhard &amp; Lienhard, <i>A Heat Transfer Textbook</i>, 6th ed.: Problem 1.3; §4.5 eqns. 4.27–4.51; '
      'Example 4.8; Problems 4.12, 4.20; Tables A.1–A.2. Rod geometry and sensor positions: '
      'docs/module_notes/module_07_rod_instrument.md. Build from the repository root (phys39a environment):<br/>'
      '/opt/anaconda3/envs/phys39a/bin/python code/module7/A4/build_a4.py')


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs); self.states = []
    def showPage(self):
        self.states.append(dict(self.__dict__)); self._startPage()
    def save(self):
        count = len(self.states)
        for state in self.states:
            self.__dict__.update(state)
            self.setFont('Helvetica', 6)
            self.drawString(42, 824, 'A4_Chen · a4_finite_length_biot.md')
            self.drawRightString(553, 824, '2026-11-02')
            self.drawCentredString(297.5, 23, f'{self._pageNumber} / {count}')
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def plain(text):
    text = re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>', r'[\2](\1)', text)
    for a, b in (('<br/>', '\n'), ('<b>', '**'), ('</b>', '**'), ('<i>', '*'), ('</i>', '*'),
                 ('<super>', '^'), ('</super>', ''), ('<sub>', '_'), ('</sub>', '')):
        text = text.replace(a, b)
    return text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')


def render():
    temp = Path(tempfile.mkdtemp(prefix='phys39-a4-equations-'))
    story = []; markdown = []; n = 0
    for kind, value, extra in blocks:
        if kind == 'page': story.append(PageBreak()); continue
        if kind in ['title', 'h', 'sub', 'p']:
            style = STYLES[{'title': 'title', 'h': 'heading', 'sub': 'sub', 'p': 'body'}[kind]]
            if kind == 'h': story.append(HRFlowable(width='100%', thickness=.6, color=colors.grey, spaceBefore=4, spaceAfter=8))
            story.append(Paragraph(value, style))
            markdown.append({'title': '# ', 'h': '## ', 'sub': '### ', 'p': ''}[kind] + plain(value) + '\n')
        elif kind == 'eq':
            n += 1; path = temp/f'eq{n}.png'
            fig = plt.figure(figsize=(7.1, .5)); fig.text(.5, .5, '$' + value + '$', ha='center', va='center', fontsize=11)
            fig.savefig(path, dpi=200, bbox_inches='tight', pad_inches=.04); plt.close(fig)
            from PIL import Image as PILImage
            with PILImage.open(path) as im: w, hp = im.size
            dw = min(WIDTH, w*72/200); img = Image(str(path), width=dw, height=dw*hp/w); img.hAlign = 'CENTER'
            story.extend([img, Spacer(1, 7)])
            markdown.append('$$\n' + value + '\n$$\n')
        elif kind == 'table':
            head, rows = value
            widths = extra or [WIDTH/len(head)]*len(head)
            widths = [w*WIDTH/sum(widths) for w in widths]
            cells = [[Paragraph(xml.escape(str(c)), STYLES['table']) for c in row] for row in [head] + rows]
            tab = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
            tab.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eeeeee')),
                                     ('LINEBELOW', (0, 0), (-1, 0), .6, colors.grey),
                                     ('LINEBELOW', (0, 1), (-1, -1), .25, colors.lightgrey),
                                     ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 5),
                                     ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
            story.extend([tab, Spacer(1, 8)])
            markdown.extend(['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join(['---']*len(head)) + ' |'])
            markdown.extend('| ' + ' | '.join(map(str, row)) + ' |' for row in rows)
            markdown.append('')
        elif kind == 'figure':
            img = Image(str(value), width=WIDTH, height=WIDTH*3.9/10)
            story.append(KeepTogether([img, Spacer(1, 3), Paragraph(extra, STYLES['caption'])]))
            markdown.append(f'![{plain(extra)}](../figures/module_07/a4/{value.name})\n\n*{plain(extra)}*\n')
    OUT.mkdir(parents=True, exist_ok=True)
    pdf, md = OUT/'A4_Chen.pdf', OUT/'a4_finite_length_biot.md'
    doc = SimpleDocTemplate(str(pdf), pagesize=(595, 842), leftMargin=42, rightMargin=42, topMargin=40,
                            bottomMargin=40, title='A4 — Finite Length and Biot Number for the Course Rod',
                            author='Kyle Chen')
    doc.build(story, canvasmaker=NumberedCanvas)
    md.write_text('\n'.join(markdown) + '\n')
    print(f'PDF: {pdf}\nMarkdown: {md}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--commit', help='Git commit to cite (default: current HEAD)')
    args = parser.parse_args()
    commit = args.commit or subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True,
                                           text=True, check=True).stdout.strip()
    prepare_report(commit)
    render()
