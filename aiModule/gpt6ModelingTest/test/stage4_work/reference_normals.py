import FreeCAD as A,Part,json,traceback,time,collections
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');q=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3')
try:
 sh=Part.Shape();sh.read(str(p/'complete_outer.brep'));s=sh.Faces[0].Surface;ref=Part.Shape();ref.read(str(q/'smooth_outer.brep'));faces=ref.Faces;owners=collections.defaultdict(list)
 for i,f in enumerate(faces):
  for e in f.Edges:owners[e.hashCode()].append(i)
 ep=[max(owners[e.hashCode()],key=lambda i:faces[i].Area) for e in ref.Edges]
 poles=s.getPoles();out=[];cached=[None]*len(poles[0]);maxdistance=0.
 for i,row in enumerate(poles):
  ns=[]
  for j,pt in enumerate(row):
   v=Part.Vertex(pt);idx=cached[j]
   if idx is not None:
    r=v.distToShape(faces[idx])
    if r[0]>.35:idx=None
   if idx is None:
    r=v.distToShape(ref);info=r[2][0]
    if info[3]=='Face':idx=info[4]
    elif info[3]=='Edge':idx=ep[info[4]]
    else:idx=min(range(len(faces)),key=lambda k:v.distToShape(faces[k])[0])
    cached[j]=idx
   target=r[1][0][1];u,vv=faces[idx].Surface.parameter(target);n=faces[idx].normalAt(u,vv);ns.append([-n.x,-n.y,-n.z]);maxdistance=max(maxdistance,r[0])
  out.append(ns)
  if i%10==0:(p/'normal_progress.json').write_text(json.dumps(dict(row=i,total=len(poles),max_distance=maxdistance)))
 (p/'reference_normals.json').write_text(json.dumps(out));(p/'normal_progress.json').write_text(json.dumps(dict(done=True,max_distance=maxdistance)))
except:(p/'refnormal_error.txt').write_text(traceback.format_exc())

