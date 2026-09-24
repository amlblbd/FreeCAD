import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/B_pillar_stage3.FCStd');ref=d.getObject('ReferenceSTEP').Shape;out=[]
 for k in [134,138,159,249]:
  f=ref.Faces[k-1];a,b,c,e=f.ParameterRange;n=f.normalAt((a+b)/2,(c+e)/2);f.exportBrep(str(p/('tab_face_%d.brep'%k)));so=f.extrude(n*-2.5);so.exportBrep(str(p/('tab_solid_%d.brep'%k)));row=dict(face=k,wires=len(f.Wires),normal=[n.x,n.y,n.z],area=f.Area,volume=so.Volume,valid=so.isValid());
  try:so.check(True);row['bop']='passed'
  except Exception as ex:row['bop']=str(ex)
  out.append(row)
 (p/'tabs.json').write_text(json.dumps(out,indent=2));A.closeDocument(d.Name)
except:(p/'tabs_error.txt').write_text(traceback.format_exc())
