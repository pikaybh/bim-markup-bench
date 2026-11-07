"""True safe parser, AST, source location and declarative XML-only diff tests."""
from __future__ import annotations
import copy
from decimal import Decimal
import json
from pathlib import Path
import unittest

import jsonschema
from src.runtime.ast import semantic_diff
from src.runtime.xml_parser import MarkupParseError, parse_xml, try_parse_update

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"examples/valid/basic_building.xml").read_bytes()
ZERO_DIGEST="0"*64

class ParserPositiveTests(unittest.TestCase):
    def test_typed_ast_and_source_file(self):
        doc=parse_xml(SOURCE,filename="/Users/example/secret/building.xml",
                       expected_source_sha256=ZERO_DIGEST)
        self.assertEqual(doc.source_filename,"building.xml")
        self.assertEqual(doc.source_bytes,SOURCE)
        self.assertEqual(doc.units,"m")
        self.assertEqual(doc.ifc_schema,"IFC4X3")
        self.assertEqual(len(doc.levels),1)
        self.assertEqual(len(doc.elements),8)
        self.assertEqual(len(doc.relations),1)
        wall=doc.managed_by_id()["north_wall"]
        self.assertEqual(wall.kind,"Wall")
        self.assertEqual(wall.attrs()["height"],Decimal("3"))
        self.assertEqual(wall.attrs()["thickness"],Decimal("0.2"))
        self.assertEqual(wall.span.line,9)
        self.assertGreater(wall.span.column,0)
        self.assertTrue(SOURCE[wall.span.start_byte:wall.span.start_tag_end_byte].startswith(b"<Wall "))
        self.assertEqual(wall.span.file,"building.xml")
        self.assertEqual(wall.id,"north_wall")

    def test_input_bytes_immutable_and_comments_retained(self):
        src=SOURCE.replace(b"<Elements>",b"<Elements>\n  <!-- USER MARKUP COMMENT -->")
        old=bytes(src)
        doc=parse_xml(src)
        self.assertEqual(doc.source_bytes,old)
        self.assertIn(b"USER MARKUP COMMENT",doc.source_bytes)
        self.assertEqual(len(doc.elements),8)

    def test_context_source_hash_mismatch_rejected(self):
        with self.assertRaises(MarkupParseError) as e:
            parse_xml(SOURCE,expected_source_sha256="1"*64)
        self.assertEqual(e.exception.diagnostic["code"],"XML_SOURCE_HASH")
        self.assertNotIn("1"*64,e.exception.diagnostic["message"])

    def test_different_whitespace_same_digest(self):
        src=SOURCE.replace(b'height="3" thickness="0.2"',b'thickness="0.2" height="3"')
        self.assertEqual(parse_xml(SOURCE).semantic_sha256,parse_xml(src).semantic_sha256)

    def test_equal_decimal_values_have_equal_digest_and_no_delta(self):
        before=parse_xml(SOURCE)
        after=parse_xml(SOURCE.replace(b'thickness="0.2"', b'thickness="0.20"'))
        delta=semantic_diff(before,after)
        self.assertEqual(delta.effect,"NO_OP")
        self.assertEqual(before.semantic_sha256,after.semantic_sha256)

    def test_multibyte_comment_preserves_character_column_and_byte_span(self):
        changed=SOURCE.replace(b'<Elements>', '<Elements>건설 <!-- Korean comment -->'.encode("utf-8"))
        with self.assertRaises(MarkupParseError):
            # Non-whitespace free text is rejected by the closed schema.
            parse_xml(changed)
        changed=SOURCE.replace(b'<Elements>', '<Elements><!-- 건설 -->'.encode("utf-8"))
        doc=parse_xml(changed)
        self.assertEqual(len(doc.elements),8)
        wall=doc.elements[0]
        self.assertTrue(changed[wall.span.start_byte:wall.span.start_tag_end_byte].startswith(b"<Wall "))

    def test_invalid_xml_cannot_leak_identifier_secret(self):
        data=SOURCE.replace(b'id="north_wall"',b'id="sk-verysecretstring123456"')
        with self.assertRaises(MarkupParseError) as context:
            parse_xml(data)
        msg=json.dumps(context.exception.diagnostic)
        self.assertNotIn("sk-verysecretstring123456",msg)

    def test_safe_diagnostic_schema_and_source_position(self):
        invalid=(ROOT/"examples/invalid/negative_dimension.xml").read_bytes()
        try:
            parse_xml(invalid,filename="/secret/private/negative_dimension.xml")
        except MarkupParseError as exc:
            d=exc.diagnostic
            schema=json.loads((ROOT/"schemas/diagnostic.schema.json").read_text())
            jsonschema.validate(d,schema)
            self.assertEqual(d["code"],"XML_SCHEMA")
            self.assertEqual(d["file"],"negative_dimension.xml")
            self.assertEqual(d["line"],5)
            self.assertGreater(d["column"],0)
            self.assertEqual(d["element_id"],"w1")
            self.assertNotIn("/secret/private",json.dumps(d))
        else:
            self.fail("Negative thickness unexpectedly parsed")

