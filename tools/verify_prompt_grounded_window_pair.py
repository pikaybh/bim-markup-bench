"""G1 #16: instruction-derived source-only D0/I0 Window move parity.

This G1 trusted *offline manual oracle* reads ONLY allowed public task
instruction and verified original IFC. Crucially it NEVER accesses the
benchmark's private target/evaluation/GT fields, opens GT IFC, imports
official scorer, calls an LLM, or exposes selected answer to either model.

D0 receives the existing real source-only XML view; trusted source-only
construction makes a declarative document edit, then separate trusted
controller compiles its accepted XML. I0 uses an independently authored
IfcOpenShell manual reference implementation with the two IFC GUIDs
parsed directly from the public instruction and no D0 compiler import.

This does not make an agent capable of interpreting the task; the exact
public prompt syntax is a frozen, restricted deterministic case only.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.placement
from lxml import etree
import numpy as np

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.direct_markup.agent_runner import (
    SourceFileEdit,SourceOnlySettings,TrustedCompilationController,
    stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    create_matched_observations,ImperativeControlSession,ControlConfig,
)
from src.runner.offline_context_cost_gate import (
    matched_shared_components,component,
)
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report


ROOT=Path(__file__).resolve().parents[1]
FROZEN_TASK="WIN-UPD-DIR-A-002"
PINNED_PUBLIC_TASK_DATA_SHA="9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
PINNED_SAMPLE_SHA="75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
PINNED_INPUT_SHA="c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9"

# Only THIS published prompt syntax is supported and frozen for G1.
# No command-list grammar and no authoring instructions are model-exposed.
PUBLIC_WINDOW_MOVE=re.compile(
    r"Move the window with ID (?P<window>[A-Za-z0-9_$]{22}) "
    r"by (?P<distance>[0-9]+(?:\.[0-9]+)?)m in positive "
    r"(?P<axis>[xyz]) direction\. "
    r"Also move the opening (?P<opening>[A-Za-z0-9_$]{22}) "
    r"the same and preserve all relationships\.",
    re.ASCII,
)


class PromptGroundedOracleBlocked(ValueError):
    """Reject incomplete/ambiguous/mismatched public task source evidence."""


@dataclass(frozen=True)
class PublicWindowMove:
    window_guid:str
    opening_guid:str
    positive_world_y_m:Decimal

    def __post_init__(self):
        if self.window_guid==self.opening_guid:
            raise PromptGroundedOracleBlocked("Distinct native Window and Opening required")


def parse_public_window_move(text:str)->PublicWindowMove:
    """Parse ONLY the public sentence; no task.target or GT metadata."""
    if not isinstance(text,str) or len(text)>512:
        raise PromptGroundedOracleBlocked("Invalid/oversized public instruction")
    match=PUBLIC_WINDOW_MOVE.fullmatch(text)
    if match is None:
        raise PromptGroundedOracleBlocked(
            "Unrecognized/ambiguous public Window/Opening move or extra instructions")
    amount=Decimal(match["distance"])
    if match["axis"]!="y" or amount!=Decimal("1"):
        raise PromptGroundedOracleBlocked(
            "Only the frozen positive world-Y 1m task is supported")
    return PublicWindowMove(
        match["window"],match["opening"],amount)


def _sha(path:Path)->str:
    if not path.is_file() or path.is_symlink():
        raise PromptGroundedOracleBlocked("Missing/linked pinned public original IFC")
    return sha256(path.read_bytes()).hexdigest()


def verified_public_task_and_source(root:Path=ROOT)->tuple[dict,Path,str]:
    """Fail closed to immutable public metadata and source IFC ONLY."""
    file=root/"data/tasks.jsonl"
    manifest=root/"manifests/pilot_36_candidate_v0.json"
    if _sha(file)!=PINNED_PUBLIC_TASK_DATA_SHA or _sha(manifest)!=PINNED_SAMPLE_SHA:
        raise PromptGroundedOracleBlocked("Frozen task metadata/sample digest changed")
    source_records=read_tasks(file)
    matches=[r for r in source_records if r["task_id"]==FROZEN_TASK]
    candidate=json.loads(manifest.read_text("utf8"))
    if (len(matches)!=1 or len(candidate.get("tasks",[]))!=36
            or sum(row["task_id"]==FROZEN_TASK
                   for row in candidate["tasks"])!=1):
        raise PromptGroundedOracleBlocked("Frozen Window task not uniquely in candidate")
    task=matches[0]
    # These are the ONLY task fields permitted past the boundary.
    public={"task_id":FROZEN_TASK,"instruction":task["prompt"],
            "input_file":"input.ifc"}
    parse_public_window_move(public["instruction"])
    tree_file=root/"data/bim_edit_remote_tree.json"
    remote=json.loads(tree_file.read_text("utf8"))
    remote_by_path={r["path"]:r for r in remote if r.get("type")=="file"}
    relative=repo_asset_path(task["input_ifc"])
    original=_files_in_root(root/"data/ifc",relative)
    if not original.is_file() or original.is_symlink():
        raise PromptGroundedOracleBlocked("Public original input IFC not cached")
    verify_local_asset_bytes(original,remote_by_path[relative])
    digest=_sha(original)
    if digest!=PINNED_INPUT_SHA:
        raise PromptGroundedOracleBlocked("Frozen Window original IFC bytes changed")
    return public,original,digest


def _native_prompt_bindings(model,move:PublicWindowMove):
    """Resolve both GUIDs ONLY from public prompt, not private task target."""
    try:
        window=model.by_guid(move.window_guid)
        opening=model.by_guid(move.opening_guid)
    except RuntimeError as exc:
        # IfcOpenShell's by_guid raises RuntimeError for an absent GUID
        # on the pinned native kernel. Do not expose raw native failures.
        raise PromptGroundedOracleBlocked(
            "Public instruction IFC entity types unresolved") from exc
    if (window is None or opening is None
            or not window.is_a("IfcWindow")
            or not opening.is_a("IfcOpeningElement")):
        raise PromptGroundedOracleBlocked("Public instruction IFC entity types unresolved")
    if (len(window.FillsVoids)!=1 or
            window.FillsVoids[0].RelatingOpeningElement!=opening
            or len(opening.HasFillings)!=1 or
            opening.HasFillings[0].RelatedBuildingElement!=window
            or len(opening.VoidsElements)!=1):
        raise PromptGroundedOracleBlocked(
            "Public Window/Openings are not uniquely related")
    host=opening.VoidsElements[0].RelatingBuildingElement
    if not host.is_a("IfcWall"):
        raise PromptGroundedOracleBlocked("Public Opening is not hosted by a Wall")
    frame=np.asarray(
        ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement),
        dtype=float)
    if frame.shape!=(4,4) or not np.isfinite(frame).all():
        raise PromptGroundedOracleBlocked("Invalid host native world frame")
    world=np.array([0.,float(move.positive_world_y_m),0.],dtype=float)
    try:
        local=np.linalg.solve(frame[:3,:3],world)
    except np.linalg.LinAlgError as exc:
        raise PromptGroundedOracleBlocked("Non-invertible host frame") from exc
    if not np.allclose(local,(float(move.positive_world_y_m),0.,0.),
                       rtol=0,atol=1e-8):
        raise PromptGroundedOracleBlocked(
            "Published world displacement cannot use one XML local Opening offset")
    return window,opening,host,float(local[0])


def _native_world_xyz(entity)->np.ndarray:
    return np.asarray(
        ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement)[:3,3],
        dtype=float)


def _snapshot_entities(model)->dict[int,str]:
    return {e.id():str(e) for e in model}


def _changed_native_entity_classes(before,after,expected_location_id:int)->int:
    a=_snapshot_entities(before)
    b=_snapshot_entities(after)
    if set(a)!=set(b):
        raise PromptGroundedOracleBlocked("Native IFC entity inventory changed")
    modified=[key for key in a if a[key]!=b[key]]
    if modified!=[expected_location_id]:
        raise PromptGroundedOracleBlocked(
            "Native IFC changed entities besides the intended Opening location")
    changed=before.by_id(expected_location_id)
    if not changed.is_a("IfcCartesianPoint"):
        raise PromptGroundedOracleBlocked("Changed native entity was not an IFC point")
    return len(modified)


def _compile_pair_from_public_prompt(
    public:dict,original:Path,digest:str,move:PublicWindowMove
)->dict:
    native=ifcopenshell.open(str(original))
    win,opening,_,local_dx=_native_prompt_bindings(native,move)
    point_id=opening.ObjectPlacement.RelativePlacement.Location.id()
    root_before={r.GlobalId for r in native.by_type("IfcRoot")}
    relationships=native_topology_inventory(native)
    win_xyz=_native_world_xyz(win)
    op_xyz=_native_world_xyz(opening)

    with TemporaryDirectory(prefix="g1-frozen-public-prompt-pair-") as td:
        base=Path(td)
        direct_session=stage_source_only_workspace(
            original,base/"D0_work",public,SourceOnlySettings())
        direct=direct_session.agent_visible_context()
        observations=create_matched_observations(original,public)
        imperative=ImperativeControlSession(observations,ControlConfig())
        imperative_visible=imperative.model_visible_context()
        shared=matched_shared_components(direct,observations,digest)
        if (direct.instruction!=public["instruction"]
                or imperative_visible["instruction"]!=public["instruction"]
                or imperative_visible["OS_sandbox_available"] is not False
                or imperative_visible["allowed_execution_operations"]!=[]
                or direct.allowed_operations!=(
                    "read_text","patch_text","rewrite_xml_text")):
            raise PromptGroundedOracleBlocked("Actual G2 model views/disabled tools differ")
        if not all(shared[k]["sha256"]==component(text).sha256 for k,text in (
            ("public_instruction",public["instruction"]),
            ("v01_source_xml",direct.xml_text),
            ("v01_schema_spec",direct.language_spec),
        )):
            raise PromptGroundedOracleBlocked("Mismatched shared model text")
        doc=etree.fromstring(direct.xml_text.encode("utf8"))
        nodes=[e for e in doc.iter() if isinstance(e.tag,str)]
        xml_windows=[e for e in nodes if
                     etree.QName(e).localname=="Window"
                     and e.get("ifcGuid")==move.window_guid]
        xml_openings=[e for e in nodes if
                      etree.QName(e).localname=="Opening"
                      and e.get("ifcGuid")==move.opening_guid]
        if len(xml_windows)!=1 or len(xml_openings)!=1:
            raise PromptGroundedOracleBlocked("Both public IFC IDs not visible uniquely in XML")
        xml_window=xml_windows[0]
        xml_opening=xml_openings[0]
        if xml_window.get("opening")!=xml_opening.get("id"):
            raise PromptGroundedOracleBlocked("Visible XML Window/Opening link mismatch")
        old=xml_opening.get("offset")
        try:
            old_offset=Decimal(old)
        except Exception as exc:
            raise PromptGroundedOracleBlocked("Public XML opening offset invalid") from exc
        if not old_offset.is_finite():
            raise PromptGroundedOracleBlocked("Public XML opening offset non-finite")
        xml_opening.set("offset",format(old_offset+move.positive_world_y_m,"f"))
        revised=etree.tostring(doc,encoding="utf8",xml_declaration=True).decode("utf8")
        edit=SourceFileEdit(
            filename="building.xml",expected_sha256=direct.xml_byte_sha256,
            mode="whole_file_rewrite",old_text="",new_text=revised,
            agent_declared_success=False,
        )
        attempt=direct_session.attempt(edit)
        if attempt["status"]!="ACCEPTED_VALID_XML":
            raise PromptGroundedOracleBlocked("Trusted public-prompt D0 source edit refused")
        d0=base/"D0_native.ifc"
        i0=base/"I0_native.ifc"
        compiled=TrustedCompilationController.compile_accepted(
            direct_session,original,d0)
        manual_ifc_reference(
            original,i0,"MOVE_OPENING",
            target_guid=move.opening_guid,delta_x=local_dx)
        if ([item.operation for item in compiled.operations]
                !=["MOVE_OPENING_WITH_FILLING"]
                or compiled.unexpected_root_changes):
            raise PromptGroundedOracleBlocked("D0 compiler emitted unexpected native edits")
        independent=parity_report(d0,i0)
        if not independent["parity"]:
            raise PromptGroundedOracleBlocked("Native-only D0/I0 IFC comparison failed")
        produced=[]
        for result_path in (d0,i0):
            result=ifcopenshell.open(str(result_path))
            result_win,result_op,_,_=_native_prompt_bindings(result,move)
            if {r.GlobalId for r in result.by_type("IfcRoot") }!=root_before:
                raise PromptGroundedOracleBlocked("Original IFC Root identities changed")
            if native_topology_inventory(result)!=relationships:
                raise PromptGroundedOracleBlocked("Native relation graph changed")
            expected_world=np.array([0.,float(move.positive_world_y_m),0.])
            for current,old_xyz in ((result_win,win_xyz),(result_op,op_xyz)):
                if not np.allclose(
                        _native_world_xyz(current)-old_xyz,expected_world,
                        rtol=0,atol=1e-6):
                    raise PromptGroundedOracleBlocked(
                        "Native Window or Opening displacement does not match public prompt")
            _changed_native_entity_classes(native,result,point_id)
            produced.append(sha256(result_path.read_bytes()).hexdigest())
    if _sha(original)!=digest:
        raise PromptGroundedOracleBlocked("Original public IFC changed during manual G1 pair")
    return {
        "status":"PASS_PROMPT_DERIVED_SOURCE_ONLY_PAIR_OFFICIAL_TASK_STILL_UNVERIFIED",
        "task_id":FROZEN_TASK,
        "original_public_ifc_sha256":digest,
        "public_instruction_sha256":component(public["instruction"]).sha256,
        "public_window_and_opening_ids_resolved_without_grader_target_field":True,
        "source_task_target_metadata_read_for_authoring":False,
        "common_model_facing_observation_byte_identical":True,
        "common_model_visible_text_fields":{
            key:shared[key] for key in (
                "public_task_id","public_instruction","v01_source_xml",
                "v01_schema_spec","source_ifc_digest")
        },
        "imperative_only_api_notes_utf8_bytes":len(
            imperative_visible["api_reference_notes"].encode("utf8")),
        "model_facing_tool_and_feedback_parity_approved":False,
        "model_provider_token_counts":None,
        "world_move_read_from_public_instruction":True,
        "window_and_opening_native_world_move_matches_instruction":True,
        "all_existing_relationships_preserved":True,
        "all_existing_IfcRoot_ids_preserved":True,
        "only_changed_native_entity_class":"IfcCartesianPoint",
        "changed_native_entity_count_per_arm":1,
        "declarative_operation":"MOVE_OPENING_WITH_FILLING",
        "independent_native_D0_I0_observation_parity":True,
        "IFC_full_file_d0_i0_equal":produced[0]==produced[1],
        "d0_ifc_sha256":produced[0],
        "i0_ifc_sha256":produced[1],
        "input_ifc_bytes_unchanged":True,
        "output_IFC_committed":False,
        "developer_chosen_result_exposed_to_either_model":False,
        "source_only_deterministic_instruction_pair_demonstrated":True,
        "full_official_reference_IFC_task_success_proven":False,
        "official_evaluator_executed":False,
        "official_tasks_scored":0,
        "LLM_calls":0,
        "paid_provider_charges_USD":None,
        "G1_G2_G3_live_release_authorized":False,
    }


def verify_prompt_grounded_window_pair(root:Path=ROOT)->dict:
    public,original,digest=verified_public_task_and_source(root)
    move=parse_public_window_move(public["instruction"])
    return _compile_pair_from_public_prompt(public,original,digest,move)


def main()->int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    arg=parser.parse_args()
    report=verify_prompt_grounded_window_pair()
    if arg.output_json:
        file=arg.output_json
        if file.is_symlink() or file.exists() or not file.parent.is_dir():
            parser.error("Refuse overwrite/symlink/missing parent evidence path")
        with file.open("x",encoding="utf8",newline="\n") as f:
            f.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        key:report[key] for key in (
            "status","task_id","original_public_ifc_sha256",
            "public_window_and_opening_ids_resolved_without_grader_target_field",
            "common_model_facing_observation_byte_identical",
            "window_and_opening_native_world_move_matches_instruction",
            "all_existing_relationships_preserved",
            "independent_native_D0_I0_observation_parity",
            "changed_native_entity_count_per_arm",
            "official_tasks_scored","LLM_calls",
            "G1_G2_G3_live_release_authorized",
        )
    },sort_keys=True,indent=2))
    # The manual real-source parity passes, but official scoring, live
    # inference and original task correctness are still not proved.
    return 2


if __name__=="__main__":
    raise SystemExit(main())
