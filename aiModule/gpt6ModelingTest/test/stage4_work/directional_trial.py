import FreeCAD as A,Part,json,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');r=[];solids=[]
try:
 o=Part.Shape();o.read(str(p/'complete_outer.brep'));surf=o.Faces[0].Surface;v0,v1=surf.getVKnots()[0],surf.getVKnots()[-1]
 for name,u0,u1,vec in [('left',0.,.12,A.Vector(2.5,0,0)),('front',.1,.9,A.Vector(0,-2.5,0)),('right',.88,1.,A.Vector(-2.5,0,0))]:
  s=surf.copy();s.segment(u0,u1,v0,v1);f=s.toShape();sh=f.extrude(vec);rr=dict(name=name,valid=sh.isValid(),solids=len(sh.Solids),volume=sh.Volume);sh.exportBrep(str(p/('directional_'+name+'.brep')))
  try:sh.check(True);rr['bop']='passed'
  except Exception as e:rr['bop']=str(e)
  solids.append(sh);r.append(rr);(p/'directional_result.json').write_text(json.dumps(r,indent=2))
except:(p/'directional_error.txt').write_text(traceback.format_exc())
