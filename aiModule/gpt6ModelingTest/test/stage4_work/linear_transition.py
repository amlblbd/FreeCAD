import FreeCAD as A,Part,json,sys,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
try:
 rows=[json.loads((p/f).read_text()) for f in ['full_profiles.json','inner_profiles.json']];curves=[]
 for rr in rows:
  cc=[]
  for r in rr:
   c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*q) if len(q)==3 else A.Vector(*q,r['height']) for q in r['poles']],r['mults'],r['knots'],False,3);cc.append(c)
  curves.append(cc)
 sh=[]
 for f in ['complete_outer.brep','paired_inner.brep']:
  s=Part.Shape();s.read(str(p/f));sh.append(s.Faces[0].Surface)
 fs=[]
 for k in range(len(rows[0])-1):
  faces=[];h=rows[0][k]['height']
  for ix in range(2):
   if 40<=h<55:
    a,b=curves[ix][k:k+2];s=Part.BSplineSurface();s.buildFromPolesMultsKnots([[v,w] for v,w in zip(a.getPoles(),b.getPoles())],a.getMultiplicities(),[2,2],a.getKnots(),[0.,1.],False,False,3,1);f=s.toShape()
   else:
    s=sh[ix].copy();ks=s.getVKnots();s.segment(0.,1.,ks[k],ks[k+1]);f=s.toShape()
   faces.append(f)
  fo,fi=faces;fs.extend(faces)
  for ei in [0,2]+([1] if k==0 else [])+([3] if k==len(rows[0])-2 else []):fs.append(Part.makeRuledSurface(fo.Edges[ei],fi.Edges[ei],1))
 shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'linear_transition.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),solids=len(solid.Solids),volume=solid.Volume)
 (p/'linear_transition.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'linear_transition.json').write_text(json.dumps(r,indent=2))
except:(p/'linear_transition_error.txt').write_text(traceback.format_exc())
