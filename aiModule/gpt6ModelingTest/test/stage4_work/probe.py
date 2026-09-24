import FreeCAD as A,Part,json,traceback,sys,collections
from pathlib import Path
sys.path.insert(0,'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test');import BPillarSurface
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/B_pillar_stage3.FCStd');ref=d.getObject('ReferenceSTEP').Shape;rows=[]
 for i,f in enumerate(ref.Faces):
  s=f.Surface
  if type(s).__name__=='OffsetSurface':
   rows.append(dict(face=i+1,area=f.Area,offset=getattr(s,'Offset',None),attributes=dir(s) if not rows else []))
 (p/'offset_surfaces.json').write_text(json.dumps(rows,default=str,indent=2))
 out={}
 for key in ['LowerCrownLoft','UpperMasterLoft']:
  sh=d.getObject(key).Shape;sh.exportBrep(str(p/(key+'.brep')));f=sh.Faces[0];a,b,c,e=f.ParameterRange;v=f.normalAt((a+b)/2,(c+e)/2);out[key]=dict(normal=[v.x,v.y,v.z],edges=len(sh.Edges),area=sh.Area)
 outer=d.getObject('OuterSkin').Shape;loops=[]
 for i,f in enumerate(outer.Faces):
  if len(f.Wires)>1:loops.append(dict(face=i+1,wires=len(f.Wires),area=f.Area))
 out['outer_internal_loops']=loops
 (p/'probe.json').write_text(json.dumps(out,indent=2))
 vs,ts=ref.tessellate(1.);(p/'reference_mesh.json').write_text(json.dumps(dict(v=[[q.x,q.y,q.z] for q in vs],t=ts)))
 A.closeDocument(d.Name)
except:(p/'probe_error.txt').write_text(traceback.format_exc())
