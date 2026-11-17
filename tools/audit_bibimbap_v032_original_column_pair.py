"""Actual original-public BIBIMBAP test_04 D0/I0 developer native Create pair.

Execution order is deliberate: pinned original question + original IFC, independent
imperative Python I0, independent native oracle (before any declarative D0 or
original scorer import), declarative whole-XML D0, independent native pair
oracle, and ONLY THEN unchanged original author grader for both.

Neither LLM inference nor a claimed original45 causal performance sample.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v032_original_column_i0 import (
    SPEC_METRES, SOURCE_SHA, create_independent_public_column_i0,
)

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "https://github.com/pikaybh/bim-markup-bench/issues/179"
TASK = "test_04"
QUESTION_SHA = "bdc610efa790a67c601a0c3d9056c47c702a7af9bcb05d3b8e3acb3d9771ce57"
FROZEN_GATE = (
    "reports/bibimbap_v031_original45_eligibility_and_overlap_20261117.json",
    "d6680b3eadb5733be547c09ab8deed58dd48c7feaccbc3cb562b6e60b475c7dd",
)
HISTORICAL_D0 = "reports/bibimbap_test04_column_v2_developer_d0_20261113.json"
HISTORICAL_D0_SHA = "d55ffa4945c74e30e5b2143021f9cc07ea621c7f0b3e1d3316a0bbada6e6a870"
XML_COLUMN_ID = "bibi118_preregistered_fixed_d0_column"
EXPECTED_METRIC_BBOX = (12., 8., 0., 12.3, 8.3, 3.)


class OriginalColumnV032Blocked(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise OriginalColumnV032Blocked(reason)


def native_original_product_geometry(model: ifcopenshell.file) -> dict:
    """Independent world-coordinate native geometry snapshot of source products."""
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    snapshots = {}
    for obj in model.by_type("IfcProduct"):
        guid = obj.GlobalId
        require(type(guid) is str and guid not in snapshots,
                "Missing/duplicated original source IFC product GUID")
        has_native_rep = obj.Representation is not None
        if not has_native_rep:
            snapshots[guid] = (obj.is_a(), False, None)
            continue
        try:
            mesh = ifcopenshell.geom.create_shape(settings, obj)
        except Exception as exc:
            # Fail closed: cannot claim full original product geometry preservation.
            raise OriginalColumnV032Blocked(
                f"Independent native source product geometry unavailable: {obj.is_a()}"
            ) from exc
        pts = np.asarray(mesh.geometry.verts, dtype=float)
        require(pts.size >= 9 and pts.size % 3 == 0 and np.isfinite(pts).all(),
                "Existing native IFC source geometry invalid")
        three = pts.reshape(-1, 3)
        bounds = tuple(float(x) for x in (*three.min(axis=0), *three.max(axis=0)))
        snapshots[guid] = (obj.is_a(), True, bounds)
    return snapshots


def verified_original_native_create(
    original_mm: Path, candidate_mm: Path, *, known_new_column_guid: str | None = None
) -> dict:
    """Neither writer helper nor scorer imported; source and candidate actual IFC."""
    original = ifcopenshell.open(str(original_mm))
    candidate = ifcopenshell.open(str(candidate_mm))
    require(original.schema == candidate.schema == "IFC4X3",
            "Original IFC4X3 schema was not retained")
    require(abs(ifcopenshell.util.unit.calculate_unit_scale(original)-.001) < 1e-12
            and abs(ifcopenshell.util.unit.calculate_unit_scale(candidate)-.001) < 1e-12,
            "Original native millimetre units not preserved")
    a_roots = {o.GlobalId: o for o in original.by_type("IfcRoot")}
    b_roots = {o.GlobalId: o for o in candidate.by_type("IfcRoot")}
    require(len(a_roots) == len(original.by_type("IfcRoot"))
            and len(b_roots) == len(candidate.by_type("IfcRoot"))
            and set(a_roots).issubset(b_roots),
            "Original native IFC Root identities lost/duplicated")
    for g, entity in a_roots.items():
        newer = b_roots[g]
        require(entity.is_a() == newer.is_a()
                and entity.Name == newer.Name
                and entity.Description == newer.Description,
                "Native existing IFC Root class/name/description changed")
    old_products = {o.GlobalId: o for o in original.by_type("IfcProduct")}
    new_products = {o.GlobalId: o for o in candidate.by_type("IfcProduct")}
    require(set(old_products) <= set(new_products)
            and len(new_products) == len(old_products) + 1,
            "Native result adds non-Column product or deletes original product")
    added = set(new_products) - set(old_products)
    require(len(added) == 1, "Exactly one native IFC product must be created")
    new_guid = next(iter(added))
    if known_new_column_guid is not None:
        require(new_guid == known_new_column_guid,
                "Declared independent writer-created Column does not match actual IFC")
    created = new_products[new_guid]
    require(created.is_a("IfcColumn"), "Original public IFC creation not a physical Column")
    extra_roots = set(b_roots) - set(a_roots)
    require(new_guid in extra_roots
            and all(g == new_guid or b_roots[g].is_a("IfcRelContainedInSpatialStructure")
                    for g in extra_roots),
            "Unallowed extra native root classes introduced")
    storey = ifcopenshell.util.element.get_container(created)
    require(storey is not None and storey.is_a("IfcBuildingStorey")
            and storey.Name == "L1" and abs(float(storey.Elevation)) < 1e-8
            and storey.GlobalId in a_roots,
            "Column not contained in original zero-elevation native storey")
    require(created.Representation is not None, "Created Column lacks a native representation")
    solids = [o for rep in created.Representation.Representations
              for o in rep.Items if o.is_a("IfcExtrudedAreaSolid")]
    require(len(solids) == 1 and math.isclose(float(solids[0].Depth), 3000.,
            abs_tol=1e-4, rel_tol=0),
            "Native original mm IFC rectangular solid depth must be 3000 mm")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    mesh = ifcopenshell.geom.create_shape(settings, created)
    points = np.asarray(mesh.geometry.verts, dtype=float).reshape(-1, 3)
    require(points.shape[0] >= 3 and np.isfinite(points).all(),
            "Column has no valid native mesh")
    bbox = tuple(float(x) for x in (*points.min(axis=0), *points.max(axis=0)))
    require(all(math.isclose(x, y, abs_tol=1e-5, rel_tol=0)
                for x, y in zip(bbox, EXPECTED_METRIC_BBOX)),
            "Native created Column world coordinates/dimensions differ from public task")
    old_geom = native_original_product_geometry(original)
    new_geom = native_original_product_geometry(candidate)
    for guid, (native_type, has_rep, old_bounds) in old_geom.items():
        updated_type, updated_rep, updated_bounds = new_geom[guid]
        require((native_type, has_rep) == (updated_type, updated_rep),
                "Existing original native product class or representation status altered")
        if old_bounds is not None:
            require(all(math.isclose(v, w, rel_tol=0, abs_tol=1e-5)
                        for v, w in zip(old_bounds, updated_bounds)),
                    "Existing native original IFC product world geometry changed")
    return {
        "status": "INDEPENDENT_NATIVE_ORIGINAL_CREATE_COLUMN_AND_SOURCE_PRESERVATION_PASS",
        "original_source_native_root_count": len(a_roots),
        "original_source_native_product_count": len(old_products),
        "original_source_product_geometry_verified_count": sum(
            x[1] for x in old_geom.values()),
        "original_source_product_without_geometry_count": sum(
            not x[1] for x in old_geom.values()),
        "original_root_guids_classes_names_descriptions_preserved": True,
        "all_original_product_geometry_preserved": True,
        "one_and_only_one_created_physical_IfcColumn": True,
        "new_root_type_only_Column_and_optional_spatial_containment": True,
        "new_column_contained_in_original_L1_storey": True,
        "new_native_column_world_bbox_m": list(bbox),
        "new_native_column_swept_solid_depth_mm": float(solids[0].Depth),
    }


def create_declarative_D0_after_independent_I0(original_mm: Path,
                                               candidate_mm: Path) -> dict:
    """Complete state XML direct edit; uses frozen v0.2 trusted compiler unchanged."""
    from src.runtime.ifc_projection import project_ifc
    from src.runtime.experimental_v2_column import compile_declarative_xml_v2

    original = ifcopenshell.open(str(original_mm))
    metric = ifcopenshell.util.unit.convert_file_length_units(original, "METER")
    with TemporaryDirectory(prefix="bmb-v032-d0-metric-") as td:
        root = Path(td)
        native_metric_source = root / "input_m.ifc"
        metric.write(str(native_metric_source))
        snapshot = project_ifc(native_metric_source)
        whole = etree.fromstring(snapshot.xml)
        namespace = etree.QName(whole).namespace
        levels = whole.find("{" + namespace + "}Levels")
        editable_storeys = [v for v in levels if v.get("elevation") == "0"]
        require(len(editable_storeys) == 1,
                "Original native L1 zero-elevation source missing/ambiguous in full XML")
        elements = whole.find("{" + namespace + "}Elements")
        require(elements is not None and not any(x.get("id") == XML_COLUMN_ID for x in elements),
                "Original declarative Column test identifier already exists")
        x, y, z, width, depth, height = SPEC_METRES
        attrs = {
            "id": XML_COLUMN_ID,
            "level": editable_storeys[0].get("id"),
            "x": str(x), "y": str(y), "z": str(z),
            "width": str(width), "depth": str(depth), "height": str(height),
        }
        etree.SubElement(elements, "{" + namespace + "}Column", attrib=attrs)
        edited = etree.tostring(whole, encoding="utf8")
        require(edited != snapshot.xml, "No declarative XML source change")
        candidate_m = root / "candidate_m.ifc"
        generated = compile_declarative_xml_v2(
            native_metric_source, edited, candidate_m)
        require([x.operation for x in generated.operations] == ["CREATE_COLUMN"],
                "Trusted D0 compiler did not infer exactly one Column creation")
        mm = ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(candidate_m)), "MILLIMETER")
        mm.write(str(candidate_mm))
        return {
            "status": generated.as_dict()["status"],
            "complete_declarative_XML_one_added_Column_no_mutator_opcode": True,
            "trusted_d0_operation": generated.operations[0].operation,
            "trusted_d0_new_native_Column_guid": generated.operations[0].ifc_guid,
            "edited_declarative_XML_sha256": sha256(edited).hexdigest(),
            "output_original_mm_IFC_sha256": file_hash(candidate_mm),
            "D0_uses_older_separately_scoped_column_v02_compiler": True,
        }


def pair_public_test04(root: Path, author: Path, data: Path) -> dict:
    require(_head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
            "Pinned author/data Git commits changed")
    require(file_hash(root / FROZEN_GATE[0]) == FROZEN_GATE[1],
            "v0.31 frozen report hash mismatch")
    gate = json.loads((root / FROZEN_GATE[0]).read_text(encoding="utf8"))
    row = [r for r in gate["rows"] if r["task_id"] == TASK]
    require(len(row) == 1 and row[0]["audit_priority_tier"]
            == "P4_NO_DEVELOPER_NATIVE_PAIR_PROVEN"
            and row[0]["original_crud"] == "create"
            and row[0]["eligible_for_matched_causal_LLM_trial"] is False
            and gate["original_intention_to_test_task_count"] == 45
            and gate["original45_developer_native_equal_witnesses"] == 11,
            "Frozen v0.31 original45 scope/eligibility drift")
    require(file_hash(root / HISTORICAL_D0) == HISTORICAL_D0_SHA,
            "Historical original D0 fixture report SHA mismatch")
    historical = json.loads((root / HISTORICAL_D0).read_text(encoding="utf8"))
    require(historical["source_task_id"] == TASK
            and historical["original_ifc_source_sha256"] == SOURCE_SHA
            and historical["public_question_sha256"] == QUESTION_SHA
            and historical["source_crud"] == "create"
            and historical["original_author_results"]["original_author_score"] == 1.0
            and historical["developer_authored_fixture_not_model_output"] is True
            and historical["developer_fixed_unrequested_dimensions_m"]
            == {"width": .3, "depth": .3},
            "Original D0 preregistered fixture historical evidence drift")
    all_tasks = {x["test_id"]: x for x in public_45(author, data)}
    require(len(all_tasks) == 45 and TASK in all_tasks,
            "Original public 45 task population changed")
    task = all_tasks[TASK]
    require(task["crud"] == "create" and task["category"] == "basic"
            and task["public_question_sha256"] == QUESTION_SHA
            and task["original_ifc_sha256"] == SOURCE_SHA
            and task["original_source_ifc_relpath"] == "basic_tasks.ifc",
            "Original public Column create task identity/source changed")
    question = task["public_question"].lower()
    require("column" in question and "3m" in question
            and "(12, 8)" in question,
            "Pinned original public question differs from fixed Column control")
    original = data / "ifc" / task["original_source_ifc_relpath"]
    require(original.is_file() and not original.is_symlink()
            and file_hash(original) == SOURCE_SHA,
            "Original public IFC missing or mutated")

    with TemporaryDirectory(prefix="bmb-v032-public-real-original-column-") as td:
        temp = Path(td)
        i_path = temp / "I0_native_original_mm.ifc"
        # CRITICAL: the I0 module does not import any D0/compiler/parser/grader.
        i = create_independent_public_column_i0(original, i_path)
        i_audit = verified_original_native_create(
            original, i_path, known_new_column_guid=i["new_native_IfcColumn_globalid"])
        i_sha = file_hash(i_path)
        # Only now instantiate the declarative D0 compiler.
        d_path = temp / "D0_native_original_mm.ifc"
        d = create_declarative_D0_after_independent_I0(original, d_path)
        d_audit = verified_original_native_create(
            original, d_path, known_new_column_guid=d["trusted_d0_new_native_Column_guid"])
        d_sha = file_hash(d_path)
        require(all(d_audit[k] == i_audit[k] for k in d_audit),
                "Native new Column geometry/source preservation differs D0 vs I0")
        require(i_sha == i["candidate_native_IFC_SHA256"]
                and d_sha == d["output_original_mm_IFC_sha256"]
                and file_hash(original) == SOURCE_SHA,
                "Original source or separately frozen candidate IFC changed")
        # Author grader is accessed ONLY after both native files and
        # independent native geometry + original-scene oracles have passed.
        from tools.bibimbap_matched25_cli import grade_author
        original_score_i = grade_author(author, original, i_path, TASK)
        original_score_d = grade_author(author, original, d_path, TASK)
        require(original_score_i == original_score_d
                and original_score_i["status"] == "AUTHOR_SCORED"
                and original_score_i["original_author_score"] == 1.0
                and original_score_i["original_author_full_mark"] is True
                and original_score_i["original_author_metrics"]
                == {"object_exists": 1.0, "right_location": 1.0,
                    "right_dimensions": 1.0, "integrity_constraint": 1.0},
                "Pinned original author scorers differ or are not full on both controls")
        require(file_hash(original) == SOURCE_SHA
                and _head(author) == AUTHOR_SHA and _head(data) == DATA_SHA,
                "Original benchmark source or Git revision modified")
        return {
            "status": "V032_ORIGINAL_PUBLIC_TEST04_DEVELOPER_D0_I0_NATIVE_COLUMN_SEMANTIC_PARITY_AUTHOR_1_0",
            "issue": ISSUE,
            "original_public_task_id": TASK,
            "original45_intention_to_test_denominator": 45,
            "pinned_original_author_git_sha": AUTHOR_SHA,
            "pinned_original_data_git_sha": DATA_SHA,
            "original_public_question_sha256": QUESTION_SHA,
            "original_source_mm_IFC_sha256": SOURCE_SHA,
            "frozen_v031_source_gate_sha256": FROZEN_GATE[1],
            "original_source_schema": "IFC4X3",
            "public_create_operation": "CREATE_ABSOLUTE_COLUMN",
            "predeclared_unrequested_width_and_depth_m": [0.3, 0.3],
            "developer_only_new_actual_original_create_pair": True,
            "independent_imperative_python_i0_executed_before_declarative_d0": True,
            "D0_uses_full_declarative_XML_not_imperative_wrapper": True,
            "original_sources_and_previous_reports_modified": False,
            "native_task_specific_Column_geometry_and_original_product_preservation_equal": True,
            "source_original_roots_identity_and_world_product_geometries_preserved": True,
            "native_independent_oracle_both_arms": d_audit,
            "native_full_D0_IFC_sha256": d_sha,
            "native_full_I0_IFC_sha256": i_sha,
            "native_full_D0_I0_bytes_equal": d_sha == i_sha,
            "native_new_Column_GUIDs_same_between_arms": (
                i["new_native_IfcColumn_globalid"] == d["trusted_d0_new_native_Column_guid"]),
            "original_author_score_D0": original_score_d,
            "original_author_score_I0": original_score_i,
            "original_author_scores_equal_full": True,
            "original_test04_historic_developer_D0_only_before_this_checkpoint": True,
            "prior_v031_original45_full_native_D0_I0_byte_equal_witness_count": 11,
            "new_cumulative_original45_full_native_byte_equal_witness_count": (
                12 if d_sha == i_sha else 11),
            "new_separate_semantic_only_original_public_create_pair_count": (
                0 if d_sha == i_sha else 1),
            "original45_full_information_equivalence_proven": 0,
            "original45_full_native_write_capability_equivalence_proven": 0,
            "matched_real_D_I_LLM_trials": 0,
            "causal_representational_performance_inference_permitted": False,
            "new_paid_provider_requests": 0,
            "benchmark_author_grader_private_targets_not_used_to_construct_either_arm": True,
            "full_original_45_create_coverage_claimed": False,
            "llm_model_success_estimate": None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--write", type=Path,
                        help="Write once only; never overwrite frozen evidence")
    args = parser.parse_args()
    result = pair_public_test04(args.root, args.author, args.data)
    encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf8")
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        with args.write.open("xb") as file:
            file.write(encoded)
        print("WROTE " + str(args.write) + " " + sha256(encoded).hexdigest())
    else:
        print(json.dumps({
            "status": result["status"],
            "native_task_geometry": result["native_task_specific_Column_geometry_and_original_product_preservation_equal"],
            "byte_equal": result["native_full_D0_I0_bytes_equal"],
            "author_D0": result["original_author_score_D0"]["original_author_score"],
            "author_I0": result["original_author_score_I0"]["original_author_score"],
            "candidate_sha256_D0": result["native_full_D0_IFC_sha256"],
            "candidate_sha256_I0": result["native_full_I0_IFC_sha256"],
            "model_calls": result["matched_real_D_I_LLM_trials"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
