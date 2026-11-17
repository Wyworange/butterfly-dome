# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Places the butterflies on the dome (positions, clearances); writes layout.json.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import os, sys, numpy as np, json, time
_c=os.getcwd(); sys.path.insert(0,'/home/claude/v10'); os.chdir('/home/claude/v10'); import geo4 as G; os.chdir(_c)
from shapely import affinity
from shapely.geometry import Point
from scipy.spatial import cKDTree
R=75.0; LIFT=15.0
def wing_pts(scale,step):
    g=affinity.scale(affinity.translate(G.sheet,0,61.7),scale,scale,origin=(0,0)); hx=0.02*150.6*scale
    minx,miny,maxx,maxy=g.bounds; xs,ys=np.meshgrid(np.arange(hx,maxx,step),np.arange(miny,maxy,step))
    P=np.c_[xs.ravel(),ys.ravel()]; P=P[[g.contains(Point(*p)) for p in P]]
    ring=np.array(g.exterior.coords)[::2]; ring=ring[ring[:,0]>=hx]
    return np.vstack([P,ring]),hx
WP={}
def frame(polar,az):
    th,ph=np.radians(polar),np.radians(az); n=np.array([np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)])
    h=np.array([0,1.0,0]) if polar<1 else np.array([-np.cos(th)*np.cos(ph),-np.cos(th)*np.sin(ph),np.sin(th)])
    return n,h,np.cross(h,n)
INDEP=True
def states(kind):
    if INDEP: return [(l,p) for l in (0,6,12) for p in (0,30,60)]
    return [(0,0),(5,20 if kind=='L' else 0),(10,40 if kind=='L' else 0),(12.5,50 if kind=='L' else 30),(15,60)]
def cloud(b,lift,phi):
    scale=b['scale']; key=scale
    if key not in WP: WP[key]=wing_pts(scale,2.0 if scale>0.7 else 1.2)
    W,hx=WP[key]; n,h,s=frame(b['polar'],b['az']); rot=np.radians(b.get('rot',0))
    h,s=np.cos(rot)*h+np.sin(rot)*s,np.cos(rot)*s-np.sin(rot)*h
    base=R*n+n*(b['clr']+lift); p=np.radians(phi); out=[]
    for sd in (1,-1):
        x=W[:,0]-hx; y=W[:,1]
        out.append(base+sd*hx*s+y[:,None]*h+x[:,None]*(sd*np.cos(p)*s+np.sin(p)*n))
    bw=6.0*scale/0.5*0.5+3; L=12*scale+4
    g=np.mgrid[-bw/2:bw/2+0.1:1.0,-L/2:L/2+0.1:1.0,-4:0.1:1.0].reshape(3,-1).T
    out.append(base+g[:,0:1]*s+g[:,1:2]*h+g[:,2:3]*n)
    tt=np.linspace(R+0.5,R+b['clr']+lift-4,12); out.append(tt[:,None]*n[None,:])   # rod along the normal, above the dome
    cloud.nw=len(out[0])+len(out[1])
    return np.vstack(out)
def dome_ok(b):
    for lift,phi in states(b['kind']):
        c=cloud(b,lift,phi); rr=np.linalg.norm(c,axis=1)
        wing=c[:cloud.nw]
        if (np.linalg.norm(wing,axis=1)<R+1.0).any() and (wing[:,2]>-1).any():
            m=(np.linalg.norm(wing,axis=1)<R+1.0)&(wing[:,2]>0)
            if m.any(): return False
    return True
def pair_ok(b1,b2,clr):
    S1=[cKDTree(cloud(b1,l,p)) for l,p in states(b1['kind'])]
    for l2,p2 in states(b2['kind']):
        c2=cloud(b2,l2,p2)
        for T in S1:
            d,_=T.query(c2,distance_upper_bound=clr)
            if np.isfinite(d).any(): return False
    return True

def body_r(b):
    n,h,s=frame(b['polar'],b['az']); p=(R+b['clr'])*n; return float(np.hypot(p[0],p[1]))
