"""Typed relation, provenance, ownership safety and dependency invalidation."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from src.runtime.ast import semantic_diff
from src.runtime.binder import BindingError, allocate_new_ifc_guid, bind_document
from src.runtime.ifc_projection import project_ifc
from src.runtime.semantic_graph import (
    GraphEdge, GraphNode, graph_diff, make_graph, validate_containment_acyclic
)
from src.runtime.xml_parser import parse_xml, MarkupParseError

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=(ROOT/"examples/valid/basic_building.xml").read_bytes()
SOURCE=ROOT/"tests/fixtures/synthetic/input.ifc"

def bind_text(data:bytes):
    return bind_document(parse_xml(data)).graph

class GraphPositiveTests(unittest.TestCase):
    def test_synthetic_example_binds_all_typified_relations(self):
        graph=bind_text(EXAMPLE)
        self.assertEqual(len(graph.nodes),9)
        self.assertIn(GraphEdge("host_void","north_wall","opening_window","derived"),graph.edges)
        self.assertIn(GraphEdge("host_void","north_wall","opening_door","derived"),graph.edges)
        self.assertIn(GraphEdge("opening_fill","opening_window","window_1","derived"),graph.edges)
        self.assertIn(GraphEdge("opening_fill","opening_door","door_1","derived"),graph.edges)
        self.assertIn(GraphEdge("space_boundary","room_101","north_wall","declared"),graph.edges)
        self.assertIn(GraphEdge("aggregated_in_storey","level_1","room_101","derived"),graph.edges)

    def test_deterministic_identity_and_graph_fingerprint(self):
        one=bind_text(EXAMPLE)
        two=bind_text(EXAMPLE.replace(b'height="3" thickness="0.2"',
                                       b'thickness="0.20" height="3.0"'))
        self.assertEqual(one.fingerprint,two.fingerprint)
        self.assertEqual(one.nodes,two.nodes)
        first=one.by_id()["north_wall"].ifc_guid
        self.assertEqual(first,two.by_id()["north_wall"].ifc_guid)
        self.assertEqual(len(first),22)
        self.assertEqual(one.by_id()["north_wall"].provenance,"deterministic_new")
        self.assertEqual(graph_diff(one,two).is_noop,True)

    def test_original_synthetic_ifc_relation_evidence(self):
        projected=project_ifc(SOURCE)
        doc=parse_xml(projected.xml)
        bound=bind_document(doc,projection=projected)
        self.assertEqual(bound.report()["existing_source_globalids"],8)
        self.assertEqual(bound.report()["source_relation_checks"],7)
        self.assertTrue(bound.report()["all_ifc_relation_contracts_satisfied"])
        self.assertEqual(bound.report()["deterministically_allocated_new_globalids"],0)
        self.assertTrue(all(n.provenance=="existing_source" for n in bound.graph.nodes))

    def test_native_evidence_does_not_infer_space_boundary(self):
        projected=project_ifc(SOURCE)
        bound=bind_document(parse_xml(projected.xml),projection=projected)
        self.assertFalse(any(e.relation=="space_boundary" for e in bound.graph.edges))
        self.assertTrue(projected.opaque_relation_reasons)

    def test_wall_dependents_and_space_invalidation(self):
        graph=bind_text(EXAMPLE)
        self.assertEqual(set(graph.affected_by({"north_wall"})),
            {"north_wall","opening_window","opening_door","window_1","door_1","room_101"})

    def test_one_edge_edit_does_not_modify_unrelated_geometry(self):
        a=bind_text(EXAMPLE)
        b=bind_text(EXAMPLE.replace(
            b'    <SpaceBoundary space="room_101" element="north_wall" kind="PHYSICAL"/>',
            b''))
        diff=graph_diff(a,b)
        self.assertFalse(diff.is_noop)
        self.assertEqual(diff.added_nodes,())
        self.assertEqual(diff.removed_nodes,())
        self.assertEqual(diff.changed_nodes,())
        self.assertEqual(len(diff.removed_edges),1)
        self.assertEqual(diff.added_edges,())
        self.assertIn("room_101",diff.invalidates)
        self.assertEqual(a.by_id()["north_wall"],b.by_id()["north_wall"])

    def test_changed_wall_invalidates_openings_and_fillings(self):
        a=bind_text(EXAMPLE)
        b=bind_text(EXAMPLE.replace(b'thickness="0.2"',b'thickness="0.25"'))
        diff=graph_diff(a,b)
        self.assertEqual(diff.changed_nodes,("north_wall",))
        self.assertIn("window_1",diff.invalidates)
        self.assertIn("door_1",diff.invalidates)
        self.assertIn("room_101",diff.invalidates)
        self.assertFalse(diff.as_dict()["ifc_written"])

class GraphNegativeTests(unittest.TestCase):
    def test_opening_outside_wall_fails_even_valid_xml(self):
        doc=parse_xml(EXAMPLE.replace(b'offset="1.6"',b'offset="5.7"'))
        with self.assertRaisesRegex(BindingError,"horizontal extent"):
            bind_document(doc)

    def test_shortened_wall_with_existing_window_fails(self):
        doc=parse_xml(EXAMPLE.replace(b'height="3" thickness="0.2"',
                                      b'height="2" thickness="0.2"'))
        with self.assertRaisesRegex(BindingError,"vertical extent"):
            bind_document(doc)

    def test_filling_wider_than_its_opening_fails(self):
        doc=parse_xml(EXAMPLE.replace(
            b'<Window id="window_1" opening="opening_window" width="1.2"',
            b'<Window id="window_1" opening="opening_window" width="3"'))
        with self.assertRaisesRegex(BindingError,"Filling exceeds"):
            bind_document(doc)

    def test_bad_storey_crossing_space_boundary(self):
        changed=EXAMPLE.replace(b'  </Levels>',b'    <Level id="level_2" elevation="3"/>\n  </Levels>')
        changed=changed.replace(b'<Space id="room_101" level="level_1"',
                                b'<Space id="room_101" level="level_2"')
        doc=parse_xml(changed)
        with self.assertRaisesRegex(BindingError,"crosses storeys"):
            bind_document(doc)

    def test_ifc_source_hash_mismatch_with_projection(self):
        projected=project_ifc(SOURCE)
        changed=projected.xml.replace(projected.source.source_sha256.encode(),b"1"*64)
        with self.assertRaises(BindingError):
            bind_document(parse_xml(changed),projection=projected)

    def test_existing_identity_cannot_be_overridden(self):
        p=project_ifc(SOURCE)
        doc=parse_xml(p.xml)
        old=list(p.projected_global_ids)[0][0]
        injected=p.xml.replace(old.encode(),b"1"*22)
        with self.assertRaises(BindingError):
            bind_document(parse_xml(injected),projection=p)

    def test_new_xml_local_id_cannot_smuggle_existing_guid(self):
        p=project_ifc(SOURCE)
        x=p.xml
        wall_id=next(e.id for e in parse_xml(x).elements if e.kind=="Wall")
        example_wall=next(e for e in parse_xml(x).elements if e.kind=="Wall")
        # Insert a new element with an old source IFC Guid; it must be rejected.
        original_start=x[example_wall.span.start_byte:example_wall.span.start_tag_end_byte]
        copied=original_start.replace(b'id="'+wall_id.encode()+b'"',b'id="unowned_new_wall"')
        tampered=x.replace(b"<Elements>",b"<Elements>\n    "+copied)
        # duplicate GlobalId is caught by XML schema or binder; both fail closed.
        try:
            parsed=parse_xml(tampered)
        except MarkupParseError:
            return
        with self.assertRaises(BindingError):
            bind_document(parsed,projection=p)

    def test_globalid_allocation_collision_rejected(self):
        sha="0"*64
        guid=allocate_new_ifc_guid(sha,"Wall","wall_unique",set())
        with self.assertRaisesRegex(BindingError,"collided"):
            allocate_new_ifc_guid(sha,"Wall","wall_unique",{guid})

    def test_direct_cyclic_containment_denied(self):
        x=GraphNode("x","Wall","0"*22,"deterministic_new",())
        y=GraphNode("y","Opening","1"*22,"deterministic_new",())
        with self.assertRaisesRegex(BindingError,"Cyclic"):
            validate_containment_acyclic([x,y],[
                GraphEdge("host_void","x","y","derived"),
                GraphEdge("host_void","y","x","derived")])

    def test_unknown_graph_node_invalidation_is_not_silent(self):
        with self.assertRaises(BindingError):
            bind_text(EXAMPLE).affected_by({"missing"})

if __name__=="__main__":unittest.main()

class CLIAndRealIFCBindingTests(unittest.TestCase):
    def test_cli_binds_synthetic_without_side_effects(self):
        import subprocess
        import json
        import sys
        source=SOURCE
        before=source.read_bytes()
        run=subprocess.run([sys.executable,"-m","tools.inspect_graph",
                            "--source-ifc",str(source)],
                           cwd=ROOT,capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stderr+run.stdout)
        info=json.loads(run.stdout)
        self.assertEqual(info["status"],"TYPED_GRAPH_ONLY_NO_IFC_OUTPUT")
        self.assertTrue(info["all_ifc_relation_contracts_satisfied"])
        self.assertEqual(info["source_relation_checks"],7)
        self.assertEqual(before,source.read_bytes())

    def test_real_bim_edit_small_wall_junction_relations(self):
        p=ROOT/"data/ifc/simple/17_input.ifc"
        if not p.exists():
            self.skipTest("Pinned tiny public IFC asset not locally cached")
        proj=project_ifc(p,strict_on_opaque=True)
        bound=bind_document(parse_xml(proj.xml),projection=proj)
        self.assertEqual(bound.report()["existing_source_globalids"],7)
        self.assertEqual(bound.report()["source_relation_checks"],10)
        self.assertTrue(bound.report()["all_ifc_relation_contracts_satisfied"])
