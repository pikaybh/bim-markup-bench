"""v0.14 original-source IFC4X3 hosted Window-only native deletion.

EXPERIMENTAL RESEARCH ONLY, never production Xim. The direct XML editor
sees the ENTIRE current original Window inventory as a small source-SHA-
pinned declarative substate. Removing one or more <Window> records means
their native IfcWindow objects are deleted in an independently verified
source copy. XML never exposes an imperative 'Delete' command, arbitrary
GUID, hidden target, IfcOpenShell API, or trusted native mutation logic.

Original source host Wall and native IfcOpeningElement are deliberately
RETAINED as voids: "remove a window" does not mean patch the wall or
remove the hole. The original IfcRelFillsElement is removed and exclusive
Window properties/material assignment cleaned; shared original
type/classification/storey memberships are updated without destroying
relationships, owner history or original sequence. All unrelated native
Root, original STEP, meshes, geometry and metadata remain source-owned.

This is NOT general native write access to the v0.13 read-only catalog,
NOT a full BIM XML edit model, NOT Window MOVE, NOT Opening CREATE/UPDATE/
DELETE, NOT IfcSpace/IfcBeam edit support and NOT full45 task parity.
Old v0.1-v0.13 historical research source and benchmark D0 are unchanged.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import tempfile

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit
from lxml import etree

from src.security.agent_boundary import check_xml_bytes,SecurityBoundaryError
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.experimental_v13_opaque_source import (
    project_original_native_v13,
)

NS="urn:bim-markup-bench:source-window-delete:v0.14"
Q="{"+NS+"}"
MAX_DELETED_WINDOWS=8
EXPECTED_INVERSES=Counter({
    "IfcRelDefinesByProperties":2,
    "IfcRelAssociatesMaterial":1,
    "IfcRelAssociatesClassification":1,
    "IfcRelDefinesByType":1,
    "IfcRelFillsElement":1,
    "IfcRelContainedInSpatialStructure":1,
})
SHARED_MEMBERSHIP_ATTR={
    "IfcRelDefinesByType":"RelatedObjects",
    "IfcRelAssociatesClassification":"RelatedObjects",
    "IfcRelContainedInSpatialStructure":"RelatedElements",
}
EXCLUSIVE_PROPERTIES={
    "IfcRelFillsElement":1,
    "IfcRelAssociatesMaterial":1,
    "IfcRelDefinesByProperties":2,
    "IfcPropertySet":2,
}


class NativeWindowV14Error(ValueError):
    pass


@dataclass(frozen=True)
class OriginalNativeWindowStateV14:
    source_sha256:str
    original_native_source_catalog_sha256:str
    source_schema:str
    original_full_window_count:int
    xml:bytes

    def report(self):
        return {
            "status":"ORIGINAL_IFC4X3_HOSTED_WINDOW_DECLARATIVE_FULL_INVENTORY_V014",
            "source_sha256":self.source_sha256,
            "native_source_catalog_sha256":self.original_native_source_catalog_sha256,
            "full_original_window_count":self.original_full_window_count,
            "window_state_xml_sha256":sha256(self.xml).hexdigest(),
            "declarative_window_substate_is_not_entire_BIM_model":True,
            "native_window_move_supported":False,
            "native_opening_edit_supported":False,
            "source_native_space_beam_edit_supported":False,
            "full_original45_backend_parity":False,
            "new_paid_model_calls":0,
        }


@dataclass(frozen=True)
class SharedNativeRelation:
    global_id:str
    ifc_class:str
    membership_attr:str
    original_member_guids:tuple[str,...]
    original_owner_history_id:int|None


@dataclass(frozen=True)
class WindowDeleteV14Report:
    source_sha256:str
    output_sha256:str
    edited_window_state_xml_sha256:str
    target_original_window_guids:tuple[str,...]
    retained_original_opening_guids:tuple[str,...]
    removed_original_native_root_guids:tuple[str,...]
    modified_original_shared_membership_relations:tuple[str,...]
    independent_unrelated_roots_preserved:int
    independent_native_geometries_preserved:int
    output_path:Path

    def as_dict(self):
        return {
            "status":"ORIGINAL_IFC4X3_SOURCE_NATIVE_HOSTED_WINDOW_DELETE_V014",
            "source_sha256":self.source_sha256,
            "result_sha256":self.output_sha256,
            "edited_window_state_xml_sha256":self.edited_window_state_xml_sha256,
            "source_original_window_delete_targets":
                list(self.target_original_window_guids),
            "original_opening_voids_retained":
                list(self.retained_original_opening_guids),
            "removed_exclusive_original_root_guids":
                list(self.removed_original_native_root_guids),
            "source_shared_membership_relation_guids_modified":
                list(self.modified_original_shared_membership_relations),
            "unrelated_original_native_roots_preserved":
                self.independent_unrelated_roots_preserved,
            "source_original_native_geometries_preserved":
                self.independent_native_geometries_preserved,
            "source_original_ifc_unmodified":True,
            "source_native_host_wall_and_opening_geometry_rebuilt":False,
            "editor_can_move_or_add_original_window":False,
            "editor_can_edit_original_IfcSpace_or_IfcBeam":False,
            "full_original45_semantic_write_parity":False,
            "LLM_or_paid_API_calls":0,
            "result_path":str(self.output_path),
        }


def _sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def _schema()->etree.XMLSchema:
    spec=(Path(__file__).resolve().parents[2]/
          "spec"/"experimental_original_hosted_window_v014.xsd")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,huge_tree=False)
    root=etree.parse(str(spec),parser)
    if root.find(".//{http://www.w3.org/2001/XMLSchema}include") is not None:
        raise NativeWindowV14Error("External experimental native XSD includes forbidden")
    if root.find(".//{http://www.w3.org/2001/XMLSchema}import") is not None:
        raise NativeWindowV14Error("External experimental native XSD imports forbidden")
    return etree.XMLSchema(root)


def _native_filled_windows(f):
    windows={}
    for obj in sorted(f.by_type("IfcWindow"),key=lambda w:w.GlobalId):
        fills=list(obj.FillsVoids)
        if len(fills)!=1 or fills[0].RelatedBuildingElement!=obj:
            raise NativeWindowV14Error("Original IfcWindow has ambiguous native IfcRelFillsElement")
        opening=fills[0].RelatingOpeningElement
        if opening is None or not opening.is_a("IfcOpeningElement"):
            raise NativeWindowV14Error("Original IFC native Window opening is unavailable")
        voids=list(opening.VoidsElements)
        if len(voids)!=1 or voids[0].RelatedOpeningElement!=opening:
            raise NativeWindowV14Error("Original Opening lacks a unique source IfcRelVoidsElement")
        host=voids[0].RelatingBuildingElement
        if host is None or not host.is_a("IfcWall"):
            raise NativeWindowV14Error("Only native original IfcWall hosted openings accepted")
        if len(opening.HasFillings)!=1 or opening.HasFillings[0]!=fills[0]:
            raise NativeWindowV14Error("Original Opening has multiple/native unsupported fillings")
        windows[obj.GlobalId]=(opening.GlobalId,host.GlobalId)
    return windows


def native_full_window_state_v14(source:Path)->OriginalNativeWindowStateV14:
    if source.is_symlink() or not source.is_file():
        raise NativeWindowV14Error("Immutable original IFC4X3 source must be an ordinary file")
    snap=snapshot_source(source)
    if snap.ifc_schema!="IFC4X3":
        raise NativeWindowV14Error("Original hosted native Window delete is IFC4X3-only")
    f=ifcopenshell.open(str(source))
    if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-8:
        raise NativeWindowV14Error("Original native IFC4X3 must be explicitly metre-normalized")
    # v0.13 keeps inaccessible typed original windows in a physically
    # audited READ ONLY catalog. This v0.14 substate is separately *authorised*
    # for narrowly-scoped native Window deletion, never for native metadata
    # change or complete source catalog edit.
    v13=project_original_native_v13(source)
    if v13.native_source_sha256!=snap.source_sha256:
        raise NativeWindowV14Error("v0.13 original source SHA disagrees with v0.14")
    cat=sha256(v13.source_catalog_xml).hexdigest()
    orig=_native_filled_windows(f)
    root=etree.Element(
        Q+"NativeWindowState",nsmap={None:NS},
        attrib={
            "version":"0.14",
            "sourceModelSha256":snap.source_sha256,
            "sourceCatalogSha256":cat,
            "sourceIfcSchema":"IFC4X3",
            "units":"m",
            "editScope":"FULL_ORIGINAL_WINDOW_INVENTORY_DELETE_ONLY",
        }
    )
    windows=etree.SubElement(root,Q+"Windows")
    for guid,(opening,host) in sorted(orig.items()):
        etree.SubElement(windows,Q+"Window",attrib={
            "ifcGuid":guid,
            "originalOpeningGuid":opening,
            "originalHostWallGuid":host,
            "originalIfcClass":"IfcWindow",
            "ownership":"ORIGINAL_NATIVE_SOURCE",
        })
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,
                       pretty_print=True)
    _read_window_nodes(xml,snap.source_sha256,cat,orig)
    if _sha(source)!=snap.source_sha256:
        raise NativeWindowV14Error("Original source changed while building Windows XML")
    return OriginalNativeWindowStateV14(
        snap.source_sha256,cat,"IFC4X3",len(orig),xml)


def _read_window_nodes(xml:bytes,source_sha:str,catalog_sha:str,
                       original:dict[str,tuple[str,str]])->dict[str,tuple[str,str]]:
    try:
        check_xml_bytes(xml)
    except SecurityBoundaryError as exc:
        raise NativeWindowV14Error("Unsafe native Window declarative XML") from exc
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,huge_tree=False,
                           remove_comments=True,remove_pis=True)
    try:
        root=etree.fromstring(xml,parser=parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise NativeWindowV14Error("Malformed or unsafe native Window declarative XML") from exc
    if root.getroottree().docinfo.doctype:
        raise NativeWindowV14Error("DTD is forbidden in native Window source XML")
    if root.tag!=Q+"NativeWindowState" or not _schema().validate(root):
        raise NativeWindowV14Error("Original native Window full inventory XSD rejected edit")
    if (root.get("sourceModelSha256")!=source_sha
        or root.get("sourceCatalogSha256")!=catalog_sha
        or root.get("sourceIfcSchema")!="IFC4X3"):
        raise NativeWindowV14Error("Native source/catalog hash or original schema mismatch")
    result={}
    window_container=root.find(Q+"Windows")
    for entry in window_container:
        guid=entry.get("ifcGuid")
        pair=(entry.get("originalOpeningGuid"),entry.get("originalHostWallGuid"))
        if guid in result or guid not in original or original[guid]!=pair:
            raise NativeWindowV14Error(
                "A retained original Window was duplicated/created or its native opening/host changed"
            )
        result[guid]=pair
    if set(result)-set(original):
        raise NativeWindowV14Error("Full original Window state cannot create native Windows")
    return result


def _window_source_dependents(f,guids:tuple[str,...]):
    if not guids or len(guids)>MAX_DELETED_WINDOWS:
        raise NativeWindowV14Error("Only 1..8 original native Window deletions per transaction")
    source_roots={x.GlobalId:x for x in f.by_type("IfcRoot")}
    expected_removed=set()
    shared_map={}
    retained_openings={}
    for guid in guids:
        window=source_roots.get(guid)
        if window is None or not window.is_a("IfcWindow"):
            raise NativeWindowV14Error("Original source Window no longer exists")
        inverses=list(f.get_inverse(window))
        if Counter(x.is_a() for x in inverses)!=EXPECTED_INVERSES:
            raise NativeWindowV14Error("Original Window has unsupported inverse dependency pattern")
        fills=[x for x in inverses if x.is_a("IfcRelFillsElement")]
        if len(fills)!=1 or fills[0].RelatedBuildingElement!=window:
            raise NativeWindowV14Error("Original Window/native IfcRelFills is not unique")
        opening=fills[0].RelatingOpeningElement
        if not opening.is_a("IfcOpeningElement") or (
            len(opening.HasFillings)!=1 or
            opening.HasFillings[0]!=fills[0]):
            raise NativeWindowV14Error("Original Opening filling relation is not safely exclusive")
        voids=list(opening.VoidsElements)
        if len(voids)!=1 or not voids[0].RelatingBuildingElement.is_a("IfcWall"):
            raise NativeWindowV14Error("Source Opening does not have exactly one native host wall")
        if Counter(x.is_a() for x in f.get_inverse(opening))!=Counter({
            "IfcRelFillsElement":1,"IfcRelVoidsElement":1
        }):
            raise NativeWindowV14Error("Source Opening has unexpected native inverse dependencies")
        retained_openings[guid]=(opening.GlobalId,
                                 voids[0].RelatingBuildingElement.GlobalId)
        exclusive=[window,fills[0]]
        for rel in inverses:
            if rel.is_a("IfcRelAssociatesMaterial"):
                if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0]!=window:
                    raise NativeWindowV14Error("Source Window material relation not exclusive")
                exclusive.append(rel)
            elif rel.is_a("IfcRelDefinesByProperties"):
                if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0]!=window:
                    raise NativeWindowV14Error("Source Window PropertySet relation not exclusive")
                pset=rel.RelatingPropertyDefinition
                if (pset is None or not pset.is_a("IfcPropertySet")
                    or set(f.get_inverse(pset))!={rel}):
                    raise NativeWindowV14Error("Source original Window Pset ownership not exclusive")
                exclusive.extend((rel,pset))
            elif rel.is_a() in SHARED_MEMBERSHIP_ATTR:
                klass=rel.is_a()
                attr=SHARED_MEMBERSHIP_ATTR[klass]
                if window not in getattr(rel,attr):
                    raise NativeWindowV14Error("Source shared relationship missing target Window")
                if rel.GlobalId not in shared_map:
                    shared_map[rel.GlobalId]=SharedNativeRelation(
                        rel.GlobalId,klass,attr,
                        tuple(x.GlobalId for x in getattr(rel,attr)),
                        rel.OwnerHistory.id() if rel.OwnerHistory else None,
                    )
            elif rel.is_a()!="IfcRelFillsElement":
                raise NativeWindowV14Error("Window contains native unsupported relationship")
        if (len(exclusive)!=7 or
            Counter(x.is_a() for x in exclusive)!=
            Counter({"IfcWindow":1,**EXCLUSIVE_PROPERTIES})):
            raise NativeWindowV14Error("Original Window exclusive source root ownership unexpected")
        exclusive_ids={x.GlobalId for x in exclusive}
        if len(exclusive_ids)!=len(exclusive) or (expected_removed&exclusive_ids):
            raise NativeWindowV14Error("Original Window exclusive rooted dependencies are shared")
        expected_removed|=exclusive_ids
    target_set=set(guids)
    for rel in shared_map.values():
        survivors=set(rel.original_member_guids)-target_set
        if not survivors or not (set(rel.original_member_guids)&target_set):
            raise NativeWindowV14Error("Native source shared membership cannot become empty")
        if len(set(rel.original_member_guids))!=len(rel.original_member_guids):
            raise NativeWindowV14Error("Original native relationship has duplicate membership")
    if expected_removed&set(shared_map):
        raise NativeWindowV14Error("Original native relationship ambiguous exclusive/shared ownership")
    return tuple(sorted(expected_removed)),tuple(
        shared_map[k] for k in sorted(shared_map)),retained_openings


def _restore_native_shared_relation_history(f,shared,deleted:set[str]):
    """Restore original order/OwnerHistory; no fresh timestamp side effect.

    IfcOpenShell root.remove_product currently creates a new OwnerHistory
    timestamp and reorders original RelatedObjects in IfcRelDefinesByType.
    Restore *source original* metadata; this is a SOURCE-ANCHORED stable
    delete operation, not inventing a real edit timestamp. New orphan
    OwnerHistory objects must be removed before IFC validation.
    """
    newly_orphaned={}
    for original in shared:
        try:
            relation=f.by_guid(original.global_id)
        except RuntimeError as exc:
            raise NativeWindowV14Error("Native source shared Root deleted unexpectedly") from exc
        if relation.is_a()!=original.ifc_class:
            raise NativeWindowV14Error("Original source shared relation class changed")
        desired=tuple(
            f.by_guid(g) for g in original.original_member_guids
            if g not in deleted
        )
        if not desired:
            raise NativeWindowV14Error("Shared source relationship membership became empty")
        current=getattr(relation,original.membership_attr)
        if {x.GlobalId for x in current}!={x.GlobalId for x in desired}:
            raise NativeWindowV14Error("Native API edited unexpected original relationship member")
        setattr(relation,original.membership_attr,desired)
        previous=original.original_owner_history_id
        current_history=relation.OwnerHistory
        current_id=current_history.id() if current_history else None
        if previous!=current_id:
            if previous is None:
                relation.OwnerHistory=None
            else:
                try:
                    relation.OwnerHistory=f.by_id(previous)
                except RuntimeError as exc:
                    raise NativeWindowV14Error("Original native source OwnerHistory no longer exists") from exc
            if current_history is not None:
                newly_orphaned[current_id]=current_history
    for stepid in sorted(newly_orphaned):
        history=newly_orphaned[stepid]
        if not f.get_inverse(history):
            f.remove(history)
        else:
            raise NativeWindowV14Error(
                "Native API created a new OwnerHistory used outside affected source relations"
            )


def _native_volume_and_mesh(product):
    """Exact source native geometry fingerprint independent of XML geometry.

    For unlike original triangulation order, compare quantized world
    vertices as a multiset and counts, plus signed/absolute true volume
    when available. A voided Wall must retain original native shape.
    """
    import numpy as np
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,product)
        vertices=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)
        faces=np.asarray(shape.geometry.faces,dtype=np.int64).reshape(-1,3)
        volume=float(ifcopenshell.util.shape.get_volume(shape.geometry))
    except Exception as exc:
        raise NativeWindowV14Error("Source native physical product geometry unavailable") from exc
    if (len(vertices)<4 or len(faces)<4 or
        not np.all(np.isfinite(vertices)) or not np.isfinite(volume)):
        raise NativeWindowV14Error("Source original physical native mesh invalid")
    rounded=np.rint(vertices/1e-6).astype(np.int64)
    return (
        len(vertices),len(faces),Counter(map(tuple,rounded)),round(volume,7)
    )


def _verify_native_window_only_delete(source:Path,after:Path,
                                      target_guids:tuple[str,...],
                                      removed_root_guids:tuple[str,...],
                                      affected_shared:tuple[SharedNativeRelation,...],
                                      retained_openings:dict[str,tuple[str,str]])->tuple[int,int]:
    src=ifcopenshell.open(str(source))
    out=ifcopenshell.open(str(after))
    if src.schema!="IFC4X3" or out.schema!=src.schema or (
        abs(ifcopenshell.util.unit.calculate_unit_scale(out)-1.)>1e-8
    ):
        raise NativeWindowV14Error("Original IFC4X3 schema/metre native source changed")
    orig_roots={x.GlobalId:x for x in src.by_type("IfcRoot")}
    new_roots={x.GlobalId:x for x in out.by_type("IfcRoot")}
    if (set(orig_roots)-set(new_roots)!=set(removed_root_guids)
        or set(new_roots)-set(orig_roots)):
        raise NativeWindowV14Error("Native Window deletion changed non-owned IFC Root inventory")
    target_set=set(target_guids)
    shared={x.global_id:x for x in affected_shared}
    preserved=0
    for guid in sorted(set(orig_roots)&set(new_roots)):
        prior=orig_roots[guid]
        post=new_roots[guid]
        if prior.is_a()!=post.is_a():
            raise NativeWindowV14Error("Unrelated source IFC Root class changed")
        if guid in shared:
            rec=shared[guid]
            members=getattr(post,rec.membership_attr)
            if tuple(x.GlobalId for x in members)!=tuple(
                g for g in rec.original_member_guids if g not in target_set
            ):
                raise NativeWindowV14Error("Original native shared membership order/content wrong")
            for i in range(len(prior)):
                name=prior.attribute_name(i)
                if name==rec.membership_attr:
                    continue
                if str(prior[i])!=str(post[i]):
                    raise NativeWindowV14Error(
                        "Original shared source relationship metadata/OwnerHistory changed"
                    )
        elif str(prior)!=str(post):
            raise NativeWindowV14Error("Unrelated original source IFC Root changed on Window delete")
        preserved+=1
    # The unmodified original *source Wall void* is still exactly the same;
    # only the filling is removed. This is not a Door/Window+Opening pair
    # operation and must never make the hole disappear.
    for window_guid,(opening_guid,host_guid) in retained_openings.items():
        if window_guid not in target_set:
            raise NativeWindowV14Error("Unexpected original Opening preservation target")
        if (window_guid in new_roots or
            opening_guid not in new_roots or
            host_guid not in new_roots):
            raise NativeWindowV14Error("Original Window/Opening/host survivor graph broken")
        old_open=orig_roots[opening_guid];new_open=new_roots[opening_guid]
        if str(old_open)!=str(new_open):
            raise NativeWindowV14Error("Original void Opening STEP/placement changed")
        prior_void=old_open.VoidsElements
        post_void=new_open.VoidsElements
        if (len(prior_void)!=1 or len(post_void)!=1
            or prior_void[0].GlobalId!=post_void[0].GlobalId
            or post_void[0].RelatingBuildingElement.GlobalId!=host_guid
            or len(new_open.HasFillings)!=0):
            raise NativeWindowV14Error("Original IFC native host void or Window fill not closed")
    original_products={x.GlobalId:x for x in src.by_type("IfcProduct")}
    current_products={x.GlobalId:x for x in out.by_type("IfcProduct")}
    if (set(original_products)-set(current_products)!=target_set
        or set(current_products)-set(original_products)):
        raise NativeWindowV14Error("Native API removed/created unrelated source IFC Products")
    # All retained Product physical shapes are actually checked in world
    # space, not inferred solely from Root/STEP strings.
    kept_mesh=0
    for guid in sorted(set(original_products)&set(current_products)):
        prior=original_products[guid];post=current_products[guid]
        if (prior.Representation is None)!=(post.Representation is None):
            raise NativeWindowV14Error("Original retained Product native representation changed")
        if prior.Representation is None:
            continue
        if _native_volume_and_mesh(prior)!=_native_volume_and_mesh(post):
            raise NativeWindowV14Error("Original retained Product native physical mesh changed")
        kept_mesh+=1
    # Source original STEP ids must not be expanded by newly generated
    # timestamp OwnerHistory or unrelated native API representations.
    original_step={x.id() for x in src}
    later_step={x.id() for x in out}
    if later_step-original_step:
        raise NativeWindowV14Error("Native API introduced extra STEP entity to source Windows deletion")
    return preserved,kept_mesh


def compile_native_hosted_windows_v14(source:Path,edited_xml:bytes,
                                      destination:Path)->WindowDeleteV14Report:
    if (source.is_symlink() or not source.is_file()
        or destination.exists() or destination.is_symlink()
        or source.resolve()==destination.resolve()
        or not destination.parent.is_dir()):
        raise NativeWindowV14Error("Native original source and UNUSED output path required")
    before_sha=_sha(source)
    original_state=native_full_window_state_v14(source)
    if before_sha!=original_state.source_sha256:
        raise NativeWindowV14Error("Original source file changed before native compiler")
    f=ifcopenshell.open(str(source))
    original=_native_filled_windows(f)
    nodes=_read_window_nodes(
        edited_xml,original_state.source_sha256,
        original_state.original_native_source_catalog_sha256,
        original,
    )
    deleted=tuple(sorted(set(original)-set(nodes)))
    removed,shared,openings=_window_source_dependents(f,deleted)
    source_steps={x.id() for x in f}
    model=ifcopenshell.open(str(source))
    # Mutate only a fresh source clone. Never hold dereferenced
    # IfcOpenShell entity pointers across root.remove_product(), whose
    # native C++ entity lifetime may have ended after the removal.
    for guid in deleted:
        try:
            win=model.by_guid(guid)
        except RuntimeError as exc:
            raise NativeWindowV14Error("Source original Window disappeared before delete") from exc
        ifcopenshell.api.root.remove_product(model,product=win)
    _restore_native_shared_relation_history(model,shared,set(deleted))
    if {x.id() for x in model}-source_steps:
        raise NativeWindowV14Error("Native Win deletion generated a non-original IFC STEP node")
    if _sha(source)!=before_sha:
        raise NativeWindowV14Error("Immutable IFC source changed before candidate staging")
    with tempfile.TemporaryDirectory(
        prefix=".bibi142-native-windows-",dir=str(destination.parent)
    ) as tmp:
        stage=Path(tmp)/"candidate_metres_native.ifc"
        model.write(str(stage))
        roots_preserved,geometries_preserved=_verify_native_window_only_delete(
            source,stage,deleted,removed,shared,openings)
        if _sha(source)!=before_sha or destination.exists():
            raise NativeWindowV14Error("Original source/destination changed before atomic commit")
        # On Windows this rename fails when the destination already
        # exists, providing safer no-overwrite behavior than os.replace.
        os.rename(stage,destination)
    final=_sha(destination)
    if _sha(source)!=before_sha:
        raise NativeWindowV14Error("Immutable native source changed after staged commit")
    return WindowDeleteV14Report(
        before_sha,final,sha256(edited_xml).hexdigest(),deleted,
        tuple(sorted(o for o,h in openings.values())),
        removed,tuple(x.global_id for x in shared),
        roots_preserved,geometries_preserved,destination)
