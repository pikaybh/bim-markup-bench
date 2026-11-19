"""G1 #16 — exact public spatial-Wall instruction to D0/I0 native IFC.

ONE developer-authored, source-only (not an LLM) verification of the
original frozen WAL-CRE-SPA-A-003. The trusted parser and geometric
reference live OUTSIDE both agent workspaces. It never reads the
dataset's private target, grading reference IFC, results, or evaluator.

The prompt entails a Wall and orthogonal junctions; it does NOT
specify a new Space name/type/Psets/QTO or an explicit room splitting
rule. Therefore this proof stops at Wall/Path joins and reports the
unsplit source Space as a separate unresolved decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree
import numpy as np

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.direct_markup.agent_runner import (
    SourceFileEdit,SourceOnlySettings,TrustedCompilationController,
    stage_source_only_workspace,
)
from src.imperative_control.agent_runner import (
    ControlConfig,ImperativeControlSession,create_matched_observations,
)
from src.runner.offline_context_cost_gate import matched_shared_components
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report
from tools.verify_spatial_wall_manual_oracle import (
    _geometry_from_public_instruction,_world_bounds,
)

ROOT=Path(__file__).resolve().parents[1]
CASE="WAL-CRE-SPA-A-003"
NS="urn:bim-markup-bench:toy:v0"
NEW_ID="g1_t_path_join_manual"
SOURCE_SHA="e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de"
TASKS_SHA="9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
PILOT_SHA="75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
NEW_WALL_NAMESPACE=uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd")
JOIN_NAMESPACE=uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111")

PROMPT_RE=re.compile(
    r"create a wall that spans orthogonally between the wall with the ID "
    r"(?P<first>[A-Za-z0-9_$]{22}) and (?P<second>[A-Za-z0-9_$]{22}) "
    r"and begins at (?P<offset>[0-9]+(?:\.[0-9]+)?)m in \+y direction "
    r"from the right side of the door looking from inside of the room "
    r"with the ID (?P<room>[A-Za-z0-9_$]{22})\. "
    r"It must have a thickness of (?P<thickness>[0-9]+(?:\.[0-9]+)?)m "
    r"and a height of (?P<height>[0-9]+(?:\.[0-9]+)?)m\.",
    re.ASCII,
)


class WallPromptGateBlocked(ValueError):
    """Invalid public instruction / source-side native evidence."""


@dataclass(frozen=True)
class PublicWallSpec:
    first_wall:str
    second_wall:str
    room:str
    door_right_jamb_offset_y_m:Decimal
    thickness_m:Decimal
    height_m:Decimal


def parse_public_wall_spec(prompt:str)->PublicWallSpec:
    """Reject any grammar extension, extra command, or unsupported task value."""
    if not isinstance(prompt,str) or len(prompt)>640:
        raise WallPromptGateBlocked("Missing or oversized public instruction")
    match=PROMPT_RE.fullmatch(prompt)
    if match is None:
        raise WallPromptGateBlocked("Unknown or ambiguous wall instruction")
    first,second,room=(match[name] for name in ("first","second","room"))
    if len({first,second,room})!=3:
        raise WallPromptGateBlocked("Public room/wall identifiers must be distinct")
    offset,thickness,height=(
        Decimal(match[name]) for name in ("offset","thickness","height"))
    if ((offset,thickness,height)
            !=(Decimal("1.3025"),Decimal("0.175"),Decimal("2.800"))):
        raise WallPromptGateBlocked("Non-frozen wall dimensions or offset")
    return PublicWallSpec(first,second,room,offset,thickness,height)


def _sha(path:Path)->str:
    if path.is_symlink() or not path.is_file():
        raise WallPromptGateBlocked("Missing or linked pinned IFC/manifest")
    return sha256(path.read_bytes()).hexdigest()


def verified_public_input(root:Path=ROOT)->tuple[dict,Path,str]:
    """The agent gets only {task_id,instruction,input_file}."""
    tasks_path=root/"data/tasks.jsonl"
    pilot_path=root/"manifests/pilot_36_candidate_v0.json"
    if _sha(tasks_path)!=TASKS_SHA or _sha(pilot_path)!=PILOT_SHA:
        raise WallPromptGateBlocked("Original task/candidate evidence changed")
    candidates=json.loads(pilot_path.read_text("utf8"))
    if (len(candidates.get("tasks",[]))!=36 or
            sum(row.get("task_id")==CASE for row in candidates["tasks"])!=1):
        raise WallPromptGateBlocked("Fixed pilot task missing/duplicated")
    entries=[row for row in read_tasks(tasks_path) if row["task_id"]==CASE]
    if len(entries)!=1:
        raise WallPromptGateBlocked("Public task not unique")
    task=entries[0]
    prompt=task["prompt"]
    parse_public_wall_spec(prompt)
    # Deliberately never inspect 'target', 'evaluation' or 'ground_truth_ifc'.
    public={"task_id":CASE,"instruction":prompt,"input_file":"input.ifc"}
    tree=json.loads((root/"data/bim_edit_remote_tree.json").read_text("utf8"))
    remote={entry["path"]:entry for entry in tree if entry.get("type")=="file"}
    relative=repo_asset_path(task["input_ifc"])
    original=_files_in_root(root/"data/ifc",relative)
    verify_local_asset_bytes(original,remote[relative])
    digest=_sha(original)
    if digest!=SOURCE_SHA:
        raise WallPromptGateBlocked("Native source is not the frozen public IFC")
    return public,original,digest


def _created_guid(digest:str)->str:
    identity=f"bim-markup-v0.1:{digest}:IfcWall:{NEW_ID}"
    return ifcopenshell.guid.compress(uuid.uuid5(
        NEW_WALL_NAMESPACE,identity).hex)


def _join_guid(digest:str,host_guid:str,new_guid:str)->str:
    return ifcopenshell.guid.compress(uuid.uuid5(
        JOIN_NAMESPACE,f"connect-v0.1:{digest}:{host_guid}:{new_guid}").hex)


def _actual_world_geometry(public:dict,source:Path,spec:PublicWallSpec):
    import ifcopenshell
    from src.runtime.ifc_projection import project_ifc

    model=ifcopenshell.open(str(source))
    projection=project_ifc(source)
    g=_geometry_from_public_instruction({"prompt":public["instruction"]},
                                        model,projection)
    # Input-only analytical check, distinct from the permissive regex in
    # the historical manual geometry source helper.
    if (g["thickness"]!=spec.thickness_m or g["height"]!=spec.height_m
            or g["door_side_identification"] !=
            "WEST_OF_DOOR_LOOK_EAST_RIGHT_HAND_WORLD_MINUS_Y"):
        raise WallPromptGateBlocked("Native source geometric interpretation diverged")
    try:
        wall_a=model.by_guid(spec.first_wall)
        wall_b=model.by_guid(spec.second_wall)
        room=model.by_guid(spec.room)
    except RuntimeError as exc:
        raise WallPromptGateBlocked("Public room/Wall GUID absent from source IFC") from exc
    if not (wall_a.is_a("IfcWall") and wall_b.is_a("IfcWall")
            and room.is_a("IfcSpace")):
        raise WallPromptGateBlocked("Invalid public entity classes")
    native_door=model.by_type("IfcDoor")
    if len(native_door)!=1:
        raise WallPromptGateBlocked("The door viewpoint is not unique")
    door_lo,_=_world_bounds(native_door[0])
    expected_y=float(door_lo[1]+float(spec.door_right_jamb_offset_y_m))
    if not np.isclose(float(g["start"][1]),expected_y,atol=1e-6,rtol=0):
        raise WallPromptGateBlocked("Right-hand door jamb plus world Y offset mismatched")
    if not np.isclose(float(g["end"][1]),expected_y,atol=1e-6,rtol=0):
        raise WallPromptGateBlocked("New Wall must lie on expected world Y line")
    room_lo,room_hi=_world_bounds(room)
    if not (np.isclose(float(g["start"][2]),float(room_lo[2]),atol=1e-6)
            and float(g["end"][0])>float(g["start"][0])
            and float(g["start"][0])>=float(room_lo[0])-1e-6
            and float(g["end"][0])<=float(room_hi[0])+1e-6):
        raise WallPromptGateBlocked("New Wall does not span the source room")
    return model,projection,g


def _original_native_relations_preserved(before:dict,after:dict,
                                         new_wall_guid:str)->int:
    """New path relationships only; old containment may add the Wall."""
    if not set(before).issubset(after):
        raise WallPromptGateBlocked("Existing IFC relationship deleted")
    updates=0
    for guid,old in before.items():
        cur=after[guid]
        if cur==old:
            continue
        if (old[0]!="IfcRelContainedInSpatialStructure"
                or cur[0]!=old[0] or cur[1]!=old[1]
                or not set(old[2]).issubset(cur[2])
                or set(cur[2])-set(old[2])!={new_wall_guid}):
            raise WallPromptGateBlocked("Unrelated IFC native relationship changed")
        updates+=1
    extras=[value for key,value in after.items() if key not in before]
    if (len(extras) not in (2,3) or
            sum(value[0]=="IfcRelConnectsPathElements" for value in extras)!=2 or
            any(value[0] not in (
                "IfcRelConnectsPathElements","IfcRelContainedInSpatialStructure"
            ) for value in extras)):
        raise WallPromptGateBlocked("Unexpected native IFC relationships created")
    if updates + sum(v[0]=="IfcRelContainedInSpatialStructure" for v in extras)!=1:
        raise WallPromptGateBlocked("New wall missing exactly one storey containment")
    return 2


def verify_prompt_grounded_spatial_wall(root:Path=ROOT, *, physical_observer=None)->dict:
    """Run real D0 XML -> IFC and independent I0 Python -> IFC, source only."""
    public,original,digest=verified_public_input(root)
    spec=parse_public_wall_spec(public["instruction"])
    source,projection,g=_actual_world_geometry(public,original,spec)
    before_relations=native_topology_inventory(source)
    before_roots={r.GlobalId for r in source.by_type("IfcRoot")}
    original_bounds=sum(r.is_a("IfcRelSpaceBoundary")
                        for r in source.by_type("IfcRelSpaceBoundary"))
    new_guid=_created_guid(digest)
    mapping=dict(projection.projected_global_ids)
    if not all(key in mapping for key in (
            spec.first_wall,spec.second_wall,spec.room)):
        raise WallPromptGateBlocked("Source IFC references not all visible in D0 XML")
    with TemporaryDirectory(prefix="g1-public-spatial-wall-") as temp:
        base=Path(temp)
        dsession=stage_source_only_workspace(
            original,base/"D0_workspace",public,SourceOnlySettings())
        dcontext=dsession.agent_visible_context()
        observed=create_matched_observations(original,public)
        i_visible=ImperativeControlSession(
            observed,ControlConfig()).model_visible_context()
        shared=matched_shared_components(dcontext,observed,digest)
        if (dcontext.instruction!=public["instruction"]
                or i_visible["instruction"]!=public["instruction"]
                or dcontext.allowed_operations!=(
                    "read_text","patch_text","rewrite_xml_text")
                or i_visible["OS_sandbox_available"] is not False
                or i_visible["allowed_execution_operations"]!=[]):
            raise WallPromptGateBlocked("Actual arm-specific model tool gates differ")
        tree=etree.fromstring(dcontext.xml_text.encode("utf8"))
        elements=tree.find(".//{"+NS+"}Elements")
        relations=tree.find(".//{"+NS+"}Relations")
        if elements is None or relations is None or any(
                node.get("id")==NEW_ID for node in tree.iter()):
            raise WallPromptGateBlocked("Invalid D0 declarative source graph")
        attrs={
            "id":NEW_ID,"level":g["storey_local_id"],
            "x1":str(g["start"][0]),"y1":str(g["start"][1]),"z1":str(g["start"][2]),
            "x2":str(g["end"][0]),"y2":str(g["end"][1]),"z2":str(g["end"][2]),
            "height":str(spec.height_m),"thickness":str(spec.thickness_m),
        }
        etree.SubElement(elements,"{"+NS+"}Wall",attrs)
        for host in (spec.first_wall,spec.second_wall):
            etree.SubElement(relations,"{"+NS+"}Connects",{
                "from":mapping[host],"to":NEW_ID})
        changed=etree.tostring(tree,encoding="utf8",xml_declaration=True).decode("utf8")
        candidate=SourceFileEdit(
            filename="building.xml",expected_sha256=dcontext.xml_byte_sha256,
            mode="whole_file_rewrite",old_text="",new_text=changed,
            agent_declared_success=False)
        accepted=dsession.attempt(candidate)
        if accepted["status"]!="ACCEPTED_VALID_XML":
            raise WallPromptGateBlocked("Trusted prompt-based declarative state rejected")
        d0=base/"D0.ifc"
        report=TrustedCompilationController.compile_accepted(dsession,original,d0)
        actions=[entry.operation for entry in report.operations]
        if actions!=["CREATE_WALL","ADD_WALL_PATH_CONNECTION",
                     "ADD_WALL_PATH_CONNECTION"] or report.unexpected_root_changes:
            raise WallPromptGateBlocked("Unexpected XML->IFC physical operation plan")
        native=ifcopenshell.open(str(d0))
        i_base=base/"I0-base.ifc"
        i0=base/"I0.ifc"
        manual_ifc_reference(
            original,i_base,"CREATE_WALL",new_guid=new_guid,
            storey_guid=g["storey_guid"],
            start=tuple(float(x) for x in g["start"]),
            end=tuple(float(x) for x in g["end"]),
            height=float(spec.height_m),thickness=float(spec.thickness_m))
        independent=ifcopenshell.open(str(i_base))
        created=independent.by_guid(new_guid)
        for host,terminal in (
            (spec.first_wall,"ATSTART"),(spec.second_wall,"ATEND")
        ):
            independent.createIfcRelConnectsPathElements(
                GlobalId=_join_guid(digest,host,new_guid),
                RelatingElement=independent.by_guid(host),
                RelatedElement=created,
                RelatingConnectionType="ATPATH",
                RelatedConnectionType=terminal,
                RelatingPriorities=(),RelatedPriorities=())
        independent.write(str(i0))
        parity=parity_report(d0,i0)
        if not parity["parity"]:
            raise WallPromptGateBlocked("IFC-native D0/I0 observations differ")
        baseline_count=len(source.by_type("IfcRelSpaceBoundary"))
        hashes=[]
        for path in (d0,i0):
            output=ifcopenshell.open(str(path))
            wall=output.by_guid(new_guid)
            if wall is None or not wall.is_a("IfcWall"):
                raise WallPromptGateBlocked("Native IFC output missing intended Wall")
            old_missing=before_roots-{obj.GlobalId for obj in output.by_type("IfcRoot")}
            if old_missing:
                raise WallPromptGateBlocked("Native existing IFC roots deleted")
            _original_native_relations_preserved(
                before_relations,native_topology_inventory(output),new_guid)
            new_paths=[rel for rel in output.by_type("IfcRelConnectsPathElements")
                       if rel.RelatedElement.GlobalId==new_guid]
            if not (len(new_paths)==2 and {
                (rel.RelatingElement.GlobalId,
                 str(rel.RelatingConnectionType),
                 str(rel.RelatedConnectionType)) for rel in new_paths
            }=={
                (spec.first_wall,"ATPATH","ATSTART"),
                (spec.second_wall,"ATPATH","ATEND"),
            }):
                raise WallPromptGateBlocked("Native Wall T-path contacts differ from prompt")
            if len(output.by_type("IfcRelSpaceBoundary"))!=baseline_count:
                raise WallPromptGateBlocked("Unrequested Space split appeared in source-only pair")
            lo,hi=_world_bounds(wall)
            expected_lo=np.array([float(g["start"][0]),float(g["start"][1]),
                                  float(g["start"][2])])
            expected_hi=np.array([float(g["end"][0]),
                                  float(g["end"][1]+g["thickness"]),
                                  float(g["start"][2]+g["height"])])
            if not (np.allclose(lo,expected_lo,rtol=0,atol=1e-6)
                    and np.allclose(hi,expected_hi,rtol=0,atol=1e-6)):
                raise WallPromptGateBlocked("Real-world Wall bbox differs from source prompt")
            hashes.append(sha256(path.read_bytes()).hexdigest())
        old_room=source.by_guid(spec.room)
        new_wall=native.by_guid(new_guid)
        room_lo,room_hi=_world_bounds(old_room)
        wall_lo,wall_hi=_world_bounds(new_wall)
        intrusion=np.maximum(
            np.minimum(room_hi,wall_hi)-np.maximum(room_lo,wall_lo),0)
        overlap=float(np.prod(intrusion))
        if overlap<=0.5:
            raise WallPromptGateBlocked("Original room and authored Wall do not overlap")
        if physical_observer is not None:
            # Trusted offline callback: original and ephemeral candidate IFCs
            # are never supplied to a tested model or included in its context.
            physical_evidence=physical_observer(original,d0,i0,public["instruction"])
    if _sha(original)!=digest:
        raise WallPromptGateBlocked("Public input IFC mutated during manual source oracle")
    result={
        "status":"PASS_PROMPT_GROUNDED_WALL_TWO_JOINS_SOURCE_ONLY_FULL_ORACLE_BLOCKED",
        "frozen_task_id":CASE,
        "source_ifc_sha256":digest,
        "public_instruction_sha256":sha256(public["instruction"].encode("utf8")).hexdigest(),
        "public_ids_resolved_in_native_source_and_direct_XML":True,
        "native_source_only_geometry_interpreted_without_GT":True,
        "prompt_right_side_door_world_y_offset_verified":True,
        "prompt_width_height_and_orthogonal_between_two_walls_verified":True,
        "native_d0_i0_ifc_six_category_parity":True,
        "d0_ifc_sha256":hashes[0],
        "i0_ifc_sha256":hashes[1],
        "full_ifc_files_byte_equal":hashes[0]==hashes[1],
        "raw_native_ifc_byte_repeatability_proven":False,
        "semantic_parity_not_identical_raw_bytes":True,
        "native_path_joins_to_prompt_walls":2,
        "native_wall_bbox_min_m":[round(float(x),6) for x in expected_lo],
        "native_wall_bbox_max_m":[round(float(x),6) for x in expected_hi],
        "existing_native_roots_preserved":True,
        "original_native_relationships_preserved":True,
        "existing_space_boundaries_unmodified":True,
        "source_room_wall_volume_overlap_m3":round(overlap,6),
        "room_split_if_required_by_official_target_proven":False,
        "new_room_name_type_psets_qto_in_public_instruction":False,
        "experimental_v02_space_authoring_exposed_to_model":False,
        "complete_task_oracle_proven":False,
        "common_actual_model_visible_text_component_hashes":shared,
        "common_model_source_components_byte_identical":True,
        "I0_only_api_reference_bytes":len(
            i_visible["api_reference_notes"].encode("utf8")),
        "equal_provider_model_tokenization_or_execution_feedback_proven":False,
        "model_generated_output_used":False,
        "source_private_target_or_ground_truth_used":False,
        "official_bim_edit_grader_called":False,
        "official_tasks_scored":0,
        "model_provider_calls":0,
        "paid_spend_authorized":False,
        "G1_G2_G3_experiment_unblocked":False,
    }
    if physical_observer is not None:
        result["trusted_source_only_native_spatial_evidence"]=physical_evidence
    return result


def main()->int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    options=parser.parse_args()
    result=verify_prompt_grounded_spatial_wall()
    if options.output_json:
        file=options.output_json
        if file.exists() or file.is_symlink() or not file.parent.is_dir():
            parser.error("Refuse overwrite, symlink or missing report directory")
        with file.open("x",encoding="utf8",newline="\n") as out:
            out.write(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({key:result[key] for key in (
        "status","frozen_task_id","native_d0_i0_ifc_six_category_parity",
        "native_path_joins_to_prompt_walls","source_room_wall_volume_overlap_m3",
        "complete_task_oracle_proven","official_tasks_scored",
        "model_provider_calls"
    )},sort_keys=True,indent=2))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
