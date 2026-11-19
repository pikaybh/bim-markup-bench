"""v0.18 original-public-source common IFC facts: two-arm D/I replay tests.

No LLM, author scorer, private answers, native file edits, paid API calls.
Original 45 task count retained. This is NOT OS sandbox / causal-ready.
"""
from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v018_common_read import (
    PACKET_SCHEMA, CommonReadBlocked, CommonReadSession,
    build_public_source_packet, bind_public_question_to_frozen_source_packet,
    canonical_json, compare_equal_observations, strict_llm_trial_launch_gate,
)

ROOT = Path(os.getenv("BIBIMBAP_EXPERIMENT_BASE", r"D:\문서\D__1_Projects\202611"))
HERE = Path(__file__).resolve().parents[1]
AUTHOR = ROOT / "bibimbap-author-upstream"
DATA = ROOT / "bibimbap-author-data"
REPORT = HERE / "reports" / "bibimbap_v018_original45_common_read_observation_audit_20261114.json"
REPORT_SHA = "89a53c28a9c5e679fcdfb962bebe6b9bd8075e4ac0437e07ea1a0b72ea7b1b2a"


class V018CommonOriginalSourceObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file() or not AUTHOR.is_dir() or not DATA.is_dir():
            raise unittest.SkipTest("Expected pinned versioned original public test inputs")
        cls.public = {t["test_id"]: t for t in public_45(AUTHOR, DATA)}
        cls.audit = json.loads(REPORT.read_text(encoding="utf8"))
        cls.packets = {}
        cls.raw = {}
        cls.native_source_hashes = {}
        for case in ("test_15", "test_16", "topological_test_15"):
            t = cls.public[case]
            original = DATA / "ifc" / t["original_source_ifc_relpath"]
            cls.native_source_hashes[case] = file_hash(original)
            packet = build_public_source_packet(
                original, t["public_question_sha256"]
            )
            cls.packets[case] = packet
            cls.raw[case] = json.loads(packet)

    def test_pinned_original_source_data_and_45_intention_to_test(self):
        self.assertEqual(_head(AUTHOR), AUTHOR_SHA)
        self.assertEqual(_head(DATA), DATA_SHA)
        self.assertEqual(len(self.public), 45)
        self.assertEqual(file_hash(REPORT), REPORT_SHA)
        self.assertEqual(self.audit["original_original45_denominator"],45)
        self.assertEqual(self.audit["original_unique_ifc_source_count"],31)
        self.assertEqual(
            self.audit["original_public_15_per_crud"],
            {"create":15,"update":15,"delete":15})
        self.assertEqual(
            set(x["task_id"] for x in
                self.audit["all_45_public_task_read_observation_audit"]),
            set(self.public))
        self.assertTrue(self.audit["original_full_population_45_preserved"])

    def test_all_45_two_arm_common_fact_read_replay_passes(self):
        self.assertTrue(self.audit["common_read_observation_bytes_equal_across_45_tasks"])
        self.assertEqual(self.audit["common_read_observation_parity_case_count"],45)
        self.assertEqual(
            len(self.audit["all_45_public_task_read_observation_audit"]),45)
        for item in self.audit["all_45_public_task_read_observation_audit"]:
            with self.subTest(case=item["task_id"]):
                self.assertEqual(
                    item["shared_read_only_observation_replay"],"PASS")
                self.assertTrue(item["native_IFC_original_source_unchanged"])
                self.assertGreater(item["identical_D_I_read_calls"],0)
                self.assertLessEqual(item["identical_D_I_read_calls"],25)
                self.assertGreater(item["observed_native_source_class_query_count"],0)
                self.assertIsInstance(item["common_public_facts_packet_sha256"],str)
                self.assertEqual(item["real_matched_LLM_run_count"],0)
                self.assertFalse(item["independent_native_Python_execution_confinement_proven"])
                self.assertFalse(item["full_original_IFC_semantic_information_equivalent"])
                self.assertTrue(item["is_original45_public_denominator_member"])

    def test_source_31_unique_IFCs_and_all_native_480_products(self):
        self.assertEqual(
            self.audit["actual_distinct_original_IfcProduct_inventory_count_across_source_snapshots"],480)
        self.assertEqual(
            self.audit["original_source_schema_counts_across_unique_IFCs"],
            {"IFC2X3":2, "IFC4":1, "IFC4X3":28})
        self.assertEqual(
            self.audit["geometry_coverage_by_original_native_unique_source"],
            {"NO_SHAPE_REPRESENTATION":125, "PHYSICAL_WORLD_BBOX_METRES":355})
        self.assertEqual(
            self.audit["placement_coverage_by_original_native_unique_source"],
            {"WORLD_PLACEMENT_AVAILABLE":480})

    def test_original_public_task_snapshots_only_and_byte_determinism(self):
        for case in self.packets:
            with self.subTest(case=case):
                t=self.public[case]
                src=DATA/"ifc"/t["original_source_ifc_relpath"]
                rerun=build_public_source_packet(src,t["public_question_sha256"])
                self.assertEqual(rerun,self.packets[case])
                self.assertEqual(
                    self.raw[case]["public_source"]["original_ifc_sha256"],
                    file_hash(src))
                self.assertEqual(
                    self.raw[case]["public_source"]["public_question_sha256"],
                    t["public_question_sha256"])
                self.assertEqual(file_hash(src), self.native_source_hashes[case])

    def test_original_IFC_product_inventory_complete_and_geom_explicit(self):
        for case in ("test_15","topological_test_15"):
            with self.subTest(case=case):
                source = DATA/"ifc"/self.public[case]["original_source_ifc_relpath"]
                original = ifcopenshell.open(str(source))
                packet = self.raw[case]
                model_ids={p.GlobalId for p in original.by_type("IfcProduct")}
                packet_ids={p["global_id"] for p in packet["products"]}
                self.assertEqual(packet_ids,model_ids)
                self.assertEqual(
                    len(packet_ids),
                    packet["manifest"]["all_native_source_IfcProduct_count"])
                self.assertEqual(
                    len(packet_ids),
                    packet["manifest"]["serialized_native_IfcProduct_count"])
                for product in packet["products"]:
                    self.assertIn(product["geometry"]["status"],
                                  ("PHYSICAL_WORLD_BBOX_METRES", "NO_SHAPE_REPRESENTATION",
                                   "MESH_EMPTY", "MESH_NONFINITE", "MESH_UNAVAILABLE"))
                    if product["geometry"]["status"] != "PHYSICAL_WORLD_BBOX_METRES":
                        self.assertIsNone(product["geometry"]["bbox_world_m"])
                    self.assertEqual(product["placement"]["status"],
                                     "WORLD_PLACEMENT_AVAILABLE")

    def test_common_read_fact_packet_not_authoring_command_interface(self):
        self.assertEqual(self.raw["test_15"]["schema"], PACKET_SCHEMA)
        self.assertFalse(
            self.raw["test_15"]["manifest"][
                "native_IFC_file_writer_or_mutator_access_in_packet"])
        self.assertFalse(
            self.raw["test_15"]["manifest"][
                "full_native_IFC_semantic_information_equivalent"])
        self.assertFalse(
            self.raw["test_15"]["manifest"][
                "geometry_raw_mesh_and_topology_exhaustive"])
        self.assertFalse(
            self.raw["test_15"]["manifest"]["ifc_property_sets_exhaustive"])

    def test_native_original_IFC_source_unit_is_not_falsely_metre(self):
        packet=self.raw["test_15"]
        self.assertEqual(packet["public_source"]["ifc_schema"],"IFC4X3")
        self.assertAlmostEqual(
            packet["public_source"]["native_length_unit_to_metres"],0.001)
        # World geometry is already converted to metres by native IfcOpenShell
        # geom, not rounded/treated as native millimetres.
        high_slab=next(
            x for x in packet["products"]
            if x["ifc_class"]=="IfcSlab" and x["geometry"]["bbox_world_m"] is not None
        )
        self.assertLess(
            high_slab["geometry"]["bbox_world_m"][2][1],100)

    def test_D_I_sessions_same_raw_responses_and_sha_transcript(self):
        source=self.packets["test_15"]
        digest=sha256(source).hexdigest()
        d=CommonReadSession(source,"D",expected_packet_sha256=digest)
        i=CommonReadSession(source,"I",expected_packet_sha256=digest)
        original_public=self.public["test_15"]["public_question"]
        target_guid=next(p["global_id"] for p in self.raw["test_15"]["products"]
                         if p["global_id"] in original_public)
        queries=(
            {"operation":"source_summary"},
            {"operation":"list_all_products"},
            {"operation":"list_by_class","ifc_class":"IfcColumn"},
            {"operation":"get_product","global_id":target_guid},
            {"operation":"related_relations","global_id":target_guid},
        )
        verdict=compare_equal_observations(d,i,queries)
        self.assertTrue(verdict["D_and_I_exact_common_read_response_bytes_identical"])
        self.assertEqual(verdict["call_count"],len(queries))
        self.assertEqual(d.calls_used,i.calls_used)
        self.assertEqual(d.receipt()["observation_hash_transcript"],
                         i.receipt()["observation_hash_transcript"])
        self.assertEqual(d.receipt()["packet_sha256"],digest)
        self.assertEqual(i.receipt()["packet_sha256"],digest)

    def test_source_readonly_list_by_class_results_actual_native(self):
        packet=self.packets["test_15"]
        s=CommonReadSession(packet,"D",expected_packet_sha256=sha256(packet).hexdigest())
        out=json.loads(s.request("list_by_class",ifc_class="IfcColumn"))
        src=DATA/"ifc"/self.public["test_15"]["original_source_ifc_relpath"]
        native=ifcopenshell.open(str(src))
        self.assertEqual({x["global_id"] for x in out["products"]},
                         {x.GlobalId for x in native.by_type("IfcColumn")})
        self.assertTrue(all(x["ifc_class"]=="IfcColumn" for x in out["products"]))
        none=json.loads(s.request("list_by_class",ifc_class="IfcNonExisting"))
        self.assertEqual(none["products"],[])

    def test_returned_json_is_independent_not_a_mutable_source(self):
        packet=self.packets["test_15"]
        s=CommonReadSession(packet,"I",expected_packet_sha256=sha256(packet).hexdigest())
        first=json.loads(s.request("list_all_products"))
        first["products"].clear()
        second=json.loads(s.request("list_all_products"))
        self.assertEqual(len(second["products"]),
                         len(self.raw["test_15"]["products"]))
        self.assertNotEqual(len(first["products"]),len(second["products"]))

    def test_valid_packet_rebind_keeps_original_IFC_facts(self):
        a=self.packets["test_15"]
        b=self.packets["test_16"]
        reb=bind_public_question_to_frozen_source_packet(
            a,self.public["test_16"]["public_question_sha256"])
        self.assertEqual(reb,b)
        self.assertNotEqual(sha256(a).hexdigest(),sha256(b).hexdigest())
        self.assertEqual(
            self.raw["test_15"]["products"],self.raw["test_16"]["products"])
        self.assertEqual(
            self.raw["test_15"]["relationships"],self.raw["test_16"]["relationships"])

    def test_canonical_packet_rejects_truncated_or_noncanonical(self):
        source=self.packets["test_15"]
        good=sha256(source).hexdigest()
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source+b"\n","D",expected_packet_sha256=good)
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source[:-2],"D",expected_packet_sha256=good)
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source,"I",expected_packet_sha256="0"*64)
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source,"D",expected_packet_sha256="invalid")
        with self.assertRaises(CommonReadBlocked):
            bind_public_question_to_frozen_source_packet(source+b"\n",
                self.public["test_16"]["public_question_sha256"])

    def test_read_only_unexpected_write_or_invalid_query_blocked_without_budget_use(self):
        source=self.packets["test_15"]
        s=CommonReadSession(source,"D",expected_packet_sha256=sha256(source).hexdigest())
        blocked=(
            {"operation":"edit_element"},
            {"operation":"write_ifc"},
            {"operation":"get_product","global_id":"../../secrets"},
            {"operation":"get_product","global_id":"Z"*22},
            {"operation":"source_summary","global_id":"Z"*22},
            {"operation":"list_all_products","ifc_class":"IfcColumn"},
            {"operation":"list_by_class","ifc_class":"../../../foo"},
        )
        for q in blocked:
            with self.subTest(query=q), self.assertRaises(CommonReadBlocked):
                s.request(**q)
        self.assertEqual(s.calls_used,0)

    def test_source_read_cap_25_and_no_retries_free(self):
        source=self.packets["test_15"]
        digest=sha256(source).hexdigest()
        s=CommonReadSession(source,"D",expected_packet_sha256=digest,max_calls=1)
        s.request("source_summary")
        self.assertEqual(s.calls_used,1)
        with self.assertRaises(CommonReadBlocked):
            s.request("source_summary")
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source,"I",expected_packet_sha256=digest,max_calls=26)
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(source,"I",expected_packet_sha256=digest,max_calls=0)

    def test_equal_read_requires_different_arms_same_source_bytes_and_budget(self):
        packet=self.packets["test_15"]
        h=sha256(packet).hexdigest()
        b=self.packets["test_16"]
        with self.assertRaises(CommonReadBlocked):
            compare_equal_observations(
                CommonReadSession(packet,"D",expected_packet_sha256=h),
                CommonReadSession(b,"I",expected_packet_sha256=sha256(b).hexdigest()),
                ({"operation":"source_summary"},))
        with self.assertRaises(CommonReadBlocked):
            compare_equal_observations(
                CommonReadSession(packet,"D",expected_packet_sha256=h,max_calls=5),
                CommonReadSession(packet,"I",expected_packet_sha256=h,max_calls=4),
                ({"operation":"source_summary"},))
        with self.assertRaises(CommonReadBlocked):
            compare_equal_observations(
                CommonReadSession(packet,"I",expected_packet_sha256=h),
                CommonReadSession(packet,"I",expected_packet_sha256=h),
                ({"operation":"source_summary"},))

    def test_model_launch_fail_closed_if_python_original_native_sidechannel(self):
        gate=strict_llm_trial_launch_gate(
            common_facts_identical=True,native_python_original_ifc_mount=True,
            python_unrestricted_filesystem_or_exec=True,
            independent_os_sandbox_attestation=False,
            matched_write_capability_verified=False,
            explicit_paid_budget_approved=False)
        self.assertEqual(gate["status"],"BLOCKED")
        self.assertFalse(gate["causal_real_LLM_launch_permitted_by_this_module"])
        self.assertIn("PYTHON_NATIVE_ORIGINAL_IFC_SIDE_CHANNEL_PRESENT",
                      gate["blockers"])
        self.assertIn("UNRESTRICTED_PYTHON_CODE_OR_FILESYSTEM_SIDE_CHANNEL_PRESENT",
                      gate["blockers"])
        self.assertIn("NO_VERIFIED_EXTERNAL_OS_SANDBOX_ATTESTATION",
                      gate["blockers"])
        self.assertIn("NO_EXPLICIT_PAID_LLM_BUDGET_APPROVAL",
                      gate["blockers"])

    def test_even_boolean_only_fake_attestation_cannot_launch_unsafe_python(self):
        gate=strict_llm_trial_launch_gate(
            common_facts_identical=True,native_python_original_ifc_mount=False,
            python_unrestricted_filesystem_or_exec=False,
            independent_os_sandbox_attestation=True,
            matched_write_capability_verified=True,
            explicit_paid_budget_approved=True)
        self.assertFalse(gate["causal_real_LLM_launch_permitted_by_this_module"])
        self.assertEqual(gate["status"],"REQUIRES_INDEPENDENT_HOST_ENFORCEMENT")

    def test_bad_input_corruption_fail_closed_on_original_packet(self):
        source=self.packets["test_15"]
        tampered=json.loads(source)
        tampered["products"].pop()
        tampered_bytes=canonical_json(tampered)
        with self.assertRaises(CommonReadBlocked):
            CommonReadSession(tampered_bytes,"D",
                expected_packet_sha256=sha256(source).hexdigest())

    def test_all_original_data_and_prior_evidence_read_only_unmodified(self):
        for case in self.native_source_hashes:
            src=DATA/"ifc"/self.public[case]["original_source_ifc_relpath"]
            self.assertEqual(file_hash(src),self.native_source_hashes[case])
        self.assertEqual(_head(AUTHOR),AUTHOR_SHA)
        self.assertEqual(_head(DATA),DATA_SHA)
        self.assertEqual(self.audit["new_real_matched_D_I_LLM_trials"],0)
        self.assertEqual(self.audit["new_paid_model_requests"],0)
        self.assertEqual(self.audit["new_paid_usd"],0)
        self.assertFalse(
            self.audit["Python_file_mount_and_exec_side_channel_eliminated"])
        self.assertFalse(
            self.audit["full_IFC_entity_relationship_property_mesh_information_equivalence"])

    def test_model_read_module_is_not_source_editor_or_scorer_importer(self):
        from tools import bibimbap_v018_common_read
        txt=Path(bibimbap_v018_common_read.__file__).read_text(encoding="utf8")
        tree=ast.parse(txt)
        modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                modules.append(node.module or "")
            elif isinstance(node,ast.Import):
                modules.extend(x.name for x in node.names)
        self.assertFalse(any(m.startswith(("src.","tools.")) for m in modules))
        self.assertFalse(any(m.startswith("ifcopenshell.api") for m in modules))
        self.assertNotIn("grade_author(",txt)
        self.assertNotIn("compile_declarative_xml",txt)


if __name__=="__main__":
    unittest.main()
