from pathlib import Path
import json,numpy as np
from scipy.interpolate import BSpline
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');rows=json.loads((p/'full_profiles.json').read_text());r=next(r for r in rows if r['height']==47);v=np.array(json.loads((p/'outer47_joined.json').read_text()));ar=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];u=np.linspace(0,1,3001);data=np.column_stack([np.interp(u,ar/ar[-1],v[:,j]) for j in [0,1]]);B=BSpline.design_matrix(u,np.repeat(r['knots'],r['mults']),3).toarray();c=np.zeros((B.shape[1],2));c[0]=data[0];c[-1]=data[-1];c[1:-1]=np.linalg.lstsq(B[:,1:-1],data-B[:,0,None]*c[0]-B[:,-1,None]*c[-1],rcond=None)[0];r['poles']=c.tolist()
(p/'full_profiles_before47.json').write_text((p/'full_profiles.json').read_text());(p/'full_profiles.json').write_text(json.dumps(rows))
