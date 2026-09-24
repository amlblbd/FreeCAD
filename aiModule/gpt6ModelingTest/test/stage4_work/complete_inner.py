import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument(str(p.parent/'B_pillar_stage3.FCStd'));ref=d.getObject('ReferenceSTEP').Shape;outer=Part.Shape();outer.read(str(p/'inputs/stage3/smooth_outer.brep'));ids=json.loads((p/'inner_face_ids.json').read_text());added=[]
 for ix,f in enumerate(ref.Faces):
  if ix+1 in ids or type(f.Surface).__name__!='Plane' or f.Area<2:continue
  n=f.normalAt(0,0)
  for of in outer.Faces:
   if type(of.Surface).__name__!='Plane' or n.dot(of.normalAt(0,0))>-.999:continue
   dist=(f.CenterOfMass-of.CenterOfMass).dot(of.normalAt(0,0))
   if abs(dist+2.5)<.02 and f.distToShape(of)[0]<2.6:
    ids.append(ix+1);added.append(dict(face=ix+1,area=f.Area,center=list(f.CenterOfMass),distance=dist));break
 skin=Part.makeCompound([ref.Faces[i-1] for i in ids]);skin.exportBrep(str(p/'reference_inner_complete.brep'));(p/'inner_planes_added.json').write_text(json.dumps(added,indent=2));rows=json.loads((p/'full_profiles.json').read_text());out=[]
 for row in rows:
  h=row['height']
  if h=='Top' or h==0:continue
  sec=skin.section(Part.makePlane(1400,600,A.Vector(-700,-300,h)));out.append(dict(height=h,edges=[[[v.x,v.y] for v in e.discretize(Number=max(3,int(e.Length/.3)+1))] for e in sec.Edges if e.Length>1e-5]));(p/'inner_raw_complete.json').write_text(json.dumps(out))
 A.closeDocument(d.Name)
except:(p/'inner_complete_error.txt').write_text(traceback.format_exc())
