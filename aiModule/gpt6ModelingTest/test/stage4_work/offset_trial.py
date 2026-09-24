import FreeCAD as A,Part,json,time,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');out=[]
for name in ['LowerCrownLoft','UpperMasterLoft']:
 t=time.time()
 try:
  s=Part.Shape();s.read(str(p/(name+'.brep')));r=s.makeOffsetShape(2.5,.01,fill=True);r.exportBrep(str(p/(name+'_offset.brep')))
  rec=dict(name=name,seconds=time.time()-t,valid=r.isValid(),solids=len(r.Solids),faces=len(r.Faces),volume=r.Volume)
  try:r.check(True);rec['bop']='passed'
  except Exception as e:rec['bop']=str(e)
  out.append(rec)
 except Exception as e:out.append(dict(name=name,error=str(e),seconds=time.time()-t))
 (p/'offset_trial.json').write_text(json.dumps(out,indent=2))
