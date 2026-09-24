import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');s=Part.Shape();s.read(str(p/'body_valid_24.brep'));t=Part.Shape();t.read(str(p/'tab_solid_134.brep'));o=Part.Shape();o.read(str(p/'complete_outer.brep'));face=o.Faces[0];q=face.valueAt(.5,300);n=face.normalAt(.5,300);tests=[q+n,q-n,A.Vector(0,0,300),A.Vector(10000,10000,10000)];r={'original':dict(volume=s.Volume,orientation=s.Orientation,shell_orientation=s.Shells[0].Orientation,inside=[s.isInside(x,1e-6,True) for x in tests],points=[list(x) for x in tests])}
for mode in ['remake','fix']:
 sh=Part.makeSolid(s.Shells[0]) if mode=='remake' else s.copy()
 if mode=='fix':sh.fix(.00001,.00001,.001)
 r[mode]=dict(volume=sh.Volume,orientation=sh.Orientation,inside=[sh.isInside(x,1e-6,True) for x in tests],valid=sh.isValid())
 try:
  fused=sh.fuse(t,.001);r[mode]['fuse']=dict(volume=fused.Volume,valid=fused.isValid(),solids=len(fused.Solids));fused.exportBrep(str(p/('oriented_'+mode+'_fuse.brep')))
 except Exception as e:r[mode]['error']=str(e)
 sh.exportBrep(str(p/('oriented_'+mode+'.brep')));(p/'orientation_audit.json').write_text(json.dumps(r,indent=2))
