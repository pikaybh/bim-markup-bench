"""Read-only audit of exactly frozen 45 original BIBIMBAP edit records.

Does not invoke a model, change/model-correct the source, run the original
grader, mutate product code, or convert failed attempts into successes.
Only basic XML-state semantic differences are measured independently.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from tools.audit_bibimbap_test05_real_semantic import analyze
from tools.run_bibimbap_full45_luna import (
    ROOT, RUN_ROOT, COHORT_REPORT, MANIFEST, ORIGINAL_PILOT, _load,
    APPROVED_CAP_USD,
)
from tools.bibimbap_public_packet import sha

AUDIT_REPORT = ROOT / "reports" / "bibimbap_original45_luna_semantic_audit_20261112.json"
OLD_START = "PUBLIC SOURCE PROJECTION (building.xml):\n"
OLD_END = "\n\nPUBLIC EXPERIMENTAL XML GRAMMAR:"

def audit() -> dict:
    cohort = _load(COHORT_REPORT)
    prep = _load(MANIFEST)
    if len(cohort["individual_results"]) != 45 or len(prep["frozen_population"]) != 45:
        raise ValueError("45-row cohort manifest drift")
    rows = cohort["individual_results"]
    if sum(r["model_calls_attempted"] for r in rows) != 36:
        raise ValueError("Original one-shot and exactly 35 new calls expected")
    if Decimal(cohort["cost_estimated_usd_including_prior_test05"])>=APPROVED_CAP_USD:
        raise ValueError("Cumulative paid spend estimate exceeds owner cap")
    observations=[]
    for row in rows:
        public={
            "test_id":row["test_id"],"status":row["status"],"crud":row["source_crud"],
            "category":row["source_category"],
            "author_score":row.get("author_score"),
            "author_noop_score":row.get("original_author_noop_score",0),
            "author_full_score":row["author_full_score"],
            "provider_attempts":row.get("model_calls_attempted",0),
            "xml_semantic_diff":None,
        }
        if row["test_id"]=="test_05":
            previous = _load(ROOT / "reports/bibimbap_test05_luna_semantic_diff_20261112.json")
            raw_old=_load(ORIGINAL_PILOT)
            if row["actual_model_output_sha256"] != raw_old["raw_model_output_sha256"]:
                raise ValueError("Prior model response changed")
            public["xml_semantic_diff"]=previous["difference"]
            public["model_source_preserved_sha256"]=previous["model_output_exact_sha256"]
        elif row["status"] in ("BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED",
                                "BLOCKED_PUBLIC_INPUT_TOO_LARGE",
                                "BLOCKED_NEW_SOURCE_PROJECTION_ERROR"):
            public["reason"]="NO_MODEL_EXPOSURE_ON_UNSUPPORTED_INPUT"
        else:
            folder=RUN_ROOT/row["test_id"]
            original_packet=folder/"public_packet.json"
            candidate=folder/"model_generated_exact.raw.txt"
            if not original_packet.is_file() or not candidate.is_file():
                public["reason"]="NOT_GENERATED_OR_MISSING_EVIDENCE"
                observations.append(public)
                continue
            packet=_load(original_packet)
            if sha(json.dumps(packet,sort_keys=True,ensure_ascii=False).encode("utf8")) != row["public_packet_sha256"]:
                raise ValueError("Original model-facing packet hash mismatch")
            raw=candidate.read_bytes()
            if sha(raw)!=row.get("model_generated_exact_sha256"):
                raise ValueError("Actual provider XML bytes modified after submission")
            public["model_source_preserved_sha256"]=sha(raw)
            body=packet["input"]
            source=body.split(OLD_START,1)[1].split(OLD_END,1)[0].encode("utf8")
            if sha(source)!=row["source_original_xml_state_sha256"]:
                raise ValueError("Model-visible IFC XML source projection drift")
            try:
                public["xml_semantic_diff"]=analyze(source,raw)
            except Exception as exc:
                public["reason"]="INVALID_XML_MODEL_OUTPUT"
                public["xml_parse_failure_type"]=type(exc).__name__
        observations.append(public)
    full=[x for x in observations if x["author_full_score"]]
    valid_mutations=[]
    for x in full:
        diff=x["xml_semantic_diff"]
        if not diff:
            continue
        some_change=(diff["new_id_count"]>0 or diff["dropped_existing_id_count"]>0 or
                     diff["modified_existing_id_count"]>0 or
                     not diff["old_relation_container_and_nonid_nodes_unchanged"])
        if some_change:
            valid_mutations.append(x["test_id"])
    never_call=[
        x["test_id"] for x in observations
        if x["status"]=="BLOCKED_UNSUPPORTED_SOURCE_PREDECLARED"
    ]
    no_op_base=sum((Decimal(str(x["author_noop_score"])) for x in observations),Decimal(0))/45
    author_avg=Decimal(str(cohort["mean_original_author_score_all45_zero_for_non_scored"]))
    return {
        "status":"REPRODUCIBLE_READ_ONLY_XML_SEMANTIC_AUDIT",
        "cohort_sha256":sha(COHORT_REPORT.read_bytes()),
        "preflight_sha256":sha(MANIFEST.read_bytes()),
        "raw_original_provider_outputs_preserved":True,
        "model_calls_this_audit":0,
        "total_original_edit_tasks":45,
        "total_actual_provider_calls_reused_and_new":36,
        "previous_one_shot_reused_once":True,
        "predeclared_unsupported_source_count":len(never_call),
        "unsupported_source_task_ids":never_call,
        "author_original_fullscore_tasks":[x["test_id"] for x in full],
        "author_original_fullscore_count":len(full),
        "author_original_fullscore_with_actual_xml_semantic_change_count":len(valid_mutations),
        "author_original_fullscore_with_actual_xml_semantic_change_task_ids":valid_mutations,
        "original_author_mean_score_45_zero_filled":str(author_avg),
        "original_author_noop_baseline_mean_45":str(no_op_base),
        "original_author_noop_scores_are_not_edit_success":True,
        "full_independent_strict_task_success_rate":None,
        "individual_source_differences":observations,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=audit()
    if args.output_json:
        if args.output_json.exists() or not args.output_json.parent.is_dir():
            parser.error("Refuse overwrite or missing destination")
        with args.output_json.open("xb") as f:
            f.write((json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8"))
    print(json.dumps({
        "status":report["status"],
        "author_original_fullscore_tasks":report["author_original_fullscore_tasks"],
        "original_author_noop_baseline_mean_45":report["original_author_noop_baseline_mean_45"],
        "original_author_mean_score_45_zero_filled":report["original_author_mean_score_45_zero_filled"],
        "model_calls_this_audit":0,
    },sort_keys=True))

if __name__=="__main__":
    main()
