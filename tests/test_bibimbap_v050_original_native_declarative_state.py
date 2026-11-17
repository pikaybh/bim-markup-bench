"""v0.50 D-state direct declarative IFC research controls and tamper negatives."""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from lxml import etree

from src.runtime.experimental_v44_original_native_step_readonly import Q
from src.runtime.experimental_v45_original_native_mutations import (
    project_original_native_mutations_v045,
)
from src.runtime.experimental_v50_original_declarative_state import (
    DeclarativeState050Error, MAX_XML_BYTES, MAX_CALLS,
    project_original_declarative_state_v050,
    parse_original_declarative_state_diff_v050,
    _xsd,
)
from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash
from tools.audit_bibimbap_v045_original4_native_mutations import make_illustrative_plan
from tools.audit_bibimbap_v048_original4_semantic_controls import (
    positive_developer_source_edit,
)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,
)
from tools.bibimbap_v050_direct_original_state_session import (
    DirectOriginalStateSession050,
)
from tools import audit_bibimbap_v050_declarative_state as audit


BASE = Path(r"D:\문서\D__1_Projects\202611")
AUTHOR = BASE / "bibimbap-author-upstream"
DATA = BASE / "bibimbap-author-data"
TASKS = audit.TASK_IDS
FROZEN_SHA = "eb6bef852eabf12ed76b5c5df861a8e5a355a5142e5ad0d3732d646b25dfb28a"


