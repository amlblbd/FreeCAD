import FreeCAD as A,Part,json,sys,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
try:
 d=A.newDocument();objs=[]
 for r in json.loads((p/'inner_profiles.json').read_text()):
  c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*q) if len(q)==3 else A.Vector(*q,r['height']) for q in r['poles']],r['mults'],r['knots'],False,3);o=d.addObject('Part::Feature','S');o.Shape=c.toShape();objs.append(o)
 inner=BPillarSurface.surface(objs);inner.exportBrep(str(p/'paired_inner.brep'));outer=Part.Shape();outer.read(str(p/'complete_outer.brep'));s=outer.Faces[0].Surface;ins=inner.Surface;fs=[];bands=s.getVKnots();itop=ins.getVKnots()[-1];otop=bands[-1]
 # Parametric upper rim average heights differ: use matching section indices for trimming.
 ib=ins.getVKnots()
 assert len(ib)==len(bands)
 for k,(a,b) in enumerate(zip(bands,bands[1:])):
  fo=Part.makeRuledSurface(s.vIso(a).toShape(),s.vIso(b).toShape(),1);fi=Part.makeRuledSurface(ins.vIso(ib[k]).toShape(),ins.vIso(ib[k+1]).toShape(),1);fs.extend([fo,fi])
  for side in [0.,1.]:
   e1=Part.makeLine(s.value(side,a),s.value(side,b));e2=Part.makeLine(ins.value(side,ib[k]),ins.value(side,ib[k+1]));fs.append(Part.makeRuledSurface(e1,e2,1))
  if k==0:fs.append(Part.makeRuledSurface(s.vIso(a).toShape(),ins.vIso(ib[k]).toShape(),1))
  if k==len(bands)-2:fs.append(Part.makeRuledSurface(s.vIso(b).toShape(),ins.vIso(ib[k+1]).toShape(),1))
 shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'ruled_solid.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),volume=solid.Volume,solids=len(solid.Solids),faces=len(solid.Faces));(p/'ruled_result.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'ruled_result.json').write_text(json.dumps(r,indent=2));A.closeDocument(d.Name)
except:(p/'ruled_error.txt').write_text(traceback.format_exc())
