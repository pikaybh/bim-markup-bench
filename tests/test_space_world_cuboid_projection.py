"""G1 #11 source-only Space projection: exact world cuboid, not a bounding-box guess."""
from __future__ import annotations

import hashlib
import json
from math import cos, sin, pi
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import numpy as np

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from src.runtime.compiler import compile_declarative_xml

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="WAL-CRE-SPA-A-003"


def pinned_source_and_room()->tuple[Path,str]:
    row={r["task_id"]:r for r in read_tasks(ROOT/"data/tasks.jsonl")}[TASK_ID]
    tree=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf8"))
    lookup={r["path"]:r for r in tree if r.get("type")=="file"}
    rel=repo_asset_path(row["input_ifc"])
    source=_files_in_root((ROOT/"data/ifc").resolve(),rel)
    verify_local_asset_bytes(source,lookup[rel])
    import re
    refs=re.findall(r"(?<![A-Za-z0-9_$])[A-Za-z0-9_$]{22}(?![A-Za-z0-9_$])",row["prompt"])
    if len(refs)!=3:
        raise ValueError("Frozen task reference pattern changed")
    return source,refs[2]


class ExactWorldSpaceProjectionTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"No pinned public metadata")
    def test_rotated_internal_space_is_exact_axis_aligned_world_box(self):
        source,room=pinned_source_and_room()
        original=hashlib.sha256(source.read_bytes()).hexdigest()
        projected=project_ifc(source)
        self.assertIn(room,dict(projected.projected_global_ids))
        self.assertNotIn(room,{o.ifc_guid for o in projected.opaque_references})
        nodes=[e for e in parse_xml(projected.xml).elements if e.ifc_guid==room]
        self.assertEqual(len(nodes),1)
        self.assertEqual(nodes[0].kind,"Space")
        attrs={k:float(v) for k,v in nodes[0].attrs().items()
               if k in ("x","y","z","width","depth","height")}
        self.assertEqual(attrs,{"x":0.175,"y":2.9,"z":0.0,
                                "width":4.45,"depth":3.125,"height":2.8})
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"No pinned public metadata")
    def test_rotated_swept_profile_that_yields_oblique_world_shape_stays_opaque(self):
        source,room=pinned_source_and_room()
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        with TemporaryDirectory(prefix="own-neg-oblique-space-") as tmp:
            changed=Path(tmp)/"changed.ifc"
            model=ifcopenshell.open(str(source))
            space=model.by_guid(room)
            solids=[item for representation in space.Representation.Representations
                    for item in representation.Items if item.is_a("IfcExtrudedAreaSolid")]
            self.assertEqual(len(solids),1)
            position=solids[0].Position
            self.assertIsNotNone(position)
            position.RefDirection=model.createIfcDirection((cos(pi/4),sin(pi/4),0.))
            model.write(str(changed))
            changed_projection=project_ifc(changed)
            self.assertNotIn(room,dict(changed_projection.projected_global_ids))
            self.assertIn(room,{o.ifc_guid for o in changed_projection.opaque_references})
            # A fabricated AABB edit would be worse than a clear unsupported status.
            self.assertNotIn(room,{e.ifc_guid for e in parse_xml(changed_projection.xml).elements})
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)

    @unittest.skipUnless((ROOT/"data/tasks.jsonl").is_file(),"No pinned public metadata")
    def test_newly_projected_space_noop_copies_immutable_source(self):
        source,_=pinned_source_and_room()
        original=source.read_bytes()
        xml=project_ifc(source).xml
        with TemporaryDirectory(prefix="own-native-space-noop-") as tmp:
            out=Path(tmp)/"same.ifc"
            result=compile_declarative_xml(source,xml,out)
            self.assertEqual(result.operations,())
            self.assertEqual(out.read_bytes(),original)
        self.assertEqual(source.read_bytes(),original)


if __name__=="__main__":
    unittest.main()
