"""Issue #247: REAL local IFC4 D_FULL / D_MANAGED / pinned-Docker I_NATIVE proof.

Sources are self-authored deterministic IFC4 synthesis, NOT GNI IFCs, original
BIBIMBAP test assets, independent blind samples or scored model outputs.
This audit may execute native geometry and local isolated Docker Python, but
NO paid/API/model call, externally supplied IFC, original grader, hidden GT,
rights approval, archive download, network or source-specific benchmark answer.

Four synthetic cases cross 2 native-length units x 2 wall orientations.
Compare full native IFC CSG/geometry/topology via STEP-neutral independent
native scope; keep source-bound declarative XML and independent Python paths.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree

from tools import bibimbap_v066_ifc4_synthetic_host as synth
from tools import bibimbap_v066_ifc4_source_neutral_door as door
from tools import bibimbap_v066_ifc4_native_semantic_admission as gate
from tools import audit_bibimbap_v066_step_identity_fairness as step
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor,file_hash,PINNED_DOCKER_IMAGE
)
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v057_provenance import (
    refuse_all_model_trials_v057,ProviderTrialBlocked057,
)
from tools import audit_bibimbap_v066_zenodo_handoff as parent

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_synthetic_ifc4_DI_20261119.json"
PARENT_SHA="f089801dd7131338bc3b45821d319424cbd6ba4dc28287f07346aaf5cd9ed631"
CASES=(("metre","X"),("metre","Y"),("millimetre","X"),("millimetre","Y"))
NEGATIVE_XML=("source_sha_corruption","missing_original_wall","forged_operation_node","wrong_geometry_extent")
NEGATIVE_IFC=("changed_unrelated_source_slab","orphan_native_cartesian_point","removed_new_filling_relationship")
NAMESPACE=uuid.UUID("b06d2045-1e4c-4a47-99fa-b2f7ba3b02fc")

def need(value,why):
    if not value: raise AssertionError(why)

def canonical(report):
    return (json.dumps(report,ensure_ascii=False,sort_keys=True,
                       indent=2,allow_nan=False)+"\n").encode("utf8")

def _guid(label):
    return ifcopenshell.guid.compress(uuid.uuid5(NAMESPACE,label).hex)

def engineering_state(model,unit,axis):
    """Construct self-authored engineering geometry, NOT a benchmark GT."""
    walls=model.by_type("IfcWall")
    need(model.schema=="IFC4" and len(walls)==1,
         "Only precisely authored blank IFC4 synthetic source")
    ob=((2.0,3.05),(-.1,.3),(0.,2.2)) if axis=="X" else (
        (-.3,.1),(2.0,3.05),(0.,2.2))
    db=((2.025,3.025),(.07,.13),(0.,2.1)) if axis=="X" else (
        (-.13,-.07),(2.025,3.025),(0.,2.1))
    return {
        "host":walls[0].GlobalId,
        "opening_guid":_guid("IFC4-"+unit+"-"+axis+"-opening"),
        "door_guid":_guid("IFC4-"+unit+"-"+axis+"-door"),
        "axis":axis,"opening_box":ob,"door_box":db,
    }

def complete_final_state(initial,desired,*,managed):
    """Semantic addition of complete final Door and Opening state, no ops."""
    doc=etree.fromstring(initial)
    insertion=doc[1] if managed else doc[2]
    need(not len(insertion),"Expected original empty final-state new entities")
    for element,guid_name,foreign_name,foreign_value,box_name in (
        ("Opening","opening_guid","hostOriginalWallGuid",
         desired["host"],"opening_box"),
        ("Door","door_guid","fillsOpeningGuid",
         desired["opening_guid"],"door_box"),
    ):
        etree.SubElement(insertion,door.Q+element,{
            "guid":desired[guid_name],foreign_name:foreign_value,
            **door._box_attrs(desired[box_name]),
        })
    return etree.tostring(doc,encoding="utf8",xml_declaration=True)

def pure_independent_native_python(state):
    """Generic standalone I control; no D module, author scorer or GT."""
    data={
        "axis":state["axis"],
        "opening_guid":state["opening_guid"],
        "door_guid":state["door_guid"],
        "opening_box":tuple(x for pair in state["opening_box"] for x in pair),
        "door_box":tuple(x for pair in state["door_box"] for x in pair),
    }
    code=r"""
import numpy as np
import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.feature
import ifcopenshell.util.unit

# Independent edit using real native IFC loaded by the pinned Python executor.
walls=sorted(ifc.by_type('IfcWall'), key=lambda wall:wall.GlobalId)
assert len(walls)==1
host=walls[0]
contexts=[c for c in ifc.by_type('IfcGeometricRepresentationSubContext')
          if c.ContextIdentifier=='Body' and c.TargetView=='MODEL_VIEW']
