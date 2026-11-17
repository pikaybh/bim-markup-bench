"""v0.51 independent ORIGINAL IFC source/candidate validator for executed Python.

No XML edit plan, D-state compiler, original benchmark scorer or private GT.
This oracle derives the *actual native IFC changed GUID set* by comparing source
and candidate physical geometry. It shares only low-level IFC/mesh primitives
with the previously independently authored v0.45 validator, not typed commands.
A valid IFC edit need not solve the original public task.
"""
from __future__ import annotations

from collections import Counter
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit

from tools.bibimbap_matched25_tools import file_hash
from src.runtime.experimental_v44_original_native_step_readonly import (
    PINS, check_original_native_readonly_source,
)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    _mesh, _root_snapshots, _relation_refs, _safe_delete_roots,
    _body_solid, _close,
)


class IndependentNativePython051Error(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise IndependentNativePython051Error(reason)


def _protected_native_details(model) -> dict[str, tuple]:
    """Check source non-physical IFC metadata without changing candidate state.

    For original four sources, property/material/unit objects are not managed
    edit surfaces in either research arm. Compare their actual native STEP
    content keyed by *original* STEP identity, including values/references.
    """
    types = (
        "IfcPropertySingleValue", "IfcPropertySet",
        "IfcMaterial", "IfcMaterialLayer", "IfcMaterialLayerSet",
        "IfcMaterialConstituent", "IfcSIUnit", "IfcUnitAssignment",
        "IfcGeometricRepresentationContext",
    )
    result = {}
    for type_name in types:
        for entity in model.by_type(type_name):
            result[f"{entity.id()}:{entity.is_a()}"] = str(entity)
    return result


def _bbox_changed(before, after) -> bool:
    return (before["vertex_counter"] != after["vertex_counter"]
            or before["triangles"] != after["triangles"])


def verify_independent_native_python_v051(
    source: Path, candidate: Path, *,
    source_sha: str, task_id: str,
) -> dict:
    """Independently accept *native* bounded mutations without any XML plan.

    No model-private correct-answer GUIDs/target values/positive fixtures.
    This is native edit authority verification, not public task correctness.
    """
    source, candidate = Path(source), Path(candidate)
    need(source.is_file() and candidate.is_file()
         and not source.is_symlink() and not candidate.is_symlink()
         and source.resolve() != candidate.resolve()
         and candidate.stat().st_size < 20_000_000
         and source_sha in PINS and PINS[source_sha][0] == task_id
         and file_hash(source) == source_sha,
         "Original source SHA/task/path or candidate native IFC invalid")
    # Reject clearly non-STEP bytes before IfcOpenShell allocates an invalid
    # partial native handle (some versions warn from its destructor).
    with candidate.open("rb") as fd:
        prefix = fd.read(64)
        fd.seek(max(0, candidate.stat().st_size - 128))
        suffix = fd.read()
    need(prefix.startswith(b"ISO-10303-21;")
         and b"END-ISO-10303-21;" in suffix,
         "Native candidate must contain complete IFC STEP envelope")
    original = ifcopenshell.open(str(source))
    need(check_original_native_readonly_source(source, source_sha, original)
         == task_id, "Original exact native source inventory changed")
    modified = ifcopenshell.open(str(candidate))
    for f in (original, modified):
        need(f.schema == "IFC4X3"
             and abs(ifcopenshell.util.unit.calculate_unit_scale(f) - .001) < 1e-12,
             "Original and output IFC must retain native IFC4X3/mm units")
    need(file_hash(source) == source_sha,
         "Original public source IFC changed during oracle read")

    source_ids = {r.GlobalId: r for r in original.by_type("IfcRoot")}
    target_ids = {r.GlobalId: r for r in modified.by_type("IfcRoot")}
    need(not (set(target_ids) - set(source_ids)),
         "Native Python candidate invented new IFC Root GUIDs/relationships")
    missing_roots = set(source_ids) - set(target_ids)
    before_roots, after_roots = _root_snapshots(original), _root_snapshots(modified)
    for guid in after_roots:
        need(before_roots[guid] == after_roots[guid],
             "Surviving original native Root type/name/description changed")

    original_products = {p.GlobalId: p for p in original.by_type("IfcProduct")}
    result_products = {p.GlobalId: p for p in modified.by_type("IfcProduct")}
    missing_products = set(original_products) - set(result_products)
    need(not (set(result_products) - set(original_products)),
         "Candidate introduced out-of-scope native physical product")
    need(all(original_products[g].is_a("IfcColumn") for g in missing_products),
         "Candidate deleted non-Column original physical product")
    if task_id == "topological_test_17":
        need(1 <= len(missing_products) <= 9,
             "Original ten-Column deletion requires 1..9 actual missing columns")
        need(missing_roots.issubset(_safe_delete_roots(original, missing_products)),
             "Deleted Column changed unrelated original source roots or metadata")
    else:
        need(not missing_roots and not missing_products,
             "UPDATE cannot delete any original source IFC element/root")

    source_rels = {r.GlobalId: r for r in original.by_type("IfcRelationship")}
    result_rels = {r.GlobalId: r for r in modified.by_type("IfcRelationship")}
    need(not (set(result_rels) - set(source_rels)),
         "Native candidate introduced unrelated original IFC relationships")
    for guid, rel in result_rels.items():
        prior = _relation_refs(source_rels[guid])
        after = _relation_refs(rel)
        if missing_products:
            allowed_after = tuple(p for p in prior if not (
                isinstance(p[1], str) and p[1] in missing_products
            ))
            need(allowed_after == after,
                 "Native candidate modified kept original relationship endpoints/roles")
        else:
            need(prior == after, "Original IFC relationship endpoints changed")

    # Inspect ALL native physical elements, not just a task's desired targets.
    src_elems = {p.GlobalId: p for p in original.by_type("IfcElement")}
    dst_elems = {p.GlobalId: p for p in modified.by_type("IfcElement")}
    need(set(dst_elems) == set(src_elems) - missing_products,
         "Native candidate added/removed other original physical element classes")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    source_meshes = {g: _mesh(e, settings) for g, e in src_elems.items()}
    target_meshes = {g: _mesh(e, settings) for g, e in dst_elems.items()}
    need(all(s is not None for s in source_meshes.values())
         and all(s is not None for s in target_meshes.values()),
         "Unrenderable native IFC source or edited element")

    changes = {g for g in target_meshes
               if _bbox_changed(source_meshes[g], target_meshes[g])}
    if task_id == "geometry_test_14":
        slabs = original.by_type("IfcSlab")
        need(len(slabs) == 1 and changes == {slabs[0].GlobalId}
             and not missing_products, "Exactly one source-native Slab must change")
        g = slabs[0].GlobalId
        prev = _body_solid(original_products[g], mapped=False)
        nxt = _body_solid(result_products[g], mapped=False)
        old = (float(prev.SweptArea.XDim)/1000,
               float(prev.SweptArea.YDim)/1000)
        new = (float(nxt.SweptArea.XDim)/1000,
               float(nxt.SweptArea.YDim)/1000)
        need(sum(abs(a-b)>1e-6 for a,b in zip(old,new)) == 1
             and all(a >= b-1e-6 for a,b in zip(new,old))
             and .1 <= min(new) <= max(new) <= 25
             and _close(prev.Depth, nxt.Depth),
             "Original slab must increase one source rectangle dimension only")
        a, b = source_meshes[g]["bbox"], target_meshes[g]["bbox"]
        need(all(_close(sum(a[i]),sum(b[i])) for i in range(3))
             and _close(a[2][1]-a[2][0], b[2][1]-b[2][0]),
             "Slab native centre/Z or original thickness changed")
    elif task_id == "geometry_test_15":
        cols = {c.GlobalId for c in original.by_type("IfcColumn")}
        need(len(cols) == 4 and len(changes) == 1
             and changes.issubset(cols) and not missing_products,
             "Exactly one original native Column must move")
        g = next(iter(changes))
        p, q = original_products[g].ObjectPlacement, result_products[g].ObjectPlacement
        need(p is not None and q is not None
             and p.is_a("IfcLocalPlacement") and q.is_a("IfcLocalPlacement")
             and ((p.PlacementRelTo is None and q.PlacementRelTo is None)
                  or (p.PlacementRelTo is not None and q.PlacementRelTo is not None
                      and p.PlacementRelTo.id() == q.PlacementRelTo.id())),
             "Original native column parent placement changed")
        before = ifcopenshell.util.placement.get_local_placement(p)
        after = ifcopenshell.util.placement.get_local_placement(q)
        need(all(_close(before[i,j], after[i,j], 1e-8)
                 for i in range(4) for j in range(4)
                 if (i,j) not in ((0,3), (1,3))),
             "Moved column changed original Z or orientation")
        dx = (after[0,3]-before[0,3])/1000
        dy = (after[1,3]-before[1,3])/1000
        need(abs(dx)+abs(dy) > 1e-6 and
             all(abs(after[i,3]/1000) <= 40 for i in (0,1)),
             "Column world XY did not change or exceeds bounded source")
        old = source_meshes[g]["positions"]
        projected = Counter((round(v[0]+dx,6),
                             round(v[1]+dy,6),v[2]) for v in old)
        need(target_meshes[g]["vertex_counter"] == projected
             and _close(_body_solid(original_products[g],True).Depth,
                        _body_solid(result_products[g],True).Depth),
             "Native Column physical motion not exact XY translation")
    elif task_id == "topological_test_11":
        cols = {c.GlobalId for c in original.by_type("IfcColumn")}
        need(len(cols) == 2 and changes == cols and not missing_products,
             "Both source shared-mapped Columns must change height")
        old_cols = [_body_solid(original_products[g],True) for g in sorted(cols)]
        new_cols = [_body_solid(result_products[g],True) for g in sorted(cols)]
        need(old_cols[0].id() == old_cols[1].id()
             and new_cols[0].id() == new_cols[1].id(),
             "Source mapped Column shared body must remain shared")
        old_depth = float(old_cols[0].Depth)/1000
        new_depth = float(new_cols[0].Depth)/1000
        need(.2 <= new_depth <= 10
             and abs(new_depth-old_depth) > 1e-6,
             "Shared source-native Column height must change within bounds")
        for g in cols:
            old = source_meshes[g]["bbox"]
            new = target_meshes[g]["bbox"]
            need(all(_close(old[i][j],new[i][j])
                     for i in (0,1) for j in (0,1))
                 and _close(old[2][0],new[2][0])
                 and _close(new[2][1]-new[2][0],new_depth),
                 "Column native top/bottom or X/Y changed outside shared depth")
    elif task_id == "topological_test_17":
        need(not changes and len(original.by_type("IfcColumn")) == 10,
             "Deleting original columns cannot alter surviving native geometry")
        need({g for g in src_elems if g not in dst_elems} == missing_products,
             "All deleted physical elements must be original source Columns")
    else:
        raise IndependentNativePython051Error("Non-original-four source task")

    untouched = set(src_elems) - changes - missing_products
    need(all(source_meshes[g]["vertex_counter"] ==
             target_meshes[g]["vertex_counter"] and
             source_meshes[g]["triangles"] == target_meshes[g]["triangles"]
             for g in untouched),
         "Non-target original IFC physical geometry changed")

    # For all original source-native files, material, unit and direct property
    # values are outside *both* research arms' managed rights. A source-only
    # original pset may be deleted with a deleted object; check surviving values.
    old_protected = _protected_native_details(original)
    new_protected = _protected_native_details(modified)
    for key, val in new_protected.items():
        need(key in old_protected and val == old_protected[key],
             "Candidate changed original non-target units/properties/materials")
    if not missing_products:
        need(new_protected == old_protected,
             "UPDATE removed original non-target material/property/unit entity")
    need(file_hash(source) == source_sha,
         "Original IFC source changed during native Python independent evaluation")
    return {
        "status": "V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS",
        "task_id": task_id,
        "source_sha256": source_sha,
        "candidate_sha256": file_hash(candidate),
        "changed_guid_count": len(changes),
        "deleted_original_column_count": len(missing_products),
        "original_source_unchanged": True,
        "non_target_native_geometry_unchanged": True,
        "original_native_relationships_preserved_except_deleted_reference": True,
        "original_native_property_material_units_preserved": True,
        "author_scorer_called": False,
        "original_public_task_success_claimed": False,
    }
