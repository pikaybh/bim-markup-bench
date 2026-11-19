"""Source-pinned native IFC metadata guard regression tests; no GT or LLM.

These guard original IfcSpaceType, property sets and numerical quantities
without inventing a new Space's unique number/type/reference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from src.runtime.compiler import compile_declarative_xml
from src.runtime.space_metadata_gate import (
    SpaceMetadataPolicyError,preflight_source_room_semantics,
    verify_native_space_metadata,
)
from tests.test_declarative_space_partition_compiler import (
    make_space_split_state,NEW_FAR_ID,
)
from src.runtime.binder import allocate_new_ifc_guid
from tests.test_native_t_path_junction import authored_markup


class SpaceMetadataSemanticsTests(unittest.TestCase):
    def test_original_type_and_instance_psets_are_preserved_without_fake_inheritance(self):
        source,edited=make_space_split_state()
        _,refs,_,_=authored_markup()
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        far_guid=allocate_new_ifc_guid(original_sha,"Space",NEW_FAR_ID,set())
        original=ifcopenshell.open(str(source))
        types,definitions,associations=preflight_source_room_semantics(
            original,refs[2])
        self.assertEqual(len(types),1)
        self.assertEqual(len(definitions),2)
        self.assertEqual(len(associations),0)
        self.assertEqual(sorted(x[2][1] for x in definitions),
                         ["Pset_SpaceCommon","Pset_SpaceHeaterTypeCommon"])
        with TemporaryDirectory(prefix="native-space-metadata-success-") as td:
            candidate=Path(td)/"bounded.xml.ifc"
            compile_declarative_xml(source,edited,candidate)
            resulting=ifcopenshell.open(str(candidate))
            policy=verify_native_space_metadata(original,resulting,
                                                refs[2],far_guid)
            details=policy.report()
            self.assertEqual(details["source_space_type_relations"],1)
            self.assertEqual(details["source_space_pset_relations"],2)
            self.assertEqual(details["source_space_qto_relations"],0)
            self.assertEqual(details["source_space_instance_reference_properties"],2)
            self.assertEqual(details["new_space_type_relations"],0)
            self.assertEqual(details["new_space_pset_relations"],0)
            self.assertTrue(details["existing_room_metadata_preserved"])
            self.assertTrue(details["other_source_space_metadata_preserved"])
            self.assertFalse(details["official_task_eligible"])
            self.assertFalse(details["metadata_semantically_complete"])
            self.assertEqual(len(resulting.by_guid(refs[2]).IsTypedBy),1)
            self.assertEqual(len(resulting.by_guid(refs[2]).IsDefinedBy),2)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         original_sha)

    def test_incorrect_shared_reference_pset_replication_is_rejected(self):
        source,edited=make_space_split_state()
        _,refs,_,_=authored_markup()
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        far_guid=allocate_new_ifc_guid(original_sha,"Space",NEW_FAR_ID,set())
        with TemporaryDirectory(prefix="native-space-pset-leak-") as td:
            candidate=Path(td)/"bounded.ifc"
            compile_declarative_xml(source,edited,candidate)
            source_f=ifcopenshell.open(str(source))
            output=ifcopenshell.open(str(candidate))
            original=output.by_guid(refs[2])
            far=output.by_guid(far_guid)
            cloned_link=original.IsDefinedBy[0]
            cloned_link.RelatedObjects=tuple((*cloned_link.RelatedObjects,far))
            with self.assertRaisesRegex(SpaceMetadataPolicyError,
                                        "Existing source Space"):
                verify_native_space_metadata(source_f,output,refs[2],far_guid)

    def test_incorrect_space_type_inheritance_is_rejected(self):
        source,edited=make_space_split_state()
        _,refs,_,_=authored_markup()
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        far_guid=allocate_new_ifc_guid(original_sha,"Space",NEW_FAR_ID,set())
        with TemporaryDirectory(prefix="native-space-typed-leak-") as td:
            candidate=Path(td)/"bounded.ifc"
            compile_declarative_xml(source,edited,candidate)
            source_f=ifcopenshell.open(str(source))
            result=ifcopenshell.open(str(candidate))
            original=result.by_guid(refs[2])
            rel=original.IsTypedBy[0]
            rel.RelatedObjects=tuple((*rel.RelatedObjects,result.by_guid(far_guid)))
            with self.assertRaisesRegex(SpaceMetadataPolicyError,
                                        "Existing source Space"):
                verify_native_space_metadata(source_f,result,refs[2],far_guid)

    def test_source_quantity_recalculation_not_automatically_invented(self):
        source,edited=make_space_split_state()
        _,refs,_,_=authored_markup()
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        original=ifcopenshell.open(str(source))
        room=original.by_guid(refs[2])
        amount=original.createIfcQuantityArea(Name="NetFloorArea",AreaValue=1.0)
        qto=original.createIfcElementQuantity(
            GlobalId=ifcopenshell.guid.new(),
            Name="Qto_SpaceBaseQuantities",Quantities=(amount,))
        original.createIfcRelDefinesByProperties(
            GlobalId=ifcopenshell.guid.new(),RelatedObjects=(room,),
            RelatingPropertyDefinition=qto)
        with self.assertRaisesRegex(SpaceMetadataPolicyError,
                                    "quantity set requires explicit"):
            preflight_source_room_semantics(original,refs[2])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         original_sha)

    def test_nonstandard_complex_property_policy_rejected(self):
        source,_,_,_=authored_markup()
        _,refs,_,_=authored_markup()
        original=ifcopenshell.open(str(source))
        room=original.by_guid(refs[2])
        prop_set=room.IsDefinedBy[0].RelatingPropertyDefinition
        special=original.createIfcPropertyListValue(
            Name="CalculatedOccupancy",ListValues=(original.createIfcLabel("unsafe"),))
        prop_set.HasProperties=tuple((*prop_set.HasProperties,special))
        with self.assertRaisesRegex(SpaceMetadataPolicyError,
                                    "complex native Space property"):
            preflight_source_room_semantics(original,refs[2])


if __name__=="__main__":
    unittest.main()
