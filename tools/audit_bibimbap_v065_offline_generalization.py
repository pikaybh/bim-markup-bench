"""v0.65 source-cluster leakage, cross-schema general adapter and NO-LAUNCH audit.

Reads existing 45 PUBLIC task metadata and frozen v0.58-v0.64 reports.
NEVER reads additional original heldout/unknown IFC geometry or any
unseen scorer. Uses only 2 already-exposed original IFC sources for
REAL native general D_FULL/managed/Docker-I tests (IFC2X3 and IFC4X3).
Records all 31 SHA source-cluster rights/leakage status; zero certified
blind sources. No provider/models/paid API/upload. Author-score caveats
are from PREVIOUS frozen audits, not new evaluator access.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
import re
import shutil
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor,file_hash,PINNED_DOCKER_IMAGE,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)
from tools import audit_bibimbap_v063_original_exterior_door_DI as a063
from tools import audit_bibimbap_v064_ifc2x3_north_door_DI as a064
from tools.bibimbap_v065_source_neutral_door import (
    Q,STATUS,source_model,full_initial_xml,managed_initial_xml,
    parse_full_xml,expand_managed_xml,compile_hosted_door,post_native_ifc_gate,
    semantic_digest,_box_attrs,
)
from tools.bibimbap_v065_offline_trial_admission import (
    proposal_manifest,deny_original_model_trial,TrialBlocked065,canonical,
)

ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\文書\D__1_Projects\202611")  # overwritten to use normal Windows path below
BASE=Path("D:/문서/D__1_Projects/202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v065_source_neutral_cross_schema_leakage_no_launch_20261118.json"
PARENT64=ROOT/"reports"/"bibimbap_v064_original_ifc2x3_north_door_native_DI_20261118.json"
PARENT63=ROOT/"reports"/"bibimbap_v063_original_external_door_csg_native_DI_20261118.json"
FROZEN58=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
SHA64="0499d218d2da2dcb5277c36ce33ae2fcb93ca40ef41fa0c9b079270e5ad7669d"
SHA63="77ea754501be7142319b425d31f17fd60b1ade9addb724ace4ecf7b70aba2437"
SHA58="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
PARENT_HEAD="a20bcc5fa6bf3ad4de0f18c9b6d79acb8b3d498d"
AUTHOR_HEAD="667004e16bd38fd7d538bcee56191465429fd975"
OLDER_VERIFIED={"geometry_test_14","geometry_test_15",
                "topological_test_11","topological_test_17"}
FIXED_SIX={"geometry_test_03","geometry_test_13","geometry_test_19",
           "topological_test_05","topological_test_12","topological_test_18"}
CONFIRMED_EXPOSED=OLDER_VERIFIED|FIXED_SIX
EXPOSURE_LABEL="EXPOSED_SOURCE_DEVELOPER_IMPLEMENTED_AUTHOR_METRICS"
QUARANTINE_LABEL="NOT_CERTIFIED_UNSEEN_CATALOG_METADATA_PRESENT"
SEED="v065-independent-public-source-SHA-quarantine-NO-TRIAL-20261118"


def need(ok,why):
    if not ok:raise AssertionError(why)


def source_registry(v058):
    rows=v058["all_original_45_task_capability_matrix"]
    need(len(rows)==45 and len({r["original_test_id"] for r in rows})==45,
         "Frozen v058 original 45 public task registry drifted")
    clusters=defaultdict(list)
    for row in rows:
        sha=row["source_cluster_ifc_SHA256"]
        need(re.fullmatch(r"[0-9a-f]{64}",sha) is not None,
             "Original public source SHA invalid")
        clusters[sha].append(row)
    need(len(clusters)==31 and
         sorted(Counter(len(v) for v in clusters.values()).items())==[(1,30),(15,1)],
         "Original-source family 31/45 clustering drifted")
    result=[]
    for sha,group in sorted(clusters.items()):
        names=sorted(x["original_test_id"] for x in group)
        exposed=bool(set(names)&CONFIRMED_EXPOSED)
        need(len({x["original_input_native_schema"] for x in group})==1
             and len({x["original_input_IFC_relative_path"] for x in group})==1,
             "One original source SHA must have one schema and relative path")
        row=group[0]
        result.append({
            "original_source_ifc_SHA256":sha,
            "source_original_relative_path":row["original_input_IFC_relative_path"],
            "original_schema":row["original_input_native_schema"],
            "source_task_count":len(names),
            "original_public_task_ids":names,
            "original_task_categories":sorted({r["category"] for r in group}),
            "original_task_CRUD":sorted({r["original_crud"] for r in group}),
            "source_task_question_SHA256":{
                r["original_test_id"]:r["original_question_SHA256"]
                for r in group},
            "former_v058_original_cluster_assignment":v058[
                "source_cluster_registry"][sha]["assignment"],
            "v065_updated_exposure_classification":
                EXPOSURE_LABEL if exposed else QUARANTINE_LABEL,
            "developer_control_source_tasks_observed":
                sorted(set(names)&CONFIRMED_EXPOSED),
            "original_source_family_seen_by_earlier_catalog_metadata":True,
            "unseen_source_confirmed_by_independent_fresh_auditor":False,
            "independent_new_source_ITT_admission":False,
            "source_original_IFC_creator_chain_of_title_documented":False,
            "per_original_IFC_license_proven":False,
            "original_IFC_attribution_records_complete":False,
            "external_model_provider_upload_rights_verified":False,
            "external_model_provider_retention_rights_verified":False,
            "source_external_provider_trial": "BLOCKED",
        })
    need(len(result)==31,"Source-family rights ledger incomplete")
    return result


def select_quarantined_metadata_candidates(clusters):
    """Freeze only metadata staging order; NOT a blinded test set.

    Stratify across source schema, original task CRUD, task category;
    NEVER open unseen source IFC, grader or infer missing functionality.
    The source-family SHA is the unit and cannot cross candidate splits.
    """
    untouched=[row for row in clusters
               if row["v065_updated_exposure_classification"]==QUARANTINE_LABEL]
    groups=defaultdict(list)
    for row in untouched:
        for crud in row["original_task_CRUD"]:
            for cat in row["original_task_categories"]:
                groups[(row["original_schema"],crud,cat)].append(row)
    # deterministic purely public source SHA clustering, no author grade.
    seeded=random.Random(SEED)
    priority=[
        ("IFC2X3","create","geometry"),
        ("IFC4","create","geometry"),
        ("IFC4X3","create","geometry"),
        ("IFC4X3","update","geometry"),
        ("IFC4X3","delete","topological"),
        ("IFC4X3","create","topological"),
    ]
    selected=[]
    for bucket in priority:
        eligible=sorted(groups.get(bucket,[]),
                        key=lambda r:r["original_source_ifc_SHA256"])
        eligible=[c for c in eligible if c["original_source_ifc_SHA256"]
                  not in {r["original_source_ifc_SHA256"] for r in selected}]
        if eligible:selected.append(eligible[seeded.randrange(len(eligible))])
    return {
        "status":"METADATA_ONLY_QUARANTINE_CANDIDATES_NOT_BLIND_NOT_ADMITTED",
        "stratification_buckets_requested":[list(x) for x in priority],
        "candidate_SHA_and_task_ids":[{
            "source_ifc_SHA256":r["original_source_ifc_SHA256"],
            "original_task_ids":r["original_public_task_ids"],
            "schema":r["original_schema"],
            "crud":r["original_task_CRUD"],
            "category":r["original_task_categories"],
            "rights_approved":False,
            "independent_blind_certified":False,
        } for r in selected],
        "source_family_cluster_disjoint":len({
            r["original_source_ifc_SHA256"] for r in selected})==len(selected),
        "no_candidate_source_geometry_read_in_v065":True,
        "no_candidate_author_grader_read_in_v065":True,
        "candidate_task_scoring_or_provider_trial_admitted":False,
        "seed":SEED,
    }


def _guid(schema,which):
    return ifcopenshell.guid.compress(
        uuid.uuid5(uuid.NAMESPACE_DNS,
                   "v065-SOURCE-NEUTRAL-LOCAL-DEVELOPER-ONLY-"+schema+"-"+which).hex)


def _flat(box):
    return tuple(v for lo,hi in box for v in (lo,hi))


def _case_fixture(model,schema):
    """Only engineering-EXPOSED source model fixture in evaluator audit.

    These known source placements are kept OUT of generic model-facing
    compiler and trial gate. Demo is not blind/external/representative.
    """
    if schema=="IFC2X3":
        host=next(w for w in model.by_type("IfcWall")
                  if abs(w.ObjectPlacement.RelativePlacement.Location.Coordinates[1]-1600.)<1)
        opening=((-0.475,0.475),(1.4,1.8),(0.,2.2))
        door=((-0.45,0.45),(1.575,1.620),(0.,2.1))
    elif schema=="IFC4X3":
        host=next(w for w in model.by_type("IfcWall")
                  if abs(w.ObjectPlacement.RelativePlacement.Location.Coordinates[1]-100.)<1)
        opening=((3.6,4.55),(-.1,.3),(0.,2.2))
        door=((3.625,4.525),(.075,.120),(0.,2.1))
    else:raise AssertionError("Two exposed-source schemas only")
    return {
        "host":host.GlobalId,
        "opening_guid":_guid(schema,"opening"),
        "door_guid":_guid(schema,"door"),
        "axis":"X",
        "opening_box":opening,
        "door_box":door,
    }


def _final_xml(initial,st,managed=False):
    elem=etree.fromstring(initial)
    target=elem[1] if managed else elem[2]
    etree.SubElement(target,Q+"Opening",{
        "guid":st["opening_guid"],
        "hostOriginalWallGuid":st["host"],
        **_box_attrs(st["opening_box"]),
    })
    etree.SubElement(target,Q+"Door",{
        "guid":st["door_guid"],
        "fillsOpeningGuid":st["opening_guid"],
        **_box_attrs(st["door_box"]),
    })
    return etree.tostring(elem,encoding="utf8",xml_declaration=True)


def _real_independent_I_python(st,model):
    old={
        "axis":st["axis"],
        "host_guid":st["host"],
        "door_guid":st["door_guid"],
        "opening_guid":st["opening_guid"],
        "door_bbox":_flat(st["door_box"]),
        "opening_bbox":_flat(st["opening_box"]),
    }
    idx=sorted(model.by_type("IfcWall"),key=lambda w:w.GlobalId).index(
        model.by_guid(st["host"]))
    if model.schema=="IFC2X3":
        code=a064._independent_live_python_code_v064(old,idx)
    else:
        code=a063._developer_real_python_code(old,idx)
    need("commit()" in code
         and "data.tests" not in code
         and "target_guid" not in code.lower()
         and "private_target" not in code.lower()
         and "original_author" not in code.lower(),
         "Real developer Python must be independent source-only, no grader or GT")
    return code


def prove_cross_schema_local_sources():
    all_rows={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    cases=[]
    with TemporaryDirectory(prefix="v065-OFFLINE-real-IFC2x3-4x3-") as t:
        tmp=Path(t)
        for i,task in enumerate(("geometry_test_03","topological_test_05")):
            row=all_rows[task]
            original=DATA/"ifc"/row["original_source_ifc_relpath"]
            sha=row["original_ifc_sha256"]
            model=source_model(original,sha)
            state=_case_fixture(model,model.schema)
            initial=full_initial_xml(original,sha)
            managed=managed_initial_xml(original,sha)
            complete=_final_xml(initial,state)
            compact=_final_xml(managed,state,managed=True)
            interpreted=parse_full_xml(original,sha,complete)
            expanded,compact_state=expand_managed_xml(original,sha,compact)
            need(interpreted==compact_state==state
                 and expanded==complete,
                 "Source-independent full/managed D physical final-state mismatch")
            work=tmp/f"exposed-schema-case-{i}"
            work.mkdir()
            D=work/"D_FULL.ifc"
            M=work/"D_MANAGED.ifc"
            compile_hosted_door(original,sha,interpreted,D)
            compile_hosted_door(original,sha,compact_state,M)
            verdict_D=post_native_ifc_gate(original,sha,D)
            verdict_M=post_native_ifc_gate(original,sha,M)
            need(verdict_D["status"]==verdict_M["status"]==STATUS,
                 "Source-neutral independently real IFC2X3/IFC4X3 D native gate fail")
            # This is genuinely general Python in pinned LOCAL Docker,
            # not calling D compiler or task-specific D source-native gate.
            pre=live_pinned_local_runtime_admission_v052()
            need(pre["status"]=="RUNTIME_ADMITTED",
                 "Genuine local Linux Docker runtime not attested")
            sandbox=work/"I_NATIVE"
            sandbox.mkdir()
            result_file=sandbox/"current.ifc"
            shutil.copyfile(original,result_file)
            executor=DockerIFCExecutor()
            need(type(executor) is DockerIFCExecutor,
                 "Actual pinned OS-isolated Docker IFC executor required")
            source_code=_real_independent_I_python(state,model)
            run=executor.run(sandbox,source_code)
            need(run["status"]=="ok"
                 and run.get("committed") is True
                 and run.get("backend")=="linux_docker_sandbox",
                 "Independent I Python not genuinely executed in pinned local Linux Docker")
            verdict_I=post_native_ifc_gate(original,sha,result_file)
            need(verdict_I["status"]==STATUS
                 and file_hash(original)==sha,
                 "Unmodified original IFC source or native schema gate rejected I")
            d=[semantic_digest(x) for x in (verdict_D,verdict_M,verdict_I)]
            need(d[0]==d[1]==d[2],
                 "Genuine source-neutral D/I IFC semantics disagree")
            cases.append({
                "technical_developer_exposed_task_id":task,
                "original_source_schema":model.schema,
                "original_source_sha256":sha,
                "original_initial_full_XML_utf8_bytes":len(initial),
                "original_managed_initial_XML_utf8_bytes":len(managed),
                "new_full_final_state_XML_utf8_bytes":len(complete),
                "new_managed_final_state_XML_utf8_bytes":len(compact),
                "all_three_equivalent_original_IFC_native_semantic_SHA256":d[0],
                "native_actual_full_wall_CSG_removed_m3":
                    verdict_D["actual_wall_csg_volume_removed_m3"],
                "original_native_STEP_entities_preserved":
                    verdict_D["original_ifc_source_step_entities_unchanged"],
                "new_native_IFC2X3_IFC4X3_schema_errors":0,
                "same_task_independent_source_neutral_D_Full_Managed_I_admitted":True,
                "real_pinned_linux_docker_general_python_run":True,
                "original_host_guid_redacted":True,
                "original_new_root_guids_redacted":True,
                "author_repository_grader_not_reinvoked":True,
                "model_provider_calls":0,
            })
    return cases


def source_grammar_inventory():
    """Grounded in actual committed source; no heldout scorer imports."""
    targets={
        "v050_original_declarative":
            ["tools/bibimbap_v050_direct_original_state_session.py"],
        "v055_primary":
            ["tools/bibimbap_v055_transactional_primary_DI_sessions.py"],
        "v057_managed":
            ["tools/bibimbap_v057_managed_final_state_session.py"],
        "v059_space_delete":
            ["tools/bibimbap_v059_topo18_native.py",
             "tools/bibimbap_v059_topo18_sessions.py"],
        "v060_window_delete":
            ["tools/bibimbap_v060_geometry19_native.py",
             "tools/bibimbap_v060_geometry19_sessions.py"],
        "v061_window_move":
            ["tools/bibimbap_v061_geometry13_native.py",
             "tools/bibimbap_v061_geometry13_sessions.py"],
        "v062_wall_shorten":
            ["tools/bibimbap_v062_topology12_native.py",
             "tools/bibimbap_v062_topology12_sessions.py"],
        "v063_ifc4x3_door_create":
            ["tools/bibimbap_v063_exterior_door_native.py",
             "tools/bibimbap_v063_exterior_door_sessions.py"],
        "v064_ifc2x3_door_create":
            ["tools/bibimbap_v064_ifc2x3_north_door_native.py",
             "tools/bibimbap_v064_ifc2x3_north_door_sessions.py"],
        "v065_generic_hosted_door_create":
            ["tools/bibimbap_v065_source_neutral_door.py"],
    }
    out=[]
    for family,files in sorted(targets.items()):
        parts=[]
        for fn in files:
            f=ROOT/fn
            need(f.is_file(),"Original native source-controlled code missing "+fn)
            parts.append(f.read_text(encoding="utf8"))
        blob="\n".join(parts)
        names=[]
        for textlabel in (
            "D_COMPLETE_XML","D_MANAGED_FINAL_STATE",
            "execute_ifc_code","submit_building_xml","submit_managed_final_state",
            "IFC4X3","IFC2X3","GlobalId","SOURCE_SHA",
            "native_ifc_schema","original_author","data.tests",
            "IfcRelVoidsElement","IfcRelFillsElement",
            "_native_entity_signature_v060","source_ifc_sha256",
        ):
            if textlabel in blob:names.append(textlabel)
        out.append({
            "source_adapter_family":family,
            "original_committed_module_files":files,
            "module_SHA256":{fn:file_hash(ROOT/fn) for fn in files},
            "source_code_literal_features_observed":names,
            "source_specific_contract_or_shape_assumptions":
                ("per-task native source-specific code; NOT general" if family not in
                 ("v050_original_declarative","v055_primary","v057_managed",
                  "v065_generic_hosted_door_create") else
                 "bounded independent original family; review full code limits"),
            "independent_model_generated_trial_confirmed":False,
        })
    need(len(out)==len(targets),"Source grammar inventory incomplete")
    return out


def build_report():
    for path,digest in ((PARENT64,SHA64),(PARENT63,SHA63),(FROZEN58,SHA58)):
        need(file_hash(path)==digest,
             "Frozen existing original source benchmark report SHA drift")
    v058=json.loads(FROZEN58.read_text("utf8"))
    v064=json.loads(PARENT64.read_text("utf8"))
    v063=json.loads(PARENT63.read_text("utf8"))
    need(v064["original_fixed_six_now_developer_technically_supported_count"]==6
         and v064["actual_LLM_generated_model_trials"]==0
         and v063["actual_model_generated_trials"]==0,
         "Original research prior source-exposure claims drift")
    import subprocess
    current=subprocess.check_output(
        ["git","-C",str(AUTHOR),"rev-parse","HEAD"],text=True).strip()
    need(current==AUTHOR_HEAD,"Original pinned author evaluator checkout revision drift")
    license_names=("LICENSE","LICENSE.txt","LICENSE.md","LICENSE.rst",
                   "COPYING","COPYING.txt")
    recognized=[x for x in license_names if (AUTHOR/x).is_file()]
    need(not recognized,"Pinned author code license unexpectedly changed; re-review")
    clusters=source_registry(v058)
    need(len({task for c in clusters for task in c["original_public_task_ids"]})==45,
         "Original source-cluster manifest loses tasks")
    exposed=[c for c in clusters if c["v065_updated_exposure_classification"]==EXPOSURE_LABEL]
    quarantined=[c for c in clusters if c["v065_updated_exposure_classification"]==QUARANTINE_LABEL]
    need(len(exposed)==10
         and len(quarantined)==21
         and len({task for c in exposed for task in c[
             "developer_control_source_tasks_observed"]})==10,
         "Known exposure 10 original distinct source families drifted")
    v058_six=set(v058["prospective_six_source_heldout_task_ids"])
    need(v058_six==FIXED_SIX
         and all(next(c for c in clusters if task in c[
             "original_public_task_ids"])["v065_updated_exposure_classification"]
                 ==EXPOSURE_LABEL for task in FIXED_SIX),
         "Former v058 untouched six NOW exposed; cannot remain blind")
    trial=select_quarantined_metadata_candidates(clusters)
    ledger_bytes=canonical({"source_cluster_ledger":clusters})
    manifest=proposal_manifest(sha256(ledger_bytes).hexdigest())
    try:
        deny_original_model_trial(
            original_ifc_upload_allowed=True,
            model_snapshot="FAKE_APPROVED",
            paid_cap_usd=1000000,
            fake_user_consent=True,
            all_rights_verified=True,
        )
        raise AssertionError("Unconditional original model firewall bypassed")
    except TrialBlocked065:
        pass
    generic=prove_cross_schema_local_sources()
    need(len(generic)==2
         and {r["original_source_schema"] for r in generic}=={"IFC2X3","IFC4X3"},
         "Two actual exposed original source schemas not validated")
    return {
        "status":"V065_OFFLINE_31_SOURCE_CLUSTER_LEAKAGE_2_SCHEMA_GENERAL_DOOR_CSG_REAL_DOCKER_NO_LAUNCH_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/245",
        "parent_v064_exact_git_head":PARENT_HEAD,
        "parent_v064_frozen_report_sha256":SHA64,
        "parent_v063_frozen_report_sha256":SHA63,
        "v058_original_cohort_frozen_sha256":SHA58,
        "original_repository_author_checkout_commit":AUTHOR_HEAD,
        "original_author_checkout_license_file_recognized":False,
        "original_author_README_references_LICENSE_but_no_actual_file":True,
        "original_author_repo_code_redistribution_permission_VERIFIED":False,
        "original_paper_publication_url":"https://ec-3.org/publication/ec32026_271/",
        "paper_official_scorer_vs_pinned_checkout_parity_VERIFIED":False,
        "paper_official_best_baseline_score_not_comparable_to_45_edit_subset":True,
        "dataset_card_identifier":"clemenskujat/bibimbap-data",
        "dataset_card_license_label_only":"cc-by-4.0",
        "source_original_IFC_per_file_license_chain_of_title_verified":False,
        "original_IFC_per_file_model_provider_upload_or_retention_authorized":False,
        "original_unique_source_sha_clusters":31,
        "original_public_edit_task_count":45,
        "original_crud_task_counts":v058["original_crud_counts"],
        "original_source_schema_task_counts":v058["source_input_schema_task_counts"],
        "original_source_schema_unique_clusters":
            v058["source_input_schema_unique_cluster_counts"],
        "original_one_IFC_source_shared_by_fifteen_basic_tasks":True,
        "actual_developer_exposed_source_clusters_count":10,
        "source_clusters_catalogued_but_NOT_CERTIFIED_unseen":21,
        "certified_independent_unseen_confirmatory_clusters":0,
        "v058_former_prespecified_six_are_NOW_developer_exposed":True,
        "v058_former_six_no_longer_blind_and_cannot_be_preserved_as_holdout":True,
        "original_source_cluster_leakage_ledger_sha256":
            sha256(ledger_bytes).hexdigest(),
        "original_source_per_file_rights_ledger":clusters,
        "potential_new_quarantined_candidate_metadata_only":trial,
        "zero_quarantine_candidate_geometry_or_grader_reads":True,
        "native_D_I_prior_adapter_code_inventory":source_grammar_inventory(),
        "source_neutral_adapter_function_source_code_SHA256":
            file_hash(ROOT/"tools"/"bibimbap_v065_source_neutral_door.py"),
        "source_neutral_supported_edit_family":
            "ONE_HOSTED_NATIVE_IFCDOOR_PLUS_IFCOPENING_IFC2X3_OR_IFC4X3",
        "source_neutral_initial_XML_identical_D_Full_Managed_I_plan":True,
        "source_neutral_real_developer_exposed_original_IFC_models_tested":2,
        "source_neutral_real_original_IFC_edits_D_full_managed":4,
        "source_neutral_real_original_IFC_edits_Docker_I":2,
        "source_neutral_actual_new_IFC2X3_IFC4X3_schema_errors":0,
        "source_neutral_strict_STEP_ID_and_five_new_roots_may_bias_general_I":True,
        "source_neutral_not_universal_for_moves_deletions_or_non_axis_aligned":True,
        "real_genuine_pinned_local_Linux_Docker_image":PINNED_DOCKER_IMAGE,
        "source_neutral_developer_only_two_source_cross_schema_controls":generic,
        "source_author_scorer_known_discrepancies":[
            {
                "task":"topological_test_05",
                "pinned_earlier_report_SHA256":SHA63,
                "claim":"Author repo gives 1.0 both genuine exterior and interior Door; public outer-envelope proxy fails interior. No source IfcSpace.",
                "published_official_scorer_equivalence":False,
            },
            {
                "task":"geometry_test_19",
                "claim":"Pinned author's grader references GUID absent from original IFC; no official score inferred.",
                "published_official_scorer_equivalence":False,
            },
            {
                "task":"topological_test_17",
                "claim":"Original repo non-target integrity check rejects lawful dependent property/type cascade: correct deletion author's score 0.50.",
                "published_official_scorer_equivalence":False,
            },
            {
                "task":"geometry_test_03",
                "pinned_earlier_report_SHA256":SHA64,
                "claim":"Original author grader distinguishes nearest +Y (1.0) from farther +Y (score below 1), native IFC2X3 full CSG both valid.",
                "published_official_scorer_equivalence":False,
            },
        ],
        "offline_non_registered_provider_trial_candidate_manifest":manifest,
        "original_IFC_provider_upload_count":0,
        "paid_or_unpaid_model_generation_calls_count":0,
        "actual_model_generated_attempts_count":0,
        "actual_billed_provider_tokens":None,
        "actual_paid_model_cost_USD":0,
        "hard_unconditional_no_provider_launcher_even_forged_all_true":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--write",action="store_true")
    opts.add_argument("--check",action="store_true")
    args=parser.parse_args()
    report=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:f.write(report)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==report,
             "Actual local 2-source pinned Docker and 31-source ledger replay drift")
    print("V065_OFFLINE_GENERALIZATION_SOURCE_CLUSTER_AND_NO_LAUNCH=PASS "
          "SOURCES=31 EXPOSED=10 CERTIFIED_BLIND=0 "
          "GENERIC_NATIVE_IFC2X3_IFC4X3=2 "
          "ACTUAL_PINNED_DOCKER_I=2 TRIAL_CALLS=0 "
          "REPORT_SHA256="+sha256(report).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
