import FreeCAD as A,Part,json,traceback,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
def cap(s,i,v,w):
 a=s.vIso(v);b=i.vIso(w);ea=a.toShape();eb=b.toShape();p0=a.value(a.FirstParameter);p1=a.value(a.LastParameter);q0=b.value(b.FirstParameter);q1=b.value(b.LastParameter)
 return Part.Face(Part.Wire([ea,Part.makeLine(p1,q1),eb.reversed(),Part.makeLine(q0,p0)]))
try:
 outer=Part.Shape();outer.read(str(p/'complete_outer.brep'));inner=Part.Shape();inner.read(str(p/'paired_inner.brep'));s=outer.Faces[0].Surface;i=inner.Faces[0].Surface;s.segment(0.,1.,75.,595.);i.segment(0.,1.,75.,595.)
 fs=[s.toShape(),i.toShape(),cap(s,i,75.,75.),cap(s,i,595.,595.)]+[Part.makeRuledSurface(s.uIso(a).toShape(),i.uIso(a).toShape(),1) for a in [0.,1.]]
 shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0]);solid.exportBrep(str(p/'upper_solid_test.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),faces=len(solid.Faces),volume=abs(solid.Volume));(p/'upper_solid_test.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'upper_solid_test.json').write_text(json.dumps(r,indent=2))
except:(p/'upper_solid_error.txt').write_text(traceback.format_exc())
