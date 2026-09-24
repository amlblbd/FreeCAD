import json,numpy as np
from pathlib import Path
from scipy.interpolate import splprep,splev,BSpline
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');outer=json.loads((p/'full_profiles.json').read_text());raw={r['height']:r['edges'] for r in json.loads((p/'inner_raw_complete.json').read_text())};knots=outer[0]['knots'];mults=outer[0]['mults'];t=np.repeat(knots,mults);u=np.linspace(0,1,3001);B=BSpline.design_matrix(u,t,3).toarray();rows=[]
for r in outer:
 h=r['height']
 if h=='Top':rows.append(next(x for x in json.loads((p/'inner_profiles.json').read_text()) if x['height']=='Top'));continue
 es=[np.array(e) for e in raw[2 if h==0 else h]];chains=[]
 while es:
  v=es.pop(0)
  while es:
   opts=[(np.linalg.norm(a-b),i,j) for i,e in enumerate(es) for j,(a,b) in enumerate([(v[-1],e[0]),(v[-1],e[-1]),(v[0],e[-1]),(v[0],e[0])])];dist,i,j=min(opts)
   if dist>25:break
   q=es.pop(i)
   if j==0:v=np.vstack([v,q])
   elif j==1:v=np.vstack([v,q[::-1]])
   elif j==2:v=np.vstack([q,v])
   else:v=np.vstack([q[::-1],v])
  chains.append(v)
 v=max(chains,key=lambda a:np.linalg.norm(np.diff(a,axis=0),axis=1).sum())
 if v[0,0]>v[-1,0]:v=v[::-1]
 ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];v=v[np.r_[True,np.diff(ar)>1e-9]];ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];data=np.column_stack([np.interp(u,ar/ar[-1],v[:,j]) for j in range(2)])
 cp=np.zeros((B.shape[1],2));cp[0]=data[0];cp[-1]=data[-1];cp[1:-1]=np.linalg.lstsq(B[:,1:-1],data-B[:,0,None]*cp[0]-B[:,-1,None]*cp[-1],rcond=None)[0]
 rec=dict(r);rec['poles']=cp.tolist();rows.append(rec)
(p/'inner_profiles_projected.json').write_text((p/'inner_profiles.json').read_text());(p/'inner_profiles.json').write_text(json.dumps(rows))