assert len(contexts)==1
body=contexts[0]
axis=__AXIS__
opening_box=__OPENING_BOX__
door_box=__DOOR_BOX__

def orient_world(box):
    world=np.eye(4)
    if axis=='X':
        world[:3,3]=[box[0],box[2],box[4]]
    else:
        world[:3,0]=[0.,1.,0.]
        world[:3,1]=[-1.,0.,0.]
        world[:3,3]=[box[1],box[2],box[4]]
    return world

long_index=0 if axis=='X' else 2
cross_index=2 if axis=='X' else 0
opening=ifcopenshell.api.root.create_entity(
    ifc,ifc_class='IfcOpeningElement',name='Independent Native Door Opening')
opening.GlobalId=__OPENING_GUID__
orep=ifcopenshell.api.geometry.add_wall_representation(
    ifc,context=body,
    length=opening_box[long_index+1]-opening_box[long_index],
    height=opening_box[5]-opening_box[4],
    thickness=opening_box[cross_index+1]-opening_box[cross_index])
ifcopenshell.api.geometry.assign_representation(
    ifc,product=opening,representation=orep)
ifcopenshell.api.geometry.edit_object_placement(
    ifc,product=opening,matrix=orient_world(opening_box))
ifcopenshell.api.feature.add_feature(ifc,feature=opening,element=host)

new_door=ifcopenshell.api.root.create_entity(
    ifc,ifc_class='IfcDoor',name='Independent Native Door')
new_door.GlobalId=__DOOR_GUID__
scale=ifcopenshell.util.unit.calculate_unit_scale(ifc)
new_door.OverallWidth=round(
    (door_box[long_index+1]-door_box[long_index])/scale,6)
new_door.OverallHeight=round((door_box[5]-door_box[4])/scale,6)
drep=ifcopenshell.api.geometry.add_wall_representation(
    ifc,context=body,
    length=door_box[long_index+1]-door_box[long_index],
    height=door_box[5]-door_box[4],
    thickness=door_box[cross_index+1]-door_box[cross_index])
ifcopenshell.api.geometry.assign_representation(
    ifc,product=new_door,representation=drep)
ifcopenshell.api.geometry.edit_object_placement(
    ifc,product=new_door,matrix=orient_world(door_box))
ifcopenshell.api.feature.add_filling(ifc,opening=opening,element=new_door)
storey=host.ContainedInStructure[0].RelatingStructure
ifc.create_entity('IfcRelContainedInSpatialStructure',
    GlobalId=ifcopenshell.guid.new(),RelatedElements=(new_door,),
    RelatingStructure=storey)
