import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');s=Part.Shape();s.read(str(p/'body_valid_24.brep'));t=Part.Shape();t.read(str(p/'tab_solid_134.brep'));r=[]
for mode in ['faces','shell_reverse_faces']:
 fs=s.Faces
 if mode=='shell_reverse_faces':
  shell=s.Shells[0].copy();shell.reverse();fs=shell.Faces
 sh=Part.makeSolid(Part.makeShell(fs));rr=dict(mode=mode,volume=sh.Volume,orientation=sh.Orientation,shell_orientation=sh.Shells[0].Orientation,valid=sh.isValid());rr['far_inside']=sh.isInside(A.Vector(10000,10000,10000),1e-6,True)
 try:
  fused=sh.fuse(t);rr['fuse']=dict(volume=fused.Volume,valid=fused.isValid(),solids=len(fused.Solids));fused.exportBrep(str(p/('normalized_'+mode+'_fuse.brep')))
 except Exception as e:rr['error']=str(e)
 sh.exportBrep(str(p/('normalized_'+mode+'.brep')));r.append(rr);(p/'normalize_solid.json').write_text(json.dumps(r,indent=2))
