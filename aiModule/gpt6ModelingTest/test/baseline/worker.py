"""Executed only by FreeCADCmd; never saves or changes the original document."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

import FreeCAD as App
import Part

RUN = Path(os.environ['BPILLAR_BASELINE_RUN'])
INPUT = RUN / 'inputs'
TASK = os.environ['BPILLAR_BASELINE_TASK']
sys.path.insert(0, str(INPUT))
import BPillarSurface


def save(data):
    (RUN / (TASK + '.json')).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def read(name):
    shape = Part.Shape()
    shape.read(str(INPUT / 'stage4_work' / name))
    return shape


def basic(shape):
    box = shape.BoundBox
    return dict(null=shape.isNull(), valid=shape.isValid(), closed=shape.isClosed(),
                solids=len(shape.Solids), shells=len(shape.Shells), faces=len(shape.Faces),
                edges=len(shape.Edges), volume_mm3=shape.Volume, area_mm2=shape.Area,
                bounds_mm=[box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax])


def check(shape):
    result = basic(shape)
    try:
        shape.check(True)
        result['bop'] = 'passed' if not result['null'] else 'failed_null_shape'
    except Exception as exc:
        result['bop'] = 'failed'
        result['bop_error'] = str(exc)
    return result


def open_doc():
    return App.openDocument(str(INPUT / 'B_pillar_stage4_working.FCStd'))


def main():
    environment = dict(freecad=App.Version(), occ=getattr(Part, 'OCC_VERSION', 'unknown'),
                       python=sys.version)
    if TASK == 'document':
        doc = open_doc()
        body = doc.Stage4BodyTrial
        exported = RUN / 'saved_body.brep'
        body.Shape.exportBrep(str(exported))
        paired = read('paired_solid.brep')
        comparison = RUN / 'normalized_paired.brep'
        paired.exportBrep(str(comparison))
        result = dict(environment=environment, body=basic(body.Shape), body_type=body.TypeId,
                      body_expressions=body.ExpressionEngine, body_dependencies=[o.Name for o in body.OutList],
                      default_ear_thickness=doc.Stage4Parameters.EarThickness,
                      reference_source=doc.ReferenceSTEP.SourceFile,
                      reference_embedded=not doc.ReferenceSTEP.Shape.isNull(),
                      stage3_proxy=type(doc.UpperMasterLoft.Proxy).__name__,
                      paired=basic(paired),
                      normalized_brep_equal=exported.read_bytes() == comparison.read_bytes(),
                      saved_body_sha256=hashlib.sha256(exported.read_bytes()).hexdigest(),
                      ears=[dict(name=doc.getObject('EarWall'+str(i)).Name,
                                 expressions=doc.getObject('EarWall'+str(i)).ExpressionEngine)
                            for i in (134,138,159,249)])
        save(result)
        App.closeDocument(doc.Name)
    elif TASK == 'body':
        doc = open_doc()
        save(dict(environment=environment, source='saved document, no explicit recompute',
                  geometry=check(doc.Stage4BodyTrial.Shape)))
        App.closeDocument(doc.Name)
    elif TASK == 'paired':
        save(dict(environment=environment, source='stage4_work/paired_solid.brep',
                  geometry=check(read('paired_solid.brep'))))
    elif TASK == 'ears':
        doc = open_doc()
        results = []
        for thickness in (2.0, 2.5, 3.0, 2.5):
            doc.Stage4Parameters.EarThickness = thickness
            doc.recompute()
            for i in (134,138,159,249):
                obj = doc.getObject('EarWall'+str(i))
                results.append(dict(name=obj.Name, requested_mm=thickness,
                                    length_mm=obj.LengthFwd.Value, state=list(obj.State),
                                    geometry=check(obj.Shape)))
                save(dict(environment=environment, checks=results, finished=False))
        save(dict(environment=environment, checks=results, finished=True,
                  all_passed=all(x['length_mm'] == x['requested_mm'] and
                                 x['geometry']['valid'] and x['geometry']['solids'] == 1 and
                                 x['geometry']['bop'] == 'passed' for x in results)))
        App.closeDocument(doc.Name)
    elif TASK == 'distance':
        outer = read('complete_outer.brep').Faces[0]
        inner = read('paired_inner.brep')
        u0,u1,v0,v1 = outer.ParameterRange
        samples = []
        for x in range(25):
            for y in range(31):
                point = outer.valueAt(u0+(u1-u0)*(x+.5)/25, v0+(v1-v0)*(y+.5)/31)
                samples.append([point.x,point.y,point.z,Part.Vertex(point).distToShape(inner)[0]])
        save(dict(environment=environment, method='25 x 31 UV cell centers; outer-to-inner nearest distance, NOT normal wall thickness',
                  samples=len(samples), min_mm=min(x[3] for x in samples), max_mm=max(x[3] for x in samples),
                  rms_from_2_5_mm=math.sqrt(sum((x[3]-2.5)**2 for x in samples)/len(samples)),
                  points_xyz_distance_mm=samples))
    else:
        # Reproduce historical diagnostic construction from the CURRENT surface files.
        # These are capped diagnostic regions, not Boolean cuts of the saved body.
        outer = read('complete_outer.brep').Faces[0].Surface
        inner = read('paired_inner.brep').Faces[0].Surface
        bs, ib = outer.getVKnots(), inner.getVKnots()
        if len(bs) != len(ib):
            raise ValueError('Outer/inner section counts differ')
        if TASK == 'surface_body':
            lo,hi = '0','top'
        else:
            _,lo,hi = TASK.split('_')
        a = bs.index(float(lo))
        b = len(bs)-1 if hi == 'top' else bs.index(float(hi))
        faces = []
        for k in range(a,b):
            so,si = outer.copy(),inner.copy()
            so.segment(0.,1.,bs[k],bs[k+1])
            si.segment(0.,1.,ib[k],ib[k+1])
            fo,fi = so.toShape(),si.toShape()
            faces.extend([fo,fi])
            for ix in [0,2]+([1] if k==a else [])+([3] if k==b-1 else []):
                faces.append(Part.makeRuledSurface(fo.Edges[ix],fi.Edges[ix],1))
        sewn = Part.makeCompound(faces)
        sewn.sewShape()
        if len(sewn.Shells) != 1:
            raise ValueError('Expected one sewn shell')
        solid = Part.makeSolid(sewn.Shells[0])
        if solid.Volume < 0:
            solid.reverse()
        result = dict(environment=environment, method='Reconstructed and capped surface bands; not a cut of the saved body',
                      outer_v_range=[bs[a],bs[b]], inner_v_range=[ib[a],ib[b]], geometry=check(solid))
        if TASK == 'surface_body':
            rebuilt_path = RUN / 'surface_body.brep'
            paired_path = RUN / 'normalized_paired.brep'
            solid.exportBrep(str(rebuilt_path))
            paired = read('paired_solid.brep')
            paired.exportBrep(str(paired_path))
            result['paired_comparison'] = dict(geometry=basic(paired),
                normalized_brep_equal=rebuilt_path.read_bytes() == paired_path.read_bytes(),
                volume_difference_mm3=solid.Volume-paired.Volume)
        save(result)


try:
    main()
except Exception:
    save(dict(error=traceback.format_exc()))
    raise
