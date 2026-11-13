"""Read-only, evidence-tiered 45-task capability matrix (BIBIMBAP).

No model invocation, no edits to original BIBIMBAP data or Xim, and NO
publication of original author's hidden evaluator/GT. The hand-curated task
taxonomy comes ONLY from the 45 public original instructions. Classification
of task support is prospective/structural, NOT LLM success or D0 oracle proof.

Optional --replay-dir replays *frozen, previously billed* XML text to isolate
trusted compiler reasons in a disposable directory. This never resubmits to a
model or changes the original historical report.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash,ROOT
from src.runtime.compiler import compile_declarative_xml

BASELINE=ROOT/"reports"/"bibimbap_original45_luna_20261112.json"
SOURCE_PROTOCOL=ROOT/"docs"/"protocol"/"bibimbap_matched25_agentic_xml_vs_python_20261112.md"
COMPILER=ROOT/"src"/"runtime"/"compiler.py"
OPERATIONS=ROOT/"src"/"runtime"/"ifc_mutations.py"
GRAMMAR=ROOT/"spec"/"toy_markup_v0.xsd"
SOURCE=ROOT/"src"/"runtime"/"ifc_projection.py"
OUT=ROOT/"reports"/"bibimbap45_capability_audit_20261113.json"

# Public-question-derived expert taxonomy. A single row describes the exact
# *required kind of edit*, never an intended answer or target geometry.
#
# XML = schema can state desired geometry/relationship; conditional means
# geometry or relation ownership must be proven on actual source.
# Capability = static compiler support for a class of change, NOT task pass.
#
# All 45 rows are pinned to the original edit cohort IDs; adding an easy
# alternate task or removing an unprojectable row is a hard failure.
#
# Fields: (public requirement key, IFC target types, schema expressivity,
#          code operation family, source native compiler gate, blocker key).
SPEC={
    "test_01":("door_in_host_wall",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","CREATE_DOOR_WITH_VOID","MISSING","HOSTED_DOOR_CREATION"),
    "test_02":("rectangular_slab_create",("IfcSlab",),"YES","CREATE_SLAB","MISSING","SLAB_CREATION"),
    "test_03":("slab_center_opening_create",("IfcOpeningElement","IfcSlab"),"NO","SLAB_VOID_CREATE","MISSING","SLAB_HOSTED_OPENING_SCHEMA"),
    "test_04":("column_create",("IfcColumn",),"YES","CREATE_COLUMN","MISSING","COLUMN_CREATION"),
    "test_05":("straight_wall_create",("IfcWall",),"YES","CREATE_WALL","IMPLEMENTED_SUBSET","WALL_CREATE_NATIVE"),
    "test_11":("rotate_wall_about_z",("IfcWall",),"YES","ROTATE_WALL","MISSING","WALL_PLANAR_POSE_CHANGE"),
    "test_12":("move_hosted_door_x",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","MOVE_DOOR","MISSING","DOOR_WITH_OPENING_MOVE"),
    "test_13":("window_height_increase",("IfcWindow",),"YES","UPDATE_WINDOW_HEIGHT","MISSING","WINDOW_HEIGHT_UPDATE"),
    "test_14":("slab_height_decrease",("IfcSlab",),"CONDITIONAL","UPDATE_SLAB_HEIGHT","MISSING","SLAB_DIMENSION_UPDATE"),
    "test_15":("move_column_y",("IfcColumn",),"YES","MOVE_COLUMN","MISSING","COLUMN_PLACEMENT"),
    "test_16":("delete_column",("IfcColumn",),"YES","DELETE_COLUMN","MISSING","COLUMN_DELETE"),
    "test_17":("delete_door",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","DELETE_DOOR_WITH_OPENING","CONDITIONAL","HOSTED_PAIR_CASCADE"),
    "test_18":("delete_opening",("IfcOpeningElement",),"CONDITIONAL","DELETE_HOSTED_OPENING","MISSING","STANDALONE_OPENING_DELETE"),
    "test_19":("delete_wall",("IfcWall",),"YES","DELETE_WALL","CONDITIONAL","WALL_WITH_DEPENDENTS"),
    "test_20":("delete_room",("IfcSpace",),"YES","DELETE_SPACE","MISSING","SPACE_DELETE"),
    "geometry_test_01":("create_slab_over_columns",("IfcSlab","IfcColumn"),"CONDITIONAL","CREATE_SLAB","MISSING","SLAB_CREATION"),
    "geometry_test_02":("create_column_centroid_walls",("IfcColumn",),"YES","CREATE_COLUMN","MISSING","COLUMN_CREATION"),
    "geometry_test_03":("create_door_north_wall",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","CREATE_DOOR_WITH_VOID","MISSING","HOSTED_DOOR_CREATION"),
    "geometry_test_04":("create_space_left_of_column",("IfcSpace",),"CONDITIONAL","CREATE_SPACE","MISSING","SPACE_CREATION"),
    "geometry_test_05":("wall_in_empty_project",("IfcWall",),"YES","CREATE_WALL","IMPLEMENTED_SUBSET","SCHEMA_INPUT_IFC4"),
    "geometry_test_11":("all_storey2_wall_height_minus05",("IfcWall",),"YES","UPDATE_WALL_HEIGHT","IMPLEMENTED_SUBSET","WALL_HEIGHT_UPDATE"),
    "geometry_test_12":("rotate_wall_45deg_center",("IfcWall",),"YES","ROTATE_WALL","MISSING","WALL_PLANAR_POSE_CHANGE"),
    "geometry_test_13":("move_wide_window_global_x",("IfcWindow","IfcOpeningElement"),"CONDITIONAL","MOVE_OPENING_WITH_FILLING","CONDITIONAL","GLOBAL_DIRECTION_VS_HOST_OFFSET"),
    "geometry_test_14":("square_slab_reshape",("IfcSlab",),"CONDITIONAL","RESHAPE_SLAB","MISSING","SLAB_DIMENSION_UPDATE"),
    "geometry_test_15":("relocate_columns_rectangular",("IfcColumn",),"YES","MOVE_COLUMN","MISSING","COLUMN_PLACEMENT"),
    "geometry_test_16":("delete_between_doors",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","DELETE_DOOR_WITH_OPENING","CONDITIONAL","HOSTED_PAIR_CASCADE"),
    "geometry_test_17":("delete_detached_exterior_walls",("IfcWall",),"YES","DELETE_WALL","CONDITIONAL","WALL_WITH_DEPENDENTS"),
    "geometry_test_18":("delete_west_wall_windows",("IfcWindow",),"CONDITIONAL","DELETE_WINDOW","CONDITIONAL","WINDOW_RELATIONAL_CASCADE"),
    "geometry_test_19":("delete_two_opposite_windows",("IfcWindow",),"CONDITIONAL","DELETE_WINDOW","CONDITIONAL","WINDOW_RELATIONAL_CASCADE"),
    "geometry_test_20":("delete_wall_nearest_column",("IfcWall",),"YES","DELETE_WALL","CONDITIONAL","WALL_WITH_DEPENDENTS"),
    "topological_test_01":("wall_enclose_room",("IfcWall","IfcSpace"),"CONDITIONAL","CREATE_WALL","CONDITIONAL","ROOM_TOPOLOGICAL_CLOSURE"),
    "topological_test_02":("column_inside_walls",("IfcColumn",),"YES","CREATE_COLUMN","MISSING","COLUMN_CREATION"),
    "topological_test_03":("wall_partition_two_rooms",("IfcWall","IfcSpace"),"CONDITIONAL","CREATE_WALL","CONDITIONAL","ROOM_SPACE_BOUNDARY_EFFECT"),
    "topological_test_04":("slab_closes_walls",("IfcSlab",),"CONDITIONAL","CREATE_SLAB","MISSING","SLAB_CREATION"),
    "topological_test_05":("door_connect_inside_outside",("IfcDoor","IfcOpeningElement"),"CONDITIONAL","CREATE_DOOR_WITH_VOID","MISSING","HOSTED_DOOR_CREATION"),
    "topological_test_11":("extend_columns_up_to_slab",("IfcColumn","IfcSlab"),"YES","UPDATE_COLUMN_HEIGHT","MISSING","COLUMN_HEIGHT_UPDATE"),
    "topological_test_12":("shorten_outer_wall",("IfcWall",),"YES","CHANGE_WALL_LENGTH","MISSING","WALL_PLANAR_POSE_CHANGE"),
    "topological_test_13":("move_window_to_wall_exterior",("IfcWindow","IfcOpeningElement"),"CONDITIONAL","MOVE_OPENING_WITH_FILLING","CONDITIONAL","HOSTED_OPENING_OFFSET_WITH_GLOBAL_RELATION"),
    "topological_test_14":("trim_beams_to_wall",("IfcBeam","IfcWall"),"NO","TRIM_BEAM","MISSING","BEAM_UNREPRESENTED"),
    "topological_test_15":("move_slab_onto_slab",("IfcSlab",),"CONDITIONAL","MOVE_SLAB","MISSING","SLAB_PLACEMENT"),
    "topological_test_16":("delete_wall_touching_two",("IfcWall",),"YES","DELETE_WALL","CONDITIONAL","WALL_WITH_DEPENDENTS"),
    "topological_test_17":("delete_columns_unrelated_slab",("IfcColumn",),"YES","DELETE_COLUMN","MISSING","COLUMN_DELETE"),
    "topological_test_18":("delete_room_enclosed",("IfcSpace",),"YES","DELETE_SPACE","MISSING","SPACE_DELETE"),
    "topological_test_19":("delete_column_inside_walls",("IfcColumn",),"YES","DELETE_COLUMN","MISSING","COLUMN_DELETE"),
    "topological_test_20":("delete_columns_outside_rooms",("IfcColumn",),"YES","DELETE_COLUMN","MISSING","COLUMN_DELETE"),
}

# Audited interpreter dispatch operation families, with source-dependent
# native limitations. This is not a substitute for per-task D0 model.
CODE_SUPPORTED={
    "CREATE_WALL":("CREATE_WALL",),
    "UPDATE_WALL_HEIGHT":("UPDATE_WALL_HEIGHT",),
    "DELETE_WALL":("DELETE_WALL",),
    "DELETE_WINDOW":("DELETE_WINDOW",),
    "DELETE_DOOR_WITH_OPENING":("DELETE_HOSTED_DOOR_OPENING",),
    "MOVE_OPENING_WITH_FILLING":("MOVE_OPENING_WITH_FILLING",),
}

BLOCKER_EXPLANATION={
    "HOSTED_DOOR_CREATION":"XML has Door/Opening but native compiler has no CREATE_DOOR_WITH_VOID handler",
    "SLAB_CREATION":"Schema has rectangular Slab but no native CREATE_SLAB transaction",
    "SLAB_HOSTED_OPENING_SCHEMA":"Opening.host is Wall-only; slab opening not representable",
    "COLUMN_CREATION":"Schema has Column but native CREATE_COLUMN handler absent",
    "WALL_CREATE_NATIVE":"Standalone straight Wall creation has positive native IFC fixture",
    "WALL_PLANAR_POSE_CHANGE":"Existing Wall x/y endpoint/rotation native mutation not supported",
    "DOOR_WITH_OPENING_MOVE":"Door + opening global translation, not general hosted slide operation",
    "WINDOW_HEIGHT_UPDATE":"Window height and filling/void native resizing unavailable",
    "SLAB_DIMENSION_UPDATE":"Native Slab thickness/edge reshape unsupported",
    "COLUMN_PLACEMENT":"Native Column placement change unavailable",
    "COLUMN_DELETE":"Native Column deletion and owned relations unavailable",
    "HOSTED_PAIR_CASCADE":"Compiler supports only narrowly eligible *paired* Door+Opening deletion, not general Door removal",
    "STANDALONE_OPENING_DELETE":"Opening-only delete/cascade unsupported by native compiler",
    "WALL_WITH_DEPENDENTS":"Native Wall deletion allowed only for narrow standalone eligibility, not generally connected/hosted walls",
    "SPACE_DELETE":"Native IfcSpace delete plus boundary/containment cleanup unavailable",
    "SPACE_CREATION":"General IfcSpace creation and boundaries unavailable (special bounded two-Space split is not equivalent)",
    "SCHEMA_INPUT_IFC4":"Actual original IFC4 input unsupported by IFC4X3-only projector",
    "WALL_HEIGHT_UPDATE":"Simple native swept-solid Wall height update implemented for eligible IFC4X3",
    "GLOBAL_DIRECTION_VS_HOST_OFFSET":"Can change hosted Opening.offset but global-X movement requires correct host orientation/projection",
    "WINDOW_RELATIONAL_CASCADE":"Some hosted Window deletion supported only with strict original void/filling/relationship eligibility",
    "ROOM_TOPOLOGICAL_CLOSURE":"Native Wall creation present but room enclosure and boundaries not guaranteed by author score",
    "ROOM_SPACE_BOUNDARY_EFFECT":"Native Wall creation possible but independent room separation/space boundaries unverified",
    "HOSTED_OPENING_OFFSET_WITH_GLOBAL_RELATION":"Native Opening.offset update present but spatial positioning and untouched geometry need independent verification",
    "COLUMN_HEIGHT_UPDATE":"Native Column profile height update unavailable",
    "BEAM_UNREPRESENTED":"IfcBeam not part of v0.1 managed XML schema",
    "SLAB_PLACEMENT":"Native Slab placement change unavailable",
}

def _single_sha(path:Path)->str:
    return file_hash(path)

def structural_45(author:Path,dataset:Path)->dict:
    public=public_45(author,dataset)
    previous=json.loads(BASELINE.read_text(encoding="utf8"))["individual_results"]
    old={x["test_id"]:x for x in previous}
    if len(public)!=45 or len(SPEC)!=45 or set(SPEC)!={x["test_id"] for x in public}:
        raise ValueError("Manual public-task taxonomy not exactly original 45 questions")
    if len(old)!=45 or set(old)!=set(SPEC):
        raise ValueError("Original actual 45-run evidence mismatch")
    native_text=OPERATIONS.read_text(encoding="utf8")+COMPILER.read_text(encoding="utf8")
    gram=GRAMMAR.read_text(encoding="utf8")
    for value in CODE_SUPPORTED.values():
        if any(v not in native_text for v in value):
            raise ValueError("Claimed compiler operation missing from source")
    for kind in ("Wall","Slab","Column","Space","Window","Door","Opening"):
        if f'name="{kind}"' not in gram:
            raise ValueError("Expected schema kind missing: "+kind)
    report_rows=[]
    seen_files={}
    for entry in public:
        k=entry["test_id"];require=SPEC[k]
        name,types,expressible,family,gate,blocker=require
        if gate=="MISSING" and family in CODE_SUPPORTED:
            raise ValueError("Manual compiler missing status contradicts actual dispatched operation")
        if gate in ("IMPLEMENTED_SUBSET","CONDITIONAL") and family not in CODE_SUPPORTED:
            raise ValueError("Manual supported status not matched by compiler operation family")
        if expressible=="NO" and gate!="MISSING":
            raise ValueError("Impossible XML declaration cannot have executable compiler gate")
        orig=dataset/"ifc"/entry["original_source_ifc_relpath"]
        source_hash=entry["original_ifc_sha256"]
        if file_hash(orig)!=source_hash:
            raise ValueError("Pinned original IFC hash mismatch")
        if source_hash not in seen_files:
            f=ifcopenshell.open(str(orig))
            classes=("IfcBuildingStorey","IfcWall","IfcSlab","IfcColumn",
                     "IfcDoor","IfcWindow","IfcSpace","IfcOpeningElement",
                     "IfcBeam","IfcRelVoidsElement","IfcRelFillsElement")
            seen_files[source_hash]={
                "schema":f.schema,
                "metres_per_ifc_length_unit":float(ifcopenshell.util.unit.calculate_unit_scale(f)),
                "source_class_counts":{c:len(f.by_type(c)) for c in classes},
            }
        sourceinfo=seen_files[source_hash]
        past=old[k]
        projected=(entry["xml_source_projection_previously_observed"]=="PROJECTABLE")
        if projected!=(past["source_projection_earlier"]=="PROJECTABLE"):
            raise ValueError("Historical projectability mismatch")
        if not projected:
            cause="SOURCE_PROJECTION_BLOCKED"
        elif expressible=="NO":
            cause="XML_DECLARATIVE_SCHEMA_GAP"
        elif gate=="MISSING":
            cause="NATIVE_COMPILER_MISSING"
        elif gate=="CONDITIONAL":
            cause="CONDITIONAL_BACKEND_WITHOUT_TASK_ORACLE"
        else:
            cause="SUPPORTED_SLICE_STRICT_TASK_UNVERIFIED"
        report_rows.append({
            "original_task_id":k,
            "crud":entry["crud"],"category":entry["category"],
            "public_question_sha256":entry["public_question_sha256"],
            "original_source_ifc_sha256":source_hash,
            "original_source_ifc_relpath":entry["original_source_ifc_relpath"],
            "original_ifc_schema":sourceinfo["schema"],
            "source_metres_per_length_unit":sourceinfo["metres_per_ifc_length_unit"],
            "original_ifc_type_inventory":sourceinfo["source_class_counts"],
            "public_task_requirement_key":name,
            "required_native_ifc_types":list(types),
            "required_native_mutation_family":family,
            "xml_schema_declaration_expressible":expressible,
            "compiler_native_operation_gate":gate,
            "compiler_dispatched_operations":list(CODE_SUPPORTED.get(family,())),
            "known_implementation_blocker_key":blocker,
            "known_implementation_blocker":BLOCKER_EXPLANATION[blocker],
            "source_xml_projectable_previously":projected,
            "source_projectability_reported_reason":entry["xml_source_preflight_issue"],
            "pre_model_oracle_eligibility_gate":cause,
            "historical_one_shot_status":past["status"],
            "historical_one_shot_author_score":past.get("author_score"),
            "historical_one_shot_author_full_mark":past.get("author_full_score",False),
            "previous_independent_strict_task_oracle_verified":False,
            "future_D0_end_to_end_oracle_proved":False,
            "existing_mutation_runtime_is_explicitly_restricted":True,
        })
    if len(report_rows)!=45 or len({x["original_task_id"] for x in report_rows})!=45:
        raise ValueError("Missing or duplicate original task")
    if sum(x["source_xml_projectable_previously"] for x in report_rows)!=36:
        raise ValueError("Frozen 36/9 projectability changed")
    by_gate=Counter(x["pre_model_oracle_eligibility_gate"] for x in report_rows)
    by_cause=Counter(x["known_implementation_blocker_key"] for x in report_rows)
    return {
        "schema":"bibimbap-45-capability-evidence/v1",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/116",
        "status":"FULL_45_PUBLIC_TASK_STATIC_CAPABILITY_AUDIT_ONLY",
        "all_45_original_editing_task_ids_accounted":True,
        "source_only_taxonomy_no_hidden_grader_access":True,
        "model_requests":0,"api_spend_usd":"0",
        "this_is_not_an_LLM_benchmark_result":True,
        "this_is_not_45_D0_oracle_passes":True,
        "source_projected_36_of_45":36,
        "source_blocked_9_of_45":9,
        "original_45_itt_denominator":45,
        "model_capability_not_conflated_with_compiler":True,
        "original_author_score_not_equivalent_to_strict_task_pass":True,
        "strict_task_oracle_complete_count":0,
        "paper_equivalent_45_task_bim_backend_available":False,
        "baseline_luna45_report_sha256":file_hash(BASELINE),
        "compiler_source_sha256":file_hash(COMPILER),
        "ifc_mutations_source_sha256":file_hash(OPERATIONS),
        "declarative_schema_sha256":file_hash(GRAMMAR),
        "source_projection_source_sha256":file_hash(SOURCE),
        "gates_by_count":dict(sorted(by_gate.items())),
        "blocker_family_counts":dict(sorted(by_cause.items())),
        "by_operation":{v:dict(Counter(x["pre_model_oracle_eligibility_gate"] for x in report_rows if x["crud"]==v))
                        for v in ("create","update","delete")},
        "individual_task_gap_matrix":report_rows,
    }

def replay_failure_cause(row:dict, replay:Path)->dict:
    original_task=row["original_task_id"]
    root=replay/original_task
    raw=root/"model_generated_exact.raw.txt"
    source=root/"source_normalized_m.ifc"
    meta=root/"attempt_result.json"
    if not all(p.is_file() and not p.is_symlink() for p in (raw,source,meta)):
        raise ValueError("Previous genuine provider evidence missing: "+original_task)
    prev=json.loads(meta.read_text(encoding="utf8"))
    if (prev.get("status")!="TRUSTED_XML_OR_NATIVE_GRADING_FAILED"
        or prev.get("model_generated_exact_sha256")!=file_hash(raw)
        or prev.get("normalized_ifc_sha256")!=file_hash(source)):
        raise ValueError("Historical result/raw/source hash mismatch: "+original_task)
    with tempfile.TemporaryDirectory(prefix="bibi116-compiler-audit-") as td:
        target=Path(td)/"candidate.ifc"
        try:
            compiled=compile_declarative_xml(source,raw.read_bytes(),target)
            return {"status":"REPLAY_COMPILED_PREVIOUSLY_FAILED",
                    "compiler_operations":[op.operation for op in compiled.operations],
                    "original_failure_may_be_SCORER_OR_EXPERIMENT_PIPELINE":True}
        except Exception as exc:
            message=str(exc).split(": ",1)[-1].lower()
            if ("only creation of a new standalone wall" in message):
                cause="NATIVE_CREATE_CLASS_NOT_IMPLEMENTED"
            elif ("only verified wall geometry" in message):
                cause="NATIVE_GEOMETRY_EDIT_NOT_IMPLEMENTED"
            elif ("relationship deletion" in message or "relationship addition" in message):
                cause="NATIVE_RELATION_MUTATION_NOT_IMPLEMENTED"
            elif ("only safe removal" in message or "standalone" in message):
                cause="NATIVE_DELETE_SCOPE_NOT_SUPPORTED"
            elif ("door+opening delete must be an isolated" in message):
                cause="HOSTED_PAIR_DELETE_PRECONDITION"
            elif ("no match found for key-sequence" in message
                  or "xml_schema:" in message):
                cause="INVALID_XML_RELATION_REFERENCE"
            elif ("cannot delete wall with host/" in message):
                cause="DEPENDENT_WALL_DELETE_REJECTED"
            elif ("opening is outside the hosted wall" in message):
                cause="INVALID_MODEL_HOSTED_OPENING_OFFSET"
            elif ("unplanned semantic graph" in message):
                cause="DECLARATIVE_DIFF_NOT_EXECUTABLE"
            elif ("source" in message and "unsupported" in message):
                cause="SOURCE_GEOMETRY_UNSUPPORTED"
            else:
                cause="OTHER_COMPILER_REJECTION"
            return {"status":"REPLAY_COMPILER_REJECTED",
                    "error_type":type(exc).__name__,
                    "normalized_failure_class":cause}

def historical_replay(report:dict, replays:Path)->dict:
    if not replays.is_dir() or replays.is_symlink():
        raise ValueError("Frozen original local evidence directory required for replay")
    outputs={}
    rows=report["individual_task_gap_matrix"]
    for row in rows:
        if row["historical_one_shot_status"]!="TRUSTED_XML_OR_NATIVE_GRADING_FAILED":
            continue
        outputs[row["original_task_id"]]=replay_failure_cause(row,replays)
    if len(outputs)!=21:
        raise ValueError("Expected exactly 21 existing one-shot compiler/grade failures")
    report["historical_21_failures_replayed_read_only"]=True
    report["historical_failures_by_replay_category"]=dict(sorted(Counter(
        x.get("normalized_failure_class",x["status"]) for x in outputs.values()).items()))
    for row in rows:
        if row["original_task_id"] in outputs:
            row["historical_read_only_compile_replay"]=outputs[row["original_task_id"]]
    return report

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",required=True,type=Path)
    parser.add_argument("--dataset",required=True,type=Path)
    parser.add_argument("--replay-dir",type=Path)
    parser.add_argument("--output-json",required=True,type=Path)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Refuse overwriting existing capability report")
    report=structural_45(args.author_repo.resolve(strict=True),
                         args.dataset.resolve(strict=True))
    if args.replay_dir is not None:
        report=historical_replay(report,args.replay_dir)
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as f:
        f.write((json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({
        "status":report["status"],"original_tasks":len(report["individual_task_gap_matrix"]),
        "gates":report["gates_by_count"],
        "historical_replay":report.get("historical_failures_by_replay_category"),
        "api_cost":report["api_spend_usd"],
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
