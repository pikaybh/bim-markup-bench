"""Independent OFFLINE process to validate OWN synthetic IFC outcome only.

The generated script is never imported here; no public benchmark GT or
official scorer modules are loaded. Invoked after the candidate container
has exited and its image/worker output has been bounded by the controller.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import ifcopenshell

def _wall_depth(model)->float:
    wall=model.by_type("IfcWall")[0]
    solid=next((item for rep in wall.Representation.Representations
                for item in rep.Items if item.is_a("IfcExtrudedAreaSolid")),None)
    if solid is None:
        raise ValueError("Expected native swept wall solid")
    return float(solid.Depth)


def evaluate(source_path:Path,result_path:Path)->dict:
    for item in (source_path,result_path):
        if item.is_symlink() or not item.is_file() or not 0<item.stat().st_size<=256*1024:
            raise ValueError("Unsafe or missing OWN IFC grader input")
    source=ifcopenshell.open(str(source_path))
    result=ifcopenshell.open(str(result_path))
    if source.schema!="IFC4X3" or result.schema!="IFC4X3":
        raise ValueError("OWN benchmark requires IFC4X3")
    if len(source.by_type("IfcWall"))!=1 or len(result.by_type("IfcWall"))!=1:
        raise ValueError("OWN benchmark requires one and only one Wall")
    source_roots={x.GlobalId:x for x in source.by_type("IfcRoot")}
    result_roots={x.GlobalId:x for x in result.by_type("IfcRoot")}
    if set(source_roots)!=set(result_roots):
        raise ValueError("Unexpected root identity creation/deletion")
    if any(source_roots[guid].is_a()!=result_roots[guid].is_a()
           for guid in source_roots):
        raise ValueError("Unexpected IFC native root class change")
    original_depth=_wall_depth(source)
    result_depth=_wall_depth(result)
    if abs(original_depth-3.0)>1e-6 or abs(result_depth-3.3)>1e-6:
        raise ValueError("Wrong trusted OWN wall edit depth")
    # For this OWN fixture we can additionally require byte-for-byte
    # identical STEP instances EXCEPT the one expected wall swept solid.
    # This is a narrow self-test oracle, NOT official IFC geometry scoring.
    source_steps={entity.id():str(entity) for entity in source}
    result_steps={entity.id():str(entity) for entity in result}
    if set(source_steps)!=set(result_steps):
        raise ValueError("Unexpected native STEP entity creation/deletion")
    changed=[identifier for identifier in source_steps
             if source_steps[identifier]!=result_steps[identifier]]
    if (len(changed)!=1
            or not source.by_id(changed[0]).is_a("IfcExtrudedAreaSolid")
            or not result.by_id(changed[0]).is_a("IfcExtrudedAreaSolid")):
        raise ValueError("Unexpected IFC entity modifications beyond wall depth")
    if sha256(source_path.read_bytes()).digest()==sha256(result_path.read_bytes()).digest():
        raise ValueError("No native output change observed")
    return {
        "status":"OWN_WALL_EDIT_VERIFIED",
        "source_schema":"IFC4X3",
        "output_schema":"IFC4X3",
        "native_wall_count":1,
        "original_wall_depth":original_depth,
        "result_wall_depth":result_depth,
        "root_global_ids_preserved":True,
        "only_expected_swept_wall_step_changed":True,
        "official_metric_score":None,
        "official_tasks_scored":0,
        "paid_model_calls":0,
    }


def main()->int:
    if len(sys.argv)!=3:
        return 2
    try:
        result=evaluate(Path(sys.argv[1]),Path(sys.argv[2]))
    except (ValueError,IndexError,RuntimeError,OSError):
        return 2
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
