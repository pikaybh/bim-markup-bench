"""Actual IFC4X3 wall thickness/mesh tests and unsupported geometry controls."""
from __future__ import annotations
import tempfile
from decimal import Decimal
from pathlib import Path
import unittest

import ifcopenshell
import ifcopenshell.geom
from lxml import etree as ET

from src.runtime.compiler import CompilerError, compile_declarative_xml
from src.runtime.geometry_ops import (
    UnsupportedIFCMutation, edit_wall_thickness, wall_thickness_eligibility
)
from src.runtime.ifc_projection import project_ifc,_body_extrusion,_rect_extents
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"

def prepare_free_wall(tmp:Path)->tuple[Path,str]:
    source_projection=project_ifc(SOURCE)
    level=parse_xml(source_projection.xml).levels[0].id
    new=b'<Wall id="free_thickness_wall" level="'+level.encode()+b'" x1="0" y1="5" z1="0" x2="4" y2="5" z2="0" height="3" thickness="0.2"/>'
    authored=source_projection.xml.replace(b"<Elements>",b"<Elements>\n"+new)
    output=tmp/"free_wall_source.ifc"
    first=compile_declarative_xml(SOURCE,authored,output)
    return output,first.operations[0].ifc_guid

def edit_wall_xml(source:Path,guid:str,thickness:str)->bytes:
    projection=project_ifc(source)
    root=ET.fromstring(projection.xml)
    wall=next(e for e in root.xpath('//*[local-name()="Wall"]') if e.get("ifcGuid")==guid)
    wall.set("thickness",thickness)
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def wall_mesh_y_span(model:ifcopenshell.file,guid:str)->float:
    wall=model.by_guid(guid)
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    mesh=ifcopenshell.geom.create_shape(settings,wall)
    vertices=list(mesh.geometry.verts)
    ys=vertices[1::3]
    return max(ys)-min(ys)

class WallParametricThicknessTests(unittest.TestCase):
    def test_real_thickness_changes_ifc_parametric_profile_and_mesh(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            source,guid=prepare_free_wall(tmp)
            source_bytes=source.read_bytes()
            a=ifcopenshell.open(str(source))
            before_mesh_span=wall_mesh_y_span(a,guid)
            original_rect=_rect_extents(_body_extrusion(a.by_guid(guid)).SweptArea)
            self.assertAlmostEqual(original_rect[3]-original_rect[1],0.2)
            edited=edit_wall_xml(source,guid,"0.35")
            dest=tmp/"thickness_updated.ifc"
            result=compile_declarative_xml(source,edited,dest)
            b=ifcopenshell.open(str(dest))
            changed_profile=_body_extrusion(b.by_guid(guid)).SweptArea
            output_rect=_rect_extents(changed_profile)
            self.assertAlmostEqual(output_rect[3]-output_rect[1],0.35,places=6)
            self.assertAlmostEqual(wall_mesh_y_span(b,guid)-before_mesh_span,0.15,places=6)
            self.assertEqual([op.operation for op in result.operations],
                ["UPDATE_WALL_THICKNESS"])
            self.assertEqual(result.unexpected_root_changes,())
            self.assertGreaterEqual(result.untouched_root_objects_verified,20)
            self.assertEqual(source.read_bytes(),source_bytes)
            self.assertNotEqual(result.source_graph_fingerprint,result.result_graph_fingerprint)

    def test_nontrivial_wall_thickness_change_zero_or_negative_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source,guid=prepare_free_wall(Path(temp))
            for bad in ("0","-0.2","1001"):
                with self.subTest(thickness=bad):
                    dest=Path(temp)/("bad"+bad.replace("-","n")+".ifc")
                    with self.assertRaises((CompilerError,ValueError)):
                        compile_declarative_xml(source,edit_wall_xml(source,guid,bad),dest)
                    self.assertFalse(dest.exists())

    def test_existing_hosted_wall_cannot_be_thickened_without_void_propagation(self):
        before=SOURCE.read_bytes()
        p=project_ifc(SOURCE)
        root=ET.fromstring(p.xml)
        wall=next(e for e in root.xpath('//*[local-name()="Wall"]'))
        wall.set("thickness","0.3")
        xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/"unsafe_thickness.ifc"
            with self.assertRaisesRegex(CompilerError,"dependencies"):
                compile_declarative_xml(SOURCE,xml,dest)
            self.assertFalse(dest.exists())
        self.assertEqual(before,SOURCE.read_bytes())

    def test_thickness_staged_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            source,guid=prepare_free_wall(tmp)
            dest=tmp/"occupied.ifc"
            dest.write_bytes(b"existing")
            with self.assertRaises(CompilerError):
                compile_declarative_xml(source,edit_wall_xml(source,guid,"0.4"),dest)
            self.assertEqual(dest.read_bytes(),b"existing")

    def test_noop_numerical_format_preserves_exact_ifc(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            source,guid=prepare_free_wall(tmp)
            xml=edit_wall_xml(source,guid,"0.200")
            out=tmp/"same.ifc"
            report=compile_declarative_xml(source,xml,out)
            self.assertEqual(out.read_bytes(),source.read_bytes())
            self.assertEqual(report.operations,())

    def test_geometry_operations_do_not_leak_ifc_writer_to_model(self):
        self.assertNotIn(b"create_wall",project_ifc(SOURCE).xml)
        self.assertNotIn(b"openai",project_ifc(SOURCE).xml.lower())

    def test_direct_geometry_helper_refuses_host(self):
        model=ifcopenshell.open(str(SOURCE))
        wall=model.by_type("IfcWall")[0]
        with self.assertRaisesRegex(UnsupportedIFCMutation,"dependencies"):
            wall_thickness_eligibility(model,wall)
        with self.assertRaises(UnsupportedIFCMutation):
            edit_wall_thickness(model,wall,Decimal("0.35"))

if __name__=="__main__":unittest.main()
