"""Deterministic and fail-closed G0 #3 IFC rights/provenance checks."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from unittest import TestCase, mock

from src.data import pilot_ifc_rights as gate


def synthetic_step(hint: str = "") -> bytes:
    return (
        "ISO-10303-21;\nHEADER;\n"
        "FILE_DESCRIPTION(('source fixture'),'2;1');\n"
        "FILE_NAME('fixture.ifc','2026-11-10T00:00:00',('Author'),('Org'),"
        "'Generator','Exporter','');\n"
        "FILE_SCHEMA(('IFC4X3_ADD2'));\n"
        f"/* {hint} */\n"
        "ENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"
    ).encode("ascii")


class PilotProvenanceTests(TestCase):
    def test_header_without_license_hint_does_not_clear_rights(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "own.ifc"
            p.write_bytes(synthetic_step())
            record = gate.summarize_ifc_header(p)
        self.assertTrue(record["step_header_present"])
        self.assertFalse(record["copyright_or_license_text_hint"])
        self.assertFalse(record["explicit_model_rights_verified"])

    def test_header_with_license_hint_is_not_a_redistribution_grant(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "own.ifc"
            p.write_bytes(synthetic_step("CC BY 4.0 copyright"))
            record = gate.summarize_ifc_header(p)
        self.assertTrue(record["copyright_or_license_text_hint"])
        self.assertFalse(record["explicit_model_rights_verified"])

    def test_header_truncated_and_non_ifc_fails_closed(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "bad.ifc"
            p.write_bytes(b"ISO-10303-21;\nHEADER;\n" + b"A" * (gate.HEADER_LIMIT + 8))
            with self.assertRaises(gate.IFCProvenanceBlocked):
                gate.summarize_ifc_header(p)
            p.write_bytes(b"invalid bytes")
            with self.assertRaises(gate.IFCProvenanceBlocked):
                gate.summarize_ifc_header(p)

    def test_cannot_reclassify_existing_rights_ledger(self):
        with mock.patch.object(gate, "RIGHTS_LEDGER_SHA", "0" * 64):
            with self.assertRaisesRegex(gate.IFCProvenanceBlocked, "rights"):
                gate._load_frozen(gate.ROOT)

    def test_prior_audit_hash_change_fails_closed(self):
        with mock.patch.object(gate, "PRIOR_AUDIT_SHA", "0" * 64):
            with self.assertRaisesRegex(gate.IFCProvenanceBlocked, "prior"):
                gate._load_frozen(gate.ROOT)

    def test_actual_verified_source_reference_inventory_and_privacy(self):
        evidence = gate.audit_pilot_ifc_rights()
        self.assertEqual(evidence["tasks_total"], 36)
        self.assertEqual(evidence["status_counts"], {
            "BLOCKED_PAIRED_INPUT_REFERENCE_CONTENT_MISSING": 6,
            "VERIFIED_PINNED_BYTES_RIGHTS_UNRESOLVED": 30,
        })
        self.assertEqual(evidence["unique_remaining_file_count"], 10)
        self.assertEqual(evidence["unique_remaining_file_bytes"], 1476908702)
        self.assertEqual(evidence["unique_verified_file_count"], 42)
        self.assertEqual(evidence["unique_verified_file_bytes"], 87353128)
        self.assertFalse(evidence["model_redistribution_rights_cleared"])
        self.assertEqual(evidence["individual_model_license_documents_verified"], 0)
        self.assertEqual(evidence["official_tasks_scored"], 0)
        self.assertEqual(evidence["LLM_calls"], 0)
        text = json.dumps(evidence)
        for private_key in (
            "ground_truth_ifc", "input_ifc", "target_guid", "IfcGloballyUniqueId",
            "Author", "Org", "API_KEY",
        ):
            self.assertNotIn(private_key, text)
        self.assertEqual(len(evidence["tasks"]), 36)
        self.assertEqual(len({r["task_id"] for r in evidence["tasks"]}), 36)