class ParserNegativeTests(unittest.TestCase):
    def test_invalid_examples_fail(self):
        for p in sorted((ROOT/"examples/invalid").glob("*.xml")):
            with self.subTest(filename=p.name),self.assertRaises(MarkupParseError):
                parse_xml(p.read_bytes(),filename=p.name)

    def test_dtd_and_external_entity_fail_closed(self):
        malicious=b'<!DOCTYPE Building [<!ENTITY x SYSTEM "file:///etc/passwd">]><Building>&x;</Building>'
        with self.assertRaises(MarkupParseError) as e:
            parse_xml(malicious)
        self.assertEqual(e.exception.diagnostic["code"],"XML_SECURITY_OR_SYNTAX")

    def test_oversized_or_too_deep_fail(self):
        for data in (
            b'<Building>' + b"x"*(2*1024*1024) + b'</Building>',
            b"<A>"*100 + b"</A>"*100,
            b'<Building a="1" ' + b" ".join((f'attr{i}="x"').encode() for i in range(40)) + b'/>',
        ):
            with self.subTest(length=len(data)),self.assertRaises(MarkupParseError):
                parse_xml(data)

    def test_unknown_include_and_renamed_tags_fail(self):
        for invalid in (
            SOURCE.replace(b"<Elements>",b'<Elements><Include href="file:///etc/passwd"/>'),
            SOURCE.replace(b'<Wall id="north_wall"',b'<RunCommand id="north_wall"'),
        ):
            with self.assertRaises(MarkupParseError):
                parse_xml(invalid)

    def test_partial_edit_does_not_replace_last_valid_document(self):
        valid=parse_xml(SOURCE)
        outcome=try_parse_update(valid,b'<Building><Wall id="partial"')
        self.assertFalse(outcome.accepted)
        self.assertIs(outcome.committed,valid)
        self.assertEqual(len(outcome.diagnostics),1)
        self.assertIn("code",outcome.diagnostics[0])

    def test_valid_updated_state_commits(self):
        original=parse_xml(SOURCE)
        updated=try_parse_update(original,SOURCE.replace(b'thickness="0.2"',b'thickness="0.3"'))
        self.assertTrue(updated.accepted)
        self.assertIsNot(updated.committed,original)
        self.assertNotEqual(updated.committed.semantic_sha256,original.semantic_sha256)

