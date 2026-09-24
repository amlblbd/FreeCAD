import FreeCAD as A,Part,json,traceback
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
try:
 d=A.openDocument(str(p.parent/'B_pillar_stage3.FCStd'));ref=d.ReferenceSTEP.Shape;outer=Part.Shape();outer.read(str(p/'inputs/stage3/smooth_outer.brep'));inner=Part.Shape();inner.read(str(p/'reference_inner_complete.brep'));rs=json.loads((p/'all_band_clearances.json').read_text());out=[]
 for row in sorted(rs,key=lambda r:r['distance'])[:7]:
  q=A.Vector(*row['points'][0][0]);r=Part.Vertex(q).distToShape(outer);qref=r[1][0][1];support=r[2][0];rec=dict(height=row['height'],fit_distance=r[0],reference_point=list(qref),support=support,reference_inner_distance=Part.Vertex(qref).distToShape(inner)[0]);
  if support[3]=='Face':
   f=outer.Faces[support[4]];u,v=f.Surface.parameter(qref);n=f.normalAt(u,v);line=Part.makeLine(qref-n*.01,qref-n*12);hits=ref.section(line).Vertexes;rec['reference_normal_hits']=sorted((v.Point-qref).Length for v in hits if (v.Point-qref).Length>.02)
  out.append(rec);(p/'thin_regions_reference.json').write_text(json.dumps(out,indent=2))
 A.closeDocument(d.Name)
except:(p/'thin_regions_error.txt').write_text(traceback.format_exc())
