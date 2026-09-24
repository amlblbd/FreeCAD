import FreeCAD as A,Part,json,traceback,math
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument(str(p.parent/'B_pillar_stage3.FCStd'));ref=d.getObject('ReferenceSTEP').Shape;outer=Part.Shape();outer.read(str(p/'inputs/stage3/smooth_outer.brep'));selected=[];audit=[]
 for k,f in enumerate(ref.Faces):
  if type(f.Surface).__name__=='OffsetSurface' and abs(abs(f.Surface.OffsetValue)-2.5)<1e-6:selected.append(f);audit.append(k+1);continue
  if f.Area<5:continue
  q=Part.Vertex(f.CenterOfMass).distToShape(f)[1][0][1];r=Part.Vertex(q).distToShape(outer)
  if abs(r[0]-2.5)>.02 or r[2][0][3]!='Face':continue
  target=r[1][0][1];of=outer.Faces[r[2][0][4]];u,v=f.Surface.parameter(q);a,b=of.Surface.parameter(target)
  if f.normalAt(u,v).dot(of.normalAt(a,b))<-.98:selected.append(f);audit.append(k+1)
 skin=Part.makeCompound(selected);skin.exportBrep(str(p/'reference_inner_skin.brep'));(p/'inner_face_ids.json').write_text(json.dumps(audit))
 rows=json.loads((p/'full_profiles.json').read_text());result=[]
 for r in rows:
  h=r['height']
  if not isinstance(h,(int,float)) or h==0:continue
  shape=skin.section(Part.makePlane(1400,600,A.Vector(-700,-300,h)));parts=[]
  for e in shape.Edges:
   vs=e.discretize(Number=max(3,int(e.Length/.35)+1));parts.append([[v.x,v.y] for v in vs])
  result.append(dict(height=h,edges=parts));(p/'inner_raw_sections.json').write_text(json.dumps(result));(p/'inner_extract_progress.json').write_text(json.dumps(dict(height=h,edges=len(parts))))
 # Closest points on the reference inner skin for the slanted top rim.
 r=next(r for r in rows if r['height']=='Top');c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*v) for v in r['poles']],r['mults'],r['knots'],False,3);top=[]
 for i in range(501):
  u=i/500;q=c.value(u);v=Part.Vertex(q).distToShape(skin)[1][0][1];top.append([u,v.x,v.y,v.z])
 (p/'inner_top_points.json').write_text(json.dumps(top));A.closeDocument(d.Name)
except:(p/'inner_extract_error.txt').write_text(traceback.format_exc())
