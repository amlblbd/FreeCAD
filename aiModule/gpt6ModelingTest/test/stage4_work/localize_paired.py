import FreeCAD as A,Part,json,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sh=Part.Shape();sh.read(str(p/'paired_solid.brep'));out=[]
for i,f in enumerate(sh.Faces):
 try:f.check(True);v='passed'
 except Exception as e:v=str(e)
 if v!='passed':out.append(dict(face=i+1,center=[f.CenterOfMass.x,f.CenterOfMass.y,f.CenterOfMass.z],area=f.Area,error=v))
 (p/'paired_bad_faces.json').write_text(json.dumps(out,indent=2))
