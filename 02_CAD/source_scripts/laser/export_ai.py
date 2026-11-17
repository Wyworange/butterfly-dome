# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Writes the laser cut sheets as .ai / .pdf / .svg / .dxf (red = cut, blue = engrave).
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Laser files for Illustrator: wings (polyester film) and acrylic stiffeners, each as .ai (PDF-compatible),
.svg and .dxf. Cut = RGB red 255,0,0 hairline; score (tie mark on the stiffener arm) = blue 0,0,255."""
import sys, ezdxf, numpy as np
sys.path.insert(0,'/home/claude/dome/laser')
from shapely.geometry import Polygon, LineString
from shapely import affinity
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from stiff_acr import stiffener, TYPES, min_width
OUT='/home/claude/dome/deliver/laser_AI/'
import os; os.makedirs(OUT,exist_ok=True)
MARGIN=5.0
HAIR=0.01*mm   # 0.01 mm stroke

def write_all(base, cuts, scores, size):
    W,H=size
    # ---- AI / PDF ----
    for ext in ('ai','pdf'):
        c=canvas.Canvas(OUT+f'{base}.{ext}',pagesize=(W*mm,H*mm)); c.setLineWidth(HAIR)
        c.setTitle(base); c.setAuthor('laser export')
        for col,items in (((1,0,0),cuts),((0,0,1),scores)):
            c.setStrokeColorRGB(*col)
            for pts,closed in items:
                p=c.beginPath(); p.moveTo(pts[0][0]*mm,pts[0][1]*mm)
                for x,y in pts[1:]: p.lineTo(x*mm,y*mm)
                if closed: p.close()
                c.drawPath(p,stroke=1,fill=0)
        c.showPage(); c.save()
    # ---- SVG (mm units, y flipped) ----
    def d(pts,closed): return 'M'+' L'.join(f'{x:.3f},{H-y:.3f}' for x,y in pts)+(' Z' if closed else '')
    with open(OUT+f'{base}.svg','w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n')
        f.write('<g id="CUT" fill="none" stroke="#FF0000" stroke-width="0.01">\n')
        for pts,cl in cuts: f.write(f'<path d="{d(pts,cl)}"/>\n')
        f.write('</g>\n<g id="SCORE" fill="none" stroke="#0000FF" stroke-width="0.01">\n')
        for pts,cl in scores: f.write(f'<path d="{d(pts,cl)}"/>\n')
        f.write('</g>\n</svg>\n')
    # ---- DXF ----
    doc=ezdxf.new('R2010'); doc.units=ezdxf.units.MM
    doc.layers.add('CUT',color=1); doc.layers.add('SCORE',color=5); m=doc.modelspace()
    for lay,items in (('CUT',cuts),('SCORE',scores)):
        for pts,cl in items: m.add_lwpolyline(pts,close=cl,dxfattribs={'layer':lay})
    doc.saveas(OUT+f'{base}.dxf')

def rings(g,dx=0,dy=0):
    out=[]
    for gg in getattr(g,'geoms',[g]):
        for r in [gg.exterior]+list(gg.interiors): out.append(([(x+dx,y+dy) for x,y in r.coords],True))
    return out

# ================= wings: take the verified min-2.5 layout from the DXF =================
src=ezdxf.readfile('/home/claude/dome/laser/laser_wings_AI_min2.5.dxf')
P=[[tuple(p[:2]) for p in e.get_points()] for e in src.modelspace().query('LWPOLYLINE[layer=="CUT"]')]
allp=np.vstack([np.array(p) for p in P]); x0,y0=allp.min(0); x1,y1=allp.max(0)
cuts=[([(x-x0+MARGIN,y-y0+MARGIN) for x,y in p],True) for p in P]
WS=(x1-x0+2*MARGIN, y1-y0+2*MARGIN)
write_all('laser_WINGS_polyester0.18mm', cuts, [], WS)
print('wings: %d paths, sheet %.0f x %.0f mm'%(len(cuts),*WS))

# ================= acrylic stiffeners: 4 butterflies x 2 + 2 spare = 10 per size =================
cuts=[]; scores=[]; y=MARGIN; Wmax=0; info=[]
for n in ('L150','S75','S53'):
    # row 1 = right-wing plates x5, row 2 = left-wing plates (mirror) x5  (4 butterflies + 1 spare)
    rows=[]
    for sd in (1,-1):
        s_,m_=stiffener(n,sd); rows.append((affinity.rotate(s_,90,origin=(0,0)),affinity.rotate(m_,90,origin=(0,0))))
    w=max(r[0].bounds[2]-r[0].bounds[0] for r in rows); h=max(r[0].bounds[3]-r[0].bounds[1] for r in rows); gap=3.0
    for i in range(10):
        r,c=divmod(i,5)
        ss,mm_=rows[r]; b=ss.bounds; s=ss
        bx=MARGIN+c*(w+gap)-b[0]; by=y+r*(h+gap)-b[1]
        cuts+=rings(ss,bx,by); scores.append(([(px+bx,py+by) for px,py in mm_.coords],False))
        Wmax=max(Wmax,MARGIN+c*(w+gap)+w)
    info.append((n,w,h,min_width(s)))
    y+=2*(h+gap)+4
SS=(Wmax+MARGIN, y-4+MARGIN-3)
# flip vertically so the sheet reads top-down: L150 first, and in each size the RIGHT-wing row on top
flip=lambda items:[([(px,SS[1]-py) for px,py in pts],cl) for pts,cl in items]
cuts=flip(cuts); scores=flip(scores)
write_all('laser_STIFFENERS_acrylic_1-16in', cuts, scores, SS)
for r in info: print('stiffener %s: %.1f x %.1f mm, thin spots %s'%r)
print('stiffener sheet %.0f x %.0f mm'%SS)
