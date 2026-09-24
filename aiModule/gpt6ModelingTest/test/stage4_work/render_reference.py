import json,numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');m=json.loads((p/'reference_mesh.json').read_text());vv=np.array(m['v']);tri=vv[np.array(m['t'])];nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12);color=np.array([.67,.76,.83])[None,:]*(.5+.5*np.abs(nn@np.array([.3,.7,.6])))[:,None]
fig=plt.figure(figsize=(15,8))
for i,(az,el) in enumerate([(75,15),(-80,15),(-70,45)]):
 ax=fig.add_subplot(1,3,i+1,projection='3d');mask=np.ones(len(tri),bool) if i<2 else tri[:,:,2].min(axis=1)<100;ax.add_collection3d(Poly3DCollection(tri[mask],facecolors=color[mask],edgecolors='none',antialiased=False));ax.set_xlim(-230,230);ax.set_ylim(-45,45);ax.set_zlim(0,625 if i<2 else 120);ax.set_box_aspect((460,90,625 if i<2 else 120));ax.view_init(el,az);ax.set_yticks([-30,0,30]);ax.set_title(['Reference front','Reference rear','Lower detail'][i])
fig.tight_layout();fig.savefig(p/'reference_views.png',dpi=140)
