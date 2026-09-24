import json,numpy as np
from scipy.interpolate import BSpline,splev
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');q=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3');rr=json.loads((q/'smooth_fitted.json').read_text());rr=[r for r in rr if r['height']<55];base=json.loads((q/'compatible_profiles.json').read_text());knots=base[0]['knots'];mults=base[0]['mults'];t=np.repeat(knots,mults);u=np.linspace(0,1,3001);B=BSpline.design_matrix(u,t,3).toarray();out=[]
for r in rr:
 oldt=np.repeat(r['knots'],r['mults']);v=np.array(splev(u,(oldt,np.array(r['poles']).T,3))).T;c=np.zeros((B.shape[1],2));c[0]=v[0];c[-1]=v[-1];c[1:-1]=np.linalg.lstsq(B[:,1:-1],v-B[:,0,None]*c[0]-B[:,-1,None]*c[-1],rcond=None)[0]
 rec={k:v for k,v in r.items() if k not in ['points','fit_points']};rec.update(poles=c.tolist(),knots=knots,mults=mults);out.append(rec)
bottom=dict(out[0]);bottom['height']=0.;out.insert(0,bottom)
(p/'full_profiles.json').write_text(json.dumps(out+base))
