"""Trusted source-only declarative Space split compiler roundtrip tests.

The fixture's XML declares *states*, not "Split" or mutation commands. No
target/GT IFC is opened. The source is SHA-pinned and never edited in place.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
from lxml import etree

from src.runtime.compiler import compile_declarative_xml,CompilerError
from src.runtime.ifc_projection import project_ifc
from src.runtime.binder import allocate_new_ifc_guid
from src.runtime.space_partition_preflight import plan_rectangular_space_partition
from src.runtime.space_partition_sandbox import sandbox_native_space_split
from tests.test_native_t_path_junction import authored_markup,_new_guid,NS
from src.runtime.xml_parser import parse_xml

NEW_FAR_ID="g1_far_space_state"


def make_space_split_state():
    source,refs,geometry,joined_state=authored_markup()
    base=etree.fromstring(joined_state)
    bindings=dict(project_ifc(source).projected_global_ids)
    old_room_id=bindings[refs[2]]
    old_room=next(n for n in base.iter()
                  if isinstance(n.tag,str) and n.get("id")==old_room_id)
    far=base.find(".//{"+NS+"}Elements")
    relations=base.find(".//{"+NS+"}Relations")
    if old_room is None or far is None or relations is None:
        raise ValueError("Missing frozen Space XML document state")
    original_attrs=dict(old_room.attrib)
    # The authored state describes two non-overlapping Spaces separated by
    # the new wall, not a procedural SplitSpace instruction.
    wall_y=geometry["start"][1]
    wall_depth=geometry["thickness"]
    near_depth=wall_y-geometry["start"][1]+(wall_y-__import__("decimal").Decimal("2.9"))
    far_y=wall_y+wall_depth
    far_depth=__import__("decimal").Decimal(original_attrs["y"])+__import__("decimal").Decimal(original_attrs["depth"])-far_y
    old_room.set("depth",str(near_depth))
    new_attrs={k:v for k,v in original_attrs.items() if k not in ("ifcGuid",)}
    new_attrs.update(id=NEW_FAR_ID,y=str(far_y),depth=str(far_depth))
    etree.SubElement(far,"{"+NS+"}Space",new_attrs)
    # Existing room's far wall must be assigned to the far partition. The
    # remaining two source reference walls straddle BOTH partition rooms.
    original_room_bounds=[n.get("element") for n in relations
                          if n.tag=="{"+NS+"}SpaceBoundary"
                          and n.get("space")==old_room_id]
    far_wall_candidates=[w for w in original_room_bounds
                         if w not in (bindings[refs[0]],bindings[refs[1]])]
    if len(far_wall_candidates)!=1:
        raise ValueError("Pinned far end wall boundary not uniquely identifiable")
    far_wall_local=far_wall_candidates[0]
    old_far_edges=[n for n in relations
                   if n.tag=="{"+NS+"}SpaceBoundary"
                   and n.get("space")==old_room_id
                   and n.get("element")==far_wall_local]
    if len(old_far_edges)!=1:
        raise ValueError("Pinned native far wall boundary relationship not unique")
    relations.remove(old_far_edges[0])
    for local in (bindings[refs[0]],bindings[refs[1]],far_wall_local,
                  "g1_t_path_join_manual"):
        etree.SubElement(relations,"{"+NS+"}SpaceBoundary",
                         {"space":NEW_FAR_ID,"element":local,"kind":"PHYSICAL"})
    etree.SubElement(relations,"{"+NS+"}SpaceBoundary",
                     {"space":old_room_id,"element":"g1_t_path_join_manual",
                      "kind":"PHYSICAL"})
    # The other original host Wall must span the original near and new far
    # rooms, too; it is not the task's dedicated reference host.
    old_relations={(n.get("space"),n.get("element")) for n in relations
                   if n.tag=="{"+NS+"}SpaceBoundary"}
    side_walls=[n.get("element") for n in relations
                if n.tag=="{"+NS+"}SpaceBoundary" and n.get("space")==old_room_id
                and n.get("element") not in (bindings[refs[0]],"g1_t_path_join_manual")]
    # Any side Wall already referenced to near remains a boundary of far.
    for wall_local in side_walls:
        if (NEW_FAR_ID,wall_local) not in old_relations:
            etree.SubElement(relations,"{"+NS+"}SpaceBoundary",
                             {"space":NEW_FAR_ID,"element":wall_local,"kind":"PHYSICAL"})
            old_relations.add((NEW_FAR_ID,wall_local))
    return source,etree.tostring(base,encoding="utf-8",xml_declaration=True)


class DeclarativeBoundedSpaceSplitTests(unittest.TestCase):
    def test_exact_source_only_state_compiles_to_native_space_split(self):
        source,edited=make_space_split_state()
        original=hashlib.sha256(source.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="source-xml-space-state-") as folder:
            output=Path(folder)/"split.ifc"
            report=compile_declarative_xml(source,edited,output)
            self.assertTrue(report.write_committed)
            self.assertEqual([op.operation for op in report.operations],
                ["CREATE_WALL","ADD_WALL_PATH_CONNECTION","ADD_WALL_PATH_CONNECTION","SPLIT_SPACE"])
            result=ifcopenshell.open(str(output))
            self.assertEqual(len(result.by_type("IfcSpace")),3)
            self.assertEqual(len(result.by_type("IfcRelSpaceBoundary")),19)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            self.assertEqual(report.unexpected_root_changes,())

    def test_independent_python_imperative_partition_matches_full_declarative_ifc(self):
        import uuid
        from src.runtime.binder import allocate_new_ifc_guid
        from tests.test_native_t_path_junction import authored_markup
        from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
        from tests.oracles.python.independent_ifc_checker import parity_report
        from tests.oracles.python.independent_space_partition import (
            author_independent_space_partition,
        )
        from src.runtime.space_partition_preflight import _surface_polygon,_exact_box
        source,edited=make_space_split_state()
        _,refs,geom,_=authored_markup()
        before_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        orig=ifcopenshell.open(str(source))
        old_room=refs[2]
        new_wall_guid=allocate_new_ifc_guid(
            before_sha,"Wall","g1_t_path_join_manual",set())
        far_guid=allocate_new_ifc_guid(before_sha,"Space",NEW_FAR_ID,set())
        with TemporaryDirectory(prefix="g1-independent-full-space-pair-") as folder:
            tmp=Path(folder)
            direct=tmp/"D0.ifc";ibase=tmp/"I0_wall.ifc"
            ijoined=tmp/"I0_joins.ifc";imperative=tmp/"I0_final.ifc"
            report=compile_declarative_xml(source,edited,direct)
            self.assertTrue(report.write_committed)
            manual_ifc_reference(source,ibase,"CREATE_WALL",
                new_guid=new_wall_guid,storey_guid=geom["storey_guid"],
                start=tuple(float(x) for x in geom["start"]),
                end=tuple(float(x) for x in geom["end"]),
                height=float(geom["height"]),thickness=float(geom["thickness"]))
            f=ifcopenshell.open(str(ibase))
            wall=f.by_guid(new_wall_guid)
            for relating,connection in zip(refs[:2],("ATSTART","ATEND")):
                name=f"connect-v0.1:{before_sha}:{relating}:{new_wall_guid}"
                rel_guid=ifcopenshell.guid.compress(
                    uuid.uuid5(uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111"),
                               name).hex)
                f.createIfcRelConnectsPathElements(
                    GlobalId=rel_guid,RelatingElement=f.by_guid(relating),
                    RelatedElement=wall,RelatingConnectionType="ATPATH",
                    RelatedConnectionType=connection,
                    RelatingPriorities=(),RelatedPriorities=())
            f.write(str(ijoined))
            author_independent_space_partition(
                ijoined,imperative,source_sha=before_sha,
                source_space_guid=old_room,new_wall_guid=new_wall_guid,
                new_space_guid=far_guid)
            result=parity_report(direct,imperative)
            self.assertTrue(result["parity"],str(result))
            a=ifcopenshell.open(str(direct))
            b=ifcopenshell.open(str(imperative))
            self.assertEqual(
                {r.GlobalId for r in a.by_type("IfcRelSpaceBoundary")},
                {r.GlobalId for r in b.by_type("IfcRelSpaceBoundary")})
            for relation in a.by_type("IfcRelSpaceBoundary"):
                same=b.by_guid(relation.GlobalId)
                self.assertEqual(same.RelatingSpace.GlobalId,
                                 relation.RelatingSpace.GlobalId)
                self.assertEqual(
                    same.RelatedBuildingElement.GlobalId
                    if same.RelatedBuildingElement else None,
                    relation.RelatedBuildingElement.GlobalId
                    if relation.RelatedBuildingElement else None)
                a_lo,a_hi,a_ax,a_n=_surface_polygon(
                    relation.RelatingSpace,relation)
                b_lo,b_hi,b_ax,b_n=_surface_polygon(
                    same.RelatingSpace,same)
                self.assertEqual(a_ax,b_ax)
                self.assertTrue(__import__("numpy").allclose(a_lo,b_lo,atol=1e-6))
                self.assertTrue(__import__("numpy").allclose(a_hi,b_hi,atol=1e-6))
                self.assertTrue(__import__("numpy").allclose(a_n,b_n,atol=1e-6))
            for guid in (old_room,far_guid):
                a_lo,a_hi=_exact_box(a.by_guid(guid),kind="IfcSpace")
                b_lo,b_hi=_exact_box(b.by_guid(guid),kind="IfcSpace")
                self.assertTrue(__import__("numpy").allclose(a_lo,b_lo,atol=1e-6))
                self.assertTrue(__import__("numpy").allclose(a_hi,b_hi,atol=1e-6))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         before_sha)

    def test_missing_edited_space_boundary_denied_before_output_commit(self):
        source,edited=make_space_split_state()
        original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        xml=etree.fromstring(edited)
        relations=xml.find(".//{"+NS+"}Relations")
        invalid=[r for r in relations
                 if r.tag=="{"+NS+"}SpaceBoundary"
                 and r.get("space")==NEW_FAR_ID
                 and r.get("element")=="g1_t_path_join_manual"]
        self.assertEqual(len(invalid),1)
        relations.remove(invalid[0])
        with TemporaryDirectory(prefix="deny-omitted-space-boundary-") as folder:
            dest=Path(folder)/"never-created.ifc"
            with self.assertRaisesRegex(CompilerError,"Partition lacks two"):
                compile_declarative_xml(source,etree.tostring(xml),dest)
            self.assertFalse(dest.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_sha)

    def test_forged_far_space_world_position_denied_without_output(self):
        source,edited=make_space_split_state()
        root=etree.fromstring(edited)
        far=next(x for x in root.iter() if isinstance(x.tag,str)
                 and x.tag=="{"+NS+"}Space" and x.get("id")==NEW_FAR_ID)
        far.set("y",str(float(far.get("y"))+0.12))
        with TemporaryDirectory(prefix="deny-forged-far-room-") as folder:
            dest=Path(folder)/"never-created.ifc"
            with self.assertRaisesRegex(CompilerError,"Space body diverges"):
                compile_declarative_xml(source,etree.tostring(root),dest)
            self.assertFalse(dest.exists())

    def test_unapproved_rehomed_wall_boundary_denied_by_reprojected_graph(self):
        source,edited=make_space_split_state()
        root=etree.fromstring(edited)
        near=next(x.get("id") for x in root.iter()
                  if isinstance(x.tag,str) and x.tag=="{"+NS+"}Space"
                  and x.get("ifcGuid") and x.get("y")=="2.9")
        # Adding a false boundary to the near room cannot survive the
        # verified native-projection graph comparison.
        walls=[n.get("id") for n in root.iter() if isinstance(n.tag,str)
               and n.tag=="{"+NS+"}Wall" and n.get("ifcGuid")]
        self.assertTrue(walls)
        relations=root.find(".//{"+NS+"}Relations")
        target=next(w for w in walls if not any(
            rel.get("space")==near and rel.get("element")==w
            for rel in relations if rel.tag=="{"+NS+"}SpaceBoundary"))
        etree.SubElement(relations,"{"+NS+"}SpaceBoundary",
                         {"space":near,"element":target,"kind":"PHYSICAL"})
        with TemporaryDirectory(prefix="deny-fabricated-boundary-") as folder:
            dest=Path(folder)/"never-created.ifc"
            with self.assertRaisesRegex(CompilerError,"whole edited XML state"):
                compile_declarative_xml(source,etree.tostring(root),dest)
            self.assertFalse(dest.exists())

    def test_unrelated_source_space_dimension_edit_rejected_without_output(self):
        source,edited=make_space_split_state()
        xml=etree.fromstring(edited)
        room=next(n for n in xml.iter()
                  if isinstance(n.tag,str) and n.tag=="{"+NS+"}Space"
                  and n.get("ifcGuid"))
        room.set("width",str(float(room.get("width"))+0.25))
        with TemporaryDirectory(prefix="reject-unsupported-space-edit-") as folder:
            out=Path(folder)/"should-not-exist.ifc"
            with self.assertRaises(CompilerError):
                compile_declarative_xml(source,etree.tostring(xml),out)
            self.assertFalse(out.exists())


if __name__=="__main__":
    unittest.main()
