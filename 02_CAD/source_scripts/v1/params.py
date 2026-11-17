# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Parameters for the butterfly body and the earlier base design.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np
# ===== global frame: X right, Y back (viewer at -Y), Z up; base origin = base bottom centre =====
BASE_OD=90.0; WALL=2.0; H_SHELL=44.0; LID_T=2.0          # base total = 46 (rev B)
FLOOR_T=2.5
SHAFT=np.array([0.0,-24.0])   # rev B: moved forward so the sheath entry sits outside the line fan                               # MG90S output shaft
# MG90S nominal (check your unit: SERVO_EAR_Z is bottom -> underside of ears)
SV_L,SV_W,SV_H=22.8,12.2,28.5; SV_SHAFT_OFF=5.5; SV_EAR_SPAN=32.5; SV_EAR_T=2.5; SV_EAR_Z=18.0; SV_EAR_HOLE=27.8
SV_CEN=SHAFT+np.array([0,SV_SHAFT_OFF])                 # body centre (body extends toward +Y)
Z_SV0=0.5                                                # servo bottom sits in a 2.0-deep floor pocket (0.5 skin)
Z_DECK_TOP=Z_SV0+SV_EAR_Z                                # 20.5
Z_SV_TOP=Z_SV0+SV_H                                      # 31.0
Z_HORN_TOP=Z_SV0+32.0+1.6                                # top of stock single-arm horn ~36.1
ARM_T=2.4; Z_ARM0=Z_HORN_TOP; Z_ARM1=Z_ARM0+ARM_T        # 36.1 .. 38.5
Z_LINE=Z_ARM1+0.6                                        # line plane 39.1
# drive
RS=25.0; E=15.5; STROKE=3.15
PK=np.array([46,68,90,112,134.]); DELTA=np.array([-24,-12,0,12,24.])
ST_ANG=PK+DELTA                                          # station world angles about the shaft
STATIONS=[SHAFT+RS*np.array([np.cos(np.radians(a)),np.sin(np.radians(a))]) for a in ST_ANG]
TUBE_D=1.9; TUBE_HOLE=0.8; Z_TUBE0=9.5                   # tail tubes in the comb block
# sheath / line
SHEATH_D=2.0; SHEATH_SEAT=2.15
ENTRY=np.array([0.0,14.5]); ENTRY_D=6.4
# butterfly
SPANS=[18,22,26,30,34]
BODY_W=6.4; HINGE_X=1.5; ARM_R=3.0; ARM_DY=1.2; LT=2.6

# electronics (rev B)
XIAO_W,XIAO_L=17.8,21.0; XIAO_C=np.array([0.0,31.2]); USB_Z=FLOOR_T+3.0+1.0+1.6   # USB-C centre height
SW_X=-30.0
FLOOR_SCREW_ANG=(0,60,120,180)
WELLS=((-23,-18,6),(23,-18,6),(-26,13,14),(26,13,14))   # (x, y, height) ballast cups, inner Ø20.8
COMB_HALF=32.0   # tip block half-angle (deg)
HORN_R=13.0     # trim the stock single-arm horn to this radius
STONE_SCREWS=((-6.9,12.0),(4.0,9.0))   # M2 from below into heat-set inserts in the stone foot
STONE_FOOT=((-1.9,12.0),17.7,14.5)     # ellipse centre, width X, depth Y
STEM_LID=(14.9,11.8)   # blind hole Ø2.6 x1.5 in the lid top for the stem rod tail
