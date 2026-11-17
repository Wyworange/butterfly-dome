# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : v2: watertight dome mesh built with manifold3d.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Watertight dome mesh via manifold3d (the OCC sphere tessellation leaves gaps)."""
import numpy as np, trimesh, manifold3d as mf
from cad2 import BUT, module, RD, RI, DW, HOLE_R, OUT
SEG=256
def cylinder_between(p0,p1,r):
    p0=np.asarray(p0,float); p1=np.asarray(p1,float); v=p1-p0; L=np.linalg.norm(v); z=v/L
    c=mf.Manifold.cylinder(L,r,r,48)
    # rotate +z onto z
    a=np.array([0,0,1.0]); ax=np.cross(a,z); s=np.linalg.norm(ax); cth=a@z
    if s<1e-9: R=np.eye(3) if cth>0 else np.diag([1,-1,-1])
    else:
        ax/=s; K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]]); R=np.eye(3)+s*K+(1-cth)*K@K
    M=np.c_[R,p0]; return c.transform(M.tolist())
def box(dx,dy,dz,x,y,z):  # z = bottom
    return mf.Manifold.cube([dx,dy,dz]).translate([x-dx/2,y-dy/2,z])
d=mf.Manifold.sphere(RD,SEG)-mf.Manifold.sphere(RI,SEG)
d=d-box(400,400,200,0,0,-200)
for b in BUT:
    n,h,s,ap,k,up=module(b); d=d-cylinder_between(ap-n*(DW+3),ap+n*3,HOLE_R)
d=d-box(8,4.0,3.4,-(RD-1.25),0,-0.01)
d=d-box(8,10,5.0,RD-1.25,0,-0.01)
m=d.to_mesh(); tm=trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts)
tm.export(OUT+'D2_dome.stl'); print('watertight',tm.is_watertight,'faces',len(tm.faces),tm.bounds.round(1).tolist())
