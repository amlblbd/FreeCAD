import FreeCAD as A,Part,json
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');out=[]
for name in ['filled_cap_0','filled_cap_2','filled_caps_solid']:
 s=Part.Shape();s.read(str(p/(name+'.brep')));r=dict(name=name,valid=s.isValid(),faces=len(s.Faces),wires=len(s.Wires));s.fix(.00001,.00001,.01);r['fixed_valid']=s.isValid()
 try:s.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 s.exportBrep(str(p/(name+'_fixed.brep')));out.append(r)
(p/'filled_fix.json').write_text(json.dumps(out,indent=2))
