# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Builds the dome, plinth, floor, cam drum, rockers, sliders and bodies -> STEP / STL.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import sys, json, numpy as np, cadquery as cq
sys.path.insert(0,'/home/claude/cad'); sys.path.insert(0,'/home/claude/dome')
from dp import *
from lay import frame
from cams import cam_poly, rocker_poly
from kin import LINES, alpha_for_pull, tip, A0
def cyl(r,h,x=0,y=0,z=0): return cq.Workplane('XY').workplane(offset=z).center(x,y).circle(r).extrude(h)
def box(dx,dy,dz,x=0,y=0,z=0): return cq.Workplane('XY').box(dx,dy,dz,centered=(True,True,False)).translate((x,y,z))
def axcyl(p0,p1,r):
    p0=np.asarray(p0,float); p1=np.asarray(p1,float); d=p1-p0; L=float(np.linalg.norm(d))
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r,L,cq.Vector(*p0),cq.Vector(*(d/L))))
def poly2solid(g,x0,t):
    out=None
    for gg in getattr(g,'geoms',[g]):
        gg=gg.simplify(0.02)
        w=cq.Workplane('YZ').workplane(offset=x0).polyline([tuple(p) for p in list(gg.exterior.coords)[:-1]]).close().extrude(t)
        for r in gg.interiors: w=w.cut(cq.Workplane('YZ').workplane(offset=x0-0.1).polyline([tuple(p) for p in list(r.coords)[:-1]]).close().extrude(t+0.2))
        out=w if out is None else out.union(w)
    return out
DC=np.array([0,0,ZD])                                     # dome centre
# ================= butterflies / modules =================
def body_scale(b): return 2.0 if b['kind']=='L' else 1.0
def body_span_eq(b): return 75.3 if b['kind']=='L' else 150.6*b['scale']
def module(b):
    n,h,s=frame(b['polar'],b['az']); rot=np.radians(b.get('rot',0)); h,s=np.cos(rot)*h+np.sin(rot)*s,np.cos(rot)*s-np.sin(rot)*h
    k=body_scale(b); ys=4.25*k
    axis_pt=DC+RD*n+ys*h                                  # sleeve axis passes under the body socket
    return n,h,s,axis_pt,k,ys
# ================= D1 dome =================
def build_dome():
    d=cq.Workplane('XY').sphere(RD).cut(cq.Workplane('XY').sphere(RD-DW)).cut(box(400,400,200,0,0,-200)).translate(tuple(DC))
    d=d.union(cyl(RD-DW,3.0,0,0,ZD).cut(cyl(RD-DW-5.0,4,0,0,ZD-0.5)))           # base ring 5 wide
    for a in (45,135,225,315):
        x,y=(RD-DW-2.5)*np.cos(np.radians(a)),(RD-DW-2.5)*np.sin(np.radians(a)); d=d.cut(cyl(0.8,7,x,y,ZD-0.5))
    for b in LAY:
        n,h,s,ap,k,ys=module(b)
        e1=s; e2=h
        d=d.union(axcyl(ap-n*SL_LEN,ap-n*1.6,5.0))
    for b in LAY:
        n,h,s,ap,k,ys=module(b); e1=s; e2=h
        d=d.cut(axcyl(ap-n*(SL_LEN+1),ap+n*3,SL_BORE/2))
        for sg in (1,-1):
            c=ap+e1*3.4+e2*1.2*sg
            d=d.cut(axcyl(c-n*(SL_LEN+1),c+n*3,0.5))
        sa=ap+e1*3.4+e2*1.2-n*SL_LEN; d=d.cut(axcyl(sa-n*1,sa+n*3.0,1.075))           # bob sheath seat
        g0=ap+e1*3.4; d=d.cut(axcyl(g0+e2*1.2-n*0.6,g0-e2*1.2-n*0.6,0.45).union(axcyl(g0+e2*1.2+n*1.0,g0-e2*1.2+n*1.0,0.45)))  # surface groove for the U-turn
    return d.clean()
# ================= sliders =================
def slider(b):
    n,h,s,ap,k,ys=module(b)
    top=RD+b['clr']-6.8*k+4.5                             # socket top (along the axis from the dome centre)
    bot=RD-SL_LEN-SPRING_L0                               # fitting top at rest
    L=top-bot
    r=cyl(ROD_D/2,L,0,0,0).union(cyl(2.5,6,0,0,-6)).cut(cyl(ROD_BORE/2,L+8,0,0,-7))
    r=r.cut(cyl(1.075,3.0,0,0,-6.01))                     # flap sheath seat (moves with the slider)
    r=r.cut(cq.Workplane('YZ').workplane(offset=-4).center(0,-1.8).circle(0.5).extrude(8))   # cross hole: tie the bob line
    return r,L
