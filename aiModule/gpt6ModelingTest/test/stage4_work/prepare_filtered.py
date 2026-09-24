from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');s=(p/'fit_inner_chain.py').read_text(encoding='utf-8-sig');s=s.replace('from scipy.interpolate import splprep,splev,BSpline','from scipy.interpolate import splprep,splev,BSpline\nfrom scipy.spatial import cKDTree')
s=s.replace("es=[np.array(e) for e in raw[2 if h==0 else h]];chains=[]", "outerxy=np.array(splev(np.linspace(0,1,10001),(t,np.array(r['poles']).T,3))).T;tree=cKDTree(outerxy);es=[]\n for edge in raw[2 if h==0 else h]:\n  edge=np.array(edge);dist,_=tree.query(edge);ok=dist<7.\n  if np.mean(ok)<.5:continue\n  edge=edge[ok]\n  if len(edge)>1:es.append(edge)\n chains=[]")
s=s.replace("if v[0,0]>v[-1,0]:v=v[::-1]", "if v[0,0]>v[-1,0]:v=v[::-1]\n j0=int(np.argmin(np.linalg.norm(v-outerxy[0],axis=1)));j1=int(np.argmin(np.linalg.norm(v-outerxy[-1],axis=1)));v=v[min(j0,j1):max(j0,j1)+1]\n if j0>j1:v=v[::-1]")
s=s.replace("(p/'inner_profiles_projected.json').write_text((p/'inner_profiles.json').read_text());",'')
(p/'fit_inner_chain_filtered.py').write_text(s,encoding='utf-8')
