# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Reads the wing outlines from the original Illustrator artwork (butterfly-1-2.ai).
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Wings straight from butterfly-1-2.ai: both halves as drawn, every decorative hole kept (only the two old
mechanism screw holes B/W per half are dropped). Model frame: x = span, y = body axis (+ head), body centre at 0."""
import os, sys, numpy as np
_c=os.getcwd(); os.chdir('/home/claude/v10'); sys.path.insert(0,'/home/claude/v10'); import ext; os.chdir(_c)
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
os.chdir('/home/claude/v10'); bfp=ext.load('butterfly-1-2'); os.chdir(_c)
bf=[Polygon(a).buffer(0) for a in bfp]
AXp=81.41; Ay_p=10.03
SCREW=[np.array(p) for p in ((69.03,12.06),(66.9,34.95),(2*AXp-69.03,12.06),(2*AXp-66.9,34.95))]
def is_screw(p): return any(p.distance(Point(*q))<0.5 for q in SCREW)
def half(i):
    H=bf[i]; holes=[p for j,p in enumerate(bf) if j!=i and p.area<H.area*0.5 and H.contains(p.representative_point())]
    keep=[p for p in holes if not is_screw(p)]; drop=len(holes)-len(keep)
    g=H
    for p in keep: g=g.difference(p)
    return g,len(keep),drop
L,nl,dl=half(0); R,nr,dr=half(27)
FULL_PAGE=unary_union([L,R]).buffer(0.005).buffer(-0.005)
def T(g): return affinity.translate(affinity.scale(affinity.translate(g,-AXp,-Ay_p),1,-1,origin=(0,0)),0,61.7)
FULL=T(FULL_PAGE)
def wing_half(scale,sd,hx):
    """one wing (sd=+1 right / -1 left) at `scale` x AI size, cut at |x| = hx + 0.3 (hinge gap)"""
    g=affinity.scale(FULL,scale,scale,origin=(0,0))
    cut=box(hx+0.3,-999,999,999) if sd==1 else box(-999,-999,-hx-0.3,999)
    h=g.intersection(cut); h=max(getattr(h,'geoms',[h]),key=lambda q:q.area)
    return h
if __name__=='__main__':
    print('left half holes kept %d (dropped %d screw holes), right half kept %d (dropped %d)'%(nl,dl,nr,dr))
    print('full span %.1f, area %.0f, holes %d'%(FULL.bounds[2]-FULL.bounds[0],FULL.area,len(FULL.interiors)))