# ================= bodies =================
import body as BD
def body_for(b):
    k=body_scale(b); sp=body_span_eq(b)
    BD.ARM_ZONE=ARM_ZONE_L if k!=1.0 else ARM_ZONE_S        # open arm zone (half length); small: 2.5 mm laser arms side by side
    BD.Z_WALL_TOP=-(ACR_T+0.1)/k                             # wall top sits 0.1 below the acrylic stiffener (body is scaled by k afterwards)
    bb,L=BD.body(sp); bb=bb.cut(box(3,3,3,0,0.8,BD.Z_BOT-3.0))           # drop the old locating pin
    if k!=1.0: bb=cq.Workplane('XY').add(bb.val().scale(k))
    ys=4.25*k; zb=BD.Z_BOT*k
    bb=bb.cut(cyl(1.65,4.5,0,ys,zb-0.01))
    p0=np.array([0,0.6*k,-4.0*k]); p1=np.array([0,ys,zb+4.5]); bb=bb.cut(axcyl(p0,p1+(p1-p0)/np.linalg.norm(p1-p0)*0.4,0.6))
    return bb,L*k
# ================= drive =================
def x_of(k): return DRUM_X0+PITCH*k+CAM_T/2
def build_drum():
    d=None
    for k,l in enumerate(LINES):
        prof,_=cam_poly(l); s_=poly2solid(prof,DRUM_X0+PITCH*k,CAM_T)
        d=s_ if d is None else d.union(s_)
    core=cq.Workplane('YZ').workplane(offset=DRUM_X0-0.6).circle(6.0).extrude(PITCH*N_CAM+0.6)
    d=d.union(core).union(cq.Workplane('YZ').workplane(offset=-DRUM_X0).circle(3.4).extrude(5.0))
    d=d.cut(cq.Workplane('YZ').workplane(offset=DRUM_X0-1).circle(2.3).extrude(PITCH*N_CAM+8))
    d=d.cut(cq.Workplane('YZ').workplane(offset=DRUM_X0-0.61).circle(3.8).extrude(1.6))          # horn hub recess
    d=d.cut(cq.Workplane('YZ').workplane(offset=DRUM_X0-0.61).center(0,-3.5).rect(5.9,7.0).extrude(1.6))   # trimmed horn arm key
    return d.translate((0,DRUM_Y,DRUM_Z))
def build_rocker():
    from shapely.geometry import Point
    g=rocker_poly(); r=poly2solid(g,0,RK_T)                                   # arms 2.8 thick, flush with the hub face that lies on the bed
    hub=poly2solid(Point(0,0).buffer(3.0,resolution=24).difference(Point(0,0).buffer(1.1,resolution=24)),0,PITCH)   # hub = full pitch -> rockers stack hub-to-hub, aligned with the cams
    return r.union(hub)
def build_spacer(L):
    return cq.Workplane('YZ').circle(3.0).circle(1.1).extrude(L)
SV_SH=np.array([DRUM_X0-1.2,DRUM_Y,DRUM_Z])   # horn face
def build_servo_dummy():
    xb=SV_SH[0]-33.6
    sv=box(28.5,SV_L,SV_W,0,0,0).translate((0,0,-SV_W/2)).translate((xb+14.25,DRUM_Y+SV_SHAFT_OFF,DRUM_Z))
    ears=box(2.5,SV_EAR_SPAN,SV_W,0,0,0).translate((0,0,-SV_W/2)).translate((xb+18+1.25,DRUM_Y+SV_SHAFT_OFF,DRUM_Z))
    sh=cq.Workplane('YZ').workplane(offset=xb+28.5).center(DRUM_Y,DRUM_Z).circle(2.4).extrude(33.6-28.5-1.6)
    hub=cq.Workplane('YZ').workplane(offset=SV_SH[0]-1.6).center(DRUM_Y,DRUM_Z).circle(3.7).extrude(1.6)
    return sv.union(ears).union(sh).union(hub),xb
