"""Audit public-input context parity and native Space metadata observability.

ONE frozen input, trusted source-only metadata.  No GT, hidden evaluator,
LLM API, OS sandbox or candidate output IFC.  The common observation check
must NOT be conflated with full semantic-input/evaluation parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell

from src.data.bim_edit import read_tasks,repo_asset_path
from src.direct_markup.agent_runner import (
    SourceOnlySettings,stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    create_matched_observations,ImperativeControlSession,ControlConfig,
)
from src.runtime.space_metadata_gate import (
    preflight_source_room_semantics,
)
from tests.test_native_t_path_junction import pinned_input


def verify_core_text_observation_parity(direct,imperative,source_sha)->dict:
    """Require every *shared* source fact to match byte-for-byte.

    This deliberately does not claim authoring tool-policy parity, IFC
    metadata completeness or matched LLM execution budgets.
    """
    checks={
        "public_task_id":direct.task_id==imperative.task_id,
        "public_instruction":direct.instruction==imperative.instruction,
        "xml_projection_bytes":direct.xml_text==imperative.model_xml_text,
        "toy_xml_spec_bytes":direct.language_spec==imperative.toy_language_spec,
        "source_input_ifc_sha256":source_sha==imperative.input_ifc_sha256,
    }
    if not all(checks.values()):
        raise ValueError("The two arms' source observations diverged")
    return checks


def audit_one_public_space_context()->dict:
    task,source,refs=pinned_input()
    original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    public_payload={
        "task_id":task["task_id"],
        "instruction":task["prompt"],
        "input_file":"input.ifc",
    }
    source_f=ifcopenshell.open(str(source))
    room=source_f.by_guid(refs[2])
    types,psets,associations=preflight_source_room_semantics(
        source_f,refs[2])
    with TemporaryDirectory(prefix="g1-space-source-context-pair-") as folder:
        workspace=Path(folder)/"D"
        session=stage_source_only_workspace(
            source,workspace,public_payload,SourceOnlySettings())
        direct=session.agent_visible_context()
        imperative=create_matched_observations(source,public_payload)
        control=ImperativeControlSession(imperative,ControlConfig())
        code_context=control.model_visible_context()
        core_equal=verify_core_text_observation_parity(
            direct,imperative,original_sha)
        if code_context["model_xml_text"]!=direct.xml_text:
            raise ValueError("Imperative model-facing XML differs from declarative context")
        prohibited=("ground_truth_ifc","gt_path","evaluation","expected_output",
                    "OPENAI_API_KEY")
        if any(name in code_context for name in prohibited):
            raise ValueError("Imperative context contains a grader/secret field")
        if code_context["OS_sandbox_available"] or code_context["allowed_execution_operations"]:
            raise ValueError("Imperative runner unexpectedly permits executable model code")
        exposed=direct.xml_text
        # The XML is a *partial* IFC view, and does NOT embed source Space
        # type or Pset definitions. This is a detectable information loss,
        # not proof one LLM approach is better/worse.
        names=[record[2] for record in types]
        pset_names=[row[2][1] for row in psets]
        if any(name in exposed for name in (*names,*pset_names)):
            raise ValueError("Unexpected Space type/Pset names present in projected toy XML")
        declared_d_actions=tuple(direct.allowed_operations)
        declared_i_actions=tuple(code_context["allowed_authoring_operations"])
        if "submit_python_text" not in declared_i_actions:
            raise ValueError("Imperative model output contract unexpectedly changed")
        report={
            "status":"PASS_CORE_TEXT_CONTEXT_EQUAL_FULL_SEMANTIC_PARITY_BLOCKED",
            "frozen_task_id":task["task_id"],
            "input_source_sha256":original_sha,
            "model_context_equal_fields":core_equal,
            "core_source_text_context_equal":True,
            "xml_source_byte_sha256":direct.xml_byte_sha256,
            "shared_xml_projection_sha256":
                hashlib.sha256(direct.xml_text.encode("utf8")).hexdigest(),
            "shared_toy_spec_sha256":
                hashlib.sha256(direct.language_spec.encode("utf8")).hexdigest(),
            "source_ifc_space_type_relation_count":len(types),
            "source_ifc_space_instance_pset_relation_count":len(psets),
            "source_ifc_space_association_count":len(associations),
            "native_type_and_psets_omitted_from_xml_projection":True,
            "direct_arm_operations":list(declared_d_actions),
            "imperative_arm_operations":list(declared_i_actions),
            "imperative_extra_api_reference_present":
                bool(code_context.get("api_reference_notes")),
            "immutable_input_ifc_bytes_preserved":
                original_sha==hashlib.sha256(source.read_bytes()).hexdigest(),
            "model_information_equivalence_proven":False,
            "both_arms_cover_source_native_type_pset":False,
            "native_space_type_and_reference_semantics_eligible":False,
            "official_evaluator_used":False,
            "model_provider_calls":0,
            "official_scores":0,
            "ground_truth_loaded":False,
            "fixed_sample_modified":False,
        }
    return report


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=audit_one_public_space_context()
    if args.output_json:
        path=args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refusing overwrite/symlink or missing evidence directory")
        with path.open("x",encoding="utf8",newline="\n") as stream:
            stream.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    # Only the core shared text passed. The full metadata/fair comparison
    # precondition is still blocked; non-zero gate status is intentional.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
