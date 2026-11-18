"""Issue #247: stable semantic IFC state versus arbitrary numeric STEP labels.

Synthetic lexer negatives need NO real IFC; two native positive controls
are already-developer-exposed originals only, never unseen source or grader.
"""
from __future__ import annotations

from hashlib import sha256
import json
from unittest import TestCase, main

from tools import audit_bibimbap_v066_step_identity_fairness as a


EXAMPLE = (b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n"
           b"#1=FOO('in-quote #2 and escaped ''#1''',#2);/* comment #1 */\n"
           b"#2=BAR();\nENDSEC;\nEND-ISO-10303-21;\n")
SHA = "90e4a99c0dda3d551de0a59abdf66cba5beb42fc10e0f471337488060c358253"


class NativeIFCStepIdentityFairness066(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(a.OUTPUT.read_text("utf8"))

    def test_01_canonical_frozen_report_bytes(self):
        self.assertEqual(a.OUTPUT.read_bytes(), a.canonical(self.report))

    def test_02_frozen_report_sha(self):
        self.assertEqual(sha256(a.OUTPUT.read_bytes()).hexdigest(), SHA)

    def test_03_reindex_bijection_roundtrip_with_opaque_literals_and_comments(self):
        new, mapping = a.relabel_spf(EXAMPLE)
        self.assertEqual(mapping, {1: 2, 2: 1})
        self.assertIn(b"'in-quote #2 and escaped ''#1'''", new)
        self.assertIn(b"/* comment #1 */", new)
        self.assertIn(b"#2=FOO(", new)
        self.assertIn(b"#1=BAR();", new)
        restored, _, _ = a.scan_spf(new, {v: k for k, v in mapping.items()})
        self.assertEqual(restored, EXAMPLE)

    def test_04_reject_duplicate_entity_ids(self):
        bad = EXAMPLE.replace(b"#2=BAR();", b"#1=BAR();")
        with self.assertRaises(a.RelabelError):
            a.relabel_spf(bad)

    def test_05_reject_unknown_referenced_entity(self):
        bad = EXAMPLE.replace(b"FOO('in-quote #2 and escaped ''#1''',#2)",
                              b"FOO('in-quote #2 and escaped ''#1''',#999)")
        with self.assertRaises(a.RelabelError):
            a.relabel_spf(bad)

    def test_06_reject_unterminated_comment_or_literal(self):
        with self.assertRaises(a.RelabelError):
            a.scan_spf(EXAMPLE + b"/* never ends")
        with self.assertRaises(a.RelabelError):
            a.scan_spf(EXAMPLE + b"'never ends")

    def test_07_reject_nonbijective_mapping(self):
        with self.assertRaises(a.RelabelError):
            a.scan_spf(EXAMPLE, {1: 1, 2: 1})
        with self.assertRaises(a.RelabelError):
            a.scan_spf(EXAMPLE, {1: 1})

    def test_08_two_real_previously_exposed_native_schemas(self):
        self.assertEqual(self.report["real_native_alternative_encoding_cases"], 2)
        self.assertEqual(self.report["two_IFC_schemas"], ["IFC2X3", "IFC4X3"])
        self.assertEqual({x["same_native_IFC_after_one_to_one_STEP_ID_only_relabel"][
            "native_schema_identifier"] for x in self.report["cases"]},
            {"IFC2X3", "IFC4X3"})

    def test_09_real_ifc_geometry_schema_and_root_class_preserved(self):
        cases = self.report["cases"]
        self.assertEqual([x["same_native_IFC_after_one_to_one_STEP_ID_only_relabel"][
            "native_geometry_products_physically_equal"] for x in cases], [5, 11])
        self.assertEqual([x["same_native_IFC_after_one_to_one_STEP_ID_only_relabel"][
            "native_root_STEP_IDs_reassigned"] for x in cases], [57, 121])
        self.assertTrue(all(x["same_native_IFC_after_one_to_one_STEP_ID_only_relabel"][
            "native_IFC_schema_error_delta"] == 0 for x in cases))
        self.assertTrue(all(x["same_native_IFC_after_one_to_one_STEP_ID_only_relabel"][
            "source_semantic_payload_inverse_byte_identical"] for x in cases))

    def test_10_existing_native_gate_false_rejection_is_exact_step_reason(self):
        self.assertEqual(self.report["strict_gate_false_rejections_due_to_STEP_number_only"], 2)
        self.assertTrue(all(x["v065_strict_original_D_full_gate_passed"] for x in self.report["cases"]))
        self.assertTrue(all(x["v065_strict_gate_rejects_legal_reencoding"] for x in self.report["cases"]))
        self.assertTrue(all("ALL ORIGINAL native STEP IDs" in x["v065_rejection_reason"]
                            for x in self.report["cases"]))

    def test_11_no_provider_or_new_source_and_no_author_score(self):
        self.assertTrue(self.report["no_original_author_scorer_or_GT_read"])
        self.assertTrue(self.report["no_model_paid_calls_or_provider_upload"])
        self.assertTrue(all(x["input_source_IFC_preserved_by_sha"] for x in self.report["cases"]))

    def test_12_strict_gate_not_replaced_or_unconditionally_weakened(self):
        self.assertIn("not arbitrary edit equivalence",
                      self.report["independent_validator_scope"])
        self.assertIn("Arbitrary Python IFC native edits that use different legal geometry representations",
                      self.report["not_yet_proven"])

    def test_13_regenerate_real_native_ifcs_matches_frozen_audit(self):
        self.assertEqual(a.canonical(a.build_report()), a.OUTPUT.read_bytes())


if __name__ == "__main__":
    main()
