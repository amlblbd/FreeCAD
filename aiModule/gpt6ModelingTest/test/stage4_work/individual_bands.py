import FreeCAD as A,Part,json,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');ss=[]
for f in ['complete_outer.brep','paired_inner.brep']:
 s=Part.Shape();s.read(str(p/f));ss.append(s.Faces[0].Surface)
kn=[s.getVKnots() for s in ss];out=[]
for k,h in enumerate(kn[0][:-1]):
 if not 36<=h<60:continue
 start=time.time();faces=[]
 for j,s in enumerate(ss):
  f=s.copy();f.segment(0.,1.,kn[j][k],kn[j][k+1]);faces.append(f.toShape())
 outer,inner=faces;caps=[Part.makeRuledSurface(outer.Edges[ix],inner.Edges[ix],1) for ix in range(4)];sh=Part.makeCompound(faces+caps);sh.sewShape();solid=Part.makeSolid(sh.Shells[0]);r=dict(height=[h,kn[0][k+1]],valid=solid.isValid())
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 r['seconds']=time.time()-start;out.append(r);(p/'individual_band_checks.json').write_text(json.dumps(out,indent=2))
