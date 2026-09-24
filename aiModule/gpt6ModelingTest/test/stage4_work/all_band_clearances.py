import FreeCAD as A,Part,json,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');ss=[]
for f in ['complete_outer.brep','paired_inner.brep']:
 sh=Part.Shape();sh.read(str(p/f));ss.append(sh.Faces[0].Surface)
kn=[s.getVKnots() for s in ss];out=[]
for k,h in enumerate(kn[0][:-1]):
 fs=[]
 for j,s in enumerate(ss):
  su=s.copy();su.segment(0.,1.,kn[j][k],kn[j][k+1]);fs.append(su.toShape())
 dist,pts,sup=fs[0].distToShape(fs[1]);r=dict(height=[h,kn[0][k+1]],distance=dist,points=[[list(a),list(b)] for a,b in pts[:2]])
 if dist<1e-5:
  sh=fs[0].section(fs[1]);r.update(intersection_edges=len(sh.Edges),intersection_length=sh.Length);sh.exportBrep(str(p/('intersection_band_'+str(k)+'.brep')))
 out.append(r);(p/'all_band_clearances.json').write_text(json.dumps(out,indent=2))
