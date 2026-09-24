import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');out=[]
for ix in [134,138,159,249]:
 s=Part.Shape();s.read(str(p/('tab_face_'+str(ix)+'.brep')));f=s.Faces[0];n=f.normalAt(0,0)
 for t in [2.,2.5,3.]:
  solid=f.extrude(-n*t);r=dict(face=ix,thickness=t,valid=solid.isValid(),closed=solid.isClosed(),solids=len(solid.Solids),volume=solid.Volume)
  try:solid.check(True);r['bop']='passed'
  except Exception as e:r['bop']=str(e)
  out.append(r)
(p/'tabs_parameter_validation.json').write_text(json.dumps(out,indent=2))
