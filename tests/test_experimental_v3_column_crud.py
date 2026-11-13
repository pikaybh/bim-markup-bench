"""Genuine native IFC positive/negative evidence for prospective Column v0.3.

No paid LLM calls; controlled D0 fixtures use *public* input IFC only.
Existing v0.1/v0.2 and historical model results are never rewritten.
"""
from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v3_projection import project_ifc_v3
from src.runtime.experimental_v3_column import (
    ColumnV3Error,compile_declarative_xml_v3,_world_bbox,
    _delete_preservation,_unchanged_after_update,_placement_point,
)
from src.runtime.experimental_v2_column import compile_declarative_xml_v2
from src.runtime.ifc_projection import project_ifc
from tools.bibimbap_matched25_tools import file_hash
from tools.oracle_bibimbap_column15_16_native import (
    NativeColumnOracleError,strict_move_column,strict_delete_column,
)


BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=BASE/"bibimbap-author-data"/"ifc"/"basic_tasks.ifc"
SYN=ROOT/"tests"/"fixtures"/"synthetic"/"input.ifc"
NS="{urn:bim-markup-bench:toy:v0}"
COL_MOVE="22hyxvAPr65PFt9WZfHSMu"
COL_DELETE="22hyxvAPr65PFt9WZfHS2x"


def by_guid(root,guid):
    return next(x for x in root.findall(".//"+NS+"Column")
                if x.get("ifcGuid")==guid)


def edited_xml(source, guid, *, field=None, delta=None, delete=False):
    root=etree.fromstring(project_ifc_v3(source).xml)
    col=by_guid(root,guid)
    if delete:
        col.getparent().remove(col)
    else:
        col.set(field,str(float(col.get(field))+delta))
    return etree.tostring(root,encoding="utf8",xml_declaration=True)


