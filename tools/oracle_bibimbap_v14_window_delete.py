"""Independent IFC-only native Window deletion oracle for v0.14.

No imports from v0.14 writer, v0.13 source catalog, old runtime projection,
original BIBIMBAP author scorer, hidden target or model. Independently
check exact source-owned dependency roots, explicit native IFC relationships,
unmodified other IFC roots/STEP and all remaining world-space physical
products. Retained host IfcWall and original IfcOpeningElement/IfcRelVoids
must remain physically identical: this edit removes the filling ONLY.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import numpy as np


class OriginalNativeWindowOracleError(ValueError):
    pass


def _sha(path:Path):
    return sha256(path.read_bytes()).hexdigest()


def _world_mesh(product):
    if product.Representation is None:
        return None
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        mesh=ifcopenshell.geom.create_shape(settings,product)
        vertices=np.asarray(mesh.geometry.verts,dtype=float).reshape(-1,3)
        triangles=np.asarray(mesh.geometry.faces,dtype=np.int64).reshape(-1,3)
        volume=float(ifcopenshell.util.shape.get_volume(mesh.geometry))
    except Exception as exc:
        raise OriginalNativeWindowOracleError(
            "Unverifiable actual original IFC product world geometry"
        ) from exc
    if (len(vertices)<4 or len(triangles)<4 or
        not np.all(np.isfinite(vertices)) or not np.isfinite(volume)):
        raise OriginalNativeWindowOracleError("Original native world mesh degenerate")
    quantized=np.rint(vertices*1e6).astype(np.int64)
    return (
        len(vertices),len(triangles),
        tuple(sorted(Counter(map(tuple,quantized)).items())),
        round(volume,7),
    )


def _preexisting_exclusive_roots(model,guids:tuple[str,...]):
    """Recompute original own/dependant Root closure independently."""
    removed=set()
    source_openings={}
    affected_membership={}
    for target in guids:
        try:
            win=model.by_guid(target)
        except RuntimeError as exc:
            raise OriginalNativeWindowOracleError("Original requested Window GUID absent") from exc
        if not win.is_a("IfcWindow"):
            raise OriginalNativeWindowOracleError("Requested native IFC product not a Window")
        inverses=list(model.get_inverse(win))
        counts=Counter(x.is_a() for x in inverses)
        expected={
            "IfcRelDefinesByProperties":2,"IfcRelAssociatesMaterial":1,
            "IfcRelAssociatesClassification":1,"IfcRelDefinesByType":1,
            "IfcRelFillsElement":1,"IfcRelContainedInSpatialStructure":1,
        }
        if counts!=expected:
            raise OriginalNativeWindowOracleError("Original native source Window dependency pattern changed")
        win_deps={win.GlobalId}
        fills=[x for x in inverses if x.is_a("IfcRelFillsElement")]
        if len(fills)!=1:
            raise OriginalNativeWindowOracleError("Original Window filling relation missing")
        fill=fills[0]
        opening=fill.RelatingOpeningElement
        if (fill.RelatedBuildingElement!=win or
            not opening.is_a("IfcOpeningElement") or
            len(opening.VoidsElements)!=1 or
            len(opening.HasFillings)!=1 or
            opening.HasFillings[0]!=fill):
            raise OriginalNativeWindowOracleError("Original source Opening/filling relationship invalid")
        host=opening.VoidsElements[0].RelatingBuildingElement
        if not host.is_a("IfcWall"):
            raise OriginalNativeWindowOracleError("Expected actual native source IfcWall host")
        source_openings[target]=(opening.GlobalId,host.GlobalId,
                                 fill.GlobalId,
                                 opening.VoidsElements[0].GlobalId)
        win_deps.add(fill.GlobalId)
        for rel in inverses:
            kind=rel.is_a()
            if kind=="IfcRelAssociatesMaterial":
                if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0]!=win:
                    raise OriginalNativeWindowOracleError("Original Window material relationship shared")
                win_deps.add(rel.GlobalId)
            elif kind=="IfcRelDefinesByProperties":
                if len(rel.RelatedObjects)!=1 or rel.RelatedObjects[0]!=win:
                    raise OriginalNativeWindowOracleError("Window PropertySet relation unexpectedly shared")
                pset=rel.RelatingPropertyDefinition
                if (pset is None or not pset.is_a("IfcPropertySet")
                    or set(model.get_inverse(pset))!={rel}):
                    raise OriginalNativeWindowOracleError("Window PropertySet has nonexclusive native ownership")
                win_deps.add(rel.GlobalId)
                win_deps.add(pset.GlobalId)
            elif kind in ("IfcRelDefinesByType","IfcRelAssociatesClassification",
                          "IfcRelContainedInSpatialStructure"):
                attr=("RelatedElements" if kind=="IfcRelContainedInSpatialStructure"
                      else "RelatedObjects")
                if target not in [x.GlobalId for x in getattr(rel,attr)]:
                    raise OriginalNativeWindowOracleError("Original Window missing shared membership")
                if rel.GlobalId not in affected_membership:
                    affected_membership[rel.GlobalId]=(
                        kind,attr,
                        tuple(x.GlobalId for x in getattr(rel,attr)),
                    )
        if len(win_deps)!=7 or removed&win_deps:
            raise OriginalNativeWindowOracleError("Original exclusive native Window dependency roots not unique")
        removed|=win_deps
    for rel,(cls,attr,members) in affected_membership.items():
        if not set(members)-set(guids):
            raise OriginalNativeWindowOracleError("Original native shared classification/type/storey would become empty")
    return removed,source_openings,affected_membership


def verify_source_native_window_delete(
    source:Path,candidate:Path,
    deleted_original_window_guids:tuple[str,...],
    *,expected_original_source_sha256:str|None=None,
    expected_output_sha256:str|None=None,
)->dict:
    if (not source.is_file() or source.is_symlink() or
        not candidate.is_file() or candidate.is_symlink()
        or source.resolve()==candidate.resolve()):
        raise OriginalNativeWindowOracleError("Original IFC source/candidate file paths must exist and differ")
    original_sha=_sha(source)
    if expected_original_source_sha256 and original_sha!=expected_original_source_sha256:
        raise OriginalNativeWindowOracleError("Original native IFC source hash mismatch")
    result_sha=_sha(candidate)
    if expected_output_sha256 and result_sha!=expected_output_sha256:
        raise OriginalNativeWindowOracleError("Result native IFC candidate hash mismatch")
    original=ifcopenshell.open(str(source))
    edited=ifcopenshell.open(str(candidate))
    if (original.schema!="IFC4X3" or edited.schema!=original.schema or
        abs(ifcopenshell.util.unit.calculate_unit_scale(original)-1)>1e-8 or
        abs(ifcopenshell.util.unit.calculate_unit_scale(edited)-1)>1e-8):
        raise OriginalNativeWindowOracleError("IFC4X3 native metre schema changed")
    deleted=tuple(sorted(deleted_original_window_guids))
    if (not deleted or len(deleted)>8 or len(set(deleted))!=len(deleted)):
        raise OriginalNativeWindowOracleError("Expected unique 1..8 original Window delete targets")
    old_root={x.GlobalId:x for x in original.by_type("IfcRoot")}
    new_root={x.GlobalId:x for x in edited.by_type("IfcRoot")}
    removed_expected,hosts,shared=_preexisting_exclusive_roots(original,deleted)
    if (set(old_root)-set(new_root)!=removed_expected
        or set(new_root)-set(old_root)):
        raise OriginalNativeWindowOracleError(
            "Unexpected original IFC Root deleted/added beyond target-owned closure"
        )
    for guid in sorted(set(old_root)&set(new_root)):
        a=old_root[guid];b=new_root[guid]
        if a.is_a()!=b.is_a():
            raise OriginalNativeWindowOracleError("Retained native source IFC Root class changed")
        if guid not in shared:
            if str(a)!=str(b):
                raise OriginalNativeWindowOracleError("Unrelated original native IFC Root changed")
        else:
            cls,attr,members=shared[guid]
            desired=tuple(x for x in members if x not in deleted)
            actual=tuple(x.GlobalId for x in getattr(b,attr))
            if b.is_a()!=cls or actual!=desired:
                raise OriginalNativeWindowOracleError("Native source shared membership not exact")
            for i in range(len(a)):
                name=a.attribute_name(i)
                if name==attr:
                    continue
                if str(a[i])!=str(b[i]):
                    raise OriginalNativeWindowOracleError(
                        "Original shared relation metadata/history/source identity changed"
                    )
    origprod={x.GlobalId:x for x in original.by_type("IfcProduct")}
    postprod={x.GlobalId:x for x in edited.by_type("IfcProduct")}
    if (set(origprod)-set(postprod)!=set(deleted)
        or set(postprod)-set(origprod)):
        raise OriginalNativeWindowOracleError("Native IFC product inventory modified beyond selected Windows")
    for window,(opening,host,fill,void) in hosts.items():
        if opening not in new_root or host not in new_root:
            raise OriginalNativeWindowOracleError("Original host Wall or original void Opening was deleted")
        op=new_root[opening]
        if (len(op.VoidsElements)!=1
            or op.VoidsElements[0].GlobalId!=void
            or op.VoidsElements[0].RelatingBuildingElement.GlobalId!=host
            or len(op.HasFillings)!=0):
            raise OriginalNativeWindowOracleError(
                "Original host Wall Opening was closed or still contains deleted Window"
            )
        if fill in new_root:
            raise OriginalNativeWindowOracleError("Original deleted window IfcRelFillsElement remains")
    preserved_mesh=0
    for guid in sorted(set(origprod)&set(postprod)):
        if _world_mesh(origprod[guid])!=_world_mesh(postprod[guid]):
            raise OriginalNativeWindowOracleError("Original non-target physical Product world geometry changed")
        if origprod[guid].Representation is not None:
            preserved_mesh+=1
    if {x.id() for x in edited}-{x.id() for x in original}:
        raise OriginalNativeWindowOracleError("New native STEP entity/OwnerHistory timestamp inserted")
    if _sha(source)!=original_sha or _sha(candidate)!=result_sha:
        raise OriginalNativeWindowOracleError("Native IFC source/candidate mutated during independent oracle")
    return {
        "status":"INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014",
        "original_source_sha256":original_sha,
        "candidate_native_sha256":result_sha,
        "original_requested_windows_removed":list(deleted),
        "independently_expected_deleted_owned_root_guids":sorted(removed_expected),
        "independently_original_source_openings_retained":
            sorted(x[0] for x in hosts.values()),
        "independently_original_host_wall_guids_preserved":
            sorted(set(x[1] for x in hosts.values())),
        "independently_source_shared_membership_relation_guids":
            sorted(shared),
        "non_target_original_root_count_preserved":
            len(set(old_root)&set(new_root)),
        "actual_world_native_product_meshes_preserved":preserved_mesh,
        "source_original_ifc_schema_and_units_retained":True,
        "original_IfcRelVoids_and_Window_fill_semantics_preserved":True,
        "original_host_wall_opening_unchanged":True,
        "candidate_independent_native_scene_proof_not_original_author_grade":True,
        "original_author_scorer_not_invoked":True,
        "hidden_ground_truth_not_used":True,
        "full_original45_semantic_edit_equivalence_proven":False,
        "model_calls":0,
    }
