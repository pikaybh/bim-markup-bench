"""v0.48 INDEPENDENT original-question geometric predicates, not author grading.

The four original public questions contain enough information to construct
bounded, disclosed *research-defined* geometric semantic conditions. This
module independently reads ORIGINAL SOURCE and candidate IFC4X3 millimetre
files and their actual IfcOpenShell native world meshes.

IMPORTANT: IfcOpenShell geom.create_shape().geometry.verts are ALREADY METRES
even when source IFC length unit scale is 0.001. Do NOT divide world mesh
vertex coordinates by 1000. Placement raw native coordinates are millimetres.

Only true 8-vertex/12-triangle axis-aligned closed rectangular boxes from
the exact four frozen originals are admitted. Non-boxes/rotated/missing
geometry and nonpinned original question/source fail CLOSED. No hidden GT,
author benchmark grader/scorer or model generated execution is used.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
import numpy as np

from src.runtime.experimental_v44_original_native_step_readonly import PINS
from tools.bibimbap_matched25_tools import file_hash

# 0.1 mm physical contact tolerance. Other dimensions must remain above
# this margin; this is not an undocumented zero tolerance / arbitrary bbox.
TOL_M = 0.0001
MIN_POSITIVE_AREA_OVERLAP_M = 0.0001
GUID_RE = re.compile(r"\bid\s+([A-Za-z0-9_$]{22})(?=\W|$)",re.IGNORECASE)

ORIGINAL_PREDICATES={
    "geometry_test_14":"one_slab_rectangular_world_prism_is_square_one_original_side_increased",
    "geometry_test_15":"exactly_four_original_column_xy_centres_form_rectangle_one_column_moved",
    "topological_test_11":"all_original_columns_physically_contact_named_upper_slab_bottom_no_overlap",
    "topological_test_17":"delete_exactly_original_columns_not_physically_touching_named_lower_slab_top",
}


class OriginalSemantic048Error(ValueError):
    """Unsupported source, ambiguity, invalid geometry, corruption, spoof."""


def check(value,why):
    if not value:
        raise OriginalSemantic048Error(why)


@dataclass(frozen=True)
class Box:
    guid:str
    ifc_class:str
    lo:tuple[float,float,float]
    hi:tuple[float,float,float]

    def widths(self):
        return tuple(self.hi[i]-self.lo[i] for i in range(3))

    def centers(self):
        return tuple((self.hi[i]+self.lo[i])/2 for i in range(3))

    def as_record(self):
        return {
            "guid":self.guid,
            "ifcClass":self.ifc_class,
            "worldBBoxMinM":[round(v,6) for v in self.lo],
            "worldBBoxMaxM":[round(v,6) for v in self.hi],
        }


def _mesh_box(p,settings)->Box:
    check(p.is_a("IfcProduct") and p.is_a() in ("IfcSlab","IfcColumn"),
          "Only original native IfcSlab/IfcColumn physical world box")
    check(p.Representation is not None,
          "Original IFC product has no represented native physical shape")
    try:
        owner=ifcopenshell.geom.create_shape(settings,p)
    except Exception as exc:
        raise OriginalSemantic048Error(
            f"Unrenderable original native IFC product geometry: {type(exc).__name__}") from exc
    points=np.array(list(owner.geometry.verts),dtype=float)
    faces=np.array(list(owner.geometry.faces),dtype=int)
    check(points.size==24 and faces.size==36
          and np.isfinite(points).all(),
          "Physical source must have exactly 8 true world vertices and 12 triangular faces")
    points=points.reshape((8,3))
    faces=faces.reshape((12,3))
    check((faces>=0).all() and (faces<=7).all()
          and (np.min(points,axis=0)>-1e6).all()
          and (np.max(points,axis=0)<1e6).all(),
          "Original IFC native world triangle indexing/coordinates invalid")
    lo=points.min(axis=0); hi=points.max(axis=0)
    widths=hi-lo
    check((widths>2*MIN_POSITIVE_AREA_OVERLAP_M).all(),
          "Original IFC source bounding prism degenerate")
    # AABB is not sufficient for general clipped, slanted or rotated shapes.
    # Require every vertex at a distinct physical corner of the AABB.
    corners=set()
    for row in points:
        signs=[]
        for axis in range(3):
            if abs(row[axis]-lo[axis])<=TOL_M/10:
                signs.append(0)
            elif abs(row[axis]-hi[axis])<=TOL_M/10:
                signs.append(1)
            else:
                raise OriginalSemantic048Error(
                    "Not an axis-aligned physical box; AABB-only semantic verdict forbidden")
        corners.add(tuple(signs))
    check(len(corners)==8,
          "Native represented product missing real box corners")
    # In an 8-corner closed triangular surface, each corner is referenced
    # by the source face connectivity; explicit nondegenerate faces required.
    check(set(faces.flatten().tolist())==set(range(8)),
          "Source triangles do not use all physical box corners")
    # A real closed native box must be a two-manifold triangulated surface:
    # exactly 18 undirected triangle edges, each edge used exactly twice;
    # exactly two triangles on each of six physical planar box faces;
    # those two triangles must cover the entire physical rectangle area.
    edges=Counter()
    plane_triangles=Counter()
    plane_area=Counter()
    for face in faces:
        a,b,c=points[face]
        area=float(np.linalg.norm(np.cross(b-a,c-a))/2)
        check(area>1e-9,"Degenerate native triangle cannot certify physical surface")
        for i,j in ((0,1),(1,2),(2,0)):
            u,v=int(face[i]),int(face[j])
            edges[tuple(sorted((u,v)))]+=1
        planes=[]
        for axis in range(3):
            for side,bound in ((0,lo[axis]),(1,hi[axis])):
                if all(abs(q[axis]-bound)<TOL_M/10 for q in (a,b,c)):
                    planes.append((axis,side))
        check(len(planes)==1,
              "Original native triangle not contained in exactly one box face")
        plane=planes[0]
        plane_triangles[plane]+=1
        plane_area[plane]+=area
    check(len(edges)==18 and all(v==2 for v in edges.values())
          and set(plane_triangles)=={(i,j) for i in range(3) for j in (0,1)}
          and all(v==2 for v in plane_triangles.values()),
          "Source IFC native box triangular surface is not closed six-face manifold")
    for (axis,side),area in plane_area.items():
        other=[i for i in range(3) if i!=axis]
        expected=float(widths[other[0]]*widths[other[1]])
        check(abs(area-expected)<max(1e-7,expected*1e-5),
              "Native box physical face triangles do not cover complete prism face")
    return Box(p.GlobalId,p.is_a(),tuple(float(v) for v in lo),
               tuple(float(v) for v in hi))


def _all_boxes(model,klass,settings)->dict[str,Box]:
    source=model.by_type(klass)
    out={p.GlobalId:_mesh_box(p,settings) for p in source}
    check(len(out)==len(source),"Original native IFC contains repeated GUIDs")
    return out


def _same_box(a:Box,b:Box)->bool:
    return a.guid==b.guid and all(
        abs(a.lo[i]-b.lo[i])<TOL_M/10
        and abs(a.hi[i]-b.hi[i])<TOL_M/10 for i in range(3))


def _is_close(a:float,b:float)->bool:
    return abs(a-b)<=TOL_M


def _overlap_xy(a:Box,b:Box)->bool:
    return (min(a.hi[0],b.hi[0])-max(a.lo[0],b.lo[0])
             > MIN_POSITIVE_AREA_OVERLAP_M
         and min(a.hi[1],b.hi[1])-max(a.lo[1],b.lo[1])
             > MIN_POSITIVE_AREA_OVERLAP_M)


def _same_original_placements_except_one(original,candidate)->tuple[int,list[str]]:
    check(set(original)==set(candidate) and len(original)==4,
          "Original rectangular arrangement requires same four Column GUIDs")
    changes=[]
    for guid,prior in original.items():
        now=candidate[guid]
        check(all(_is_close(x,y) for x,y in
                  zip(prior.widths(),now.widths())),
              "Original columns must retain true physical width/depth/height")
        check(_is_close(prior.centers()[2],now.centers()[2]),
              "Original Columns' Z positions cannot be changed for XY rectangle task")
        shift=sum(abs(prior.centers()[k]-now.centers()[k]) for k in (0,1))
        if shift>TOL_M:
            changes.append(guid)
    return len(changes),changes


def _levels(values):
    ans=[]
    for v in sorted(values):
        if ans and abs(v-ans[-1])<=TOL_M:
            continue
        ans.append(v)
    return ans


def _rectangle_centers(columns:dict[str,Box])->tuple[bool,dict]:
    check(len(columns)==4,"Need exactly 4 original source Columns")
    xy=[(b.centers()[0],b.centers()[1]) for b in columns.values()]
    x=_levels([v[0] for v in xy])
    y=_levels([v[1] for v in xy])
    corners=set()
    for px,py in xy:
        a=[i for i,v in enumerate(x) if abs(px-v)<=TOL_M]
        b=[i for i,v in enumerate(y) if abs(py-v)<=TOL_M]
        if len(a)!=1 or len(b)!=1:
            return False,{"xLevels":x,"yLevels":y}
        corners.add((a[0],b[0]))
    ok=len(x)==2 and len(y)==2 and len(corners)==4
    if ok:
        ok=x[1]-x[0]>0.1 and y[1]-y[0]>0.1
    return ok,{
        "uniqueColumnCenterWorldX_M":[round(v,6) for v in x],
        "uniqueColumnCenterWorldY_M":[round(v,6) for v in y],
        "occupiedUniqueRectangleCorners":len(corners),
    }


def _named_target_slab(question:str,model):
    matches=GUID_RE.findall(question)
    check(len(matches)==1,
          "Original public named Slab question must contain exactly one reference GUID")
    guid=matches[0]
    obj=model.by_guid(guid)
    check(obj is not None and obj.is_a("IfcSlab"),
          "Named exact original source reference is not IfcSlab")
    return guid


def _contained_in_storey(model)->dict[str,str]:
    storeys={}
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if not rel.RelatingStructure.is_a("IfcBuildingStorey"):
            continue
        for child in rel.RelatedElements:
            if child.is_a("IfcProduct"):
                check(child.GlobalId not in storeys,
                      "Original IFC has ambiguous multiple containment storeys")
                storeys[child.GlobalId]=rel.RelatingStructure.GlobalId
    return storeys


def _source_identity(source:Path,original_sha:str,question:str,task_id:str):
    check(isinstance(source,Path) and source.is_file()
          and not source.is_symlink() and original_sha in PINS
          and file_hash(source)==original_sha,
          "Original native IFC source SHA or path not from the four exact public sources")
    pin=PINS[original_sha]
    check(pin[0]==task_id
          and task_id in ORIGINAL_PREDICATES
          and isinstance(question,str)
          and sha256(question.encode("utf8")).hexdigest()==pin[2],
          "Original published task identity or exact question SHA changed")
    return pin


def evaluate_original_semantic048(
        source:Path,candidate:Path,*,original_sha:str,
        task_id:str,public_question:str)->dict:
    """Independent original-4 native IFC world-geometry predicate.

    Research-defined correctness, NOT author-ground-truth or author scorer
    equivalence, and no task-specific answer is supplied to model-facing tools.
    The existing independent v0.45 source-preservation physical oracle MUST
    separately be run before using a PASS as an eligible candidate result.
    """
    source=Path(source);candidate=Path(candidate)
    _source_identity(source,original_sha,public_question,task_id)
    check(candidate.is_file() and not candidate.is_symlink()
          and candidate.stat().st_size>100 and candidate.resolve()!=source.resolve(),
          "Candidate must be different actual native original-mm IFC file")
    f=ifcopenshell.open(str(source))
    g=ifcopenshell.open(str(candidate))
    check(f.schema==g.schema=="IFC4X3"
          and abs(ifcopenshell.util.unit.calculate_unit_scale(f)-0.001)<1e-12
          and abs(ifcopenshell.util.unit.calculate_unit_scale(g)-0.001)<1e-12,
          "Native source/candidate IFC schema or millimetre units incompatible")
    s=ifcopenshell.geom.settings()
    s.set(s.USE_WORLD_COORDS,True)
    # World mesh coordinates are already METRES, irrespective of native units.
    slabs0=_all_boxes(f,"IfcSlab",s)
    slabs1=_all_boxes(g,"IfcSlab",s)
    cols0=_all_boxes(f,"IfcColumn",s)
    cols1=_all_boxes(g,"IfcColumn",s)
    check(file_hash(source)==original_sha,
          "Original true native IFC source changed during geometric semantic audit")
    reason=None
    observation={}
    pass_bool=False
    if task_id=="geometry_test_14":
        check(len(slabs0)==len(slabs1)==1
              and set(slabs0)==set(slabs1),
              "One original source slab must remain same IFC GUID")
        old=next(iter(slabs0.values()))
        new=slabs1[old.guid]
        original_widths=old.widths()
        new_widths=new.widths()
        check(abs(original_widths[0]-original_widths[1])>.1
              and len(cols0)==len(cols1)==0,
              "Original published slab must genuinely not be a square already")
        flags=[new_widths[i]-original_widths[i]>TOL_M for i in (0,1)]
        unchanged=[_is_close(new_widths[i],original_widths[i]) for i in (0,1)]
        pass_bool=(
            _is_close(new_widths[0],new_widths[1])
            and sum(flags)==1 and sum(unchanged)==1
            and _is_close(new_widths[2],original_widths[2])
            and _is_close(new.centers()[2],old.centers()[2])
        )
        observation={
            "sourceOriginalSlabGUID":old.guid,
            "originalWorldXYSpanM":[round(v,6) for v in original_widths[:2]],
            "candidateWorldXYSpanM":[round(v,6) for v in new_widths[:2]],
            "candidateSquareDimDifferenceM":round(abs(new_widths[0]-new_widths[1]),6),
            "oneWorldHorizontalSideIncreased":sum(flags)==1,
            "otherWorldHorizontalSideUnchanged":sum(unchanged)==1,
            "originalPhysicalSlabThicknessPreserved":_is_close(
                new_widths[2],original_widths[2]),
        }
        reason="Original physical slab horizontal extents must be square; one and only one original side increased"
    elif task_id=="geometry_test_15":
        check(len(cols0)==len(cols1)==4 and not slabs0 and not slabs1,
              "Original source must have four native Columns and no Slab")
        source_is_rect,_=_rectangle_centers(cols0)
        check(not source_is_rect,
              "Original public four Columns already form rectangle; source is not task baseline")
        n,changed=_same_original_placements_except_one(cols0,cols1)
        is_rect,geometry=_rectangle_centers(cols1)
        pass_bool=n==1 and is_rect
        observation={
            **geometry,"originalColumnsChangedWorldXYCount":n,
            "changedOriginalColumnGUIDs":changed,
            "candidateExactlyFourCornerRectangle":is_rect,
        }
        reason="Exactly one source Column moved; four true world XY centres must form all four corners of rectangle"
    elif task_id=="topological_test_11":
        named=_named_target_slab(public_question,f)
        check(len(slabs0)==len(slabs1)==2
              and set(slabs0)==set(slabs1)
              and len(cols0)==len(cols1)==2
              and set(cols0)==set(cols1)
              and all(_same_box(b,slabs1[guid]) for guid,b in slabs0.items()),
              "Original named source Slabs and two original Columns must be retained")
        underside=slabs0[named].lo[2]
        original_top=[v.hi[2] for v in cols0.values()]
        check(all(top<underside-.1 for top in original_top),
              "Original published columns do not require increased native height")
        contacts={}
        for guid,old in cols0.items():
            now=cols1[guid]
            preserved_xy=all(_is_close(old.lo[i],now.lo[i])
                             and _is_close(old.hi[i],now.hi[i]) for i in (0,1))
            top_touch=_is_close(now.hi[2],underside)
            base_fixed=_is_close(now.lo[2],old.lo[2])
            upward=now.hi[2]>old.hi[2]+TOL_M
            xy_contact=_overlap_xy(now,slabs0[named])
            contacts[guid]={
                "candidateTopM":round(now.hi[2],6),
                "namedSlabUndersideM":round(underside,6),
                "topContactWithin0p1mm":top_touch,
                "footprintPositiveAreaOverlap":xy_contact,
                "columnBaseAndXYUnchanged":base_fixed and preserved_xy,
                "columnPhysicalHeightIncreased":upward,
            }
        pass_bool=all(all([
            a["topContactWithin0p1mm"],
            a["footprintPositiveAreaOverlap"],
            a["columnBaseAndXYUnchanged"],
            a["columnPhysicalHeightIncreased"],
        ]) for a in contacts.values())
        observation={
            "originalPublicQuestionNamedSlabGUID":named,
            "originalUpperSlabUndersideWorldM":round(underside,6),
            "originalColumnTopWorldM":[round(v,6) for v in sorted(original_top)],
            "originalSourceColumnGUIDs":sorted(cols0),
            "columnContactObservationsByOriginalGUID":contacts,
        }
        reason="All source Columns' TOP surfaces must physically meet underside of SPECIFICALLY NAMED original upper Slab and overlap in world XY"
    elif task_id=="topological_test_17":
        named=_named_target_slab(public_question,f)
        check(len(slabs0)==len(slabs1)==2
              and set(slabs0)==set(slabs1)
              and all(_same_box(slab,slabs1[guid]) for guid,slab in slabs0.items())
              and len(cols0)==10
              and set(cols1).issubset(cols0),
              "Original source ten Columns and both Slab geometry must be source-preserved")
        target=slabs0[named]
        target_top=target.hi[2]
        physical_contact={guid:(
            _is_close(box.lo[2],target_top) and _overlap_xy(box,target))
            for guid,box in cols0.items()}
        retained={guid for guid,touching in physical_contact.items() if touching}
        nonrelated=set(cols0)-retained
        check(0<len(nonrelated)<=9 and retained and len(retained)<len(cols0),
              "Original named Slab does not distinguish a valid nonempty deletion set")
        storeys=_contained_in_storey(f)
        target_storey=storeys.get(named)
        check(target_storey is not None
              and all(storeys.get(g) is not None for g in cols0),
              "Original containment storey metadata does not cover named Slab and 10 Columns")
        same_storey={g for g in cols0 if storeys[g]==target_storey}
        check(same_storey==retained,
              "Ambiguous original relation: physical contact and Storey containment disagree")
        pass_bool=(set(cols1)==retained
                   and all(_same_box(cols0[guid],cols1[guid])
                           for guid in cols1))
        observation={
            "originalPublicQuestionNamedSlabGUID":named,
            "originalNamedSlabTopWorldM":round(target_top,6),
            "sourceColumnCount":len(cols0),
            "sourceColumnsPhysicallyTouchingNamedSlabCount":len(retained),
            "sourceColumnsNotPhysicallyTouchingNamedSlabCount":len(nonrelated),
            "sourceTouchingColumnsMatchNativeIfcRelContainedInSpatialStructure":True,
            "sourcePhysicalContactByGUID":dict(sorted(physical_contact.items())),
            "candidateRemainingColumnGUIDs":sorted(cols1),
            "candidateRemovedOriginalColumnGUIDs":sorted(set(cols0)-set(cols1)),
            "candidateRetainsExactlySourceTouchingColumns":set(cols1)==retained,
        }
        reason="Delete exactly all source Columns without geometric contact with NAMED lower Slab top; source physical contact independently corroborated by native storey containment"
    else:
        raise OriginalSemantic048Error("Unsupported original public task identity")
    return {
        "status":("V048_RESEARCH_DEFINED_ORIGINAL_TASK_PHYSICAL_SEMANTIC_PASS"
                  if pass_bool else "V048_RESEARCH_DEFINED_ORIGINAL_TASK_PHYSICAL_SEMANTIC_FAIL"),
        "candidatePassesIndependentResearchPhysicalPredicate":bool(pass_bool),
        "sourceOriginalPublicIFCSha256":original_sha,
        "candidateOriginalNativeMMIFCSha256":file_hash(candidate),
        "originalPublicQuestionSha256":sha256(public_question.encode("utf8")).hexdigest(),
        "originalPublicTaskId":task_id,
        "semanticPhysicalPredicate":ORIGINAL_PREDICATES[task_id],
        "physicalToleranceMetres":TOL_M,
        "positiveXYAreaOverlapAxisToleranceMetres":MIN_POSITIVE_AREA_OVERLAP_M,
        "sourceLengthUnit":"MILLIMETRE",
        "IfcOpenShellNativeWorldShapeVertexUnit":"METRE",
        "nativeWorldGeometryBoxValidation":"8_TRUE_VERTICES_12_NONDEGENERATE_TRIANGLES_ALL_8_AXIS_ALIGNED_CORNERS",
        "physicalObservations":observation,
        "researchPredicateDescription":reason,
        "independent_v045_source_preservation_oracle_must_pass_separately":True,
        "originalAuthorGraderGroundTruthEquivalenceProven":False,
        "originalAuthorEvaluatorCalled":False,
        "realLLMTrial":False,
    }
