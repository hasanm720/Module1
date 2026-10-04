"""Build A2 with the A1 reference typography and editable HTML using PySide6.
Run with QT_QPA_PLATFORM=offscreen python build_a2_pdf.py.
"""
from pathlib import Path
import os
import re
import base64
from math_assets import render_equations
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextDocument, QPdfWriter, QPageSize, QPageLayout, QFont, QImage, QPainter, QAbstractTextDocumentLayout
from PySide6.QtCore import QMarginsF, QUrl, QRectF, Qt, QBuffer, QByteArray, QIODevice

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = ROOT / 'docs/module_notes'
conclusion = (HERE / 'part5_answers.md').read_text().split('## 5. Conclusion\n\n')[1].strip()
html = '''<html><head><meta charset="utf-8"><style>
body {font-family: Helvetica; font-size: 10.5pt; color: #000000;}
h1 {font-size: 21pt; font-weight: normal; margin-top: 8px; margin-bottom: 7px;} h2 {font-size: 15.75pt; font-weight: normal; margin-top: 12px; margin-bottom: 10px;}
p {line-height: 22px; margin-top: 0px; margin-bottom: 14px;} .eq {font-family: 'Times New Roman', serif; text-align:center; margin:6px;}
td, th {padding:2px;} .small {font-size:8.5pt;} .caption {font-size:8.5pt; font-style:italic;}
</style></head><body>
<h1>A2 — TEC Heating and Cooling Analysis</h1>
<hr>
<p>Assignment code: A2<br>Module: PHYS39 Module 4<br>Team members: Kyle Chen and Muhammad Hasan</p>
<hr>
<h2>1. Part 4 graph</h2>
<p align="center"><img src="../other_files/module4/P4_Temperature_susceptibility/temperature_vs_signed_pwm.png" width="360" height="260"></p>
<p class="caption">Figure 1. Heating: 0 to +43; cooling: −63 to 0 PWM counts. Points are recorded range midpoints; bars show min–max ranges. Steady-state settling/drift criteria were not documented.</p>
<hr>
<h2>2. Measured slopes and ratio</h2>
<p>Signed-PWM slopes: m<sub>h</sub> = 0.531 °C/count; m<sub>c</sub> = 0.188 °C/count. Their ratio is r = 0.531/0.188 = 2.8245 ≈ 2.82, using rounded graph labels. Both branches are nearly linear with slight local-slope variation.</p>
<hr>
<h2>3. PWM proof and steady-state slope derivation</h2>
<p>During period τ, signed current is I for Dτ and zero otherwise, with nonnegative duty cycle D. Direct integration gives</p>
<p class="eq">⟨i⟩ = (1/τ) ∫<sub>0</sub><sup>τ</sup> i(t) dt = IDτ/τ = DI;<br>
⟨i²⟩ = (1/τ) ∫<sub>0</sub><sup>τ</sup> i(t)² dt = I²Dτ/τ = DI².</p>
<p>Since ⟨i⟩² = D²I² ≠ ⟨i²⟩, Peltier and Joule terms both scale with D at fixed ON-current, consistent with the nearly linear graph. Using ⟨i⟩² incorrectly predicts quadratic Joule heating.</p>
<p>With thermal capacitance C, zero-PWM temperature T<sub>0</sub>, and passive conductance G (including TEC conduction once):</p>
<p class="eq">C dT<sub>o</sub>/dt = Q̇<sub>TEC</sub> − G(T<sub>o</sub> − T<sub>0</sub>);<br>
at steady state, dT<sub>o</sub>/dt = 0 ⇒ G(T<sub>o</sub> − T<sub>0</sub>) = Q̇<sub>TEC</sub>.</p>
<p>At steady state, net heat flow vanishes. For positive ON-state Peltier power P and object-face Joule power J, u = signed PWM/255 and Q̇<sub>TEC</sub> = uP + |u|J:</p>

<p class="eq">Heating (u ≥ 0): T<sub>h</sub> − T<sub>0</sub> = u(P + J)/G;<br>
Cooling (u ≤ 0): T<sub>c</sub> − T<sub>0</sub> = u(P − J)/G.<br>
dT<sub>h</sub>/du = (P + J)/G; &nbsp; dT<sub>c</sub>/du = (P − J)/G.</p>
<p>Both derivatives are positive for net cooling (P &gt; J). Signed-PWM slopes each contain 1/255, which cancels along with G:</p>
<p class="eq">r = (P + J)/(P − J) ⇒ (r − 1)P = (r + 1)J<br>
⇒ <b>J/P = (r − 1)/(r + 1) = 0.4771</b>. Check: r = 2 ⇒ J/P = 1/3.</p>
<p>This assumes equal ON-current and G in both directions and constant properties.</p>
<hr>
<h2>4. Laird values, conditions, and predicted ratio</h2>
<p>Laird CP14-127-045-L2-W4.5, part 58910-501, revision 00 (June 1, 2022), p. 3, <b>27 °C hot-side column</b>:</p>
<table border="1" cellspacing="0" cellpadding="2" width="100%">
<tr><th>Quantity</th><th>Value</th><th>Meaning and condition</th></tr>
<tr><td>R</td><td>1.50 Ω</td><td>Module electrical resistance at the listed hot-side temperature.</td></tr>
<tr><td>I<sub>max</sub></td><td>8.6 A</td><td>Current specified at ΔT<sub>max</sub>.</td></tr>
<tr><td>Q̇<sub>c,max</sub></td><td>71.3 W</td><td>Maximum cold-side heat removal at ΔT = 0.</td></tr>
<tr><td>ΔT<sub>max</sub></td><td>70.5 K</td><td>Maximum face-temperature difference at Q̇<sub>c</sub> = 0.</td></tr>
</table>
<p>At ΔT = 0, passive TEC conduction vanishes. Using the assignment’s symmetric half-Joule construction:</p>
<p class="eq">J<sub>max</sub> = ½I<sub>max</sub>²R = ½(8.6)²(1.50) = <b>55.47 W</b>;<br>
P<sub>max</sub> = Q̇<sub>c,max</sub> + J<sub>max</sub> = 71.30 + 55.47 = <b>126.77 W</b>;<br>
r<sub>Laird</sub> = (126.77 + 55.47)/(126.77 − 55.47) = <b>2.5560 ≈ 2.56</b>.</p>
<p>All powers are thermal; the listed maxima need not share one test condition.</p>
<hr>
<h2>5. Measured versus data-sheet ratios</h2>
<p>Measured r = 2.8245 versus predicted 2.5560: 10.5% higher. Full duty does not ensure I<sub>max</sub>: supply limits, bridge drop, wiring, and TEC resistance set current. PWM versus DC, finite temperature differences, passive paths, changing properties, and fit curvature also limit agreement.</p>
<hr>
<h2>6. Passive thermal conduction</h2>
<p>Heat flows outward when the block is hotter than room temperature and inward when colder. Symmetric conduction opposes both excursions and cancels from r; it cannot alone explain unequal slopes. Joule heat assists heating and opposes cooling.</p>
<hr>
<h2>7. Conclusion</h2><p>CONCLUSION</p>
</body></html>'''.replace('CONCLUSION', conclusion)
app = QApplication([])
assets = []
for image, width, height in render_equations():
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, 'PNG')
    buffer.close()
    uri = 'data:image/png;base64,' + base64.b64encode(bytes(data)).decode('ascii')
    assets.append((uri, image, width, height))
