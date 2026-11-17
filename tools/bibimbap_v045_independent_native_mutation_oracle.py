"""Independent original IFC4X3/mm v0.45 native physical mutation oracle.

NO import of v0.45 writer, compiler or task answers. It independently
parses the exact model-facing XML, verifies its v0.44 immutable original
STEP/metadata/geometry using the prior independent oracle, and compares
actual source/OUTPUT IFC product identity, relations, placement and physical
geometry. A generic valid mutation is NOT an original task score.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
import ifcopenshell.util.placement
from lxml import etree

from tools.bibimbap_v044_independent_original_native_source_oracle import (
    ORIGINAL_PINS,validate_original_v044_native_model_read,hash_file)

Q="{urn:bim-markup-bench:toy:v0}"
AUTH="SELECTIVE_NATIVE_MUTATION_SUBJECT_TO_INDEPENDENT_ORACLE"
MODE="SINGLE_TYPED_PLAN_NATIVE_MUTATION"
EXPECTED_OP={
    "geometry_test_14":"SetSlabRectangleDimensions",
    "geometry_test_15":"MoveColumnPlacement",
    "topological_test_11":"SetAllMappedColumnDepth",
    "topological_test_17":"DeleteColumnsByGuid",
}


class IndependentNativeMutation045Error(ValueError):
    pass


def need(cond,msg):
    if not cond:
        raise IndependentNativeMutation045Error(msg)


def _num(value,lo=-1000.,hi=1000.):
    try:
        n=float(value)
    except Exception as exc:
        raise IndependentNativeMutation045Error(
            "Invalid original-source model native edit numeric value") from exc
    need(math.isfinite(n) and lo<=n<=hi,"Out of bounds or non-finite original IFC mutation")
    return n


def _mesh(p,settings):
    if p.Representation is None:
        return None
    shape=ifcopenshell.geom.create_shape(settings,p)
    vertices=list(shape.geometry.verts)
    triangles=list(shape.geometry.faces)
    need(vertices and not len(vertices)%3 and triangles and not len(triangles)%3,
         "Real IFC world geometric solids must have nonempty indexed triangles")
    positions=[tuple(round(float(vertices[i+j]),6) for j in range(3))
               for i in range(0,len(vertices),3)]
    tris=[tuple(int(triangles[i+j]) for j in range(3))
          for i in range(0,len(triangles),3)]
    need(all(0<=min(t) and max(t)<len(positions) for t in tris),
         "Real IFC triangle references outside original world vertices")
    return {
        "positions":positions,
        "triangles":tuple(sorted(tuple(sorted(positions[i] for i in t)) for t in tris)),
        "vertex_counter":Counter(positions),
        "bbox":tuple((min(p[i] for p in positions),
                      max(p[i] for p in positions)) for i in range(3)),
    }


def _refs(thing):
    if isinstance(thing,ifcopenshell.entity_instance):
        yield thing
    elif isinstance(thing,(list,tuple)):
        for part in thing:
            yield from _refs(part)


def _relation_refs(r):
    # Original relation direct endpoint roles only, not inferred topology.
    return tuple(sorted((r.attribute_name(i),v.GlobalId if v.is_a("IfcRoot")
                        else v.id(),v.is_a())
                        for i in range(len(r)) for v in _refs(r[i])))


def _root_snapshots(model):
    return {r.GlobalId:(r.is_a(),str(r.Name or ""),str(r.Description or ""))
            for r in model.by_type("IfcRoot")}


def _body_solid(product,mapped):
    need(product.Representation is not None,"Missing real original source body representation")
    reps=[r for r in product.Representation.Representations
          if r.RepresentationIdentifier=="Body"]
    need(len(reps)==1 and len(reps[0].Items)==1,
         "Ambiguous source mapped/rectangular body representation")
    item=reps[0].Items[0]
    if mapped:
        need(item.is_a("IfcMappedItem") and item.MappingSource is not None,
             "Original native column is not mapped")
        reps=item.MappingSource.MappedRepresentation.Items
        need(len(reps)==1,"Ambiguous shared mapped source")
        item=reps[0]
    need(item.is_a("IfcExtrudedAreaSolid") and
         item.SweptArea.is_a("IfcRectangleProfileDef"),
         "Actual original source native solid is not rectangular extrusion")
    return item


def _safe_delete_roots(orig,removed_targets):
    """Allowed collateral root removal only if SOLELY owned by deleted products."""
    allowed=set(removed_targets)
    for rel in orig.by_type("IfcRelationship"):
        related=getattr(rel,"RelatedObjects",None)
        if related is None:
            related=getattr(rel,"RelatedElements",None)
        if related is None:
            continue
        guids={x.GlobalId for x in related if x.is_a("IfcRoot")}
        if guids and guids.issubset(removed_targets):
            allowed.add(rel.GlobalId)
            pset=getattr(rel,"RelatingPropertyDefinition",None)
            if pset is not None and pset.is_a("IfcPropertySet"):
                # Ignore if shared by any other surviving related products.
                owners=[
                    r for r in orig.by_type("IfcRelDefinesByProperties")
                    if r.RelatingPropertyDefinition==pset
                ]
                if owners and all(
                        {x.GlobalId for x in rr.RelatedObjects}
                        .issubset(removed_targets) for rr in owners):
                    allowed.add(pset.GlobalId)
    return allowed


def _reconstruct_v044_unmodified_source_xml(src,source_sha):
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,huge_tree=False,recover=False)
    need(b"<!DOCTYPE" not in src.upper() and b"<!ENTITY" not in src.upper(),
         "XML DTD/XXE forbidden")
    root=etree.fromstring(src,parser)
    need(root.tag==Q+"Building" and len(root)==2
         and root[0].tag==Q+"OriginalNativeIFCSource"
         and root[1].tag==Q+"NativeEditPlan",
         "Original complete v0.45 model-visible XML missing immutable native source")
    header={
        "version":"0.45",
        "sourceOriginalIFCSha256":source_sha,
        "sourceIfcSchema":"IFC4X3",
        "sourceLengthUnit":"MILLIMETER_NATIVE",
        "sourceCompleteness":"ALL_ORIGINAL_NATIVE_STEP_DATA_ENTITIES_EXACT_WITH_DERIVED_READONLY_MESH",
        "nativeMutationPermission":AUTH,
    }
    need(dict(root.attrib)==header,
         "Original source/IFC schema/units/edit permissions altered")
    plan=root[1]
    need(dict(plan.attrib)=={
        "planVersion":"0.45",
        "sourceOriginalIFCSha256":source_sha,
        "editAuthority":MODE,
    } and len(plan)==1,"One exact typed source plan must be present")
    # Check immutable original structured metadata + EVERY native STEP DATA line
    # with the existing independently implemented v0.44 source oracle.
    root.remove(plan)
    root.set("version","0.44")
    root.set("nativeMutationPermission","NONE_READ_ONLY")
    v44=etree.tostring(root,encoding="utf8",xml_declaration=True,
                       pretty_print=False)
    return v44,plan


def _parse_typed_plan(plan,task,source):
    node=plan[0]
    kind=node.tag.removeprefix(Q)
    need(kind==EXPECTED_OP[task],
         "Original public source uses a different explicitly allowed native operation")
    if kind=="SetSlabRectangleDimensions":
        need(len(node)==0 and set(node.attrib)=={"ifcGuid","newXDimM","newYDimM"},
             "Slab rectangle command malformed")
        p={x.GlobalId:x for x in source.by_type("IfcSlab")}
        g=node.get("ifcGuid")
        need(len(p)==1 and g in p,"Not original native single Slab")
        solid=_body_solid(p[g],False)
        x=_num(node.get("newXDimM"),.1,25.);y=_num(node.get("newYDimM"),.1,25.)
        original=(float(solid.SweptArea.XDim)/1000,
                  float(solid.SweptArea.YDim)/1000)
        deltas=(x-original[0],y-original[1])
        need(sum(abs(d)>1e-6 for d in deltas)==1 and max(deltas)>1e-6,
             "Original slab command must grow exactly one original profile side")
        return kind,{g},(x,y)
    if kind=="MoveColumnPlacement":
        need(len(node)==0 and set(node.attrib)==
             {"ifcGuid","newWorldOriginXM","newWorldOriginYM"},
             "Original column XY move command malformed")
        cols={c.GlobalId:c for c in source.by_type("IfcColumn")}
        guid=node.get("ifcGuid")
        need(len(cols)==4 and guid in cols,"Original source Column GUID invalid")
        _body_solid(cols[guid],True)
        x=_num(node.get("newWorldOriginXM"),-40,40)
        y=_num(node.get("newWorldOriginYM"),-40,40)
        world=ifcopenshell.util.placement.get_local_placement(
            cols[guid].ObjectPlacement)
        need(abs(x-world[0,3]/1000)+abs(y-world[1,3]/1000)>1e-6,
             "Original column source absolute XY coordinates unchanged")
        return kind,{guid},(x,y)
    if kind=="SetAllMappedColumnDepth":
        need(len(node)==0 and set(node.attrib)=={"newDepthM"},
             "All original mapped column shared depth command malformed")
        cols=source.by_type("IfcColumn")
        need(len(cols)==2,"Expected exactly two original mapped Columns")
        solids=[_body_solid(x,True) for x in cols]
        need(solids[0].id()==solids[1].id(),
             "Original IFC shares no safe column shape map")
        depth=_num(node.get("newDepthM"),.2,10.)
        need(abs(depth-solids[0].Depth/1000)>1e-6,
             "Original source column height cannot be no-op")
        return kind,{p.GlobalId for p in cols},(depth,)
    if kind=="DeleteColumnsByGuid":
        need(set(node.attrib)==set() and 1<=len(node)<=9,
             "Only explicit set of 1..9 original columns may be deleted")
        available={c.GlobalId for c in source.by_type("IfcColumn")}
        need(len(available)==10,"Original source column inventory changed")
        deleted=[]
        for x in node:
            need(x.tag==Q+"DeleteColumn" and len(x)==0
                 and set(x.attrib)=={"ifcGuid"}
                 and x.get("ifcGuid") in available
                 and x.get("ifcGuid") not in deleted,
                 "Invalid, duplicated, invented, non-column GUID deletion")
            deleted.append(x.get("ifcGuid"))
        return kind,set(deleted),()
    raise IndependentNativeMutation045Error("Unknown original IFC operation")


def _close(a,b,eps=2e-6):
    return abs(a-b)<=eps


def verify_original_native_mutation_v045(
        original_source:Path,candidate_mm:Path,*,submitted_xml:bytes,
        source_sha:str,task_id:str)->dict:
    original_source=Path(original_source)
    candidate_mm=Path(candidate_mm)
    need(task_id in ORIGINAL_PINS
         and source_sha==ORIGINAL_PINS[task_id][0]
         and original_source.is_file()
         and candidate_mm.is_file()
         and not original_source.is_symlink()
         and not candidate_mm.is_symlink()
         and original_source.resolve()!=candidate_mm.resolve()
         and hash_file(original_source)==source_sha,
         "Original native IFC4X3/mm public source hash or candidate path invalid")
    v44,plan=_reconstruct_v044_unmodified_source_xml(
        submitted_xml,source_sha)
    validate_original_v044_native_model_read(
        original_source,v44,task_id=task_id)
    src=ifcopenshell.open(str(original_source))
    target=ifcopenshell.open(str(candidate_mm))
    for file in (src,target):
        need(file.schema=="IFC4X3"
             and _close(ifcopenshell.util.unit.calculate_unit_scale(file),.001,1e-12),
             "Original source and edited candidate must both remain IFC4X3/mm")
    kind,changes,params=_parse_typed_plan(plan,task_id,src)
    all_src={r.GlobalId:r for r in src.by_type("IfcRoot")}
    all_dst={r.GlobalId:r for r in target.by_type("IfcRoot")}
    original_root_meta=_root_snapshots(src)
    candidate_root_meta=_root_snapshots(target)
    need(not (set(all_dst)-set(all_src)),
         "Native candidate added unexpected source Root, relation or product GUID")
    missing=set(all_src)-set(all_dst)
    if kind=="DeleteColumnsByGuid":
        need(changes.issubset(missing),
             "Native candidate did not delete exactly requested actual original columns")
        need(missing.issubset(_safe_delete_roots(src,changes)),
             "Deleting original columns removed unrelated original native relationships/metadata")
    else:
        need(not missing,
             "A native edit other than DeleteColumns cannot remove original IFC Roots")
    for guid in set(all_dst):
        need(original_root_meta[guid]==candidate_root_meta[guid],
             "Native edit modified unrelated original IFC Root class/name/description")

    src_products={p.GlobalId:p for p in src.by_type("IfcProduct")}
    dst_products={p.GlobalId:p for p in target.by_type("IfcProduct")}
    need(set(dst_products)==set(src_products)-(
        changes if kind=="DeleteColumnsByGuid" else set()),
        "Native original product population changed outside the typed edit set")

    src_rels={r.GlobalId:r for r in src.by_type("IfcRelationship")}
    dst_rels={r.GlobalId:r for r in target.by_type("IfcRelationship")}
    need(not (set(dst_rels)-set(src_rels)),
         "New or forged original native relationship GUIDs appeared")
    for guid,r in dst_rels.items():
        old=src_rels[guid]
        before=_relation_refs(old)
        after=_relation_refs(r)
        if kind=="DeleteColumnsByGuid":
            # Existing source relationship reference to a deleted column may
            # disappear only at that exact explicit original column GUID.
            expected=tuple(x for x in before if not (
                isinstance(x[1],str) and x[1] in changes))
            need(after==expected,
                 "Retained original native IFC relationship endpoints/roles changed outside deletion")
        else:
            need(before==after,
                 "Original native IFC relationship endpoints/roles changed after update")

    source_elements={p.GlobalId:p for p in src.by_type("IfcElement")}
    dest_elements={p.GlobalId:p for p in target.by_type("IfcElement")}
    need(set(dest_elements)==set(source_elements)-(
        changes if kind=="DeleteColumnsByGuid" else set()),
        "Original native physical element count or class changed outside allowed edit")
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    affected=0
    preserved=0
    before_meshes={}
    after_meshes={}
    for guid,item in source_elements.items():
        before_meshes[guid]=_mesh(item,settings)
    for guid,item in dest_elements.items():
        after_meshes[guid]=_mesh(item,settings)
    for guid,orig_mesh in before_meshes.items():
        if guid not in after_meshes:
            need(guid in changes and kind=="DeleteColumnsByGuid",
                 "Original source physical element disappeared outside delete operation")
            affected+=1
            continue
        new_mesh=after_meshes[guid]
        need(orig_mesh is not None and new_mesh is not None,
             "Native original geometry unexpectedly inaccessible")
        if guid not in changes:
            need(orig_mesh["triangles"]==new_mesh["triangles"]
                 and orig_mesh["vertex_counter"]==new_mesh["vertex_counter"],
                 "Unrelated original IFC product physically changed during native edit")
            preserved+=1
        else:
            need(orig_mesh["triangles"]!=new_mesh["triangles"]
                 or orig_mesh["vertex_counter"]!=new_mesh["vertex_counter"],
                 "Typed native edit produced no actual physical source geometry change")
            affected+=1
    if kind=="SetSlabRectangleDimensions":
        guid=next(iter(changes))
        before=before_meshes[guid]["bbox"]
        after=after_meshes[guid]["bbox"]
        old_solid=_body_solid(src_products[guid],False)
        new_solid=_body_solid(dst_products[guid],False)
        need(_close(new_solid.SweptArea.XDim/1000,params[0])
             and _close(new_solid.SweptArea.YDim/1000,params[1])
             and _close(new_solid.Depth,old_solid.Depth),
             "Native original Slab rectangle dimensions or extrusion thickness incorrect")
        for axis in range(3):
            need(_close(sum(before[axis]),sum(after[axis])),
                 "Slab original dimension change moved its original footprint center or height")
        need(_close(after[2][1]-after[2][0],
                    before[2][1]-before[2][0])
             and sorted(round(after[i][1]-after[i][0],6) for i in (0,1))==
                 sorted(round(x,6) for x in params),
             "Native Slab physical XY dimensions do not match submitted original source plan")
    elif kind=="MoveColumnPlacement":
        guid=next(iter(changes))
        a=src_products[guid].ObjectPlacement
        b=dst_products[guid].ObjectPlacement
        need(a.is_a("IfcLocalPlacement") and b.is_a("IfcLocalPlacement")
             and ((a.PlacementRelTo is None and b.PlacementRelTo is None)
                  or (a.PlacementRelTo is not None and
                      b.PlacementRelTo is not None and
                      a.PlacementRelTo.id()==b.PlacementRelTo.id())),
             "Moved original Column placement changed its original IFC parent")
        before_mat=ifcopenshell.util.placement.get_local_placement(a)
        after_mat=ifcopenshell.util.placement.get_local_placement(b)
        need(all(_close(before_mat[i,j],after_mat[i,j],1e-8)
                 for i in range(4) for j in range(4)
                 if (i,j) not in ((0,3),(1,3))),
             "Moved original Column changed original source Z, orientation, parent or basis")
        before=(before_mat[0,3]/1000,before_mat[1,3]/1000,before_mat[2,3]/1000)
        after=(after_mat[0,3]/1000,after_mat[1,3]/1000,after_mat[2,3]/1000)
        delta=(params[0]-before[0],params[1]-before[1],0)
        need(_close(after[0],params[0]) and _close(after[1],params[1])
             and _close(after[2],before[2]),
             "Native source Column original-mm absolute edit position differs from XML")
        old=before_meshes[guid]
        new=after_meshes[guid]
        expected=Counter(tuple(round(v[i]+delta[i],6) for i in range(3))
                         for v in old["positions"])
        need(new["vertex_counter"]==expected,
             "Column physical mapped-world vertices did not translate exactly by XML XY")
        need(_body_solid(src_products[guid],True).Depth==
             _body_solid(dst_products[guid],True).Depth,
             "Moved original column silently changed native shared mapped geometry depth")
    elif kind=="SetAllMappedColumnDepth":
        source_cols=src.by_type("IfcColumn")
        candidate_cols=target.by_type("IfcColumn")
        need(len(source_cols)==len(candidate_cols)==2
             and {c.GlobalId for c in source_cols}==changes,
             "All two original mapped Columns must be height-edited as one shared shape")
        ss={_body_solid(p,True).id() for p in source_cols}
        tt={_body_solid(p,True).id() for p in candidate_cols}
        need(len(ss)==len(tt)==1,
             "Original two mapped Columns unexpectedly lost shared native representation")
        for guid in changes:
            prior=before_meshes[guid]["bbox"]
            next_=after_meshes[guid]["bbox"]
            need(_close(_body_solid(dst_products[guid],True).Depth/1000,params[0])
                 and all(_close(prior[i][0],next_[i][0]) and
                         _close(prior[i][1],next_[i][1]) for i in (0,1))
                 and _close(prior[2][0],next_[2][0])
                 and _close(next_[2][1]-next_[2][0],params[0]),
                 "Original Column height physical top, XY or bottom differs from XML depth")
    elif kind=="DeleteColumnsByGuid":
        need(len(changes)>=1 and len(target.by_type("IfcColumn"))==
             len(src.by_type("IfcColumn"))-len(changes),
             "Native original source deletion count/class incorrectly changed")
        need(all(src_products[g].is_a("IfcColumn") for g in changes),
             "Non-Column original native entity was deleted")
        need(all(s.GlobalId in dst_products for s in src.by_type("IfcSlab")),
             "Original source Slabs must remain physically intact after Column deletion")
    else:
        raise IndependentNativeMutation045Error("Unsupported original IFC mutation type")
    need(hash_file(original_source)==source_sha,
         "Original source IFC file changed while independently validating native candidate")
    return {
        "status":"V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS",
        "task_id":task_id,
        "operation_kind":kind,
        "original_source_sha256":source_sha,
        "candidate_original_native_mm_sha256":hash_file(candidate_mm),
        "source_ifc_schema":"IFC4X3",
        "source_length_unit":"millimetres",
        "all_original_model_visible_readonly_STEP_revalidated":True,
        "original_product_guids_preserved_except_explicit_deletions":True,
        "original_relationships_and_roles_preserved_except_deletion_refs":True,
        "non_target_original_physical_products_unchanged":preserved,
        "exact_target_original_physical_products_actually_changed":affected,
        "original_author_task_semantic_success_proven":False,
        "original_author_grader_called":False,
    }
