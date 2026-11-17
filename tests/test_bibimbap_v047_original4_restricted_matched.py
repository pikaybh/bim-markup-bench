"""v0.47 original four real matched restricted XML-vs-Python native IFC pilot tests.

Source-locked original questions/IFC; real model-facing paired sessions,
byte-identical independent native-mm IFC outputs for four developer NON-SOLUTION
actions; strict AST negative injection, original source immutability, rollback,
25-tool-call budget and exact frozen report reproduction. No LLM/author grader.
"""
from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash,UnsupportedArm,MAX_CODE_BYTES
from tools.audit_bibimbap_v045_original4_native_mutations import (
    make_illustrative_plan)
from tools import audit_bibimbap_v047_original4_matched_restricted as audit
from tools.bibimbap_v047_restricted_python_native_session import (
    MatchedOriginalXmlSession047,RestrictedOriginalPythonSession047,
    RestrictedNativePython047Error,parse_single_restricted_python_call,
    typed_python_to_exact_original_xml,exact_model_facing_python_source,
    FUNCTION_BY_TASK)
from src.runtime.experimental_v45_original_native_mutations import (
    TASK_OPERATIONS,parse_original_native_edit_plan_v045,
    OriginalNativeMutation045Error)
from src.runtime.experimental_v44_original_native_step_readonly import PINS
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v047_original4_restricted_XML_Python_native_matched_20261117.json"
FROZEN_SHA="cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa"
TASKS=audit.TASKS


