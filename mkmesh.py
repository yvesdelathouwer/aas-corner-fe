# mkmesh.py C OUT.med  -- rebuild the v8 AAS-corner FE mesh (h_ef = 100, d = 16) for corner distance C [mm]
# Reverse-engineered from the package meshes m8_h100_d16_ct{50,75,100}; validated 27 Sep 2026:
# regenerated C=50 gives 0.02 mm -> 12953 N (package mesh 12886 N, +0.5 %).
# Half model z>=0 (SYMZ), block [0,C+220]^2 x [0,220]; corner edge = line x=0,y=0 along z.
# Tension anchor: axis +x at (y=C,z=0): steel r8 x0-100, head r16 x86.4-100, soft sleeve r8-11 x0-86.4,
#   hard zone HZ r<20 x0-84.4, elastic head zone HZH r<22 x84.4-106. Loaded end face HEADT at x=0.
# Shear anchor: axis +y at (x=C,z=0): steel r8 y0-100 (interrupted by the tension sleeve where they cross),
#   hard zone HZ r<15. Loaded end face HEADV at y=0.
# Needs gmsh >= 4.11 python module. Writes MED directly (group names = physical names).
import sys, math, random, gmsh
C = float(sys.argv[1]); out = sys.argv[2]
L = C + 220.0; H = 220.0
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.model.add("v8")
occ = gmsh.model.occ
def cylx(x0, x1, r): return (3, occ.addCylinder(x0, C, 0, x1 - x0, 0, 0, r))
def cyly(y0, y1, r): return (3, occ.addCylinder(C, y0, 0, 0, y1 - y0, 0, r))
random.seed(1)
box = (3, occ.addBox(0, 0, 0, L, L, H))
tools = [cylx(0, 100, 8), cylx(86.4, 100, 16), cylx(0, 86.4, 11), cylx(84.4, 106, 22), cylx(0, 84.4, 20),
         cyly(0, 100, 8), cyly(0, 100, 15)]
clipped = []
for t in tools:
    bb = (3, occ.addBox(0, 0, 0, L, L, H)); r, _ = occ.intersect([t], [bb]); clipped += r
occ.fragment([box], clipped); occ.synchronize()
def classify(p):
    x, y, z = p; rT = math.hypot(y - C, z); rV = math.hypot(x - C, z)
    if rT < 8 and x < 100: return 'STEEL'          # tension bar
    if rT < 16 and 86.4 < x < 100: return 'STEEL'  # tension head
    if rT < 11 and x < 86.4: return 'SLV'          # sleeve (interrupts the shear bar at the crossing)
    if rV < 8 and y < 100: return 'STEEL'          # shear bar
    if rT < 22 and 84.4 < x < 106: return 'HZH'
    if (rT < 20 and x < 84.4) or (rV < 15 and y < 100): return 'HZ'
    return 'CONC'
vol = {}
for d, t in gmsh.model.getEntities(3):
    bb = gmsh.model.getBoundingBox(d, t); p = None
    for _ in range(20000):
        q = [bb[i] + (bb[i + 3] - bb[i]) * random.random() for i in range(3)]
        if gmsh.model.isInside(d, t, q): p = q; break
    if p is None: raise SystemExit("no inside point for volume %d" % t)
    vol.setdefault(classify(p), []).append(t)
for i, (k, v) in enumerate(sorted(vol.items())): gmsh.model.addPhysicalGroup(3, v, tag=1001 + i, name=k)
eps = 1e-3
def faces(cond): return [t for d, t in gmsh.model.getEntities(2) if cond(gmsh.model.getBoundingBox(d, t))]
gmsh.model.addPhysicalGroup(2, faces(lambda b: abs(b[2]) < eps and abs(b[5]) < eps), tag=2001, name='SYMZ')
gmsh.model.addPhysicalGroup(2, faces(lambda b: abs(b[0] - L) < eps and abs(b[3] - L) < eps), tag=2002, name='FARX')
gmsh.model.addPhysicalGroup(2, faces(lambda b: abs(b[1] - L) < eps and abs(b[4] - L) < eps), tag=2003, name='FARY')
gmsh.model.addPhysicalGroup(2, faces(lambda b: abs(b[0]) < eps and abs(b[3]) < eps and b[1] > C - 8.01 and b[4] < C + 8.01 and b[5] < 8.01), tag=2004, name='HEADT')
gmsh.model.addPhysicalGroup(2, faces(lambda b: abs(b[1]) < eps and abs(b[4]) < eps and b[0] > C - 8.01 and b[3] < C + 8.01 and b[5] < 8.01), tag=2005, name='HEADV')
fm = gmsh.model.mesh.field
def cyl(xc, yc, ax, ay, az, r, v):
    c = fm.add("Cylinder"); fm.setNumber(c, "Radius", r); fm.setNumber(c, "VIn", v); fm.setNumber(c, "VOut", 1e3)
    for k, val in (("XCenter", xc), ("YCenter", yc), ("ZCenter", 0), ("XAxis", ax), ("YAxis", ay), ("ZAxis", az)): fm.setNumber(c, k, val)
    return c
a1 = cyl(53, C, 106, 0, 0, 20.5, 3.0); a2 = cyl(C, 50, 0, 100, 0, 16, 3.0)
a3 = cyl(53, C, 106, 0, 0, 30, 6.0); a4 = cyl(C, 50, 0, 100, 0, 26, 6.0)
bx = fm.add("Box"); fm.setNumber(bx, "VIn", 11); fm.setNumber(bx, "VOut", 45)
for k, v in (("XMin", 0), ("XMax", C + 150), ("YMin", 0), ("YMax", C + 150), ("ZMin", 0), ("ZMax", 150), ("Thickness", 50)): fm.setNumber(bx, k, v)
mn = fm.add("Min"); fm.setNumbers(mn, "FieldsList", [a1, a2, a3, a4, bx]); fm.setAsBackgroundMesh(mn)
for k, v in (("Mesh.MeshSizeExtendFromBoundary", 0), ("Mesh.MeshSizeFromPoints", 0), ("Mesh.MeshSizeFromCurvature", 0),
             ("Mesh.Algorithm", 5), ("Mesh.Algorithm3D", 1), ("Mesh.ElementOrder", 2), ("Mesh.SecondOrderLinear", 1),
             ("Mesh.Optimize", 1), ("Mesh.SaveAll", 0), ("General.NumThreads", 2)):
    gmsh.option.setNumber(k, v)
gmsh.model.mesh.generate(3)
gmsh.write(out)
print("C", C, "nodes", len(gmsh.model.mesh.getNodes()[0]), {k: len(v) for k, v in vol.items()})
gmsh.finalize()
