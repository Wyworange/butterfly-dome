# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Acrylic wing stiffener geometry (min feature 2.5 mm), left / right mirror parts.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Laser-cut acrylic stiffener (base plate glued under each wing half), min feature 2.5 mm.
Frame: same as the wings (x span, +y head, body centre 0, hinge axis x=+hx, z=0); right wing = sd +1.
Plate under the wing root + one straight arm that runs past the hinge under the body.
No hole at the arm tip (a hole would leave < 2.5 mm of material): the Y-thread is tied round the arm
at the score mark (x = hx - R) and fixed with a drop of CA."""
import sys, numpy as np
sys.path.insert(0,'/home/claude/dome/laser'); sys.path.insert(0,'/home/claude/dome/cad')
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
import minweb as MW
from wings_ai import wing_half
ACR_T=1.6   # stiffener = laser-cut acrylic 1/16" (1.59 mm)
# name: scale, hinge x, arm radius R, arm width, arm offset DY, plate width, body length
TYPES={'L150':(1.0,3.0,6.0,3.0,2.4,7.4,45.2),
       'S75': (0.5,1.5,3.0,2.5,1.5,3.7,22.6),
       'S53': (0.35,1.5,3.0,2.5,1.5,4.5,15.8)}
TIP_EXT=1.0      # arm runs this far past the tie point so the knot cannot slip off
_w={}
def wing(name):
    if name not in _w:
        sc,hx=TYPES[name][:2]; _w[name]=MW.enforce_best(wing_half(sc,1,hx),2.55,0.4)[0]
    return _w[name]
def stiffener(name, sd=1):
    """left wing (sd=-1) = mirror of the right wing's root shape, with its arm on the other side (-y)"""
    sc,hx,R,aw,dy,pw,Lb=TYPES[name]; dy=dy*sd
    x0=hx+0.3; xt=hx-R; xe=xt-TIP_EXT
    plate=box(x0,-(Lb-0.4)/2,x0+pw,(Lb-0.4)/2).intersection(Polygon(wing(name).exterior).buffer(-0.15))
    # parking notch for the other wing's arm tip (mirror of this arm), +0.3 clearance all round
    notch=box(x0-1,-dy-aw/2-0.3,-xe+0.3,-dy+aw/2+0.3)   # other wing's arm tip lies at -dy
    plate=plate.difference(notch)
    arm=box(xe,dy-aw/2,x0+1.5,dy+aw/2)
    s=unary_union([plate,arm]).buffer(-1.24,join_style=1).buffer(1.24,join_style=1)  # drop anything thinner than 2.5
    s=max(getattr(s,'geoms',[s]),key=lambda q:q.area)
    s=unary_union([s,arm]).buffer(0.4,join_style=1).buffer(-0.4,join_style=1)       # square arm end + inside fillets
    s=max(getattr(s,'geoms',[s]),key=lambda q:q.area).simplify(0.01)
    mark=LineString([(xt,dy-aw/2+0.4),(xt,dy+aw/2-0.4)])                   # score line = tie point
    if sd==-1: s=affinity.scale(s,-1,1,origin=(0,0)); mark=affinity.scale(mark,-1,1,origin=(0,0))
    return s, mark
def min_width(g, w=2.5):
    """thickness check: area that vanishes under an opening of radius w/2, ignoring convex corners"""
    op=g.buffer(-w/2+0.01,join_style=1).buffer(w/2-0.01,join_style=1)
    th=g.difference(op); bad=[]
    from shapely.geometry import Point
    ope=unary_union([g.exterior for g in getattr(op,'geoms',[op])])
    for q in getattr(th,'geoms',[th]):
        if q.is_empty or q.area<0.01: continue
        depth=max(ope.distance(Point(p)) for p in q.exterior.coords)
        if depth>0.6: bad.append((round(q.area,2),round(depth,2),np.round(q.centroid.coords[0],1).tolist()))
    return bad
if __name__=='__main__':
    for n in TYPES:
        s,_=stiffener(n); b=s.bounds
        print(n,'size %.1f x %.1f'%(b[2]-b[0],b[3]-b[1]),'area %.0f'%s.area,'thin spots',min_width(s),
              'overlap L/R stiffeners %.3f'%s.intersection(stiffener(n,-1)[0]).area)
