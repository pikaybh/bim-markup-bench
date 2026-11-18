"""Independent OFFLINE native scope oracle for v0.66 Window final-state edits.

Derives either exactly one Window group deletion or one horizontal group
translation from source/candidate native IFC, never a task-specific answer,
XML command, author scorer or target GUID. Builds *independent source API*
reference state, compares fully typed STEP-label-independent IFC graph
fingerprints, original identities and actual native-world meshes.

This oracle intentionally accepts a limited native authoring strategy.
Equality to source API cleanup is NOT proof that other valid IFC encodings
are equivalent or invalid. Paper benchmark score is never inferred.
"""
from __future__ import annotations

from hashlib import sha256
from collections import Counter
from pathlib import Path
import json
import math
import time

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.unit
import ifcopenshell.util.placement
import numpy as np

from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import _schema_error_counter
from tools.bibimbap_v066_window_final_state import source, groups, _mesh_bounds
from tools.bibimbap_v066_native_semantic_admission import (
    _hash, _roots_by_guid, DEPTHS,
)

STATUS = "V066_SOURCE_NEUTRAL_WINDOW_NATIVE_MOVE_DELETE_SCOPE_PASS"
MAX_MOVE_M = 1.


class WindowScope066Error(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise WindowScope066Error(message)


def _near_box(a,b,shift=(0.,0.,0.), tol=3.e-5):
    return all(abs(a[i][j]+shift[i]-b[i][j]) < tol
               for i in range(3) for j in (0,1))


def _all_original_products(model):
    return {x.GlobalId:x for x in model.by_type("IfcProduct")}


def _clone_native_reference(original_path):
    return ifcopenshell.open(str(original_path))


def _replay_world_delta_independently(model, members, offset_world):
    """Independent oracle implementation: parent 3x3 matrix inversion."""
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    for p in members[1:]:
        placement = p.ObjectPlacement
        parent = placement.PlacementRelTo
        mat = (ifcopenshell.util.placement.get_local_placement(parent)
               if parent else np.eye(4))
        current = np.array(placement.RelativePlacement.Location.Coordinates,dtype=float)
        # IFCSOURCE millimetre, physical world displacement metre.
        native = np.linalg.inv(mat[:3,:3]).dot(
            np.array(offset_world,dtype=float)/scale)
        placement.RelativePlacement.Location.Coordinates = tuple(
            float(x) for x in current+native)


def _replay_delete_independently(model, original_group):
    """Rebuild IFC source cleanup, without reading XML or candidate edits."""
    for e in (*original_group["details"],original_group["window"],original_group["opening"]):
        ifcopenshell.api.root.remove_product(model,product=e)


def _normalize_mutable_owner_history_clock(original, expected, candidate):
    """Permit only real native API cleanup clock skew, never other metadata.

    Reference ifcopenshell.api.remove_product writes LastModifiedDate at
    process time. Compare the rest of full entity graph separately, after
    normalizing this one declared native update.
    """
    a = original.by_type("IfcOwnerHistory")
    b = expected.by_type("IfcOwnerHistory")
    c = candidate.by_type("IfcOwnerHistory")
    need(len(b)==len(c),"Native reference/candidate OwnerHistory population drifted")
    for expect_history, result_history in zip(b,c):
        expected_time = expect_history.LastModifiedDate
        actual_time = result_history.LastModifiedDate
        if expected_time == actual_time:
            continue
        now = int(time.time())
        need(type(actual_time) is int and type(expected_time) is int
             and abs(actual_time-expected_time) < 300
             and abs(actual_time-now) < 300,
             "Native API OwnerHistory LastModifiedDate timestamp unauthorized")
        expect_history.LastModifiedDate = 0
        result_history.LastModifiedDate = 0


def _native_value(value, previous):
    """IFC writer float roundtrip tolerance at 1e-6 native mm = 1nm."""
    if isinstance(value,ifcopenshell.entity_instance):
        if value.id():
            return ["reference",previous[value.id()]]
        return ["express_inline",value.is_a(),[_native_value(x,previous) for x in value]]
    if isinstance(value,(tuple,list)):
        return ["aggregate",[_native_value(x,previous) for x in value]]
    if value is None:return ["missing"]
    if isinstance(value,bool):return ["boolean",value]
    if isinstance(value,int):return ["integer",value]
    if isinstance(value,float):
        need(math.isfinite(value),"Nonfinite native IFC value")
        rounded=round(value,6)
        return ["real",f"{0. if rounded == 0 else rounded:.6f}"]
    if isinstance(value,str):return ["text_enum",value]
    raise WindowScope066Error("Unsupported native IFC value type")


# EXPRESS SET aggregates are order-insensitive; IFC ordered LIST coordinates
# and geometric paths MUST retain their order. This restricted whitelist is
# tied to known official IFC attributes, not arbitrary free-form sorting.
SET_FIELDS=frozenset({"RelatedObjects","RelatedElements","HasProperties",
                      "RelatedDefinitions"})


def _window_graph_hashes(model):
    entities=list(model)
    prev={e.id():"__REFERENCE__" for e in entities}
    stages={}
    for depth in range(max(DEPTHS)+1):
        next_labels={}
        for e in entities:
            attributes=[]
            for idx,actual in enumerate(e):
                encoded=_native_value(actual,prev)
                if e.attribute_name(idx) in SET_FIELDS and isinstance(actual,(tuple,list)):
                    encoded=["aggregate_set",sorted(encoded[1],key=lambda x:json.dumps(
                        x,sort_keys=True,separators=(",",":")))]
                attributes.append(encoded)
            next_labels[e.id()]=_hash([e.is_a(),attributes])
        if depth in DEPTHS:stages[depth]=Counter(next_labels.values())
        prev=next_labels
    return stages


def _graph_equal(expected, observed):
    ref = _window_graph_hashes(expected)
    got = _window_graph_hashes(observed)
    for depth in DEPTHS:
        need(ref[depth] == got[depth],
             f"Native IFC entire typed source/reference graph mismatch "
             f"(no STEP-ID dependence, depth {depth})")


def post_window_native_scope(original_path:Path, source_sha:str,
                             candidate_path:Path) -> dict:
    """Source-agnostic Window group scope, native IFC2X3 unsupported."""
    original_path, candidate_path = Path(original_path), Path(candidate_path)
    need(original_path.is_file() and candidate_path.is_file()
         and not original_path.is_symlink()
         and not candidate_path.is_symlink()
         and original_path.resolve()!=candidate_path.resolve()
         and len(source_sha)==64 and file_hash(original_path)==source_sha,
         "SHA-pinned original IFC and fresh separate candidate required")
    candidate_sha = file_hash(candidate_path)
    before = source(original_path,source_sha)
    candidate = ifcopenshell.open(str(candidate_path))
    need(candidate.schema_identifier == before.schema_identifier
         and abs(ifcopenshell.util.unit.calculate_unit_scale(candidate) -
                 ifcopenshell.util.unit.calculate_unit_scale(before)) < 1e-12,
         "IFC schema or native unit changed")
    original_groups = groups(before)
    old_roots = _roots_by_guid(before)
    new_roots = _roots_by_guid(candidate)
    need(not (set(new_roots) - set(old_roots)),
         "Unauthorized new IFC Root entity")
    need(all(old_roots[g].is_a() == new_roots[g].is_a()
             for g in set(old_roots) & set(new_roots)),
         "Original IFC Root class was substituted")
    source_products = _all_original_products(before)
    final_products = _all_original_products(candidate)

    old_win = set(original_groups)
    new_win = {w.GlobalId for w in candidate.by_type("IfcWindow")}
    deleted = old_win-new_win
    created = new_win-old_win
    need(not created and len(deleted)<=1,
         "Only one already existing Window may be deleted; no new Window")
    if deleted:
        kind = "delete"
        chosen = next(iter(deleted))
        source_group = original_groups[chosen]
        expected = _clone_native_reference(original_path)
        _replay_delete_independently(expected,groups(expected)[chosen])
        expected_roots = _roots_by_guid(expected)
        need(set(expected_roots)==set(new_roots)
             and all(expected_roots[x].is_a()==new_roots[x].is_a()
                     for x in expected_roots),
             "Native Window/detail/Opening cascade deleted wrong Roots")
        expected_products = _all_original_products(expected)
        need(set(expected_products)==set(final_products),
             "Native Window cascade left/removed wrong original products")
        _normalize_mutable_owner_history_clock(before,expected,candidate)
        _graph_equal(expected,candidate)
        for g,p in expected_products.items():
            cp = final_products[g]
            if p.Representation is not None:
                need(cp.Representation is not None
                     and _near_box(_mesh_bounds(p),_mesh_bounds(cp)),
                     "Native deleted-assembly remaining physical product changed")
        offset = (0.,0.,0.)
        survivor = len(expected_products)
    else:
        kind = "move"
        need(len(new_roots)==len(old_roots)
             and set(new_roots)==set(old_roots)
             and set(final_products)==set(source_products),
             "Move must preserve entire source Root + product roster")
        moved = []
        for guid,grp in original_groups.items():
            prior = _mesh_bounds(grp["window"])
            after = _mesh_bounds(final_products[guid])
            offset = tuple(round(after[k][0]-prior[k][0],6) for k in range(3))
            if any(abs(x)>3.e-5 for x in offset):
                moved.append((guid,offset))
        need(len(moved)==1,
             "Exactly one original Window assembly must physically move")
        chosen, offset = moved[0]
        source_group = original_groups[chosen]
        need(abs(offset[2])<3.e-5
             and .01 <= math.hypot(offset[0],offset[1]) <= MAX_MOVE_M
             and all(math.isfinite(v) for v in offset),
             "Nonzero bounded horizontal hosted Window translation required")
        members={p.GlobalId for p in source_group["members"]}
        for guid,old in source_products.items():
            now = final_products[guid]
            need(now.is_a() == old.is_a()
                 and (now.Representation is None) == (old.Representation is None),
                 "Native original product class or representedness changed")
            if old.Representation is None:
                continue
            # Host Wall's physical cut moves, but its overall exterior
            # bounding box and source semantic representation still match
            # the reference when checked against replay.
            desired = offset if guid in members else (0.,0.,0.)
            need(_near_box(_mesh_bounds(old),_mesh_bounds(now),desired),
                 "Window, Opening, detail or untouched original world geometry invalid")
        expected = _clone_native_reference(original_path)
        _replay_world_delta_independently(
            expected, groups(expected)[chosen]["members"],offset)
        _graph_equal(expected,candidate)
        for prod in expected.by_type("IfcProduct"):
            if prod.Representation is not None:
                need(_near_box(_mesh_bounds(prod),
                               _mesh_bounds(final_products[prod.GlobalId])),
                     "Native replayed physical geometry does not equal candidate")
        survivor = len(source_products)

    new_errors = _schema_error_counter(candidate_path)-_schema_error_counter(original_path)
    need(not new_errors, "New original IFC schema validation violations")
    need(file_hash(original_path)==source_sha and
         file_hash(candidate_path)==candidate_sha,
         "Source/native candidate edited mid-verification")
    digest_payload={
        "source":source_sha,"kind":kind,"chosen_source_window_guid":chosen,
        "offset_m":[round(x,5) for x in offset],
        "surviving_products":survivor,
        "total_window_groups":len(original_groups),
    }
    return {
        "status": STATUS,
        "kind":kind,
        "original_source_schema":before.schema_identifier,
        "native_step_id_invariants_required":False,
        "all_original_source_untouched_products_physically_preserved":True,
        "source_native_root_classes_and_relationships_checked":True,
        "native_full_reference_graph_step_number_independent":True,
        "chosen_assembly_member_count":len(source_group["members"]),
        "deleted_or_moved_window_groups":1,
        "physical_offset_world_m":[round(x,5) for x in offset],
        "semantic_edit_digest":sha256(json.dumps(
            digest_payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "source_correctness_against_original_public_question":None,
        "original_author_or_official_paper_scorer_used":False,
        "source_ifc_sha256":source_sha,
        "candidate_ifc_sha256":candidate_sha,
        "new_schema_findings":0,
    }
