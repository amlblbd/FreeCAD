import FreeCAD as A,Part,json,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');out=[]
for name in ['complete_outer','inner_test']:
 sh=Part.Shape();sh.read(str(p/(name+'.brep')));s=sh.Faces[0].Surface;kk=s.getVKnots()
 for a,b in zip(kk,kk[1:]):
  if a>100:continue
  z=s.copy();z.segment(0.,1.,a,b);t=time.time()
  try:z.toShape().check(True);v='passed'
  except Exception as e:v=str(e)
  out.append(dict(name=name,span=[a,b],bop=v,time=time.time()-t));(p/'band_checks.json').write_text(json.dumps(out,indent=2))
