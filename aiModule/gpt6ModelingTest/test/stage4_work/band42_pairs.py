import FreeCAD as A,Part,json,time,itertools
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');faces=[]
for f in ['complete_outer.brep','paired_inner.brep']:
 sh=Part.Shape();sh.read(str(p/f));s=sh.Faces[0].Surface;s.segment(0.,1.,42.,44.);faces.append(s.toShape())
names=['outer','inner','left','bottom','right','top'];fo,fi=faces;faces += [Part.makeRuledSurface(fo.Edges[i],fi.Edges[i],1) for i in range(4)];out=[]
for a,b in itertools.combinations(range(6),2):
 sh=Part.makeCompound([faces[a],faces[b]]);sh.sewShape();r=dict(pair=[names[a],names[b]])
 try:sh.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 out.append(r);(p/'band42_pairs.json').write_text(json.dumps(out,indent=2))
