import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 outer=Part.Shape();outer.read(str(p/'inputs/stage3/smooth_outer.brep'));inner=Part.Shape();inner.read(str(p/'reference_inner_complete.brep'))
 heights=[42.2,42.35,42.39,42.6,43,43.5]
 result=[]
 for h in heights:
  row={'height':h}
  for name,skin in [('outer',outer),('inner',inner)]:
   cut=skin.section(Part.makePlane(1400,600,A.Vector(-700,-300,h)))
   row[name]=[[[v.x,v.y] for v in e.discretize(Number=max(3,int(e.Length/.3)+1))] for e in cut.Edges if e.Length>1e-5]
  result.append(row);(p/'local42_raw.json').write_text(json.dumps(result))
except:(p/'local42_error.txt').write_text(traceback.format_exc())
