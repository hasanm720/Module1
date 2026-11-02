"""Draw the Module 7 bench wiring (thermistor dividers, Uno, IBT_2 H-bridge, TEC).

    python code/module7/wiring_diagram.py   ->  docs/figures/module_07/wiring_diagram.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

OUT = Path(__file__).resolve().parents[2] / 'docs/figures/module_07/wiring_diagram.png'
RED, BLK, SIG, PWM = '#c62828', '#222222', '#1565c0', '#ef6c00'
# Column per analog pin: (pin, wire tag, role)
SENSORS = [('A0', 'T6', 'rod, highest'), ('A1', 'T5', 'TEC base'), ('A2', 'T4', 'rod'),
           ('A3', 'T3', 'rod'), ('A4', 'T2', 'rod'), ('A5', 'T1', 'rod, x = 0')]
RAIL_5V, RAIL_GND = 11.0, 0.8

fig, ax = plt.subplots(figsize=(17, 11))
ax.set_xlim(0, 20.9); ax.set_ylim(-0.2, 12.4); ax.axis('off')


def wire(xs, ys, color=BLK, lw=2):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle='round', zorder=2)


def dot(x, y, color=BLK):
    ax.add_patch(Circle((x, y), 0.07, color=color, zorder=4))


def box(x0, y0, x1, y1, title, color='#eceff1'):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=color, ec=BLK, lw=2, zorder=1))
    ax.text((x0 + x1) / 2, y1 + 0.15, title, ha='center', va='bottom', fontsize=12, weight='bold')


def pin(x, y, name, side):
    ax.text(x + (0.12 if side == 'left' else -0.12), y, name, ha='left' if side == 'left' else 'right',
            va='center', fontsize=10, family='monospace', zorder=5)


def test_point(x, y, n):
    ax.add_patch(Circle((x, y), 0.22, fc='#fff176', ec=BLK, lw=1.5, zorder=6))
    ax.text(x, y, str(n), ha='center', va='center', fontsize=10, weight='bold', zorder=7)


# Breadboard rails
wire([0.4, 13.3], [RAIL_5V] * 2, RED, 4)
wire([0.4, 9.0], [RAIL_GND] * 2, BLK, 4)
ax.text(0.4, RAIL_5V + 0.2, '5 V rail (breadboard), fed from Uno 5V. Check that it is not split mid-board!',
        color=RED, fontsize=10, va='bottom')
ax.text(0.4, RAIL_GND - 0.25, 'GND rail (breadboard)', fontsize=10, va='top')

# Uno
box(9.3, 2.6, 11.6, 10.2, 'Arduino Uno')
node_y = {}
for i, (p, tag, role) in enumerate(SENSORS):
    # Resistors all sit above y = 9.5 and thermistors below y = 5.5, so each
    # signal wire (at its own height in between) crosses only plain wires.
    x, y = 0.9 + 1.35 * i, 8.9 - 0.55 * i
    node_y[p] = y
    wire([x, x], [RAIL_5V, 10.6], RED); dot(x, RAIL_5V, RED)
    ax.add_patch(Rectangle((x - 0.17, 9.5), 0.34, 1.1, fc='white', ec=BLK, lw=1.5, zorder=3))
    ax.text(x + 0.22, 10.05, '100 kΩ', rotation=90, va='center', fontsize=8)
    wire([x, x], [9.5, 5.5]); dot(x, y, SIG)
    ax.add_patch(Rectangle((x - 0.17, 3.8), 0.34, 1.7, fc='#ffe0b2', ec=BLK, lw=1.5, zorder=3))
    ax.plot([x - 0.3, x + 0.3], [3.95, 5.35], color=BLK, lw=1, zorder=4)
    ax.text(x + 0.22, 4.65, 'NTC 100 k', rotation=90, va='center', fontsize=8)
    wire([x, x], [3.8, RAIL_GND]); dot(x, RAIL_GND)
    ax.text(x, 11.75, f'{tag}\n{role}', ha='center', va='bottom', fontsize=9, weight='bold')
    wire([x, 9.3], [y, y], SIG, 1.6)
    pin(9.3, y, p, 'left')
# Uno power to the rails
wire([9.0, 9.0, 9.3], [RAIL_5V, 9.7, 9.7], RED, 2.5); dot(9.0, RAIL_5V, RED); pin(9.3, 9.7, '5V', 'left')
wire([9.0, 9.0, 9.3], [RAIL_GND, 3.0, 3.0], BLK, 2.5); dot(9.0, RAIL_GND); pin(9.3, 3.0, 'GND', 'left')

# IBT_2 control header
box(13.7, 2.6, 16.4, 10.2, 'IBT_2 (BTS7960) H-bridge')
hdr = {'VCC': 9.6, 'R_EN': 9.0, 'L_EN': 8.4, 'RPWM': 7.4, 'LPWM': 6.6, 'R_IS': 5.6, 'L_IS': 5.0, 'GND': 3.6}
for name, y in hdr.items():
    pin(13.7, y, name, 'left')
for name, x in (('VCC', 12.5), ('R_EN', 12.8), ('L_EN', 13.1)):
    wire([x, x, 13.7], [RAIL_5V, hdr[name], hdr[name]], RED, 2.5); dot(x, RAIL_5V, RED)
pin(11.6, 7.4, 'D9', 'right'); pin(11.6, 6.6, 'D10', 'right'); pin(11.6, 3.6, 'GND', 'right')
wire([11.6, 13.7], [7.4, 7.4], PWM, 2.5); wire([11.6, 13.7], [6.6, 6.6], PWM, 2.5)
ax.text(12.65, 7.5, 'HEAT', color=PWM, ha='center', va='bottom', fontsize=9, weight='bold')
ax.text(12.65, 6.7, 'COOL', color=PWM, ha='center', va='bottom', fontsize=9, weight='bold')
wire([11.6, 13.7], [3.6, 3.6], BLK, 2.5)
ax.text(12.65, 3.7, 'common GND', ha='center', va='bottom', fontsize=8)
ax.text(13.85, 4.3, 'R_IS, L_IS: not connected', fontsize=8, style='italic')

# Power side: supply and TEC
for name, y in (('B+', 9.3), ('B−', 8.5), ('M+', 5.6), ('M−', 4.8)):
    pin(16.4, y, name, 'right')
box(17.6, 8.0, 20.2, 10.0, 'ALITO 12 V 10 A supply', '#e3f2fd')
pin(17.6, 9.3, 'V+', 'left'); pin(17.6, 8.5, 'V−', 'left')
wire([16.4, 17.6], [9.3, 9.3], RED, 3); wire([16.4, 17.6], [8.5, 8.5], BLK, 3)
box(17.6, 4.2, 20.2, 6.2, 'TEC (Peltier)', '#fce4ec')
wire([16.4, 17.6], [5.6, 5.6], RED, 3); wire([16.4, 17.6], [4.8, 4.8], BLK, 3)
ax.text(18.9, 3.9, 'T5 thermistor in TEC base', ha='center', va='top', fontsize=9)

# Test points (measure with GUI sending HEAT 255)
for n, (x, y) in enumerate([(20.5, 8.9), (17.0, 8.9), (13.4, 10.1), (13.4, 8.8), (12.0, 7.85), (17.0, 6.05)], 1):
    test_point(x, y, n)
tests = ['Test with the multimeter while the GUI sends HEAT 255:',
         '1  Supply V+ to V−: ~12 V',
         '2  IBT B+ to B−: ~12 V',
         '3  IBT VCC to GND: ~5 V   (0 V = dead/split rail)',
         '4  R_EN and L_EN to GND: ~5 V each',
         '5  Uno D9 to GND: ~5 V   (PWM 255 = always high)',
         '6  IBT M+ to M−: ~12 V   (= TEC drive)',
         'The first test that fails marks the fault.']
ax.text(13.7, 2.2, '\n'.join(tests), fontsize=9.5, va='top', family='monospace',
        bbox=dict(fc='#fffde7', ec='#999', boxstyle='round,pad=0.4'))
ax.set_title('Module 7 wiring: six thermistor dividers, Arduino Uno, IBT_2 H-bridge, TEC', fontsize=15, weight='bold')

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches='tight')
print(OUT)
