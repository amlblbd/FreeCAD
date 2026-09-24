import json,collections,numpy as np
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work');q=p/'thickness_measurement.json'
if q.exists():
 r=json.loads(q.read_text());print('Offsets',collections.Counter(round(x['offset'],4) for x in r['offset_faces']));v=[x['thickness'] for x in r['normal_ray_samples']];print('ray samples',len(v),'min median max',np.min(v),np.median(v),np.max(v))
r=json.loads(Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work/inputs/stage3/smooth_fitted.json').read_text());print([(x['height'],round(x['width'],2),[round(v,1) for v in x['chain_lengths']]) for x in r if x['height']<=55])
