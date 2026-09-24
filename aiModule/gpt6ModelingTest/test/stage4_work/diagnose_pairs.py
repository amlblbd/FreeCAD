import FreeCAD as A,Part,json,sys,traceback,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
try:
 d=A.newDocument();objs=[];out=[]
 for r in json.loads((p/'inner_profiles_projected.json').read_text()):
  c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*q) if len(q)==3 else A.Vector(*q,r['height']) for q in r['poles']],r['mults'],r['knots'],False,3);o=d.addObject('Part::Feature','S');o.Shape=c.toShape();objs.append(o)
  try:o.Shape.check(True);e='passed'
  except Exception as x:e=str(x)
  out.append(dict(height=r['height'],curve_check=e))
 inner=BPillarSurface.surface(objs);inner.exportBrep(str(p/'projected_inner.brep'));s=Part.Shape();s.read(str(p/'complete_outer.brep'));su=s.Faces[0].Surface;si=inner.Surface;ku=su.getVKnots();ki=si.getVKnots();rr=[]
 for k,(a,b) in enumerate(zip(ku,ku[1:])):
  u=su.copy();v=si.copy();u.segment(0.,1.,a,b);v.segment(0.,1.,ki[k],ki[k+1]);fo=u.toShape();fi=v.toShape();walls=[Part.makeRuledSurface(x,y,1) for x,y in zip(fo.Edges,fi.Edges)];sh=Part.makeCompound([fo,fi]+walls);sh.sewShape();solid=Part.makeSolid(sh.Shells[0]);rec=dict(span=[a,b],valid=solid.isValid())
  try:solid.check(True);rec['bop']='passed'
  except Exception as x:rec['bop']=str(x)
  rr.append(rec);(p/'profile_band_diagnosis.json').write_text(json.dumps(dict(profiles=out,bands=rr),indent=2))
 A.closeDocument(d.Name)
except:(p/'diagnosis_error.txt').write_text(traceback.format_exc())
