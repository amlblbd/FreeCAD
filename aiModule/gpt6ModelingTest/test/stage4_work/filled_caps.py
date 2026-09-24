import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 surfaces=[]
 for name in ['complete_outer.brep','paired_inner.brep']:
  sh=Part.Shape();sh.read(str(p/name));surfaces.append(sh.Faces[0].Surface)
 bs=[s.getVKnots() for s in surfaces];fs=[];bound={0:[],2:[]};corners={};a=bs[0].index(40.);b=bs[0].index(55.)
 for k in range(len(bs[0])-1):
  ff=[]
  for j,s in enumerate(surfaces):
   c=s.copy();c.segment(0.,1.,bs[j][k],bs[j][k+1]);ff.append(c.toShape())
  fo,fi=ff;fs.extend(ff)
  for ei in [0,2]:
   cap=Part.makeRuledSurface(fo.Edges[ei],fi.Edges[ei],1)
   if a<=k<b:
    bound[ei].extend([fo.Edges[ei],fi.Edges[ei]])
    if k==a or k==b-1:
     for edge in cap.Edges:
      vs=edge.Vertexes
      if len(vs)==2 and abs(vs[0].Point.z-vs[1].Point.z)<1e-5 and abs(vs[0].Point.z-(40 if k==a else 55))<1e-4:bound[ei].append(edge)
   else:fs.append(cap)
  if k==0:fs.append(Part.makeRuledSurface(fo.Edges[1],fi.Edges[1],1))
  if k==len(bs[0])-2:fs.append(Part.makeRuledSurface(fo.Edges[3],fi.Edges[3],1))
 for ei,edges in bound.items():
  face=Part.makeFilledFace(edges);face.exportBrep(str(p/('filled_cap_'+str(ei)+'.brep')));fs.extend(face.Faces)
 shell=Part.makeCompound(fs);shell.sewShape();r=dict(shells=len(shell.Shells));solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'filled_caps_solid.brep'));r.update(valid=solid.isValid(),closed=solid.isClosed(),solids=len(solid.Solids),volume=solid.Volume)
 (p/'filled_caps_result.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'filled_caps_result.json').write_text(json.dumps(r,indent=2))
except:(p/'filled_caps_error.txt').write_text(traceback.format_exc())
