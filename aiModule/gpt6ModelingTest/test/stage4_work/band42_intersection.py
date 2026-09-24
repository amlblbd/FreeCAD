import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');fs=[]
for name in ['complete_outer.brep','paired_inner.brep']:
 sh=Part.Shape();sh.read(str(p/name));s=sh.Faces[0].Surface;s.segment(0.,1.,42.,44.);fs.append(s.toShape())
inter=fs[0].section(fs[1]);inter.exportBrep(str(p/'band42_intersection.brep'));out=[]
for e in inter.Edges:
 out.append(dict(length=e.Length,points=[list(v) for v in e.discretize(Number=21)]))
(p/'band42_intersection.json').write_text(json.dumps(out,indent=2))
