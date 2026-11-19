"""Issue #15: rotated hosted openings, independent IFC baseline and native guards.

OWN synthetic fixtures only; the official fixed public task is tested
separately under a trusted, source-only oracle after these tests pass.
"""
from __future__ import annotations
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np
from lxml import etree

from src.runtime.compiler import compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import (_plain_opening_local_frame,
                                      _validate_opening_move_preflight,
                                      native_topology_inventory)
from src.runtime.ifc_mutations import UnsupportedIFCMutation
from src.runtime.xml_parser import parse_xml
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report


SOURCE=Path(__file__).resolve().parents[1]/"tests/fixtures/synthetic/input.ifc"
NS="urn:bim-markup-bench:toy:v0"


def rotated_own_source(destination:Path, *, tilt:bool=False)->tuple[str,str]:
    f=ifcopenshell.open(str(SOURCE))
    wall=f.by_type("IfcWall")[0]
    origin=wall.ObjectPlacement.RelativePlacement
    origin.RefDirection=f.createIfcDirection((0.,1.,0.))
    if tilt:
        # A tilted host changes the local wall extrusion/vertical semantics.
        origin.Axis=f.createIfcDirection((1.,0.,0.))
    opening=next(o for o in f.by_type("IfcOpeningElement")
                 if o.Name=="Window Opening")
    window=opening.HasFillings[0].RelatedBuildingElement
    f.write(str(destination))
    return opening.GlobalId,window.GlobalId


