import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');ss=[]
for f in ['complete_outer.brep','paired_inner.brep']:
 sh=Part.Shape();sh.read(str(p/f));ss.append(sh.Faces[0].Surface)
out=[]
for mode in ['inner_linear','both_linear','outer_linear']:
 fs=[]
 for j,s in enumerate(ss):
  if mode=='both_linear' or (mode=='inner_linear' and j==1) or (mode=='outer_linear' and j==0):
   a=s.vIso(42.);b=s.vIso(44.);su=Part.BSplineSurface();su.buildFromPolesMultsKnots([[v,w] for v,w in zip(a.getPoles(),b.getPoles())],a.getMultiplicities(),[2,2],a.getKnots(),[42.,44.],False,False,3,1)
  else:su=s.copy();su.segment(0.,1.,42.,44.)
  fs.append(su.toShape())
 fo,fi=fs;fs.extend([Part.makeRuledSurface(fo.Edges[k],fi.Edges[k],1) for k in range(4)]);sh=Part.makeCompound(fs);sh.sewShape();solid=Part.makeSolid(sh.Shells[0]);r=dict(mode=mode,valid=solid.isValid())
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 out.append(r);solid.exportBrep(str(p/('band42_'+mode+'.brep')));(p/'band42_linear_checks.json').write_text(json.dumps(out,indent=2))
