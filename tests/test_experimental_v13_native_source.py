"""Prospective original native IFC source-safe read-only v0.13 tests.

Real pinned original public IFC4X3 + IFC2X3 + IFC4. Exact source original
IfcRelVoids, IfcRelFills, Space/Beam meshes and rooted product identity
are independently verified. No compiler edit of opaque original source
objects, no hidden GT or provider calls.
"""
from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import json
import os
import tempfile
import time
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v13_opaque_source import (
    project_original_native_v13,project_original_ifc_v13,
    NativeReadV13Error,CATALOG_NS,
)
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.markup_normal_form import NS
from tools.oracle_bibimbap_v13_native_source import (
    IndependentV13SourceError,verify_v13_original_native_source,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
Q="{"+NS+"}"
R="{"+CATALOG_NS+"}"
SOURCES={
    "geom18":"01/01/01_01_018.ifc",
    "geom19":"01/01/01_01_019.ifc",
    "beam":"01/02/01_02_014.ifc",
    "space":"01/02/01_02_001.ifc",
    "basic":"basic_tasks.ifc",
    "ifc2x3door":"01/01/01_01_003.ifc",
    "ifc2x3space":"01/01/01_01_004.ifc",
    "ifc4empty":"empty.ifc",
}
BAD_18={"07NAHYposfcUjqlUhBJbQM"}
BAD_19={
    "0glQxPaBwI0t3x8bVYfCFb",
    "20UNRRDp_InaW8_dq7ad4F",
    "2uqjQk25XmTcRq6AABC8gG",
}
FILL_18={"1xzI3PuNvF1RRUjZb8YIV$"}
FILL_19={
    "1mRYVM4YfFFBRkcbz1hH$v",
    "1mRYVM4YfFFBRkcbz1hH_L",
    "1mRYVM4YfFFBRkcbz1hHpZ",
}


class V13ReadOnlySourceOriginal(unittest.TestCase):
    def source(self,key):
        path=DATA/SOURCES[key]
        if not path.is_file():
            self.skipTest("Original pinned public source IFC dataset not mounted")
        td=tempfile.TemporaryDirectory(prefix="bibi140-v013-real-")
        self.addCleanup(td.cleanup)
        source=Path(td.name)/"metre_normalized_source.ifc"
        original_sha=file_hash(path)
        self.addCleanup(lambda:self.assertEqual(file_hash(path),original_sha))
        f=ifcopenshell.open(str(path))
        ifcopenshell.util.unit.convert_file_length_units(
            f,"METER").write(str(source))
        source_sha=file_hash(source)
        self.addCleanup(lambda:self.assertEqual(file_hash(source),source_sha))
        return source,Path(td.name)

    def run_oracle(self,key):
        src,folder=self.source(key)
        result=project_original_native_v13(src)
        proof=verify_v13_original_native_source(
            src,result.projection.xml,result.source_catalog_xml)
        return src,folder,result,proof


class TestV13RealOriginalPositive(V13ReadOnlySourceOriginal):
    def test_failed_original_geometry18_read_repair_exact_one_opening_and_fill(self):
        src,folder,v,proof=self.run_oracle("geom18")
        self.assertEqual(set(v.demoted_opening_guids),BAD_18)
        self.assertEqual(set(v.demoted_fill_guids),FILL_18)
        self.assertEqual(set(
            proof["independently_original_native_hosted_out_of_extent_openings"]),BAD_18)
        self.assertEqual(set(
            proof["independently_source_original_linked_fills_protected"]),FILL_18)
        self.assertEqual(proof["original_native_products_all_cataloged"],59)
        self.assertEqual(proof["original_native_opaque_product_types"]["IfcWindow"],1)

    def test_failed_original_geometry19_read_repair_exact_three_openings_and_fills(self):
        src,folder,v,proof=self.run_oracle("geom19")
        self.assertEqual(set(v.demoted_opening_guids),BAD_19)
        self.assertEqual(set(v.demoted_fill_guids),FILL_19)
        self.assertEqual(set(
            proof["independently_original_native_hosted_out_of_extent_openings"]),BAD_19)
        self.assertEqual(set(
            proof["independently_source_original_linked_fills_protected"]),FILL_19)
        self.assertEqual(proof["original_native_products_all_cataloged"],26)
        self.assertEqual(proof["original_native_opaque_product_types"]["IfcWindow"],3)

    def test_no_original_host_wall_axis_or_opening_modified_or_clamped(self):
        for key in ("geom18","geom19"):
            with self.subTest(original=key):
                src,folder,v,proof=self.run_oracle(key)
                untouched=ifcopenshell.open(str(src))
                self.assertEqual(
                    proof["original_normalized_source_sha256"],file_hash(src))
                self.assertTrue(proof[
                    "native_source_IFC_root_and_geometry_identity_preserved"])
                for guid in v.demoted_opening_guids:
                    op=untouched.by_guid(guid)
                    self.assertTrue(op.is_a("IfcOpeningElement"))
                    self.assertEqual(len([
                        x for x in untouched.by_type("IfcRelVoidsElement")
                        if x.RelatedOpeningElement.GlobalId==guid
                    ]),1)

    def test_full_old_v09_source_xml_remains_unmodified_for_clean_source(self):
        src,folder=self.source("basic")
        old=project_ifc_v9(src)
        new=project_original_ifc_v13(src)
        self.assertEqual(old.xml,new.projection.xml)
        self.assertEqual(old.projected_global_ids,
                         new.projection.projected_global_ids)
        self.assertEqual(new.demoted_opening_guids,())
        self.assertEqual(new.demoted_fill_guids,())
        proof=verify_v13_original_native_source(
            src,new.projection.xml,new.source_catalog_xml)
        self.assertEqual(proof["original_native_products_all_cataloged"],43)

    def test_demotion_does_not_remove_any_other_typed_source_relationship(self):
        for key in ("geom18","geom19"):
            with self.subTest(original=key):
                src,folder=self.source(key)
                old=project_ifc_v9(src)
                v=project_original_native_v13(src)
                oldroot=etree.fromstring(old.xml)
                newroot=etree.fromstring(v.projection.xml)
                oldelts={x.get("ifcGuid"):x.tag for x in oldroot.find(Q+"Elements")}
                newelts={x.get("ifcGuid"):x.tag for x in newroot.find(Q+"Elements")}
                self.assertEqual(set(oldelts)-set(newelts),set(v.demoted_opening_guids)|set(v.demoted_fill_guids))
                self.assertEqual(set(newelts)-set(oldelts),set())
                self.assertEqual(newroot.find(Q+"Relations").attrib,
                                 oldroot.find(Q+"Relations").attrib)
                self.assertEqual(
                    etree.tostring(newroot.find(Q+"Relations")),
                    etree.tostring(oldroot.find(Q+"Relations")))

    def test_original_IFC4X3_safe_typed_source_still_has_full_strict_native_binder(self):
        for key in ("geom18","geom19","beam","space","basic"):
            with self.subTest(original=key):
                src,folder=self.source(key)
                v=project_original_native_v13(src)
                ast=parse_xml(v.projection.xml,
                              expected_source_sha256=v.native_source_sha256)
                bound=bind_document(ast,projection=v.projection)
                self.assertEqual(bound.missing_source_relation_edges,())
                self.assertTrue(bound.report()[
                    "all_ifc_relation_contracts_satisfied"])

    def test_beams_are_original_native_geometry_readonly_not_fake_xml(self):
        src,folder,v,proof=self.run_oracle("beam")
        root=etree.fromstring(v.source_catalog_xml)
        beams=[x for x in root.findall("./"+R+"Products/"+R+"Product")
               if x.get("ifcClass")=="IfcBeam"]
        self.assertEqual(len(beams),4)
        self.assertTrue(all(x.get("typedXmlRepresentation")=="NO_READONLY_NATIVE_SOURCE_ONLY"
                            for x in beams))
        self.assertTrue(all(x.get("compilerEditPermission")=="NONE_FROM_THIS_CATALOG"
                            for x in beams))
        self.assertTrue(all(x.find(R+"SourceWorldMesh").get("state")==
                            "ORIGINAL_NATIVE_TRIANGULATION_READONLY"
                            for x in beams))
        self.assertEqual(proof["original_native_opaque_product_types"]["IfcBeam"],4)

    def test_source_IfcSpace_native_geometry_and_aggregation_are_cataloged(self):
        src,folder,v,proof=self.run_oracle("space")
        root=etree.fromstring(v.source_catalog_xml)
        spaces=[x for x in root.findall("./"+R+"Products/"+R+"Product")
                if x.get("ifcClass")=="IfcSpace"]
        self.assertEqual(len(spaces),1)
        space=spaces[0]
        self.assertEqual(space.get("typedXmlRepresentation"),
                         "NO_READONLY_NATIVE_SOURCE_ONLY")
        self.assertTrue(space.get("originalAggregationParentGuid"))
        self.assertEqual(space.find(R+"SourceWorldMesh").get("state"),
                         "ORIGINAL_NATIVE_TRIANGULATION_READONLY")
        self.assertTrue(any(x.get("ifcClass")=="IfcRelAggregates"
                            and x.get("originalRelatedGuid")==space.get("ifcGuid")
                            for x in root.findall("./"+R+"OriginalNativeRelationshipEvidence/"+R+"Relation")))

    def test_legacy_ifc2x3_and_ifc4_use_original_distinct_native_schema_XSD(self):
        for key,expected in (
            ("ifc2x3door","IFC2X3"),
            ("ifc2x3space","IFC2X3"),
            ("ifc4empty","IFC4"),
        ):
            with self.subTest(key=key):
                src,folder,v,proof=self.run_oracle(key)
                self.assertEqual(v.source_original_ifc_schema,expected)
                root=etree.fromstring(v.projection.xml)
                self.assertEqual(etree.QName(root).namespace,
                    "urn:bim-markup-bench:legacy:v0.8")
                c=etree.fromstring(v.source_catalog_xml)
                self.assertEqual(c.get("sourceIfcSchema"),expected)
                self.assertEqual(v.demoted_opening_guids,())
                self.assertEqual(v.demoted_fill_guids,())
                self.assertEqual(proof["source_catalog_sha256"],
                                 sha256(v.source_catalog_xml).hexdigest())

    def test_every_original_native_product_and_selected_explicit_link_original(self):
        for key in ("geom18","geom19","beam","space","basic","ifc2x3space"):
            with self.subTest(original=key):
                src,folder,v,proof=self.run_oracle(key)
                self.assertTrue(proof[
                    "native_source_IFC_root_and_geometry_identity_preserved"])
                self.assertEqual(proof["source_catalog_sha256"],
                                 sha256(v.source_catalog_xml).hexdigest())
                self.assertGreater(proof["original_native_explicit_source_relationship_edges"],0)
                self.assertFalse(proof["full_original45_IFC_write_parity_proven"])

    def test_repeated_catalog_and_typed_xml_are_byte_identical_after_clock_tick(self):
        src,folder=self.source("geom19")
        first=project_original_native_v13(src)
        time.sleep(1.12)
        second=project_original_native_v13(src)
        self.assertEqual(first.projection.xml,second.projection.xml)
        self.assertEqual(first.source_catalog_xml,second.source_catalog_xml)
        self.assertEqual(first.report(),second.report())

    def test_report_does_not_claim_editable_demoted_or_lossless_IFC_XML(self):
        src,folder,v,proof=self.run_oracle("geom19")
        result=v.report()
        self.assertFalse(result["semantic_native_write_supported_for_demoted_elements"])
        self.assertFalse(result["original_entire_IFC_serialized_losslessly_to_XML"])
        self.assertFalse(result["full_original_45_task_edit_parity"])
        self.assertTrue(result["original_source_not_modified"])
        self.assertEqual(result["new_model_requests"],0)


class TestV13IndependentNegative(V13ReadOnlySourceOriginal):
    def test_original_raw_millimetre_IFC4X3_rejected_for_v13_source(self):
        raw=DATA/SOURCES["geom18"]
        with self.assertRaises(NativeReadV13Error):
            project_original_ifc_v13(raw)

    def test_unknown_original_schema_alias_never_accepted_from_catalog(self):
        src,folder,v,proof=self.run_oracle("geom18")
        cat=etree.fromstring(v.source_catalog_xml)
        cat.set("sourceIfcSchema","IFC2X3")
        with self.assertRaises(IndependentV13SourceError):
            verify_v13_original_native_source(
                src,v.projection.xml,etree.tostring(cat))

    def test_original_product_globalid_removed_from_catalog_detected(self):
        src,folder,v,proof=self.run_oracle("geom18")
        cat=etree.fromstring(v.source_catalog_xml)
        prods=cat.find(R+"Products")
        prods.remove(prods[0])
        with self.assertRaises(IndependentV13SourceError):
            verify_v13_original_native_source(
                src,v.projection.xml,etree.tostring(cat))

    def test_original_native_space_or_beam_mesh_hash_tampering_detected(self):
        for key,typ in (("beam","IfcBeam"),("space","IfcSpace")):
            with self.subTest(key=key):
                src,folder,v,proof=self.run_oracle(key)
                cat=etree.fromstring(v.source_catalog_xml)
                element=next(x for x in cat.findall("./"+R+"Products/"+R+"Product")
                             if x.get("ifcClass")==typ)
                element.find(R+"SourceWorldMesh").set("worldMeshSha256","0"*64)
                with self.assertRaises(IndependentV13SourceError):
                    verify_v13_original_native_source(
                        src,v.projection.xml,etree.tostring(cat))

    def test_fabricated_edit_permission_on_readonly_product_detected(self):
        src,folder,v,proof=self.run_oracle("geom19")
        cat=etree.fromstring(v.source_catalog_xml)
        node=next(x for x in cat.findall("./"+R+"Products/"+R+"Product")
                  if x.get("ifcGuid") in BAD_19)
        node.set("compilerEditPermission","ALLOW_REWRITE_ORIGINAL")
        with self.assertRaises(IndependentV13SourceError):
            verify_v13_original_native_source(
                src,v.projection.xml,etree.tostring(cat))

    def test_original_explicit_IfcRelVoids_relation_tamper_detected(self):
        src,folder,v,proof=self.run_oracle("geom19")
        cat=etree.fromstring(v.source_catalog_xml)
        link=next(x for x in cat.findall(
            "./"+R+"OriginalNativeRelationshipEvidence/"+R+"Relation")
            if x.get("ifcClass")=="IfcRelVoidsElement")
        link.set("originalRelatingGuid","0"*22)
        with self.assertRaises(IndependentV13SourceError):
            verify_v13_original_native_source(
                src,v.projection.xml,etree.tostring(cat))

    def test_old_invalid_original_typed_XML_is_still_rejected_by_strict_native_binder(self):
        for key in ("geom18","geom19"):
            with self.subTest(key=key):
                src,folder=self.source(key)
                old=project_ifc_v9(src)
                ast=parse_xml(old.xml,expected_source_sha256=old.source.source_sha256)
                with self.assertRaises(Exception):
                    bind_document(ast,projection=old)

    def test_demoted_source_opening_injected_back_to_typed_XML_detected(self):
        src,folder=self.source("geom19")
        v=project_original_native_v13(src)
        old=project_ifc_v9(src)
        t=etree.fromstring(v.projection.xml)
        orig=etree.fromstring(old.xml)
        removed=next(x for x in orig.find(Q+"Elements")
                     if x.get("ifcGuid") in BAD_19)
        t.find(Q+"Elements").append(removed)
        with self.assertRaises(IndependentV13SourceError):
            verify_v13_original_native_source(
                src,etree.tostring(t),v.source_catalog_xml)

    def test_original_native_IFC_byte_hash_immutability_never_writes(self):
        src,folder=self.source("geom18")
        before=file_hash(src)
        _=project_original_native_v13(src)
        self.assertEqual(before,file_hash(src))


if __name__=="__main__":
    unittest.main()