class RotatedHostOpeningTests(unittest.TestCase):
    def test_own_90_degree_host_opening_and_window_move_world_positive_y(self):
        with TemporaryDirectory(prefix="own-rotated-opening-") as folder:
            root=Path(folder)
            source=root/"source.ifc"
            opening_guid,window_guid=rotated_own_source(source)
            original=source.read_bytes()
            projected=project_ifc(source)
            xml=etree.fromstring(projected.xml)
            candidate=[node for node in xml.iter()
                       if isinstance(node.tag,str)
                       and node.get("ifcGuid")==opening_guid]
            self.assertEqual(len(candidate),1)
            old_offset=Decimal(candidate[0].get("offset"))
            candidate[0].set("offset",format(old_offset+Decimal("0.5"),"f"))
            edited=etree.tostring(xml,encoding="utf-8",xml_declaration=True)
            before=ifcopenshell.open(str(source))
            before_xyz=np.asarray(ifcopenshell.util.placement.get_local_placement(
                before.by_guid(window_guid).ObjectPlacement)[:3,3])
            prior_rels=native_topology_inventory(before)
            direct=root/"D0.ifc"
            imperative=root/"I0.ifc"
            report=compile_declarative_xml(source,edited,direct)
            manual_ifc_reference(source,imperative,"MOVE_OPENING",
                                 target_guid=opening_guid,delta_x=0.5)
            result=ifcopenshell.open(str(direct))
            after_xyz=np.asarray(ifcopenshell.util.placement.get_local_placement(
                result.by_guid(window_guid).ObjectPlacement)[:3,3])
            self.assertTrue(np.allclose(after_xyz-before_xyz,(0.,0.5,0.),atol=1e-6))
            self.assertEqual(prior_rels,native_topology_inventory(result))
            self.assertEqual(report.operations[0].operation,"MOVE_OPENING_WITH_FILLING")
            self.assertTrue(parity_report(direct,imperative)["parity"])
            self.assertEqual(source.read_bytes(),original)

    def test_tilted_host_rejected_by_native_preflight(self):
        with TemporaryDirectory(prefix="own-tilted-opening-") as folder:
            path=Path(folder)/"tilted.ifc"
            opening_guid,_=rotated_own_source(path,tilt=True)
            f=ifcopenshell.open(str(path))
            opening=f.by_guid(opening_guid)
            wall=opening.VoidsElements[0].RelatingBuildingElement
            with self.assertRaises(UnsupportedIFCMutation):
                _plain_opening_local_frame(opening,wall)


    @unittest.skipUnless((SOURCE.parents[3]/"data/tasks.jsonl").is_file(),
                         "Pinned task metadata not cached")
    def test_pinned_real_window_move_d0_i0_agree_without_ground_truth(self):
        """Trusted manual oracle, *not* an LLM result or official score."""
        from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
        from src.data.pilot_asset_audit import _files_in_root
        root=SOURCE.parents[3]
        records={t["task_id"]:t for t in read_tasks(root/"data/tasks.jsonl")}
        task=records["WIN-UPD-DIR-A-002"]
        rel=repo_asset_path(task["input_ifc"])
        source=_files_in_root(root/"data/ifc",rel)
        if not source.is_file():
            self.skipTest("Pinned original IFC input not cached")
        tree=json.loads((root/"data/bim_edit_remote_tree.json").read_text(encoding="utf8"))
        remote={v["path"]:v for v in tree if v.get("type")=="file"}
        verify_local_asset_bytes(source,remote[rel])
        original=source.read_bytes()
        original_hash=hashlib.sha256(original).hexdigest()
        source_ifc=ifcopenshell.open(str(source))
        target=source_ifc.by_guid(task["target"]["guids"][0])
        self.assertTrue(target.is_a("IfcWindow"))
        opening=target.FillsVoids[0].RelatingOpeningElement
        orig_rels=native_topology_inventory(source_ifc)
        before=np.asarray(ifcopenshell.util.placement.get_local_placement(
            target.ObjectPlacement)[:3,3])
        projection=project_ifc(source)
        doc=etree.fromstring(projection.xml)
        matching=[n for n in doc.iter() if isinstance(n.tag,str)
                  and n.get("ifcGuid")==opening.GlobalId]
        self.assertEqual(len(matching),1)
        before_offset=Decimal(matching[0].get("offset"))
        matching[0].set("offset",str(before_offset+Decimal("1")))
        edited=etree.tostring(doc,encoding="utf-8",xml_declaration=True)
        with TemporaryDirectory(prefix="fixed-public-source-own-oracle-") as temp:
            d=Path(temp)
            direct=d/"D0.ifc"; imperative=d/"I0.ifc"
            report=compile_declarative_xml(source,edited,direct)
            self.assertEqual([op.operation for op in report.operations],
                             ["MOVE_OPENING_WITH_FILLING"])
            manual_ifc_reference(source,imperative,"MOVE_OPENING",
                                 target_guid=opening.GlobalId,delta_x=1.)
            result=ifcopenshell.open(str(direct))
            after=np.asarray(ifcopenshell.util.placement.get_local_placement(
                result.by_guid(target.GlobalId).ObjectPlacement)[:3,3])
            self.assertTrue(np.allclose(after-before,(0.,1.,0.),atol=1e-6))
            self.assertEqual(orig_rels,native_topology_inventory(result))
            parity=parity_report(direct,imperative)
            self.assertTrue(parity["parity"],str(parity))
            self.assertEqual(report.unexpected_root_changes,())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)

    @unittest.skipUnless((SOURCE.parents[3]/"data/tasks.jsonl").is_file(),
                         "Pinned task metadata not cached")
    def test_real_source_window_move_into_adjacent_void_is_denied(self):
        """A real rotated 3D profile must not bypass the overlap preflight."""
        from src.data.bim_edit import read_tasks,repo_asset_path
        from src.data.pilot_asset_audit import _files_in_root
        from src.runtime.compiler import CompilerError
        root=SOURCE.parents[3]
        records={t["task_id"]:t for t in read_tasks(root/"data/tasks.jsonl")}
        task=records["WIN-UPD-DIR-A-002"]
        source=_files_in_root(root/"data/ifc",repo_asset_path(task["input_ifc"]))
        if not source.is_file():
            self.skipTest("Pinned original IFC input not cached")
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        f=ifcopenshell.open(str(source))
        opening=f.by_guid(task["target"]["guids"][0]).FillsVoids[0].RelatingOpeningElement
        xml=etree.fromstring(project_ifc(source).xml)
        match=[n for n in xml.iter() if isinstance(n.tag,str)
               and n.get("ifcGuid")==opening.GlobalId]
        self.assertEqual(len(match),1)
        # Real native other void occupies host x=2.8..3.4; proposed edited
        # void would occupy x=2.9..3.5. The candidate must not be emitted.
        match[0].set("offset","3.5")
        edit=etree.tostring(xml,encoding="utf8",xml_declaration=True)
        with TemporaryDirectory(prefix="reject-real-void-overlap-") as temp:
            output=Path(temp)/"invalid.ifc"
            with self.assertRaisesRegex(CompilerError,"overlap"):
                compile_declarative_xml(source,edit,output)
            self.assertFalse(output.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)


    def test_shared_opening_placement_point_fails_before_any_mutation(self):
        with TemporaryDirectory(prefix="own-shared-placement-") as folder:
            path=Path(folder)/"shared.ifc"
            f=ifcopenshell.open(str(SOURCE))
            window_opening=next(o for o in f.by_type("IfcOpeningElement")
                                if o.Name=="Window Opening")
            another=next(o for o in f.by_type("IfcOpeningElement")
                         if o.GlobalId!=window_opening.GlobalId)
            another.ObjectPlacement.RelativePlacement.Location=(
                window_opening.ObjectPlacement.RelativePlacement.Location)
            f.write(str(path))
            model=ifcopenshell.open(str(path))
            candidate=model.by_guid(window_opening.GlobalId)
            before=path.read_bytes()
            with self.assertRaisesRegex(UnsupportedIFCMutation,"shared/unexpected"):
                _validate_opening_move_preflight(
                    model,candidate,{"offset":2.1,"width":1.2},
                    model.by_type("IfcOpeningElement"),source_offset=1.6)
            self.assertEqual(before,path.read_bytes())


if __name__=="__main__":
    unittest.main()
