import FreeCAD as A,Part,json,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');r=[]
for name in ['LowerCrownLoft','UpperMasterLoft']:
 sh=Part.Shape();sh.read(str(p/(name+'.brep')));s=sh.Faces[0].Surface;bs=s.getVKnots()
 for k in ([0,len(bs)//2,len(bs)-2]):
  a=s.copy();a.segment(0.,1.,bs[k],bs[k+1]);f=a.toShape();v=dict(name=name,band=k,z=[bs[k],bs[k+1]])
  try:
   out=f.makeOffsetShape(2.5,.001,fill=True);v.update(valid=out.isValid(),solids=len(out.Solids),volume=out.Volume);out.check(True);v['bop']='passed';out.exportBrep(str(p/(name+'_band_'+str(k)+'.brep')))
  except Exception as e:v['error']=str(e)
  r.append(v);(p/'band_offsets.json').write_text(json.dumps(r,indent=2))