blocks = iter(assets)
def equation_image(match):
    uri, image, width, height = next(blocks)
    return f'<p align="center" style="margin:4px"><img src="{uri}" width="{round(width*0.83)}" height="{round(height*0.83)}"></p>'
html = re.sub(r'<p class="eq">.*?</p>', equation_image, html, flags=re.S)
# Mathematical identifiers in prose use the same italic serif convention.
html = re.sub(r'(?<![\w>])([mTQI])<sub>(.*?)</sub>', r'<span style="font-family:Times New Roman"><i>\1</i><sub>\2</sub></span>', html)
(OUTPUT / 'A2_Chen_Hasan.html').write_text(html)
doc = QTextDocument()
doc.setDefaultFont(QFont('Helvetica', 10.5))
doc.setBaseUrl(QUrl.fromLocalFile(str(OUTPUT) + '/'))
image_url = QUrl('../other_files/module4/P4_Temperature_susceptibility/temperature_vs_signed_pwm.png')
doc.addResource(QTextDocument.ImageResource, image_url, QImage(str(ROOT / 'docs/other_files/module4/P4_Temperature_susceptibility/temperature_vs_signed_pwm.png')))
for uri, image, _, _ in assets:
    doc.addResource(QTextDocument.ImageResource, QUrl(uri), image)
doc.setHtml(html)
writer = QPdfWriter(str(OUTPUT / 'A2_Chen_Hasan.pdf'))
writer.setResolution(96)
writer.setPageSize(QPageSize(QPageSize.A4))
writer.setPageMargins(QMarginsF(14.1, 14.1, 14.1, 14.1), QPageLayout.Millimeter)
writer.setTitle('A2 — TEC Heating and Cooling Analysis')
writer.setCreator('Kyle Chen and Muhammad Hasan')
doc.setPageSize(writer.pageLayout().paintRectPixels(96).size())
# Draw each page explicitly so running headers and page counts match A1.
page_rect = writer.pageLayout().paintRectPixels(96)
page_width, page_height = page_rect.width(), page_rect.height()
page_count = doc.pageCount()
print(f'Layout pages: {page_count}')
painter = QPainter(writer)
for page in range(page_count):
    if page:
        writer.newPage()
    painter.save()
    painter.setClipRect(QRectF(0, 0, page_width, page_height))
    painter.translate(0, -page * page_height)
    context = QAbstractTextDocumentLayout.PaintContext()
    context.clip = QRectF(0, page * page_height, page_width, page_height)
    doc.documentLayout().draw(painter, context)
    painter.restore()
    painter.setFont(QFont('Helvetica', 6.75))
    painter.drawText(QRectF(0, -37, page_width, 18), Qt.AlignLeft, 'module_04_evidence.md')
    painter.drawText(QRectF(0, -37, page_width, 18), Qt.AlignRight, '2026-10-04')
    painter.drawText(QRectF(0, page_height + 17, page_width, 18), Qt.AlignHCenter, f'{page + 1} / {page_count}')
painter.end()
print(OUTPUT / 'A2_Chen_Hasan.pdf')
