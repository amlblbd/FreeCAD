import json,numpy as np
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');r=next(r for r in json.loads((p/'inputs/stage3/smooth_sections.json').read_text()) if r['height']==47);edges=[np.array(c['points']) for c in r['chains']];v=edges.pop(0);gaps=[]
while edges:
 opts=[(np.linalg.norm(a-b),i,j) for i,e in enumerate(edges) for j,(a,b) in enumerate([(v[-1],e[0]),(v[-1],e[-1]),(v[0],e[-1]),(v[0],e[0])])];dist,i,j=min(opts);q=edges.pop(i);gaps.append([float(dist),j])
 if j==0:v=np.vstack([v,q])
 elif j==1:v=np.vstack([v,q[::-1]])
 elif j==2:v=np.vstack([q,v])
 else:v=np.vstack([q[::-1],v])
print('gaps',gaps);print('ends',v[0],v[-1])
if v[0,0]>v[-1,0]:v=v[::-1]
(p/'outer47_joined.json').write_text(json.dumps(v.tolist()))