class OriginalFourNativeDeclarativeState050(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = {t["test_id"]: t for t in public_45(AUTHOR, DATA)}
        cls.temp = TemporaryDirectory(prefix="bmb-v050-tests-private-dev-")
        cls.states = {}
        cls.controls = {}
        cls.sessions = {}
        for i, tid in enumerate(TASKS):
            task = cls.tasks[tid]
            source = DATA / "ifc" / task["original_source_ifc_relpath"]
            sha = task["original_ifc_sha256"]
            snap = project_original_declarative_state_v050(source, source_sha=sha)
            internal = project_original_native_mutations_v045(source, source_sha=sha).xml
            cls.states[tid] = {"source": source, "sha": sha, "xml": snap.xml}
            for control in ("positive", "negative"):
                developer = (positive_developer_source_edit(
                    internal, source, tid, task["public_question"]
                ) if control == "positive" else
                    make_illustrative_plan(internal, tid, source))
                edit = audit.developer_control_to_declarative_state(snap.xml, developer)
                cls.controls[(tid, control)] = edit
            session = DirectOriginalStateSession050(
                source, Path(cls.temp.name) / f"valid_{i}"
            )
            result = session.call("submit_building_xml", {
                "xml_text": cls.controls[(tid, "positive")].decode("utf8"),
            })
            if result["status"] != "ok":
                raise AssertionError(f"positive source-native IFC failure {tid}: {result}")
            cls.sessions[tid] = session

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp_case = TemporaryDirectory(prefix="bmb-v050-negative-")
        self.addCleanup(self.temp_case.cleanup)
        self.root = Path(self.temp_case.name)

    def _root(self, tid="geometry_test_14", control="positive"):
        return etree.fromstring(self.controls[(tid, control)])

    def _submit_poison(self, mutate, tid="geometry_test_14", control="positive"):
        root = self._root(tid, control)
        mutate(root)
        payload = etree.tostring(root, xml_declaration=True, encoding="utf8")
        source = self.states[tid]
        with self.assertRaises((DeclarativeState050Error, ValueError, etree.XMLSyntaxError)):
            parse_original_declarative_state_diff_v050(
                source["source"], payload, source_sha=source["sha"],
            )
        self.assertEqual(file_hash(source["source"]), source["sha"])

    def test_01_existing_prior_report_frozen_hash_unchanged(self):
        self.assertEqual(file_hash(audit.REPORT), FROZEN_SHA)
        for name, expected in audit.FROZEN_PRIOR.values():
            self.assertEqual(file_hash(audit.ROOT / "reports" / name), expected)

    def test_02_d_state_model_facing_source_never_contains_commands(self):
        for tid in TASKS:
            x = self.states[tid]["xml"]
            self.assertNotIn(b"NativeEditPlan", x)
            self.assertNotIn(b"<Set", x)
            self.assertNotIn(b"<Move", x)
            self.assertNotIn(b"<DeleteColumn", x)
            self.assertNotIn(b"<Execute", x)
            self.assertNotIn(b"<Create", x)
            self.assertEqual(etree.fromstring(x).tag, Q + "BuildingState")
            self.assertTrue(_xsd().validate(etree.fromstring(x)))

    def test_03_explicit_managed_overlay_not_source_free_BIM(self):
        expected = {"geometry_test_14": 1, "geometry_test_15": 4,
                    "topological_test_11": 2, "topological_test_17": 10}
        for tid in TASKS:
            state = etree.fromstring(self.states[tid]["xml"])
            self.assertEqual(len(state), 2)
            self.assertEqual(state[0].tag, Q + "OriginalNativeIFCSource")
            self.assertEqual(state[1].tag, Q + "ManagedElements")
            self.assertEqual(len(state[1]), expected[tid])
            self.assertEqual(state.get("sourceOriginalIFCSha256"),
                             self.states[tid]["sha"])

    def test_04_both_physical_controls_are_real_source_state_diffs(self):
        for tid in TASKS:
            for control in ("positive", "negative"):
                d = parse_original_declarative_state_diff_v050(
                    self.states[tid]["source"], self.controls[(tid, control)],
                    source_sha=self.states[tid]["sha"],
                )
                self.assertEqual(d.task_id, tid)
                self.assertGreaterEqual(len(d.changed_original_ids), 1)
                self.assertNotIn(b"NativeEditPlan", self.controls[(tid, control)])
                self.assertIn(b"NativeEditPlan", d.internal_native_writer_xml)

    def test_05_four_real_physical_native_declarative_positives(self):
        for tid in TASKS:
            source = self.states[tid]
            session = self.sessions[tid]
            self.assertTrue(session.output_ifc.is_file())
            self.assertEqual(file_hash(source["source"]), source["sha"])
            observed = evaluate_original_semantic048(
                source["source"], session.output_ifc,
                original_sha=source["sha"], task_id=tid,
                public_question=self.tasks[tid]["public_question"],
            )
            self.assertTrue(observed["candidatePassesIndependentResearchPhysicalPredicate"])

    def test_06_actual_read_returns_last_valid_whole_state(self):
        for tid in TASKS:
            session = self.sessions[tid]
            read = session.call("read_building_xml", {})
            self.assertEqual(read["status"], "ok")
            self.assertEqual(read["xml"].encode("utf8"),
                             self.controls[(tid, "positive")])
            self.assertEqual(read["current_xml_sha256"],
                             sha256(self.controls[(tid, "positive")]).hexdigest())

    def test_07_reject_noop_as_native_edit(self):
        for tid in TASKS:
            source = self.states[tid]
            with self.subTest(task=tid), self.assertRaises(DeclarativeState050Error):
                parse_original_declarative_state_diff_v050(
                    source["source"], source["xml"], source_sha=source["sha"],
                )

    def test_08_reject_edited_immutable_original_STEP(self):
        def poison(root):
            entity = root[0].find(".//" + Q + "StepEntity")
            self.assertIsNotNone(entity)
            entity.text += "FORGED"
        self._submit_poison(poison)

    def test_09_reject_edited_original_source_geometry(self):
        def poison(root):
            geom = root[0].find(".//" + Q + "ProductGeometry")
            geom.set("worldMeshSha256", "0" * 64)
        self._submit_poison(poison)

    def test_10_reject_source_identity_and_root_permission_spoof(self):
        self._submit_poison(lambda r: r.set("sourceOriginalIFCSha256", "0" * 64))
        self._submit_poison(lambda r: r.set("managedSemantics", "UNBOUNDED"))
        self._submit_poison(lambda r: r[1].set("boundary", "EVERYTHING"))

    def test_11_reject_opcode_wrapped_as_XML(self):
        self._submit_poison(lambda r: etree.SubElement(r[1], Q + "MoveElement"))
        self._submit_poison(lambda r: etree.SubElement(r[1], Q + "NativeEditPlan"))

    def test_12_reject_new_or_duplicate_managed_guids(self):
        def add_unknown(root):
            etree.SubElement(root[1], Q + "Column", {
                "ifcGuid": "1234567890123456789012",
            })
        self._submit_poison(add_unknown, tid="topological_test_17")
        self._submit_poison(lambda r: r[1].append(copy.deepcopy(r[1][0])),
                            tid="topological_test_17")

    def test_13_reject_renamed_existing_identity(self):
        self._submit_poison(lambda r: r[1][0].set("ifcGuid", "1234567890123456789012"),
                            tid="topological_test_17")

    def test_14_reject_edited_node_extra_fields_or_class_change(self):
        self._submit_poison(lambda r: r[1][0].set("newDepthM", "4.000000"))
        self._submit_poison(lambda r: r[1][0].set("extrusionDepthM", "5.000000"),
                            tid="geometry_test_15")
        self._submit_poison(lambda r: setattr(r[1][0], "tag", Q + "Wall"))

    def test_15_reject_malicious_external_entity_payload(self):
        source = self.states["geometry_test_14"]
        evil = (b'<?xml version="1.0"?>'
                b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>'
                + source["xml"].split(b"?>", 1)[1])
        with self.assertRaises((ValueError, etree.XMLSyntaxError)):
            parse_original_declarative_state_diff_v050(
                source["source"], evil, source_sha=source["sha"],
            )

    def test_16_reject_unbounded_or_nonfinite_state_numbers(self):
        self._submit_poison(lambda r: r[1][0].set("dimXM", "NaN"))
        self._submit_poison(lambda r: r[1][0].set("dimXM", "1e9999"))
        self._submit_poison(lambda r: r[1][0].set("dimXM", "0.000000"))
        self._submit_poison(lambda r: r[1][0].set("dimXM", "-1.000000"))

    def test_17_reject_slab_second_field_decrease_or_second_change(self):
        self._submit_poison(lambda r: r[1][0].set("dimXM", "8.000000"))
        self._submit_poison(lambda r: r[1][0].set("dimYM", "11.000000"))
        self._submit_poison(lambda r: r[1][0].set("dimXM", "2.000000"))

    def test_18_reject_two_column_moves_instead_of_one(self):
        def poison(root):
            root[1][0].set("worldXM", "5.000000")
            root[1][1].set("worldXM", "6.000000")
        self._submit_poison(poison, tid="geometry_test_15")

    def test_19_reject_one_of_two_shared_depths_unchanged(self):
        def poison(root):
            root[1][0].set("extrusionDepthM", "1.500000")
        self._submit_poison(poison, tid="topological_test_11")

    def test_20_reject_inconsistent_original_shared_depths(self):
        def poison(root):
            root[1][0].set("extrusionDepthM", "2.000000")
            root[1][1].set("extrusionDepthM", "2.500000")
        self._submit_poison(poison, tid="topological_test_11")

    def test_21_reject_delete_none_all_or_reorder(self):
        self._submit_poison(lambda r: r[1].clear(),
                            tid="topological_test_17")
        def no_delete(root):
            root[1].clear()
            snap = etree.fromstring(self.states["topological_test_17"]["xml"])
            for node in snap[1]:
                root[1].append(copy.deepcopy(node))
        self._submit_poison(no_delete, tid="topological_test_17")
        def reversed_order(root):
            nodes = list(root[1])
            root[1][:] = list(reversed(nodes))
        self._submit_poison(reversed_order, tid="topological_test_17")

    def test_22_reject_tamper_source_hash_after_host_creation(self):
        source = self.states["geometry_test_14"]["source"]
        copied = self.root / "source.ifc"
        shutil.copyfile(source, copied)
        session = DirectOriginalStateSession050(copied, self.root / "isolated")
        copied.write_bytes(copied.read_bytes() + b"\n")
        result = session.call("read_building_xml", {})
        self.assertEqual(result["error_type"], "OriginalSourceChanged")
        self.assertIsNone(session.output_ifc)

    def test_23_tool_budgets_include_every_call(self):
        source = self.states["geometry_test_14"]["source"]
        session = DirectOriginalStateSession050(source, self.root / "budget")
        for _ in range(MAX_CALLS):
            self.assertEqual(session.call("read_building_xml", {})["status"], "ok")
        self.assertEqual(session.call("read_building_xml", {})["error_type"],
                         "ToolBudgetExhausted")
        self.assertIsNone(session.output_ifc)

    def test_24_existing_valid_ifc_and_state_survive_failed_submission(self):
        session = self.sessions["geometry_test_14"]
        prior_xml = session.current_xml
        prior_ifc = session.output_ifc
        prior_hash = file_hash(prior_ifc)
        bad = prior_xml.replace(b"<ManagedElements", b"<NativeEditPlan", 1)
        result = session.call("submit_building_xml", {
            "xml_text": bad.decode("utf8"),
        })
        self.assertEqual(result["status"], "error")
        self.assertTrue(result["last_valid_xml_preserved"])
        self.assertIs(session.output_ifc, prior_ifc)
        self.assertEqual(file_hash(prior_ifc), prior_hash)
        self.assertEqual(session.current_xml, prior_xml)

    def test_25_tool_surface_contains_exact_two_state_tools_not_commands(self):
        session = self.sessions["geometry_test_14"]
        self.assertEqual([t["name"] for t in session.tools],
                         ["read_building_xml", "submit_building_xml"])
        self.assertNotIn("NativeEditPlan", str(session.tools))
        self.assertNotIn("submit_native_python", str(session.tools))
        self.assertNotIn("IfcOpenShell", str(session.tools))

    def test_26_no_original_author_benchmark_score_or_model_pair_claim(self):
        report = json.loads(audit.REPORT.read_text(encoding="utf8"))
        self.assertEqual(report["real_native_original_mm_IFC_generated"], 8)
        self.assertEqual(report["real_D_state_vs_typed_legacy_native_candidate_byte_equal"], 8)
        self.assertEqual(report["positive_developer_research_physical_semantic_controls"], 4)
        self.assertEqual(report["negative_developer_research_physical_semantic_controls"], 4)
        self.assertEqual(report["matched_D_state_vs_unrestricted_Python_IFC_model_trials"], 0)
        self.assertIsNone(report["original_author_benchmark_scores"])
        self.assertIsNone(report["causal_D_state_vs_I_native_result"])

    def test_27_audit_full_native_original_sources_replay_exact_bytes(self):
        self.assertEqual(audit.canonical(audit.build_report()),
                         audit.REPORT.read_bytes())

    def test_28_frozen_report_never_overwritten_by_write_gate(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb") as _:
                pass


if __name__ == "__main__":
    unittest.main()
