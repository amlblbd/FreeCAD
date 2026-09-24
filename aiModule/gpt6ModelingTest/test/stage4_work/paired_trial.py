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
  so=s.copy();si=ins.copy();so.segment(0.,1.,a,b);si.segment(0.,1.,ib[k],ib[k+1]);fo=so.toShape();fi=si.toShape();fs.extend([fo,fi])
  for ix in [0,2]+([1] if k==0 else [])+([3] if k==len(bands)-2 else []):fs.append(Part.makeRuledSurface(fo.Edges[ix],fi.Edges[ix],1))
 shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'paired_solid.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),volume=solid.Volume,solids=len(solid.Solids),faces=len(solid.Faces));(p/'paired_result.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'paired_result.json').write_text(json.dumps(r,indent=2));A.closeDocument(d.Name)
except:(p/'paired_error.txt').write_text(traceback.format_exc())
