import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 outer=Part.Shape();outer.read(str(p/'inputs/stage3/smooth_outer.brep'));inner=Part.Shape();inner.read(str(p/'reference_inner_skin.brep'))
 heights=[5,10,12,14,18,22,28,36,42,44,44.8,44.9,46,47.3,47.5,49,51,53,57,60,65,70,600,602,604]
 result=[]
 for h in heights:
  row={'height':h}
  for name,skin in [('outer',outer),('inner',inner)]:
   cut=skin.section(Part.makePlane(1400,600,A.Vector(-700,-300,h)))
   row[name]=[[[v.x,v.y] for v in e.discretize(Number=max(3,int(e.Length/.3)+1))] for e in cut.Edges if e.Length>1e-5]
  result.append(row);(p/'dense_raw.json').write_text(json.dumps(result))
except:(p/'dense_error.txt').write_text(traceback.format_exc())
