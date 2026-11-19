"""Self-authored small IFC4 Window+Opening native source, never GNI/BIBIMBAP.

Two exclusive hosted IFC4 Window assemblies on one 6-m Wall, each Window
has an explicit relative placement parented by its own Opening. Original
unrelated opaque Slab stays unchanged. Uses metre/mm and X/Y wall axes.
Every root GUID and unordered original IFC SET is canonical for identical
source SHA across separate runs. No task answer, scorer or provider data.
"""
from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.api.context
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.unit
import numpy as np

from tools.bibimbap_v066_ifc4_synthetic_host import (
    fixture as blank_host, guid,
)


def fixture(*,unit:str,axis:str):
    assert unit in ("metre","millimetre") and axis in ("X","Y")
    f=blank_host(unit=unit,axis=axis)
    tag=f"{unit}-{axis}"
    host=f.by_type("IfcWall")[0]
    storey=f.by_type("IfcBuildingStorey")[0]
    bodies=[c for c in f.by_type("IfcGeometricRepresentationSubContext")
            if c.ContextIdentifier=="Body" and c.TargetView=="MODEL_VIEW"]
    assert len(bodies)==1
    body=bodies[0]
    scale=ifcopenshell.util.unit.calculate_unit_scale(f)
    for idx,along in enumerate((1.1,3.6)):
        opening=ifcopenshell.api.root.create_entity(
            f,ifc_class="IfcOpeningElement",name=f"Synthetic Window Opening {idx}")
        op_rep=ifcopenshell.api.geometry.add_wall_representation(
            f,context=body,length=1.0,height=1.3,thickness=.3)
        ifcopenshell.api.geometry.assign_representation(
            f,product=opening,representation=op_rep)
        frame=np.eye(4)
        if axis=="X":
            frame[:3,3]=[along,-.05,1.]
        else:
            frame[:3,0]=[0.,1.,0.]
            frame[:3,1]=[-1.,0.,0.]
            frame[:3,3]=[.05,along,1.]
        ifcopenshell.api.geometry.edit_object_placement(
            f,product=opening,matrix=frame)
        ifcopenshell.api.feature.add_feature(f,feature=opening,element=host)
        window=ifcopenshell.api.root.create_entity(
            f,ifc_class="IfcWindow",name=f"Synthetic Window {idx}")
        window.OverallWidth=round(.8/scale,6)
        window.OverallHeight=round(1.1/scale,6)
        winrep=ifcopenshell.api.geometry.add_wall_representation(
            f,context=body,length=.8,height=1.1,thickness=.06)
        ifcopenshell.api.geometry.assign_representation(
            f,product=window,representation=winrep)
        # These CARTESIANPOINT coordinates are native IFC length units:
        # local X is wall length; local Y is the cross-face window inset.
        loc=f.createIfcCartesianPoint((.1/scale,.10/scale,.1/scale))
        axis2=f.createIfcAxis2Placement3D(loc,None,None)
        window.ObjectPlacement=f.createIfcLocalPlacement(
            opening.ObjectPlacement,axis2)
        ifcopenshell.api.feature.add_filling(
            f,opening=opening,element=window)
        ifcopenshell.api.spatial.assign_container(
            f,products=[window],relating_structure=storey)
    roots=f.by_type("IfcRoot")
    for i,root in enumerate(roots):
        root.GlobalId=guid(f"window-source-{tag}-{i}-{root.is_a()}")
    assignments=f.by_type("IfcUnitAssignment")
    assert len(assignments)==1
    assignments[0].Units=tuple(sorted(
        assignments[0].Units,key=lambda u:(u.UnitType,u.is_a())))
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        rel.RelatedElements=tuple(sorted(
            rel.RelatedElements,key=lambda e:e.GlobalId))
    for rel in f.by_type("IfcRelAggregates"):
        rel.RelatedObjects=tuple(sorted(
            rel.RelatedObjects,key=lambda e:e.GlobalId))
    f.header.file_name.name=f"synthetic_ifc4_window_{tag}.ifc"
    f.header.file_name.time_stamp="2026-11-19T00:00:00"
    assert f.schema=="IFC4"
    assert len(f.by_type("IfcWindow"))==2
    assert len(f.by_type("IfcOpeningElement"))==2
    assert len(f.by_type("IfcRelFillsElement"))==2
    assert len(f.by_type("IfcRelVoidsElement"))==2
    return f


def write_fresh(path:Path,*,unit:str,axis:str):
    path=Path(path)
    assert path.parent.is_dir() and not path.exists()
    model=fixture(unit=unit,axis=axis)
    model.write(str(path))
    assert path.is_file() and path.stat().st_size>4500
    return path
