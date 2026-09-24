from pathlib import Path
import json,numpy as np
from scipy.interpolate import BSpline,splev
from scipy.spatial import cKDTree
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');outer=json.loads((p/'full_profiles.json').read_text());raw={r['height']:r['edges'] for r in json.loads((p/'inner_raw_sections.json').read_text())};knots=outer[0]['knots'];mults=outer[0]['mults'];t=np.repeat(knots,mults);fitU=np.linspace(0,1,3001);B=BSpline.design_matrix(fitU,t,3).toarray();out=[];audit=[]
for r in outer:
 h=r['height']
 if h=='Top':
  vv=np.array(json.loads((p/'inner_top_points.json').read_text()));data=np.column_stack([np.interp(fitU,vv[:,0],vv[:,j]) for j in [1,2,3]])
 else:
  v=np.concatenate([np.array(a) for a in raw[2 if h==0 else h]])
  cu=np.linspace(0,1,10001);xy=np.array(splev(cu,(t,np.array(r['poles']).T,3))).T;tree=cKDTree(xy);dd,ii=tree.query(v);uv=[]
  for pt,index in zip(v,ii):
   opts=[]
   for j in [max(0,index-1),min(len(cu)-2,index)]:
    a=xy[j];b=xy[j+1];d=b-a;w=np.clip(np.dot(pt-a,d)/np.dot(d,d),0,1);q=a+d*w;opts.append((np.linalg.norm(pt-q),cu[j]+(cu[j+1]-cu[j])*w))
   dist,u=min(opts)
   if dist<8:uv.append([u,pt[0],pt[1],dist])
  uv=np.array(sorted(uv,key=lambda x:x[0]));end0=v[np.argmin(np.linalg.norm(v-xy[0],axis=1))];end1=v[np.argmin(np.linalg.norm(v-xy[-1],axis=1))]
  # Remove duplicate parameter values, selecting the closest inner skin branch.
  bins={}
  for q in uv:
   k=round(q[0],6)
   if k not in bins or q[3]<bins[k][3]:bins[k]=q
  uv=np.array([bins[k] for k in sorted(bins) if 0<k<1]);uv=np.vstack([[0,*end0,0],uv,[1,*end1,0]])
  data=np.column_stack([np.interp(fitU,uv[:,0],uv[:,j]) for j in [1,2]])
 c=np.zeros((B.shape[1],data.shape[1]));c[0]=data[0];c[-1]=data[-1];c[1:-1]=np.linalg.lstsq(B[:,1:-1],data-B[:,0,None]*c[0]-B[:,-1,None]*c[-1],rcond=None)[0]
 rec={k:v for k,v in r.items() if k not in ['points','fit_points']};rec['poles']=c.tolist();out.append(rec);audit.append(dict(height=h,max_fit_error=float(np.linalg.norm(B@c-data,axis=1).max())))
(p/'inner_profiles.json').write_text(json.dumps(out));(p/'inner_fit_audit.json').write_text(json.dumps(audit,indent=2));print('profiles',len(out),'largest fit residual',max(x['max_fit_error'] for x in audit))
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,4,figsize=(15,7))
for axes,h in zip(ax.flat,[2,15,40,47,55,75,310,595]):
 for rows,col in [(outer,'#387faa'),(out,'#cb7631')]:
  r=next(r for r in rows if r['height']==h);xy=np.array(splev(fitU,(t,np.array(r['poles']).T,3))).T;axes.plot(xy[:,0],xy[:,1],color=col,linewidth=1)
 axes.set_title(str(h));axes.set_aspect('equal')
fig.tight_layout();fig.savefig(p/'paired_profiles.png',dpi=130)
