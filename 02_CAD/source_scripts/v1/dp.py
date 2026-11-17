# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : All v1 parameters: dome, plinth, sliders, drive geometry and the cam schedule.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Dome version parameters. Frame: origin = plinth bottom centre, X right, Y back (viewer at -Y), Z up. mm."""
import numpy as np, json
HP=50.0; R_OUT=75.0; WALL=2.5; R_IN=R_OUT-WALL; FLOOR_T=3.0; TOP_T=3.0
ZD=HP                                  # dome base plane = plinth top
RD=75.0; DW=2.5                        # dome outer radius, wall
LAY=json.load(open('/home/claude/dome/cad/layout.json'))
# ---- slider module (per butterfly, along the dome normal) ----
SL_R0=RD; SL_LEN=14.0; SL_OD=9.0; SL_BORE=3.5; ROD_D=3.2; ROD_BORE=1.6; TRAVEL=12.0
SPRING_L0=17.0; COLLAR_D=5.0
# ---- drive (in the plinth) ----
SV_L,SV_W,SV_H=22.8,12.2,28.5; SV_SHAFT_OFF=5.5; SV_EAR_SPAN=32.5; SV_EAR_Z=18.0; SV_EAR_HOLE=27.8
DRUM_Y,DRUM_Z=-30.0,20.0; N_CAM=12; CAM_T=3.2; CAM_GAP=0.0; RK_T=2.8; PITCH=CAM_T+CAM_GAP
DRUM_X0=-PITCH*N_CAM/2                 # left end of the cam stack (servo side)
R_BASE=10.5
PIV_Y,PIV_Z=-14.5,34.0; ARM_IN=14.0; ARM_OUT=32.0; NOSE_R=1.5
# lines (cam index -> function); stroke = slider/wing pull needed at the butterfly
# group: which butterflies (indices into LAY) the line pulls
def kind(i): return LAY[i]['kind']
L_IDX=[i for i,b in enumerate(LAY) if b['kind']=='L']; S_IDX=[i for i,b in enumerate(LAY) if b['kind']=='S']
LINES=[]
for k,i in enumerate(L_IDX):
    LINES.append(dict(name=f'L{k+1} bob',fn='bob',who=[i],stroke=12.0))
    LINES.append(dict(name=f'L{k+1} flap',fn='flap',who=[i],stroke=6.3))
SA=S_IDX[0::2]; SB=S_IDX[1::2]
LINES+= [dict(name='Small A flap',fn='flap',who=SA,stroke=3.15+0.4),dict(name='Small B flap',fn='flap',who=SB,stroke=3.15+0.4),
         dict(name='Small A bob',fn='bob',who=SA,stroke=12.0),dict(name='Small B bob',fn='bob',who=SB,stroke=12.0)]
# timing windows on the servo sweep 0..180 (deg): list of (start, end) bumps; ramps = RAMP deg
SCHED={'L1 bob':[(0,95)],'L1 flap':[(35,85)],'L2 bob':[(28,123)],'L2 flap':[(63,113)],
       'L3 bob':[(56,151)],'L3 flap':[(91,141)],'L4 bob':[(84,180)],'L4 flap':[(122,172)],
       'Small A flap':[(14,40),(74,100),(134,160)],'Small B flap':[(44,70),(104,130)],
       'Small A bob':[(2,85)],'Small B bob':[(95,178)]}
RAMP_BOB=40.0; SPRING_F=0.20

# laser-cut stiffeners (min feature 2.5 mm): arm width / offset / open zone in the body (half length)
ARM_W_S=2.5; ARM_DY_S=1.5; ARM_ZONE_S=3.1
ARM_W_L=3.0; ARM_DY_L=2.4; ARM_ZONE_L=2.2   # L body is the k=1 body scaled x2 -> zone 4.4 actual
ACR_T=1.6   # stiffener = laser-cut acrylic 1/16" (1.59 mm)
