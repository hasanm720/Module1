"""Typeset A2 equations with local Qt fonts; no external renderer required."""
from PySide6.QtGui import QFont, QFontMetricsF, QImage, QPainter, QColor
from PySide6.QtCore import Qt

class Box:
    def __init__(self,w,h,base,draw): self.w,self.h,self.base,self.draw=w,h,base,draw

def text(s, size=16, italic=False):
    font=QFont('Times New Roman'); font.setPixelSize(size); font.setItalic(italic)
    m=QFontMetricsF(font); w=m.horizontalAdvance(s)
    def draw(p,x,y):
        p.setFont(font); p.drawText(x,y+m.ascent(),s)
    return Box(w,m.height(),m.ascent(),draw)

def row(*items):
    items=[text(x) if isinstance(x,str) else x for x in items]
    base=max(i.base for i in items); height=base+max(i.h-i.base for i in items)
    def draw(p,x,y):
        for i in items: i.draw(p,x,y+base-i.base); x+=i.w
    return Box(sum(i.w for i in items),height,base,draw)

def frac(a,b):
    w=max(a.w,b.w)+8; h=a.h+b.h+8; base=a.h+4+5
    def draw(p,x,y):
        a.draw(p,x+(w-a.w)/2,y); p.drawLine(x+1,y+a.h+4,x+w-1,y+a.h+4); b.draw(p,x+(w-b.w)/2,y+a.h+8)
    return Box(w,h,base,draw)

def script(a, sub=None, sup=None):
    lower=text(sub,11) if sub else None; upper=text(sup,11) if sup else None
    top=5 if upper else 0; width=max(lower.w if lower else 0,upper.w if upper else 0)
    def draw(p,x,y):
        a.draw(p,x,y+top)
        if lower: lower.draw(p,x+a.w,y+top+a.base-3)
        if upper: upper.draw(p,x+a.w,y)
    return Box(a.w+width,a.h+top+(5 if lower else 0),a.base+top,draw)

def v(s,sub=None,sup=None): return script(text(s,italic=True),sub,sup) if sub or sup else text(s,italic=True)
def r(*xs): return row(*xs)
def f(a,b): return frac(a,b)
def d(var): return r(text('d'),var)
def power(s): return v(s,sup='2')
def q(sub): return v('Q̇',sub)

def render_equations():
    I=v('I'); D=v('D'); tau=v('τ'); P=v('P'); J=v('J'); G=v('G'); u=v('u'); t=v('t'); one=text('1')
    integral=script(text('∫',26), '0','τ')
    eqs=[
      [r('⟨',v('i'),'⟩ = ',f(one,tau),' ',integral,' ',v('i'),'(t) dt = ',f(r(I,D,tau),tau),' = ',D,I),
       r('⟨',power('i'),'⟩ = ',f(one,tau),' ',integral,' ',power('i'),'(t) dt = ',f(r(power('I'),D,tau),tau),' = ',D,power('I'))],
      [r(v('C'),' ',f(d(v('T','o')),d(t)),' = ',q('TEC'),' − ',G,'(',v('T','o'),' − ',v('T','0'),')'),
       r(f(d(v('T','o')),d(t)),' = 0  ⇒  ',G,'(',v('T','o'),' − ',v('T','0'),') = ',q('TEC'))],
      [r(v('T','h'),' − ',v('T','0'),' = ',f(r(u,'(',P,' + ',J,')'),G),'  (',u,' ≥ 0);     ',v('T','c'),' − ',v('T','0'),' = ',f(r(u,'(',P,' − ',J,')'),G),'  (',u,' ≤ 0)'),
       r(f(d(v('T','h')),d(u)),' = ',f(r(P,' + ',J),G),';      ',f(d(v('T','c')),d(u)),' = ',f(r(P,' − ',J),G))],
      [r(v('r'),' = ',f(r(P,' + ',J),r(P,' − ',J)),'  ⇒  (',v('r'),' − 1)',P,' = (',v('r'),' + 1)',J),
       r(f(J,P),' = ',f(r(v('r'),' − 1'),r(v('r'),' + 1')),' = 0.4771;     ',v('r'),' = 2  ⇒  ',f(J,P),' = ',f(one,text('3')))],
      [r(v('J','max'),' = ',f(one,text('2')),v('I','max','2'),v('R'),' = ',f(one,text('2')),'(8.6)²(1.50) = 55.47 W'),
       r(v('P','max'),' = ',q('c,max'),' + ',v('J','max'),' = 71.30 + 55.47 = 126.77 W'),
       r(v('r','Laird'),' = ',f(text('126.77 + 55.47'),text('126.77 − 55.47')),' = 2.5560 ≈ 2.56')]
    ]
    assets=[]
    for index,lines in enumerate(eqs,1):
        w=int(max(b.w for b in lines)+8); h=int(sum(b.h for b in lines)+8*(len(lines)-1)+8)
        image=QImage(w*4,h*4,QImage.Format_ARGB32); image.fill(QColor('white'))
        painter=QPainter(image); painter.scale(4,4); painter.setRenderHint(QPainter.Antialiasing); painter.setPen(QColor('black'))
        y=4
        for b in lines: b.draw(painter,(w-b.w)/2,y); y+=b.h+8
        painter.end(); assets.append((image,w,h))
    return assets