class DeclarativeDiffTests(unittest.TestCase):
    def test_edit_wall_thickness_and_new_wall(self):
        before=parse_xml(SOURCE)
        modified=SOURCE.replace(b'thickness="0.2"',b'thickness="0.3"')
        after=parse_xml(modified)
        delta=semantic_diff(before,after)
        self.assertEqual(delta.modified,("north_wall",))
        self.assertEqual(delta.created,())
        self.assertEqual(delta.deleted,())
        self.assertFalse(delta.as_dict()["ifc_mutated"])
        self.assertEqual(delta.effect,"DECLARATIVE_STATE_DIFF")

    def test_create_delete_without_any_command_opcode(self):
        before=parse_xml(SOURCE)
        new_wall=(b'<Wall id="new_wall" level="level_1" x1="0" y1="4" z1="0" '
                  b'x2="6" y2="4" z2="0" height="3" thickness="0.2"/>')
        augmented=SOURCE.replace(b"<Elements>",b"<Elements>\n   "+new_wall)
        after=parse_xml(augmented)
        delta=semantic_diff(before,after)
        self.assertIn("new_wall",delta.created)
        self.assertEqual(delta.deleted,())
        self.assertNotIn(b"<Create",augmented)
        reverted=semantic_diff(after,before)
        self.assertEqual(reverted.deleted,("new_wall",))

    def test_relationship_removed_is_structural_change(self):
        before=parse_xml(SOURCE)
        removed=SOURCE.replace(b'    <SpaceBoundary space="room_101" element="north_wall" kind="PHYSICAL"/>',b'')
        after=parse_xml(removed)
        delta=semantic_diff(before,after)
        self.assertEqual(len(delta.relations_removed),1)
        self.assertEqual(delta.created,())
        self.assertEqual(delta.deleted,())
        self.assertEqual(delta.effect,"DECLARATIVE_STATE_DIFF")

    def test_no_op_preserves_semantic_hash(self):
        before=parse_xml(SOURCE)
        changed=SOURCE.replace(b'height="3" thickness="0.2"',b'thickness="0.2" height="3"')
        after=parse_xml(changed)
        delta=semantic_diff(before,after)
        self.assertEqual(delta.effect,"NO_OP")
        self.assertEqual(delta.old_semantic_sha256,delta.new_semantic_sha256)

    def test_existing_guid_and_source_hash_immutable(self):
        before=parse_xml(SOURCE)
        new=parse_xml(SOURCE.replace(b'sourceModelSha256="'+ZERO_DIGEST.encode()+b'"',
                                      b'sourceModelSha256="'+b'1'*64+b'"'))
        with self.assertRaisesRegex(ValueError,"Source IFC hash"):
            semantic_diff(before,new)
        old_with_guid=SOURCE.replace(b'<Wall id="north_wall"',
                                      b'<Wall id="north_wall" ifcGuid="'+b'0'*22+b'"')
        new_with_guid=SOURCE.replace(b'<Wall id="north_wall"',
                                      b'<Wall id="north_wall" ifcGuid="'+b'1'*22+b'"')
        with self.assertRaisesRegex(ValueError,"GlobalId"):
            semantic_diff(parse_xml(old_with_guid),parse_xml(new_with_guid))

    def test_duplicate_ref_invalid_before_diff(self):
        bad=SOURCE.replace(b'host="north_wall"',b'host="not_a_wall"')
        with self.assertRaises(MarkupParseError):
            parse_xml(bad)

if __name__=="__main__":unittest.main()

class ValidatorCliTests(unittest.TestCase):
    def test_cli_accepts_valid_rejects_invalid_without_writing_ifc(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp)
            good=temp/"good.xml"
            bad=temp/"bad.xml"
            good.write_bytes(SOURCE)
            bad.write_bytes((ROOT/"examples/invalid/negative_dimension.xml").read_bytes())
            calls=[]
            for source in (good,bad):
                run=subprocess.run([sys.executable,"-m","tools.validate_markup",str(source)],
                                   cwd=ROOT,timeout=15,text=True,capture_output=True)
                calls.append((run,json.loads(run.stdout)))
            self.assertEqual(calls[0][0].returncode,0,calls[0][0].stderr)
            self.assertEqual(calls[0][1]["status"],"VALID_DECLARATIVE_XML_ONLY")
            self.assertFalse(calls[0][1]["output_ifc_written"])
            self.assertEqual(calls[1][0].returncode,2,calls[1][0].stderr)
            self.assertEqual(calls[1][1]["status"],"INVALID")
            self.assertEqual(list(temp.glob("*.ifc")),[])
            self.assertEqual(good.read_bytes(),SOURCE)

    def test_cli_refuses_wrong_ifc_hash(self):
        import subprocess
        import sys
        run=subprocess.run([sys.executable,"-m","tools.validate_markup",
                            "examples/valid/basic_building.xml",
                            "--expected-source-sha256","1"*64],
                           cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,2)
        self.assertEqual(json.loads(run.stdout)["diagnostic"]["code"],"XML_SOURCE_HASH")
