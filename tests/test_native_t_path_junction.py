"""Issue #15: native T-path IFC4X3 joins on fixed public INPUT, no GT access.

Each test compiles a declarative XML snapshot, never imperative markup.
The independent Python arm changes the same pinned input without importing
the declarative compiler or topology mutator for authoring.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
import uuid

import ifcopenshell
import ifcopenshell.geom
import numpy as np
from lxml import etree as ET

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.runtime.compiler import compile_declarative_xml, CompilerError
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report
from tools.verify_spatial_wall_manual_oracle import _geometry_from_public_instruction

ROOT=Path(__file__).resolve().parents[1]
CASE="WAL-CRE-SPA-A-003"
NS="urn:bim-markup-bench:toy:v0"
NEW_WALL_ID="g1_t_path_join_manual"
NEW_WALL_NS=uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd")


def pinned_input():
    t={x["task_id"]:x for x in read_tasks(ROOT/"data/tasks.jsonl")}[CASE]
    tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf8"))
    by_path={x["path"]:x for x in tree if x.get("type")=="file"}
    rel=repo_asset_path(t["input_ifc"])
    source=_files_in_root((ROOT/"data/ifc").resolve(),rel)
    verify_local_asset_bytes(source,by_path[rel])
    refs=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",t["prompt"])
    if len(refs)!=3:
        raise AssertionError("Frozen public prompt reference count changed")
    return t,source,refs


def authored_markup(*,new_y:float|None=None,connection_mode:str="both",
                    boundary:bool=False):
    task,source,refs=pinned_input()
    model=ifcopenshell.open(str(source))
    projected=project_ifc(source)
    g=_geometry_from_public_instruction(task,model,projected)
    node=ET.fromstring(projected.xml)
    elements=node.find(".//{"+NS+"}Elements")
    relations=node.find(".//{"+NS+"}Relations")
    if elements is None or relations is None:
        raise AssertionError("Required declarative graph sections unavailable")
    y=float(g["start"][1]) if new_y is None else new_y
    # Native swept wall thickness is to the +Y side of its X-axis.
    ET.SubElement(elements,"{"+NS+"}Wall",{
        "id":NEW_WALL_ID,"level":g["storey_local_id"],
        "x1":str(g["start"][0]),"y1":str(y),"z1":str(g["start"][2]),
        "x2":str(g["end"][0]),"y2":str(y),"z2":str(g["end"][2]),
        "height":str(g["height"]),"thickness":str(g["thickness"]),
    })
    lookup=dict(projected.projected_global_ids)
    if connection_mode=="both":
        for key in refs[:2]:
            ET.SubElement(relations,"{"+NS+"}Connects",
                          {"from":lookup[key],"to":NEW_WALL_ID})
    elif connection_mode=="reverse":
        ET.SubElement(relations,"{"+NS+"}Connects",
                      {"from":NEW_WALL_ID,"to":lookup[refs[0]]})
    elif connection_mode=="first":
        ET.SubElement(relations,"{"+NS+"}Connects",
                      {"from":lookup[refs[0]],"to":NEW_WALL_ID})
    elif connection_mode!="none":
        raise ValueError("Unknown own-test connection mode")
    if boundary:
        ET.SubElement(relations,"{"+NS+"}SpaceBoundary",
                      {"space":lookup[refs[2]],"element":NEW_WALL_ID,"kind":"PHYSICAL"})
    text=ET.tostring(node,encoding="utf8",xml_declaration=True)
    return source,refs,g,text


def _new_guid(original_hash:str)->str:
    name=f"bim-markup-v0.1:{original_hash}:IfcWall:{NEW_WALL_ID}"
    return ifcopenshell.guid.compress(uuid.uuid5(NEW_WALL_NS,name).hex)


def _path_summary(model,new_wall_guid):
    return sorted(
        (r.RelatingElement.GlobalId,
         r.RelatedElement.GlobalId,
         str(r.RelatingConnectionType),
         str(r.RelatedConnectionType),
         tuple(r.RelatingPriorities),tuple(r.RelatedPriorities),
         r.ConnectionGeometry is None)
        for r in model.by_type("IfcRelConnectsPathElements")
        if r.RelatedElement.GlobalId==new_wall_guid
    )


class NativeTPathJoinTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned public metadata missing")
    def test_real_source_two_t_connections_and_independent_python_arm(self):
        source,refs,g,edited=authored_markup()
        frozen_sha=hashlib.sha256(source.read_bytes()).hexdigest()
        initial=ifcopenshell.open(str(source))
        before=native_topology_inventory(initial)
        new_guid=_new_guid(frozen_sha)
        with TemporaryDirectory(prefix="native-t-junction-g1-") as temp:
            d=Path(temp)
            direct=d/"D0.ifc"
            imperative=d/"I0.ifc"
            scratch=d/"I0_base.ifc"
            report=compile_declarative_xml(source,edited,direct)
            self.assertEqual([x.operation for x in report.operations],
                ["CREATE_WALL","ADD_WALL_PATH_CONNECTION","ADD_WALL_PATH_CONNECTION"])
            result=ifcopenshell.open(str(direct))
            edges=_path_summary(result,new_guid)
            self.assertEqual(len(edges),2)
            self.assertEqual({(x[2],x[3]) for x in edges},
                             {("ATPATH","ATSTART"),("ATPATH","ATEND")})
            self.assertEqual({x[0] for x in edges},set(refs[:2]))
            self.assertEqual({x[1] for x in edges},{new_guid})
            self.assertTrue(all(x[4]==() and x[5]==() and x[6] for x in edges))
            self.assertEqual(len(result.by_type("IfcRelConnectsPathElements")),
                             len(initial.by_type("IfcRelConnectsPathElements"))+2)
            after=native_topology_inventory(result)
            for rel_id,typed in before.items():
                if typed[0]=="IfcRelContainedInSpatialStructure":
                    self.assertEqual(typed[1],after[rel_id][1])
                    self.assertTrue(set(typed[2]).issubset(after[rel_id][2]))
                else:
                    self.assertEqual(typed,after[rel_id])
            self.assertEqual(len(result.by_guid(new_guid).ConnectedFrom),2)
            self.assertEqual(len(result.by_guid(new_guid).ConnectedTo),0)
            self.assertEqual(
                sum(x.is_a("IfcRelSpaceBoundary") for x in result.get_inverse(result.by_guid(new_guid))),
                0)
            # Independent imperative authoring: no call to D0 compiler's
            # mutation planner/relationship helper; source IFC is shared.
            manual_ifc_reference(source,scratch,"CREATE_WALL",new_guid=new_guid,
                storey_guid=g["storey_guid"],
                start=tuple(float(v) for v in g["start"]),
                end=tuple(float(v) for v in g["end"]),
                height=float(g["height"]),thickness=float(g["thickness"]))
            other=ifcopenshell.open(str(scratch))
            new_wall=other.by_guid(new_guid)
            for ref,which in zip(refs[:2],("ATSTART","ATEND")):
                # Both arms share a preregistered deterministic relation
                # identity rule, but I0 constructs it independently.
                relation_seed=(f"connect-v0.1:{frozen_sha}:{ref}:{new_guid}")
                rel_guid=ifcopenshell.guid.compress(uuid.uuid5(
                    uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111"),
                    relation_seed).hex)
                other.create_entity("IfcRelConnectsPathElements",
                    GlobalId=rel_guid,
                    RelatingElement=other.by_guid(ref),RelatedElement=new_wall,
                    RelatingPriorities=(),RelatedPriorities=(),
                    RelatingConnectionType="ATPATH",RelatedConnectionType=which)
            other.write(str(imperative))
            self.assertEqual(_path_summary(result,new_guid),_path_summary(other,new_guid))
            self.assertTrue(parity_report(direct,imperative)["parity"])
            # Neither D0 nor I0 edited the shared pinned public input IFC.
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),frozen_sha)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned public metadata missing")
    def test_reversed_declaration_cannot_disguise_path_contact(self):
        source,_,_,edited=authored_markup(connection_mode="reverse")
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="reject-reversed-t-junction-") as temp:
            target=Path(temp)/"should_not_exist.ifc"
            with self.assertRaisesRegex(CompilerError,"actual endpoints or verified T"):
                compile_declarative_xml(source,edited,target)
            self.assertFalse(target.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned public metadata missing")
    def test_noncontact_new_wall_is_not_connected_to_existing_host(self):
        source,_,_,edited=authored_markup(connection_mode="first")
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        root=ET.fromstring(edited)
        wall=next(n for n in root.iter()
                  if isinstance(n.tag,str) and n.get("id")==NEW_WALL_ID)
        # Displace the branch start 0.25 m away from the native host surface.
        wall.set("x1",str(float(wall.get("x1"))+0.25))
        payload=ET.tostring(root,encoding="utf8",xml_declaration=True)
        with TemporaryDirectory(prefix="reject-disjoint-t-junction-") as temp:
            target=Path(temp)/"should_not_exist.ifc"
            with self.assertRaisesRegex(CompilerError,"contact one unobstructed"):
                compile_declarative_xml(source,payload,target)
            self.assertFalse(target.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned public metadata missing")
    def test_native_hosted_door_void_blocks_conflicting_t_junction(self):
        source,_,_,edited=authored_markup(new_y=4.15)
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="reject-void-t-junction-") as temp:
            output=Path(temp)/"invalid.ifc"
            with self.assertRaisesRegex(CompilerError,"unobstructed host side"):
                compile_declarative_xml(source,edited,output)
            self.assertFalse(output.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").exists(),"Pinned public metadata missing")
    def test_unverified_space_boundary_remains_blocked_without_room_split(self):
        source,_,_,edited=authored_markup(boundary=True)
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="reject-false-space-boundary-") as temp:
            target=Path(temp)/"should_not_exist.ifc"
            with self.assertRaisesRegex(CompilerError,"relationship addition"):
                compile_declarative_xml(source,edited,target)
            self.assertFalse(target.exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_hash)


if __name__=="__main__":
    unittest.main()
