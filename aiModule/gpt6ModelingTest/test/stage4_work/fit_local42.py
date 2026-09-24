import json,numpy as np
from pathlib import Path
from scipy.interpolate import BSpline
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
raw=json.loads((p/'local42_raw.json').read_text());outer=json.loads((p/'full_profiles.json').read_text());inner=json.loads((p/'inner_profiles.json').read_text());r=outer[0];u=np.linspace(0,1,3001);B=BSpline.design_matrix(u,np.repeat(r['knots'],r['mults']),3).toarray();audit=[]
for name,rows in [('outer',outer),('inner',inner)]:
 (p/(name+'_profiles_before_local42.json')).write_text(json.dumps(rows))
 for row in raw:
  es=[np.array(e) for e in row[name]];chains=[];gaps=[]
  while es:
   v=es.pop(0)
   while es:
    dist,i,j=min((np.linalg.norm(a-b),i,j) for i,e in enumerate(es) for j,(a,b) in enumerate([(v[-1],e[0]),(v[-1],e[-1]),(v[0],e[-1]),(v[0],e[0])]))
    if dist>25:break
    gaps.append(float(dist));q=es.pop(i)
    v=np.vstack([v,q] if j==0 else [v,q[::-1]] if j==1 else [q,v] if j==2 else [q[::-1],v])
   chains.append(v)
  if not chains:continue
  v=max(chains,key=lambda a:np.linalg.norm(np.diff(a,axis=0),axis=1).sum())
  if v[0,0]>v[-1,0]:v=v[::-1]
  ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];v=v[np.r_[True,np.diff(ar)>1e-9]];ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))]
  data=np.column_stack([np.interp(u,ar/ar[-1],v[:,j]) for j in range(2)]);cp=np.zeros((B.shape[1],2));cp[0]=data[0];cp[-1]=data[-1];cp[1:-1]=np.linalg.lstsq(B[:,1:-1],data-B[:,0,None]*cp[0]-B[:,-1,None]*cp[-1],rcond=None)[0]
  rec=dict(r);rec.update(height=row['height'],poles=cp.tolist());rows.append(rec);audit.append(dict(surface=name,height=row['height'],gap=max(gaps,default=0),ends=[v[0].tolist(),v[-1].tolist()],fitmax=float(np.linalg.norm(B@cp-data,axis=1).max())))
 rows.sort(key=lambda r:1000 if r['height']=='Top' else r['height'])
 (p/('full_profiles.json' if name=='outer' else 'inner_profiles.json')).write_text(json.dumps(rows))
(p/'local42_fit_audit.json').write_text(json.dumps(audit,indent=2))
