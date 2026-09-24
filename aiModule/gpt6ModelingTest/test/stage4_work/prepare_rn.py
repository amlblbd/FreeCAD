from pathlib import Path
f=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/normalfit_trial.py');s=f.read_text(encoding='utf-8-sig');a=s.index(' # Additional longitudinal');b=s.index(' ins=Part.BSplineSurface()',a)
s=s[:a]+''' ku=s.getUKnots();kv=s.getVKnots();mu=s.getUMultiplicities();mv=s.getVMultiplicities()
 ns=json.loads((p/'reference_normals.json').read_text());pts=s.getPoles();shift=[[q+A.Vector(*ns[i][j])*2.5 for j,q in enumerate(row)] for i,row in enumerate(pts)]
'''+s[b:];s=s.replace('normalfit_test.json','refnormal_test.json').replace('normalfit_error.txt','refnormal_solid_error.txt');Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/refnormal_solid.py').write_text(s,encoding='utf-8')