@unittest.skipUnless(PUBLIC.is_file(),"Pinned original BIBIMBAP public file missing")
class RealMappedColumnTests(unittest.TestCase):
    def setUp(self):
        scratch=tempfile.TemporaryDirectory(prefix="bibi120-mapped-column-")
        self.addCleanup(scratch.cleanup)
        self.temp=Path(scratch.name)
        self.original_sha=file_hash(PUBLIC)
        self.addCleanup(lambda:self.assertEqual(file_hash(PUBLIC),self.original_sha))
        file=ifcopenshell.open(str(PUBLIC))
        self.source=self.temp/"source_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(file,"METER").write(str(self.source))
        self.source_sha=file_hash(self.source)
        self.addCleanup(lambda:self.assertEqual(file_hash(self.source),self.source_sha))

    def test_ten_real_original_mapped_columns_become_read_only_envelopes(self):
        prev=project_ifc(self.source)
        projection=project_ifc_v3(self.source)
        self.assertEqual(dict(prev.unsupported_class_counts)["IfcColumn"],10)
        self.assertEqual(dict(projection.supported_class_counts)["IfcColumn"],10)
        self.assertEqual(len(etree.fromstring(projection.xml).findall(".//"+NS+"Column")),10)
        f=ifcopenshell.open(str(self.source))
        for box in etree.fromstring(projection.xml).findall(".//"+NS+"Column"):
            low,high=_world_bbox(f.by_guid(box.get("ifcGuid")))
            for actual,expected in zip(low,tuple(float(box.get(c)) for c in ("x","y","z"))):
                self.assertAlmostEqual(actual,expected,places=5)
            for actual,expected in zip(
                tuple(high[i]-low[i] for i in range(3)),
                tuple(float(box.get(c)) for c in ("width","depth","height"))
            ):
                self.assertAlmostEqual(actual,expected,places=5)

    def test_move_real_original_column_only_one_placement_point_changes(self):
        f=ifcopenshell.open(str(self.source))
        col=f.by_guid(COL_MOVE)
        before=_world_bbox(col)
        point_id=_placement_point(f,col).id()
        other_bboxes={c.GlobalId:_world_bbox(c) for c in f.by_type("IfcColumn")
                      if c.GlobalId!=COL_MOVE}
        dst=self.temp/"moved.ifc"
        report=compile_declarative_xml_v3(
            self.source,edited_xml(self.source,COL_MOVE,field="y",delta=-3),dst)
        self.assertEqual([x.operation for x in report.operations],["MOVE_COLUMN"])
        self.assertEqual(report.as_dict()["status"],"COMMITTED_SCOPED_IFC4X3_MOVE_COLUMN_V3")
        self.assertFalse(report.as_dict()["general_bim_edit_45_supported"])
        after=ifcopenshell.open(str(dst))
        end=_world_bbox(after.by_guid(COL_MOVE))
        for i in range(3):
            change=-3.0 if i==1 else 0
            self.assertAlmostEqual(end[0][i]-before[0][i],change,places=5)
            self.assertAlmostEqual(end[1][i]-before[1][i],change,places=5)
        self.assertEqual(other_bboxes,{
            c.GlobalId:_world_bbox(c) for c in after.by_type("IfcColumn")
            if c.GlobalId!=COL_MOVE
        })
        self.assertGreater(_unchanged_after_update(self.source,dst,COL_MOVE,point_id),10)
        independent=strict_move_column(self.source,dst,COL_MOVE,dy=-3.)
        self.assertEqual(independent["changed_native_step_entity_count"],1)
        with self.assertRaises(NativeColumnOracleError):
            strict_move_column(self.source,dst,COL_MOVE,dy=+3.)

    def test_delete_real_original_column_preserves_other_natives(self):
        f=ifcopenshell.open(str(self.source))
        other_bboxes={c.GlobalId:_world_bbox(c) for c in f.by_type("IfcColumn")
                      if c.GlobalId!=COL_DELETE}
        dst=self.temp/"deleted.ifc"
        report=compile_declarative_xml_v3(
            self.source,edited_xml(self.source,COL_DELETE,delete=True),dst)
        self.assertEqual([x.operation for x in report.operations],["DELETE_COLUMN"])
        self.assertEqual(report.as_dict()["status"],"COMMITTED_SCOPED_IFC4X3_DELETE_COLUMN_V3")
        after=ifcopenshell.open(str(dst))
        self.assertEqual(len(after.by_type("IfcColumn")),9)
        with self.assertRaises(RuntimeError):
            after.by_guid(COL_DELETE)
        self.assertEqual(other_bboxes,{
            c.GlobalId:_world_bbox(c) for c in after.by_type("IfcColumn")
        })
        self.assertGreater(_delete_preservation(self.source,dst,COL_DELETE),50)
        independent=strict_delete_column(self.source,dst,COL_DELETE)
        self.assertEqual(independent["preserved_original_other_columns"],9)
        with self.assertRaises(NativeColumnOracleError):
            strict_delete_column(self.source,dst,COL_MOVE)

    def test_fail_closed_mapped_type_height_not_direct_solid(self):
        dest=self.temp/"mapped_height_no.ifc"
        with self.assertRaisesRegex(ColumnV3Error,"unshared direct extrusion"):
            compile_declarative_xml_v3(
                self.source,edited_xml(self.source,COL_MOVE,field="height",delta=0.5),dest)
        self.assertFalse(dest.exists())

    def test_fail_closed_unrelated_width_or_size_changes(self):
        for fld in ("width","depth"):
            dst=self.temp/(fld+"_bad.ifc")
            with self.assertRaisesRegex(ColumnV3Error,"world xyz translation OR direct solid height"):
                compile_declarative_xml_v3(
                    self.source,edited_xml(self.source,COL_MOVE,field=fld,delta=.25),dst)
            self.assertFalse(dst.exists())

    def test_fail_closed_mixed_two_columns(self):
        root=etree.fromstring(project_ifc_v3(self.source).xml)
        by_guid(root,COL_MOVE).set("y","-8.1")
        by_guid(root,COL_DELETE).getparent().remove(by_guid(root,COL_DELETE))
        dst=self.temp/"mixed.ifc"
        with self.assertRaisesRegex(ColumnV3Error,"Only one existing Column"):
            compile_declarative_xml_v3(self.source,etree.tostring(root),dst)
        self.assertFalse(dst.exists())

    def test_fail_closed_unhandled_delete_dependency(self):
        file=ifcopenshell.open(str(self.source))
        column=file.by_guid(COL_DELETE)
        wall=file.by_type("IfcWall")[0]
        file.create_entity("IfcRelConnectsElements",
                          GlobalId=ifcopenshell.guid.new(),
                          RelatingElement=column,RelatedElement=wall)
        new_source=self.temp/"with_dependency.ifc"
        file.write(str(new_source))
        dst=self.temp/"unallowed.ifc"
        with self.assertRaisesRegex(ColumnV3Error,"unhandled native inverse dependency"):
            compile_declarative_xml_v3(new_source,
                                       edited_xml(new_source,COL_DELETE,delete=True),dst)
        self.assertFalse(dst.exists())

    def test_fail_closed_result_tampering_other_column_metadata(self):
        dst=self.temp/"moved.ifc"
        compile_declarative_xml_v3(
            self.source,edited_xml(self.source,COL_MOVE,field="y",delta=-3),dst)
        file=ifcopenshell.open(str(dst))
        file.by_guid(COL_DELETE).Name="Unrelated column was also changed"
        corrupted=self.temp/"corrupted.ifc"
        file.write(str(corrupted))
        source_model=ifcopenshell.open(str(self.source))
        point_id=_placement_point(source_model,source_model.by_guid(COL_MOVE)).id()
        with self.assertRaisesRegex(ColumnV3Error,"non-target IFC STEP data"):
            _unchanged_after_update(self.source,corrupted,COL_MOVE,point_id)
        with self.assertRaises(NativeColumnOracleError):
            strict_move_column(self.source,corrupted,COL_MOVE,dy=-3.)

    def test_fail_closed_result_tampering_other_product_after_delete(self):
        dst=self.temp/"deleted.ifc"
        compile_declarative_xml_v3(
            self.source,edited_xml(self.source,COL_DELETE,delete=True),dst)
        file=ifcopenshell.open(str(dst))
        file.by_guid(COL_MOVE).Name="Unrelated surviving column damaged"
        corrupted=self.temp/"corrupted.ifc"
        file.write(str(corrupted))
        with self.assertRaisesRegex(ColumnV3Error,"Unrelated original IFC Root"):
            _delete_preservation(self.source,corrupted,COL_DELETE)
        with self.assertRaises(NativeColumnOracleError):
            strict_delete_column(self.source,corrupted,COL_DELETE)

    def test_fail_closed_bad_source_hash_and_noop(self):
        root=etree.fromstring(project_ifc_v3(self.source).xml)
        dst=self.temp/"noop.ifc"
        with self.assertRaisesRegex(ColumnV3Error,"Only one existing Column"):
            compile_declarative_xml_v3(self.source,etree.tostring(root),dst)
        self.assertFalse(dst.exists())
        root.set("sourceModelSha256","f"*64)
        with self.assertRaises(Exception):
            compile_declarative_xml_v3(self.source,etree.tostring(root),dst)
        self.assertFalse(dst.exists())


