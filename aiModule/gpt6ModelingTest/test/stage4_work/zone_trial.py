import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');o=Part.Shape();o.read(str(p/'complete_outer.brep'));i=Part.Shape();i.read(str(p/'paired_inner.brep'));s=o.Faces[0].Surface;ins=i.Faces[0].Surface;bs=s.getVKnots();ib=ins.getVKnots();result=[]
for lo,hi in [(0,40),(40,55),(55,75),(75,595),(595,bs[-1])]:
 try:
  a=bs.index(float(lo));b=len(bs)-1 if hi==bs[-1] else bs.index(float(hi));fs=[]
  for k in range(a,b):
   so=s.copy();si=ins.copy();so.segment(0.,1.,bs[k],bs[k+1]);si.segment(0.,1.,ib[k],ib[k+1]);fo=so.toShape();fi=si.toShape();fs.extend([fo,fi])
   for ix in [0,2]+([1] if k==a else [])+([3] if k==b-1 else []):fs.append(Part.makeRuledSurface(fo.Edges[ix],fi.Edges[ix],1))
  shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
  if solid.Volume<0:solid.reverse()
  solid.exportBrep(str(p/('zone_'+str(lo)+'.brep')));r=dict(lo=lo,hi=hi,valid=solid.isValid(),volume=solid.Volume)
  try:solid.check(True);r['bop']='passed'
  except Exception as e:r['bop']=str(e)
 except Exception as e:r=dict(lo=lo,error=str(e))
 result.append(r);(p/'zone_checks.json').write_text(json.dumps(result,indent=2))
