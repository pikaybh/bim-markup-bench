"""G1 #15: direct XML state deletion -> trusted native IFC (restricted).

Tests real published source and its native relationships; all GT grader
annotations and official BIM-Edit answer paths remain absent from inputs.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
from lxml import etree

from src.runtime.compiler import compile_declarative_xml, CompilerError
from src.runtime.hosted_door_delete import (
    preflight_door_opening_deletion, verify_scoped_door_delete_output,
)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.ifc_projection import project_ifc
from tests.oracles.python.independent_public_door_delete import (
    native_door_opening_delete,
)
from tests.oracles.python.public_door_delete_postconditions import (
    check_native_i0_result,
)
from tools.verify_public_door_delete_gate import verified_public_source


class NativePairedDeleteRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public, cls.guids, cls.source = verified_public_source()
        cls.original_sha = sha256(cls.source.read_bytes()).hexdigest()
        cls.projection = project_ifc(cls.source)
        cls.model = ifcopenshell.open(str(cls.source))
        cls.pair = preflight_door_opening_deletion(
            cls.model, cls.guids["door"], cls.guids["opening"])

    def _changed(self, changes: tuple[str, ...] = ("Door", "Opening"),
                 *, alter_wall_height=False, extra_window=False) -> bytes:
        xml = etree.fromstring(self.projection.xml)
        nodes = {
            etree.QName(e).localname:e for e in tuple(xml.iter())
            if isinstance(e.tag, str)
            and e.get("ifcGuid") in (self.guids["door"],self.guids["opening"])
        }
        if set(nodes) != {"Door","Opening"}:
            raise AssertionError("Frozen target XML differs from pinned projection")
        for name in changes:
            nodes[name].getparent().remove(nodes[name])
        if alter_wall_height:
            wall = next(e for e in xml.iter() if etree.QName(e).localname=="Wall")
            wall.set("height",str(float(wall.get("height"))+0.5))
        if extra_window:
            window = next(e for e in xml.iter() if etree.QName(e).localname=="Window")
            window.getparent().remove(window)
        return etree.tostring(xml,encoding="utf8",xml_declaration=True)

    def _compile(self, updated: bytes):
        with TemporaryDirectory(prefix="g1-door-delete-compiled-") as td:
            output=Path(td)/"result.ifc"
            report=compile_declarative_xml(self.source,updated,output)
            self.assertTrue(output.is_file())
            self.assertEqual(len(report.operations),1)
            self.assertEqual(report.operations[0].operation,
                             "DELETE_HOSTED_DOOR_OPENING")
            measured = check_native_i0_result(
                self.source,output,self.public["instruction"])
            self.assertEqual(measured["native_IfcRoot_deleted"],10)
            self.assertEqual(measured["surviving_shared_relations_updated"],3)
            self.assertEqual(measured["native_unrelated_world_meshes_preserved"],13)
            self.assertTrue(measured["host_wall_opening_void_closed"])
            self.assertFalse(measured["unmentioned_space_boundary_policy_resolved"])
            self.assertEqual(report.unexpected_root_changes,())
            self.assertGreater(report.untouched_root_objects_verified,0)
            self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),
                             self.original_sha)
            return measured

    def test_d0_real_native_pair_matches_independently_generated_i0_outcome(self):
        before=sha256(self.source.read_bytes()).hexdigest()
        d0=self._compile(self._changed())
        with TemporaryDirectory(prefix="g1-door-independent-parity-") as td:
            i0=Path(td)/"i0.ifc"
            native_door_opening_delete(
                self.source,i0,self.guids["door"],self.guids["opening"])
            observed=check_native_i0_result(
                self.source,i0,self.public["instruction"])
        for field in (
            "native_IfcRoot_deleted","native_IfcRoot_removed_class_counts",
            "surviving_shared_relations_updated",
            "native_original_IfcSpace_count",
            "native_IfcRelSpaceBoundary_deleted",
            "original_Opening_direct_storey_assignments",
            "native_unrelated_world_meshes_preserved",
            "host_wall_mesh_volume_gain_m3",
            "host_wall_opening_void_closed",
        ):
            self.assertEqual(d0[field],observed[field],field)
        self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),before)

    def _reject_without_output(self, data: bytes):
        with TemporaryDirectory(prefix="g1-door-rejected-") as td:
            result=Path(td)/"should-not-exist.ifc"
            original_sha=sha256(self.source.read_bytes()).hexdigest()
            with self.assertRaises(CompilerError):
                compile_declarative_xml(self.source,data,result)
            self.assertFalse(result.exists())
            self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),original_sha)

    def test_single_door_only_is_not_a_supported_native_deletion(self):
        self._reject_without_output(self._changed(("Door",)))

    def test_single_opening_only_with_existing_door_is_not_supported(self):
        self._reject_without_output(self._changed(("Opening",)))

    def test_paired_delete_plus_wall_geometry_change_is_not_silent_partial_commit(self):
        self._reject_without_output(self._changed(alter_wall_height=True))

    def test_paired_delete_plus_other_window_delete_is_not_silent_partial_commit(self):
        self._reject_without_output(self._changed(extra_window=True))

    def test_source_door_with_unexpected_inverse_relation_is_rejected(self):
        f=ifcopenshell.open(str(self.source))
        door=f.by_guid(self.guids["door"])
        group=f.create_entity("IfcGroup",GlobalId=ifcopenshell.guid.new())
        f.create_entity(
            "IfcRelAssignsToGroup",GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=(door,),RelatingGroup=group,
        )
        with self.assertRaisesRegex(
            UnsupportedIFCMutation,"unsupported native inverse"):
            preflight_door_opening_deletion(
                f,self.guids["door"],self.guids["opening"])

    def test_shared_pset_prevents_removal_of_unrelated_door_metadata(self):
        f=ifcopenshell.open(str(self.source))
        door=f.by_guid(self.guids["door"])
        another=next(x for x in f.by_type("IfcDoor")
                     if x.GlobalId != door.GlobalId)
        rel=next(x for x in f.get_inverse(door)
                 if x.is_a("IfcRelDefinesByProperties"))
        rel.RelatedObjects=(door,another)
        with self.assertRaisesRegex(
            UnsupportedIFCMutation,"property assignment is shared"):
            preflight_door_opening_deletion(
                f,self.guids["door"],self.guids["opening"])

    def test_unexpected_direct_opening_storey_assignment_rejected(self):
        f=ifcopenshell.open(str(self.source))
        opening=f.by_guid(self.guids["opening"])
        door=f.by_guid(self.guids["door"])
        container=door.ContainedInStructure[0]
        container.RelatedElements=tuple(container.RelatedElements)+(opening,)
        with self.assertRaisesRegex(
            UnsupportedIFCMutation,"relationship or opening storey ambiguous"):
            preflight_door_opening_deletion(
                f,self.guids["door"],self.guids["opening"])

    def test_missing_original_door_space_boundary_is_not_silently_skipped(self):
        f=ifcopenshell.open(str(self.source))
        door=f.by_guid(self.guids["door"])
        f.remove(door.ProvidesBoundaries[0])
        with self.assertRaisesRegex(
            UnsupportedIFCMutation,"unsupported native inverse"):
            preflight_door_opening_deletion(
                f,self.guids["door"],self.guids["opening"])

    def test_fabricated_native_postcondition_suppresses_publication_atomically(self):
        with TemporaryDirectory(prefix="g1-native-rollback-") as td:
            output=Path(td)/"never-committed.ifc"
            with patch("src.runtime.compiler.verify_scoped_door_delete_output",
                       side_effect=UnsupportedIFCMutation("Injected native invalidity")):
                with self.assertRaises(CompilerError):
                    compile_declarative_xml(self.source,self._changed(),output)
            self.assertFalse(output.exists())
            self.assertEqual(sha256(self.source.read_bytes()).hexdigest(),
                             self.original_sha)
            self.assertEqual(list(Path(td).glob(".bim-compiler-*")),[])

    def test_validator_does_not_tolerate_unrelated_mesh_change(self):
        with TemporaryDirectory(prefix="g1-deletion-collateral-") as td:
            good=Path(td)/"good.ifc"
            native_door_opening_delete(
                self.source,good,self.guids["door"],self.guids["opening"])
            after=ifcopenshell.open(str(good))
            unrelated=next(w for w in after.by_type("IfcWall")
                           if w.GlobalId!=self.guids["wall"])
            point=unrelated.ObjectPlacement.RelativePlacement.Location
            xyz=tuple(point.Coordinates)
            point.Coordinates=(xyz[0]+0.3,xyz[1],xyz[2])
            with self.assertRaises(UnsupportedIFCMutation):
                verify_scoped_door_delete_output(self.model,after,self.pair)

    def test_preflight_rejects_mismatched_ifc_classes_and_unpaired_openings(self):
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_door_opening_deletion(
                self.model,self.guids["wall"],self.guids["opening"])
        other=next(x for x in self.model.by_type("IfcOpeningElement")
                   if x.GlobalId!=self.guids["opening"])
        with self.assertRaises(UnsupportedIFCMutation):
            preflight_door_opening_deletion(
                self.model,self.guids["door"],other.GlobalId)


if __name__=="__main__":
    unittest.main()