def build_floor():
    f=cyl(R_IN-0.2,FLOOR_T)
    sv,xb=build_servo_dummy()
    yc=DRUM_Y+SV_SHAFT_OFF
    f=f.union(box(20,SV_L-2,DRUM_Z-SV_W/2-FLOOR_T,xb+12,yc,FLOOR_T))                                  # servo saddle
    for sg in (1,-1):
        ye=yc+sg*SV_EAR_HOLE/2
        post=box(4.0,5.0,DRUM_Z+3-FLOOR_T,xb+18-2.0,ye,FLOOR_T).cut(cq.Workplane('YZ').workplane(offset=xb+18-6).center(ye,DRUM_Z).circle(0.8).extrude(8))
        f=f.union(post)
    xr=-DRUM_X0+2.0
    f=f.union(box(5,9,DRUM_Z+5-FLOOR_T,xr+2.5,DRUM_Y,FLOOR_T).cut(cq.Workplane('YZ').workplane(offset=xr-1).center(DRUM_Y,DRUM_Z).circle(3.6).extrude(8)))
    for xp in (DRUM_X0-3.2,-DRUM_X0+2.2):
        w=4.0 if xp>0 else 3.0
        p=box(w,6,PIV_Z+3-FLOOR_T,xp+(w/2 if xp>0 else -w/2+0),PIV_Y,FLOOR_T).cut(cq.Workplane('YZ').workplane(offset=xp-5).center(PIV_Y,PIV_Z).circle(1.05).extrude(12))
        f=f.union(p)
    for (u,v) in ((14.0,2.5),(15.3,50.7),(66.1,7.6),(66.1,35.5)):
        x,y=v-26.67,UNO_Y0-u; f=f.union(cyl(2.6,4,x,y,FLOOR_T)).cut(cyl(1.3,6,x,y,FLOOR_T+0.5))
    for a in (45,135,225,315):
        x,y=66*np.cos(np.radians(a)),66*np.sin(np.radians(a)); f=f.cut(cyl(1.1,5,x,y,-0.5)).cut(cyl(2.1,1.3,x,y,-0.01))
    return f.clean(),sv
UNO_Y0=63.6
def seat_xy():
    S=[]
    for k,l in enumerate(LINES):
        n=len(l['who']); ty=tip(A0)[0]
        ys=[ty] if n==1 else list(ty+3.3*(np.arange(n)-(n-1)/2))
        for j,y in enumerate(ys): S.append((k,j,x_of(k),y))
    return S
def build_plinth():
    p=cyl(R_OUT,HP).cut(cyl(R_IN,HP-TOP_T,0,0,-0.01))
    p=p.union(cyl(R_IN,1.5,z=FLOOR_T).cut(cyl(R_IN-2.5,3,z=FLOOR_T-0.5)))
    for a in (45,135,225,315):
        x,y=66*np.cos(np.radians(a)),66*np.sin(np.radians(a)); p=p.union(cyl(3.2,9,x,y,FLOOR_T)).cut(cyl(0.8,10,x,y,FLOOR_T-0.5))
        x,y=(RD-DW-2.5)*np.cos(np.radians(a)),(RD-DW-2.5)*np.sin(np.radians(a)); p=p.cut(cyl(1.1,5,x,y,HP-4)).cut(cyl(2.1,1.3,x,y,HP-TOP_T-0.01))
    for (k,j,x,y) in seat_xy():
        p=p.cut(cyl(0.6,5,x,y,HP-TOP_T-1)).cut(cyl(1.075,2.0,x,y,HP-2.0))
    zc=FLOOR_T+4+1.6+5.5
    for (xc,w,hh) in ((38.1-26.67,12.5,11.5),(7.6-26.67,9.5,11.5)):
        yw=np.sqrt(R_OUT**2-xc**2); p=p.cut(box(w+1,12,hh+1,xc,yw,zc-(hh+1)/2))
    return p.clean()
def build_splitter(n):
    w=3.3*(n-1)+3.0; s=box(w,3.0,2.0,0,0,0).edges('|Z').fillet(1.2)
    for j in range(n): s=s.cut(cyl(0.5,3,-(n-1)*1.65+3.3*j,0,-0.5))
    return s.cut(box(0.8,4,0.8,0,0,-0.01)) if False else s.rotate((0,0,0),(0,0,1),90)
if __name__=='__main__':
    import os, time; os.makedirs('out',exist_ok=True); t0=time.time()
    def ex(p,n): cq.exporters.export(p,f'out/{n}.stl',tolerance=0.02,angularTolerance=0.15); cq.exporters.export(p,f'out/{n}.step')
    if 'drive' in sys.argv:
        drum=build_drum(); ex(drum,'C_cam_drum'); print('drum',round(time.time()-t0))
        ex(build_rocker(),'R_rocker_x12'); fl,sv=build_floor(); ex(fl,'P0_floor'); cq.exporters.export(sv,'out/_servo.stl')
        ex(build_plinth(),'P1_plinth_with_top_plate'); ex(build_splitter(4),'Q_splitter_4holes_x4'); ex(build_spacer(2.6),'T_spacer_x2'); print('plinth',round(time.time()-t0))
    dome=build_dome(); ex(dome,'D1_dome'); print('dome',round(time.time()-t0))
    for i,b in enumerate(LAY):
        s_,L=slider(b); ex(s_,f'S{i+1:02d}_slider_{"L" if b["kind"]=="L" else "S"}{L:.1f}')
    done=set()
    for b in LAY:
        key=(b['kind'],b['scale'])
        if key in done: continue
        done.add(key); bb,L=body_for(b); ex(bb,f'K_body_{"L150" if b["kind"]=="L" else ("S75" if b["scale"]==0.5 else "S53")}')
    print('all',round(time.time()-t0))
