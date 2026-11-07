"""Independent native IFC topology checks for bounded declarative XML edits."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.util.placement
from lxml import etree as ET
import numpy as np

from src.runtime.compiler import compile_declarative_xml, CompilerError
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import native_topology_inventory
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
NS="urn:bim-markup-bench:toy:v0"

def source_xml():
    return project_ifc(SOURCE).xml

def build(xml:bytes, fn):
    root=ET.fromstring(xml)
    fn(root)
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def _elements(root):
    return root.find(".//{"+NS+"}Elements")

def _relations(root):
    return root.find(".//{"+NS+"}Relations")

def _one(root,kind,attrs=None):
    found=[x for x in root.iter() if isinstance(x.tag,str) and ET.QName(x).localname==kind
           and (attrs is None or all(x.get(k)==v for k,v in attrs.items()))]
    if len(found)!=1:
        raise AssertionError(f"Expected exactly one {kind}, found {len(found)}")
    return found[0]

def joined_wall_markup(xml):
    level=parse_xml(xml).levels[0].id.encode()
    first=(b'<Wall id="free_a" level="'+level+
           b'" x1="0" y1="5" z1="0" x2="4" y2="5" z2="0" height="3" thickness="0.2"/>')
    second=(b'<Wall id="free_b" level="'+level+
            b'" x1="4" y1="5" z1="0" x2="4" y2="8" z2="0" height="3" thickness="0.2"/>')
    return xml.replace(b"<Elements>",b"<Elements>\n  "+first+b"\n  "+second)

def create_joined_native_wall_source(tmp):
    dest=tmp/"two_free_walls.ifc"
    report=compile_declarative_xml(SOURCE,joined_wall_markup(source_xml()),dest)
    ids={op.ifc_guid for op in report.operations}
    doc=parse_xml(project_ifc(dest).xml)
    typed=[n for n in doc.elements if n.ifc_guid in ids]
    assert len(typed)==2
    return dest,tuple(typed)

def connected_markup(source_path,one,two):
    def action(root):
        ET.SubElement(_relations(root),"{"+NS+"}Connects",
                      {"from":one.id,"to":two.id})
    return build(project_ifc(source_path).xml,action)

def _native_rels(file):
    return {
        typ:sorted((r.GlobalId for r in file.by_type(typ)))
        for typ in ("IfcRelVoidsElement","IfcRelFillsElement",
                    "IfcRelContainedInSpatialStructure",
                    "IfcRelSpaceBoundary","IfcRelConnectsElements")
    }

class NativeWindowTopologyTests(unittest.TestCase):
    def test_delete_window_removes_fill_not_host_opening_or_wall(self):
        before_bytes=SOURCE.read_bytes()
        a=ifcopenshell.open(str(SOURCE))
        w=a.by_type("IfcWindow")[0]
        guid=w.GlobalId
        fills=list(w.FillsVoids)
        fill_guid=fills[0].GlobalId
        opening_guid=fills[0].RelatingOpeningElement.GlobalId
        host_guid=fills[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement.GlobalId
        before=_native_rels(a)
        changed=build(source_xml(),lambda root:_elements(root).remove(_one(root,"Window")))
        with tempfile.TemporaryDirectory() as temp:
            result=Path(temp)/"without_window.ifc"
            report=compile_declarative_xml(SOURCE,changed,result)
            b=ifcopenshell.open(str(result))
            after=_native_rels(b)
            self.assertEqual(report.operations[0].operation,"DELETE_WINDOW")
            self.assertEqual(len(b.by_type("IfcWindow")),0)
            self.assertEqual(len(b.by_type("IfcOpeningElement")),2)
            self.assertEqual(len(b.by_type("IfcRelVoidsElement")),2)
            self.assertEqual(b.by_guid(host_guid).GlobalId,host_guid)
            self.assertEqual(b.by_guid(opening_guid).GlobalId,opening_guid)
            self.assertEqual(len(b.by_guid(opening_guid).HasFillings),0)
            self.assertNotIn(fill_guid,after["IfcRelFillsElement"])
            self.assertEqual(len(after["IfcRelFillsElement"]),1)
            self.assertEqual(before["IfcRelVoidsElement"],after["IfcRelVoidsElement"])
            self.assertEqual(before["IfcRelSpaceBoundary"],after["IfcRelSpaceBoundary"])
            self.assertEqual(report.unexpected_root_changes,())
        self.assertEqual(SOURCE.read_bytes(),before_bytes)

    def test_opening_offset_moves_fill_geometry_without_relation_loss(self):
        f=ifcopenshell.open(str(SOURCE))
        opening=next(o for o in f.by_type("IfcOpeningElement") if o.Name=="Window Opening")
        guid=opening.GlobalId
        filled=opening.HasFillings[0].RelatedBuildingElement
        window_guid=filled.GlobalId
        old_xy=np.asarray(ifcopenshell.util.placement.get_local_placement(
            filled.ObjectPlacement)[:3,3],dtype=float)
        native_prior=_native_rels(f)
        def move(root):
            _one(root,"Opening",{"ifcGuid":guid}).set("offset","2.1")
        changed=build(source_xml(),move)
        with tempfile.TemporaryDirectory() as temp:
            result=Path(temp)/"moved.ifc"
            report=compile_declarative_xml(SOURCE,changed,result)
            b=ifcopenshell.open(str(result))
            actual=b.by_guid(window_guid)
            new_xyz=np.asarray(ifcopenshell.util.placement.get_local_placement(
                actual.ObjectPlacement)[:3,3],dtype=float)
            self.assertTrue(np.allclose(new_xyz-old_xy,[0.5,0,0],atol=1e-6))
            self.assertEqual(b.by_guid(guid).ObjectPlacement.RelativePlacement.Location.Coordinates,
                             (2.1,0.0,0.9))
            self.assertEqual(native_prior,_native_rels(b))
            self.assertEqual(report.operations[0].operation,"MOVE_OPENING_WITH_FILLING")
            self.assertEqual(report.unexpected_root_changes,())
            # Reprojection independently reads true native IFC offset.
            projected=parse_xml(project_ifc(result).xml)
            o=next(n for n in projected.elements if n.ifc_guid==guid)
            self.assertAlmostEqual(float(o.attrs()["offset"]),2.1)

class NativeConnectionTopologyTests(unittest.TestCase):
    def test_create_two_walls_and_relation_from_single_xml_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            original=source_xml()
            def add_relation(root):
                ET.SubElement(_relations(root),"{"+NS+"}Connects",
                              {"from":"free_a","to":"free_b"})
            combined=build(joined_wall_markup(original),add_relation)
            output=tmp/"walls_and_connection.ifc"
            report=compile_declarative_xml(SOURCE,combined,output)
            self.assertEqual({op.operation for op in report.operations},
                {"CREATE_WALL","ADD_WALL_CONNECTION"})
            self.assertEqual(sum(op.operation=="CREATE_WALL" for op in report.operations),2)
            f=ifcopenshell.open(str(output))
            newrels=f.by_type("IfcRelConnectsElements")
            self.assertEqual(len(newrels),1)
            r=newrels[0]
            guids={op.ifc_guid for op in report.operations if op.operation=="CREATE_WALL"}
            self.assertEqual({r.RelatingElement.GlobalId,r.RelatedElement.GlobalId},guids)
            self.assertTrue(r.RelatingElement.ContainedInStructure)
            self.assertTrue(r.RelatedElement.ContainedInStructure)
            self.assertEqual(report.unexpected_root_changes,())

    def test_add_then_remove_native_wall_connection_without_walls_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            source,typed=create_joined_native_wall_source(tmp)
            p=project_ifc(source)
            with_conn=tmp/"connected.ifc"
            first=compile_declarative_xml(source,connected_markup(source,*typed),with_conn)
            self.assertEqual(first.operations[0].operation,"ADD_WALL_CONNECTION")
            rel_guid=first.operations[0].ifc_guid
            f=ifcopenshell.open(str(with_conn))
            self.assertEqual(len(f.by_type("IfcRelConnectsElements")),1)
            self.assertEqual(f.by_guid(rel_guid).GlobalId,rel_guid)
            def remove(root):
                relations=_relations(root)
                relations.remove(_one(root,"Connects"))
            edited=build(project_ifc(with_conn).xml,remove)
            without=tmp/"disconnected.ifc"
            second=compile_declarative_xml(with_conn,edited,without)
            self.assertEqual(second.operations[0].operation,"REMOVE_WALL_CONNECTION")
            self.assertEqual(second.operations[0].ifc_guid,rel_guid)
            f2=ifcopenshell.open(str(without))
            self.assertEqual(len(f2.by_type("IfcRelConnectsElements")),0)
            self.assertEqual(len(f2.by_type("IfcWall")),3)
            for obj in typed:
                self.assertIsNotNone(f2.by_guid(obj.ifc_guid))
            self.assertEqual(second.unexpected_root_changes,())

class RejectInvalidTopologyTests(unittest.TestCase):
    def test_opening_collision_with_door_rejected(self):
        def overlap(root):
            _one(root,"Opening",{"offset":"1.6"}).set("offset","3.5")
        invalid=build(source_xml(),overlap)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"invalid.ifc"
            with self.assertRaisesRegex(CompilerError,"overlap"):
                compile_declarative_xml(SOURCE,invalid,out)
            self.assertFalse(out.exists())

    def test_missing_host_reference_blocks_before_write(self):
        invalid=source_xml().replace(b'host="wall_',b'host="no_such_wall_',1)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"invalid.ifc"
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,invalid,out)
            self.assertFalse(out.exists())

    def test_connect_nonmeeting_wall_endpoints_rejected(self):
        def connect(root):
            # Build a second wall too far away to meet any existing wall.
            level=_one(root,"Level").get("id")
            ET.SubElement(_elements(root),"{"+NS+"}Wall",
                          {"id":"distant_wall","level":level,"x1":"50","y1":"50",
                           "z1":"0","x2":"54","y2":"50","z2":"0",
                           "height":"3","thickness":"0.2"})
            ET.SubElement(_relations(root),"{"+NS+"}Connects",
                          {"from":_one(root,"Wall",{"ifcGuid":
                            next(e.ifc_guid for e in parse_xml(source_xml()).elements
                                 if e.kind=="Wall")}).get("id"),
                           "to":"distant_wall"})
        invalid=build(source_xml(),connect)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"invalid.ifc"
            with self.assertRaisesRegex(CompilerError,"actual endpoints"):
                compile_declarative_xml(SOURCE,invalid,out)
            self.assertFalse(out.exists())

    def test_duplicate_connection_declaration_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source,typed=create_joined_native_wall_source(Path(temp))
            def duplicate(root):
                for _ in range(2):
                    ET.SubElement(_relations(root),"{"+NS+"}Connects",
                                  {"from":typed[0].id,"to":typed[1].id})
            xml=build(project_ifc(source).xml,duplicate)
            out=Path(temp)/"duplicate.ifc"
            with self.assertRaisesRegex(CompilerError,"Duplicate declared"):
                compile_declarative_xml(source,xml,out)
            self.assertFalse(out.exists())

    def test_delete_opening_with_window_still_hosted_rejected(self):
        def delete(root):
            _elements(root).remove(_one(root,"Opening",{"offset":"1.6"}))
        invalid=build(source_xml(),delete)
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"invalid.ifc"
            with self.assertRaises(CompilerError):
                compile_declarative_xml(SOURCE,invalid,out)
            self.assertFalse(out.exists())

    def test_window_delete_with_other_property_dependency_denied(self):
        import ifcopenshell.api.pset
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"source_with_window_pset.ifc"
            f=ifcopenshell.open(str(SOURCE))
            window=f.by_type("IfcWindow")[0]
            pset=ifcopenshell.api.pset.add_pset(f,product=window,name="Pset_WindowsCommon")
            ifcopenshell.api.pset.edit_pset(f,pset=pset,properties={"Reference":"must_survive"})
            f.write(str(path))
            xml=build(project_ifc(path).xml,lambda root:_elements(root).remove(_one(root,"Window")))
            out=Path(temp)/"invalid.ifc"
            with self.assertRaisesRegex(CompilerError,"type/material/other"):
                compile_declarative_xml(path,xml,out)
            self.assertFalse(out.exists())

    def test_space_boundary_not_silently_managed_when_source_space_has_no_geometry(self):
        p=project_ifc(SOURCE)
        self.assertIn("IfcSpace",p.report()["unsupported_counts"])
        self.assertTrue(any("IfcRelSpaceBoundary" in s for s in p.opaque_relation_reasons))
        self.assertNotIn(b"<SpaceBoundary",p.xml)

if __name__=="__main__":unittest.main()

class GeometryAndSpatialBoundaryOracleTests(unittest.TestCase):
    def test_native_space_boundary_was_not_fabricated_from_xml(self):
        # The referenced IfcSpace exists but has no source geometry; its IFC
        # physical boundary must survive exactly, but cannot be edited via XML.
        f=ifcopenshell.open(str(SOURCE))
        native=f.by_type("IfcRelSpaceBoundary")
        self.assertEqual(len(native),1)
        rel=native[0]
        self.assertTrue(rel.RelatingSpace.is_a("IfcSpace"))
        self.assertTrue(rel.RelatedBuildingElement.is_a("IfcWall"))
        self.assertEqual(str(rel.PhysicalOrVirtualBoundary),"PHYSICAL")
        self.assertEqual(str(rel.InternalOrExternalBoundary),"INTERNAL")
        self.assertNotIn(b"SpaceBoundary",project_ifc(SOURCE).xml)
