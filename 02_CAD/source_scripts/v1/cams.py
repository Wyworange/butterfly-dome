# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Cam disc profiles and the rocker outline (2D, shapely).
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely import affinity
from shapely.ops import unary_union
from kin import *
def cam_poly(line):
    pc=pitch_curve(line)
    # the drum turns 0..180 only; outside that arc the nose never touches -> pad with base circle
    th=np.radians(TH); rho=np.linalg.norm(pc,axis=1)
    ang=np.arctan2(pc[:,1],pc[:,0])
    full=np.linspace(-np.pi,np.pi,1441); rr=np.full_like(full,R_BASE+NOSE_R)
    # map touched angles
    for a,r in zip(ang,rho):
        i=int(round((a+np.pi)/(2*np.pi)*1440))%1441; rr[i]=max(rr[i],r) if rr[i]>R_BASE+NOSE_R+1e-6 else r
    # smooth fill of gaps by interpolation over touched samples
    order=np.argsort(ang); a_s=ang[order]; r_s=rho[order]
    span=(a_s.min(),a_s.max())
    rr=np.where((full>=span[0])&(full<=span[1]),np.interp(full,a_s,r_s),R_BASE+NOSE_R)
    pitch=Polygon(np.c_[rr*np.cos(full),rr*np.sin(full)]).buffer(0)
    prof=pitch.buffer(-NOSE_R,resolution=24).buffer(0.0)
    return prof,pitch
def rocker_poly():
    hub=Point(0,0).buffer(3.0,resolution=24)
    bar_in=LineString([(0,0),(-6,5.5),(-12.6,5.5),(-ARM_IN,0)]).buffer(1.3,resolution=12)
    nose=Point(-ARM_IN,0).buffer(NOSE_R,resolution=24)
    bar_out=LineString([(0,0),(ARM_OUT,0)]).buffer(1.4,resolution=12)
    tip=Point(ARM_OUT,0).buffer(2.0,resolution=24)
    g=unary_union([hub,bar_in,nose,bar_out,tip]).difference(Point(0,0).buffer(1.1,resolution=24)).difference(Point(ARM_OUT,0).buffer(0.55,resolution=16))
    return g
def rocker_at(g,a):
    # local frame: in-arm along -x at a=0; world (y,z): rotate by angle so in-arm direction = (-cos a,-sin a)
    return affinity.translate(affinity.rotate(g,a,origin=(0,0),use_radians=True),PIV_Y,PIV_Z)
if __name__=='__main__':
    RK=rocker_poly(); worst=9
    for k,l in enumerate(LINES):
        prof,_=cam_poly(l); pulls=pull_profile(l,TH); m=9
        for th,p in zip(TH[::10],pulls[::10]):
            a=alpha_for_pull(p); camw=affinity.translate(affinity.rotate(prof,th,origin=(0,0)),DRUM_Y,DRUM_Z)
            body=rocker_at(RK.difference(Point(-ARM_IN,0).buffer(NOSE_R+0.6)),a)
            m=min(m,body.distance(camw))
            nz=rocker_at(Point(-ARM_IN,0).buffer(NOSE_R),a); m_n=nz.distance(camw)
            if m_n>0.25: print('  nose lifts off',k,th,round(m_n,2))
        rmin=min(np.linalg.norm(np.array(prof.exterior.coords),axis=1)); rmax=max(np.linalg.norm(np.array(prof.exterior.coords),axis=1))
        worst=min(worst,m); print(f"{k:2d} {l['name']}: cam r {rmin:.1f}-{rmax:.1f}, rocker body to cam min {m:.2f}")
    print('worst',round(worst,2))
