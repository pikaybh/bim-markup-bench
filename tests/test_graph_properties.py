"""Additional graph negative tests and cross-model source identity cases."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from src.runtime.binder import BindingError, bind_document
from src.runtime.ifc_projection import project_ifc
from src.runtime.semantic_graph import GraphEdge, GraphNode, BindingError, make_graph
from src.runtime.xml_parser import parse_xml

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=(ROOT/"examples/valid/basic_building.xml").read_bytes()

class GraphPropertyTests(unittest.TestCase):
    def test_graph_rejects_duplicate_globalid_different_localids(self):
        nodes=[
            GraphNode("a","Wall","0"*22,"existing_source",()),
            GraphNode("b","Wall","0"*22,"existing_source",()),
        ]
        with self.assertRaisesRegex(BindingError,"Duplicate IFC GlobalId"):
            make_graph("0"*64,nodes,[],[])

    def test_graph_rejects_multiple_parent_ownership(self):
        nodes=[
            GraphNode("l1","Level","0"*22,"existing_source",()),
            GraphNode("l2","Level","1"*22,"existing_source",()),
            GraphNode("w","Wall","2"*22,"existing_source",()),
        ]
        with self.assertRaisesRegex(BindingError,"multiple conflicting"):
            make_graph("0"*64,nodes,[
                GraphEdge("in_storey","l1","w","derived"),
                GraphEdge("in_storey","l2","w","derived"),
            ],[])

    def test_source_snapshot_unchanged_on_binder_failure(self):
        source=ROOT/"tests/fixtures/synthetic/input.ifc"
        old=source.read_bytes()
        projection=project_ifc(source)
        # Geometry precondition violation is valid XSD, invalid semantic graph.
        tampered=projection.xml.replace(b'offset="1.6"',b'offset="6.8"')
        with self.assertRaisesRegex(BindingError,"horizontal extent"):
            bind_document(parse_xml(tampered),projection=projection)
        self.assertEqual(source.read_bytes(),old)

    def test_new_object_allocated_without_ever_touching_source_ifc(self):
        source=ROOT/"tests/fixtures/synthetic/input.ifc"
        old=source.read_bytes()
        p=project_ifc(source)
        new_wall=(b'<Wall id="supplementary_wall" level="'+
                  parse_xml(p.xml).levels[0].id.encode()+
                  b'" x1="0" y1="3" z1="0" x2="6" y2="3" z2="0" height="3" thickness="0.2"/>')
        edited=parse_xml(p.xml.replace(b'<Elements>',b'<Elements>\n    '+new_wall))
        result=bind_document(edited,projection=p)
        self.assertEqual(result.report()["deterministically_allocated_new_globalids"],1)
        self.assertEqual(source.read_bytes(),old)
        new_id=result.graph.by_id()["supplementary_wall"].ifc_guid
        self.assertNotIn(new_id,dict(p.source.global_ids))
        self.assertFalse(result.report()["ifc_mutated"])

if __name__=="__main__":unittest.main()
