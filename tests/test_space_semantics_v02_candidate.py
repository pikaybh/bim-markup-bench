"""Versioned IFC Space semantics candidate: source-only, no LLM/evaluation.

The model-facing v0.1 projection and preregistered sampling remain unchanged.
All IFC mutations here use in-memory copies solely to test fail-closed guards.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

import ifcopenshell
from lxml import etree

from tests.test_native_t_path_junction import pinned_input
from src.runtime.ifc_projection import project_ifc
from src.runtime.space_semantics_candidate import (
    UnsupportedSpaceSemanticCandidate,NS,
    project_space_semantics_candidate,verify_unedited_space_semantics_candidate,
    _make_source_spaces,
)

TAG=lambda name:"{"+NS+"}"+name


class SpaceSemanticsV02CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task,cls.source,cls.reference_guids=pinned_input()
        cls.source_sha=hashlib.sha256(cls.source.read_bytes()).hexdigest()
        cls.original_v01_xml=project_ifc(cls.source).xml
        cls.candidate=project_space_semantics_candidate(cls.source)

    def test_source_readonly_type_and_psets_for_both_spatial_rooms(self):
        report=verify_unedited_space_semantics_candidate(
            self.source,self.candidate.xml)
        self.assertEqual(report["source_space_count"],2)
        self.assertEqual(report["source_type_count"],2)
        self.assertEqual(report["source_instance_pset_count"],4)
        self.assertEqual(report["source_reference_property_count"],4)
        self.assertTrue(report["source_semantic_observation_matches_exact_ifc"])
        self.assertFalse(report["model_facing_protocol_promoted"])
        self.assertFalse(report["new_space_metadata_authoring_supported"])
        root=etree.fromstring(self.candidate.xml)
        rooms=root.findall(TAG("Space"))
        self.assertEqual(len(rooms),2)
        self.assertEqual({r.get("name") for r in rooms},{"131","134"})
        for room in rooms:
            self.assertIsNotNone(room.find(TAG("Type")))
            self.assertEqual(len(room.findall(".//"+TAG("PropertySet"))),2)
            self.assertEqual(
                [prop.get("valueType") for prop in room.findall(
                    ".//"+TAG("Property")) if prop.get("name")=="Reference"],
                ["IfcIdentifier","IfcIdentifier"])
            self.assertEqual(room.find(TAG("Quantities")).get("status"),
                             "NONE_IN_SOURCE")
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                         self.source_sha)
        self.assertEqual(project_ifc(self.source).xml,self.original_v01_xml)

    def test_candidate_can_be_reproduced_twice_with_identical_bytes(self):
        other=project_space_semantics_candidate(self.source)
        self.assertEqual(other.xml,self.candidate.xml)
        self.assertEqual(other.report(),self.candidate.report())

    def test_tampered_reference_cannot_pass_native_source_verification(self):
        root=etree.fromstring(self.candidate.xml)
        props=[x for x in root.findall(".//"+TAG("Property"))
               if x.get("name")=="Reference"]
        self.assertTrue(props)
        props[0].set("value","forged-room-number")
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "edited or contains invented"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))

    def test_tampered_source_type_identity_rejected(self):
        root=etree.fromstring(self.candidate.xml)
        root.find(".//"+TAG("Type")).set("typeGuid","0"*22)
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "edited or contains invented"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))

    def test_duplicate_or_new_space_is_never_inferred_from_public_input(self):
        root=etree.fromstring(self.candidate.xml)
        old=root.find(TAG("Space"))
        extra=etree.fromstring(etree.tostring(old))
        extra.set("name","invented-room")
        extra.set("ifcGuid","0"*22)
        extra.set("localId","invented_room")
        root.append(extra)
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "edited or contains invented"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))

    def test_stale_or_mismatched_source_sha_blocked(self):
        root=etree.fromstring(self.candidate.xml)
        root.set("sourceModelSha256","0"*64)
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "digest differs"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))

    def test_fake_quantity_and_unsupported_grammar_blocked(self):
        root=etree.fromstring(self.candidate.xml)
        root.find(".//"+TAG("Quantities")).set("status","CALCULATED")
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "secure local XSD"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))
        root=etree.fromstring(self.candidate.xml)
        etree.SubElement(root,TAG("CreateSpace"),attrib={"name":"B"})
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "secure local XSD"):
            verify_unedited_space_semantics_candidate(
                self.source,etree.tostring(root,encoding="utf8"))

    def test_unsafe_entity_declarations_never_accepted(self):
        blob=(b'<?xml version="1.0"?><!DOCTYPE SpaceSemantics '
              b'[<!ENTITY e SYSTEM "file:///windows/win.ini">]>'
              +self.candidate.xml[self.candidate.xml.index(b"<SpaceSemantics"):])
        with self.assertRaisesRegex(UnsupportedSpaceSemanticCandidate,
                                    "secure local XSD"):
            verify_unedited_space_semantics_candidate(self.source,blob)

    def test_source_with_complex_property_or_qto_is_explicitly_unsupported(self):
        model=ifcopenshell.open(str(self.source))
        known=project_ifc(self.source)
        room=model.by_guid(self.reference_guids[2])
        original=room.IsDefinedBy[0].RelatingPropertyDefinition
        special=model.createIfcPropertyListValue(
            Name="PrivateUnsupported",ListValues=(model.createIfcLabel("bad"),))
        original.HasProperties=tuple((*original.HasProperties,special))
        with self.assertRaisesRegex(ValueError,"complex native Space property"):
            _make_source_spaces(model,known)
        model=ifcopenshell.open(str(self.source))
        room=model.by_guid(self.reference_guids[2])
        qto=model.createIfcElementQuantity(
            GlobalId=ifcopenshell.guid.new(),Name="Qto_SpaceBaseQuantities",
            Quantities=(model.createIfcQuantityVolume(
                Name="GrossVolume",VolumeValue=1.0),))
        model.createIfcRelDefinesByProperties(
            GlobalId=ifcopenshell.guid.new(),RelatingPropertyDefinition=qto,
            RelatedObjects=(room,))
        with self.assertRaisesRegex(ValueError,"quantity set requires explicit"):
            _make_source_spaces(model,known)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                         self.source_sha)

    def test_exact_source_metadata_is_represented_only_in_candidate_profile(self):
        self.assertIn(b"SpaceSemantics",self.candidate.xml)
        self.assertIn(b"Pset_SpaceCommon",self.candidate.xml)
        self.assertIn(b"pilotroom 131",self.candidate.xml)
        self.assertNotIn(b"Pset_SpaceCommon",self.original_v01_xml)
        self.assertNotIn(b"SpaceSemantics",self.original_v01_xml)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                         self.source_sha)


if __name__=="__main__":
    unittest.main()
