from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
s=(p/'save_working.FCMacro').read_text(encoding='utf-8-sig').replace('import FreeCAD as A,FreeCADGui as G,Part,json,sys,os,traceback','import FreeCAD as A,Part,json,sys,os,traceback')
s=s.replace("wall.ViewObject.ShapeColor=(.2,.8,.45);",'').replace("body.ViewObject.ShapeColor=(.72,.75,.80);body.ViewObject.Transparency=30;",'')
s=s.replace(' body.ViewObject.Visibility=True',' # Visibility is set by the opening macro').replace(' for wall in walls:wall.ViewObject.Visibility=True','')
s=s.replace(' G.activeDocument().activeView().viewAxonometric();G.activeDocument().activeView().fitAll();d.recompute();',' d.recompute();')
s=s.replace("G.activeDocument().activeView().saveImage(str(p.parent/'阶段4_工作预览.png'),1200,1000,'White');",'')
s=s.replace('finally:os._exit(0)','finally:pass')
(p/'save_working_cli.py').write_text(s,encoding='utf-8')
