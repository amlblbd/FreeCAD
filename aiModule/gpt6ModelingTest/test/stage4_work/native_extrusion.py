import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');d=A.newDocument();f=d.addObject('Part::Feature','Base');s=Part.Shape();s.read(str(p/'tab_face_134.brep'));f.Shape=s;x=d.addObject('Part::Extrusion','Wall');x.Base=f;x.Dir=-s.Faces[0].normalAt(0,0);x.LengthFwd=2.5;x.Solid=True;d.recompute();(p/'native_extrusion.json').write_text(json.dumps(dict(properties=x.PropertiesList,dir=list(x.Dir),volume=x.Shape.Volume,valid=x.Shape.isValid(),solids=len(x.Shape.Solids)),indent=2))