result={'native_door_opening_added':True}
commit()
"""
    for token,value in (
        ("__AXIS__",repr(data["axis"])),
        ("__OPENING_BOX__",repr(data["opening_box"])),
        ("__DOOR_BOX__",repr(data["door_box"])),
        ("__OPENING_GUID__",repr(data["opening_guid"])),
        ("__DOOR_GUID__",repr(data["door_guid"])),
    ):
        need(code.count(token)==1,"Standalone I code template token drift")
        code=code.replace(token,value)
    need("commit()" in code and "tools." not in code
         and "data.tests" not in code
         and "private_target" not in code.lower()
         and "target_guid" not in code.lower()
         and "author_scorer" not in code.lower(),
         "Independent native Python must not use D, grader, GT or task ID")
    return code

def _bad_xml(source,sha,kind,complete):
    data=etree.fromstring(complete)
    if kind=="source_sha_corruption":
        data.attrib["sourceIFCSha256"]="f"*64
    elif kind=="missing_original_wall":
        data[1].remove(data[1][0])
    elif kind=="forged_operation_node":
        etree.SubElement(data[2],door.Q+"Move",{"target":"SYNTHETIC"})
    elif kind=="wrong_geometry_extent":
        # Same original real wall, new door extends outside opening.
        box=data[2][1]
        box.set("maxXM","4.025000")
    else:raise AssertionError("Unknown deliberately invalid XML")
    return etree.tostring(data,encoding="utf8",xml_declaration=True)

def _native_mutated(base:Path,output:Path,kind,state):
    model=ifcopenshell.open(str(base))
    if kind=="changed_unrelated_source_slab":
        slab=model.by_type("IfcSlab")[0]
        slab.Name="UNAUTHORIZED_SOURCE_SLAB_MUTATION"
    elif kind=="orphan_native_cartesian_point":
        model.create_entity("IfcCartesianPoint",Coordinates=(123456.,654321.,1.))
    elif kind=="removed_new_filling_relationship":
        rel=next(x for x in model.by_type("IfcRelFillsElement")
                 if x.RelatedBuildingElement.GlobalId==state["door_guid"])
        model.remove(rel)
    else:raise AssertionError("Unknown deliberately invalid native IFC")
    model.write(str(output))
    need(output.is_file(),"Bad native test file not written")

def run_case(work:Path,unit:str,axis:str):
    tag=unit+"-"+axis
    folder=work/tag
    folder.mkdir()
    source=synth.write_fresh(folder/"source.ifc",unit=unit,axis=axis)
    sha=file_hash(source)
    original=door.source_model(source,sha)
    state=engineering_state(original,unit,axis)
    full=door.full_initial_xml(source,sha)
    managed=door.managed_initial_xml(source,sha)
    d_full=complete_final_state(full,state,managed=False)
    d_managed=complete_final_state(managed,state,managed=True)
    parsed=door.parse_full_xml(source,sha,d_full)
    expanded,parsed_managed=door.expand_managed_xml(source,sha,d_managed)
    need(parsed==parsed_managed==state and expanded==d_full,
         "IFC4 complete declarative final state D_FULL and D_MANAGED differ")
    output={}
    for label,parsed_state in (("D_FULL",parsed),("D_MANAGED",parsed_managed)):
        target=folder/(label+".ifc")
        door.compile_hosted_door(source,sha,parsed_state,target)
        outcome=gate.post_native_semantic_gate(source,sha,target)
        need(outcome["status"]==gate.STATUS,
             "IFC4 native D output rejected by independent step-neutral gate")
        output[label]=(target,outcome)
    # Real local Python executor uses a new original source IFC clone.
    script=pure_independent_native_python(state)
    sandbox=folder/"I_NATIVE"
    sandbox.mkdir()
    shutil.copyfile(source,sandbox/"current.ifc")
    execution=DockerIFCExecutor().run(sandbox,script)
    need(execution["status"]=="ok"
         and execution.get("committed") is True
         and execution.get("backend")=="linux_docker_sandbox",
         "IFC4 general IfcOpenShell I_NATIVE not really committed in Linux Docker")
    i_native=sandbox/"current.ifc"
    i_outcome=gate.post_native_semantic_gate(source,sha,i_native)
    need(i_outcome["status"]==gate.STATUS,
         "IFC4 I code did not pass native IFc scope")
    output["I_NATIVE"]=(i_native,i_outcome)
    digests={
        arm:result["native_physical_edit_semantic_SHA256"]
        for arm,(_,result) in output.items()
    }
    need(len(set(digests.values()))==1,
         "Actual IFC4 full native geometry/topology differs D vs I")
    # STEP IDs are serialization artifacts and cannot determine correctness.
    relabeled,idx=step.relabel_spf(output["D_FULL"][0].read_bytes())
    relabel_file=folder/"step_relabel.ifc"
    relabel_file.write_bytes(relabeled)
    step_result=gate.post_native_semantic_gate(source,sha,relabel_file)
    need(step_result["native_physical_edit_semantic_SHA256"]==
         next(iter(digests.values())),
         "STEP-reencoded native IFC4 falsely rejected")
    negatives={}
    for kind in NEGATIVE_XML:
        try:door.parse_full_xml(source,sha,_bad_xml(source,sha,kind,d_full))
        except door.NeutralDoor065Error:
            negatives[kind]=True
        else:raise AssertionError("Malformed IFC4 declarative source XML was admitted "+kind)
    for kind in NEGATIVE_IFC:
        wrong=folder/(kind+".ifc")
        _native_mutated(output["D_FULL"][0],wrong,kind,state)
        try:gate.post_native_semantic_gate(source,sha,wrong)
        except gate.SemanticNative066Error:
            negatives[kind]=True
        else:raise AssertionError("Bad IFC4 native scope unexpectedly admitted "+kind)
    need(len(negatives)==7 and all(negatives.values()),
         "Not all negative IFC4 fixtures were rejected")
    need(file_hash(source)==sha,"Synthetic original source modified by any D/I arm")
    return {
        "synthetic_developer_unit":unit,
        "synthetic_original_IFC_schema":original.schema,
        "synthetic_wall_axis":axis,
        "source_original_ifc_SHA256":sha,
        "source_ifc_bytes":source.stat().st_size,
        "original_IFC_wall_count":len(original.by_type("IfcWall")),
        "unrelated_opaque_original_slab_count":len(original.by_type("IfcSlab")),
        "full_initial_XML_UTF8_bytes":len(full),
        "managed_initial_XML_UTF8_bytes":len(managed),
        "full_final_state_XML_UTF8_bytes":len(d_full),
        "managed_final_state_XML_UTF8_bytes":len(d_managed),
        "independent_I_Python_code_UTF8_bytes":len(script.encode("utf8")),
        "native_D_FULL_D_MANAGED_I_PHY_semantic_digest":next(iter(digests.values())),
        "all_three_IFC4_native_semantics_equal":True,
        "actual_IFC_wall_CSG_cut_m3":i_outcome["actual_wall_CSG_volume_removed_m3"],
        "new_IFC_schema_error_count":i_outcome["new_schema_findings"],
        "true_linux_docker_Ifcopenshell_I_committed":True,
        "STEP_numeric_relabel_native_equivalent":True,
        "synthetic_negative_XML_and_IFC_rejection_cases":negatives,
        "unmodified_original_IFC_Source_SHA_verified":True,
        "original_hidden_BIBIMBAP_author_grader_read":False,
        "independent_blind_source_certified":False,
        "model_generated_attempts":0,
    }

def build_report():
    need(file_hash(parent.REPORT)==PARENT_SHA,
         "Prior Zenodo GNI metadata/rights frozen audit changed")
    pre=live_pinned_local_runtime_admission_v052()
    need(pre["status"]=="RUNTIME_ADMITTED",
         "Pinned Linux Docker is required; simulator is not comparable")
    try:refuse_all_model_trials_v057({"owner_consent":True,"paid_budget":100})
    except ProviderTrialBlocked057:pass
    else:raise AssertionError("Original IFC provider trial refusal bypassed")
    with TemporaryDirectory(prefix="v066-synthetic-ifc4-DI-") as t:
        cases=[run_case(Path(t),unit,axis) for unit,axis in CASES]
    need(len(cases)==4
         and {(x["synthetic_developer_unit"],x["synthetic_wall_axis"])
               for x in cases}==set(CASES)
         and all(x["all_three_IFC4_native_semantics_equal"]
                 for x in cases),"IFC4 synthetic case coverage did not complete")
    return {
        "status":"V066_IFC4_SYNTHETIC_FULL_MANAGED_AND_REAL_DOCKER_I_NATIVE_COMPATIBILITY_PASS_NOT_BLIND",
        "issue":247,
        "audit_kind":"DEVELOPER_GENERATED_IFC4_ONLY_NOT_GNI_ARCHIVE_NOT_BLIND",
        "parent_gni_Zenodo_frozen_report_SHA256":PARENT_SHA,
        "source_generator_module_sha256":file_hash(
            ROOT/"tools"/"bibimbap_v066_ifc4_synthetic_host.py"),
        "expanded_IFC4_compiler_module_sha256":file_hash(
            ROOT/"tools"/"bibimbap_v066_ifc4_source_neutral_door.py"),
        "STEP_independent_IFC4_native_scope_module_sha256":file_hash(
            ROOT/"tools"/"bibimbap_v066_ifc4_native_semantic_admission.py"),
        "pinned_local_Docker_image_digest":PINNED_DOCKER_IMAGE,
        "native_schema":"IFC4",
        "units_tested":["metre","millimetre"],
        "host_wall_axes_tested":["X","Y"],
        "unique_developer_generated_original_IFC4_models":4,
        "positive_actual_native_IFC4_D_full_managed_I_outputs":12,
        "STEP_id_reencoded_native_ifc_equivalent_variants":4,
        "negative_actual_IFC4_XML_and_native_mutations_rejected":28,
        "model_provider_calls":0,
        "original_bibimbap_or_gni_ifc_files_read":0,
        "new_external_ifc_uploads":0,
        "original_author_private_task_or_GT_grader_read":False,
        "real_independent_blind_source_count":0,
        "independently_licensed_GNI_ifc_member_validated":False,
        "IFC4_support_scope_only":
            "ONE hosted Door+Opening creation on represented axis-aligned Walls, complete existing wall roster, metre/mm, ONE new source-independent semantic diff, original native assets opaque; not universal IFC4 or Window IFC4",
        "all_synthetic_IFC4_native_results":cases,
        "permission_to_start_original_or_gni_model_trials":False,
        "future_GNI_IFC4_asset_and_task_admission_still_requires":
            "Per-member source rights, creator/embedded content, separate independent hidden task/evaluator, model/tool/read budget/owner consent",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    opts=p.parse_args()
    raw=canonical(build_report())
    if opts.write:
        with REPORT.open("xb") as f:f.write(raw)
    else:
        need(REPORT.read_bytes()==raw,
             "Synthetic IFC4 Docker D/I report not reproducible byte-for-byte")
    print("V066_SYNTHETIC_IFC4_"+("WRITE" if opts.write else "CHECK")+
          "=PASS sources=4 D_I_outputs=12 STEP_neutral=4 negatives=28 model_calls=0")

if __name__=="__main__":
    main()
