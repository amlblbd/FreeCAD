import FreeCAD as A,Part,json,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 s=Part.Shape();s.read('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3/smooth_outer.brep');s.sewShape();r=dict(input_faces=len(s.Faces),shells=len(s.Shells));(p/'reference_offset.json').write_text(json.dumps(r))
 t=time.time();q=s.makeOffsetShape(-2.5,.01,fill=True);q.exportBrep(str(p/'reference_shell_solid.brep'));r.update(seconds=time.time()-t,valid=q.isValid(),solids=len(q.Solids),faces=len(q.Faces),volume=q.Volume);(p/'reference_offset.json').write_text(json.dumps(r))
 try:q.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'reference_offset.json').write_text(json.dumps(r,indent=2))
except:(p/'reference_offset_error.txt').write_text(traceback.format_exc())
