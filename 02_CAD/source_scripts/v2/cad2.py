# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : v2 simplified redesign (not built): dome with pegs, base and two-step line spool.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Butterfly dome v2 - one servo, all wings flap together, very simple assembly.

Parts
  D2_dome            hemisphere R75 (wall 2.5) with 7 peg holes, orientation notch, cable notch
  PEG_1..PEG_7       short hollow posts: pushed in from inside (flange inside), butterfly body glued on top
  B2_base            disc + locating lip + servo pocket + line-guide ring (7 eyelets)
  SPOOL              two-step line spool glued onto a trimmed servo horn: r8 for large, r4 for medium
Butterflies (bodies, wings, acrylic plates) are the existing ones: #1-#4 L150, #5-#7 S75.
Frame: base top / dome rim at z=0, dome centre at the origin.
"""
import sys, numpy as np, cadquery as cq
sys.path.insert(0,'/home/claude/dome/cad'); sys.path.insert(0,'/home/claude/dome')
from dp import LAY, RD, DW, SV_L, SV_W, SV_H, SV_SHAFT_OFF, SV_EAR_SPAN
from lay import frame
OUT='/home/claude/dome/v2/out/'
import os; os.makedirs(OUT,exist_ok=True)

def cyl(r,h,x=0,y=0,z=0): return cq.Workplane('XY').workplane(offset=z).center(x,y).circle(r).extrude(h)
def box(dx,dy,dz,x=0,y=0,z=0): return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def axcyl(p0,p1,r):
    p0=np.asarray(p0,float); p1=np.asarray(p1,float); v=p1-p0; L=np.linalg.norm(v)
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,L,cq.Vector(*p0),cq.Vector(*(v/L))))
def ball(r): return cq.Workplane('XY').add(cq.Solid.makeSphere(r,cq.Vector(0,0,0)))

BUT=LAY[:7]                       # #1-#4 large, #5-#7 medium
RI=RD-DW
HOLE_R=1.7                        # dome hole for the Ø3.2 peg
PEG_R=1.6; PEG_BORE=0.8; FL_R=4.0; FL_T=1.5
# spool / guide ring
RING_RI, RING_T, RING_H = 25.0, 2.0, 49.0
SPOOL_Z0 = SV_H + 1.0             # spool bottom: servo shaft top (28.5 above the base) + horn
R_L, R_M = 8.0, 4.0               # stroke = r x 45 deg  -> 6.3 mm (large) / 3.1 mm (medium)
Z_L, Z_M = SPOOL_Z0+6.0, SPOOL_Z0+13.5    # centres of the two 6 mm steps (6 mm tall: tolerant to horn height)

def module(b):
    n,h,s=frame(b['polar'],b['az']); rot=np.radians(b.get('rot',0)); h,s=np.cos(rot)*h+np.sin(rot)*s,np.cos(rot)*s-np.sin(rot)*h
    k=2.0 if b['kind']=='L' else 1.0; ys=4.25*k
    ap=RD*n+ys*h                                   # where the peg axis crosses the outer surface
    up=b['clr']-6.8*k+4.5                          # peg top above the surface = body socket top
    return n,h,s,ap,k,up

def line_exit(b):
    n,h,s,ap,k,up=module(b); return ap-n*(DW+FL_T)  # line leaves the peg here (inside the dome)

POST_AZ, POST_R, POST_Z = 75.0, 40.0, 47.0   # #1 (top) line comes straight down: a post turns it so it enters its eyelet from outside
def azim(b):
    if b is BUT[0]: return POST_AZ
    p=line_exit(b); return np.degrees(np.arctan2(p[1],p[0]))

# ------------------------------------------------------------------ dome
def build_dome():
    d=ball(RD).cut(ball(RI)).cut(box(400,400,200,0,0,-200))
    for b in BUT:
        n,h,s,ap,k,up=module(b)
        d=d.cut(axcyl(ap-n*(DW+3),ap+n*3,HOLE_R))
    d=d.cut(box(8,4.0,3.4,-(RD-1.25),0,-0.01))                            # orientation notch at az 180
    d=d.cut(box(8,10,5.0,RD-1.25,0,-0.01))                                # cable notch at az 0 (servo cable side)
    return d

# ------------------------------------------------------------------ pegs
def build_peg(b):
    n,h,s,ap,k,up=module(b)
    fl=axcyl(ap-n*(DW+FL_T+2.0),ap,FL_R).intersect(ball(RI-0.05))          # flange, face follows the inner wall
    fl=fl.cut(axcyl(ap-n*(DW+FL_T+3),ap-n*(DW+FL_T),FL_R+1))               # flange thickness FL_T (measured at the axis)
    rod=axcyl(ap-n*(DW+FL_T),ap+n*up,PEG_R)
    p=fl.union(rod).cut(axcyl(ap-n*(DW+FL_T+4),ap+n*(up+1),PEG_BORE))
    # print frame: flange down, axis = +z
    T=np.eye(4); R=np.c_[s,h,n].T; T[:3,:3]=R; T[:3,3]=-R@(ap-n*(DW+FL_T+2.0))
    return p, T, up

# ------------------------------------------------------------------ spool
def build_spool():
    z=0
    sp=cyl(11,3.0)                                                        # bottom flange (horn recess underneath)
    sp=sp.union(cyl(R_L,6.0,0,0,3.0))                                     # large-butterfly step  z 3-9
    sp=sp.union(cyl(11,1.5,0,0,9.0))                                      # middle flange         z 9-10.5
    sp=sp.union(cyl(R_M,6.0,0,0,10.5))                                    # medium-butterfly step z 10.5-16.5
    sp=sp.union(cyl(8,1.5,0,0,16.5))                                      # top flange            z 16.5-18
    sp=sp.cut(cyl(3.8,2.2,0,0,-0.01)).cut(box(5.9,10.0,2.2,0,4.6,-0.01))  # trimmed horn: hub Ø7.6 + one arm
    sp=sp.cut(cyl(2.3,20,0,0,-1))                                         # screwdriver / horn screw hole
    for a in (45,135,225,315): sp=sp.cut(cyl(0.65,3,9.6*np.cos(np.radians(a)),9.6*np.sin(np.radians(a)),8.5))  # large ties
    for a in (90,210,330): sp=sp.cut(cyl(0.65,3,6.0*np.cos(np.radians(a)),6.0*np.sin(np.radians(a)),16.0))    # medium ties
    return sp

# ------------------------------------------------------------------ base
def build_base():
    bs=cyl(RD,3.0,0,0,-3.0)
    bs=bs.union(cyl(RI-0.3,3.0).cut(cyl(RI-2.5,4,0,0,-0.5)))              # locating lip inside the dome rim
    bs=bs.union(box(3.0,3.4,3.0,-(RI+0.6),0,0))                           # key -> dome notch at az 180
    # servo pocket: shaft on the axis, body toward +x, open at the cable end
    cx=SV_SHAFT_OFF; L=SV_L+0.6; W=SV_W+0.6; t=1.6; H=10.0
    pk=box(L+2*t,W+2*t,H,cx,0,0).cut(box(L,W,H+1,cx,0,-0.5)).cut(box(t+1,W-2,H+1,cx+L/2+t/2,0,-0.5))
    bs=bs.union(pk)
    # line-guide ring with one eyelet per butterfly, at the height of its spool step
    ring=cyl(RING_RI+RING_T,RING_H).cut(cyl(RING_RI,RING_H+1,0,0,-0.5))
    for i,b in enumerate(BUT):
        a=np.radians(azim(b)); z=Z_L if b['kind']=='L' else Z_M
        p0=np.array([(RING_RI-1)*np.cos(a),(RING_RI-1)*np.sin(a),z]); p1=np.array([(RING_RI+RING_T+1)*np.cos(a),(RING_RI+RING_T+1)*np.sin(a),z])
        ring=ring.cut(axcyl(p0,p1,0.8))
        ring=ring.cut(axcyl(p0+np.array([0,0,0])*0,p0+(p1-p0)*0.25,1.2))   # small funnel on the inside
    bs=bs.union(ring)
    a=np.radians(POST_AZ); px,py=POST_R*np.cos(a),POST_R*np.sin(a)
    post=box(6,6,POST_Z+2,0,0,0).rotate((0,0,0),(0,0,1),POST_AZ).translate((px,py,0))
    post=post.cut(axcyl([px-4*np.cos(a),py-4*np.sin(a),POST_Z],[px+4*np.cos(a),py+4*np.sin(a),POST_Z],0.8))
    bs=bs.union(post)
    # cable exit slot through the ring next to the pocket's open end, and a cable channel to the notch
    bs=bs.cut(box(6,12,8,RING_RI+1,0,-0.01))                              # cable exit through the ring (toward the dome's cable notch)
    return bs

def export(shape,name,T=None):
    import trimesh
    cq.exporters.export(shape,OUT+name+'.stl',tolerance=0.02,angularTolerance=0.15)
    m=trimesh.load(OUT+name+'.stl')
    if T is not None: m.apply_transform(T)
    m.apply_translation([0,0,-m.bounds[0,2]]); m.export(OUT+name+'.stl')
    try: cq.exporters.export(shape,OUT+name+'.step')
    except Exception: pass
    return m

if __name__=='__main__':
    for i,b in enumerate(BUT): print(f'#{i+1} {b["kind"]} az_line {azim(b):6.1f}  peg up {module(b)[5]:.1f}')
    d=build_dome(); m=export(d,'D2_dome'); print('dome',m.bounds.round(1).tolist(),m.is_watertight)
    for i,b in enumerate(BUT):
        p,T,up=build_peg(b); m=export(p,f'PEG_{i+1}',T); print(f'PEG_{i+1}',(m.bounds[1]-m.bounds[0]).round(2),m.is_watertight)
    s=build_spool(); m=export(s,'SPOOL'); print('spool',(m.bounds[1]-m.bounds[0]).round(2),m.is_watertight)
    bb=build_base(); m=export(bb,'B2_base'); print('base',(m.bounds[1]-m.bounds[0]).round(2),m.is_watertight)