class SyntheticDirectColumnHeightTests(unittest.TestCase):
    def setUp(self):
        scratch=tempfile.TemporaryDirectory(prefix="bibi120-synthetic-column-")
        self.addCleanup(scratch.cleanup)
        self.temp=Path(scratch.name)
        self.original_hash=file_hash(SYN)
        self.addCleanup(lambda:self.assertEqual(file_hash(SYN),self.original_hash))
        self.source=SYN
        f=ifcopenshell.open(str(SYN))
        self.guid=f.by_type("IfcColumn")[0].GlobalId

    def test_height_updates_only_native_extruded_solid(self):
        file=ifcopenshell.open(str(self.source))
        before=_world_bbox(file.by_guid(self.guid))
        solid=next(item for rep in file.by_guid(self.guid).Representation.Representations
                   for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
        dst=self.temp/"height_changed.ifc"
        report=compile_declarative_xml_v3(
            self.source,edited_xml(self.source,self.guid,field="height",delta=.5),dst)
        self.assertEqual(report.as_dict()["status"],"COMMITTED_SCOPED_IFC4X3_UPDATE_COLUMN_HEIGHT_V3")
        self.assertFalse(report.as_dict()["general_bim_edit_45_supported"])
        after=ifcopenshell.open(str(dst))
        now=_world_bbox(after.by_guid(self.guid))
        self.assertAlmostEqual(now[1][2]-before[1][2],.5,places=5)
        self.assertEqual(now[0],before[0])
        self.assertGreater(_unchanged_after_update(self.source,dst,self.guid,solid.id()),10)

    def test_negative_height_stays_positive(self):
        dst=self.temp/"invalid.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v3(
                self.source,edited_xml(self.source,self.guid,field="height",delta=-4),dst)
        self.assertFalse(dst.exists())


if __name__=="__main__":
    unittest.main()
