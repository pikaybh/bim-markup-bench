import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.data.bim_edit import agent_view
from src.security.agent_boundary import (
    FileAccessPolicy, LicenseRecord, SecurityBoundaryError, validate_agent_payload,
)

ROOT=Path(__file__).resolve().parents[2]
RAW={
    "task_id":"TEST-NO-ANSWER",
    "prompt":"Make the wall taller.",
    "input_ifc":"data/artificial/private_input.ifc",
    "ground_truth_ifc":"data/artificial/private_gt.ifc",
    "target":{"entity_type":"IfcWall","guids":["0"*22]},
    "evaluation":{"expected":{"answer":"secret"}},
}
class AnswerIsolationTests(unittest.TestCase):
    def test_agent_projection_strips_ground_truth(self):
        safe=validate_agent_payload(agent_view(RAW),schema_path=ROOT/"schemas/agent_input.schema.json")
        self.assertEqual(safe["input_file"],"input.ifc")
        out=json.dumps(safe)
        for forbidden in ("ground_truth_ifc","private_gt","target","evaluation","secret","private_input"):
            self.assertNotIn(forbidden,out)

    def test_extra_answer_fields_fail(self):
        for field in ("target","ground_truth_ifc","evaluation","secrets","expected_output"):
            p=agent_view(RAW)
            p[field]="grade secret"
            with self.subTest(field=field), self.assertRaises(SecurityBoundaryError):
                validate_agent_payload(p)

    def test_path_secret_telltales_blocked(self):
        for injected in ("sk-SHOULDNOTBEVISIBLEX", "OPENAI_API_KEY=secret", "../grader/private", "/grader/gt.ifc"):
            p=agent_view(RAW)
            p["instruction"]=injected
            with self.subTest(injected=injected),self.assertRaises(SecurityBoundaryError):
                validate_agent_payload(p)

class FilePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        for f in ("building.xml","input.ifc","language_spec.md"):
            (self.path/f).write_text("fixture")
        self.policy=FileAccessPolicy(self.path)

    def test_only_xml_edit_allowed(self):
        self.assertEqual(self.policy.check("edit_xml","building.xml"),self.path.resolve()/"building.xml")
        self.assertEqual(self.policy.check("read","input.ifc"),self.path.resolve()/"input.ifc")
        for f in ("input.ifc","language_spec.md","../grader/gt.ifc","/etc/passwd",".env","evaluator.py","ground_truth.ifc"):
            with self.subTest(f=f),self.assertRaises(SecurityBoundaryError):
                self.policy.check("edit_xml",f)
        for a in ("execute_python","network","subprocess","run_shell","upload","read_gt"):
            with self.subTest(action=a),self.assertRaises(SecurityBoundaryError):
                self.policy.check(a,"building.xml")

    def test_symlink_escape_fails(self):
        (self.path.resolve()/"input.ifc").unlink()
        (self.path.resolve()/"input.ifc").symlink_to("/etc/hosts")
        with self.assertRaisesRegex(SecurityBoundaryError,"symlink"):
            self.policy.check("read","input.ifc")

    def test_network_shell_denial(self):
        with self.assertRaises(SecurityBoundaryError):
            self.policy.deny_network("https://example.com/gt")
        with self.assertRaises(SecurityBoundaryError):
            self.policy.deny_shell("cat .env")

class LicenseLedgerTests(unittest.TestCase):
    def test_unknown_rights_refused(self):
        digest=hashlib.sha256(b"test").hexdigest()
        for kw in [
            dict(rights_checked=False,redistribution_permitted=True,consent_documented=True),
            dict(rights_checked=True,redistribution_permitted=False,consent_documented=True),
            dict(rights_checked=True,redistribution_permitted=True,consent_documented=False),
            dict(rights_checked=True,redistribution_permitted=True,consent_documented=True,asset_rights="UNKNOWN"),
        ]:
            with self.subTest(kw=kw),self.assertRaises(SecurityBoundaryError):
                LicenseRecord(source="synthetic",source_digest_sha256=digest,
                    asset_rights=kw.get("asset_rights","CC-BY-4.0"),
                    rights_checked=kw["rights_checked"],
                    redistribution_permitted=kw["redistribution_permitted"],
                    consent_documented=kw["consent_documented"]).authorize_redistribution()

    def test_explicit_original_fixture_permission(self):
        LicenseRecord(source="self-generated",source_digest_sha256="f"*64,
            asset_rights="Author-created",rights_checked=True,
            redistribution_permitted=True,consent_documented=True).authorize_redistribution()

if __name__=="__main__":
    unittest.main()

class XMLPreflightSecurityTests(unittest.TestCase):
    def test_dtd_xxe_bomb_and_oversized_denied(self):
        from src.security.agent_boundary import check_xml_bytes
        for payload in [
            b'<!DOCTYPE r [<!ENTITY xx SYSTEM "file:///etc/passwd">]><r>&xx;</r>',
            b'<!ENTITY x "billion laughs">',
            b'<![IGNORE[something]]>',
            b"<r>" + b"x"*(2*1024*1024) + b"</r>",
            b"",
        ]:
            with self.subTest(length=len(payload)),self.assertRaises(SecurityBoundaryError):
                check_xml_bytes(payload)
        check_xml_bytes(b'<Building><Wall id="w1"/></Building>')
