"""Genuine IFC4X3 Wall v0.5 native D0 controls and fail-closed negatives.

All original BIBIMBAP data read only; zero model inference; never replace
original #112 model scores. Independent oracle checks native IFC geometry.
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
from src.runtime.experimental_v5_wall import (
    compile_declarative_xml_v5,WallV5Error,
)
from tools.oracle_bibimbap_wall_v05 import (
    NativeWallV5OracleError,verify_wall_pose_or_length,verify_wall_delete,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
BASIC=DATA/"basic_tasks.ifc"
SHORT_SRC=DATA/"01"/"02"/"01_02_012.ifc"
NS="{urn:bim-markup-bench:toy:v0}"
ROTATE_GUID="22hyxvAPr65PFt9WZfHSP3"
REMOVE_GUID="2UsXAbj6n0fwEWqdkVuHyn"
SHORT_GUID="2c8iwp2JP1ox_Asrwk4CZr"
CONNECTED_GUID="2UsXAbj6n0fwEWqdkVuHup"
HOSTED_GUID="2UsXAbj6n0fwEWqdkVuHvg"


def find_wall(tree,guid):
    return next(x for x in tree.findall(".//"+NS+"Wall")
                if x.attrib.get("ifcGuid")==guid)


def xml_state(tree):
    return etree.tostring(tree,encoding="utf8",xml_declaration=True)


def rotate90(tree,guid):
    wall=find_wall(tree,guid)
    x,y=float(wall.get("x1")),float(wall.get("y1"))
    xx,yy=float(wall.get("x2")),float(wall.get("y2"))
    wall.set("x2",str(x-(yy-y)))
    wall.set("y2",str(y+(xx-x)))


def shorten(tree,guid,metres=1.0):
    wall=find_wall(tree,guid)
    x,y=float(wall.get("x1")),float(wall.get("y1"))
    xx,yy=float(wall.get("x2")),float(wall.get("y2"))
    length=math.hypot(xx-x,yy-y)
    wall.set("x2",str(xx-metres*(xx-x)/length))
    wall.set("y2",str(yy-metres*(yy-y)/length))


def remove_wall(tree,guid,*,remove_graph_connections=True):
    wall=find_wall(tree,guid)
    localid=wall.get("id")
    wall.getparent().remove(wall)
    if remove_graph_connections:
        connections=tree.find(NS+"Relations")
        for e in list(connections):
            if e.get("from")==localid or e.get("to")==localid:
                connections.remove(e)


@unittest.skipUnless(BASIC.is_file(),"Pinned original public IFC4X3 BIBIMBAP basic source missing")
class RealOriginalWallV5Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="bibi124-wall-real-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.original_hash=file_hash(BASIC)
        self.addCleanup(lambda:self.assertEqual(file_hash(BASIC),self.original_hash))
        m=ifcopenshell.open(str(BASIC))
        self.source=self.root/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(m,"METER").write(str(self.source))
        self.source_hash=file_hash(self.source)
        self.addCleanup(lambda:self.assertEqual(file_hash(self.source),self.source_hash))

    def tree(self):
        return etree.fromstring(project_ifc_v4(self.source).xml)

    def test_original_public_wall_plus90_native_pose_and_independent_mesh(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        out=self.root/"rotated.ifc"
        result=compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertEqual(result.operations[0].operation,"ROTATE_WALL")
        self.assertFalse(result.as_dict()["full_45_task_capability_parity"])
        proof=verify_wall_pose_or_length(
            self.source,out,ROTATE_GUID,operation="rotate",angle_deg=90)
        self.assertEqual(proof["other_original_wall_meshes_unchanged"],15)
        with self.assertRaises(NativeWallV5OracleError):
            verify_wall_pose_or_length(
                self.source,out,ROTATE_GUID,operation="rotate",angle_deg=-90)

    def test_center_pivot_rotate_one_wall_native_geometry_without_author_grade(self):
        # A second, separate fixed engineering geometry test, not a
        # post-hoc change to original test_11 D0 scorer/pivot selection.
        tree=self.tree()
        wall=find_wall(tree,ROTATE_GUID)
        x,y=float(wall.get("x1")),float(wall.get("y1"))
        xx,yy=float(wall.get("x2")),float(wall.get("y2"))
        cx,cy=(x+xx)/2.,(y+yy)/2.
        for oldx,oldy,kx,ky in (
            (x,y,"x1","y1"),(xx,yy,"x2","y2")
        ):
            wall.set(kx,str(cx-(oldy-cy)))
            wall.set(ky,str(cy+(oldx-cx)))
        out=self.root/"center_rotated.ifc"
        result=compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertEqual(result.operations[0].operation,"ROTATE_WALL")
        proof=verify_wall_pose_or_length(
            self.source,out,ROTATE_GUID,operation="rotate",
            angle_deg=90.,rotation_pivot_xyz=(cx,cy,0.))
        self.assertEqual(proof["other_original_wall_meshes_unchanged"],15)
        with self.assertRaises(NativeWallV5OracleError):
            verify_wall_pose_or_length(
                self.source,out,ROTATE_GUID,operation="rotate",
                angle_deg=90.,rotation_pivot_xyz=(x,y,0.))

    def test_original_native_wall_translate_xy_preserving_all_other_meshes(self):
        tree=self.tree()
        wall=find_wall(tree,ROTATE_GUID)
        for key in ("x1","x2"):
            wall.set(key,str(float(wall.get(key))+2))
        out=self.root/"moved.ifc"
        result=compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertEqual(result.operations[0].operation,"MOVE_WALL")
        proof=verify_wall_pose_or_length(
            self.source,out,ROTATE_GUID,operation="move",shift_xyz=(2,0,0))
        self.assertEqual(proof["other_original_wall_meshes_unchanged"],15)

    def test_original_connected_wall_delete_safely_removes_paths(self):
        tree=self.tree()
        remove_wall(tree,REMOVE_GUID)
        out=self.root/"deleted.ifc"
        result=compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertEqual(result.operations[0].operation,"DELETE_WALL_WITH_SAFE_RELATIONS")
        self.assertFalse(result.as_dict()["full_hosted_wall_delete_support"])
        proof=verify_wall_delete(self.source,out,REMOVE_GUID)
        self.assertEqual(proof["other_original_wall_meshes_unchanged"],15)
        with self.assertRaises(NativeWallV5OracleError):
            verify_wall_delete(self.source,out,ROTATE_GUID)

    def test_negative_connected_wall_rotation_rejected(self):
        tree=self.tree()
        rotate90(tree,CONNECTED_GUID)
        out=self.root/"invalid_connected.ifc"
        with self.assertRaisesRegex(WallV5Error,"Connected Wall"):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_hosted_opening_wall_delete_fail_closed(self):
        tree=self.tree()
        # Remove all XML relation edges incident to a hosted wall to avoid
        # unrelated XML dangling edges; native preflight *still* must reject
        # unsafe hosted Opening/filled Door deletion.
        remove_wall(tree,HOSTED_GUID)
        out=self.root/"unsafe_hosted_delete.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_bad_source_hash(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        tree.set("sourceModelSha256","0"*64)
        out=self.root/"incorrect_source.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_wall_delete_with_dangling_connects(self):
        tree=self.tree()
        remove_wall(tree,REMOVE_GUID,remove_graph_connections=False)
        out=self.root/"dangling.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_mixed_wall_edit_not_silent(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        another=find_wall(tree,REMOVE_GUID)
        another.set("height",str(float(another.get("height"))+0.2))
        out=self.root/"mixed.ifc"
        with self.assertRaisesRegex(WallV5Error,"Exactly one native Wall edit"):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_height_and_plan_edit_combined_rejected(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        find_wall(tree,ROTATE_GUID).set("height","4.5")
        out=self.root/"mixed_same_wall.ifc"
        with self.assertRaisesRegex(WallV5Error,"Only planar wall endpoints"):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertFalse(out.exists())

    def test_negative_original_unmodified_state_rejected(self):
        out=self.root/"noop.ifc"
        with self.assertRaisesRegex(WallV5Error,"Exactly one native Wall edit"):
            compile_declarative_xml_v5(self.source,xml_state(self.tree()),out)
        self.assertFalse(out.exists())

    def test_negative_existing_output_refused_preserve_bytes(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        out=self.root/"no_overwrite.ifc"
        out.write_bytes(b"LOCAL RESEARCH EVIDENCE")
        with self.assertRaisesRegex(WallV5Error,"destination must be unused"):
            compile_declarative_xml_v5(self.source,xml_state(tree),out)
        self.assertEqual(out.read_bytes(),b"LOCAL RESEARCH EVIDENCE")

    def test_independent_oracle_rejects_unrelated_wall_metadata_mutation(self):
        tree=self.tree()
        rotate90(tree,ROTATE_GUID)
        out=self.root/"rotated.ifc"
        compile_declarative_xml_v5(self.source,xml_state(tree),out)
        file=ifcopenshell.open(str(out))
        file.by_guid(REMOVE_GUID).Name="Corrupt unrelated source Wall"
        damaged=self.root/"damaged.ifc"
        file.write(str(damaged))
        with self.assertRaises(NativeWallV5OracleError):
            verify_wall_pose_or_length(
                self.source,damaged,ROTATE_GUID,operation="rotate",angle_deg=90)


@unittest.skipUnless(SHORT_SRC.is_file(),"Pinned original public IFC topological_test_12 input absent")
class RealDetachedWallLengthTests(unittest.TestCase):
    def test_original_detached_wall_shortens_one_metre_and_other_products_preserved(self):
        with tempfile.TemporaryDirectory(prefix="bibi124-shortening-") as td:
            d=Path(td)
            original=file_hash(SHORT_SRC)
            m=ifcopenshell.open(str(SHORT_SRC))
            source=d/"source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(m,"METER").write(str(source))
            tree=etree.fromstring(project_ifc_v4(source).xml)
            shorten(tree,SHORT_GUID,metres=1.)
            out=d/"shortened.ifc"
            result=compile_declarative_xml_v5(source,xml_state(tree),out)
            self.assertEqual(result.operations[0].operation,"CHANGE_WALL_LENGTH")
            proof=verify_wall_pose_or_length(
                source,out,SHORT_GUID,operation="shorten",shorten_metres=1.)
            self.assertIn("IfcRectangleProfileDef",proof["changed_original_step_types"])
            with self.assertRaises(NativeWallV5OracleError):
                verify_wall_pose_or_length(
                    source,out,SHORT_GUID,operation="shorten",shorten_metres=0.5)
            self.assertEqual(file_hash(SHORT_SRC),original)

    def test_negative_shortening_not_in_original_direction_rejected(self):
        with tempfile.TemporaryDirectory(prefix="bibi124-wrong-direction-") as td:
            d=Path(td)
            m=ifcopenshell.open(str(SHORT_SRC))
            source=d/"source_m.ifc"
            ifcopenshell.util.unit.convert_file_length_units(m,"METER").write(str(source))
            tree=etree.fromstring(project_ifc_v4(source).xml)
            wall=find_wall(tree,SHORT_GUID)
            wall.set("x2",str(float(wall.get("x2"))+1))
            out=d/"invalid_geometry.ifc"
            with self.assertRaisesRegex(WallV5Error,"same start and direction"):
                compile_declarative_xml_v5(source,xml_state(tree),out)
            self.assertFalse(out.exists())


if __name__=="__main__":
    unittest.main()
