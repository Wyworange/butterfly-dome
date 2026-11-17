# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Rocker kinematics: line pull per servo angle, pressure angle and servo torque check.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np
from dp import *
P=np.array([PIV_Y,PIV_Z]); D=np.array([DRUM_Y,DRUM_Z])
def nose(a): return P+ARM_IN*np.array([-np.cos(a),-np.sin(a)])
def tip(a):  return P+ARM_OUT*np.array([np.cos(a),np.sin(a)])
from scipy.optimize import brentq
def alpha_for_rho(rho): return brentq(lambda a: np.linalg.norm(nose(a)-D)-rho,np.radians(-60),np.radians(45))
A0=alpha_for_rho(R_BASE+NOSE_R); TZ0=tip(A0)[1]
def alpha_for_pull(p): return np.arcsin(np.clip((TZ0-p-PIV_Z)/ARM_OUT,-1,1))
def pull_profile(line,th):
    th=np.asarray(th,float); out=np.zeros_like(th)
    for (a,b) in SCHED[line['name']]:
        r=RAMP_BOB if line['fn']=='bob' else (b-a)/2
        u=np.clip((th-a)/r,0,1); v=np.clip((b-th)/r,0,1); s=np.minimum(u,v)
        out=np.maximum(out,(1-np.cos(np.pi*s))/2)
    return out*line['stroke']
def force(line):
    n=len(line['who'])
    if line['fn']=='bob': return n*SPRING_F*1.6*1.5
    return n*(0.20 if LAY[line['who'][0]]['kind']=='L' else 0.13)*1.5
TH=np.linspace(0,180,1801)
def pitch_curve(line):
    """nose-centre path in the drum frame (drum turns by +theta with the servo)"""
    pts=[]
    for th,p in zip(TH,pull_profile(line,TH)):
        a=alpha_for_pull(p); n=nose(a)-D; t=np.radians(th)
        c,s=np.cos(-t),np.sin(-t); pts.append([c*n[0]-s*n[1],s*n[0]+c*n[1]])
    return np.array(pts)
if __name__=='__main__':
    print('rest alpha %.1f deg, tip z %.1f, tip y %.1f'%(np.degrees(A0),TZ0,tip(A0)[0]))
    tot=np.zeros_like(TH)
    for k,l in enumerate(LINES):
        p=pull_profile(l,TH); dp=np.gradient(p,np.radians(TH[1]-TH[0])); tot+=force(l)*np.abs(dp)
        pc=pitch_curve(l); rho=np.linalg.norm(pc,axis=1)
        # pressure angle: angle between nose path normal and radial direction ~ atan(drho/(rho dtheta))
        drho=np.gradient(rho,np.radians(TH[1]-TH[0])); pa=np.degrees(np.arctan(np.abs(drho)/rho)).max()
        amin=np.degrees(alpha_for_pull(l['stroke']))
        print(f"{k:2d} {l['name']:8s} lines {len(l['who'])}  pull max {p.max():.2f}  nose rho {rho.min():.1f}-{rho.max():.1f}  max pressure angle {pa:.0f}°  tip z {TZ0-l['stroke']:.1f}-{TZ0:.1f}  force {force(l):.2f} N")
    print('peak servo torque %.0f N·mm at %.0f°  (MG90S ~176)'%(tot.max(),TH[tot.argmax()]))
