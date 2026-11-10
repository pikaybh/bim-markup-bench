"""Offline paired-input *candidate* audit, never a model run.

Tests whether a separately versioned, source-observed IFC Space semantic
overlay can be reproducibly materialized beside the same frozen v0.1 XML
view for BOTH arms. Does not modify deployed G2 runners or authorize
model-facing v0.2, official grading, or changed experiment settings.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.direct_markup.agent_runner import (
    SourceOnlySettings,stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    create_matched_observations,ControlConfig,ImperativeControlSession,
)
from src.runtime.space_semantics_candidate import (
    project_space_semantics_candidate,
    verify_unedited_space_semantics_candidate,
)
from tests.test_native_t_path_junction import pinned_input


@dataclass(frozen=True)
class CandidatePair:
    instruction:str
    source_sha256:str
    base_xml_bytes:bytes
    base_spec_bytes:bytes
    candidate_metadata_bytes:bytes

    def as_audit(self)->dict:
        return {
            "instruction_sha256":
                hashlib.sha256(self.instruction.encode("utf8")).hexdigest(),
            "source_sha256":self.source_sha256,
            "baseline_v0_1_xml_sha256":
                hashlib.sha256(self.base_xml_bytes).hexdigest(),
            "baseline_v0_1_spec_sha256":
                hashlib.sha256(self.base_spec_bytes).hexdigest(),
            "candidate_space_semantics_xml_sha256":
                hashlib.sha256(self.candidate_metadata_bytes).hexdigest(),
        }


def verify_paired_candidate_observation(left:CandidatePair,
                                        right:CandidatePair)->dict:
    if left!=right:
        raise ValueError("Proposed D/I observation payloads differ")
    if (len(left.source_sha256)!=64 or
            any(c not in "0123456789abcdef" for c in left.source_sha256)):
        raise ValueError("Source digest malformed")
    if not left.candidate_metadata_bytes:
        raise ValueError("No candidate semantic overlay supplied")
    return {
        **left.as_audit(),
        "proposed_paired_source_observation_equal":True,
        "reusable_native_metadata_observation_equal":True,
        "model_facing_v02_enabled":False,
        "input_fairness_and_model_budget_approved":False,
    }


def audit_candidate_input_pair()->dict:
    task,source,refs=pinned_input()
    source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    task_payload={
        "task_id":task["task_id"],
        "instruction":task["prompt"],
        "input_file":"input.ifc",
    }
    with TemporaryDirectory(prefix="space-v02-context-candidate-") as work:
        session=stage_source_only_workspace(
            source,Path(work)/"D_v01",
            task_payload,SourceOnlySettings())
        d=session.agent_visible_context()
        control=create_matched_observations(source,task_payload)
        i=ImperativeControlSession(control,ControlConfig())
        i_view=i.model_visible_context()
        if i_view["OS_sandbox_available"] or i_view["allowed_execution_operations"]:
            raise ValueError("I0 source-only candidate unexpectedly permits code execution")
        if d.task_id!=control.task_id:
            raise ValueError("D/I task IDs differ")
        # Two separate source-only materializations, never a shared object
        # masquerading as two independently staged candidate observations.
        d_overlay=project_space_semantics_candidate(source)
        i_overlay=project_space_semantics_candidate(source)
        d_valid=verify_unedited_space_semantics_candidate(source,d_overlay.xml)
        i_valid=verify_unedited_space_semantics_candidate(source,i_overlay.xml)
        if d_valid!=i_valid:
            raise ValueError("D/I candidate native metadata validation differs")
        direct=CandidatePair(
            d.instruction,source_sha,d.xml_text.encode("utf8"),
            d.language_spec.encode("utf8"),d_overlay.xml)
        imperative=CandidatePair(
            control.instruction,control.input_ifc_sha256,
            control.model_xml_text.encode("utf8"),
            control.toy_language_spec.encode("utf8"),i_overlay.xml)
        shared=verify_paired_candidate_observation(direct,imperative)
        if d_overlay.source_sha256!=control.input_ifc_sha256:
            raise ValueError("Overlay source digest does not match G2 IFC source")
        if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:
            raise ValueError("Original public IFC modified during candidate audit")
        return {
            **shared,
            "status":"PASS_SEPARATE_CANDIDATE_CONTEXT_MATCH_NOT_A_MODEL_READY_EXPERIMENT",
            "frozen_public_task_id":task["task_id"],
            "source_space_count":d_overlay.source_space_count,
            "source_type_count":d_overlay.source_type_count,
            "source_instance_pset_count":d_overlay.source_pset_count,
            "source_reference_count":d_overlay.source_reference_count,
            "candidate_xml_bytes":len(d_overlay.xml),
            "baseline_xml_bytes":len(direct.base_xml_bytes),
            "candidate_read_only":True,
            "native_source_space_semantics_seen_in_candidate":True,
            "frozen_v0_1_source_and_parser_unmodified":True,
            "new_space_type_pset_qto_authoring_compiler_implemented":False,
            "official_evaluator_used":False,
            "model_calls":0,
            "official_scores":0,
            "ground_truth_loaded":False,
            "fixed_sample_changed":False,
        }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=audit_candidate_input_pair()
    if args.output_json:
        output=args.output_json
        if output.is_symlink() or output.exists() or not output.parent.is_dir():
            parser.error("Output exists, symlink or parent not found")
        with output.open("x",encoding="utf8",newline="\n") as h:
            h.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    # Design-stage candidate only: no model-facing promotion or scored task.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
