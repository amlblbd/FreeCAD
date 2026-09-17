"""Parameter-driven C1 section surface; pure FreeCAD/Python, no scipy at runtime."""
import FreeCAD as App
import Part

def slopes(t,y):
    h=[b-a for a,b in zip(t,t[1:])];m=[(b-a)/s for a,b,s in zip(y,y[1:],h)]
    if len(y)==2:return [m[0],m[0]]
    d=[0.0]*len(y)
    for i in range(1,len(y)-1):
        if m[i-1]*m[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            d[i]=(w1+w2)/(w1/m[i-1]+w2/m[i])
    for index,a,b in [(0,0,1),(-1,-1,-2)]:
        v=((2*h[a]+h[b])*m[a]-h[a]*m[b])/(h[a]+h[b])
        if v*m[a]<=0:v=0.
        elif m[a]*m[b]<0 and abs(v)>3*abs(m[a]):v=3*m[a]
        d[index]=v
    return d

def surface(sections):
    curves=[o.Shape.Edges[0].Curve for o in sections]
    for c in curves:
        c.scaleKnotsToBounds(0.,1.)
        c.setKnots([round(k,10) for k in c.getKnots()])
    combined={}
    for c in curves:
        for k,m in zip(c.getKnots(),c.getMultiplicities()):combined[k]=max(m,combined.get(k,0))
    knots=sorted(combined);mults=[combined[k] for k in knots]
    for c in curves:c.insertKnots(knots,mults,1e-12,False)
    cp=[c.getPoles() for c in curves]
    t=[sum(v.z for v in row)/len(row) for row in cp]
    if any(b-a<=1e-5 for a,b in zip(t,t[1:])):raise ValueError('Section heights must remain increasing.')
    grid=[]
    for j in range(len(cp[0])):
        values=[[getattr(row[j],axis) for row in cp] for axis in ['x','y','z']]
        dd=[slopes(t,y) for y in values];col=[cp[0][j]]
        for i in range(len(cp)-1):
            step=(t[i+1]-t[i])/3
            da=App.Vector(*[v[i] for v in dd]);db=App.Vector(*[v[i+1] for v in dd])
            col.extend([cp[i][j]+da*step,cp[i+1][j]-db*step,cp[i+1][j]])
        grid.append(col)
    s=Part.BSplineSurface();s.buildFromPolesMultsKnots(grid,mults,[4]+[3]*(len(t)-2)+[4],knots,t,False,False,3,3)
    for i in range(2,len(t)):
        if not s.removeVKnot(i,2,1e-7):raise ValueError("C1 knot reduction failed")
    return s.toShape()

class SectionSurface:
    def __init__(self,obj):
        obj.addProperty('App::PropertyLinkList','Sections','Surface','Ordered editable sections')
        obj.addProperty('App::PropertyString','Method','Surface');obj.Method='Cubic Hermite / PCHIP; C1; physical section height'
        obj.Proxy=self
    def execute(self,obj):obj.Shape=surface(obj.Sections)
    def dumps(self):return None
    def loads(self,state):pass

