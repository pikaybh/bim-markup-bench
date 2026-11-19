"""v0.66 offline two-source, two-operation declarative XML / real Docker I audit.

No task-specific expected answer or grader imported. Two previously known
developer-exposed IFC4X3 source families are used purely as developer controls.
Source-neutral physical final-state full/managed XML and independent genuine
pinned local Linux Docker Python both produce source SHA-verified native IFCs.

Offline - no model provider, no original IFC uploads, no paper score.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import ifcopenshell
from lxml import etree

from tools import audit_bibimbap_v065_offline_generalization as base
from tools.bibimbap_matched25_tools import DockerIFCExecutor, file_hash
from tools.bibimbap_v052_live_original_native_python_session import (
    live_pinned_local_runtime_admission_v052,
)
from tools.bibimbap_v055_production_schema_gate import _schema_error_counter
from tools.bibimbap_v066_window_final_state import (
    _mesh_bounds,source,groups,full_source_state,managed_source_state,parse_full_state,
    expand_managed_state,compile_final_state,FinalWindow066Error,
)
from tools.bibimbap_v066_window_native_scope import (
    post_window_native_scope,WindowScope066Error,STATUS
)
from tools.audit_bibimbap_v066_step_identity_fairness import relabel_spf

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"bibimbap_v066_window_move_delete_native_20261118.json"
PARENT=ROOT/"reports"/"bibimbap_v066_native_semantic_scope_20261118.json"
PARENT_SHA="f908cc10086f0fb00efee0d8651385d378ef50221b7d6eab00ad42df7441d49b"
# These only live in the developer control AUDIT harness. The tool, XML
# grammar, compiler and independent native admission contain NO task IDs.
EXPOSED_SOURCE_CONTROLS=("geometry_test_13","geometry_test_19")
KINDS=("move","delete")


def need(condition, message):
    if not condition:raise AssertionError(message)


def canonical(report):
    return (json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")


def _developer_control(group):
    """Source-native host Wall-major direction, NOT answer-derived position."""
    source_wall_box=_mesh_bounds(group["host"])
    axis = 0 if (source_wall_box[0][1]-source_wall_box[0][0] >=
                 source_wall_box[1][1]-source_wall_box[1][0]) else 1
    return (.2,0.,0.) if axis == 0 else (0.,.2,0.)


def _submitted_state(source_xml, assembly, *, kind, offset):
    doc=etree.fromstring(source_xml)
    target={p.GlobalId for p in assembly["members"]}
    if doc.tag.endswith("ManagedFinalState"):
        items=list(doc)
    else:
        items=list(doc[1])
    for e in items:
        if e.get("ifcGuid") in target:
            if kind=="delete":
                e.set("present","false")
            else:
                for key,delta in zip(
                    ("finalWorldMinXM","finalWorldMinYM","finalWorldMinZM"),offset):
                    e.set(key,f"{float(e.get(key))+delta:.6f}")
    return etree.tostring(doc,encoding="utf8",xml_declaration=True)


def _imperative_code(kind, group_index, offset):
    """Standalone actual native Python, no D compiler or research module use.

    Selects the same source-window ordinal exposed by the local developer
    control; no task name, solution GUID, question or grader in code.
    """
    prelude=(
        "import ifcopenshell\n"
        "import ifcopenshell.api\n"
        "import ifcopenshell.geom\n"
        "import ifcopenshell.util.placement\n"
        "import ifcopenshell.util.unit\n"
        "import numpy as np\n"
        "settings=ifcopenshell.geom.settings()\n"
        "settings.set(settings.USE_WORLD_COORDS,True)\n"
        "windows=sorted(ifc.by_type('IfcWindow'),key=lambda w:w.GlobalId)\n"
        f"window=windows[{group_index}]\n"
        "opening=window.FillsVoids[0].RelatingOpeningElement\n"
        "def center_x(product):\n"
        "    shape=ifcopenshell.geom.create_shape(settings,product)\n"
        "    verts=list(shape.geometry.verts)\n"
        "    return (min(verts[0::3])+max(verts[0::3]))/2\n"
        "center=center_x(window)\n"
        "details=sorted((p for p in ifc.by_type('IfcBuildingElementProxy')"
        " if abs(center_x(p)-center)<.015),key=lambda p:p.GlobalId)\n"
    )
    if kind=="delete":
        return (prelude+
            "for part in [*details,window,opening]:\n"
            "    ifcopenshell.api.run('root.remove_product',ifc,product=part)\n"
            "result={'native_removed_window_assembly':True}\n"
            "commit()\n")
    return (prelude+
        "scale=ifcopenshell.util.unit.calculate_unit_scale(ifc)\n"
        f"delta=np.array({list(offset)!r},dtype=float)/scale\n"
        "for part in [opening,*details]:\n"
        "    pl=part.ObjectPlacement\n"
        "    parent=pl.PlacementRelTo\n"
        "    matrix=(ifcopenshell.util.placement.get_local_placement(parent)"
        " if parent else np.eye(4))\n"
        "    old=np.array(pl.RelativePlacement.Location.Coordinates,dtype=float)\n"
        "    native=np.linalg.solve(matrix[:3,:3],delta)\n"
        "    pl.RelativePlacement.Location.Coordinates=tuple(float(x)"
        " for x in old+native)\n"
        "result={'native_moved_window_assembly':True}\n"
        "commit()\n")


def _negative(source_file,sha,reference_path,temp,kind,group):
    found={}
    def reject(label, mutation):
        target=temp/(kind+"_illegal_"+label+".ifc")
        model=ifcopenshell.open(str(reference_path))
        mutation(model)
        model.write(str(target))
        try:
            post_window_native_scope(source_file,sha,target)
        except WindowScope066Error as exc:
            found[label]=str(exc)
            return
        raise AssertionError(f"Native illegality unexpectedly admitted: {label}")

    def unrelated_original_wall_name(model):
        wall=sorted(model.by_type("IfcWall"),key=lambda w:w.GlobalId)[0]
        wall.Name="UNAUTHORIZED_EXISTING_SOURCE_WALL_ATTRIBUTE"
    reject("alter_unrelated_existing_Wall_metadata", unrelated_original_wall_name)

    if kind=="delete":
        def delete_second_group(model):
            windows=sorted(model.by_type("IfcWindow"),key=lambda w:w.GlobalId)
            other=windows[0]
            opening=other.FillsVoids[0].RelatingOpeningElement
            if other.GlobalId==group["window"].GlobalId:
                other=windows[1]
                opening=other.FillsVoids[0].RelatingOpeningElement
            ifcopenshell.api.root.remove_product(model,product=other)
            ifcopenshell.api.root.remove_product(model,product=opening)
        reject("delete_second_unapproved_Window",delete_second_group)
    elif len(group["details"]):
        def unsynced_proxy(model):
            original_proxy=group["details"][0]
            proxy=model.by_guid(original_proxy.GlobalId)
            point=proxy.ObjectPlacement.RelativePlacement.Location
            coords=list(point.Coordinates)
            coords[0] += 100.
            point.Coordinates=tuple(coords)
        reject("unsynced_hosted_detail_proxy", unsynced_proxy)
    else:
        def add_anonymous_orphan(model):
            model.create_entity("IfcCartesianPoint",Coordinates=(12345.,54321.,0.))
        reject("add_unauthorized_orphan_native_entity",add_anonymous_orphan)
    return found


def run_one_case(task, row, tmp):
    src=base.DATA/"ifc"/row["original_source_ifc_relpath"]
    sha=row["original_ifc_sha256"]
    model=source(src,sha)
    native_groups=groups(model)
    chosen=sorted(native_groups)[0]
    g=native_groups[chosen]
    index=sorted(native_groups).index(chosen)
    offset=_developer_control(g)
    raw_full=full_source_state(src,sha)
    raw_managed=managed_source_state(src,sha)
    variants=[]
    for kind in KINDS:
        complete=_submitted_state(raw_full,g,kind=kind,offset=offset)
        managed=_submitted_state(raw_managed,g,kind=kind,offset=offset)
        accepted_full=parse_full_state(src,sha,complete)
        expanded,accepted_managed=expand_managed_state(src,sha,managed)
        need(accepted_full==accepted_managed
             and expanded==complete
             and accepted_full["kind"]==kind
             and accepted_full["window_guid"]==chosen,
             "Complete final-state D FULL/MANAGED equivalent plans lost")
        work=tmp/(task+"_"+kind)
        work.mkdir()
        full_IFC=work/"D_FULL.ifc"
        managed_IFC=work/"D_MANAGED.ifc"
        compile_final_state(src,sha,complete,full_IFC)
        compile_final_state(src,sha,managed,managed_IFC,managed=True)
        d_full=post_window_native_scope(src,sha,full_IFC)
        d_managed=post_window_native_scope(src,sha,managed_IFC)
        # Prove numeric STEP serialization labels are irrelevant using
        # a genuinely reopened bijective relabeling of every declaration
        # and reference, while all other STEP bytes stay unchanged.
        remapped, entity_map = relabel_spf(full_IFC.read_bytes())
        step_remapped_IFC=work/"D_FULL_STEP_RELABEL.ifc"
        step_remapped_IFC.write_bytes(remapped)
        step_verdict=post_window_native_scope(src,sha,step_remapped_IFC)
        need(len(entity_map)>0
             and step_verdict["semantic_edit_digest"]
                 ==d_full["semantic_edit_digest"],
             "Legal bijective STEP-ID remap rejected by independent native oracle")

        sandbox=work/"ISOLATED_PINNED_DOCKER"
        sandbox.mkdir()
        i_file=sandbox/"current.ifc"
        shutil.copyfile(src,i_file)
        code=_imperative_code(kind,index,offset)
        need("commit()" in code
             and "final_state" not in code
             and "author" not in code.lower()
             and "target_guid" not in code.lower()
             and "data.tests" not in code.lower()
             and "geometry_test" not in code
             and "topological_test" not in code,
             "Imperative developer control leaks D compiler/grader/answers")
        run=DockerIFCExecutor().run(sandbox,code)
        need(run.get("status")=="ok"
             and run.get("committed") is True
             and run.get("backend")=="linux_docker_sandbox",
             "Genuine pinned Linux Docker imperative native run failed")
        imperative=post_window_native_scope(src,sha,i_file)
        all_digests={v["semantic_edit_digest"]
                     for v in (d_full,d_managed,imperative,step_verdict)}
        need(len(all_digests)==1
             and all(v["status"]==STATUS and v["kind"]==kind
                     for v in (d_full,d_managed,imperative,step_verdict)),
             "Native actual D FULL/MANAGED/I physical edit scope mismatch")
        negative=_negative(src,sha,full_IFC,work,kind,g)
        need(len(negative)==2,"Both native negative controls required")
        need(file_hash(src)==sha,"Original immutable IFC source modified")
        variants.append({
            "operation_family":kind,
            "source_native_assembly_roster_count":len(native_groups),
            "source_native_original_member_group_count":len(g["members"]),
            "source_world_control_offset_m":list(offset) if kind=="move" else None,
            "D_FULL_source_xml_bytes":len(raw_full),
            "D_MANAGED_source_xml_bytes":len(raw_managed),
            "D_FULL_final_state_xml_bytes":len(complete),
            "D_MANAGED_final_state_xml_bytes":len(managed),
            "D_FULL_real_IFC_accepted":True,
            "D_MANAGED_real_IFC_accepted":True,
            "D_FULL_native_bijective_STEP_ID_relabel_real_IFC_accepted":True,
            "actual_bijectively_remapped_native_STEP_entities":len(entity_map),
            "independent_pinned_Linux_Docker_Python_I_real_IFC_accepted":True,
            "all_three_same_native_physical_semantic_digest":next(iter(all_digests)),
            "native_illegal_mutations_rejected":negative,
            "source_original_IFC_unchanged":True,
            "model_generated_attempt_count":0,
        })
    return {
        "already_developer_exposed_source_task_for_audit_only":task,
        "source_SHA256":sha,
        "source_schema":model.schema,
        "source_IFC_original_root_count":len(model.by_type("IfcRoot")),
        "native_groups":len(native_groups),
        "source_original_GUIDs_redacted":True,
        "cases":variants,
    }


def build_report():
    need(file_hash(PARENT)==PARENT_SHA,
         "Frozen v0.66 prior native semantic gate evidence changed")
    rows={r["test_id"]:r for r in base.public_45(base.AUTHOR,base.DATA)}
    pre=live_pinned_local_runtime_admission_v052()
    need(pre["status"]=="RUNTIME_ADMITTED",
         "Local genuinely pinned Linux Docker worker not admitted")
    with TemporaryDirectory(prefix="v066-window-2-native-sources-") as t:
        tmp=Path(t)
        cases=[run_one_case(task,rows[task],tmp)
               for task in EXPOSED_SOURCE_CONTROLS]
    need(len(cases)==2 and all(len(x["cases"])==2 for x in cases),
         "Both previously developer-inspected source IFCs must pass both operations")
    return {
        "status":"V066_TWO_SOURCE_NEUTRAL_WINDOW_MOVE_DELETE_NATIVE_D_FULL_MANAGED_DOCKER_I_PASS",
        "issue":247,
        "source_exposure":"ONLY_TWO_PREVIOUSLY_DEVELOPER_EXPOSED_AND_SHA_PINNED_IFC4X3",
        "prior_window_source_task_ids_used_only_in_audit_not_in_compiler":
            list(EXPOSED_SOURCE_CONTROLS),
        "frozen_v066_parent_report_SHA256":PARENT_SHA,
        "supported_schema":"IFC4X3",
        "unsupported_schema_or_complexity":[
            "IFC2X3 hosted Window move/delete not demonstrated",
            "IFC4/curved/shared/orphan proxy/multiple simultaneous changes unsupported",
            "Alternative lawful IFC representation rewrite may still be rejected by narrow native replay oracle",
            "This is physical/source-scope admissibility, not original author task correctness",
        ],
        "actual_native_original_source_count":2,
        "operation_source_pairs_executed":4,
        "real_native_XML_D_FULL_outputs":4,
        "real_native_XML_D_MANAGED_outputs":4,
        "actual_pinned_Linux_Docker_Python_I_outputs":4,
        "actual_native_bijective_STEP_ID_relabel_valid_ifc_outputs":4,
        "legal_native_edit_output_accepts":16,
        "illegal_native_mutation_rejects":8,
        "D_document_has_no_move_delete_command_elements":True,
        "source_net_ISOLATION_and_preregistered_external_transfer_rights": "BLOCKED",
        "independently_certified_blind_original_IFC_sources":0,
        "model_provider_calls":0,
        "original_IFC_uploads":0,
        "original_author_or_private_grader_accesses":0,
        "all_original_source_SHA_checks_unchanged":True,
        "cases":cases,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write",action="store_true")
    group.add_argument("--check",action="store_true")
    a=parser.parse_args()
    data=canonical(build_report())
    if a.write:
        with REPORT.open("xb") as out:out.write(data)
    else:
        need(REPORT.read_bytes()==data,
             "Frozen window move/delete native report changed")
    print("V066_NATIVE_WINDOW_MOVE_DELETE_"+("WRITE" if a.write else "CHECK")+
          "=PASS native_D_I=12 STEP_relabels=4 negative_real_IFC=8 model_calls=0")


if __name__=="__main__":
    main()
