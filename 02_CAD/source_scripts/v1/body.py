# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Butterfly body base geometry (scaled per size: L150 / S75 / S53).
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import cadquery as cq, numpy as np
from params import *
def box(dx,dy,dz,x=0,y=0,z=0): return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def cyl(r,h,x=0,y=0,z=0): return cq.Workplane('XY').workplane(offset=z).center(x,y).circle(r).extrude(h)
# local frame: hinge axes are lines x=±HINGE_X, z=0, along Y; body axis along Y (+Y = head); line exits at the tail (-Y)
Z_BOT=-6.8; Z_FLOOR=-6.2; Z_GUIDE=-5.6; Z_WALL_TOP=-0.5; Z_TOP=0.2; ARM_ZONE=2.2; RIDGE=1.2; WING_X=1.8
def body(span):
    L=max(7.2,round(0.30*span,1))           # body length; middle 4.4 mm is the open arm zone
    walls=box(BODY_W,L,Z_WALL_TOP-Z_BOT,0,0,Z_BOT)
    pocket=box(5.2,L-1.6,Z_WALL_TOP-Z_FLOOR+0.01,0,0,Z_FLOOR)
    b=walls.cut(pocket)
    # end walls rise to the bridge; bridge 3 wide on top
    # end blocks carry the hinge films (top at z=0.2, flush with the wing top); the middle 4.4 mm stays open for the arms
    eb=L/2-ARM_ZONE
    for sgn in (1,-1):
        yy=sgn*(ARM_ZONE+eb/2)
        b=b.union(box(BODY_W,eb,Z_WALL_TOP-Z_BOT,0,yy,Z_BOT))            # solid end block up to the wall top (-0.5)
        b=b.union(box(2*RIDGE,eb,Z_TOP-Z_WALL_TOP,0,yy,Z_WALL_TOP))      # hinge-film ridge |x|<=1.2, top at +0.2
    # guide tube bore (brass OD1.2) across X, near the tail
    gy=-(ARM_ZONE-0.9)
    b=b.cut(cq.Workplane('YZ').workplane(offset=-4).center(gy,Z_GUIDE).circle(0.65).extrude(8))
    # line exit slot through the tail end wall, bottom
    b=b.cut(box(0.9,L,1.4,0.6,-L/2,Z_BOT-0.01))   # slot from the guide to the tail along the floor
    # locating pin under the floor
    b=b.union(cyl(0.5,1.5,0,0.8,Z_BOT-1.5))
    # decorative thorax rings on the outer walls (0.3 deep grooves)
    for k in range(1,int(L//1.6)):
        yy=-L/2+k*1.6
        b=b.cut(box(BODY_W+1,0.4,0.3,0,yy,Z_BOT+1.2).cut(box(BODY_W-0.6,1,1,0,yy,Z_BOT+1.0)))
    # head: small dome at +Y with two antenna holes Ø0.4
    head=cq.Workplane('XZ').workplane(offset=-(L/2)).center(0,-2.2).circle(1.9).extrude(-2.2)
    b=b.union(head)
    for dx in (-0.8,0.8): b=b.cut(cq.Workplane('XZ').workplane(offset=-(L/2+1.6)).center(dx,-1.2).circle(0.22).extrude(-1.5))
    return b.clean(),L
if __name__=='__main__':
    for i,sp in enumerate(SPANS):
        b,L=body(sp)
        cq.exporters.export(b,f'out/K{i+1}_body_span{sp}.stl',tolerance=0.01,angularTolerance=0.1); cq.exporters.export(b,f'out/K{i+1}_body_span{sp}.step')
        bb=b.val().BoundingBox(); print(f'K{i+1} span {sp}: L {L}  bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}')
