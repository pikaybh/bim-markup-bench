"""Tests: v0.37 live current-host original10 CREATE preflight and barriers.

No grader, GT, model provider, Docker or original source mutations.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import ifcopenshell
from lxml import etree

from tools import audit_bibimbap_v037_remaining_create_live_gates as v037
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import XmlSourceEditSession,file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
    r"D:\\문서\\D__1_Projects\\202611"))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=(v037.ROOT/"reports"/
        "bibimbap_v037_original10_create_live_source_and_writer_gates_20261117.json")
FROZEN_REPORT_SHA="33d99e6fb624e6a5e89dc301791c269bd5ca7d2666d8618fc67379664938501f"


class OriginalTenCreateLiveGatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls)->None:
        cls.r=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={x["task_id"]:x for x in cls.r["rows"]}
        _,cls.pub=v037.original_population(AUTHOR,DATA)

    def setUp(self)->None:
        d=TemporaryDirectory(prefix="bmb-v037-negative-")
        self.addCleanup(d.cleanup)
        self.temp=Path(d.name)

    def test_01_frozen_report_sha256_and_prior_ancestors(self):
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)
        self.assertEqual(len(v037.locked_ancestors(v037.ROOT)),6)
        for rel,pin in v037.PRIOR:
            self.assertEqual(file_hash(v037.ROOT/rel),pin)

    def test_02_original_45_ITT_15_create_10_remaining_preserved(self):
        r=self.r
        self.assertEqual(r["original_public_full_ITT_45"],45)
        self.assertEqual(r["original_public_all_CREATE_15"],15)
        self.assertEqual(r["previous_5_nonblinded_original_CREATE_semantic_pairs_still_5"],5)
        self.assertEqual(r["remaining_original_CREATE_not_yet_native_D0_I0_paired"],10)
        self.assertEqual(len(r["rows"]),10)
        self.assertEqual(set(self.rows),set(v037.GENERIC_CREATE_KIND))
        self.assertTrue(set(v037.COMPLETED_CREATE_IDS).isdisjoint(self.rows))
        self.assertEqual(len(self.pub),45)

    def test_03_live_schema_and_projection_gates_count_3_and_2(self):
        r=self.r
        self.assertEqual(r["remaining_CREATE_live_source_XML_admitted_count"],5)
        self.assertEqual(r["remaining_CREATE_live_source_XML_rejected_count"],5)
        self.assertEqual(r["source_schema_hard_rejections"],3)
        self.assertEqual(r["native_geometry_projection_hard_rejections"],2)
        for tid in ("geometry_test_03","geometry_test_04","geometry_test_05"):
            row=self.rows[tid]
            self.assertEqual(row["actual_XML_session_admission"],"BLOCKED_NON_IFC4X3")
            self.assertEqual(row["actual_XML_session_block_reason"],"SCHEMA_GATE")
        for tid in ("geometry_test_01","topological_test_05"):
            row=self.rows[tid]
            self.assertEqual(row["actual_XML_session_admission"],"BLOCKED_NATIVE_PROJECTION")
            self.assertEqual(row["actual_XML_session_block_reason"],"UNSUPPORTED_GEOMETRY")

    def test_04_original_native_schema_and_unit_evidence(self):
        self.assertEqual(self.rows["geometry_test_03"]["original_ifc_schema"],"IFC2X3")
        self.assertEqual(self.rows["geometry_test_04"]["original_ifc_schema"],"IFC2X3")
        self.assertEqual(self.rows["geometry_test_05"]["original_ifc_schema"],"IFC4")
        for tid,row in self.rows.items():
            self.assertEqual(row["original_ifc_schema"],v037.EXPECTED_SCHEMAS[tid])
            self.assertTrue(row["native_millimetre_units"])
            self.assertTrue(row["source_native_sha256_unchanged_after_probe"])
            self.assertEqual(row["original_public_IFC_sha256"],
                             self.pub[tid]["original_ifc_sha256"])
            self.assertEqual(row["public_question_sha256"],
                             self.pub[tid]["public_question_sha256"])

    def test_05_explicit_named_IfcSpace_in_source_but_not_XML(self):
        r=self.rows["topological_test_01"]
        self.assertEqual(r["native_source_IfcProduct_class_counts"]["IfcSpace"],1)
        self.assertEqual(r["unrepresented_original_native_IfcProduct_classes"]["IfcSpace"],1)
        self.assertEqual(len(r["original_public_named_IfcProduct_references"]),1)
        self.assertEqual(r["original_public_named_IfcProduct_references"][0]["ifc_class"],"IfcSpace")
        self.assertEqual(r["named_GUID_in_current_full_XML"][0]["visible"],False)
        self.assertTrue(r["original_IfcSpace_required_for_room_reference_but_not_visible_in_XML"])
        self.assertFalse(r["public_room_named_GUIDs_refer_to_native_IfcWall_not_IfcSpace"])

    def test_06_original_topological03_room_IDs_are_native_Walls_not_Spaces(self):
        r=self.rows["topological_test_03"]
        self.assertEqual(r["native_source_IfcProduct_class_counts"]["IfcSpace"],2)
        self.assertEqual(r["unrepresented_original_native_IfcProduct_classes"]["IfcSpace"],2)
        self.assertEqual(len(r["original_public_named_IfcProduct_references"]),2)
        self.assertEqual({x["ifc_class"] for x in
                          r["original_public_named_IfcProduct_references"]},{"IfcWall"})
        self.assertTrue(all(x["visible"] for x in
                            r["named_GUID_in_current_full_XML"]))
        self.assertTrue(r["public_room_named_GUIDs_refer_to_native_IfcWall_not_IfcSpace"])
        self.assertTrue(r["original_IfcSpace_required_for_room_reference_but_not_visible_in_XML"])

    def test_07_three_generic_Column_or_Slab_writes_rejected_in_real_host(self):
        self.assertEqual(self.r["illustrative_GENERIC_Column_Slab_mutations_rejected"],3)
        for tid,klass in (("geometry_test_02","Column"),
                          ("topological_test_02","Column"),
                          ("topological_test_04","Slab")):
            r=self.rows[tid]
            self.assertEqual(r["generic_authoring_class_probed"],klass)
            self.assertEqual(r["actual_XML_session_admission"],"ADMITTED_SOURCE_ONLY")
            self.assertEqual(r["actual_generic_native_create_probe"],
                             "BLOCKED_UNSUPPORTED_NEW_CLASS")

    def test_08_two_generic_Wall_writes_commit_but_are_not_task_success(self):
        self.assertEqual(self.r["illustrative_GENERIC_Wall_natives_committed_not_task_success"],2)
        for tid in ("topological_test_01","topological_test_03"):
            r=self.rows[tid]
            self.assertEqual(r["generic_authoring_class_probed"],"Wall")
            self.assertEqual(r["actual_generic_native_create_probe"],
                             "ILLUSTRATIVE_WALL_SAVED_NATIVE")
            self.assertFalse(r["generic_probe_is_original_task_solution"])
            self.assertFalse(r["claimed_complete_current_D_I_causal_trial_eligibility"])

    def test_09_named_four_Walls_in_topological02_and_04_all_in_XML(self):
        for tid in ("topological_test_02","topological_test_04"):
            r=self.rows[tid]
            self.assertEqual(len(r["original_public_named_IfcProduct_references"]),4)
            self.assertTrue(all(x["ifc_class"]=="IfcWall" for x in
                                r["original_public_named_IfcProduct_references"]))
            self.assertTrue(all(x["visible"] for x in
                                r["named_GUID_in_current_full_XML"]))
        r=self.rows["geometry_test_02"]
        self.assertEqual(r["native_source_IfcProduct_class_counts"]["IfcWall"],4)
        self.assertEqual(r["live_XML_typed_node_class_counts"]["Wall"],4)

    def test_10_geometry01_original_four_columns_are_real_but_projection_rejects(self):
        r=self.rows["geometry_test_01"]
        self.assertEqual(r["native_source_IfcProduct_class_counts"]["IfcColumn"],4)
        self.assertEqual(r["actual_generic_native_create_probe"],
                         "NOT_ATTEMPTED_SOURCE_REJECTED")
        self.assertIsNone(r["visible_typed_XML_product_count"])

    def test_11_topological05_original_seven_walls_exist_but_projection_rejects(self):
        r=self.rows["topological_test_05"]
        self.assertEqual(r["native_source_IfcProduct_class_counts"]["IfcWall"],7)
        self.assertEqual(r["generic_authoring_class_probed"],"Door")
        self.assertEqual(r["actual_generic_native_create_probe"],
                         "NOT_ATTEMPTED_SOURCE_REJECTED")

    def test_12_empty_ifc_is_not_native_empty_and_schema_is_IFC4(self):
        r=self.rows["geometry_test_05"]
        self.assertEqual(r["native_source_IfcProduct_count"],3)
        self.assertEqual(r["native_source_IfcProduct_class_counts"],
                         {"IfcBuilding":1,"IfcBuildingStorey":1,"IfcSite":1})
        self.assertEqual(r["original_ifc_schema"],"IFC4")

    def test_13_exact_actionable_queue_is_complete_disjoint_and_sorted(self):
        queue=self.r["priority_tier_population"]
        self.assertEqual([x["tier"] for x in queue],list(v037.PRIORITY_TIERS))
        self.assertEqual([len(x["task_ids"]) for x in queue],[3,2,2,3])
        self.assertEqual([x["task_ids"] for x in queue],[
            ["geometry_test_03","geometry_test_04","geometry_test_05"],
            ["geometry_test_01","topological_test_05"],
            ["topological_test_01","topological_test_03"],
            ["geometry_test_02","topological_test_02","topological_test_04"],
        ])
        self.assertEqual(set(sum((x["task_ids"] for x in queue),[])),set(self.rows))

    def test_14_source_parity_native_edit_parity_and_model_trial_remain_zero(self):
        r=self.r
        self.assertEqual(r["original45_full_task_relevant_read_information_parity_proven"],0)
        self.assertEqual(r["original45_full_native_write_capability_parity_proven"],0)
        self.assertEqual(r["real_matched_LLM_D_I_trials"],0)
        self.assertEqual(r["original_author_evaluator_invocations"],0)
        self.assertEqual(r["real_model_or_paid_inference_calls"],0)
        self.assertEqual(r["Docker_executions"],0)
        self.assertEqual(r["original45_developer_native_byte_equal_11_unchanged"],11)
        self.assertFalse(r["causal_XML_vs_Python_representation_effect_supported"])
        self.assertFalse(r["live_XML_admission_means_task_success"])
        self.assertFalse(r["generic_writer_commit_means_task_success"])

    def test_15_all_10_native_source_classes_and_count_currently_consistent(self):
        for tid in self.rows:
            path=DATA/"ifc"/self.pub[tid]["original_source_ifc_relpath"]
            m=ifcopenshell.open(str(path))
            self.assertEqual(len(m.by_type("IfcProduct")),
                             self.rows[tid]["native_source_IfcProduct_count"])
            self.assertEqual(len(m.by_type("IfcRoot")),
                             self.rows[tid]["native_root_GUID_count"])
            self.assertEqual(file_hash(path),
                             self.rows[tid]["original_public_IFC_sha256"])

    def test_16_no_current_host_edits_and_all_frozen_inputs_preserved(self):
        self.assertTrue(self.r["current_v037_applies_no_changes_to_matched_host_or_original_IFC"])
        self.assertEqual(file_hash(v037.ROOT/"tools/bibimbap_matched25_tools.py"),
                         self.r["current_matched_host_file_sha256"])
        self.assertEqual(file_hash(v037.ROOT/"src/runtime/compiler.py"),
                         self.r["current_matched_default_compiler_file_sha256"])
        for row in self.rows.values():
            self.assertFalse(row["matched_LLM_execution"])
            self.assertFalse(row["original_author_evaluator_called"])
            self.assertFalse(row["full_task_relevant_information_parity_proven"])
            self.assertFalse(row["full_task_relevant_native_write_parity_proven"])

    def test_17_public_SHA_manifest_is_prior_and_pinned(self):
        path=v037.ROOT/"reports"/v037.V022_FROZEN_ROLES[0]
        self.assertEqual(file_hash(path),v037.V022_FROZEN_ROLES[1])
        roles=json.loads(path.read_text(encoding="utf8"))
        indexed={x["task_id"]:x for x in
                 roles["all45_per_task_actual_source_role_and_admission_rows"]}
        self.assertEqual(len(indexed),45)
        for tid in self.rows:
            self.assertEqual(self.rows[tid]["public_question_sha256"],
                             indexed[tid]["original_public_question_sha256"])

    def test_18_generic_full_XML_state_has_one_new_Column_not_commands(self):
        t=self.pub["geometry_test_02"]
        src=DATA/"ifc"/t["original_source_ifc_relpath"]
        before=file_hash(src)
        ses=XmlSourceEditSession(src,self.temp/"source")
        edited=v037.generic_edited_whole_xml(ses.current_xml,"Column")
        p=etree.fromstring(edited)
        ns=v037.XML_NS
        cols=[x for x in p.find(ns+"Elements") if x.tag==ns+"Column"]
        self.assertEqual(len(cols),1)
        self.assertEqual(cols[0].get("height"),"3")
        self.assertEqual(cols[0].get("width"),"0.3")
        self.assertNotIn(b"<Create",edited)
        self.assertEqual(file_hash(src),before)
        self.assertEqual(ses.submissions,0)

    def test_19_generic_Wall_and_Slab_XML_use_original_level(self):
        t=self.pub["geometry_test_02"]
        src=DATA/"ifc"/t["original_source_ifc_relpath"]
        ses=XmlSourceEditSession(src,self.temp/"source")
        doc=etree.fromstring(ses.current_xml)
        first=doc.find(v037.XML_NS+"Levels")[0].get("id")
        for cls in ("Wall","Slab"):
            edited=etree.fromstring(
                v037.generic_edited_whole_xml(ses.current_xml,cls))
            created=next(x for x in edited.find(v037.XML_NS+"Elements")
                         if x.get("id")==v037.GENERIC_CREATE_BASE["id"])
            self.assertEqual(created.get("level"),first)
            self.assertEqual(created.tag,v037.XML_NS+cls)
        self.assertEqual(ses.submissions,0)

    def test_20_generic_creator_rejects_unknown_class_without_SIDE_EFFECT(self):
        with self.assertRaisesRegex(v037.V037LiveGateBlocked,"No generic"):
            v037.generic_edited_whole_xml(b"not even XML","Door")

    def test_21_source_SHA_drift_fails_before_actual_current_host_start(self):
        t=dict(self.pub["geometry_test_02"])
        t["original_ifc_sha256"]="0"*64
        with self.assertRaisesRegex(v037.V037LiveGateBlocked,"SHA256"):
            v037.source_row(t,DATA/"ifc")

    def test_22_public_question_SHA_mismatch_rejected_with_git_head_unchanged(self):
        entries=[dict(x) for x in public_45(AUTHOR,DATA)]
        edited=next(x for x in entries if x["test_id"]=="geometry_test_02")
        edited["public_question_sha256"]="0"*64
        with patch.object(v037,"public_45",return_value=entries):
            with self.assertRaisesRegex(v037.V037LiveGateBlocked,
                                        "public question/source SHA"):
                v037.audit_remaining_create(v037.ROOT,AUTHOR,DATA)

    def test_23_duplicate_original_task_is_fatal_no_ITT_resampling(self):
        entries=[dict(x) for x in public_45(AUTHOR,DATA)]
        entries[1]["test_id"]=entries[0]["test_id"]
        with patch.object(v037,"public_45",return_value=entries):
            with self.assertRaisesRegex(v037.V037LiveGateBlocked,"45/15"):
                v037.audit_remaining_create(v037.ROOT,AUTHOR,DATA)

    def test_24_corrupted_frozen_ancestor_blocks_audit(self):
        with TemporaryDirectory(prefix="bmb-v037-ancestor-poison-") as tmp:
            t=Path(tmp)
            for rel,pin in v037.PRIOR:
                p=t/rel
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((v037.ROOT/rel).read_bytes())
            target=t/v037.PRIOR[0][0]
            target.write_bytes(target.read_bytes()+b"CORRUPT")
            with self.assertRaisesRegex(v037.V037LiveGateBlocked,"Prior immutable"):
                v037.locked_ancestors(t)

    def test_25_source_path_traversal_rejected(self):
        t=dict(self.pub["geometry_test_02"])
        t["original_source_ifc_relpath"]="../../outside.ifc"
        with self.assertRaises(v037.V037LiveGateBlocked):
            v037.source_row(t,DATA/"ifc")

    def test_26_tampered_live_cohort_priority_fails_closed(self):
        r=dict(self.rows["geometry_test_02"])
        r["actual_generic_native_create_probe"]="ILLUSTRATIVE_WALL_SAVED_NATIVE"
        with self.assertRaisesRegex(v037.V037LiveGateBlocked,"unidentified"):
            v037.classify_gates(r)

    def test_27_model_and_original_scorer_imports_absent(self):
        s=Path(v037.__file__).read_text(encoding="utf8")
        modules=[]
        for node in ast.walk(ast.parse(s)):
            if isinstance(node,ast.Import):
                modules.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):
                modules.append(node.module or "")
        for bad in ("bibimbap_author_worker","bibimbap_docker_ifc_code_worker",
                    "openai","torch","subprocess","os.system"):
            self.assertFalse(any(bad in x for x in modules))
        self.assertNotIn("grade_author(",s)
        self.assertNotIn("execute_ifc_code(",s)
        self.assertNotIn("DockerIFCExecutor(",s)

    def test_28_report_is_exclusive_write_once(self):
        self.assertTrue(REPORT.is_file())
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as handle:
                handle.write(b"never overwrite frozen evidence")
        self.assertEqual(file_hash(REPORT),FROZEN_REPORT_SHA)

    def test_29_actual_10_host_replay_generates_identical_frozen_report(self):
        # This truly runs all source-host constructor tests and 5 generic
        # IFC writer probes; it is NOT a stored-report-only claim.
        recreated=v037.audit_remaining_create(v037.ROOT,AUTHOR,DATA)
        raw=(json.dumps(recreated,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(raw,REPORT.read_bytes())
        self.assertEqual(len(recreated["rows"]),10)

    def test_30_mutated_native_source_file_does_not_change_original(self):
        t=self.pub["topological_test_03"]
        f=DATA/"ifc"/t["original_source_ifc_relpath"]
        before=file_hash(f)
        target=self.temp/"different.ifc"
        target.write_bytes(f.read_bytes()+b"tampered\n")
        false=dict(t)
        false["original_source_ifc_relpath"]="../../"+str(target.name)
        with self.assertRaises(v037.V037LiveGateBlocked):
            v037.source_row(false,DATA/"ifc")
        self.assertEqual(file_hash(f),before)

    def test_31_no_hidden_solution_or_private_original_scorer_in_frozen_report(self):
        text=REPORT.read_text(encoding="utf8")
        self.assertNotIn("original_author_score",text)
        self.assertNotIn("private_ground_truth",text)
        self.assertNotIn("API_KEY",text)
        self.assertNotIn("raw_source_IFC_base64",text)
        self.assertNotIn("Full-XML task solution",text)
        self.assertLess(REPORT.stat().st_size,40000)


if __name__=="__main__":
    unittest.main()
