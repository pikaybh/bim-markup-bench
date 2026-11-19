"""v0.10 original BIBIMBAP native IFC4X3 source-only multi-Column tests.

Real pinned public source IFC, stable declarative XML, trusted native compiler
and independent IFC-only oracle. No hidden GT, source scorer, model calls or
Xim/BIXML. Both negative and real native positive tests must be retained.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v10_column_multi import (
    MultiColumnV10Error,source_native_slab_contact_plan,
    compile_declarative_xml_v10,
)
from src.runtime.markup_normal_form import NS
from tools.oracle_bibimbap_v10_native_multi import (
    IndependentNativeMultiV10Error,
    verify_v10_original_native_column_multi_delete,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
ORIGINAL=BASE/"bibimbap-author-data"/"ifc"/"01/02/01_02_017.ifc"
PUBLIC_NAMED_SLAB="2IIWDJ6bzEPxU4iXeUX9Z5"
OTHER_UPPER_SLAB="2IIWDJ6bzEPxU4iXeUX9zb"
LOWER_CONTACT={
    "2IIWDJ6bzEPxU4iXeUX9cP","2IIWDJ6bzEPxU4iXeUX9rk",
    "2IIWDJ6bzEPxU4iXeUX9wF","2IIWDJ6bzEPxU4iXeUX9wJ",
    "2IIWDJ6bzEPxU4iXeUX9zS",
}
UPPER_NONCONTACT={
    "2IIWDJ6bzEPxU4iXeUX9_B","2IIWDJ6bzEPxU4iXeUX9ow",
    "2IIWDJ6bzEPxU4iXeUX9rK","2IIWDJ6bzEPxU4iXeUX9rM",
    "2IIWDJ6bzEPxU4iXeUX9ti",
}
Q="{"+NS+"}"


class OriginalNativeMultiV10(unittest.TestCase):
    def original(self):
        if not ORIGINAL.is_file():
            self.skipTest("Pinned public BIBIMBAP original IFC dataset not mounted")
        td=tempfile.TemporaryDirectory(prefix="bibimbap134-col-delete-")
        self.addCleanup(td.cleanup)
        folder=Path(td.name)
        original_hash=file_hash(ORIGINAL)
        self.addCleanup(lambda:self.assertEqual(file_hash(ORIGINAL),original_hash))
        original=ifcopenshell.open(str(ORIGINAL))
        self.assertEqual(original.schema,"IFC4X3")
        self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(original),.001,places=10)
        normalized=folder/"source_original_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            original,"METER").write(str(normalized))
        h=file_hash(normalized)
        self.addCleanup(lambda:self.assertEqual(file_hash(normalized),h))
        native=ifcopenshell.open(str(normalized))
        source_plan=source_native_slab_contact_plan(native,PUBLIC_NAMED_SLAB)
        projection=project_ifc_v9(normalized)
        tree=etree.fromstring(projection.xml)
        return folder,normalized,source_plan,tree

    def edited(self):
        folder,source,plan,tree=self.original()
        root=tree.find(Q+"Elements")
        original_columns=tree.findall("./"+Q+"Elements/"+Q+"Column")
        self.assertEqual(len(original_columns),10)
        for col in original_columns:
            if col.get("ifcGuid") in UPPER_NONCONTACT:
                root.remove(col)
        self.assertEqual(len(tree.findall("./"+Q+"Elements/"+Q+"Column")),5)
        return folder,source,plan,tree

    def generated(self):
        folder,source,plan,tree=self.edited()
        candidate=folder/"candidate_metres.ifc"
        report=compile_declarative_xml_v10(
            source,etree.tostring(tree,encoding="utf8"),candidate,
            reference_slab_guid=PUBLIC_NAMED_SLAB,
        )
        return folder,source,plan,tree,candidate,report


class NativePositiveV10(OriginalNativeMultiV10):
    def test_source_native_contact_partitions_ten_columns_five_five(self):
        folder,source,plan,tree=self.original()
        self.assertEqual(set(plan["contacting_keep_guids"]),LOWER_CONTACT)
        self.assertEqual(set(plan["noncontact_delete_guids"]),UPPER_NONCONTACT)
        self.assertEqual(len(plan["source_column_geometry"]),10)
        self.assertEqual(plan["named_public_slab_world_top_m"][2],0.0)

    def test_original_source_full_declarative_columns_all_visible(self):
        folder,source,plan,tree=self.original()
        nodes=tree.findall("./"+Q+"Elements/"+Q+"Column")
        self.assertEqual(len(nodes),10)
        self.assertEqual({n.get("ifcGuid") for n in nodes},
                         LOWER_CONTACT|UPPER_NONCONTACT)
        self.assertEqual(len(tree.findall("./"+Q+"Elements/"+Q+"Slab")),2)
        self.assertTrue(any(s.get("ifcGuid")==PUBLIC_NAMED_SLAB
                            for s in tree.findall(".//"+Q+"Slab")))

    def test_actual_original_native_multi_delete_survivors_and_source_slab(self):
        folder,source,plan,tree,candidate,report=self.generated()
        self.assertEqual(len(report.operations),5)
        self.assertEqual({x.ifc_guid for x in report.operations},UPPER_NONCONTACT)
        self.assertTrue(report.as_dict()["preserved_original_ifc4x3_schema"])
        self.assertFalse(report.as_dict()["original_published_45_backend_parity_proven"])
        native=ifcopenshell.open(str(candidate))
        self.assertEqual(native.schema,"IFC4X3")
        self.assertEqual({c.GlobalId for c in native.by_type("IfcColumn")},LOWER_CONTACT)
        self.assertTrue(native.by_guid(PUBLIC_NAMED_SLAB).is_a("IfcSlab"))

    def test_independent_oracle_original_step_root_and_native_slab_geometry(self):
        folder,source,plan,tree,candidate,report=self.generated()
        proof=verify_v10_original_native_column_multi_delete(
            source,candidate,reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertEqual(proof["original_native_columns_count"],10)
        self.assertEqual(set(proof["original_native_contact_columns_preserved"]),LOWER_CONTACT)
        self.assertEqual(set(proof["original_native_noncontact_columns_deleted"]),UPPER_NONCONTACT)
        self.assertEqual(proof["removed_original_native_step_entities"],75)
        self.assertEqual(proof["modified_original_native_step_entities"],2)
        self.assertTrue(proof["all_original_surviving_type_map_material_relations_preserved"])

    def test_source_material_types_psets_containment_all_preserved_on_survivors(self):
        folder,source,plan,tree,candidate,report=self.generated()
        original=ifcopenshell.open(str(source))
        result=ifcopenshell.open(str(candidate))
        before={r.GlobalId:r for r in original.by_type("IfcRoot")}
        after={r.GlobalId:r for r in result.by_type("IfcRoot")}
        for guid in LOWER_CONTACT:
            self.assertEqual(str(before[guid]),str(after[guid]))
            col=after[guid]
            inverses=result.get_inverse(col)
            self.assertEqual(len([r for r in inverses if r.is_a("IfcRelDefinesByType")]),1)
            self.assertEqual(len([r for r in inverses if r.is_a("IfcRelDefinesByProperties")]),3)
            self.assertEqual(len([r for r in inverses if r.is_a("IfcRelContainedInSpatialStructure")]),1)
        self.assertEqual(len(result.by_type("IfcRelAssociatesMaterial")),
                         len(original.by_type("IfcRelAssociatesMaterial")))

    def test_repeat_result_ifc_is_byte_identical_across_actual_wall_clock_seconds(self):
        folder,source,plan,tree=self.edited()
        xml=etree.tostring(tree)
        a=folder/"first.ifc";b=folder/"second.ifc"
        compile_declarative_xml_v10(
            source,xml,a,reference_slab_guid=PUBLIC_NAMED_SLAB)
        time.sleep(1.12)
        compile_declarative_xml_v10(
            source,xml,b,reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertEqual(file_hash(a),file_hash(b))
        self.assertEqual(a.read_bytes(),b.read_bytes())


class NativeNegativeV10(OriginalNativeMultiV10):
    def test_source_original_schema_must_be_metres_not_raw_mm(self):
        with self.assertRaises(Exception):
            project_ifc_v9(ORIGINAL)
        original=ifcopenshell.open(str(ORIGINAL))
        with self.assertRaises(MultiColumnV10Error):
            source_native_slab_contact_plan(original,PUBLIC_NAMED_SLAB)

    def test_source_bad_named_reference_globalid_must_refuse(self):
        folder,source,plan,tree=self.edited()
        result=folder/"wrong_guid.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid="0"*22)
        self.assertFalse(result.exists())

    def test_source_other_original_upper_slab_would_reverse_contacts_so_refused(self):
        folder,source,plan,tree=self.edited()
        result=folder/"wrong_slab.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=OTHER_UPPER_SLAB)
        self.assertFalse(result.exists())

    def test_declare_only_four_upper_column_deletes_refused(self):
        folder,source,plan,tree=self.original()
        columns=tree.findall("./"+Q+"Elements/"+Q+"Column")
        for col in columns:
            if col.get("ifcGuid") in sorted(UPPER_NONCONTACT)[:4]:
                tree.find(Q+"Elements").remove(col)
        result=folder/"partial.ifc"
        with self.assertRaisesRegex(MultiColumnV10Error,"exactly ALL"):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_wrong_keep_column_deleted_instead_of_one_upper_refused(self):
        folder,source,plan,tree=self.original()
        doomed=sorted(UPPER_NONCONTACT)[:4]+[sorted(LOWER_CONTACT)[0]]
        for col in tree.findall("./"+Q+"Elements/"+Q+"Column"):
            if col.get("ifcGuid") in doomed:
                tree.find(Q+"Elements").remove(col)
        result=folder/"wrong_lower.ifc"
        with self.assertRaisesRegex(MultiColumnV10Error,"exactly ALL"):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_six_deletions_including_one_true_support_refused(self):
        folder,source,plan,tree=self.edited()
        col=next(n for n in tree.findall("./"+Q+"Elements/"+Q+"Column")
                 if n.get("ifcGuid") in LOWER_CONTACT)
        tree.find(Q+"Elements").remove(col)
        result=folder/"too_many.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_declarative_noop_cannot_delete_anything(self):
        folder,source,plan,tree=self.original()
        result=folder/"noop.ifc"
        with self.assertRaisesRegex(MultiColumnV10Error,"Only removal"):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_surviving_column_moved_during_delete_refused(self):
        folder,source,plan,tree=self.edited()
        col=next(n for n in tree.findall("./"+Q+"Elements/"+Q+"Column"))
        col.set("x",str(float(col.get("x"))+.1))
        result=folder/"moved_suvivor.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_slab_edit_mixed_with_column_deletes_refused(self):
        folder,source,plan,tree=self.edited()
        slab=next(x for x in tree.findall("./"+Q+"Elements/"+Q+"Slab")
                  if x.get("ifcGuid")==PUBLIC_NAMED_SLAB)
        slab.set("thickness","0.4")
        result=folder/"mixed.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_new_column_create_mixed_with_multi_delete_refused(self):
        folder,source,plan,tree=self.edited()
        clone=next(iter(tree.findall("./"+Q+"Elements/"+Q+"Column")))
        attrs=dict(clone.attrib)
        attrs["id"]="NEW_GENERATED_SOURCE_COLUMN_NOT_PERMITTED"
        attrs.pop("ifcGuid",None)
        etree.SubElement(tree.find(Q+"Elements"),Q+"Column",attrib=attrs)
        result=folder/"mixed_create.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_missing_public_slab_from_xml_refused(self):
        folder,source,plan,tree=self.edited()
        slab=next(x for x in tree.findall("./"+Q+"Elements/"+Q+"Slab")
                  if x.get("ifcGuid")==PUBLIC_NAMED_SLAB)
        tree.find(Q+"Elements").remove(slab)
        result=folder/"missing_reference.ifc"
        with self.assertRaises(MultiColumnV10Error):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_wrong_original_source_hash_rejected(self):
        folder,source,plan,tree=self.edited()
        tree.set("sourceModelSha256","0"*64)
        result=folder/"wronghash.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_wrong_existing_ifcguid_xml_identity_rejected(self):
        folder,source,plan,tree=self.edited()
        node=next(iter(tree.findall("./"+Q+"Elements/"+Q+"Column")))
        node.set("ifcGuid","3"*22)
        result=folder/"wrongnativeguid.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_pseudo_imperative_XML_commands_rejected(self):
        folder,source,plan,tree=self.edited()
        etree.SubElement(tree.find(Q+"Elements"),Q+"Delete",attrib={
            "objectId":"column_fake"
        })
        result=folder/"commands.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_DTD_entity_xxe_XML_rejected(self):
        folder,source,plan,tree=self.edited()
        unsafe=(b'<!DOCTYPE Building [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
                +etree.tostring(tree))
        result=folder/"xxe.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v10(source,unsafe,result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertFalse(result.exists())

    def test_preexisting_output_is_immutable_and_never_overwritten(self):
        folder,source,plan,tree=self.edited()
        result=folder/"occupied.ifc"
        result.write_bytes(b"ORIGINAL SCORE EVIDENCE")
        with self.assertRaisesRegex(MultiColumnV10Error,"unused"):
            compile_declarative_xml_v10(source,etree.tostring(tree),result,
                                          reference_slab_guid=PUBLIC_NAMED_SLAB)
        self.assertEqual(result.read_bytes(),b"ORIGINAL SCORE EVIDENCE")

    def test_independent_oracle_rejects_wrong_public_reference_slab(self):
        folder,source,plan,tree,candidate,report=self.generated()
        with self.assertRaises(IndependentNativeMultiV10Error):
            verify_v10_original_native_column_multi_delete(
                source,candidate,reference_slab_guid=OTHER_UPPER_SLAB)

    def test_independent_oracle_rejects_changed_surviving_column_name(self):
        folder,source,plan,tree,candidate,report=self.generated()
        native=ifcopenshell.open(str(candidate))
        native.by_guid(sorted(LOWER_CONTACT)[0]).Name="BROKEN ORIGINAL COLUMN"
        corrupt=folder/"tampered-survivor.ifc"
        native.write(str(corrupt))
        with self.assertRaises(IndependentNativeMultiV10Error):
            verify_v10_original_native_column_multi_delete(
                source,corrupt,reference_slab_guid=PUBLIC_NAMED_SLAB)

    def test_independent_oracle_rejects_changed_surviving_type_map(self):
        folder,source,plan,tree,candidate,report=self.generated()
        native=ifcopenshell.open(str(candidate))
        col=native.by_guid(sorted(LOWER_CONTACT)[0])
        mapping=col.Representation.Representations[0].Items[0]
        extrusion=mapping.MappingSource.MappedRepresentation.Items[0]
        extrusion.Depth+=.1
        corrupt=folder/"tampered-type-map.ifc"
        native.write(str(corrupt))
        with self.assertRaises(IndependentNativeMultiV10Error):
            verify_v10_original_native_column_multi_delete(
                source,corrupt,reference_slab_guid=PUBLIC_NAMED_SLAB)

    def test_independent_oracle_rejects_reference_slab_changed_geometry(self):
        folder,source,plan,tree,candidate,report=self.generated()
        native=ifcopenshell.open(str(candidate))
        slab=native.by_guid(PUBLIC_NAMED_SLAB)
        solid=next(i for rep in slab.Representation.Representations for i in rep.Items
                   if i.is_a("IfcExtrudedAreaSolid"))
        solid.Depth+=.01
        corrupt=folder/"tampered-slab-depth.ifc"
        native.write(str(corrupt))
        with self.assertRaises(IndependentNativeMultiV10Error):
            verify_v10_original_native_column_multi_delete(
                source,corrupt,reference_slab_guid=PUBLIC_NAMED_SLAB)


if __name__=="__main__":
    unittest.main()
