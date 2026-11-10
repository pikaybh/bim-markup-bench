"""Experimental D0 XML Space metadata state: real IFC write and fail-closed.

All fixture values are independently resolved from public source IFC geometry,
not the held-out IFC ground truth or official scorer. No LLM is called.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
from lxml import etree

from src.runtime.space_semantics_candidate import project_space_semantics_candidate
from src.runtime.space_semantics_authoring_candidate import (
    NS,UnsupportedExplicitSpaceSemantics,
    compile_explicit_space_semantics_candidate,parse_authored_space_state,
)
from tests.test_declarative_space_partition_compiler import (
    make_space_split_state,NEW_FAR_ID,
)

TAG=lambda name:"{"+NS+"}"+name


def authored_new_space_metadata():
    source,geo_xml=make_space_split_state()
    old=project_space_semantics_candidate(source)
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    root=etree.Element(TAG("SpaceSemanticsState"),nsmap={None:NS},
        attrib={
            "version":"0.2-authoring-prototype",
            "sourceModelSha256":sha,
            "sourceObservationSha256":hashlib.sha256(old.xml).hexdigest(),
            "policy":"EXPLICIT_NEW_SPACE_METADATA_ONLY",
        })
    space=etree.SubElement(root,TAG("Space"),attrib={
        "localId":NEW_FAR_ID,
        "name":"135",
        "longName":"pilotroom",
        "predefinedType":"NOTDEFINED",
        "compositionType":"ELEMENT",
    })
    etree.SubElement(space,TAG("Type"),attrib={
        "name":"pilotroom 135:explicit partition",
        "predefinedType":"NOTDEFINED",
    })
    container=etree.SubElement(space,TAG("PropertySets"))
    for pset_name,entries in (
        ("Pset_SpaceCommon",(
            ("Reference","IfcIdentifier","pilotroom 135"),
            ("IsExternal","IfcBoolean","false"),
        )),
        ("Pset_SpaceHeaterTypeCommon",(
            ("Reference","IfcIdentifier","pilotroom 135"),
        )),
    ):
        pset=etree.SubElement(container,TAG("PropertySet"),attrib={"name":pset_name})
        for name,kind,value in entries:
            etree.SubElement(pset,TAG("Property"),
                             attrib={"name":name,"valueType":kind,"value":value})
    etree.SubElement(space,TAG("Quantities"),attrib={
        "netFloorAreaM2":"2.7467625",
        "netVolumeM3":"7.690935",
    })
    return source,geo_xml,old.xml,etree.tostring(root,encoding="utf8",
                                                 xml_declaration=True)


class ExperimentalExplicitSpaceMetadataTests(unittest.TestCase):
    def test_explicit_state_produces_native_type_psets_and_quantity(self):
        src,geo,old,edited=authored_new_space_metadata()
        original_sha=hashlib.sha256(src.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="v02-space-meta-d0-test-") as td:
            destination=Path(td)/"typed-split.ifc"
            report=compile_explicit_space_semantics_candidate(
                src,geo,old,edited,destination)
            self.assertTrue(report["new_space_type_declared_and_written"])
            self.assertTrue(report["new_space_two_psets_declared_and_written"])
            self.assertTrue(report["new_space_qto_explicit_and_native_geometry_checked"])
            native=ifcopenshell.open(str(destination))
            created=[r for r in native.by_type("IfcSpace") if r.Name=="135"]
            self.assertEqual(len(created),1)
            space=created[0]
            self.assertEqual(space.LongName,"pilotroom")
            self.assertEqual(space.IsTypedBy[0].RelatingType.Name,
                             "pilotroom 135:explicit partition")
            self.assertEqual(len(space.IsDefinedBy),3)
            psets=[rel.RelatingPropertyDefinition for rel in space.IsDefinedBy]
            self.assertEqual(len([p for p in psets if p.is_a("IfcPropertySet")]),2)
            qto=next(p for p in psets if p.is_a("IfcElementQuantity"))
            self.assertEqual({q.Name:(
                getattr(q,"AreaValue",None) if q.is_a("IfcQuantityArea")
                else getattr(q,"VolumeValue",None)) for q in qto.Quantities},
                {"NetFloorArea":2.7467625,"NetVolume":7.690935})
            source_rooms=ifcopenshell.open(str(src)).by_type("IfcSpace")
            for original in source_rooms:
                same=native.by_guid(original.GlobalId)
                self.assertEqual(len(original.IsDefinedBy),len(same.IsDefinedBy))
                self.assertEqual(len(original.IsTypedBy),len(same.IsTypedBy))
            self.assertFalse(report["official_task_success"])
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),original_sha)

    def test_stale_source_metadata_rejected_without_ifc(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new);root.set("sourceObservationSha256","0"*64)
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,"hash stale"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_forged_quantity_rejected_before_commit(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        root.find(".//"+TAG("Quantities")).set("netVolumeM3","999")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,"area/volume"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_conflicting_new_room_name_rejected(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        root.find(TAG("Space")).set("name","131")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,"name conflicts"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_inconsistent_new_room_reference_rejected(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        refs=[p for p in root.findall(".//"+TAG("Property")) if p.get("name")=="Reference"]
        self.assertEqual(len(refs),2)
        refs[1].set("value","pilotroom 131")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,"consistent"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_source_existing_reference_reuse_denied(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        for ref in root.findall(".//"+TAG("Property")):
            if ref.get("name")=="Reference":
                ref.set("value","pilotroom 131")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,
                                        "Reference conflicts"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_existing_space_type_name_reuse_denied(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        root.find(".//"+TAG("Type")).set("name","pilotroom 131:1597135")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,
                                        "SpaceType name conflicts"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_incorrect_new_space_local_id_rejected_before_output(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        root.find(TAG("Space")).set("localId","not_a_native_space")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,
                                        "new v0.1 Space local ID"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_forced_external_room_boolean_rejected(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        external=next(p for p in root.findall(".//"+TAG("Property"))
                      if p.get("name")=="IsExternal")
        external.set("value","true")
        with TemporaryDirectory() as td:
            output=Path(td)/"never.ifc"
            with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,
                                        "consistent"):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,etree.tostring(root),output)
            self.assertFalse(output.exists())

    def test_preexisting_output_never_overwritten(self):
        source,geo,old,new=authored_new_space_metadata()
        with TemporaryDirectory() as td:
            output=Path(td)/"preexisting.ifc"
            original=b"NEVER OVERWRITE"
            output.write_bytes(original)
            from src.runtime.transaction import TransactionError
            with self.assertRaises(TransactionError):
                compile_explicit_space_semantics_candidate(
                    source,geo,old,new,output)
            self.assertEqual(output.read_bytes(),original)

    def test_unsupported_command_style_xml_denied(self):
        source,geo,old,new=authored_new_space_metadata()
        root=etree.fromstring(new)
        etree.SubElement(root,TAG("CreateSpace"),attrib={"name":"unsafe"})
        with self.assertRaisesRegex(UnsupportedExplicitSpaceSemantics,"secure v0.2"):
            parse_authored_space_state(etree.tostring(root),
                hashlib.sha256(source.read_bytes()).hexdigest(),
                hashlib.sha256(old).hexdigest())


if __name__=="__main__":
    unittest.main()
