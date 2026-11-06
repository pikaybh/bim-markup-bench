#!/usr/bin/env python3
"""Generate ONLY original tiny IFC4X3 fixtures for isolated benchmark tests.

No Xim/BIXML data, proprietary objects, benchmark GT or paid services.
Stable synthetic GUIDs are derived from an internal UUID namespace to make
semantic models comparable across reruns; the generated textual STEP index
may depend on IfcOpenShell version, which is pinned separately.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import uuid

import numpy as np
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.profile
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit

NS = uuid.UUID("16f763e1-5b4f-4055-b5af-c2a9f5347ed3")

def stable_guid(name: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(NS,name).hex)

def assign_guid(entity, label: str):
    entity.GlobalId=stable_guid(label)
    return entity

def place(model, product, xyz):
    mat = np.eye(4, dtype="float64")
    mat[:3,3]=xyz
    ifcopenshell.api.geometry.edit_object_placement(model,product=product,matrix=mat)

def build(*, wall_height: float = 3.0, window_offset: float = 1.6) -> ifcopenshell.file:
    model=ifcopenshell.api.project.create_file(version="IFC4X3")
    project=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcProject",name="Toy Evidence Project"),"project")
    units=[
      ifcopenshell.api.unit.add_si_unit(model,unit_type="LENGTHUNIT"),
      ifcopenshell.api.unit.add_si_unit(model,unit_type="AREAUNIT"),
      ifcopenshell.api.unit.add_si_unit(model,unit_type="VOLUMEUNIT"),
    ]
    ifcopenshell.api.unit.assign_unit(model,units=units)
    top=ifcopenshell.api.context.add_context(model,context_type="Model")
    body=ifcopenshell.api.context.add_context(model,context_type="Model",context_identifier="Body",target_view="MODEL_VIEW",parent=top)
    site=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcSite",name="Synthetic Site"),"site")
    building=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcBuilding",name="Synthetic Building"),"building")
    storey=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcBuildingStorey",name="Level 1"),"storey")
    storey.Elevation=0.
    for parent, child in [(project,site),(site,building),(building,storey)]:
        ifcopenshell.api.aggregate.assign_object(model,products=[child],relating_object=parent)
    wall=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcWall",name="North Wall"),"wall")
    rep=ifcopenshell.api.geometry.add_wall_representation(model,context=body,length=6.,height=wall_height,thickness=.2)
    ifcopenshell.api.geometry.assign_representation(model,product=wall,representation=rep)
    ifcopenshell.api.spatial.assign_container(model,products=[wall],relating_structure=storey)
    place(model,wall,(0,0,0))
    slab=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcSlab",name="Ground Slab"),"slab")
    rep=ifcopenshell.api.geometry.add_slab_representation(model,context=body,depth=.25,polyline=[(0,0),(6,0),(6,5),(0,5),(0,0)])
    ifcopenshell.api.geometry.assign_representation(model,product=slab,representation=rep)
    ifcopenshell.api.spatial.assign_container(model,products=[slab],relating_structure=storey)
    place(model,slab,(0,0,-.25))
    column=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcColumn",name="Corner Column"),"column")
    profile=ifcopenshell.api.profile.add_parameterized_profile(model,ifc_class="IfcRectangleProfileDef")
    profile.XDim=.3
    profile.YDim=.3
    rep=ifcopenshell.api.geometry.add_profile_representation(model,context=body,profile=profile,depth=3.)
    ifcopenshell.api.geometry.assign_representation(model,product=column,representation=rep)
    ifcopenshell.api.spatial.assign_container(model,products=[column],relating_structure=storey)
    place(model,column,(5.7,4.7,0))
    space=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcSpace",name="Room 101"),"space")
    ifcopenshell.api.aggregate.assign_object(model,products=[space],relating_object=storey)
    rel= model.create_entity("IfcRelSpaceBoundary",GlobalId=stable_guid("space_boundary"),Name="Wall-to-Room Boundary",
        RelatingSpace=space,RelatedBuildingElement=wall,PhysicalOrVirtualBoundary="PHYSICAL",InternalOrExternalBoundary="INTERNAL")
    opening=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcOpeningElement",name="Window Opening"),"opening")
    orep=ifcopenshell.api.geometry.add_wall_representation(model,context=body,length=1.2,height=1.5,thickness=.3)
    ifcopenshell.api.geometry.assign_representation(model,product=opening,representation=orep)
    place(model,opening,(window_offset,0,.9))
    ifcopenshell.api.feature.add_feature(model,feature=opening,element=wall)
    window=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcWindow",name="North Window"),"window")
    window.OverallWidth=1.2
    window.OverallHeight=1.5
    wrep=ifcopenshell.api.geometry.add_wall_representation(model,context=body,length=1.2,height=1.5,thickness=.08)
    ifcopenshell.api.geometry.assign_representation(model,product=window,representation=wrep)
    place(model,window,(window_offset,.08,.9))
    ifcopenshell.api.feature.add_filling(model,opening=opening,element=window)
    ifcopenshell.api.spatial.assign_container(model,products=[window],relating_structure=storey)
    door=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcDoor",name="Entrance Door"),"door")
    door.OverallWidth=.9
    door.OverallHeight=2.1
    d_opening=assign_guid(ifcopenshell.api.root.create_entity(model,ifc_class="IfcOpeningElement",name="Door Opening"),"door_opening")
    dr=ifcopenshell.api.geometry.add_wall_representation(model,context=body,length=.9,height=2.1,thickness=.3)
    ifcopenshell.api.geometry.assign_representation(model,product=d_opening,representation=dr)
    place(model,d_opening,(3.7,0,0))
    ifcopenshell.api.feature.add_feature(model,feature=d_opening,element=wall)
    drep=ifcopenshell.api.geometry.add_wall_representation(model,context=body,length=.9,height=2.1,thickness=.06)
    ifcopenshell.api.geometry.assign_representation(model,product=door,representation=drep)
    place(model,door,(3.7,.07,0))
    ifcopenshell.api.feature.add_filling(model,opening=d_opening,element=door)
    ifcopenshell.api.spatial.assign_container(model,products=[door],relating_structure=storey)
    return model

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--outdir",type=Path,default=Path("tests/fixtures/synthetic"))
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    for name,kw in (
        ("input.ifc", {}),
        ("expected_wall_height.ifc", {"wall_height":3.3}),
        ("expected_window_move.ifc", {"window_offset":2.1}),
    ):
        f=build(**kw)
        out=args.outdir/name
        f.write(str(out))
        assert len(f.by_type("IfcRelVoidsElement"))==2
        assert len(f.by_type("IfcRelFillsElement"))==2
        assert len(f.by_type("IfcRelSpaceBoundary"))==1
        print(name,"bytes=",out.stat().st_size,"ifc_schema=",f.schema)

if __name__=="__main__":
    main()
