# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Arranges the printed parts onto Bambu Studio 3MF print plates.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
import numpy as np, trimesh, glob, os, sys
from shapely.geometry import MultiPoint, Polygon, box as sbox
from shapely.ops import unary_union
sys.path.insert(0,'/home/claude/cad')
O='out/'
X0,X1,Y0,Y1=15.0,241.0,5.0,251.0          # X2D dual-nozzle area 235.5 wide (keep 2-3 mm margin)
def Ry(d): return trimesh.transformations.rotation_matrix(np.radians(d),[0,1,0])
def Rx(d): return trimesh.transformations.rotation_matrix(np.radians(d),[1,0,0])
def load(name,T=None):
    m=trimesh.load(O+name+'.stl'); m.metadata['name']=name; 
    if T is not None: m.apply_transform(T)
    m.apply_translation(-m.bounds[0]*[0,0,1]); return m
def footprint(m):
    return MultiPoint(m.vertices[:,:2][::max(1,len(m.vertices)//4000)]).convex_hull
def arrange(items,fixed=()):
    placed=[]; occ=[]
    for m,p in fixed: placed.append(m); occ.append(footprint(m).buffer(3))
    items=sorted(items,key=lambda m:-footprint(m).area)
    area=sbox(X0,Y0,X1,Y1)
    for m in items:
        fp=footprint(m); c=np.array(fp.centroid.coords[0]); ok=False
        for yy in np.arange(Y0,Y1,1.5):
            for xx in np.arange(X0,X1,1.5):
                b=fp.bounds; dx,dy=xx-b[0],yy-b[1]
                g=trimesh.transformations.translation_matrix([dx,dy,0])
                from shapely import affinity
                f2=affinity.translate(fp,dx,dy)
                if not area.contains(f2): continue
                if any(f2.intersects(o) for o in occ): continue
                m.apply_translation([dx,dy,0]); placed.append(m); occ.append(f2.buffer(3)); ok=True; break
            if ok: break
        if not ok: raise RuntimeError('does not fit')
    return placed
def center_on(m,x,y):
    b=m.bounds; m.apply_translation([x-(b[0,0]+b[1,0])/2,y-(b[0,1]+b[1,1])/2,0]); return m
def save(name,meshes,title):
    sc=trimesh.Scene()
    cnt={}
    for m in meshes:
        b=m.metadata.get('name','part'); cnt[b]=cnt.get(b,0)+1; nm=f"{b}_{cnt[b]}"
        sc.add_geometry(m,node_name=nm,geom_name=nm)
    sc.export(O+name+'.3mf')
    # preview
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); plt.rcParams['font.family']='Noto Sans CJK JP'
    fig,ax=plt.subplots(figsize=(7,7)); ax.add_patch(plt.Rectangle((0,0),256,256,fc='#3a3d42')); ax.add_patch(plt.Rectangle((10.25,0),235.5,256,fc='#4a4e55'))
    for m in meshes:
        f=footprint(m); ax.fill(*f.exterior.xy,fc='#e9e8e2',ec='k',lw=0.5)
    ax.set_xlim(-5,261); ax.set_ylim(-5,261); ax.set_aspect('equal'); ax.set_title(title,fontsize=11); ax.axis('off')
    plt.savefig(O+name+'.png',dpi=80,bbox_inches='tight'); plt.close(fig)
    hmax=max(m.bounds[1,2] for m in meshes); print(name,len(meshes),'parts, max height %.0f'%hmax)
sliders=sorted(glob.glob(O+'S??_slider_*.stl'))
def slider(i): return load(os.path.basename(sliders[i])[:-4])
bodies=[('K_body_L150',4),('K_body_S75',4),('K_body_S53',4)]
# ---------- plate 1: dome ----------
dome=center_on(load('D1_dome'),128,128-50)
small=[slider(i) for i in range(len(sliders))]+[load(n) for n,c in bodies for _ in range(c)]+[load('Q_splitter_4holes_x4') for _ in range(4)]+[load('T_spacer_x2',Ry(-90)) for _ in range(2)]
save('PLATE_1_dome',arrange(small,fixed=[(dome,None)]),'Plate 1: dome + 12 sliders + 12 bodies + line splitters + spacers (supports on)')
# ---------- plate 2: plinth ----------
pl=center_on(load('P1_plinth_with_top_plate',Rx(180)),128,128-50)
small=[load('C_cam_drum',Ry(-90))]+[load('R_rocker_x12',Ry(-90)) for _ in range(12)]
save('PLATE_2_plinth',arrange(small,fixed=[(pl,None)]),'Plate 2: plinth shell (top plate down) + cam drum + 12 rockers')
# ---------- plate 3: floor ----------
fl=center_on(load('P0_floor'),128,128)
save('PLATE_3_floor',[fl],'Plate 3: floor')
# ---------- test plate ----------
def up(name):
    m=trimesh.load(O+name+'.stl'); m.metadata['name']=name; F=np.load(O+'_'+name+'_frame.npy'); n=F[1]
    m.apply_transform(trimesh.geometry.align_vectors(n,[0,0,1])); m.apply_translation([0,0,-m.bounds[0,2]]); return m
small=[up('TEST_module_big'),up('TEST_module_small'),load('TEST_drive_frame'),load('C_cam_drum',Ry(-90))]+[load('R_rocker_x12',Ry(-90)) for _ in range(12)]+\
      [load('T_spacer_x2',Ry(-90)) for _ in range(2)]+[slider(0),slider(4),load('K_body_L150'),load('K_body_S75'),load('Q_splitter_4holes_x4')]
save('PLATE_TEST',arrange(small),'Test plate: 1 large + 1 small guide sleeve, small drive base, cam drum, 12 rockers, sliders, bodies')
