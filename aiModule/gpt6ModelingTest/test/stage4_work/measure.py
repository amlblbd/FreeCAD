import FreeCAD as A,Part,json,traceback,sys,collections,math
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/B_pillar_stage3.FCStd');s=d.getObject('ReferenceSTEP').Shape;rows=[];samples=[]
 for i,f in enumerate(s.Faces):
  if type(f.Surface).__name__!='OffsetSurface':continue
  val=f.Surface.OffsetValue;rows.append(dict(face=i+1,area=f.Area,offset=val))
  if f.Area<1000:continue
  a,b,c,e=f.ParameterRange
  for frac in [.3,.5,.7]:
   u=a+(b-a)*frac;v=c+(e-c)*.5;q=f.valueAt(u,v)
   if Part.Vertex(q).distToShape(f)[0]>1e-6:continue
   n=f.normalAt(u,v);line=Part.makeLine(q-n*.05,q-n*8)
   hits=s.section(line).Vertexes;ds=sorted((h.Point-q).Length for h in hits if (h.Point-q).Length>.1)
   if ds:samples.append(dict(face=i+1,point=[q.x,q.y,q.z],thickness=ds[0]))
 (p/'thickness_measurement.json').write_text(json.dumps(dict(offset_faces=rows,normal_ray_samples=samples),indent=2))
 A.closeDocument(d.Name)
except:(p/'measurement_error.txt').write_text(traceback.format_exc())
