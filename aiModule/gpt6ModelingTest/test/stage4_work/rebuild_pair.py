import FreeCAD as A,Part,json,sys
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
d=A.newDocument();objs=[]
for r in json.loads((p/'full_profiles.json').read_text()):
 c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*q) if len(q)==3 else A.Vector(*q,r['height']) for q in r['poles']],r['mults'],r['knots'],False,3);o=d.addObject('Part::Feature','S');o.Shape=c.toShape();objs.append(o)
s=BPillarSurface.surface(objs);s.exportBrep(str(p/'complete_outer.brep'));A.closeDocument(d.Name)
exec(compile((p/'paired_trial.py').read_text(encoding='utf-8-sig'),str(p/'paired_trial.py'),'exec'))
exec(compile((p/'check_paired_wall.py').read_text(encoding='utf-8-sig'),str(p/'check_paired_wall.py'),'exec'))
