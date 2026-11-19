"""Original BIBIMBAP public topological_test_17 developer D0 audit, v0.10.

Only public natural-language question, original source IFC and source-native
meshes determine which original Columns' XML nodes are removed. Source
contact/compilation and independent IFC-only oracle run BEFORE unchanged
pinned original-author grading; no hidden target or score enters authoring.
No LLM, paid inference, historical score or normative BIXML/Xim change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v10_column_multi import (
    source_native_slab_contact_plan,compile_declarative_xml_v10,
)
from src.runtime.markup_normal_form import NS
from tools.oracle_bibimbap_v10_native_multi import (
    verify_v10_original_native_column_multi_delete,
)
from tools.bibimbap_matched25_cli import public_45,grade_author
from tools.bibimbap_matched25_tools import file_hash

TASK="topological_test_17"
REFERENCE_PUBLIC_ORIGINAL_SLAB="2IIWDJ6bzEPxU4iXeUX9Z5"
Q="{"+NS+"}"


def audit(author:Path,dataset:Path)->dict:
    tasks={row["test_id"]:row for row in public_45(author,dataset)}
    task=tasks[TASK]
    source_original=dataset/"ifc"/task["original_source_ifc_relpath"]
    input_sha=task["original_ifc_sha256"]
    if file_hash(source_original)!=input_sha:
        raise ValueError("Pinned original BIBIMBAP public IFC was changed")
    with tempfile.TemporaryDirectory(prefix="bibimbap134-original-public-D0-") as temp:
        folder=Path(temp)
        original=ifcopenshell.open(str(source_original))
        if (original.schema!="IFC4X3"
            or abs(float(ifcopenshell.util.unit.calculate_unit_scale(original))-.001)>1e-12):
            raise ValueError("Pinned original IFC4X3 source must remain native millimetres")
        normalized=folder/"source_original_ifc4x3_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(original,"METER").write(
            str(normalized))
        f=ifcopenshell.open(str(normalized))
        plan=source_native_slab_contact_plan(f,REFERENCE_PUBLIC_ORIGINAL_SLAB)
        projected=project_ifc_v9(normalized)
        root=etree.fromstring(projected.xml)
        nodes=root.findall("./"+Q+"Elements/"+Q+"Column")
        if len(nodes)!=10:
            raise ValueError("Source declarative view did not include all ten native Columns")
        actual_guids={x.get("ifcGuid") for x in nodes}
        expected_guids=set(plan["contacting_keep_guids"])|set(plan["noncontact_delete_guids"])
        if actual_guids!=expected_guids:
            raise ValueError("Original public IFC and declarative Column IDs differ")
        deleted_nodes=[]
        for col in nodes:
            if col.get("ifcGuid") in plan["noncontact_delete_guids"]:
                deleted_nodes.append((col.get("id"),col.get("ifcGuid")))
                root.find(Q+"Elements").remove(col)
        if len(deleted_nodes)!=5:
            raise ValueError("Original source-only contact must delete exactly five Column XML nodes")
        # Freeze candidate *before* consulting original author score. Nothing
        # from grader or its GT is used to choose these five source IDs.
        candidate=folder/"candidate_native_ifc4x3_m.ifc"
        compilation=compile_declarative_xml_v10(
            normalized,
            etree.tostring(root,encoding="utf8"),
            candidate,
            reference_slab_guid=REFERENCE_PUBLIC_ORIGINAL_SLAB,
        )
        if {m.ifc_guid for m in compilation.operations}!=set(plan["noncontact_delete_guids"]):
            raise ValueError("Trusted compiler altered developer frozen original public deletion set")
        independent=verify_v10_original_native_column_multi_delete(
            normalized,candidate,reference_slab_guid=REFERENCE_PUBLIC_ORIGINAL_SLAB)
        original_units=folder/"candidate_original_mm.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(candidate)),"MILLIMETER").write(str(original_units))
        if ifcopenshell.open(str(original_units)).schema!="IFC4X3":
            raise ValueError("Native schema changed on author evaluation conversion")
        # Original author grader only consulted after independent source-only
        # source/native geometry/candidate output and oracle are fixed.
        scored=grade_author(author,source_original,original_units,TASK)
        if file_hash(source_original)!=input_sha:
            raise ValueError("Original native BIBIMBAP source IFC changed during D0 scoring")
        return {
            "status":"ORIGINAL_SOURCE_IFC4X3_V010_MULTICOLUMN_DEVELOPER_D0_NOT_LLM",
            "issue":"https://github.com/pikaybh/bim-markup-bench/issues/134",
            "original_author_source_revision":"667004e16bd38fd7d538bcee56191465429fd975",
            "original_public_dataset_revision":"f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca",
            "original_public_task_id":TASK,
            "original_public_question_sha256":task["public_question_sha256"],
            "original_public_ifc_sha256":input_sha,
            "original_native_schema":"IFC4X3",
            "normalized_original_ifc_sha256":file_hash(normalized),
            "developer_source_only_public_named_reference_slab":REFERENCE_PUBLIC_ORIGINAL_SLAB,
            "developer_original_native_contact_plan":{
                "original_slab_top_world_z_m":plan["named_public_slab_world_top_m"][2],
                "original_contacting_support_columns":plan["contacting_keep_guids"],
                "original_noncontact_delete_columns":plan["noncontact_delete_guids"],
                "full_original_native_source_column_geometry":plan["source_column_geometry"],
                "original_source_relation_interpretation":plan["source_relation_policy"],
                "original_named_Slab_unchanged":True,
            },
            "direct_mark_up_developer_deleted_original_XML_node_IDs":sorted(
                deleted_nodes,key=lambda item:item[0]
            ),
            "direct_markup_model_generated_output":False,
            "native_trusted_compiler_operation_count":len(compilation.operations),
            "native_trusted_compiler_original_source_hash":compilation.source_sha256,
            "native_candidate_sha256":file_hash(candidate),
            "independent_original_native_IFC_oracle":independent,
            "original_author_D0_score_after_candidate_frozen":scored,
            "original_mm_candidate_sha256":file_hash(original_units),
            "new_model_provider_calls":0,
            "additional_paid_inference_usd":"0",
            "original_real_GPT6_Luna_45_scores_unchanged":True,
            "backend_all45_python_IFC_full_parity":False,
            "original_author_grader_edited":False,
            "original_dataset_bytes_edited":False,
        }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo",type=Path,required=True)
    parser.add_argument("--dataset",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    args=parser.parse_args()
    if args.output_json.exists() or args.output_json.is_symlink():
        parser.error("Do not overwrite prior scored D0 research evidence")
    result=audit(args.author_repo.resolve(strict=True),
                 args.dataset.resolve(strict=True))
    # Serialize BEFORE creating exclusive evidence destination. An input
    # type error must not leave an empty, misleading audit report behind.
    payload=(json.dumps(result,sort_keys=True,indent=2,
                        ensure_ascii=False)+"\n").encode("utf8")
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    with args.output_json.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({
        "status":result["status"],
        "original_author_grade":result["original_author_D0_score_after_candidate_frozen"],
        "original_native_columns_kept":len(
            result["developer_original_native_contact_plan"]["original_contacting_support_columns"]),
        "original_native_columns_deleted":len(
            result["developer_original_native_contact_plan"]["original_noncontact_delete_columns"]),
        "new_provider_calls":0,
        "report_sha256":file_hash(args.output_json),
    },sort_keys=True))


if __name__=="__main__":
    main()
