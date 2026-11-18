"""Issue #247: OFFLINE genuine source byte/tool-schema experiment FAIRNESS audit.

This is *not* a model-generated trial, a provider tokenizer or an activated
session. It reads only 4 known developer-exposed source IFCs, their metadata,
the existing pinned public-source projector modules and prior frozen reports.
It computes actual UTF8 sizes, a transparent proxy (bytes/4 ceil), paired
FULL/MANAGED/Python developer-written control payload sizes, and measures
the PROPOSED tool schemas. No hidden grader, private GT, paid call, or upload.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools import audit_bibimbap_v065_offline_generalization as v065
from tools import audit_bibimbap_v066_window_final_state as v066win
from tools import bibimbap_v065_source_neutral_door as door
from tools import bibimbap_v066_window_final_state as win
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057, refuse_all_model_trials_v057,
    ProviderTrialBlocked057,
)
from tools import bibimbap_v066_prospective_fairness_contract as fair

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_prospective_D_I_fairness_20261119.json"
FROZEN_WINDOW=ROOT/"reports"/"bibimbap_v066_window_move_delete_native_20261118.json"
WINDOW_SHA="b7ee995579d32a887dc5a34882950f2b967861b27e132591b7dd8fab40b7c8be"
FROZEN_V065=v065.REPORT
V065_SHA="cc55f6623fc65d3936cf6ee9bbacf1c46d3893aa94122317632d9f90d009382d"
SOURCE_EXPOSED_DOOR=("geometry_test_03","topological_test_05")
SOURCE_EXPOSED_WINDOW=("geometry_test_13","geometry_test_19")


def need(condition,message):
    if not condition:raise AssertionError(message)


def canonical(report):
    return (json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2,
                       allow_nan=False)+"\n").encode("utf8")


def _utf8(text):
    if isinstance(text,bytes):
        return text
    return text.encode("utf8","strict")


def _payload_metrics(raw):
    return fair.byte_metrics(_utf8(raw))


def _tool_arg_bytes(arm, content):
    name="code" if arm=="I_NATIVE" else "xml_text"
    return fair.canonical_bytes({name:content.decode("utf8","strict")
                                  if isinstance(content,bytes) else content})


def _measured_row(original,sha,schema,family,operation,full,managed,
                  submitted_full,submitted_managed,python_code):
    need(file_hash(original)==sha,
         "Unmodified developer-exposed original source SHA changed")
    need(isinstance(python_code,str) and "commit()" in python_code,
         "Developer proof must be real standalone Python")
    python_data=python_code.encode("utf8")
    read=fair.common_read_envelope(
        original_sha=sha,original_schema=schema,
        full_xml=full,managed_xml=managed)
    # Same *proposed* initial source-only read response for every arm.
    common_response=fair.canonical_bytes(read)
    reads={arm:sha256(common_response).hexdigest() for arm in fair.ARMS}
    need(len(set(reads.values()))==1,
         "The proposed per-source initial source-only read must match")
    native_bytes=original.stat().st_size
    _submission={
        "D_FULL":submitted_full,
        "D_MANAGED":submitted_managed,
        "I_NATIVE":python_data,
    }
    arms={}
    for arm,submitted in _submission.items():
        args=_tool_arg_bytes(arm,submitted)
        arms[arm]={
            "real_developer_control_submission":_payload_metrics(submitted),
            "actual_UTF8_tool_arguments":_payload_metrics(args),
            "proposed_tool_definitions_UTF8":_payload_metrics(
                fair.model_tool_schema_bytes(arm)),
            "developer_control_submission_sha256":sha256(submitted).hexdigest(),
            "source_read_envelope_SHA256":reads[arm],
            "actual_billed_provider_tokens":None,
            "actual_USD_cost":None,
        }
    need(arms["D_MANAGED"]["real_developer_control_submission"]["UTF8_bytes"] <
         arms["D_FULL"]["real_developer_control_submission"]["UTF8_bytes"],
         "Source-managed complete XML is not more compact than full")
    return {
        "native_original_IFC_SHA256":sha,
        "schema":schema,
        "family":family,
        "operation_family":operation,
        "original_native_IFC_file_bytes_local_only":native_bytes,
        "shared_proposed_initial_read_envelope_UTF8":_payload_metrics(common_response),
        "shared_proposed_source_FULL_initial_XML_UTF8":_payload_metrics(full),
        "shared_proposed_source_MANAGED_initial_XML_UTF8":_payload_metrics(managed),
        "same_proposed_read_envelope_SHA256_for_all_three":True,
        "model_input_is_really_abstract_source_projection_only":True,
        "imperative_runtime_native_IFC_access_additional_to_read":True,
        "proposed_arm_submission_payloads":arms,
        "real_original_IFC_file_SHA256_rechecked":True,
        "author_hidden_GT_read":False,
    }


def _door_cases(rows):
    cases=[]
    for task in SOURCE_EXPOSED_DOOR:
        row=rows[task]
        original=v065.DATA/"ifc"/row["original_source_ifc_relpath"]
        sha=row["original_ifc_sha256"]
        model=door.source_model(original,sha)
        st=v065._case_fixture(model,model.schema)
        full=door.full_initial_xml(original,sha)
        managed=door.managed_initial_xml(original,sha)
        submitted_full=v065._final_xml(full,st)
        submitted_managed=v065._final_xml(managed,st,managed=True)
        code=v065._real_independent_I_python(st,model)
        cases.append(_measured_row(
            original,sha,model.schema,"hosted_door_opening","create",
            full,managed,submitted_full,submitted_managed,code))
    return cases


def _window_cases(rows):
    cases=[]
    for task in SOURCE_EXPOSED_WINDOW:
        row=rows[task]
        original=v065.DATA/"ifc"/row["original_source_ifc_relpath"]
        sha=row["original_ifc_sha256"]
        f=win.source(original,sha)
        groups=win.groups(f)
        chosen=sorted(groups)[0]
        group=groups[chosen]
        index=sorted(groups).index(chosen)
        offset=v066win._developer_control(group)
        full=win.full_source_state(original,sha)
        managed=win.managed_source_state(original,sha)
        for kind in ("move","delete"):
            modified_full=v066win._submitted_state(
                full,group,kind=kind,offset=offset)
            modified_managed=v066win._submitted_state(
                managed,group,kind=kind,offset=offset)
            # No original scorer or GT reads; source-only direct XML diff.
            parsed_full=win.parse_full_state(original,sha,modified_full)
            _,parsed_managed=win.expand_managed_state(
                original,sha,modified_managed)
            need(parsed_full==parsed_managed
                 and parsed_full["kind"]==kind,
                 "Real source-neutral managed/full states mismatch")
            code=v066win._imperative_code(kind,index,offset)
            cases.append(_measured_row(
                original,sha,f.schema,"hosted_window_assembly",kind,
                full,managed,modified_full,modified_managed,code))
    return cases


def _budgets_and_blockers():
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL"
         and not rights["provider_transfer_and_retention_approved"]
         and not rights["underlying_individual_IFC_asset_rights_verified"]
         and rights["provider_exact_model_snapshot"] is None
         and rights["approved_USD_cap"] is None,
         "Original IFC usage rights unexpectedly modified")
    for forged in (None,
                   {"owner_approval":True,"external_transfer":True,
                    "provider":"unverified","budget_USD":1000000}):
        try:
            refuse_all_model_trials_v057(forged)
        except ProviderTrialBlocked057:
            pass
        else:
            raise AssertionError("Existing hard no-provider gate defeated")
    for arm in fair.ARMS:
        for regime in fair.REGIMES:
            ledger=fair.OfflineBudgetLedger(arm,regime)
            ledger.read()
            for _ in range(fair.MAX_ATTEMPTS[regime]):
                reply=ledger.submit("admitted_native_scope")
                need(reply["author_task_score"] is None if
                     regime=="feedback" else
                     not reply["feedback_visible_during_generation"],
                     "Owner hidden grader output leaked into feedback")
            summary=ledger.finalize()
            need(summary["actual_tool_calls"]==fair.MAX_CALLS[regime],
                 "Prospective budget count drifted")
    return {
        "prospective_arms":list(fair.ARMS),
        "prospective_regimes":list(fair.REGIMES),
        "common_initial_read_calls_per_trial":1,
        "one_shot_max_tool_calls_including_read":2,
        "one_shot_max_candidate_submissions":1,
        "feedback_max_tool_calls_including_read":25,
        "feedback_max_candidate_submissions":24,
        "model_facing_raw_stdout_stderr_traceback_from_I_allowed":False,
        "model_facing_original_author_task_score_allowed":False,
        "feedback_engine_status_classes":list(fair.FEEDBACK_CLASSES),
        "same_source_only_read_envelope_proposed_for_all_arms":True,
        "identical_source_information_to_I_runtime":False,
        "same_native_operation_capabilities_D_vs_I":False,
        "causal_claim_representation_only_currently_admissible":False,
        "system_workflow_comparison_future_possible_subject_to_gates":True,
        "proposed_model_snapshot":None,
        "proposed_provider_name":None,
        "proposed_decoding_params":None,
        "proposed_context_or_completion_token_cap":None,
        "proposed_price_USD_per_million_tokens":None,
        "proposed_owner_budget_USD":None,
        "independently_certified_blind_original_sources":0,
        "original_IFC_per_file_external_transfer_rights_verified":False,
        "native_IFC_provider_upload_or_retention_allowed":False,
        "authorized_new_paid_or_free_model_generation_trials":0,
        "frozen_cohort_selected_for_confirmatory_study":False,
        "billing_by_real_provider_token_usage_verified":False,
        "cost_of_actual_billed_provider_tokens":None,
        "hard_original_provider_launch_gate_retained":True,
    }


def build_report():
    need(file_hash(FROZEN_WINDOW)==WINDOW_SHA
         and file_hash(FROZEN_V065)==V065_SHA,
         "Previously frozen IFC source/control report SHA unexpectedly changed")
    rows={r["test_id"]:r for r in v065.public_45(v065.AUTHOR,v065.DATA)}
    need(all(task in rows for task in
             (*SOURCE_EXPOSED_DOOR,*SOURCE_EXPOSED_WINDOW)),
         "Four developer-exposed original IFC source IDs no longer available")
    cases=_door_cases(rows)+_window_cases(rows)
    need(len(cases)==6
         and len({c["native_original_IFC_SHA256"] for c in cases})==4
         and {c["schema"] for c in cases}=={"IFC2X3","IFC4X3"},
         "Expected four developer-exposed original source clusters and 6 cases")
    need({c["operation_family"] for c in cases}=={"create","move","delete"},
         "Expected 3 native edit operation families")
    blockers=_budgets_and_blockers()
    schemas={arm:fair.model_tool_schema_bytes(arm) for arm in fair.ARMS}
    return {
        "status":"V066_PROSPECTIVE_THREE_ARM_OFFLINE_BYTES_AND_TOOL_FAIRNESS_AUDIT_PASS_BUT_MODEL_TRIAL_BLOCKED",
        "issue":247,
        "audit_kind":"PROSPECTIVE_NOT_ACTIVE_OR_PREREGISTERED_MODEL_TRIAL",
        "frozen_prior_window_control_report_SHA256":WINDOW_SHA,
        "frozen_prior_v065_control_report_SHA256":V065_SHA,
        "actual_original_developer_exposed_unique_IFC_source_SHA_clusters":4,
        "actual_source_operation_rows":6,
        "actual_native_schema_coverage":["IFC2X3","IFC4X3"],
        "actual_edit_family_coverage":["create","delete","move"],
        "measured_artifacts":"exact UTF8 source FULL/MANAGED XML, proposed common read JSON envelope, actual developer D_FULL, D_MANAGED and Python I submissions, proposed tool JSON schemas, native original IFC file sizes",
        "proposed_tool_schema_SHA256_by_arm":{
            arm:sha256(schemas[arm]).hexdigest() for arm in fair.ARMS},
        "proposed_tool_schema_metrics_by_arm":{
            arm:fair.byte_metrics(schemas[arm]) for arm in fair.ARMS},
        "naive_token_proxy_definition":
            "ceiling(UTF8_byte_length / 4) and ceiling(Unicode_codepoint_length / 4), displayed only as rough size indicators; not any actual model tokenizer, not provider usage or pricing",
        "missing_actual_tokenizer_name":None,
        "actual_billed_input_output_cached_reasoning_tokens":None,
        "actual_paid_USD":0,
        "new_model_provider_API_calls":0,
        "source_original_IFC_uploaded_externally":False,
        "original_task_author_grader_or_hidden_GT_accessed":False,
        "proposed_tool_contract_source_SHA256":file_hash(
            ROOT/"tools"/"bibimbap_v066_prospective_fairness_contract.py"),
        "prospective_design_and_hard_scientific_blockers":blockers,
        "exposed_source_operation_byte_rows":cases,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    args=p.parse_args()
    raw=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(raw)
    else:
        need(REPORT.read_bytes()==raw,
             "Prospective three-arm size/tool fairness report not byte-identical")
    print("V066_THREE_ARM_FAIRNESS_"+("WRITE" if args.write else "CHECK")+
          "=PASS source_SHA_clusters=4 source_operation_rows=6 "
          "tool_arms=3 model_calls=0 rights=BLOCKED")


if __name__=="__main__":
    main()
