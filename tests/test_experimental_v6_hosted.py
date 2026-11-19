"""Original public BIBIMBAP IFC hosted v0.6: native positives & fail-closed negatives.

No paid model calls. Developer-fixed source edits must not be scored as GPT.
Independent oracle is separate from trusted declarative compiler.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v4_projection import project_ifc_v4
from src.runtime.experimental_v6_hosted import (
    compile_declarative_xml_v6,HostedV6Error,
)
from tools.oracle_bibimbap_hosted_v06 import (
    verify_hosted_pair_delete,verify_hosted_move,IndependentHostedV6Error,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
BASIC=DATA/"basic_tasks.ifc"
WINDOWS=DATA/"01"/"01"/"01_01_013.ifc"
DOORS=DATA/"01"/"01"/"01_01_016.ifc"
TOPO_WINDOWS=DATA/"01"/"02"/"01_02_013.ifc"
NS="{urn:bim-markup-bench:toy:v0}"
DOOR_BASIC="11kJIqz$n2Jf_DfJV1SDY7"
OPEN_BASIC="0APGbZXNKfgPNB$VQQZ0pi"
WINDOW_BASIC="11kJIqz$n2Jf_DfJV1SDbS"
OPEN_BASIC_DOOR="1U$$kq6emLyOkmIlVkRzzn"
GEO13_WINDOW_WIDE="2KbOAL4v52mv2YJ6fTql5A"
GEO13_WIDE_OPENING="2FgYNxuD5JBSJ92imotdSQ"
GEO16_MIDDLE="1g0NIEjcH1lfGqbYWRqt6L"
TOPO13_TARGET_WINDOW="0HbU4cYqD2SBtSJYoQ_eW1"


def xml_by_guid(tree,guid):
    return next(x for x in tree.find(NS+"Elements") if x.get("ifcGuid")==guid)


def remove_dependent_pair(tree,model,fill_guid):
    filler=model.by_guid(fill_guid)
    opening_guid=filler.FillsVoids[0].RelatingOpeningElement.GlobalId
    elements=tree.find(NS+"Elements")
    for guid in (fill_guid,opening_guid):
        elements.remove(xml_by_guid(tree,guid))
    return opening_guid


def set_opening_offset(tree,opening_guid,change):
    node=xml_by_guid(tree,opening_guid)
    original=float(node.get("offset"))
    node.set("offset",str(original+change))


def xml_bytes(tree):
    return etree.tostring(tree,encoding="utf8",xml_declaration=True)


class OriginalHostedV6Fixture(unittest.TestCase):
    def make_source(self,rel):
        data=DATA/rel
        if not data.exists():
            self.skipTest("Original public IFC4X3 data absent")
        folder=tempfile.TemporaryDirectory(prefix="bibi126-hosted-v6-")
        self.addCleanup(folder.cleanup)
        d=Path(folder.name)
        sha=file_hash(data)
        self.addCleanup(lambda:self.assertEqual(file_hash(data),sha))
        initial=ifcopenshell.open(str(data))
        source=d/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(initial,"METER").write(str(source))
        source_hash=file_hash(source)
        self.addCleanup(lambda:self.assertEqual(file_hash(source),source_hash))
        tree=etree.fromstring(project_ifc_v4(source).xml)
        return d,source,ifcopenshell.open(str(source)),tree


class NativePositiveHostedV6Tests(OriginalHostedV6Fixture):
    def test_original_basic_door_and_its_opening_removed_preserve_original_wall(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        opening=remove_dependent_pair(tree,f,DOOR_BASIC)
        self.assertEqual(opening,OPEN_BASIC_DOOR)
        dest=d/"deleted_pair.ifc"
        result=compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertEqual(result.operations[0].operation,"DELETE_HOSTED_FILLING_AND_OPENING")
        self.assertFalse(result.as_dict()["full_original_45_native_backend_parity"])
        proof=verify_hosted_pair_delete(source,dest,DOOR_BASIC,opening)
        self.assertTrue(proof["all_remaining_classification_relations_nonempty"])
        with self.assertRaises(IndependentHostedV6Error):
            verify_hosted_pair_delete(source,dest,WINDOW_BASIC,OPEN_BASIC)

    def test_original_basic_window_with_opening_delete_and_source_preserve(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        opening=remove_dependent_pair(tree,f,WINDOW_BASIC)
        dest=d/"window_pair_deleted.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        proof=verify_hosted_pair_delete(source,dest,WINDOW_BASIC,opening)
        self.assertEqual(proof["filling_guid_removed"],WINDOW_BASIC)
        after=ifcopenshell.open(str(dest))
        self.assertEqual(len(after.by_type("IfcWindow")),0)
        self.assertEqual(len(after.by_type("IfcDoor")),1)

    def test_original_geometry16_middle_door_pair_native_delete(self):
        d,source,f,tree=self.make_source(Path("01")/"01"/"01_01_016.ifc")
        opening=remove_dependent_pair(tree,f,GEO16_MIDDLE)
        dest=d/"middle_door_deleted.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        proof=verify_hosted_pair_delete(source,dest,GEO16_MIDDLE,opening)
        self.assertGreater(proof["original_other_ifc_products_preserved"],0)
        self.assertEqual(len(ifcopenshell.open(str(dest)).by_type("IfcDoor")),2)

    def test_original_geometry13_wide_window_and_opening_move_plus_world_x_three(self):
        d,source,f,tree=self.make_source(Path("01")/"01"/"01_01_013.ifc")
        set_opening_offset(tree,GEO13_WIDE_OPENING,3.)
        dest=d/"wide_window_moved.ifc"
        report=compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertEqual(report.operations[0].operation,"MOVE_FILLED_OPENING")
        proof=verify_hosted_move(
            source,dest,GEO13_WIDE_OPENING,delta_metres=3.,
            expected_filling_guid=GEO13_WINDOW_WIDE)
        self.assertEqual(proof["native_filling_guid"],GEO13_WINDOW_WIDE)
        with self.assertRaises(IndependentHostedV6Error):
            verify_hosted_move(
                source,dest,GEO13_WIDE_OPENING,delta_metres=-3.,
                expected_filling_guid=GEO13_WINDOW_WIDE)

    def test_original_basic_hosted_door_move_native_void_filling_both_move(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        set_opening_offset(tree,OPEN_BASIC_DOOR,.2)
        dest=d/"door_with_opening_moved.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        proof=verify_hosted_move(
            source,dest,OPEN_BASIC_DOOR,delta_metres=.2,
            expected_filling_guid=DOOR_BASIC)
        self.assertEqual(proof["native_filling_guid"],DOOR_BASIC)
        self.assertEqual(proof["world_delta_m"][0],-.2)

    def test_topological_original_window_move_native_geometry(self):
        d,source,f,tree=self.make_source(Path("01")/"02"/"01_02_013.ifc")
        opguid=f.by_guid(TOPO13_TARGET_WINDOW).FillsVoids[0].RelatingOpeningElement.GlobalId
        set_opening_offset(tree,opguid,.1)
        dest=d/"topo_window_moved.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        proof=verify_hosted_move(source,dest,opguid,delta_metres=.1,
                                 expected_filling_guid=TOPO13_TARGET_WINDOW)
        self.assertEqual(proof["world_delta_m"][1],-.1)


class NativeNegativeHostedV6Tests(OriginalHostedV6Fixture):
    def test_delete_only_door_with_opening_retained_must_reject(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        tree.find(NS+"Elements").remove(xml_by_guid(tree,DOOR_BASIC))
        dest=d/"door_only.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_delete_only_opening_with_filling_retained_must_reject(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        tree.find(NS+"Elements").remove(xml_by_guid(tree,OPEN_BASIC))
        dest=d/"opening_only.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_move_opening_without_filling_must_reject(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        empty="2v_dq1kqXwgUORGuwQrNAz"
        self.assertEqual(len(f.by_guid(empty).HasFillings),0)
        set_opening_offset(tree,empty,.1)
        dest=d/"unfilled.ifc"
        with self.assertRaisesRegex(HostedV6Error,"requires exactly one"):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_move_opening_overlapping_neighbor_fails_closed(self):
        d,source,f,tree=self.make_source(Path("01")/"01"/"01_01_013.ifc")
        # Wide Opening original [1.45,3.05]; neighboring narrow
        # [3.65,4.25]. Move by +1.0 -> [2.45,4.05] overlaps.
        set_opening_offset(tree,GEO13_WIDE_OPENING,1.)
        dest=d/"overlap.ifc"
        with self.assertRaisesRegex(Exception,"overlap"):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_move_opening_beyond_end_of_host_wall_fails_closed(self):
        d,source,f,tree=self.make_source(Path("01")/"01"/"01_01_013.ifc")
        set_opening_offset(tree,GEO13_WIDE_OPENING,100.)
        dest=d/"out_of_wall.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_multiple_unrelated_node_changes_cannot_be_silent(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        set_opening_offset(tree,OPEN_BASIC_DOOR,.1)
        set_opening_offset(tree,OPEN_BASIC,.1)
        dest=d/"two_openings.ifc"
        with self.assertRaisesRegex(HostedV6Error,"Only single Opening offset"):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_unrelated_wall_geometry_change_plus_door_delete_rejected(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        remove_dependent_pair(tree,f,DOOR_BASIC)
        wall=next(x for x in tree.findall(".//"+NS+"Wall"))
        wall.set("height",str(float(wall.get("height"))+.25))
        dest=d/"delete_and_wall_edit.ifc"
        with self.assertRaisesRegex(HostedV6Error,"Only single Opening offset"):
            compile_declarative_xml_v6(source,xml_bytes(tree),dest)
        self.assertFalse(dest.exists())

    def test_bad_source_hash_and_destination_no_overwrite(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        set_opening_offset(tree,OPEN_BASIC_DOOR,.2)
        bad=etree.fromstring(xml_bytes(tree))
        bad.set("sourceModelSha256","0"*64)
        output=d/"bad_hash.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v6(source,xml_bytes(bad),output)
        self.assertFalse(output.exists())
        output.write_bytes(b"Prior local research evidence")
        with self.assertRaisesRegex(HostedV6Error,"unused output"):
            compile_declarative_xml_v6(source,xml_bytes(tree),output)
        self.assertEqual(output.read_bytes(),b"Prior local research evidence")

    def test_noop_must_not_commit_candidate(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        out=d/"noop.ifc"
        with self.assertRaisesRegex(HostedV6Error,"Only single Opening offset"):
            compile_declarative_xml_v6(source,xml_bytes(tree),out)
        self.assertFalse(out.exists())

    def test_independent_oracle_rejects_unrelated_ifc_root_tampering(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        set_opening_offset(tree,OPEN_BASIC_DOOR,.2)
        good=d/"move.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),good)
        tampered=ifcopenshell.open(str(good))
        tampered.by_guid(DOOR_BASIC).Name="TAMPERED FILLING NAME"
        bad=d/"tampered.ifc"
        tampered.write(str(bad))
        with self.assertRaises(IndependentHostedV6Error):
            verify_hosted_move(source,bad,OPEN_BASIC_DOOR,delta_metres=.2,
                               expected_filling_guid=DOOR_BASIC)

    def test_independent_oracle_rejects_damaged_other_product_after_deletion(self):
        d,source,f,tree=self.make_source(Path("basic_tasks.ifc"))
        opening=remove_dependent_pair(tree,f,DOOR_BASIC)
        good=d/"delete.ifc"
        compile_declarative_xml_v6(source,xml_bytes(tree),good)
        tampered=ifcopenshell.open(str(good))
        tampered.by_guid(WINDOW_BASIC).Name="BROKEN UNRELATED WINDOW"
        bad=d/"tampered.ifc"
        tampered.write(str(bad))
        with self.assertRaises(IndependentHostedV6Error):
            verify_hosted_pair_delete(source,bad,DOOR_BASIC,opening)


if __name__=="__main__":
    unittest.main()
