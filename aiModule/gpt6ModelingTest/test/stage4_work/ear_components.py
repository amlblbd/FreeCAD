import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');fs=[]
for f in ['complete_outer.brep','paired_inner.brep']:
 sh=Part.Shape();sh.read(str(p/f));s=sh.Faces[0].Surface;s.segment(0.,1.,40.,55.);fs.append(s.toShape())
r=[]
for name,faces in [('outer',[fs[0]]),('inner',[fs[1]]),('outer_inner',fs),('left_cap',[Part.makeRuledSurface(fs[0].Edges[0],fs[1].Edges[0],1)]),('right_cap',[Part.makeRuledSurface(fs[0].Edges[2],fs[1].Edges[2],1)])]:
 sh=Part.makeCompound(faces);rr=dict(name=name)
 try:sh.check(True);rr['bop']='passed'
 except Exception as e:rr['bop']=str(e)
 r.append(rr);(p/'ear_components.json').write_text(json.dumps(r,indent=2))
