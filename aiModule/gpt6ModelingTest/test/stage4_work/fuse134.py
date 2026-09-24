import FreeCAD as A,Part,json,traceback,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');s=Part.Shape();s.read(str(p/'body_valid_24.brep'));t=Part.Shape();t.read(str(p/'tab_solid_134.brep'));out=[]
for tol in [.01,.1]:
 start=time.time()
 try:
  sh=s.fuse(t,tol);r=dict(tolerance=tol,valid=sh.isValid(),solids=len(sh.Solids),volume=sh.Volume,seconds=time.time()-start);sh.exportBrep(str(p/('fuse134_tol'+str(tol)+'.brep')))
  if r['valid'] and r['solids']==1:
   try:sh.check(True);r['bop']='passed'
   except Exception as e:r['bop']=str(e)
 except Exception as e:r=dict(tolerance=tol,error=str(e),seconds=time.time()-start)
 out.append(r);(p/'fuse134_checks.json').write_text(json.dumps(out,indent=2))
