import FreeCAD as A,Part,json,traceback,time
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');out=[]
def audit(name,shape):
 r=dict(step=name,valid=shape.isValid(),closed=shape.isClosed(),solids=len(shape.Solids),volume=shape.Volume,faces=len(shape.Faces));out.append(r);(p/'fusion24_result.json').write_text(json.dumps(out,indent=2));return r
try:
 assert json.loads((p/'paired_result.json').read_text())['bop']=='passed'
 s=Part.Shape();s.read(str(p/'paired_solid.brep'));s.exportBrep(str(p/'body_valid_24.brep'));tools=[]
 for ix in [134,138,159,249]:
  t=Part.Shape();t.read(str(p/('tab_solid_'+str(ix)+'.brep')));tools.append(t)
 fused=s.multiFuse(tools);fused.exportBrep(str(p/'fused24.brep'));r=audit('fusion',fused)
 try:fused.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 (p/'fusion24_result.json').write_text(json.dumps(out,indent=2))
 cutters=[]
 for ix in [134,138]:
  s=Part.Shape();s.read(str(p/('tab_face_'+str(ix)+'.brep')));f=s.Faces[0]
  for w in f.Wires:
   if w.isSame(f.OuterWire):continue
   face=Part.Face(w);face.translate(A.Vector(0,0,1));cutter=face.extrude(A.Vector(0,0,-6));cutters.append(cutter)
 # Lower open slots; final dimensions will be compared with reference.
 cutters.extend([Part.makeBox(12.03,200,15.02,A.Vector(206.29,-100,-1)),Part.makeBox(11.90,200,15.06,A.Vector(-218.05,-100,-1))])
 final=fused.cut(Part.makeCompound(cutters));final.exportBrep(str(p/'opened24.brep'));r=audit('openings',final)
 try:final.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 r['cutters_residual_volume']=[final.common(c).Volume for c in cutters];(p/'fusion24_result.json').write_text(json.dumps(out,indent=2))
except:(p/'fusion24_error.txt').write_text(traceback.format_exc())
