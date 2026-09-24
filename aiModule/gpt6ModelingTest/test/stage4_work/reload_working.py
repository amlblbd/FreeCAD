import FreeCAD as A,Part,json,sys,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
try:
 d=A.openDocument(str(p.parent/'B_pillar_stage4_working.FCStd'));r=[]
 for t in [2.,3.,2.5]:
  d.Stage4Parameters.EarThickness=t;d.recompute()
  for ix in [134,138,159,249]:
   o=d.getObject('EarWall'+str(ix));o.Shape.check(True);r.append(dict(object=o.Name,thickness=t,extrusion_length=o.LengthFwd.Value,valid=o.Shape.isValid(),solids=len(o.Shape.Solids),bop='passed'))
 assert all(x['thickness']==x['extrusion_length'] and x['valid'] and x['solids']==1 for x in r)
 (p/'working_reload_validation.json').write_text(json.dumps(dict(checks=r,reference_path=d.ReferenceSTEP.SourceFile,stage3_driver=type(d.UpperMasterLoft.Proxy).__name__,saved_default=2.5),indent=2));A.closeDocument(d.Name)
except:(p/'working_reload_error.txt').write_text(traceback.format_exc())
