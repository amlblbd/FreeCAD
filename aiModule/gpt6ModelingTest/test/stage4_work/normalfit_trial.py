import FreeCAD as A,Part,json,traceback,time
import numpy as np
from pathlib import Path
p=Path('D:/freecad/FreeCAD/aiModule/gpt6ModelingTest/test/stage4_work')
def basis(t,k,u,n):
 import bisect
 span=max(k,min(n-1,bisect.bisect_right(t,u)-1));N=[1.]+[0.]*k;L=[0.]*(k+1);R=[0.]*(k+1)
 for j in range(1,k+1):
  L[j]=u-t[span+1-j];R[j]=t[span+j]-u;saved=0.
  for r in range(j):
   temp=N[r]/(R[r+1]+L[j-r]);N[r]=saved+R[r+1]*temp;saved=L[j-r]*temp
  N[j]=saved
 row=np.zeros(n);row[span-k:span+1]=N;return row
try:
 t=time.time();sh=Part.Shape();sh.read(str(p/'complete_outer.brep'));s=sh.Faces[0].Surface
 # Additional longitudinal supports for the normal field, without changing exterior geometry.
 for a,b in zip(s.getVKnots(),s.getVKnots()[1:]):s.insertVKnot((a+b)/2,1,1e-10,False)
 ku=s.getUKnots();kv=s.getVKnots();mu=s.getUMultiplicities();mv=s.getVMultiplicities();uu=np.repeat(ku,mu);vv=np.repeat(kv,mv);ug=[sum(uu[i+1:i+4])/3 for i in range(s.NbUPoles)];vg=[sum(vv[i+1:i+4])/3 for i in range(s.NbVPoles)]
 data=np.array([[[getattr(s.normal(u,v),a) for a in ['x','y','z']] for v in vg] for u in ug]);Bu=np.array([basis(uu,3,u,len(ug)) for u in ug]);Bv=np.array([basis(vv,3,v,len(vg)) for v in vg]);cp=np.zeros_like(data)
 for axis in range(3):cp[:,:,axis]=np.linalg.solve(Bv,np.linalg.solve(Bu,data[:,:,axis]).T).T
 pts=s.getPoles();shift=[[q+A.Vector(*cp[i,j])*2.5 for j,q in enumerate(row)] for i,row in enumerate(pts)]
 ins=Part.BSplineSurface();ins.buildFromPolesMultsKnots(shift,mu,mv,ku,kv,False,False,3,3);ins.toShape().exportBrep(str(p/'inner_test.brep'))
 fs=[];bands=sh.Faces[0].Surface.getVKnots()
 for k,(a,b) in enumerate(zip(bands,bands[1:])):
  so=s.copy();si=ins.copy();so.segment(0.,1.,a,b);si.segment(0.,1.,a,b);fo=so.toShape();fi=si.toShape();fs.extend([fo,fi])
  for ix in [0,2]+([1] if k==0 else [])+([3] if k==len(bands)-2 else []):fs.append(Part.makeRuledSurface(fo.Edges[ix],fi.Edges[ix],1))
 shell=Part.makeCompound(fs);shell.sewShape();solid=Part.makeSolid(shell.Shells[0])
 if solid.Volume<0:solid.reverse()
 solid.exportBrep(str(p/'solid_test.brep'));r=dict(valid=solid.isValid(),closed=solid.isClosed(),solids=len(solid.Solids),faces=len(solid.Faces),volume=solid.Volume,seconds=time.time()-t);(p/'normalfit_test.json').write_text(json.dumps(r,indent=2))
 try:solid.check(True);r['bop']='passed'
 except Exception as e:r['bop']=str(e)
 r['total_seconds']=time.time()-t;(p/'normalfit_test.json').write_text(json.dumps(r,indent=2));vs,ts=solid.tessellate(.8);(p/'solid_test_mesh.json').write_text(json.dumps(dict(v=[[v.x,v.y,v.z] for v in vs],t=ts)))
except:(p/'normalfit_error.txt').write_text(traceback.format_exc())
