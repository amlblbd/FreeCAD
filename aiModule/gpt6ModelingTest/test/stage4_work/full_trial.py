import FreeCAD as A,Part,json,sys,traceback,time
from pathlib import Path
sys.path.insert(0,'D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test');import BPillarSurface
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.newDocument();objs=[]
 for r in json.loads((p/'full_profiles.json').read_text()):
  c=Part.BSplineCurve();c.buildFromPolesMultsKnots([A.Vector(*pt) if len(pt)==3 else A.Vector(*pt,r['height']) for pt in r['poles']],r['mults'],r['knots'],False,3);o=d.addObject('Part::Feature','S');o.Shape=c.toShape();objs.append(o)
 outer=BPillarSurface.surface(objs);outer.exportBrep(str(p/'complete_outer.brep'));s=outer.Surface if hasattr(outer,'Surface') else outer.Faces[0].Surface
 t=time.time();ku=s.getUKnots();kv=s.getVKnots();mu=s.getUMultiplicities();mv=s.getVMultiplicities();uu=[a for a,b in zip(ku,mu) for j in range(b)];vv=[a for a,b in zip(kv,mv) for j in range(b)];ug=[sum(uu[i+1:i+4])/3 for i in range(s.NbUPoles)];vg=[sum(vv[i+1:i+4])/3 for i in range(s.NbVPoles)]
 poles=s.getPoles();shift=[]
 for i,row in enumerate(poles):shift.append([q+s.normal(ug[i],vg[j])*2.5 for j,q in enumerate(row)])
 ins=Part.BSplineSurface();ins.buildFromPolesMultsKnots(shift,mu,mv,ku,kv,False,False,3,3);inner=ins.toShape();inner.exportBrep(str(p/'inner_test.brep'))
 walls=[Part.makeRuledSurface(a,b,1) for a,b in zip(outer.Edges,inner.Edges)];shell=Part.makeCompound([outer,inner]+walls);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'solid_test.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),solids=len(solid.Solids),faces=len(solid.Faces),volume=solid.Volume,seconds=time.time()-t)
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'solid_test.json').write_text(json.dumps(r,indent=2));vs,ts=solid.tessellate(.8);(p/'solid_test_mesh.json').write_text(json.dumps(dict(v=[[v.x,v.y,v.z] for v in vs],t=ts)))
 A.closeDocument(d.Name)
except:(p/'full_error.txt').write_text(traceback.format_exc())


