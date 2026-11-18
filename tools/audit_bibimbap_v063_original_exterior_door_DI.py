"""v0.63 evaluator-only original IF4X3 exterior Door+Opening D/I Docker audit.

Three developer-made cases against exact unchanged original public IFC4X3:
(1) real exterior Door with CSG through-cut, (2) structurally valid
interior-Wall Door that original author's scorer may ALSO score 1.0,
(3) exterior Door with an implausibly small panel. Each is executed as
genuinely complete D_FULL, complete D_MANAGED and OS-isolated pinned
Linux Docker general Python I. All ORIGINAL author grader imports and
physical public-question comparisons remain evaluator-only here.

No original answer GUID in frozen report or model-facing source. Actual
provider/model calls = 0. Original source IFC provider uploads = 0.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v057_provenance import (
    assert_original_source_rights_unchanged_v057,
)
from tools.bibimbap_v063_exterior_door_native import (
    SOURCE_SHA,TASK,Q,BOUNDS,source_ifc,source_envelope_v063,
    initial_full_source_v063,initial_compact_source_v063,
    parse_full_final_v063,restore_managed_final_v063,
    independent_real_original_door_scope_v063,
    source_public_exterior_pass_v063,
    semantic_digest_after_native_oracle_v063,
)
from tools.bibimbap_v063_exterior_door_sessions import (
    DirectFullState063,DirectManagedState063,LiveDockerPython063,
)


ROOT=Path(__file__).resolve().parents[1]
BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=ROOT/"reports"/"bibimbap_v063_original_external_door_csg_native_DI_20261118.json"
PARENT=ROOT/"reports"/"bibimbap_v062_original8wall_centered_shortening_native_DI_20261118.json"
PARENT_SHA="c80b6d4c6b39c51eaac96177515f0f6cd93f36e37298bae973ae4f7e57c11842"
PARENT_HEAD="65864f57688313cc3276cb0c6e87321b2662683a"
FROZEN=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"
FROZEN_SHA="0d8e7ca07a08af0afa3a08c10de5a76427e179d41cd1ca9b9df508f40fcc96c8"
FIXED_SIX=[
    "geometry_test_03","geometry_test_13","geometry_test_19",
    "topological_test_05","topological_test_12","topological_test_18",
]
SUPPORTED=set(FIXED_SIX)-{"geometry_test_03"}


def need(ok:bool,why:str):
    if not ok:raise AssertionError(why)


def canonical(value:dict)->bytes:
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)
            +"\n").encode("utf8")


def _guid(case_name:str,part:str):
    return ifcopenshell.guid.compress(
        uuid.uuid5(uuid.NAMESPACE_DNS,
                   "v063-public-source-developer-only-"+case_name+"-"+part).hex)


def _source_host_by_category(model,category:str):
    walls=sorted(model.by_type("IfcWall"),key=lambda x:x.GlobalId)
    if category=="OUTER":
        matches=[
            w for w in walls
            if abs(w.ObjectPlacement.RelativePlacement.Location.Coordinates[1]-100.)<1
        ]
    elif category=="INNER":
        matches=[
            w for w in walls
            if abs(w.ObjectPlacement.RelativePlacement.Location.Coordinates[0]-5000.)<1
        ]
    else:
        raise AssertionError("Unknown evaluator-only source wall category")
    need(len(matches)==1,"Grounded original source host category ambiguous")
    return matches[0],walls.index(matches[0])


def _fixture(case_name:str,host,category:str,width:float,height:float):
    """Original public-source physical geometry, never source hidden GT."""
    opening_width=round(width+.05,6)
    opening_height=round(height+.1,6)
    if category=="OUTER":
        center_x=4.075
        opening=(center_x-opening_width/2,center_x+opening_width/2,
                 -.1,.3,0.,opening_height)
        door=(center_x-width/2,center_x+width/2,
              .075,.120,0.,height)
    else:
        center_y=1.975
        opening=(4.8,5.2,center_y-opening_width/2,
                 center_y+opening_width/2,0.,opening_height)
        door=(4.98,5.025,center_y-width/2,
              center_y+width/2,0.,height)
    return {
        "host_guid":host.GlobalId,
        "door_guid":_guid(case_name,"DOOR"),
        "opening_guid":_guid(case_name,"OPENING"),
        "opening_bbox":opening,
        "door_bbox":door,
        "axis":"X" if category=="OUTER" else "Y",
    }


def _populate_xml(source_xml:bytes,state:dict,*,managed:bool)->str:
    root=etree.fromstring(source_xml)
    target=root[1] if managed else root[2]
    for tag,guid,links,box in (
        ("Opening",state["opening_guid"],
         {"hostOriginalWallGuid":state["host_guid"]},
         state["opening_bbox"]),
        ("Door",state["door_guid"],
         {"fillsOpeningGuid":state["opening_guid"]},
         state["door_bbox"]),
    ):
        attrs={"ifcGuid":guid,**links}
        attrs.update({name:f"{number:.6f}"
                      for name,number in zip(BOUNDS,box)})
        etree.SubElement(target,Q+tag,attrs)
    return etree.tostring(root,encoding="utf8",xml_declaration=True).decode()


def _developer_real_python_code(state:dict,host_index:int,
                                 *,opening_depth_fraction=1.0,
                                 omit_filling=False,omit_storey=False)->str:
    """Independent actual general Python/IfcOpenShell, source-only fixture.

    No import/call into the research native D compiler or original author
    grader. Real Docker clones exact original source and executes code.
    """
    def bounded_data(b):
        return tuple(float(f"{v:.6f}") for v in b)
    ob=bounded_data(state["opening_bbox"])
    db=bounded_data(state["door_bbox"])
    if opening_depth_fraction!=1.0:
        # Deliberately invalid shallow opening that does not pierce
        # either side. Complete physical door panel remains inside it.
        if state["axis"]!="X":
            raise AssertionError("Partial opening negative only X-wall")
        ob=(ob[0],ob[1],.05,.13,ob[4],ob[5])
        db=(db[0],db[1],.06,.105,db[4],db[5])
    return (
        "import numpy as np\n"
        "import ifcopenshell.api.root\n"
        "import ifcopenshell.api.geometry\n"
        "import ifcopenshell.api.feature\n"
        "walls=sorted(ifc.by_type('IfcWall'),key=lambda w:w.GlobalId)\n"
        f"host=walls[{host_index}]\n"
        "contexts=[c for c in ifc.by_type('IfcGeometricRepresentationSubContext') "
        "if c.ContextIdentifier=='Body' and c.TargetView=='MODEL_VIEW']\n"
        "body=contexts[0]\n"
        f"axis={state['axis']!r}\n"
        f"opening_bbox={ob!r}\n"
        f"door_bbox={db!r}\n"
        "def world_matrix(box):\n"
        "    m=np.eye(4)\n"
        "    if axis=='X':\n"
        "        m[:3,3]=[box[0],box[2],box[4]]\n"
        "    else:\n"
        "        m[:3,0]=[0,1,0]\n"
        "        m[:3,1]=[-1,0,0]\n"
        "        m[:3,3]=[box[1],box[2],box[4]]\n"
        "    return m\n"
        "longi=0 if axis=='X' else 2\n"
        "cross=2 if axis=='X' else 0\n"
        "opening=ifcopenshell.api.root.create_entity(ifc,"
        "ifc_class='IfcOpeningElement',name='New Door Clear Opening')\n"
        f"opening.GlobalId={state['opening_guid']!r}\n"
        "opening_rep=ifcopenshell.api.geometry.add_wall_representation(\n"
        "    ifc,context=body,"
        "length=opening_bbox[longi+1]-opening_bbox[longi],"
        "height=opening_bbox[5]-opening_bbox[4],"
        "thickness=opening_bbox[cross+1]-opening_bbox[cross])\n"
        "ifcopenshell.api.geometry.assign_representation(ifc,"
        "product=opening,representation=opening_rep)\n"
        "ifcopenshell.api.geometry.edit_object_placement(ifc,"
        "product=opening,matrix=world_matrix(opening_bbox))\n"
        "ifcopenshell.api.feature.add_feature(ifc,feature=opening,element=host)\n"
        "door=ifcopenshell.api.root.create_entity(ifc,ifc_class='IfcDoor',"
        "name='New Building Entrance Door')\n"
        f"door.GlobalId={state['door_guid']!r}\n"
        "door.OverallWidth=round((door_bbox[longi+1]-door_bbox[longi])*1000,6)\n"
        "door.OverallHeight=round((door_bbox[5]-door_bbox[4])*1000,6)\n"
        "door_rep=ifcopenshell.api.geometry.add_wall_representation(\n"
        "    ifc,context=body,length=door_bbox[longi+1]-door_bbox[longi],"
        "height=door_bbox[5]-door_bbox[4],"
        "thickness=door_bbox[cross+1]-door_bbox[cross])\n"
        "ifcopenshell.api.geometry.assign_representation(ifc,"
        "product=door,representation=door_rep)\n"
        "ifcopenshell.api.geometry.edit_object_placement(ifc,"
        "product=door,matrix=world_matrix(door_bbox))\n"
        + ("" if omit_filling else
           "ifcopenshell.api.feature.add_filling(ifc,"
           "opening=opening,element=door)\n")
        + ("" if omit_storey else
           "storey=host.ContainedInStructure[0].RelatingStructure\n"
           "ifc.create_entity('IfcRelContainedInSpatialStructure',"
           "GlobalId=ifcopenshell.guid.new(),"
           "RelatedElements=(door,),RelatingStructure=storey)\n")
        + "result={'physical_new_door':True,'physical_new_opening':True}\n"
          "commit()\n"
    )


def original_author_repo_only(original:Path,candidate:Path)->dict:
    sys.path.insert(0,str(AUTHOR))
    try:
        scorer=importlib.import_module("data.tests.topological_test_05")
        need(Path(scorer.__file__).resolve()==
             (AUTHOR/"data"/"tests"/f"{TASK}.py").resolve(),
             "Original author repo evaluator source mismatch")
        try:
            values=scorer.execute_test(str(original),str(candidate),None)
        except Exception as exc:
            return {
                "status":"BLOCKED_ORIGINAL_AUTHOR_EVALUATOR_EXCEPTION",
                "exception_class":type(exc).__name__,
                "exception_message_and_original_private_refs_redacted":True,
                "mean_score":None,
                "original_repo_metrics":None,
                "published_paper_scorer_revision_identical_verified":False,
            }
        need(isinstance(values,dict)
             and set(values)=={
                 "object_exists","right_location",
                 "right_dimensions","integrity_constraint"}
             and all(isinstance(v,(bool,float,int))
                     and math.isfinite(float(v))
                     and 0<=float(v)<=1
                     for v in values.values()),
             "Original author repo mixed Boolean/float metrics changed")
        return {
            "status":"ORIGINAL_REPOSITORY_EVALUATOR_MIXED_BOOL_FLOAT_METRICS",
            "mean_score":round(sum(map(float,values.values()))/len(values),6),
            "original_repo_metrics":dict(sorted(values.items())),
            "published_paper_scorer_revision_identical_verified":False,
        }
    finally:
        sys.path.remove(str(AUTHOR))


def build_report()->dict:
    need(file_hash(PARENT)==PARENT_SHA
         and file_hash(FROZEN)==FROZEN_SHA,
         "Prior frozen original source-native evidence drift")
    previous=json.loads(PARENT.read_text(encoding="utf8"))
    frozen=json.loads(FROZEN.read_text(encoding="utf8"))
    need(previous["v062_new_original_native_task_supported"]==
             ["topological_test_12"]
         and previous["actual_LLM_generated_model_trials"]==0
         and sorted(frozen["prospective_six_source_heldout_task_ids"])==
             FIXED_SIX,
         "Frozen original six-source cohort or parent research drift")
    rights=assert_original_source_rights_unchanged_v057()
    need(rights["status"]=="BLOCKED_NO_MODEL_PROVIDER_TRIAL",
         "No-trials rights guard unexpectedly lifted")
    rows={r["test_id"]:r for r in public_45(AUTHOR,DATA)}
    need(len(rows)==45
         and len({r["original_ifc_sha256"] for r in rows.values()})==31,
         "Original 45 public tasks/31 IFC source files changed")
    row=rows[TASK]
    original=DATA/"ifc"/row["original_source_ifc_relpath"]
    need(row["original_ifc_sha256"]==SOURCE_SHA
         and file_hash(original)==SOURCE_SHA,
         "Exact source IFC4X3 native door creation original SHA changed")
    model=source_ifc(original,source_sha=SOURCE_SHA)
    need(len(list(model))==416 and len(model.by_type("IfcRoot"))==116,
         "Original native IFC source STEP/Root population changed")
    outer,outer_index=_source_host_by_category(model,"OUTER")
    inner,inner_index=_source_host_by_category(model,"INNER")
    initial=initial_full_source_v063(original,source_sha=SOURCE_SHA)
    compact=initial_compact_source_v063(original,source_sha=SOURCE_SHA)
    cases=[
        ("PUBLIC_EXTERIOR_CSG_THROUGH_DOOR_VALID",outer,outer_index,
         "OUTER",.9,2.1,True),
        ("PUBLIC_INTERIOR_WALL_DOOR_SEMANTICALLY_WRONG",inner,inner_index,
         "INNER",.9,2.1,False),
        ("PUBLIC_EXTERIOR_TOO_NARROW_TOO_SHORT_DOOR_WRONG",
         outer,outer_index,"OUTER",.45,1.2,False),
    ]
    results=[]
    with TemporaryDirectory(prefix="v063-TRUE-LOCAL-LINUX-IFC4X3-DOOR-") as scratch:
        scratch=Path(scratch)
        for j,(label,wall,host_index,category,width,height,correct) in enumerate(cases):
            state=_fixture(label,wall,category,width,height)
            D=DirectFullState063(original,scratch/f"{j}/D")
            M=DirectManagedState063(original,scratch/f"{j}/M")
            I=LiveDockerPython063(original,scratch/f"{j}/I")
            reads=[x.call("read_building_xml",{"query":"source"}) for x in (D,M,I)]
            need(all(r["status"]=="ok" for r in reads)
                 and reads[0]["xml"]==reads[1]["xml"]==reads[2]["xml"]
                 and reads[0]["xml"].encode("utf8")==initial,
                 "Original IFC D_FULL/D_MANAGED/Docker I initial exact source XML parity failed")
            full=_populate_xml(initial,state,managed=False)
            partial=_populate_xml(compact,state,managed=True)
            source_code=_developer_real_python_code(state,host_index)
            d=D.call("submit_building_xml",{"xml_text":full})
            m=M.call("submit_managed_final_state",{"xml_text":partial})
            i=I.call("execute_ifc_code",{"code":source_code})
            need(d["status"]==m["status"]==i["status"]=="ok"
                 and i["actual_os_isolated_pinned_Linux_Docker_Python_executed"]
                 and i["actual_linux_sandbox_backend"]=="linux_docker_sandbox"
                 and D.current_xml==M.current_xml==full.encode("utf8"),
                 "Actual original native IFC4X3 Door+Opening D/I real execution failed")
            triplets=[]
            pred=[]
            grades=[]
            for x in (D,M,I):
                native=independent_real_original_door_scope_v063(
                    original,x.output_ifc,source_sha=SOURCE_SHA)
                need(native["status"]==
                     "V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS"
                     and native["native_real_wall_full_thickness_boolean_volume_removed_m3"]>.1
                     and native["original_IFC4X3_schema_errors_introduced"]==0,
                     "Genuine native 3D full-thickness CSG cut/IFC root/schema blocked")
                triplets.append(semantic_digest_after_native_oracle_v063(native))
                pred.append(source_public_exterior_pass_v063(
                    original,x.output_ifc,source_sha=SOURCE_SHA))
                grades.append(original_author_repo_only(original,x.output_ifc))
            need(triplets[0]==triplets[1]==triplets[2],
                 "Actual D/M/Docker I semantic native Door+Opening outcome differs")
            need(pred[0]==pred[1]==pred[2],
                 "Public original-source physical exterior predicate differs")
            need(pred[0]["physically_outside_connection_proxy_pass"] is correct,
                 "Original public physical exterior/dim predicate test incorrect")
            need(grades[0]==grades[1]==grades[2],
                 "Unmodified original author mixed metric differs across native D/I")
            results.append({
                "developer_source_only_physical_case":label,
                "host_original_Wall_GUID_redacted":True,
                "new_door_opening_IFC_GUIDs_redacted":True,
                "native_D_full_XML_bytes":len(full.encode("utf8")),
                "native_D_managed_XML_bytes":len(partial.encode("utf8")),
                "native_I_developer_Python_bytes":len(source_code.encode("utf8")),
                "all_D_I_original_native_semantic_digest_SHA256":triplets[0],
                "native_original_IFC_full_wall_CSG_cut_confirmed":True,
                "source_original_Wall_and_other_416_STEP_entities_unchanged":True,
                "source_IFC4X3_schema_new_errors":0,
                "public_source_exterior_physical_semantic_evaluator_only":pred[0],
                "original_author_repository_mixed_score_evaluator_only":grades[0],
                "actual_pinned_isolated_Linux_Docker_general_Python_executed":True,
                "actual_model_generated_output":False,
            })
            need(file_hash(original)==SOURCE_SHA,
                 "Original IFC accidentally modified by D/I native case")
        # Actual Docker success followed by actual native invalid model:
        # create a SECOND Door in existing I last-good IFC; strict source
        # gate must fail and preserve last-good IFC SHA exactly.
        invalid=LiveDockerPython063(original,scratch/"invalid_after_good")
        positive_state=_fixture("GOOD_CHAIN",outer,"OUTER",.9,2.1)
        first=invalid.call("execute_ifc_code",{
            "code":_developer_real_python_code(positive_state,outer_index)})
        need(first["status"]=="ok" and invalid.output_ifc is not None,
             "Actual local Docker initial valid native IFC failed")
        lastsha=file_hash(invalid.output_ifc)
        second=invalid.call("execute_ifc_code",{"code":(
            "import ifcopenshell.api.root\n"
            "door=ifcopenshell.api.root.create_entity("
            "ifc,ifc_class='IfcDoor',name='UNSUPPORTED_SECOND_DOOR')\n"
            "result={'bad_second_door':True}\n"
            "commit()\n"
        )})
        need(second["status"]=="error"
             and second["native_ifc_committed"] is False
             and file_hash(invalid.output_ifc)==lastsha,
             "Actual Docker invalid second door overwrote last-good IFC")
        # Actual shallow Opening and Door combination: valid true Docker
        # worker edits but independent source full-thickness CSG gate must
        # reject. Relationship chain is present but physical passage false.
        shallow=LiveDockerPython063(original,scratch/"invalid_shallow_cut")
        shall=shallow.call("execute_ifc_code",{"code":_developer_real_python_code(
            _fixture("SHALLOW",outer,"OUTER",.9,2.1),
            outer_index,opening_depth_fraction=.2)})
        need(shall["status"]=="error"
             and shall["native_ifc_committed"] is False
             and shallow.output_ifc is None,
             "Actual Docker shallow, non-through host cut was wrongly admitted")
        # Missing new Door->Opening filling relation also rejected.
        nofill=LiveDockerPython063(original,scratch/"invalid_no_fill")
        nfr=nofill.call("execute_ifc_code",{"code":_developer_real_python_code(
            _fixture("NO_FILL",outer,"OUTER",.9,2.1),
            outer_index,omit_filling=True)})
        need(nfr["status"]=="error"
             and nfr["native_ifc_committed"] is False
             and nofill.output_ifc is None,
             "Actual Docker unhosted/no-filling Door incorrectly admitted")
        # D last-good whole final state after malformed/incomplete roster.
        goodD=DirectFullState063(original,scratch/"goodD_bad_xml")
        first=goodD.call("submit_building_xml",{"xml_text":_populate_xml(
            initial,_fixture("D_GOOD",outer,"OUTER",.9,2.1),
            managed=False)})
        need(first["status"]=="ok","Actual complete D original Door failed")
        priorXML=goodD.current_xml
        priorSHA=file_hash(goodD.output_ifc)
        badXML=etree.fromstring(priorXML)
        badXML[1].remove(badXML[1][0])
        failed=goodD.call("submit_building_xml",{
            "xml_text":etree.tostring(badXML,encoding="utf8").decode("utf8")})
        need(failed["status"]=="error"
             and goodD.current_xml==priorXML
             and file_hash(goodD.output_ifc)==priorSHA,
             "D invalid complete seven original wall XML lost last-good IFC")
    need(len(results)==3
         and len({x["developer_source_only_physical_case"] for x in results})==3
         and all(x["actual_pinned_isolated_Linux_Docker_general_Python_executed"]
                 for x in results),
         "Three true original source developer cases missing")
    need(file_hash(original)==SOURCE_SHA,"Original IFC mutated")
    return {
        "status":"V063_SOURCE_CSG_EXTERIOR_DOOR_D_FULL_MANAGED_REAL_DOCKER_I_AND_AUTHOR_METRIC_DIVERGENCE_PASS",
        "issue":"https://github.com/pikaybh/bim-markup-bench/issues/241",
        "parent_v062_exact_HEAD":PARENT_HEAD,
        "parent_v062_frozen_report_SHA256":PARENT_SHA,
        "v058_preselected_six_frozen_SHA256":FROZEN_SHA,
        "original_45_public_task_count":45,
        "original_31_unique_IFC_source_model_count":31,
        "v058_six_task_selection_preserved":FIXED_SIX,
        "new_native_original_task_admitted_v063":[TASK],
        "five_of_six_original_fixed_source_native_developer_supported":
            sorted(SUPPORTED),
        "remaining_original_fixed_task_UNSUPPORTED":["geometry_test_03"],
        "total_original_task_specific_native_developer_supported":9,
        "other_original_45_tasks_not_native_developer_verified":36,
        "original_source_IFC_SHA256":SOURCE_SHA,
        "original_source_IFC_schema":"IFC4X3",
        "original_public_question_SHA256":row["public_question_sha256"],
        "original_author_repo_evaluator_module_SHA256":
            file_hash(AUTHOR/"data"/"tests"/f"{TASK}.py"),
        "original_source_Wall_count":7,
        "original_source_Slab_count":2,
        "original_source_IfcSpace_count":0,
        "original_source_IfcDoor_count":0,
        "original_source_IfcOpeningElement_count":0,
        "original_source_path_connection_count":9,
        "original_source_STEP_entity_count":416,
        "original_source_Root_GUID_count":116,
        "source_native_length_unit":"MILLIMETER",
        "world_mesh_length_unit":"METRE",
        "source_world_exterior_envelope_bbox_M":source_envelope_v063(model),
        "original_full_source_read_identical_all_D_I":True,
        "original_full_source_xml_utf8_bytes":len(initial),
        "original_compact_managed_source_xml_utf8_bytes":len(compact),
        "original_existing_seven_Wall_full_roster_immutable":True,
        "explicit_ONE_new_door_and_ONE_new_opening_final_entities":True,
        "real_D_FULL_original_native_IFC_cases":3,
        "real_D_MANAGED_original_native_IFC_cases":3,
        "real_pinned_Linux_Docker_I_native_IFC_cases":3,
        "actual_original_native_IFC_D_I_developer_cases":9,
        "original_IFC_new_schema_error_count":0,
        "all_three_D_I_original_native_semantic_DIGESTS_equal":True,
        "original_author_repo_mixed_Boolean_float_metrics_preserved":True,
        "original_author_score_equal_for_valid_exterior_and_invalid_interior":True,
        "source_original_IFC_has_NO_IfcSpace_true_inside_room_graph_not_verifiable":True,
        "public_source_outer_envelope_proxy_physically_independent_of_author_grader":True,
        "actual_Docker_shallow_non_through_wall_opening_rejected":True,
        "actual_Docker_unfilled_door_relation_rejected":True,
        "actual_Docker_valid_then_second_door_rejected_last_IFC_sha_preserved":True,
        "D_complete_final_good_then_incomplete_7_Wall_roster_last_SHA_XML_preserved":True,
        "source_native_IfcOpenShell_compiler_versus_arbitrary_I_edit_affordance_not_equivalent":True,
        "source_developer_exposure_destroys_unseen_original_six_confirmatory_holdout":True,
        "original_source_IFC_provider_uploads":0,
        "actual_model_generated_trials":0,
        "paid_provider_calls":0,
        "underlying_original_IFC_rights_and_provider_transfer_approval":False,
        "approved_model_snapshot_D_I_actual_tokens_cost_budget":None,
        "published_paper_official_scoring_version_parity_verified":False,
        "published_paper_official_model_score":None,
        "developer_only_real_source_door_opening_controls":results,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    z=p.add_mutually_exclusive_group(required=True)
    z.add_argument("--write",action="store_true")
    z.add_argument("--check",action="store_true")
    args=p.parse_args()
    report=canonical(build_report())
    if args.write:
        with REPORT.open("xb") as f:
            f.write(report)
    else:
        need(REPORT.is_file() and not REPORT.is_symlink()
             and REPORT.read_bytes()==report,
             "Real original source D/I pinned Docker CSG Door report replay drift")
    print("V063_ORIGINAL_SOURCE_CSG_DOOR_NATIVE_D_I=PASS "
          "NATIVE_IFCS=9/9 ACTUAL_LOCAL_PINNED_LINUX_DOCKER=3/3 "
          "MODEL_TRIALS=0 PAID=0 FROZEN_SHA256="+sha256(report).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
