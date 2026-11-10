"""Sanitized SOURCE-ONLY experimental paired IFC Space metadata oracle.

This is a developer-authored prototype of a separate v0.2 declarative final
state vs independently written Python/IfcOpenShell. It is NOT an LLM
trial, approved prompt context, official scorer, or measured BIM-Edit
accuracy. The synthetic new room "135" is explicitly author-selected,
NOT inferred from benchmark ground truth.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tests.test_space_semantics_v02_independent_pair import (
    independently_paired_v02_result,
)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=independently_paired_v02_result()
    if not (report["native_independent_six_category_parity"]
            and report["native_all_space_type_pset_qto_relation_parity"]
            and report["native_source_space_metadata_preserved"]
            and report["new_metadata_root_guid_count"]==8
            and report["introduced_ifc_schema_error_categories"]==0
            and not report["source_ifc_modified"]):
        raise RuntimeError("Explicit v0.2 Space metadata IFC oracle verification failed")
    report.update({
        "source_only_manual_synthetic_new_room_metadata":True,
        "new_room_metadata_in_benchmark_instruction_proven":False,
        "independent_ifc_geometry_validation_passed":True,
        "new_room_qto_is_exact_rectangular_box_only":True,
        "new_source_type_pset_qto_assignment_supported_in_v02_candidate":True,
        "old_v01_compiler_or_agent_runner_modified":False,
        "official_evaluator_called":False,
        "ground_truth_loaded":False,
        "frozen_36_sample_modified":False,
        "model_context_budget_approved":False,
        "full_native_space_semantics_proven":False,
    })
    if args.output_json:
        path=args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Evidence file exists/symlink or parent missing")
        with path.open("x",encoding="utf8",newline="\n") as file:
            file.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    # The paired manual oracle PASSES but this research gate remains blocked:
    # no model authored metadata, approved experiment, or official evaluation.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