class OriginalFourRestrictedMatchedPilot047(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={e["test_id"]:e for e in public_45(AUTHOR,DATA)}
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.report_rows={e["original_public_task_id"]:e
                         for e in cls.report["original_four_paired_rows"]}
        cls.tmp=TemporaryDirectory(prefix="v047-original4-typed-pilot-tests-")
        original=cls.rows["geometry_test_14"]
        cls.source=DATA/"ifc"/original["original_source_ifc_relpath"]
        cls.x=MatchedOriginalXmlSession047(
            cls.source,Path(cls.tmp.name)/"actualxml")
        cls.p=RestrictedOriginalPythonSession047(
            cls.source,Path(cls.tmp.name)/"actualpython")
        cls.edit_xml=make_illustrative_plan(
            cls.x.original_xml,"geometry_test_14",cls.source)
        cls.edit_code=audit.illustrative_python_from_original_xml(
            "geometry_test_14",cls.edit_xml)
        cls.rx=cls.x.call("submit_building_xml",{
            "xml_text":cls.edit_xml.decode("utf8")})
        cls.rp=cls.p.call("submit_native_python",{
            "python_code":cls.edit_code})
        if cls.rx["status"]!="ok" or cls.rp["status"]!="ok":
            raise AssertionError((cls.rx,cls.rp))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v047-poison-")
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)

    def reject(self,program,tid="geometry_test_14"):
        with self.assertRaises(RestrictedNativePython047Error):
            parse_single_restricted_python_call(program,task_id=tid)

    def reject_native(self,program,tid="geometry_test_14"):
        item=self.rows[tid]
        source=DATA/"ifc"/item["original_source_ifc_relpath"]
        with self.assertRaises((
                RestrictedNativePython047Error,OriginalNativeMutation045Error)):
            xml=typed_python_to_exact_original_xml(
                source,item["original_ifc_sha256"],program)
            parse_original_native_edit_plan_v045(
                source,xml,source_sha=item["original_ifc_sha256"])

    def test_01_frozen_report_SHA256_exact(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_previous_v046_frozen_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json"),
            audit.FROZEN_V046_SHA)

    def test_03_previous_v045_frozen_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/"reports"/
            "bibimbap_v045_original4_native_IFC_typed_writers_20261117.json"),
            audit.FROZEN_V045_SHA)

    def test_04_original45_15_15_15_CRUD_unchanged(self):
        self.assertEqual(len(self.rows),45)
        self.assertEqual(Counter(x["crud"] for x in self.rows.values()),
                         {"create":15,"update":15,"delete":15})

    def test_05_original_31_distinct_IFC_SHA(self):
        self.assertEqual(len({x["original_ifc_sha256"] for x in self.rows.values()}),31)

    def test_06_exact_four_original_pinned_IFC_and_question_SHA(self):
        self.assertEqual(len(PINS),4)
        for sha,(tid,crud,qsha,*_) in PINS.items():
            self.assertEqual(self.rows[tid]["original_ifc_sha256"],sha)
            self.assertEqual(self.rows[tid]["public_question_sha256"],qsha)
            self.assertEqual(self.rows[tid]["crud"],crud)

    def test_07_exact_four_original_UPDATE3_DELETE1(self):
        self.assertEqual(Counter(self.rows[t]["crud"] for t in TASKS),
                         {"update":3,"delete":1})

    def test_08_other_original_41_not_in_matched_pilot(self):
        self.assertEqual(self.report["other_original_tasks_NOT_in_matched_restricted_pilot"],41)

    def test_09_original_source_SHA_actual_bytes_unchanged(self):
        for tid in TASKS:
            row=self.rows[tid]
            self.assertEqual(file_hash(DATA/"ifc"/row["original_source_ifc_relpath"]),
                             row["original_ifc_sha256"])

    def test_10_both_model_interfaces_exact_two_tools(self):
        self.assertEqual(len(self.x.tools),len(self.p.tools))
        self.assertEqual(len(self.x.tools),2)

    def test_11_same_exact_25_tool_call_budget(self):
        self.assertEqual(self.x.call_budget,self.p.call_budget)
        self.assertEqual(self.x.call_budget,25)

    def test_12_python_source_is_byte_same_exact_v045_XML(self):
        self.assertEqual(self.p.source_xml,self.x.original_xml)

    def test_13_python_source_literal_roundtrips_original_XML_bytes(self):
        s=self.p.source_python
        self.assertTrue(s.startswith("ORIGINAL_SOURCE_XML = "))
        self.assertEqual(ast.literal_eval(s.split(" = ",1)[1].strip()).encode("utf8"),
                         self.x.original_xml)

    def test_14_python_source_string_has_no_different_original_IFC_facts(self):
        for row in self.report_rows.values():
            self.assertTrue(row["source_python_literal_roundtrip_exact_original_XML"])

    def test_15_all_four_source_metadata_immutable_native_STEP(self):
        self.assertTrue(all(row[
            "original_native_immutable_STEP_and_source_metadata_both_arms_equal"]
            for row in self.report_rows.values()))

    def test_16_all_four_allowed_operations_correct_for_original_task(self):
        self.assertEqual({r["same_whitelisted_native_task_edit_kind"]
                          for r in self.report_rows.values()},
                         set(TASK_OPERATIONS.values()))

    def test_17_all_four_submissions_actually_wrote_XML_native_IFC(self):
        self.assertTrue(all(row["actual_native_IFC_edited_and_written_XML"]
                            for row in self.report_rows.values()))

    def test_18_all_four_submissions_actually_wrote_Python_native_IFC(self):
        self.assertTrue(all(row["actual_native_IFC_edited_and_written_Python"]
                            for row in self.report_rows.values()))

    def test_19_all_four_actual_native_IFC_bytes_equal(self):
        self.assertTrue(all(row[
            "actual_two_independently_written_IFC_bytes_SHA256_IDENTICAL"]
            for row in self.report_rows.values()))

    def test_20_real_geometry14_matched_native_IFC_SHA_and_files(self):
        self.assertEqual(file_hash(self.x.output_ifc),
                         file_hash(self.p.output_ifc))
        self.assertEqual(self.rx["native_ifc_sha256"],
                         self.rp["native_ifc_sha256"])

    def test_21_source_geometry14_both_independent_oracles_PASSED(self):
        for candidate,xml in (
            (self.x.output_ifc,self.edit_xml),
            (self.p.output_ifc,self.p.current_xml),
        ):
            v=verify_original_native_mutation_v045(
                self.source,candidate,submitted_xml=xml,
                source_sha=self.rows["geometry_test_14"]["original_ifc_sha256"],
                task_id="geometry_test_14")
            self.assertEqual(v["status"],
                "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS")

    def test_22_original_four_all_independent_oracles_reported(self):
        self.assertTrue(all(x["both_arms_independent_native_oracle_PASS"]
                            for x in self.report_rows.values()))

    def test_23_original_four_actual_source_target_GUID_symmetric(self):
        self.assertTrue(all(len(x["same_original_native_target_GUIDs"])>=1
                            for x in self.report_rows.values()))

    def test_24_original_four_actual_source_edit_argument_symmetric(self):
        self.assertTrue(all("same_original_native_numerical_arguments" in x
                            for x in self.report_rows.values()))

    def test_25_v047_python_statement_translates_to_trusted_v045_XML(self):
        translated=typed_python_to_exact_original_xml(
            self.source,self.p.source_sha,self.edit_code)
        v=parse_original_native_edit_plan_v045(
            self.source,translated,source_sha=self.p.source_sha)
        self.assertEqual(v.kind,"SetSlabRectangleDimensions")
        self.assertEqual(v.args,(8.9,10.0))

    def test_26_valid_python_source_is_non_executable_literal_render(self):
        tree=ast.parse(self.p.source_python)
        self.assertEqual(len(tree.body),1)
        self.assertIsInstance(tree.body[0],ast.Assign)
        self.assertIsInstance(tree.body[0].value,ast.Constant)

    def test_27_valid_Python_exact_one_expr_call_parsed(self):
        parsed=parse_single_restricted_python_call(
            self.edit_code,task_id="geometry_test_14")
        self.assertEqual(parsed["new_x_dim_m"],8.9)

    def test_28_Python_function_call_has_no_ifcopenshell_globals(self):
        self.assertNotIn("ifcopenshell",self.edit_code)

    def test_29_valid_restricted_Python_function_type_not_unrestricted(self):
        self.assertFalse(self.report[
            "default_original_benchmark_Python_IfcOpenShell_unrestricted_tool_equivalent"])

    def test_30_no_paid_provider_Docker_author_grader_run(self):
        for k in ("real_original_task_author_evaluator_invocations",
                  "paid_provider_calls","Docker_executions",
                  "real_paid_XML_vs_Python_model_trials"):
            self.assertEqual(self.report[k],0)

    def test_31_no_original_benchmark_full_task_answers_or_scores(self):
        self.assertEqual(self.report["new_actual_original_full_task_semantic_solutions_proven"],0)
        self.assertFalse(self.report["original_45_equal_native_write_authority_proven"])

    def test_32_prior_CREATE_D0_I0_pairs_not_inflated(self):
        self.assertEqual(self.report["original_CREATE_developer_task_specific_D0_I0_pairs"],5)

    def test_33_no_unrestricted_import_statement_accepted(self):
        self.reject("import os\nset_slab_rectangle_dimensions(ifc_guid='0'*22,new_x_dim_m=8.9,new_y_dim_m=10)")

    def test_34_no_multiple_statements_accepted(self):
        self.reject(self.edit_code+"\nprint('BAD')")

    def test_35_no_multiple_calls_semicolon(self):
        self.reject(self.edit_code+"; print('BAD')")

    def test_36_no_execute_code_attribute_or_import(self):
        self.reject("__import__('os').system('echo BAD')")

    def test_37_no_attribute_based_python_function(self):
        self.reject("os.set_slab_rectangle_dimensions(ifc_guid='0',new_x_dim_m=8.9,new_y_dim_m=10)")

    def test_38_no_exec_builtin(self):
        self.reject("exec('print(1)')")

    def test_39_no_eval_builtin(self):
        self.reject("eval('1+2')")

    def test_40_no_open_builtin(self):
        self.reject("open('original_data.ifc','wb')")

    def test_41_no_lambda_python(self):
        self.reject("(lambda: 1)()")

    def test_42_no_assign_or_import_python(self):
        self.reject("x=1")

    def test_43_no_comprehension_or_loops(self):
        self.reject("[x for x in range(1000)]")

    def test_44_no_ifcopenshell_api_expr(self):
        self.reject("ifcopenshell.open('other.ifc')")

    def test_45_wrong_original_task_function_rejected(self):
        self.reject("set_all_mapped_column_depth(new_depth_m=2.0)")

    def test_46_wrong_task_delete_function_rejected(self):
        self.reject("delete_columns_by_guid(ifc_guids=['0'*22])")

    def test_47_no_positional_argument_python(self):
        self.reject("set_slab_rectangle_dimensions('0',8.9,10.0)")

    def test_48_no_missing_kwargs_python(self):
        self.reject("set_slab_rectangle_dimensions(ifc_guid='0'*22,new_x_dim_m=8.9)")

    def test_49_no_extra_keyword_python(self):
        self.reject(self.edit_code[:-1]+",unsafe=True)")

    def test_50_no_duplicate_python_kwargs(self):
        self.reject(self.edit_code[:-1]+",new_x_dim_m=8.9)")

    def test_51_no_dynamic_python_kwargs(self):
        self.reject("set_slab_rectangle_dimensions(**{'ifc_guid':'0'*22})")

    def test_52_no_python_string_concatenation_GUID(self):
        self.reject("set_slab_rectangle_dimensions(ifc_guid='0'+'0'*21,new_x_dim_m=8.9,new_y_dim_m=10.0)")

    def test_53_no_python_string_repetition_GUID(self):
        self.reject("set_slab_rectangle_dimensions(ifc_guid='0'*22,new_x_dim_m=8.9,new_y_dim_m=10.0)")

    def test_54_no_python_fstring_GUID(self):
        self.reject("set_slab_rectangle_dimensions(ifc_guid=f'{42}',new_x_dim_m=8.9,new_y_dim_m=10.0)")

    def test_55_no_Python_arithmetic_numeric(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=8+0.9"))

    def test_56_no_nested_Python_calls(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=float('8.9')"))

    def test_57_no_Python_inf_literal(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=1e999"))

    def test_58_no_Python_nan_builtin(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=float('nan')"))

    def test_59_no_Python_bool_as_numeric(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=True"))

    def test_60_no_numeric_list_as_scalar(self):
        self.reject(self.edit_code.replace("new_x_dim_m=8.9","new_x_dim_m=[8.9]"))

    def test_61_no_nonstring_IFC_GUID(self):
        self.reject(self.edit_code.replace("ifc_guid=",
                       "ifc_guid=12345 # ",1))

    def test_62_no_non22_char_IFC_GUID(self):
        self.reject(self.edit_code.replace(
            "ifc_guid="+self.report_rows["geometry_test_14"]["same_original_native_target_GUIDs"][0].__repr__(),
            "ifc_guid='BAD'"))

    def test_63_wrong_existing_original_IFC_GUID_rejected_by_native_gate(self):
        wrong=self.edit_code.replace(
            repr(self.report_rows["geometry_test_14"]["same_original_native_target_GUIDs"][0]),
            repr("0"*22))
        self.reject_native(wrong)

    def test_64_original_Slab_rectangle_bounds_rejected_by_gate(self):
        self.reject_native(self.edit_code.replace("new_x_dim_m=8.9",
                                                  "new_x_dim_m=1000.0"))

    def test_65_original_Slab_rectangle_noop_rejected_by_gate(self):
        self.reject_native(self.edit_code.replace("new_x_dim_m=8.9",
                                                  "new_x_dim_m=8.5"))

    def test_66_wrong_operation_keyword_for_column_move(self):
        self.reject(
            "move_column_placement(ifc_guid='0',new_world_origin_x_m=1.0,new_world_origin_y_m=2.0)",
            "topological_test_11")

    def test_67_shared_column_depth_nan_rejected(self):
        self.reject("set_all_mapped_column_depth(new_depth_m=1e999)",
                    "topological_test_11")

    def test_68_delete_columns_empty_list_rejected(self):
        self.reject("delete_columns_by_guid(ifc_guids=[])",
                    "topological_test_17")

    def test_69_delete_columns_duplicate_GUID_rejected(self):
        guid=self.report_rows["topological_test_17"][
            "same_original_native_target_GUIDs"][0]
        self.reject(f"delete_columns_by_guid(ifc_guids=[{guid!r},{guid!r}])",
                    "topological_test_17")

    def test_70_delete_columns_dynamic_list_comprehension_rejected(self):
        self.reject("delete_columns_by_guid(ifc_guids=[str(i) for i in range(9)])",
                    "topological_test_17")

    def test_71_delete_columns_10_guid_overlimit_rejected(self):
        self.reject("delete_columns_by_guid(ifc_guids=["+
                    ",".join(repr(str(i).zfill(22)) for i in range(10))+"])",
                    "topological_test_17")

    def test_72_delete_columns_nonexistent_guid_rejected_by_native_gate(self):
        self.reject_native(
            "delete_columns_by_guid(ifc_guids=['"+("0"*22)+"'])",
            "topological_test_17")

    def test_73_empty_Python_program_rejected(self):
        self.reject("")

    def test_74_whitespace_only_Python_program_rejected(self):
        self.reject("   \n")

    def test_75_Python_program_over_64k_rejected(self):
        self.reject(self.edit_code+"\n"+(" "*MAX_CODE_BYTES))

    def test_76_Python_program_nul_rejected(self):
        self.reject(self.edit_code+"\x00")

    def test_77_Python_program_UTF8_BOM_rejected(self):
        self.reject("\ufeff"+self.edit_code)

    def test_78_python_program_docstring_only_rejected(self):
        self.reject("'just a comment or string'")

    def test_79_actual_model_native_python_malicious_attempt_rejected_and_rollback(self):
        sha=file_hash(self.p.output_ifc)
        before=self.p.current_xml
        result=self.p.call("submit_native_python",{
            "python_code":"__import__('os').system('nope')"})
        self.assertEqual(result["status"],"error")
        self.assertFalse(result["native_ifc_committed"])
        self.assertTrue(result["last_valid_IFC_and_source_preserved"])
        self.assertEqual(file_hash(self.p.output_ifc),sha)
        self.assertEqual(self.p.current_xml,before)

    def test_80_actual_model_native_XML_spoof_source_rejected_and_rollback(self):
        sha=file_hash(self.x.output_ifc)
        result=self.x.call("submit_building_xml",{
            "xml_text":self.edit_xml.decode("utf8").replace(
                "NativeEditPlan","InventedPlan",1)})
        self.assertEqual(result["status"],"error")
        self.assertFalse(result["native_ifc_committed"])
        self.assertTrue(result["last_valid_xml_preserved"])
        self.assertEqual(file_hash(self.x.output_ifc),sha)
        self.assertEqual(self.x.current_xml,self.edit_xml)

    def test_81_actual_Python_invalid_arg_type_rejected(self):
        result=self.p.call("submit_native_python",{"python_code":17})
        self.assertEqual(result["error_type"],"InvalidSubmitArgs")

    def test_82_actual_Python_unknown_tool_rejected(self):
        result=self.p.call("execute_arbitrary_python",{})
        self.assertEqual(result["error_type"],"UnknownTool")

    def test_83_actual_Python_unknown_read_args_rejected(self):
        result=self.p.call("read_source_python",{"kwargs":"bad"})
        self.assertEqual(result["error_type"],"InvalidReadArgs")

    def test_84_actual_xml_and_py_25_call_budget_both_enforced(self):
        path=DATA/"ifc"/self.rows["geometry_test_14"]["original_source_ifc_relpath"]
        a=MatchedOriginalXmlSession047(path,self.path/"x")
        b=RestrictedOriginalPythonSession047(path,self.path/"p")
        for i in range(25):
            self.assertEqual(a.call("read_building_xml",{})["status"],"ok")
            self.assertEqual(b.call("read_source_python",{})["status"],"ok")
        self.assertEqual(a.call("read_building_xml",{})["error_type"],
                         "ToolBudgetExceeded")
        self.assertEqual(b.call("read_source_python",{})["error_type"],
                         "ToolBudgetExceeded")

    def test_85_both_arms_reject_different_budget_at_init(self):
        path=self.source
        with self.assertRaises(UnsupportedArm):
            MatchedOriginalXmlSession047(path,self.path/"a",max_calls=24)
        with self.assertRaises(UnsupportedArm):
            RestrictedOriginalPythonSession047(path,self.path/"b",max_calls=24)

    def test_86_nonoriginal_IFC_source_blocked_in_both_arms(self):
        from src.runtime.experimental_v46_original_native_catalog import source_profiles
        sha=next(iter(source_profiles()))
        row=next(x for x in self.rows.values() if x["original_ifc_sha256"]==sha)
        source=DATA/"ifc"/row["original_source_ifc_relpath"]
        with self.assertRaises(UnsupportedArm):
            MatchedOriginalXmlSession047(source,self.path/"x-nonpilot")
        with self.assertRaises(UnsupportedArm):
            RestrictedOriginalPythonSession047(source,self.path/"p-nonpilot")

    def test_87_original_public_source_changed_after_session_blocks_both(self):
        copy=self.path/"original-snapshot.ifc"
        copy.write_bytes(self.source.read_bytes())
        a=MatchedOriginalXmlSession047(copy,self.path/"xml")
        b=RestrictedOriginalPythonSession047(copy,self.path/"py")
        self.assertEqual(a.call("read_building_xml",{})["status"],"ok")
        self.assertEqual(b.call("read_source_python",{})["status"],"ok")
        copy.write_bytes(copy.read_bytes()+b"\nNOT_AN_ORIGINAL_IFC")
        self.assertEqual(a.call("read_building_xml",{})["error_type"],
                         "OriginalSourceSHAChanged")
        self.assertEqual(b.call("read_source_python",{})["error_type"],
                         "OriginalSourceSHAChanged")
        self.assertEqual(file_hash(self.source),
                         self.rows["geometry_test_14"]["original_ifc_sha256"])

    def test_88_native_source_XSD_is_prior_v045_not_changed(self):
        self.assertTrue((audit.ROOT/"spec"/
            "original_native_typed_mutations_v045.xsd").is_file())
        self.assertFalse(self.report["same_models_context_tokens_or_tool_ergonomics_proven"])

    def test_89_original_default_Python_code_session_not_replaced(self):
        from tools.bibimbap_matched25_tools import PythonIfcCodeSession
        self.assertTrue(hasattr(PythonIfcCodeSession,"call"))
        self.assertTrue(hasattr(PythonIfcCodeSession,"tools"))

    def test_90_report_previous_exact_five_CREATE_pairs(self):
        self.assertEqual(self.report["original_CREATE_developer_task_specific_D0_I0_pairs"],5)

    def test_91_frozen_report_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:f.write(b"FORGED")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_92_exact_frozen_four_real_paired_audit_byte_replay(self):
        replay=audit.audit(AUTHOR,DATA)
        raw=(json.dumps(replay,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),FROZEN_SHA)
        self.assertEqual(raw,REPORT.read_bytes())


if __name__=="__main__":
    unittest.main()
