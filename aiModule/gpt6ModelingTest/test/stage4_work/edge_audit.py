import FreeCAD as A,Part,json,collections
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');o=Part.Shape();o.read(str(p/'complete_outer.brep'));i=Part.Shape();i.read(str(p/'inner_test.brep'));r=[]
for a,b in zip(o.Edges,i.Edges):
 av=a.Vertexes;bv=b.Vertexes;r.append(dict(a=[[v.Point.x,v.Point.y,v.Point.z] for v in av],b=[[v.Point.x,v.Point.y,v.Point.z] for v in bv],area=Part.makeRuledSurface(a,b).Area))
s=Part.Shape();s.read(str(p/'solid_test.brep'));r.append(dict(edges=len(s.Edges),shellclosed=[x.isClosed() for x in s.Shells],faceareas=[f.Area for f in s.Faces],outerarea=o.Area,innerarea=i.Area))
(p/'edge_audit.json').write_text(json.dumps(r,indent=2))
