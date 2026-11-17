"""v0.48 eight real original IFC semantic control pairs (4 positive, 4 negative).

Positive controls computed from PUBLIC original IFC geometry/IFC containment
and original question (NOT from private author evaluator or hidden GT).
Negative controls are developer illustrative source-native edits from frozen
v0.45 that intentionally do not solve the ORIGINAL questions.
XML and restricted Python arms BOTH apply exact same real native IFC edits,
pass independent v0.45 scope/geometry-preservation oracle, and are checked
by a SEPARATE source-native geometric semantic checker. No paid model/trials.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import argparse
import itertools
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v047_restricted_python_native_session import (
    MatchedOriginalXmlSession047,RestrictedOriginalPythonSession047,
    typed_python_to_exact_original_xml,parse_single_restricted_python_call)
from tools.audit_bibimbap_v045_original4_native_mutations import (
    make_illustrative_plan)
from tools.audit_bibimbap_v047_original4_matched_restricted import (
    illustrative_python_from_original_xml)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,OriginalSemantic048Error,TOL_M,
    ORIGINAL_PREDICATES)
from src.runtime.experimental_v45_original_native_mutations import (
    Q,parse_original_native_edit_plan_v045,_body_solid)
from src.runtime.experimental_v44_original_native_step_readonly import PINS

ROOT=Path(__file__).resolve().parents[1]
ISSUE="https://github.com/pikaybh/bim-markup-bench/issues/211"
BASE_HEAD="a9a0a5c4ba4387995ca38543884fdbcb4705e7f6"
V047_REPORT="reports/bibimbap_v047_original4_restricted_XML_Python_native_matched_20261117.json"
V047_SHA="cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa"
V046_REPORT="reports/bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json"
V046_SHA="beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f"
TASKS=("geometry_test_14","geometry_test_15","topological_test_11",
       "topological_test_17")


def need(cond,msg):
    if not cond:
        raise AssertionError(msg)


def _named_slab(question,model):
    matches=re.findall(r"\bid\s+([A-Za-z0-9_$]{22})(?=\W|$)",
                       question,re.IGNORECASE)
    need(len(matches)==1
         and model.by_guid(matches[0]) is not None
         and model.by_guid(matches[0]).is_a("IfcSlab"),
         "Developer original public question does not identify one native source slab")
    return model.by_guid(matches[0])


def _developer_rectangle_fix_source_only(model)->tuple[str,float,float]:
    """Independent source-native IfcLocalPlacement 4-centre enumeration.

    Does not query the v0.48 semantic oracle, candidate or private grader.
    """
    import numpy as np
    columns=model.by_type("IfcColumn")
    need(len(columns)==4,"Original four published Column placements changed")
    points={}
    for c in columns:
        mat=ifcopenshell.util.placement.get_local_placement(c.ObjectPlacement)
        points[c.GlobalId]=tuple(round(float(mat[k,3])/1000,6) for k in (0,1))
    possibilities=[]
    for guid in sorted(points):
        fixed={x:y for x,y in points.items() if x!=guid}
        xs=sorted(set(p[0] for p in fixed.values()))
        ys=sorted(set(p[1] for p in fixed.values()))
        if len(xs)!=2 or len(ys)!=2:
            continue
        for target in itertools.product(xs,ys):
            if target==points[guid]:
                continue
            corners=set(fixed.values())|{target}
            if len(corners)==4 and corners==set(itertools.product(xs,ys)):
                possibilities.append((guid,target[0],target[1]))
    # A single-column rectangle in the original IFC admits more than one
    # geometrically correct move (either mismatched upper-row column).
    # The PUBLIC question does not fix a target GUID; do not invent hidden GT.
    need(len(possibilities)>=1,
         "Original source has no physically valid single-column rectangle move")
    return sorted(possibilities)[0]


def _developer_delete_set_from_original_storey(model,named_slab_guid):
    """Independent writer control derived from IFC containment, not v0.48 oracle.

    Original native IFC has no direct IfcRelConnects to the named Slab. The
    new independent v0.48 semantic oracle *separately* tests physical contact
    and requires exactly the same partition as this source containment.
    """
    container={}
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        for p in rel.RelatedElements:
            if p.is_a("IfcColumn") or p.is_a("IfcSlab"):
                need(p.GlobalId not in container,
                     "Original source has ambiguous duplicate Storey containment")
                container[p.GlobalId]=rel.RelatingStructure.GlobalId
    need(named_slab_guid in container,"Original named slab missing source Storey")
    cols=model.by_type("IfcColumn")
    need(len(cols)==10,"Original source expected ten real Columns")
    delete=sorted(c.GlobalId for c in cols
                  if container.get(c.GlobalId)!=container[named_slab_guid])
    need(len(delete)==5,"Original source does not have five unrelated upper Columns")
    return delete


def positive_developer_source_edit(
        original_xml:bytes,source:Path,tid:str,question:str)->bytes:
    """Four source/question-conditioned POSITIVE developer physical controls.

    No hardcoded IFC GUIDs, source positions, dimensions, ground truth,
    confidential benchmark labels, private scorer or exported answer files.
    These values may pass the independent RESEARCH geometric predicates;
    that does NOT imply author benchmark scorer equivalence.
    """
    model=ifcopenshell.open(str(source))
    root=etree.fromstring(original_xml)
    need(root.tag==Q+"Building" and len(root)==2
         and root[1].tag==Q+"NativeEditPlan" and len(root[1])==0,
         "Original v0.45 edit plan source became editable/tampered")
    plan=root[1]
    if tid=="geometry_test_14":
        slab=model.by_type("IfcSlab")
        need(len(slab)==1,"Original published Slab population changed")
        solid=_body_solid(slab[0],mapped=False)
        sizes=[float(solid.SweptArea.XDim)/1000,
               float(solid.SweptArea.YDim)/1000]
        need(abs(sizes[0]-sizes[1])>.1,
             "Original Slab no longer needs one side lengthened")
        new=max(sizes)
        etree.SubElement(plan,Q+"SetSlabRectangleDimensions",{
            "ifcGuid":slab[0].GlobalId,
            "newXDimM":str(round(new,6)),
            "newYDimM":str(round(new,6)),
        })
    elif tid=="geometry_test_15":
        guid,x,y=_developer_rectangle_fix_source_only(model)
        etree.SubElement(plan,Q+"MoveColumnPlacement",{
            "ifcGuid":guid,
            "newWorldOriginXM":str(x),
            "newWorldOriginYM":str(y),
        })
    elif tid=="topological_test_11":
        target=_named_slab(question,model)
        s=ifcopenshell.geom.settings()
        s.set(s.USE_WORLD_COORDS,True)
        shape_owner=ifcopenshell.geom.create_shape(s,target)
        # Native world geom vertices ALREADY in METRES, not IFC file mm.
        z=list(shape_owner.geometry.verts)[2::3]
        need(z and all(abs(v)<10000 for v in z),
             "Original upper Slab native world geometry missing")
        slab_bottom=round(min(z),6)
        cols=model.by_type("IfcColumn")
        need(len(cols)==2,"Original named slab touch involves two Columns")
        bases=[]
        for c in cols:
            owner=ifcopenshell.geom.create_shape(s,c)
            bases.append(min(list(owner.geometry.verts)[2::3]))
        need(max(bases)-min(bases)<TOL_M
             and slab_bottom-min(bases)>.2,
             "Original source columns not at common base below upper Slab")
        etree.SubElement(plan,Q+"SetAllMappedColumnDepth",{
            "newDepthM":str(round(slab_bottom-min(bases),6)),
        })
    elif tid=="topological_test_17":
        target=_named_slab(question,model)
        deleted=_developer_delete_set_from_original_storey(model,target.GlobalId)
        outer=etree.SubElement(plan,Q+"DeleteColumnsByGuid")
        for guid in deleted:
            etree.SubElement(outer,Q+"DeleteColumn",{"ifcGuid":guid})
    else:
        raise AssertionError("Only exact four original source tasks in v0.48 pilot")
    result=etree.tostring(root,encoding="utf8",xml_declaration=True)
    parse_original_native_edit_plan_v045(
        source,result,source_sha=file_hash(source))
    return result


def run_actual_paired_control(source:Path,task:dict,folder:Path,
                              *,control:str)->dict:
    """Native IFC emitted via both actual v0.47 model tools, never in-memory only."""
    need(control in ("positive","negative"),"Only frozen intended control types")
    tid=task["test_id"]
    sha=task["original_ifc_sha256"]
    x=MatchedOriginalXmlSession047(source,folder/"XML")
    p=RestrictedOriginalPythonSession047(source,folder/"Python")
    need(x.task_id==p.task_id==tid
         and x.original_xml==p.source_xml
         and x.call_budget==p.call_budget==25,
         "Original published source native evidence/budget differ between arms")
    xmlread=x.call("read_building_xml",{})
    pyread=p.call("read_source_python",{})
    need(xmlread["status"]==pyread["status"]=="ok"
         and xmlread["xml"].encode("utf8")==x.original_xml
         and pyread["original_source_xml_sha256"]==
             xmlread["current_xml_sha256"],
         "Model-facing two-arm original source question evidence not equal")
    if control=="positive":
        submitted=positive_developer_source_edit(
            x.original_xml,source,tid,task["public_question"])
    else:
        submitted=make_illustrative_plan(x.original_xml,tid,source)
    # The v0.47 helper intentionally rejects a square as a NON-SOLUTION.
    # Developer true-semantic POSITIVE control needs equivalent source-literal
    # typed Python argument serialization, without sharing any model answer.
    if tid=="geometry_test_14" and control=="positive":
        op=etree.fromstring(submitted)[-1][0]
        code=(f"set_slab_rectangle_dimensions(ifc_guid={op.get('ifcGuid')!r},"
              f"new_x_dim_m={float(op.get('newXDimM'))!r},"
              f"new_y_dim_m={float(op.get('newYDimM'))!r})")
    else:
        code=illustrative_python_from_original_xml(tid,submitted)
    check_parsed=parse_single_restricted_python_call(code,task_id=tid)
    need(bool(check_parsed),"Original source-bound Python edit not valid AST")
    translated=typed_python_to_exact_original_xml(source,sha,code)
    old_plan=parse_original_native_edit_plan_v045(
        source,submitted,source_sha=sha)
    py_plan=parse_original_native_edit_plan_v045(
        source,translated,source_sha=sha)
    need(old_plan==py_plan,
         "XML/Python original source-native controls not identical edit arguments")
    xx=x.call("submit_building_xml",{"xml_text":submitted.decode("utf8")})
    pp=p.call("submit_native_python",{"python_code":code})
    need(xx["status"]==pp["status"]=="ok"
         and xx["native_ifc_committed"] and pp["native_ifc_committed"]
         and xx["native_ifc_sha256"]==pp["native_ifc_sha256"]
         and x.output_ifc.is_file() and p.output_ifc.is_file()
         and file_hash(x.output_ifc)==file_hash(p.output_ifc),
         "Model-facing actual two native IFC candidates failed or differ in BYTES")
    physical_x=verify_original_native_mutation_v045(
        source,x.output_ifc,submitted_xml=submitted,source_sha=sha,task_id=tid)
    physical_p=verify_original_native_mutation_v045(
        source,p.output_ifc,submitted_xml=translated,source_sha=sha,task_id=tid)
    need(physical_x["status"]==physical_p["status"]==
         "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS",
         "Prior INDEPENDENT actual native writer source-preservation checker failed")
    semantic_x=evaluate_original_semantic048(
        source,x.output_ifc,original_sha=sha,
        task_id=tid,public_question=task["public_question"])
    semantic_p=evaluate_original_semantic048(
        source,p.output_ifc,original_sha=sha,
        task_id=tid,public_question=task["public_question"])
    expected=(control=="positive")
    need(semantic_x==semantic_p
         and semantic_x["candidatePassesIndependentResearchPhysicalPredicate"]
             is expected,
         "Independent original published semantic physical verdict wrong for control")
    need(x.calls==p.calls==2
         and x.base.submissions==p.submissions==1
         and x.original_xml==p.source_xml
         and file_hash(source)==sha,
         "Original two-arm tool calls or source state mismatch")
    return {
        "taskId":tid,
        "control":control,
        "originalPublicQuestionSHA256":task["public_question_sha256"],
        "originalIFCSourceSHA256":sha,
        "sourceEvidenceXMLSHA256":sha256(x.original_xml).hexdigest(),
        "XMLNativeSourceOutputSHA256":file_hash(x.output_ifc),
        "restrictedPythonNativeSourceOutputSHA256":file_hash(p.output_ifc),
        "sameActualSourceNativeCandidateIFCBytes":True,
        "bothOriginalSourceNativeEditOraclesPass":True,
        "nativeIfc4x3OriginalMM":True,
        "modelFacingReadCallsEachArm":1,
        "modelFacingEditCallsEachArm":1,
        "allowedModelToolCallsEachArm":25,
        "independentlyValidatedNativeSourcePhysicalPredicate":semantic_x,
        "researchSemanticPhysicalControlClassifiedCorrectly":True,
        "developerControlNotGivenToModelAsHiddenGT":True,
        "originalAuthorEvaluatorEquivalentOrCalled":False,
        "realPaidModelOrBenchmarkScore":False,
        "sourceOriginalUnchanged":True,
    }


def audit(author:Path,data:Path,*,progress=False)->dict:
    author=Path(author);data=Path(data)
    need(file_hash(ROOT/V047_REPORT)==V047_SHA
         and file_hash(ROOT/V046_REPORT)==V046_SHA,
         "Previous frozen original benchmark reports changed")
    originals=public_45(author,data)
    byid={x["test_id"]:x for x in originals}
    need(len(originals)==45
         and Counter(x["crud"] for x in originals)==
             {"create":15,"update":15,"delete":15}
         and len({x["original_ifc_sha256"] for x in originals})==31
         and len(PINS)==4
         and set(x[0] for x in PINS.values())==set(TASKS),
         "Exact original published 45/31/4 population changed")
    for sha,pin in PINS.items():
        row=byid[pin[0]]
        need(row["original_ifc_sha256"]==sha
             and row["public_question_sha256"]==pin[2]
             and sha256(row["public_question"].encode("utf8")).hexdigest()==pin[2],
             "Original published question/source SHA no longer matches frozen source")
    result=[]
    with TemporaryDirectory(prefix="bmb-v048-independent-original4-semantics-") as temp:
        for index,tid in enumerate(TASKS):
            task=byid[tid]
            source=data/"ifc"/task["original_source_ifc_relpath"]
            for control in ("negative","positive"):
                pair=run_actual_paired_control(
                    source,task,Path(temp)/str(index)/control,control=control)
                result.append(pair)
                if progress:
                    print("V048_INDEPENDENT_PUBLIC_SOURCE_SEMANTIC_CONTROL",
                          tid,control,pair[
                            "independentlyValidatedNativeSourcePhysicalPredicate"]["status"],
                          "NATIVE_BYTES_IDENTICAL",True,
                          "V045_SOURCE_PRESERVATION",True,flush=True)
    positives=[r for r in result if r["control"]=="positive"]
    negatives=[r for r in result if r["control"]=="negative"]
    need(len(result)==8 and len(positives)==len(negatives)==4
         and {r["taskId"] for r in positives}==set(TASKS)
         and {r["taskId"] for r in negatives}==set(TASKS)
         and all(r["researchSemanticPhysicalControlClassifiedCorrectly"]
                 and r["bothOriginalSourceNativeEditOraclesPass"]
                 and r["sameActualSourceNativeCandidateIFCBytes"] for r in result),
         "Incomplete original four semantic positive/negative native paired coverage")
    need(file_hash(ROOT/V047_REPORT)==V047_SHA
         and file_hash(ROOT/V046_REPORT)==V046_SHA,
         "Previous exact source/benchmark reports modified during v0.48 semantic audit")
    return {
        "status":"V048_FOUR_ORIGINAL_PUBLIC_TASKS_INDEPENDENT_PHYSICAL_SEMANTIC_CONTROLS_PASS",
        "issue":ISSUE,
        "stacked_on_exact_v047_frozen_commit":BASE_HEAD,
        "prior_v047_report_sha256":V047_SHA,
        "prior_v046_report_sha256":V046_SHA,
        "original_public_task_count":45,
        "original_public_CREATE":15,
        "original_public_UPDATE":15,
        "original_public_DELETE":15,
        "original_public_unique_native_IFC_source_count":31,
        "selected_original_four_tasks":list(TASKS),
        "other_original41_not_attempted_in_semantic_pilot":41,
        "positive_source_geometry_semantic_controls":4,
        "negative_source_geometry_semantic_controls":4,
        "real_native_IFC_XML_and_Python_pair_count":8,
        "real_independent_native_IFC_candidate_count":16,
        "real_two_arm_native_IFC_candidates_byte_equal_in_all_eight_controls":True,
        "real_actual_native_source_physical_preservation_oracle_pass_count":16,
        "real_v048_research_physical_semantic_positive_pass":4,
        "real_v048_research_physical_semantic_negative_rejected":4,
        "model_tool_read_count_each_arm":8,
        "model_tool_write_count_each_arm":8,
        "both_arms_exact_native_source_IFC_task_question_SHA_pins":True,
        "all_candidate_IFC_physical_geometry_original_IFC4X3_mm":True,
        "Ifcopenshell_create_shape_world_vertices_already_metres_not_native_mm":True,
        "original_named_slab_actual_geometry_not_arbitrary_IfcRelConnects":True,
        "geometric_contact_tolerance_metres":TOL_M,
        "original_author_hidden_ground_truth_access":False,
        "author_original_evaluator_equivalence_proven":False,
        "original_author_evaluator_invocations":0,
        "actual_real_LLM_model_trials":0,
        "paid_provider_calls":0,
        "Docker_executions":0,
        "original_author_benchmark_task_score_claimed":False,
        "developer_example_oracle_decision_is_NOT_author_public_benchmark_score":True,
        "all_original_published_question_and_IFC_data_unchanged":True,
        "research_main_and_Xim_unchanged":True,
        "next_priority":"v0.49 preregister frozen original4 model prompts/tokens/25-call budgets, semantic verifier blinded from model tools, assess author evaluator availability and distinct unrestricted Python arm before paid paired trials",
        "original_four_positive_and_negative_native_pairs":result,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author",type=Path,required=True)
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--progress",action="store_true")
    ap.add_argument("--write",type=Path)
    a=ap.parse_args()
    report=audit(a.author,a.data,progress=a.progress)
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
    if a.write:
        a.write.parent.mkdir(parents=True,exist_ok=True)
        with a.write.open("xb") as out:out.write(raw)
        print("V048_FROZEN_ORIGINAL4_SEMANTIC_POSITIVE_NEGATIVE_NATIVE_CONTROL_REPORT",
              a.write,sha256(raw).hexdigest(),flush=True)
    else:
        print(json.dumps({
            "status":report["status"],
            "positiveControls":report["real_v048_research_physical_semantic_positive_pass"],
            "negativeControls":report["real_v048_research_physical_semantic_negative_rejected"],
            "originalAuthorScores":0,"modelTrials":0,
        },sort_keys=True))


if __name__=="__main__":
    main()
