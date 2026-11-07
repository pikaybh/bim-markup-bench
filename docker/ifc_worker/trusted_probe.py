"""Non-LLM trusted end-to-end IFC4X3 load/geometry/write probe.

The input IFC is a tiny OWN synthetic fixture only. Does not inspect
private GT, fetch anything, invoke model providers or execute a candidate.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import os
import resource
import socket
import sys

import ifcopenshell
import ifcopenshell.geom

def blocked(callback):
    try:
        callback()
        return False
    except (OSError,PermissionError):
        return True

source=Path("/input/input.ifc")
destination=Path("/output/result.ifc")
assert source.is_file(), "No synthetic IFC input"
original_hash=sha256(source.read_bytes()).hexdigest()
file=ifcopenshell.open(str(source))
assert file.schema=="IFC4X3", "Expected IFC4X3"
wall=file.by_type("IfcWall")[0]
assert wall.Representation is not None,"Expected own synthetic wall"
settings=ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS,True)
geometry=ifcopenshell.geom.create_shape(settings,wall)
assert len(geometry.geometry.verts)>0
file.write(str(destination))
reloaded=ifcopenshell.open(str(destination))
assert reloaded.by_guid(wall.GlobalId).is_a("IfcWall")
assert sha256(source.read_bytes()).hexdigest()==original_hash
result={
    "status":"TRUSTED_IFC_WORKER_SMOKE_PASS",
    "python":sys.version.split()[0],
    "ifcopenshell":ifcopenshell.version,
    "source_sha256":original_hash,
    "result_sha256":sha256(destination.read_bytes()).hexdigest(),
    "mesh_vertex_count":len(geometry.geometry.verts)//3,
    "input_write_denied":blocked(lambda:source.write_bytes(b"nope")),
    "GT_unmounted":not Path("/grader/ground_truth.ifc").exists(),
    "network_denied":blocked(lambda:socket.create_connection(("1.1.1.1",443),timeout=1)),
    "host_key_unavailable":not os.environ.get("OPENAI_API_KEY"),
    "uid":os.geteuid(),
    "OS_process_isolation_unverified_by_this_probe":True,
    "paid_model_calls":0,
}
Path("/output/probe.json").write_text(json.dumps(result,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
