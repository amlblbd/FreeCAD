import FreeCAD as A,Part,json,math,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 s=Part.Shape();s.read(str(p/'paired_solid.brep'));o=Part.Shape();o.read(str(p/'complete_outer.brep'));i=Part.Shape();i.read(str(p/'paired_inner.brep'));f=o.Faces[0];a,b,c,e=f.ParameterRange;vals=[]
 r=dict(valid=s.isValid(),closed=s.isClosed(),volume=s.Volume,faces=len(s.Faces));(p/'solid_basic.json').write_text(json.dumps(r))
 for x in range(25):
  for y in range(31):
   u=a+(b-a)*(x+.5)/25;v=c+(e-c)*(y+.5)/31;q=f.valueAt(u,v);dist=Part.Vertex(q).distToShape(i)[0];vals.append([q.x,q.y,q.z,dist])
 r.update(samples=len(vals),min=min(x[3] for x in vals),max=max(x[3] for x in vals),rms_error=math.sqrt(sum((x[3]-2.5)**2 for x in vals)/len(vals)),worst=sorted(vals,key=lambda x:abs(x[3]-2.5))[-12:]);(p/'paired_wall_test.json').write_text(json.dumps(r,indent=2))
except:(p/'paired_wall_error.txt').write_text(traceback.format_exc())
