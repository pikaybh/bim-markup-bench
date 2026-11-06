import copy
from pathlib import Path
import shutil
import subprocess
import unittest

from src.runtime.markup_normal_form import canonical_semantic_xml, semantic_digest
from src.security.agent_boundary import SecurityBoundaryError

ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/"spec/toy_markup_v0.xsd"
VALID=ROOT/"examples/valid/basic_building.xml"
INVALID=ROOT/"examples/invalid"

class MarkupSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xmllint=shutil.which("xmllint")
        if not cls.xmllint:
            raise unittest.SkipTest("xmllint not installed; XML Schema structure check unavailable")

    def run_schema(self,path):
        return subprocess.run([self.xmllint,"--nonet","--noout","--schema",str(SCHEMA),str(path)],
            capture_output=True,text=True,timeout=7)

    def test_valid_building_schema(self):
        self.assertEqual(self.run_schema(VALID).returncode,0)

    def test_invalid_structural_and_semantic_references(self):
        for p in sorted(INVALID.glob("*.xml")):
            with self.subTest(file=p.name):
                res=self.run_schema(p)
                self.assertNotEqual(res.returncode,0,p.name+": "+res.stderr)

    def test_schema_restricts_namespace_and_commands(self):
        s=SCHEMA.read_text()
        self.assertIn('urn:bim-markup-bench:toy:v0',s)
        self.assertIn('name="openingHostReferences"',s)
        self.assertNotIn('name="Create"',s)
        self.assertNotIn('name="Update"',s)
        self.assertNotIn('name="Delete"',s)

class SemanticSourceFingerprintTests(unittest.TestCase):
    def test_whitespace_attribute_order_comments_are_not_semantic(self):
        src=VALID.read_bytes()
        changed=src.replace(b'height="3" thickness="0.2"',b'thickness="0.2" height="3"')
        changed=changed.replace(b'<Elements>',b'<Elements>\n    <!-- A harmless user comment -->\n')
        self.assertEqual(semantic_digest(src),semantic_digest(changed))

    def test_object_order_unimportant_and_geometry_changes_meaningful(self):
        src=VALID.read_bytes()
        doc=src.decode()
        start=doc.index('    <Slab')
        end=doc.index('    <Column')
        slab=doc[start:end]
        shuffled=doc[:start]+doc[end:].replace('    <Column',slab+'    <Column',1)
        self.assertEqual(semantic_digest(src),semantic_digest(shuffled.encode()))
        changed=src.replace(b'thickness="0.2"',b'thickness="0.3"')
        self.assertNotEqual(semantic_digest(src),semantic_digest(changed))

    def test_preflight_rejects_dtd(self):
        with self.assertRaises(SecurityBoundaryError):
            canonical_semantic_xml(b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><Building/>')

    def test_wrong_namespace_refused(self):
        with self.assertRaises(ValueError):
            canonical_semantic_xml(b'<Building/>')

if __name__=="__main__": unittest.main()
