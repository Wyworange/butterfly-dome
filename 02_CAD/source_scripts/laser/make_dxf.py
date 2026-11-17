# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Exports the wing DXF and draws preview images of the cut layout.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np, ezdxf, json
from shapely.geometry import LineString
from shapely import affinity
from wings_ai import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); plt.rcParams['font.family']='Noto Sans CJK JP'
LAY=json.load(open('/home/claude/dome/cad/layout.json'))
TYPES=[('L150',1.0,3.0,sum(b['kind']=='L' for b in LAY)),('S75',0.5,1.5,sum(b['kind']=='S' and b['scale']==0.5 for b in LAY)),('S53',0.35,1.5,sum(b['kind']=='S' and b['scale']==0.35 for b in LAY))]
def root_chord(scale,hx):
    g=affinity.scale(FULL,scale,scale,origin=(0,0)); l=g.intersection(LineString([(hx+0.6,-500),(hx+0.6,500)])); return l.length
doc=ezdxf.new('R2010'); doc.units=ezdxf.units.MM
doc.layers.add('CUT',color=1); doc.layers.add('NOTE',color=5)
msp=doc.modelspace(); y0=0; info=[]
def add(g,dx,dy):
    for gg in getattr(g,'geoms',[g]):
        for ring in [gg.exterior]+list(gg.interiors): msp.add_lwpolyline([(x+dx,y+dy) for x,y in ring.coords],close=True,dxfattribs={'layer':'CUT'})
for name,sc,hx,n in TYPES:
    span=150.6*sc; gap=6; per=max(1,int(580//(span+3*gap))); hh=(FULL.bounds[3]-FULL.bounds[1])*sc
    for c in range(n+1):
        col,row=c%per,c//per
        for sd in (1,-1):
            w=wing_half(sc,sd,hx); b=w.bounds
            add(w,col*(span+3*gap)+(gap if sd==1 else 0),y0+row*(hh+8)-b[1])
    y0+=((n)//per)*(hh+8)
    msp.add_text(f'{name}: span {span:.1f} mm, {n} butterflies + 1 spare. Material: white polyester 0.18 mm. Hinge axis at x=+-{hx}, wing root cut at +-{hx+0.3}',dxfattribs={'height':2.5,'layer':'NOTE'}).set_placement((0,y0-6))
    hh=(FULL.bounds[3]-FULL.bounds[1])*sc; y0+=hh+18
    info.append((name,span,n,root_chord(sc,hx),len(wing_half(sc,1,hx).interiors)))
doc.saveas('laser_wings_AI_pattern.dxf')
for r in info: print('%s span %.1f x%d (+1): root chord %.1f mm, holes per wing %d'%r)
# preview: AI original (red) vs cut outline (black) for the large wing
fig,axs=plt.subplots(1,2,figsize=(18,8))
ax=axs[0]; ax.set_aspect('equal'); ax.axis('off')
src=T(FULL_PAGE)
for sd in (1,-1):
    w=wing_half(1.0,sd,3.0); ax.add_patch(MP(np.array(w.exterior.coords),fc='#f4f2ea',ec='k',lw=1.2))
    for r in w.interiors: ax.add_patch(MP(np.array(r.coords),fc='white',ec='k',lw=0.9))
import os
os.chdir('/home/claude/v10'); raw=[np.array(a) for a in ext.load('butterfly-1-2')]; os.chdir('/home/claude/dome/laser')
for a in raw:
    p=np.c_[a[:,0]-AXp,-(a[:,1]-Ay_p)+61.7]
    if p[:,0].min()>-80 and p[:,0].max()<80 and p[:,1].min()>-30 and p[:,1].max()<80: ax.plot(p[:,0],p[:,1],color='#d23',lw=0.5)
ax.set_xlim(-80,80); ax.set_ylim(-28,70); ax.set_title('Large butterfly (1:1): black = laser cut line, red = original AI artwork (they overlap)\n6.6 mm removed in the middle for the body and hinge; only the 2 old screw holes per side were dropped',fontsize=12,loc='left')
ax=axs[1]; ax.set_aspect('equal'); ax.axis('off'); y0=0
for name,sc,hx,n in TYPES:
    span=150.6*sc; gap=6; per=max(1,int(580//(span+3*gap))); hh=(FULL.bounds[3]-FULL.bounds[1])*sc
    for c in range(n+1):
        col,row=c%per,c//per
        for sd in (1,-1):
            w=wing_half(sc,sd,hx); b=w.bounds; dx=col*(span+3*gap)+(gap if sd==1 else 0); dy=y0+row*(hh+8)-b[1]
            ax.add_patch(MP(np.array(w.exterior.coords)+[dx,dy],fc='#f4f2ea',ec='k',lw=0.5))
            for r in w.interiors: ax.add_patch(MP(np.array(r.coords)+[dx,dy],fc='white',ec='k',lw=0.3))
    ax.text(0,y0-9,f'{name}: span {span:.1f} mm, {n} pcs + 1 spare',fontsize=11)
    y0+=((n)//per)*(hh+8)
    y0+=(FULL.bounds[3]-FULL.bounds[1])*sc+18
ax.autoscale_view(); ax.set_title('Cut layout (laser_wings_AI_pattern.dxf, units: mm)',fontsize=12,loc='left')
plt.tight_layout(); plt.savefig('laser_preview.png',dpi=90)
