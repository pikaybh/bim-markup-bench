"""Issue #247: synthetic IFC4 Window group MOVE/DELETE D_FULL/MANAGED/I native.

Developer-owned four IFC4 (m/mm × X/Y) source geometries, two hosted Windows
each. No GNI/public author IFC, hidden GT, model calls or provider data. D
model-facing grammar expresses final state with stable IDs, NOT operations.
Trusted compiler derives edit from final-state diff. Independent Python
actually executes under pinned local Linux Docker. Independent IFC native
scope compares complete STEP-number-independent graph/geometry and relation
integrity. This audit is engineering-only, not benchmark accuracy evidence.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.geom
from lxml import etree

from tools import bibimbap_v066_ifc4_window_synthetic_host as synth
from tools import bibimbap_v066_ifc4_window_final_state as window
from tools import bibimbap_v066_ifc4_window_native_scope as scope
from tools.audit_bibimbap_v066_step_identity_fairness import relabel_spf
from tools import audit_bibimbap_v066_synthetic_ifc4_DI as door_audit
from tools.bibimbap_matched25_tools import (
    DockerIFCExecutor, file_hash, PINNED_DOCKER_IMAGE,
)
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v057_provenance import (
    refuse_all_model_trials_v057,ProviderTrialBlocked057,
)

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_synthetic_ifc4_window_DI_20261119.json"
PARENT_SHA="40149f8f4f86f8e86421926d71d11ccdfb9bb0d99b573c943127395dcebcb378"
CASES=(("metre","X"),("metre","Y"),("millimetre","X"),("millimetre","Y"))
OPERATIONS=("move","delete")
INVALID_XML=(
    "source_SHA_tampered","one_managed_element_missing",
    "forged_XML_move_command","partial_window_group_change",
)
INVALID_NATIVE=("original_wall_metadata_mutated",
                "orphan_anonymous_cartesian_point",
                "extra_unapproved_native_operation")


def need(condition,why):
    if not condition:raise AssertionError(why)


def canonical(payload):
    return (json.dumps(payload,ensure_ascii=False,sort_keys=True,
                       indent=2,allow_nan=False)+"\n").encode("utf8")


def offset_world(axis):
    return (.25,0.,0.) if axis=="X" else (0.,.25,0.)


def submitted_final_state(initial,assembly,kind,offset,*,managed):
    root=etree.fromstring(initial)
    roster=root if managed else root[1]
    selected={p.GlobalId for p in assembly["members"]}
    count=0
    for item in roster:
        if item.get("ifcGuid") in selected:
            count+=1
            if kind=="delete":
                item.set("present","false")
            else:
                for key,d in zip(("finalWorldMinXM","finalWorldMinYM",
                                  "finalWorldMinZM"),offset):
                    item.set(key,f"{float(item.get(key))+d:.6f}")
    need(count==len(selected),"Not entire source original Window group addressed")
    return etree.tostring(root,encoding="utf8",xml_declaration=True)


def genuine_independent_I_code(kind,index,offset):
    """Independent ordinary Python, no trusted D compiler or source scorer."""
    need(kind in OPERATIONS and index in (0,1),
         "Only source-independent developer test cases")
    prelude=(
        "import ifcopenshell\n"
        "import ifcopenshell.api.root\n"
        "import ifcopenshell.util.unit\n"
        "import ifcopenshell.util.placement\n"
        "import numpy as np\n"
        "windows=sorted(ifc.by_type('IfcWindow'),key=lambda w:w.GlobalId)\n"
        f"window=windows[{index}]\n"
        "opening=window.FillsVoids[0].RelatingOpeningElement\n"
    )
    if kind=="delete":
        return (prelude+
                "for part in (window,opening):\n"
                "    ifcopenshell.api.root.remove_product(ifc,product=part)\n"
                "result={'removed_hosted_window':True}\n"
                "commit()\n")
    return (prelude+
            "scale=ifcopenshell.util.unit.calculate_unit_scale(ifc)\n"
            f"delta=np.array({list(offset)!r},dtype=float)/scale\n"
            "placement=opening.ObjectPlacement\n"
            "parent=placement.PlacementRelTo\n"
            "parent_world=(ifcopenshell.util.placement.get_local_placement(parent)\n"
            " if parent else np.eye(4))\n"
            "native=np.linalg.solve(parent_world[:3,:3],delta)\n"
            "point=placement.RelativePlacement.Location\n"
            "before=np.array(point.Coordinates,dtype=float)\n"
            "point.Coordinates=tuple(float(x) for x in before+native)\n"
            "result={'moved_hosted_window':True}\n"
            "commit()\n")


def invalid_xml(full,assembly,kind,offset,name):
    doc=etree.fromstring(full)
    selected={p.GlobalId for p in assembly["members"]}
    if name=="source_SHA_tampered":
        doc.set("originalIFCSha256","f"*64)
    elif name=="one_managed_element_missing":
        roster=doc[1]
        member=next(x for x in roster if x.get("ifcGuid") in selected)
        roster.remove(member)
    elif name=="forged_XML_move_command":
        etree.SubElement(doc[1],window.Q+"Move",{"target":"untrusted"})
    elif name=="partial_window_group_change":
        member=next(x for x in doc[1] if x.get("ifcGuid") in selected)
        if kind=="delete":
            member.set("present","true")
        else:
            member.set("finalWorldMinXM",
                       f"{float(member.get('finalWorldMinXM'))+.1:.6f}")
    else:raise AssertionError("Unknown invalid XML trial")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True)


def mutate_candidate(valid:Path,bad:Path,kind,reference_source,other_window):
    model=ifcopenshell.open(str(valid))
    if kind=="original_wall_metadata_mutated":
        model.by_type("IfcWall")[0].Name="UNAUTHORIZED_ORIGINAL_WALL"
    elif kind=="orphan_anonymous_cartesian_point":
        model.create_entity("IfcCartesianPoint",
                            Coordinates=(123456.,654321.,100000.))
    elif kind=="extra_unapproved_native_operation":
        # Move/add/alter an unselected survivor even if an allowed window
        # was moved or deleted in the primary operation.
        partner=model.by_guid(other_window)
        if partner is None:
            raise AssertionError("Expected unselected Window preserved")
        point=partner.ObjectPlacement.RelativePlacement.Location
        coords=list(point.Coordinates)
        coords[0]+=99.
        point.Coordinates=tuple(coords)
    else:raise AssertionError("Unknown native bad IFC")
    model.write(str(bad))


def case(source_root:Path,unit:str,axis:str):
    folder=source_root/(unit+"_"+axis)
    folder.mkdir()
    original=synth.write_fresh(folder/"source.ifc",unit=unit,axis=axis)
    sha=file_hash(original)
    model=window.source(original,sha)
    groups=window.groups(model)
    need(len(groups)==2 and all(len(g["members"])==2 for g in groups.values()),
         "Expected 2 separate hosted IFC4 Window/Opening assemblies")
    selected_guid=sorted(groups)[0]
    selected=groups[selected_guid]
    other=sorted(groups)[1]
    index=0
    shift=offset_world(axis)
    initial_full=window.full_source_state(original,sha)
    initial_managed=window.managed_source_state(original,sha)
    operations=[]
    for kind in OPERATIONS:
        work=folder/kind
        work.mkdir()
        final_full=submitted_final_state(initial_full,selected,kind,shift,managed=False)
        final_managed=submitted_final_state(initial_managed,selected,kind,shift,managed=True)
        actual_full=window.parse_full_state(original,sha,final_full)
        expanded,actual_managed=window.expand_managed_state(
            original,sha,final_managed)
        need(actual_full==actual_managed
             and expanded==final_full
             and actual_full["kind"]==kind
             and actual_full["window_guid"]==selected_guid,
             "IFC4 full and managed physical final states do not semantically match")
        native={}
        for name,raw,managed in (
            ("D_FULL",final_full,False),
            ("D_MANAGED",final_managed,True),
        ):
            out=work/(name+".ifc")
            window.compile_final_state(original,sha,raw,out,managed=managed)
            native[name]=(out,scope.post_window_native_scope(original,sha,out))
        reindexed,remap=relabel_spf(native["D_FULL"][0].read_bytes())
        relabeled=work/"D_FULL_STEP_RELABELED.ifc"
        relabeled.write_bytes(reindexed)
        check_reindexed=scope.post_window_native_scope(original,sha,relabeled)
        need(len(remap)>0 and check_reindexed["kind"]==kind,
             "IFC4 Window STEP-ID relabel native reject")
        script=genuine_independent_I_code(kind,index,shift)
        need("commit()" in script and "final_state" not in script
             and "data.tests" not in script and "target_guid" not in script
             and "geometry_test" not in script and "topological_test" not in script,
             "I_NATIVE programmer tool is using answer-bearing source")
        sandbox=work/"PINNED_LINUX_DOCKER"
        sandbox.mkdir()
        shutil.copyfile(original,sandbox/"current.ifc")
        result=DockerIFCExecutor().run(sandbox,script)
        need(result.get("status")=="ok"
             and result.get("backend")=="linux_docker_sandbox"
             and result.get("committed") is True,
             "Real independent IFC4 Python in pinned Docker did not commit")
        i_result=scope.post_window_native_scope(
            original,sha,sandbox/"current.ifc")
        digests={v["semantic_edit_digest"] for v in (
            native["D_FULL"][1],native["D_MANAGED"][1],
            check_reindexed,i_result)}
        need(len(digests)==1 and all(v["kind"]==kind for v in (
            native["D_FULL"][1],native["D_MANAGED"][1],
            check_reindexed,i_result)),
            "IFC4 source-neutral D_FULL/MANAGED/I native physical outcomes disagree")
        bad_xml={}
        for name in INVALID_XML:
            try:window.parse_full_state(
                original,sha,invalid_xml(final_full,selected,kind,shift,name))
            except window.FinalWindow066Error:
                bad_xml[name]=True
            else:raise AssertionError("Invalid IFC4 final XML unexpectedly accepted: "+name)
        bad_native={}
        for name in INVALID_NATIVE:
            wrong=work/(name+".ifc")
            mutate_candidate(native["D_FULL"][0],wrong,name,original,other)
            try:scope.post_window_native_scope(original,sha,wrong)
            except scope.WindowScope066Error:
                bad_native[name]=True
            else:raise AssertionError("Illegally altered native IFC4 accepted: "+name)
        need(all(bad_xml.values()) and all(bad_native.values())
             and len(bad_xml)==4 and len(bad_native)==3,
             "Native/markup negative fixtures incomplete")
        need(file_hash(original)==sha,
             "IFC4 synthetic source mutated during native engineering")
        operations.append({
            "operation_family":kind,
            "original_source_2_window_groups":len(groups),
            "original_selected_group_members":len(selected["members"]),
            "source_only_world_offset_metres":list(shift) if kind=="move" else None,
            "D_FULL_initial_xml_utf8_bytes":len(initial_full),
            "D_MANAGED_initial_xml_utf8_bytes":len(initial_managed),
            "D_FULL_complete_final_xml_utf8_bytes":len(final_full),
            "D_MANAGED_complete_final_xml_utf8_bytes":len(final_managed),
            "independent_I_source_python_UTF8_bytes":len(script.encode("utf8")),
            "real_native_D_full_managed_I_semantically_equal":True,
            "same_physical_native_edit_digest":next(iter(digests)),
            "actual_native_STEP_reencoded_variant":True,
            "bad_xml_controls_all_rejected":bad_xml,
            "bad_native_mutations_all_rejected":bad_native,
            "original_IFC_unchanged":True,
            "real_linux_pinned_Docker_I_committed":True,
            "model_generated_trials":0,
        })
    return {
        "synthetic_unit":unit,"synthetic_wall_axis":axis,
        "source_original_schema":"IFC4",
        "source_original_ifc_sha256":sha,
        "source_original_ifc_bytes":original.stat().st_size,
        "source_initial_unmodified_windows":2,
        "source_original_unrelated_slabs":len(model.by_type("IfcSlab")),
        "native_real_operations":operations,
        "independently_blind_evaluation":False,
    }


def build_report():
    need(file_hash(door_audit.REPORT)==PARENT_SHA,
         "Frozen prior synthetic IFC4 Door and GNI rights evidence changed")
    pre=live_pinned_local_runtime_admission_v052()
    need(pre["status"]=="RUNTIME_ADMITTED",
         "Real pinned Linux Docker must be available, no simulated I allowed")
    try:refuse_all_model_trials_v057({"owner_approval":True,"paid":True})
    except ProviderTrialBlocked057:pass
    else:raise AssertionError("Original provider trial gate bypassed")
    with TemporaryDirectory(prefix="v066-synthetic-IFC4-window-") as t:
        rows=[case(Path(t),u,a) for u,a in CASES]
    need(len(rows)==4 and all(len(r["native_real_operations"])==2
                              for r in rows),
         "Four IFC4 sources x move/delete must complete")
    return {
        "status":"V066_IFC4_SYNTHETIC_WINDOW_MOVE_DELETE_REAL_D_I_SCOPE_PASS_NONBLIND",
        "issue":247,
        "frozen_synthetic_ifc4_door_parent_SHA256":PARENT_SHA,
        "source_generator_SHA256":file_hash(Path(synth.__file__)),
        "source_neutral_final_xml_compiler_SHA256":file_hash(Path(window.__file__)),
        "independent_native_step_neutral_gate_SHA256":file_hash(Path(scope.__file__)),
        "pinned_local_Docker_image":PINNED_DOCKER_IMAGE,
        "self_authored_IFC4_source_count":4,
        "source_units":["metre","millimetre"],
        "wall_axes":["X","Y"],
        "source_operation_pairs_executed":8,
        "actual_native_D_FULL_outputs":8,
        "actual_native_D_MANAGED_outputs":8,
        "actual_native_pinned_Linux_Docker_I_outputs":8,
        "step_relabel_physically_admissible_outputs":8,
        "bad_final_XML_controls_rejected":32,
        "bad_native_IFC_mutations_rejected":24,
        "model_generated_attempts":0,
        "original_BIBIMBAP_or_GNI_ifc_inputs_read":0,
        "original_author_hidden_grader_or_GT_read":0,
        "external_original_ifc_uploads":0,
        "independently_untouched_sample_count":0,
        "per_IFC_rights_or_transfer_approved":False,
        "owner_provider_or_scorer_trial_authorized":False,
        "not_universal_IFC4_support":True,
        "known_uncovered":["IFC2X3 Window move/delete",
            "IFC4 hosted detailed proxies, joined/curved/shared placements",
            "multi-edit operation combinations and arbitrary representations",
            "independent blind source acquisition/rights/actual GNI IFCs"],
        "case_results":rows,
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
        need(REPORT.read_bytes()==raw,"IFC4 window audit not byte-for-byte reproducible")
    print("V066_SYNTHETIC_IFC4_WINDOW_"+("WRITE" if opts.write else "CHECK")+
          "=PASS cases=4 op_pairs=8 D_I_native_outputs=24 STEP_relabels=8 "
          "bad_XML=32 bad_IFC=24 model_calls=0")


if __name__=="__main__":
    main()
