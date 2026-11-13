"""Research-only prospective hosted IFC4X3 v0.6 declarative XML state compiler.

Only (1) single Opening offset with its hosted filling's placement inherited,
and (2) one exact Door/Window + its Opening removed together. Unsafe native
dependencies fail closed; prior versions and input IFC remain untouched.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from src.runtime.compiler import CompileReport
from src.runtime.ifc_mutations import Mutation
from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.topology_ops import _validate_opening_move_preflight
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.transaction import stage_and_commit

EPS=1e-5


class HostedV6Error(ValueError):
    pass


class HostedV6Report(CompileReport):
    def as_dict(self):
        res=super().as_dict()
        res.update({
            "status":"COMMITTED_SCOPED_IFC4X3_"+self.operations[0].operation+"_V6",
            "compiler_version":"experimental-hosted-v0.6",
            "full_original_45_native_backend_parity":False,
            "BIXML_or_Revit_production_ready":False,
            "supported_only":"single filled Opening offset or one hosted filling+Opening removal",
        })
        return res


def _find(f,guid,cls):
    try:entity=f.by_guid(guid)
    except RuntimeError as exc:raise HostedV6Error("Native IFC GlobalId missing") from exc
    if not entity.is_a(cls):
        raise HostedV6Error("Native IFC GlobalId wrong class")
    return entity


def _preflight_pair(f,filling_guid,opening_guid):
    filler=_find(f,filling_guid,"IfcRoot")
    if not (filler.is_a("IfcDoor") or filler.is_a("IfcWindow")):
        raise HostedV6Error("Filling pair must be native IfcDoor or IfcWindow")
    opening=_find(f,opening_guid,"IfcOpeningElement")
    fills=list(filler.FillsVoids)
    voids=list(opening.VoidsElements)
    if (len(fills)!=1 or fills[0].RelatingOpeningElement.GlobalId!=opening_guid
            or len(opening.HasFillings)!=1
            or opening.HasFillings[0].RelatedBuildingElement.GlobalId!=filling_guid
            or len(voids)!=1 or not voids[0].RelatingBuildingElement.is_a("IfcWall")
            or len(opening.ContainedInStructure)!=0):
        raise HostedV6Error("Opening/Filling/Wall native dependency graph not uniquely scoped")
    host=voids[0].RelatingBuildingElement
    if host.GlobalId==filling_guid:
        raise HostedV6Error("Host and filling cannot be the same object")
    allowed_filler={
        "IfcRelFillsElement","IfcRelContainedInSpatialStructure",
        "IfcRelAssociatesMaterial","IfcRelAssociatesClassification",
        "IfcRelDefinesByType","IfcRelDefinesByProperties",
    }
    filler_inv=list(f.get_inverse(filler))
    opening_inv=list(f.get_inverse(opening))
    if ({x.is_a() for x in filler_inv}-allowed_filler
        or Counter(x.is_a() for x in filler_inv)["IfcRelFillsElement"]!=1
        or Counter(x.is_a() for x in filler_inv)["IfcRelContainedInSpatialStructure"]!=1
        or Counter(x.is_a() for x in opening_inv)!=
            Counter({"IfcRelFillsElement":1,"IfcRelVoidsElement":1})):
        raise HostedV6Error("Unsupported native hosted object inverse dependencies")
    for relation in filler_inv:
        cls=relation.is_a()
        if cls=="IfcRelDefinesByProperties":
            if len(relation.RelatedObjects)!=1:
                raise HostedV6Error("Native filler Pset relation is shared")
            pset=relation.RelatingPropertyDefinition
            if not pset.is_a("IfcPropertySet") or set(f.get_inverse(pset))!={relation}:
                raise HostedV6Error("Filler Pset has shared definition owner")
        elif cls in ("IfcRelContainedInSpatialStructure",
                      "IfcRelAssociatesMaterial","IfcRelAssociatesClassification",
                      "IfcRelDefinesByType"):
            members=(relation.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                     else relation.RelatedObjects)
            if filler not in members:
                raise HostedV6Error("Native filling relationship ownership mismatched")
    return filler,opening,host


def _native_products(f):
    return {x.GlobalId:x for x in f.by_type("IfcProduct")}


def _nonmembership_attrs_equal(before,after,attribute_name):
    if before.is_a()!=after.is_a():
        return False
    for i in range(len(before)):
        name=before.attribute_name(i)
        if name==attribute_name:
            continue
        if str(before[i])!=str(after[i]):
            return False
    return True


def _validate_pair_native(source,result,filling_guid,opening_guid):
    prior=ifcopenshell.open(str(source))
    later=ifcopenshell.open(str(result))
    if prior.schema!="IFC4X3" or later.schema!=prior.schema:
        raise HostedV6Error("Hosted pair output changed IFC4X3 schema")
    filler,opening,host=_preflight_pair(prior,filling_guid,opening_guid)
    priorroots={r.GlobalId:r for r in prior.by_type("IfcRoot")}
    newroots={r.GlobalId:r for r in later.by_type("IfcRoot")}
    oldprod=_native_products(prior)
    newprod=_native_products(later)
    if set(newprod)!=set(oldprod)-{filling_guid,opening_guid}:
        raise HostedV6Error("Pair deletion changed unrelated native IFC Products")
    if any(str(oldprod[g])!=str(newprod[g]) for g in newprod):
        raise HostedV6Error("Pair deletion altered another native IFC Product")
    relations={r.GlobalId:r for r in prior.get_inverse(filler)
               if r.is_a("IfcRoot")}
    relations.update({r.GlobalId:r for r in prior.get_inverse(opening)
                      if r.is_a("IfcRoot")})
    expect_gone={filling_guid,opening_guid}
    allowed_shared={}
    for gid,rel in relations.items():
        cls=rel.is_a()
        if cls in ("IfcRelFillsElement","IfcRelVoidsElement"):
            expect_gone.add(gid)
        elif cls=="IfcRelDefinesByProperties":
            expect_gone.update((gid,rel.RelatingPropertyDefinition.GlobalId))
        else:
            members=rel.RelatedElements if cls=="IfcRelContainedInSpatialStructure" else rel.RelatedObjects
            old_members={x.GlobalId for x in members}
            if filling_guid not in old_members:
                raise HostedV6Error("Native filler missing from source IFC relation")
            if len(old_members)==1:
                expect_gone.add(gid)
            else:
                newrel=newroots.get(gid)
                if newrel is None:
                    raise HostedV6Error("Pair deletion removed shared native relation")
                new_members=(newrel.RelatedElements if cls=="IfcRelContainedInSpatialStructure"
                             else newrel.RelatedObjects)
                if {x.GlobalId for x in new_members}!=old_members-{filling_guid}:
                    raise HostedV6Error("Pair deletion corrupted other IFC relation memberships")
                allowed_shared[gid]=(
                    "RelatedElements" if cls=="IfcRelContainedInSpatialStructure"
                    else "RelatedObjects"
                )
    if set(priorroots)-set(newroots)!=expect_gone or set(newroots)-set(priorroots):
        raise HostedV6Error("Native hosted pair deletion did not match exact root closure: missing_expected="+str(sorted(expect_gone-(set(priorroots)-set(newroots))))+" unexpected_deleted="+str(sorted((set(priorroots)-set(newroots))-expect_gone)))
    for gid in priorroots.keys()&newroots.keys():
        before=priorroots[gid]
        after=newroots[gid]
        if gid in allowed_shared:
            if not _nonmembership_attrs_equal(before,after,allowed_shared[gid]):
                # IfcOpenShell may mark a type relation OwnerHistory as MODIFIED,
                # but cannot silently pass arbitrary original attribute edits.
                if before.is_a()!="IfcRelDefinesByType":
                    raise HostedV6Error("Shared native IFC relation metadata changed")
                for i in range(len(before)):
                    key=before.attribute_name(i)
                    if key not in (allowed_shared[gid],"OwnerHistory") and str(before[i])!=str(after[i]):
                        raise HostedV6Error("Other native type relation attribute changed")
                if after.OwnerHistory is None or str(after.OwnerHistory.ChangeAction)!="MODIFIED":
                    raise HostedV6Error("Changed shared type owner history not a valid modified record")
        elif str(before)!=str(after):
            raise HostedV6Error("Unrelated IFC Root was modified during hosted deletion")
    from src.runtime.hosted_door_delete import _geometry,_same_mesh
    # Only reference geometry tool implementation is reused for this
    # trusted writer's postcondition, not for the independent oracle.
    for guid,product in oldprod.items():
        if guid in (filling_guid,opening_guid,host.GlobalId):
            continue
        if product.Representation is not None and newprod[guid].Representation is not None:
            if not _same_mesh(product,newprod[guid]):
                raise HostedV6Error("Unrelated physical native IFC product mesh changed")
    source_host=oldprod[host.GlobalId];output_host=newprod[host.GlobalId]
    source_volume=_geometry(source_host)[2]
    after_volume=_geometry(output_host)[2]
    opening_volume=_geometry(opening)[2]
    if not math.isclose(after_volume-source_volume,opening_volume,abs_tol=EPS,rel_tol=0.):
        raise HostedV6Error("Host Wall native void was not actually closed")
    return len(newprod)


def _validate_opening_move_native(source,result,opening_guid,filling_guid,delta):
    prior=ifcopenshell.open(str(source))
    later=ifcopenshell.open(str(result))
    if prior.schema!="IFC4X3" or later.schema!=prior.schema:
        raise HostedV6Error("Opening move changed original IFC schema")
    roots_a={e.GlobalId:str(e) for e in prior.by_type("IfcRoot")}
    roots_b={e.GlobalId:str(e) for e in later.by_type("IfcRoot")}
    if roots_a!=roots_b:
        raise HostedV6Error("Opening offset move changed original Root inventory/attributes")
    a={e.id():str(e) for e in prior};b={e.id():str(e) for e in later}
    if set(a)!=set(b):
        raise HostedV6Error("Opening offset move added/deleted original IFC STEP entities")
    changed={x for x in a if a[x]!=b[x]}
    original_open=_find(prior,opening_guid,"IfcOpeningElement")
    later_open=_find(later,opening_guid,"IfcOpeningElement")
    previous_point=original_open.ObjectPlacement.RelativePlacement.Location
    later_point=later_open.ObjectPlacement.RelativePlacement.Location
    if changed!={previous_point.id()} or later_point.id()!=previous_point.id():
        raise HostedV6Error("Opening move changed something besides one original native CartesianPoint")
    if (not math.isclose(later_point.Coordinates[0]-previous_point.Coordinates[0],delta,abs_tol=EPS)
        or any(not math.isclose(later_point.Coordinates[i],previous_point.Coordinates[i],abs_tol=EPS)
               for i in (1,2))):
        raise HostedV6Error("Opening local XY move differs from declared XML delta")
    if (len(original_open.HasFillings)!=1 or len(later_open.HasFillings)!=1
        or original_open.HasFillings[0].RelatedBuildingElement.GlobalId!=filling_guid
        or later_open.HasFillings[0].RelatedBuildingElement.GlobalId!=filling_guid):
        raise HostedV6Error("Moving Opening lost its original filling relation")
    host=original_open.VoidsElements[0].RelatingBuildingElement
    later_host=later_open.VoidsElements[0].RelatingBuildingElement
    if host.GlobalId!=later_host.GlobalId:
        raise HostedV6Error("Opening move changed its host")
    from src.runtime.hosted_door_delete import _geometry,_same_mesh
    origprod=_native_products(prior);newprod=_native_products(later)
    if set(origprod)!=set(newprod):
        raise HostedV6Error("Opening move changed original IFC product set")
    for guid in origprod:
        if guid in (opening_guid,filling_guid,host.GlobalId):continue
        x=origprod[guid];y=newprod[guid]
        if x.Representation is not None and y.Representation is not None:
            if not _same_mesh(x,y):
                raise HostedV6Error("Moving Opening changed unrelated native geometry")
    before_volume=_geometry(host)[2];after_volume=_geometry(later_host)[2]
    if not math.isclose(before_volume,after_volume,abs_tol=EPS,rel_tol=0):
        raise HostedV6Error("Opening translation changed host original native wall volume")
    for guid in (opening_guid,filling_guid):
        before=origprod[guid];after=newprod[guid]
        if before.Representation is None or after.Representation is None:
            raise HostedV6Error("Hosted Opening/Filling native mesh missing")
        from src.runtime.hosted_door_delete import _geometry
        bv=_geometry(before)[0];av=_geometry(after)[0]
        if bv.shape!=av.shape:
            raise HostedV6Error("Moved host/filler native mesh vertex count changed")
        frame=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
        offset=np.asarray(frame[:3,0])*delta
        before_pts=sorted(map(tuple,np.rint((bv+offset)/EPS).astype(int)))
        after_pts=sorted(map(tuple,np.rint(av/EPS).astype(int)))
        if before_pts!=after_pts:
            raise HostedV6Error("Hosted Opening/Filling native world mesh did not translate")
    return len(origprod)


def compile_declarative_xml_v6(source:Path,edited_xml:bytes,destination:Path):
    if not source.is_file() or source.is_symlink() or destination.exists() or destination.is_symlink():
        raise HostedV6Error("Immutable source IFC and unused output path required")
    proj=project_ifc_v4(source)
    before_doc=parse_xml(proj.xml,expected_source_sha256=proj.source.source_sha256)
    after_doc=parse_xml(edited_xml,expected_source_sha256=proj.source.source_sha256)
    before=bind_document(before_doc,projection=proj)
    after=bind_document(after_doc,projection=proj,verify_native_edges=False)
    delta=graph_diff(before.graph,after.graph)
    sourcehash=proj.source.source_sha256
    model=ifcopenshell.open(str(source))
    if model.schema!="IFC4X3" or abs(ifcopenshell.util.unit.calculate_unit_scale(model)-1.0)>1e-8:
        raise HostedV6Error("Only original IFC4X3 normalized metres supported")
    if snapshot_source(source).source_sha256!=sourcehash:
        raise HostedV6Error("Original source bytes changed during projection")
    old=before.graph.by_id();new=after.graph.by_id()
    delta_offset=None
    if len(delta.changed_nodes)==1 and not (
            delta.added_nodes or delta.removed_nodes or delta.added_edges or delta.removed_edges):
        localid=delta.changed_nodes[0]
        prior=old[localid];current=new[localid]
        if prior.kind!="Opening" or prior.provenance!="existing_source" or prior.ifc_guid!=current.ifc_guid:
            raise HostedV6Error("Only one existing hosted Opening offset may change")
        aa=dict(prior.attributes);bb=dict(current.attributes)
        fields={k for k in aa.keys()|bb.keys() if aa.get(k)!=bb.get(k)}
        if fields!={"offset"}:
            raise HostedV6Error("Only native hosted Opening offset is supported")
        opening=_find(model,prior.ifc_guid,"IfcOpeningElement")
        if len(opening.HasFillings)!=1:
            raise HostedV6Error("v0.6 Opening move requires exactly one native Window/Door filling")
        filling=opening.HasFillings[0].RelatedBuildingElement
        if not (filling.is_a("IfcDoor") or filling.is_a("IfcWindow")):
            raise HostedV6Error("Unsupported native Opening fill class")
        _preflight_pair(model,filling.GlobalId,opening.GlobalId)
        host,point=_validate_opening_move_preflight(
            model,opening,bb,model.by_type("IfcOpeningElement"),source_offset=aa["offset"])
        delta_offset=float(bb["offset"])-float(aa["offset"])
        if abs(delta_offset)<1e-8 or not math.isfinite(delta_offset):
            raise HostedV6Error("Opening offset change zero/nonfinite")
        original_line=after_doc.managed_by_id()[localid].span.line
        op="MOVE_FILLED_OPENING"
        main_guid=opening.GlobalId
        fill_guid=filling.GlobalId
        opening_guid=opening.GlobalId
    elif len(delta.removed_nodes)==2 and not (
            delta.changed_nodes or delta.added_nodes or delta.added_edges):
        missing=[old[k] for k in delta.removed_nodes]
        if {x.kind for x in missing} not in ({"Door","Opening"},{"Window","Opening"}):
            raise HostedV6Error("Native hosted deletion requires exact Door/Window plus Opening pair")
        filler=next(x for x in missing if x.kind in ("Door","Window"))
        opening_node=next(x for x in missing if x.kind=="Opening")
        if filler.provenance!="existing_source" or opening_node.provenance!="existing_source":
            raise HostedV6Error("Cannot delete unverified virtual Opening/Filling")
        prev_edges={edge for edge in before.graph.edges
                    if edge.source in delta.removed_nodes or edge.target in delta.removed_nodes}
        if (set(delta.removed_edges)!=prev_edges
            or {x.relation for x in prev_edges}!={"host_void","opening_fill"}
            or len(prev_edges)!=2):
            raise HostedV6Error("Native pair deletion must remove only its two relationship declarations")
        door,opening,host=_preflight_pair(model,filler.ifc_guid,opening_node.ifc_guid)
        op="DELETE_HOSTED_FILLING_AND_OPENING"
        localid=filler.id+"|"+opening_node.id
        main_guid=filler.ifc_guid
        opening_guid=opening_node.ifc_guid
        fill_guid=filler.ifc_guid
        original_line=before_doc.managed_by_id()[filler.id].span.line
    else:
        raise HostedV6Error("Only single Opening offset or exact hosted Filling+Opening deletion supported")

    def write(path):
        if op=="MOVE_FILLED_OPENING":
            x,y,z=(float(v) for v in point.Coordinates)
            point.Coordinates=(x+delta_offset,y,z)
        elif op=="DELETE_HOSTED_FILLING_AND_OPENING":
            _preflight_pair(model,fill_guid,opening_guid)
            # IfcOpenShell's remove_product leaves singleton
            # IfcRelAssociatesClassification with RelatedObjects=(), which
            # violates IFC's nonempty relationship membership contract.
            # Classifications shared with other objects are never deleted.
            singleton_classification_guids=[
                rel.GlobalId for rel in model.get_inverse(door)
                if rel.is_a("IfcRelAssociatesClassification")
                and len(rel.RelatedObjects)==1
                and rel.RelatedObjects[0].GlobalId==fill_guid
            ]
            ifcopenshell.api.root.remove_product(model,product=door)
            ifcopenshell.api.root.remove_product(model,product=opening)
            for relation_guid in singleton_classification_guids:
                try:relation=model.by_guid(relation_guid)
                except RuntimeError:continue
                if (not relation.is_a("IfcRelAssociatesClassification")
                        or len(relation.RelatedObjects)!=0):
                    raise HostedV6Error("Singleton native classification not safely empty after dependent removal")
                model.remove(relation)
        else:
            raise HostedV6Error("Unknown native hosted edit")
        model.write(str(path))

    def verify(path):
        if snapshot_source(source).source_sha256!=sourcehash:
            raise HostedV6Error("Original IFC source mutated during staged transaction")
        if op=="MOVE_FILLED_OPENING":
            _validate_opening_move_native(source,path,opening_guid,fill_guid,delta_offset)
        else:
            _validate_pair_native(source,path,fill_guid,opening_guid)

    stage_and_commit(destination,write,verify)
    preserved=( _validate_opening_move_native(source,destination,opening_guid,fill_guid,delta_offset)
               if op=="MOVE_FILLED_OPENING"
               else _validate_pair_native(source,destination,fill_guid,opening_guid))
    final=snapshot_source(destination)
    if snapshot_source(source).source_sha256!=sourcehash:
        raise HostedV6Error("Original IFC source changed post transaction")
    return HostedV6Report(
        sourcehash,final.source_sha256,
        proj.source.graph_fingerprint,final.graph_fingerprint,
        (Mutation(op,localid,main_guid,original_line,
                  ("offset",) if op=="MOVE_FILLED_OPENING" else
                  ("Filling","Opening","host_void","opening_fill"),
                  "experimental v0.6 source-owned hosted relation edits"),
         ),preserved,(),destination,True)
