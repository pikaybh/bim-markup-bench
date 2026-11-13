"""Experimental-only v0.2 native IfcColumn D0 independent regression controls."""
from __future__ import annotations

import tempfile
from pathlib import Path
import os
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.ifc_projection import project_ifc
from src.runtime.compiler import compile_declarative_xml,CompilerError
from src.runtime.experimental_v2_column import (
    compile_declarative_xml_v2,V2ColumnError,_world_bbox,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",r"D:\문서\D__1_Projects\202611"))
ROOT=Path(__file__).resolve().parents[1]
SYN=ROOT/"tests"/"fixtures"/"synthetic"/"input.ifc"
BASIC=BASE/"bibimbap-author-data"/"ifc"/"basic_tasks.ifc"

def xml_with_column(src:Path, *, identifier:str="fixture_column_v2",
                    params:dict|None=None,level_index:int=0)->bytes:
    xml=project_ifc(src).xml
    root=etree.fromstring(xml)
    ns=etree.QName(root).namespace
    levels=root.find("{"+ns+"}Levels")
    all_params={"id":identifier,"level":levels[level_index].get("id"),
                "x":"12","y":"8","z":"0","width":"0.4","depth":"0.3","height":"3"}
    all_params.update(params or {})
    etree.SubElement(root.find("{"+ns+"}Elements"),"{"+ns+"}Column",attrib=all_params)
    return etree.tostring(root,encoding="utf8",xml_declaration=True)

class ColumnV2CompilerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="bibi118-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.original_bytes=SYN.read_bytes()
        self.addCleanup(lambda:self.assertEqual(SYN.read_bytes(),self.original_bytes))
        self.source=SYN

    def test_old_v01_remains_rejecting_column_creation(self):
        old=self.root/"must_not_exist.ifc"
        xml=xml_with_column(self.source)
        with self.assertRaisesRegex(CompilerError,"Only creation of a new standalone Wall"):
            compile_declarative_xml(self.source,xml,old)
        self.assertFalse(old.exists())

    def test_new_v02_real_native_ifc_column_geometry_and_persistence(self):
        dest=self.root/"created.ifc"
        report=compile_declarative_xml_v2(self.source,xml_with_column(self.source),dest)
        self.assertTrue(dest.exists())
        self.assertEqual([x.operation for x in report.operations],["CREATE_COLUMN"])
        self.assertEqual(report.as_dict()["status"],"COMMITTED_SCOPED_IFC4X3_COLUMN_CREATE_V2")
        self.assertFalse(report.as_dict()["general_bim_edit_45_supported"])
        a=ifcopenshell.open(str(self.source));b=ifcopenshell.open(str(dest))
        self.assertEqual(len(b.by_type("IfcColumn")),len(a.by_type("IfcColumn"))+1)
        created=b.by_guid(report.operations[0].ifc_guid)
        self.assertTrue(created.is_a("IfcColumn"))
        mini,maxi=_world_bbox(created)
        for x,y in zip(mini,(12.,8.,0.)):
            self.assertAlmostEqual(x,y,places=5)
        for x,y in zip(maxi,(12.4,8.3,3.)):
            self.assertAlmostEqual(x,y,places=5)
        self.assertTrue(created.ContainedInStructure)
        self.assertEqual(file_hash(self.source),file_hash(SYN))

    def test_negative_dimensions_range_and_nonfinite(self):
        for name,value in (("width","0"),("depth","-1"),("height","0"),
                           ("width","0.0001"),("height","200"),
                           ("x","1000000000000")):
            with self.subTest(name=name,value=value):
                dest=self.root/(name+"_"+value.replace("-","n")+".ifc")
                with self.assertRaises(Exception):
                    compile_declarative_xml_v2(self.source,
                        xml_with_column(self.source,params={name:value}),dest)
                self.assertFalse(dest.exists())

    def test_negative_nonzero_storey_without_safe_frame_mapping(self):
        if not BASIC.is_file():
            self.skipTest("Pinned public original BIM file not present")
        model=ifcopenshell.open(str(BASIC))
        normalized=self.root/"basic_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(model,"METER").write(str(normalized))
        root=etree.fromstring(project_ifc(normalized).xml)
        ns=etree.QName(root).namespace
        levels=root.find("{"+ns+"}Levels")
        l=next(x for x in levels if float(x.get("elevation"))>0)
        etree.SubElement(root.find("{"+ns+"}Elements"),"{"+ns+"}Column",attrib={
            "id":"bad_nonzero_storey","level":l.get("id"),"x":"12","y":"8",
            "z":"0","width":"0.3","depth":"0.3","height":"3",
        })
        dest=self.root/"not_committed.ifc"
        with self.assertRaisesRegex(V2ColumnError,"zero-elevation storey"):
            compile_declarative_xml_v2(normalized,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_negative_two_columns_not_supported_transaction(self):
        xml=xml_with_column(self.source)
        root=etree.fromstring(xml);ns=etree.QName(root).namespace
        elem=root.find("{"+ns+"}Elements")
        original=next(x for x in elem if etree.QName(x).localname=="Column"
                      and x.get("id")=="fixture_column_v2")
        extra=etree.fromstring(etree.tostring(original))
        extra.set("id","another_column")
        extra.set("x","20")
        elem.append(extra)
        dest=self.root/"not_committed.ifc"
        with self.assertRaisesRegex(V2ColumnError,"single new native Column"):
            compile_declarative_xml_v2(self.source,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_negative_column_plus_other_wall_edit_not_silently_accepted(self):
        root=etree.fromstring(xml_with_column(self.source))
        ns=etree.QName(root).namespace
        existing=next(x for x in root.find("{"+ns+"}Elements")
                      if etree.QName(x).localname=="Wall")
        existing.set("height",str(float(existing.get("height"))+0.5))
        dest=self.root/"not_committed.ifc"
        with self.assertRaisesRegex(V2ColumnError,"isolated"):
            compile_declarative_xml_v2(self.source,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_negative_source_hash_tampering(self):
        root=etree.fromstring(xml_with_column(self.source))
        root.set("sourceModelSha256","0"*64)
        dest=self.root/"not_committed.ifc"
        with self.assertRaises(Exception):
            compile_declarative_xml_v2(self.source,etree.tostring(root),dest)
        self.assertFalse(dest.exists())

    def test_positive_real_public_basic_ifc_native_column_D0(self):
        if not BASIC.is_file():
            self.skipTest("Public original IFC not present")
        original_hash=file_hash(BASIC)
        model=ifcopenshell.open(str(BASIC))
        self.assertEqual(model.schema,"IFC4X3")
        source=self.root/"basic_normalized_m.ifc"
        ifcopenshell.util.unit.convert_file_length_units(model,"METER").write(str(source))
        root=etree.fromstring(project_ifc(source).xml)
        ns=etree.QName(root).namespace
        lvl=next(x for x in root.find("{"+ns+"}Levels") if x.get("elevation")=="0")
        etree.SubElement(root.find("{"+ns+"}Elements"),"{"+ns+"}Column",attrib={
            "id":"bibi118_public_basic_fixed_D0",
            "level":lvl.get("id"),"x":"12","y":"8","z":"0",
            "width":"0.3","depth":"0.3","height":"3",
        })
        dest=self.root/"native_result.ifc"
        report=compile_declarative_xml_v2(source,etree.tostring(root),dest)
        f=ifcopenshell.open(str(dest))
        self.assertEqual(len(f.by_type("IfcColumn")),
                         len(ifcopenshell.open(str(source)).by_type("IfcColumn"))+1)
        created=f.by_guid(report.operations[0].ifc_guid)
        self.assertEqual([round(v,5) for v in _world_bbox(created)[0]],[12,8,0])
        self.assertEqual([round(v,5) for v in _world_bbox(created)[1]],[12.3,8.3,3])
        self.assertEqual(file_hash(BASIC),original_hash)

if __name__=="__main__":
    unittest.main()
