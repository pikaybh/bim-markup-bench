"""v0.18 actual original all45 read-only, two-arm source-fact replay audit.

- Original pinned public task descriptions and 31 native IFC files only.
- Source snapshot built once per unique native IFC, rebound to each public
  question's SHA, never written as a raw dataset into Git.
- Both arm read sessions execute identical recorded queries and return
  identical bytes. NO model, XML edit, Python write, hidden answer or grader.
- A real matched causal LLM trial remains blocked until an independently
  OS-enforced Python no-source-side-channel runner exists and is attested.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v018_common_read import (
    PACKET_SCHEMA, CommonReadSession, CommonReadBlocked,
    bind_public_question_to_frozen_source_packet,
    build_public_source_packet, canonical_json, compare_equal_observations,
    strict_llm_trial_launch_gate,
)

FROZEN_V017_INFO_SHA = "c2683de1705b92ebe0ce8472c6a870b98c54c668e387ddf80c9377cdb2e88078"
FROZEN_V017_SLAB_SHA = "c6b02877a3f031c8f5435222b65db4a0fef04568119eaa750586f106d53231e8"
SPECIAL_ORIGINAL_TASKS = ("test_15", "test_16", "topological_test_15")


class OriginalCommonReadAuditBlocked(ValueError):
    pass


def audit(author: Path, data: Path, prior_info: Path, prior_slab: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise OriginalCommonReadAuditBlocked("Original public author/data Git HEAD mismatch")
    if file_hash(prior_info).lower() != FROZEN_V017_INFO_SHA:
        raise OriginalCommonReadAuditBlocked("Prior frozen original all45 native information census changed")
    if file_hash(prior_slab).lower() != FROZEN_V017_SLAB_SHA:
        raise OriginalCommonReadAuditBlocked("Prior frozen original Slab editor result changed")
    prior = json.loads(prior_info.read_text(encoding="utf8"))
    prev_slab = json.loads(prior_slab.read_text(encoding="utf8"))
    if prev_slab["original_author_scoreable_both_dev_arms_total"] != 3:
        raise OriginalCommonReadAuditBlocked("Previously frozen paired native controls changed")

    tasks = {x["test_id"]: x for x in public_45(author, data)}
    historical = {
        row["task_id"]: row
        for row in prior["all_45_task_information_parity_audit"]
    }
    if len(tasks) != 45 or len(historical) != 45 or set(tasks) != set(historical):
        raise OriginalCommonReadAuditBlocked("Original published all45 task population changed")
    crud = Counter(x["crud"] for x in tasks.values())
    if crud != Counter({"create": 15, "update": 15, "delete": 15}):
        raise OriginalCommonReadAuditBlocked("Original all45 CRUD distribution changed")
    if prior["source_unique_original_IFC_count"] != 31:
        raise OriginalCommonReadAuditBlocked("Original public 31 native source population changed")
    native_cache = {}
    original_source_sha_checks = {}
    packet_manifest = {}
    native_source_schemas = {}
    geometry_summary = Counter()
    placement_summary = Counter()
    all45 = []

    for task_id in sorted(tasks):
        task = tasks[task_id]
        prev = historical[task_id]
        original_rel = task["original_source_ifc_relpath"]
        source = data / "ifc" / original_rel
        expected_native_source_sha = task["original_ifc_sha256"]
        if (prev["original_public_ifc_sha256"] != expected_native_source_sha or
            prev["original_public_question_sha256"] != task["public_question_sha256"] or
            file_hash(source) != expected_native_source_sha):
            raise OriginalCommonReadAuditBlocked("An original public source or task question changed")

        if original_rel not in native_cache:
            packet = build_public_source_packet(
                source, task["public_question_sha256"]
            )
            manifest = json.loads(packet)
            if (manifest["schema"] != PACKET_SCHEMA or
                manifest["public_source"]["original_ifc_sha256"] != expected_native_source_sha):
                raise OriginalCommonReadAuditBlocked("Original native fact source identity mismatch")
            if (manifest["manifest"]["all_native_source_IfcProduct_count"]
                != prev["native_original_ifc_product_count"]):
                raise OriginalCommonReadAuditBlocked("Observed original native product census drift")
            if (manifest["manifest"]["serialized_native_IfcProduct_count"]
                != len(manifest["products"])):
                raise OriginalCommonReadAuditBlocked("Original product list incompletely serialized")
            native_cache[original_rel] = packet
            packet_manifest[original_rel] = manifest["manifest"]
            native_source_schemas[original_rel] = manifest["public_source"]["ifc_schema"]
            original_source_sha_checks[original_rel] = expected_native_source_sha
            geometry_summary.update(manifest["manifest"]["geometry_status_counts"])
            placement_summary.update(manifest["manifest"]["placement_status_counts"])
        else:
            packet = bind_public_question_to_frozen_source_packet(
                native_cache[original_rel], task["public_question_sha256"]
            )
            manifest = json.loads(packet)
        # Native source is opened only for initial source snapshot generation
        # outside any LLM or read session. Rebound task SHA must be exact.
        if manifest["public_source"]["public_question_sha256"] != task["public_question_sha256"]:
            raise OriginalCommonReadAuditBlocked("A frozen source packet got the wrong task identity")
        if manifest["public_source"]["original_ifc_sha256"] != expected_native_source_sha:
            raise OriginalCommonReadAuditBlocked("A frozen source packet got the wrong IFC")
        product_ids = {x["global_id"] for x in manifest["products"]}
        if len(product_ids) != prev["native_original_ifc_product_count"]:
            raise OriginalCommonReadAuditBlocked("Original native product inventory not source-complete")

        # Both source observers see the exact same bytes, but the runnable
        # imperative Python LLM is NOT enabled here: it could bypass shared
        # observations if given the raw original IFC path/filesystem access.
        packet_sha = sha256(packet).hexdigest()
        d = CommonReadSession(packet, "D", expected_packet_sha256=packet_sha)
        i = CommonReadSession(packet, "I", expected_packet_sha256=packet_sha)
        original_public_refs = sorted(set(
            x["global_id"] for x in manifest["products"] if
            x["global_id"] in (
                # Only directly named source references from ORIGINAL
                # public question text, not evaluator private targets.
                source_guid for source_guid in _public_named_guids(task["public_question"])
            )
        ))
        public_all_guids = _public_named_guids(task["public_question"])
        not_in_source = sorted(set(public_all_guids) - product_ids)
        queries: list[dict[str, Any]] = [
            {"operation": "source_summary"},
            {"operation": "list_all_products"},
        ]
        # Every original task: summary, all native product IDs, a native
        # IfcProduct class inventory, explicit PUBLIC named target details,
        # and native product relationship evidence. Classes are observed
        # from actual source packet only, not grader/private task targets.
        named_source_classes = sorted(set(
            product["ifc_class"] for product in manifest["products"]
            if product["global_id"] in original_public_refs
        ))
        observed_classes = (named_source_classes if named_source_classes
                            else sorted(set(p["ifc_class"] for p in manifest["products"]))[:1])
        for category in observed_classes:
            queries.append({"operation": "list_by_class", "ifc_class": category})
        for guid in original_public_refs:
            queries.append({"operation": "get_product", "global_id": guid})
            queries.append({"operation": "related_relations", "global_id": guid})
        if not original_public_refs and manifest["products"]:
            # At least one non-target source relationship replay for tasks
            # without an explicit public GlobalId in instruction text.
            first = manifest["products"][0]["global_id"]
            queries.extend((
                {"operation": "get_product", "global_id": first},
                {"operation": "related_relations", "global_id": first},
            ))
        if len(queries) > 25:
            raise OriginalCommonReadAuditBlocked("Original public task source observations exceed cap")
        parity = compare_equal_observations(d, i, tuple(queries))
        if d.calls_used != i.calls_used or d.calls_used != parity["call_count"]:
            raise OriginalCommonReadAuditBlocked("Paired read receipt counts differ")
        if not parity["D_and_I_exact_common_read_response_bytes_identical"]:
            raise OriginalCommonReadAuditBlocked("Actual D/I source observations differ")
        all45.append({
            "task_id": task_id,
            "category": task["category"],
            "crud": task["crud"],
            "public_instruction_sha256": task["public_question_sha256"],
            "original_source_ifc_sha256": expected_native_source_sha,
            "original_source_identity_sha256": sha256(original_rel.encode("utf8")).hexdigest(),
            "actual_original_IFC_schema": manifest["public_source"]["ifc_schema"],
            "actual_original_IfcProduct_inventory_count":
                manifest["manifest"]["all_native_source_IfcProduct_count"],
            "source_native_relationship_count":
                manifest["manifest"]["source_native_relationship_count"],
            "physical_bbox_count": manifest["manifest"]["geometry_status_counts"].get(
                "PHYSICAL_WORLD_BBOX_METRES", 0),
            "geometry_coverage_status_counts": manifest["manifest"]["geometry_status_counts"],
            "public_named_native_product_refs_present": len(original_public_refs),
            "public_named_product_refs_absent_from_snapshot": len(not_in_source),
            "native_IFC_original_source_unchanged": file_hash(source) == expected_native_source_sha,
            "common_public_facts_packet_sha256": parity["packet_sha256"],
            "observed_native_source_class_query_count": len(observed_classes),
            "identical_D_I_read_calls": parity["call_count"],
            "identical_D_I_read_transcript_sha256": parity["transcript_sha256"],
            "shared_read_only_observation_replay": "PASS",
            "full_original_IFC_semantic_information_equivalent": False,
            "original_native_backend_capability_matched_by_this_read_tool": False,
            "independent_native_Python_execution_confinement_proven": False,
            "original_author_scorer_was_called": False,
            "real_matched_LLM_run_count": 0,
            "is_original45_public_denominator_member": True,
        })

    if len(native_cache) != 31 or len(all45) != 45:
        raise OriginalCommonReadAuditBlocked("Public IFC source/read cohort incomplete")
    for rel, sha in original_source_sha_checks.items():
        if file_hash(data / "ifc" / rel) != sha:
            raise OriginalCommonReadAuditBlocked("Original public native IFC changed during read session")
    if any(r["shared_read_only_observation_replay"] != "PASS" for r in all45):
        raise OriginalCommonReadAuditBlocked("A public task observation replay failed")

    # No OS sandbox has been implemented or attested on the host.  This is
    # a conservative specific snapshot of EXISTING unsafe baseline behavior,
    # not a simulation that can serve as a real LLM model run.
    launch = strict_llm_trial_launch_gate(
        common_facts_identical=True,
        native_python_original_ifc_mount=True,
        python_unrestricted_filesystem_or_exec=True,
        independent_os_sandbox_attestation=False,
        matched_write_capability_verified=False,
        explicit_paid_budget_approved=False,
    )
    if launch["status"] != "BLOCKED" or launch["causal_real_LLM_launch_permitted_by_this_module"]:
        raise OriginalCommonReadAuditBlocked("Real model launch gate unsafe")
    return {
        "status": "ORIGINAL45_COMMON_READ_FACT_PACKET_PARITY_PROVEN_BUT_CAUSAL_LLM_LAUNCH_BLOCKED",
        "issue": "https://github.com/pikaybh/bim-markup-bench/issues/150",
        "pinned_original_author_git_sha": AUTHOR_SHA,
        "pinned_original_public_data_git_sha": DATA_SHA,
        "original_source_catalog_v017_sha256": FROZEN_V017_INFO_SHA,
        "original_native_topological_v017_sha256": FROZEN_V017_SLAB_SHA,
        "frozen_observation_packet_schema": PACKET_SCHEMA,
        "original_full_population_45_preserved": True,
        "original_original45_denominator": len(all45),
        "original_public_15_per_crud": dict(sorted(crud.items())),
        "original_unique_ifc_source_count": len(native_cache),
        "actual_distinct_original_IfcProduct_inventory_count_across_source_snapshots":
            sum(x["all_native_source_IfcProduct_count"] for x in packet_manifest.values()),
        "original_source_schema_counts_across_unique_IFCs":
            dict(sorted(Counter(native_source_schemas.values()).items())),
        "geometry_coverage_by_original_native_unique_source":
            dict(sorted(geometry_summary.items())),
        "placement_coverage_by_original_native_unique_source":
            dict(sorted(placement_summary.items())),
        "common_read_observation_bytes_equal_across_45_tasks": True,
        "common_read_observation_parity_case_count": len(all45),
        "new_real_matched_D_I_LLM_trials": 0,
        "new_paid_model_requests": 0,
        "new_paid_usd": 0,
        "newly_independent_original_author_SCORED_case_count": 0,
        "previous_source_native_developer_edit_equivalence": "5/45_3_AUTHOR_SCORABLE",
        "original_native_IFC_to_typed_XML_authoring_interface": "STILL_PARTIAL_TYPED_VIEW",
        "full_IFC_entity_relationship_property_mesh_information_equivalence": False,
        "full_IFC_native_write_operation_capability_parity_proven": False,
        "Python_file_mount_and_exec_side_channel_eliminated": False,
        "safe_real_causal_LLM_launch_gate": launch,
        "source_snapshot_payloads_and_original_IFC_files_NOT_committed": True,
        "unmodified_original_scorer_and_hidden_reference": True,
        "all_45_public_task_read_observation_audit": all45,
        "three_previously_proven_developer_source_edits_read_replay": {
            task: {"packet_sha256": next(r for r in all45 if r["task_id"] == task)[
                "common_public_facts_packet_sha256"],
                   "read_receipt_count": next(r for r in all45 if r["task_id"] == task)[
                       "identical_D_I_read_calls"]}
            for task in SPECIAL_ORIGINAL_TASKS
        },
    }


def _public_named_guids(public_question: str) -> tuple[str, ...]:
    import re
    # Exact 22-character native original IFC GlobalId strings only. This
    # may include references *absent from the source*; never use author GT.
    found = re.findall(r"(?<![0-9A-Za-z_$])([0-9A-Za-z_$]{22})(?![0-9A-Za-z_$])",
                       public_question)
    return tuple(sorted(set(found)))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--prior-v017-information", type=Path, required=True)
    p.add_argument("--prior-v017-slab", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refusing overwrite of immutable original public research report")
    result = audit(a.author, a.data,
                   a.prior_v017_information, a.prior_v017_slab)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print("COMMON_READ", result["status"])
    print("ORIGINAL_TASKS", result["original_original45_denominator"],
          "UNIQUE_IFC", result["original_unique_ifc_source_count"],
          "NATIVE_PRODUCTS", result[
              "actual_distinct_original_IfcProduct_inventory_count_across_source_snapshots"])
    print("REPLAY_PARITY", result["common_read_observation_parity_case_count"],
          "STRICT_MODEL_LAUNCH", result["safe_real_causal_LLM_launch_gate"]["status"])
    print("REPORT_SHA256", file_hash(a.output))


if __name__ == "__main__":
    main()
