# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome - CAD / fabrication source script
# Purpose : Keeps every web of the lace wing pattern >= 2.5 mm so the film does not tear.
# Author  : Yuwen Wang
# Credits : Developed with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed by
#           the author. Libraries: CadQuery, numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib.
# Note    : hard-coded paths (e.g. /home/claude/...) point to the original working folders;
#           change them before running again. See README.md in this folder.
# ---------------------------------------------------------------------------------------------
"""Enforce a minimum material width (web) on the laser-cut wings while keeping the AI pattern.
Each hole retreats symmetrically from its neighbours (pair gap g < W -> each side gives up (W-g)/2)
and fully from the wing outline (holes keep >= W from every outer edge, incl. the hinge root cut)."""
from wings_ai import *
from shapely.geometry import Polygon
from shapely.ops import unary_union
W=2.5
MIN_HOLE_W=1.0      # holes thinner than this after trimming are dropped (they would read as scratches)
MIN_HOLE_A=1.5      # mm^2

def enforce(w, Wmin=W, iters=4):
    O=Polygon(w.exterior)
    H=[Polygon(r) for r in w.interiors]
    inner=O.buffer(-Wmin, join_style=1)
    for _ in range(iters):
        new=[]
        for i,h in enumerate(H):
            g=h.intersection(inner)
            for j,hj in enumerate(H):
                if j==i: continue
                d=h.distance(hj)
                if d<Wmin-1e-3: g=g.difference(hj.buffer(Wmin/2+d/2, resolution=24))
            new.append(g)
        # split, clean, drop slivers
        H=[]
        for g in new:
            for q in getattr(g,'geoms',[g]):
                if q.geom_type!='Polygon' or q.is_empty: continue
                q=q.buffer(-MIN_HOLE_W/2, join_style=1).buffer(MIN_HOLE_W/2, join_style=1)   # only shrinks the hole
                for qq in getattr(q,'geoms',[q]):
                    if qq.geom_type=='Polygon' and qq.area>=MIN_HOLE_A: H.append(qq.simplify(0.01))
        if min_web(O,H)>=Wmin-0.02: break
    out=O
    for h in H: out=out.difference(h)
    return out, H

def min_web(O,H):
    m=99
    for i,h in enumerate(H):
        m=min(m,h.exterior.distance(O.exterior))
        for j in range(i+1,len(H)): m=min(m,h.distance(H[j]))
    return m

_cache={}
def wing_half_W(scale,sd,hx):
    k=(scale,hx)
    if k not in _cache: _cache[k]=enforce(wing_half(scale,1,hx))[0]
    g=_cache[k]
    return g if sd==1 else affinity.scale(g,-1,1,origin=(0,0))

if __name__=='__main__':
    for name,sc,hx in (('L150',1.0,3.0),('S75',0.5,1.5),('S53',0.35,1.5)):
        w=wing_half(sc,1,hx); g,H=enforce(w)
        print(f'{name}: holes {len(w.interiors)} -> {len(H)}, min web {min_web(Polygon(w.exterior),H):.2f} mm, open area {sum(p.area for p in [Polygon(r) for r in w.interiors]):.0f} -> {sum(h.area for h in H):.0f} mm2')

def enforce_merge(w, Wmin=W):
    """small sizes: instead of shrinking every hole, dissolve the thin webs (neighbouring holes merge into one
    bigger window), then keep Wmin from the outline and between the resulting windows."""
    O=Polygon(w.exterior); H=[Polygon(r) for r in w.interiors]
    merged=unary_union([h.buffer(Wmin/2, join_style=1) for h in H]).buffer(-Wmin/2, join_style=1)
    ww=O
    for q in getattr(merged,'geoms',[merged]): ww=ww.difference(q)
    ww=ww.buffer(0)
    if ww.geom_type!='Polygon': ww=max(ww.geoms,key=lambda q:q.area)
    return enforce(ww, Wmin)

def enforce_select(w, Wmin=W, fmin=0.5, order='area'):
    """keep the pattern's look: holes keep their own shape (only scaled about their centroid);
    big holes first, a hole is shrunk until it clears the outline and the holes already kept by Wmin,
    and dropped if it would have to shrink below fmin of its size."""
    O=Polygon(w.exterior); H=[Polygon(r) for r in w.interiors]
    inner=O.buffer(-Wmin, join_style=1)
    kept=[]
    for h in sorted(H,key=lambda q:-q.area):
        c=h.centroid; ok=None
        for f in np.linspace(1.0,fmin,26):
            q=affinity.scale(h,f,f,origin=c)
            if inner.contains(q) and all(q.distance(k)>=Wmin for k in kept): ok=q; break
        if ok is not None and ok.area>=MIN_HOLE_A: kept.append(ok)
    out=O
    for k in kept: out=out.difference(k)
    return out, kept

def enforce_best(w, Wmin=W, fmin=0.4, tries=150, seed=1):
    """try many hole orders for the greedy pick, keep the one that keeps the most pattern (count + open area)"""
    O=Polygon(w.exterior); H=[Polygon(r) for r in w.interiors]
    inner=O.buffer(-Wmin, join_style=1); rng=np.random.default_rng(seed)
    pre=[]
    for h in H:   # per-hole candidate shapes (scaled copies) that clear the outline
        c=h.centroid; cs=[affinity.scale(h,f,f,origin=c) for f in np.linspace(1.0,fmin,21)]
        pre.append([q for q in cs if inner.contains(q) and q.area>=MIN_HOLE_A])
    best=None
    orders=[sorted(range(len(H)),key=lambda i:-H[i].area)]+[list(rng.permutation(len(H))) for _ in range(tries)]
    for od in orders:
        kept=[]
        for i in od:
            for q in pre[i]:
                if all(q.distance(k)>=Wmin for k in kept): kept.append(q); break
        sc=sum(k.area for k in kept)/sum(h.area for h in H)+0.03*len(kept)
        if best is None or sc>best[0]: best=(sc,kept)
    kept=best[1]; out=O
    for k in kept: out=out.difference(k)
    return out, kept
