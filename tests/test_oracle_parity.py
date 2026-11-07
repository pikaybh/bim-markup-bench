"""D0 declarative XML vs independently authored I0 IfcOpenShell reference.

All inputs and targets are own synthetic non-LLM fixtures; no official GT IFC.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import uuid

import ifcopenshell
from lxml import etree as ET

from src.runtime.compiler import compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.xml_parser import parse_xml
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import inspect_ifc,parity_report

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"
XML=ROOT/"tests/oracles/xml"
NS="urn:bim-markup-bench:toy:v0"
GUID_NS=uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd")
CONNECT_NS=uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111")

def deterministic_wall_guid(path:Path,id:str):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    name=f"bim-markup-v0.1:{sha}:IfcWall:{id}"
    return ifcopenshell.guid.compress(uuid.uuid5(GUID_NS,name).hex)

def deterministic_connection_guid(path:Path,left_guid:str,right_guid:str):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    name=f"connect-v0.1:{sha}:{left_guid}:{right_guid}"
    return ifcopenshell.guid.compress(uuid.uuid5(CONNECT_NS,name).hex)

def _node(kind,xml):
    p=parse_xml(xml)
    matches=[n for n in p.elements if n.kind==kind]
    assert len(matches)==1
    return matches[0]

def _construct_xml(source:Path,modifier):
    q=project_ifc(source)
    root=ET.fromstring(q.xml)
    modifier(root)
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def _assert_parity(test:unittest.TestCase,a:Path,b:Path,operation:str):
    result=parity_report(a,b)
    test.assertTrue(result["parity"],f"{operation}: {result}")
    test.assertEqual(result["mismatched_categories"],())
    test.assertGreater(result["native_object_count_left"],0)
    return result


class FrozenD0I0ParityTests(unittest.TestCase):
    def test_four_static_direct_spatial_topology_fixtures(self):
        source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        scenarios={
            "update_wall_height": "UPDATE_WALL_HEIGHT",
            "move_hosted_opening":"MOVE_OPENING",
            "delete_hosted_window":"DELETE_WINDOW",
            "create_standalone_wall":"CREATE_WALL",
        }
        before=SOURCE.read_bytes()
        for fixture,operation in scenarios.items():
            with self.subTest(operation=operation),tempfile.TemporaryDirectory() as temp:
                edited=(XML/(fixture+".xml")).read_bytes()
                parsed=parse_xml(edited,expected_source_sha256=source_hash)
                test_dir=Path(temp)
                direct=test_dir/"D0.ifc"
                baseline=test_dir/"I0.ifc"
                d0=compile_declarative_xml(SOURCE,edited,direct)
                if operation=="UPDATE_WALL_HEIGHT":
                    guid=_node("Wall",edited).ifc_guid
                    manual_ifc_reference(SOURCE,baseline,operation,
                                         target_guid=guid,height=3.3)
                elif operation=="MOVE_OPENING":
                    guid=next(n.ifc_guid for n in parsed.elements
                              if n.kind=="Opening" and n.attrs()["offset"]==__import__("decimal").Decimal("2.1"))
                    manual_ifc_reference(SOURCE,baseline,operation,
                                         target_guid=guid,delta_x=0.5)
                elif operation=="DELETE_WINDOW":
                    orig=parse_xml(project_ifc(SOURCE).xml)
                    guid=next(n.ifc_guid for n in orig.elements if n.kind=="Window")
                    manual_ifc_reference(SOURCE,baseline,operation,target_guid=guid)
                elif operation=="CREATE_WALL":
                    guid=deterministic_wall_guid(SOURCE,"oracle_wall")
                    storey_guid=ifcopenshell.open(str(SOURCE)).by_type("IfcBuildingStorey")[0].GlobalId
                    manual_ifc_reference(SOURCE,baseline,operation,
                                         new_guid=guid,storey_guid=storey_guid)
                else:
                    self.fail("Unregistered deterministic scenario")
                _assert_parity(self,direct,baseline,operation)
                self.assertEqual(d0.operations[0].operation,
                                 "MOVE_OPENING_WITH_FILLING" if operation=="MOVE_OPENING" else operation)
                self.assertEqual(d0.unexpected_root_changes,())
        self.assertEqual(before,SOURCE.read_bytes())

    def test_full_standalone_wall_delete_in_both_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            base=tmp/"source_free_wall.ifc"
            gid=deterministic_wall_guid(SOURCE,"manual_free_wall")
            storey=ifcopenshell.open(str(SOURCE)).by_type("IfcBuildingStorey")[0].GlobalId
            manual_ifc_reference(SOURCE,base,"CREATE_WALL",new_guid=gid,storey_guid=storey)
            before=base.read_bytes()
            def remove(root):
                nodes=root.find(".//{"+NS+"}Elements")
                matches=[e for e in nodes if e.get("ifcGuid")==gid]
                self.assertEqual(len(matches),1)
                nodes.remove(matches[0])
            xml=_construct_xml(base,remove)
            direct=tmp/"D0_delete.ifc"; baseline=tmp/"I0_delete.ifc"
            report=compile_declarative_xml(base,xml,direct)
            manual_ifc_reference(base,baseline,"DELETE_WALL",target_guid=gid)
            _assert_parity(self,direct,baseline,"DELETE_WALL")
            self.assertEqual(report.operations[0].operation,"DELETE_WALL")
            self.assertEqual(base.read_bytes(),before)

    def test_wall_connection_in_both_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            storey=ifcopenshell.open(str(SOURCE)).by_type("IfcBuildingStorey")[0].GlobalId
            source1=tmp/"wall1.ifc"
            guid1=deterministic_wall_guid(SOURCE,"manual_join_a")
            manual_ifc_reference(SOURCE,source1,"CREATE_WALL",
                                 new_guid=guid1,storey_guid=storey,
                                 start=(0,5,0),end=(4,5,0))
            source2=tmp/"source_two_walls.ifc"
            guid2=deterministic_wall_guid(source1,"manual_join_b")
            manual_ifc_reference(source1,source2,"CREATE_WALL",
                                 new_guid=guid2,storey_guid=storey,
                                 start=(4,5,0),end=(4,8,0))
            def connect(root):
                doc=parse_xml(project_ifc(source2).xml)
                nodes={n.ifc_guid:n.id for n in doc.elements if n.kind=="Wall"}
                ET.SubElement(root.find(".//{"+NS+"}Relations"),"{"+NS+"}Connects",
                              {"from":nodes[guid1],"to":nodes[guid2]})
            xml=_construct_xml(source2,connect)
            direct=tmp/"D0_connect.ifc";baseline=tmp/"I0_connect.ifc"
            expected=deterministic_connection_guid(source2,guid1,guid2)
            report=compile_declarative_xml(source2,xml,direct)
            manual_ifc_reference(source2,baseline,"ADD_CONNECTION",
                                new_guid=expected,first_guid=guid1,second_guid=guid2)
            _assert_parity(self,direct,baseline,"ADD_CONNECTION")
            self.assertEqual(report.operations[0].ifc_guid,expected)
            self.assertEqual(report.operations[0].operation,"ADD_WALL_CONNECTION")

    def test_noop_roundtrip_retains_full_ifc_graph_and_raw_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            tmp=Path(temp)
            original=snapshot_source(SOURCE)
            source_view=project_ifc(SOURCE).xml
            # No model semantics changed: add harmless XML comment and numeric
            # scale notation; IFC bytes must remain identical to original.
            modified=source_view.replace(b"<Elements>",b"<Elements>\n<!-- no-op -->").replace(
                b'height="3" thickness="0.2"',b'thickness="0.20" height="3.0"')
            out=tmp/"noop.ifc"
            report=compile_declarative_xml(SOURCE,modified,out)
            after=snapshot_source(out)
            self.assertEqual(SOURCE.read_bytes(),out.read_bytes())
            self.assertEqual(original.graph_fingerprint,after.graph_fingerprint)
            self.assertEqual(original.global_ids,after.global_ids)
            self.assertEqual(original.named_relation_memberships,after.named_relation_memberships)
            self.assertEqual(original.entity_class_counts,after.entity_class_counts)
            self.assertEqual(report.operations,())

class OracleSeparationTests(unittest.TestCase):
    def test_python_reference_does_not_call_direct_xml_runtime(self):
        text=(ROOT/"tests/oracles/python/independent_ifc_oracle.py").read_text()
        for forbidden in (
            "from src.runtime.compiler", "from src.runtime.ifc_mutations",
            "from src.runtime.topology_ops","from src.runtime.binder",
            "from src.runtime.semantic_graph","compile_declarative_xml(",
            "execute(", "eval(", "exec(", "openai.",
        ):
            self.assertNotIn(forbidden,text)

    def test_frozen_oracle_markup_never_contains_grader_fields(self):
        for p in XML.glob("*.xml"):
            with self.subTest(file=p.name):
                raw=p.read_bytes()
                parse_xml(raw)
                for token in (b"ground_truth_ifc",b"evaluation",b"OPENAI_API_KEY",
                              b"<CreateWall",b"reference_solution"):
                    self.assertNotIn(token,raw)

if __name__=="__main__":unittest.main()
