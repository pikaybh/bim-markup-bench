"""Synthetic only: IFC4 source walls for GNI-schema engineering feasibility.

No GNI/BIBIMBAP original IFC, source-specific answer, benchmark scorer,
private GT, licenses, web download or model/provider input. Creates
self-authored deterministic IF4 building geometry with a single wall and
unrelated original slab. Two orientations and length-unit cases.

This is a developer regression fixture, NOT an independently blinded IFC.
"""
from __future__ import annotations

from pathlib import Path
import uuid
import numpy as np
import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit
import ifcopenshell.util.unit

NS=uuid.UUID("a2e142bf-3516-49cd-9e96-b7fad125a9fe")
def guid(label):
    return ifcopenshell.guid.compress(uuid.uuid5(NS,label).hex)

def fixture(*,unit:str,axis:str):
    assert unit in ("metre","millimetre") and axis in ("X","Y")
    f=ifcopenshell.api.project.create_file(version="IFC4")
    tag=f"{unit}-{axis}"
    project=ifcopenshell.api.root.create_entity(f,ifc_class="IfcProject",name="Synthetic IFC4 Project")
    units=[ifcopenshell.api.unit.add_si_unit(
        f,unit_type="LENGTHUNIT",**({"prefix":"MILLI"} if unit=="millimetre" else {})),
        ifcopenshell.api.unit.add_si_unit(f,unit_type="AREAUNIT"),
        ifcopenshell.api.unit.add_si_unit(f,unit_type="VOLUMEUNIT")]
    ifcopenshell.api.unit.assign_unit(f,units=units)
    top=ifcopenshell.api.context.add_context(f,context_type="Model")
    body=ifcopenshell.api.context.add_context(
        f,context_type="Model",context_identifier="Body",
        target_view="MODEL_VIEW",parent=top)
    site=ifcopenshell.api.root.create_entity(f,ifc_class="IfcSite",name="Synthetic Site")
    building=ifcopenshell.api.root.create_entity(f,ifc_class="IfcBuilding",name="Synthetic Building")
    storey=ifcopenshell.api.root.create_entity(f,ifc_class="IfcBuildingStorey",name="Synthetic Storey")
    storey.Elevation=0.
    for parent,child in ((project,site),(site,building),(building,storey)):
        ifcopenshell.api.aggregate.assign_object(f,products=[child],relating_object=parent)
    wall=ifcopenshell.api.root.create_entity(f,ifc_class="IfcWall",name="Blank Hosted Wall")
    rep=ifcopenshell.api.geometry.add_wall_representation(
        f,context=body,length=6.,height=3.,thickness=.2)
    ifcopenshell.api.geometry.assign_representation(f,product=wall,representation=rep)
    ifcopenshell.api.spatial.assign_container(f,products=[wall],relating_structure=storey)
    mat=np.eye(4)
    if axis=="Y":
        mat[:3,0]=[0.,1.,0.]
        mat[:3,1]=[-1.,0.,0.]
    ifcopenshell.api.geometry.edit_object_placement(f,product=wall,matrix=mat)
    slab=ifcopenshell.api.root.create_entity(f,ifc_class="IfcSlab",name="Unrelated Retained Ground Slab")
    rep2=ifcopenshell.api.geometry.add_slab_representation(
        f,context=body,depth=.25,
        polyline=[(0.,1.),(6.,1.),(6.,5.),(0.,5.),(0.,1.)])
    ifcopenshell.api.geometry.assign_representation(f,product=slab,representation=rep2)
    ifcopenshell.api.spatial.assign_container(f,products=[slab],relating_structure=storey)
    sm=np.eye(4)
    sm[:3,3]=[0.,0.,-.25]
    ifcopenshell.api.geometry.edit_object_placement(f,product=slab,matrix=sm)
    for i,root in enumerate(f.by_type("IfcRoot")):
        root.GlobalId=guid(f"source-{tag}-root-{i}-{root.is_a()}")
    # IfcOpenShell's SET attributes are not stable in native serialization:
    # canonicalize only original-author fixture SET order, not semantics.
    assignment=f.by_type("IfcUnitAssignment")
    assert len(assignment)==1
    assignment[0].Units=tuple(sorted(
        assignment[0].Units,key=lambda u:(u.UnitType,u.is_a())))
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        rel.RelatedElements=tuple(sorted(
            rel.RelatedElements,key=lambda entity:entity.GlobalId))
    f.header.file_name.name="synthetic_ifc4_"+tag+".ifc"
    f.header.file_name.time_stamp="2026-11-19T00:00:00"
    assert f.schema=="IFC4"
    assert abs(ifcopenshell.util.unit.calculate_unit_scale(f)-
               (1.0 if unit=="metre" else 0.001))<1e-12
    assert len(f.by_type("IfcWall"))==1 and len(f.by_type("IfcSlab"))==1
    assert not f.by_type("IfcDoor") and not f.by_type("IfcOpeningElement")
    return f


def write_fresh(path:Path,*,unit:str,axis:str):
    path=Path(path)
    assert path.parent.is_dir() and not path.exists()
    f=fixture(unit=unit,axis=axis)
    f.write(str(path))
    assert path.is_file() and path.stat().st_size>2000
    return path
