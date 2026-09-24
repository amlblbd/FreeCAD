import FreeCAD as A,Part,json,sys,os,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');sys.path.insert(0,str(p.parent));import BPillarSurface
try:
 d=A.openDocument(str(p.parent/'B_pillar_stage3.FCStd'));d.Label='B pillar - Stage 4 WORKING - NOT ACCEPTED'
 for o in d.Objects:
  if o.ViewObject:o.ViewObject.Visibility=False
 group=d.addObject('App::DocumentObjectGroup','Stage4Working');group.Label='阶段4 工作中（尚未通过整体验收）'
 params=d.addObject('App::FeaturePython','Stage4Parameters');params.Label='阶段4参数（当前仅驱动独立耳板）';params.addProperty('App::PropertyFloatConstraint','EarThickness','Wall');params.EarThickness=(2.5,2.,3.,.1);params.addProperty('App::PropertyString','Status','Validation');params.Status='Body has self-intersections. Ear thickness only: tested 2.0, 2.5, 3.0 mm. Parts NOT fused.';params.setEditorMode('Status',1);group.addObject(params)
 shapes=d.addObject('App::DocumentObjectGroup','Stage4Templates');shapes.Label='耳板轮廓模板（来自参考面）';group.addObject(shapes)
 body=d.addObject('Part::Feature','Stage4BodyTrial');body.Label='主体试算：封闭但有自交，非交付实体';s=Part.Shape();s.read(str(p/'paired_solid.brep'));body.Shape=s;body.addProperty('App::PropertyString','Validation','Stage4');body.Validation='Basic closed/valid, enhanced BOP check FAILED. Thickness is not yet parametrically validated.';body.setEditorMode('Validation',1);group.addObject(body)
 labels={134:'右耳端板（保留矩形孔）',138:'左耳端板（保留矩形孔）',159:'右耳侧板',249:'左耳侧板'};walls=[]
 for ix in [134,138,159,249]:
  s=Part.Shape();s.read(str(p/('tab_face_'+str(ix)+'.brep')));base=d.addObject('Part::Feature','EarOutline'+str(ix));base.Label=labels[ix]+'轮廓';base.Shape=s;shapes.addObject(base)
  wall=d.addObject('Part::Extrusion','EarWall'+str(ix));wall.Label=labels[ix];wall.Base=base;wall.Dir=-s.Faces[0].normalAt(0,0);wall.LengthFwd=2.5;wall.Solid=True;wall.setExpression('LengthFwd','Stage4Parameters.EarThickness');group.addObject(wall);walls.append(wall)
 d.recompute();validation=[]
 for t in [2.,2.5,3.,2.5]:
  params.EarThickness=t;d.recompute()
  for wall in walls:
   wall.Shape.check(True);assert wall.Shape.isValid() and len(wall.Shape.Solids)==1
   validation.append(dict(name=wall.Name,thickness=t,volume=wall.Shape.Volume,bop='passed'))
 for o in d.Objects:
  if o.ViewObject:o.ViewObject.Visibility=False
 # Visibility is set by the opening macro

 d.recompute();d.saveAs(str(p.parent/'B_pillar_stage4_working.FCStd'))
 (p/'working_document_validation.json').write_text(json.dumps(validation,indent=2));A.closeDocument(d.Name)
 (p/'working_document_saved.json').write_text(json.dumps(dict(file='B_pillar_stage4_working.FCStd',status='INCOMPLETE; body BOP fails; independent ear features validated')))
except:(p/'working_document_error.txt').write_text(traceback.format_exc())
finally:pass
