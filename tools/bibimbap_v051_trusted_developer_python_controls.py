"""Developer-authored direct IfcOpenShell IFC4X3 control fixtures (NOT model code).

Runs only trusted static Python on Windows. Model-authored execution is
restricted to the pinned Linux Docker worker, unavailable if daemon is down.
"""
from __future__ import annotations
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import ifcopenshell.util.placement
import numpy as np

from tools.bibimbap_matched25_tools import file_hash
from src.runtime.experimental_v44_original_native_step_readonly import PINS, check_original_native_readonly_source
from tools.bibimbap_v045_independent_native_mutation_oracle import _body_solid
from tools.audit_bibimbap_v048_original4_semantic_controls import (
    _developer_rectangle_fix_source_only,
    _developer_delete_set_from_original_storey,
    _named_slab,
)


def make_independent_native_python_control(
    source: Path, destination: Path, *,
    original_sha: str, task_id: str, public_question: str,
    positive: bool,
) -> dict:
    """Direct IfcOpenShell authoring; NEVER invokes XML/D compiler or edit plan."""
    source, destination = Path(source), Path(destination)
    if not (source.is_file() and file_hash(source)==original_sha
            and original_sha in PINS and PINS[original_sha][0] == task_id
            and destination.parent.is_dir() and not destination.exists()
            and not destination.is_symlink()):
        raise ValueError("Source original hash, task or fresh file invalid")
    f=ifcopenshell.open(str(source))
    check_original_native_readonly_source(source, original_sha, f)
    if task_id=="geometry_test_14":
        slab,=f.by_type("IfcSlab")
        profile=_body_solid(slab,False).SweptArea
        dims=[float(profile.XDim),float(profile.YDim)]
        wanted=max(dims) if positive else (min(dims)+max(dims))/2
        if dims[0]<dims[1]: profile.XDim=wanted
        else: profile.YDim=wanted
    elif task_id=="geometry_test_15":
        guid,x,y=_developer_rectangle_fix_source_only(f)
        c=f.by_guid(guid)
        placement=c.ObjectPlacement
        world=ifcopenshell.util.placement.get_local_placement(placement)
        if not positive:
            x=(x+float(world[0,3])/1000)/2
            y=(y+float(world[1,3])/1000)/2
        parent=placement.PlacementRelTo
        pm=(ifcopenshell.util.placement.get_local_placement(parent)
            if parent is not None else np.eye(4))
        local=np.linalg.inv(pm)@np.array([x*1000,y*1000,world[2,3],1.0])
        if not np.isfinite(local).all():
            raise ValueError("Column XY unrepresentable")
        placement.RelativePlacement.Location.Coordinates=tuple(
            round(float(v),6) for v in local[:3])
    elif task_id=="topological_test_11":
        slab=_named_slab(public_question,f)
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        slab_shape=ifcopenshell.geom.create_shape(settings,slab)
        slab_z=min(list(slab_shape.geometry.verts)[2::3])
        cols=f.by_type("IfcColumn")
        if len(cols)!=2:raise ValueError("Two original Columns required")
        bases=[]
        for c in cols:
            column_shape=ifcopenshell.geom.create_shape(settings,c)
            bases.append(min(list(column_shape.geometry.verts)[2::3]))
        if max(bases)-min(bases)>0.0001:
            raise ValueError("Columns must share a base")
        shared=_body_solid(cols[0],True)
        if shared.id()!=_body_solid(cols[1],True).id():
            raise ValueError("Original mapped body not shared")
        target=slab_z-bases[0]
        current=float(shared.Depth)/1000
        shared.Depth=round((target if positive else (target+current)/2)*1000,6)
    elif task_id=="topological_test_17":
        slab=_named_slab(public_question,f)
        delete=_developer_delete_set_from_original_storey(f,slab.GlobalId)
        for guid in (delete if positive else delete[:4]):
            ifcopenshell.api.run("root.remove_product",f,product=f.by_guid(guid))
    else:
        raise ValueError("Original task is not in four pinned sources")
    if file_hash(source)!=original_sha:
        raise ValueError("Original source bytes changed")
    f.write(str(destination))
    if not destination.is_file() or file_hash(source)!=original_sha:
        raise ValueError("Original IFC source mutated after trusted direct authoring")
    return {
        "task_id":task_id,
        "positive_developer_control":bool(positive),
        "candidate_sha256":file_hash(destination),
        "source_sha256":original_sha,
        "trusted_offline_Python_IfcOpenShell_API_actually_run":True,
        "untrusted_model_python_executed":False,
        "python_executed_in_pinned_Docker":False,
        "original_author_grader_called":False,
    }
