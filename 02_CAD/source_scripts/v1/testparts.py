# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Small test prints: one slider module cut out of the dome, to check fits before the full print.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np, cadquery as cq
from dome_cad import *
def test_module(idx,skirt=56.0):
    """one slider module cut out of the dome, with a skirt so it stands upright (axis vertical)"""
    b=LAY[idx]; n,h,s,ap,k,ys=module(b)
    d=build_dome()
    keep=axcyl(ap-n*(skirt+5),ap+n*20,16.0)
    piece=d.intersect(keep)
    sk=axcyl(ap-n*skirt,ap-n*2.0,17.5).cut(axcyl(ap-n*(skirt+1),ap+n*1,15.5))
    win=axcyl(ap-n*(skirt-6)+s*20,ap-n*(skirt-6)-s*20,6.0)      # side window for the lines / sheath
    piece=piece.union(sk).cut(win).cut(axcyl(ap-n*(skirt+1)+h*20,ap-n*(skirt+1)-h*20,0.1))
    # cut the foot flat: plane through ap-n*skirt normal n
    foot=ap-n*skirt
    big=axcyl(foot-n*40,foot,60.0); piece=piece.cut(big)
    return piece,ap,n,h,s
def test_frame():
    fl,sv=build_floor()
    region=box(92,46,60,-15,-29,-1)
    return fl.intersect(region)
if __name__=='__main__':
    for idx,name in ((0,'TEST_module_big'),(4,'TEST_module_small')):
        p,ap,n,h,s=test_module(idx); cq.exporters.export(p,f'out/{name}.stl',tolerance=0.02,angularTolerance=0.15); cq.exporters.export(p,f'out/{name}.step')
        np.save(f'out/_{name}_frame.npy',np.vstack([ap,n,h,s]))
        print(name,'vol %.1f'%(p.val().Volume()/1000))
    f=test_frame(); cq.exporters.export(f,'out/TEST_drive_frame.stl',tolerance=0.02,angularTolerance=0.15); cq.exporters.export(f,'out/TEST_drive_frame.step')
    bb=f.val().BoundingBox(); print('frame %.0f x %.0f x %.0f'%(bb.xlen,bb.ylen,bb.zlen))
