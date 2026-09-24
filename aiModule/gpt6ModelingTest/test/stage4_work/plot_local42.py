import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import BSpline
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');o=json.loads((p/'full_profiles.json').read_text());i=json.loads((p/'inner_profiles.json').read_text());fig,axs=plt.subplots(3,3,figsize=(15,10))
for ax,h in zip(axs.flat,[42,42.2,42.35,42.39,42.6,43,43.5,44,44.8]):
 for rows,color in [(o,'blue'),(i,'orange')]:
  r=next(r for r in rows if r['height']==h);v=BSpline(np.repeat(r['knots'],r['mults']),r['poles'],3)(np.linspace(0,1,2001));ax.plot(v[:,0],v[:,1],color=color,lw=1)
 ax.set_xlim(-230,-180);ax.set_ylim(-40,40);ax.set_aspect('equal');ax.set_title(str(h));ax.grid()
fig.tight_layout();fig.savefig(p/'local42_left_profiles.png',dpi=120)
