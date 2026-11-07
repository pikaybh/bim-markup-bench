"""Independently written manual IfcOpenShell reference recipes for G1 gate.

It DOES NOT import or invoke the direct XML compiler, its geometric mutation
helpers, binder or semantic graph. These are deterministic non-LLM I0 recipes
using only a common pinned IFC input, a frozen scenario and explicit GUID.
"""
from __future__ import annotations

import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import numpy as np


def _entity(model,guid):
    result=model.by_guid(guid)
    if result is None:
        raise ValueError("Source IFC entity is missing")
    return result


def _wall_body(wall):
    representation=wall.Representation
    bodies=[i for r in representation.Representations
            if r.RepresentationType=="SweptSolid"
            for i in r.Items if i.is_a("IfcExtrudedAreaSolid")]
    if len(bodies)!=1:
        raise ValueError("Reference recipe expects precisely one wall solid")
    return bodies[0]


def manual_ifc_reference(
    source:Path,destination:Path,operation:str,
    *,target_guid:str="",new_guid:str="",storey_guid:str="",
    first_guid:str="",second_guid:str="",
    height:float=0.0,delta_x:float=0.0,
    start:tuple[float,float,float]=(0.,5.,0.),
    end:tuple[float,float,float]=(4.,5.,0.),
):
    """One operation, one independently generated IFC; no compiler imports."""
    if destination.exists():
        raise ValueError("Oracle output must be new")
    model=ifcopenshell.open(str(source))
    if operation=="UPDATE_WALL_HEIGHT":
        wall=_entity(model,target_guid)
        if not wall.is_a("IfcWall") or height<=0:
            raise ValueError("Invalid reference wall height")
        _wall_body(wall).Depth=float(height)
    elif operation=="MOVE_OPENING":
        opening=_entity(model,target_guid)
        if not opening.is_a("IfcOpeningElement"):
            raise ValueError("Wrong reference opening class")
        pos=opening.ObjectPlacement.RelativePlacement.Location
        old=tuple(pos.Coordinates)
        pos.Coordinates=(float(old[0]+delta_x),float(old[1]),float(old[2]))
    elif operation=="DELETE_WINDOW":
        window=_entity(model,target_guid)
        if not window.is_a("IfcWindow"):
            raise ValueError("Wrong reference window class")
        ifcopenshell.api.root.remove_product(model,product=window)
    elif operation=="CREATE_WALL":
        if not new_guid or not storey_guid:
            raise ValueError("Missing reference wall GUID or storey")
        storey=_entity(model,storey_guid)
        if not storey.is_a("IfcBuildingStorey"):
            raise ValueError("Reference target is not storey")
        # Explicitly authored world endpoints, height, thickness; no
        # runtime XML compiler planning helpers are imported.
        x1,y1,z1=(float(v) for v in start)
        x2,y2,z2=(float(v) for v in end)
        dx=x2-x1;dy=y2-y1
        length=math.hypot(dx,dy)
        if length<=0.01 or abs(z1-z2)>1e-8:
            raise ValueError("Reference manual wall requires straight, horizontal endpoints")
        contexts=[c for c in model.by_type("IfcGeometricRepresentationSubContext")
                  if c.ContextIdentifier=="Body" and c.TargetView=="MODEL_VIEW"]
        if len(contexts)!=1:
            raise ValueError("No unique source body context")
        wall=ifcopenshell.api.root.create_entity(model,ifc_class="IfcWall",
                                                name="Created by declarative XML")
        wall.GlobalId=new_guid
        representation=ifcopenshell.api.geometry.add_wall_representation(
            model,context=contexts[0],length=length,height=3.0,thickness=0.2)
        ifcopenshell.api.geometry.assign_representation(model,product=wall,
                                                        representation=representation)
        frame=np.eye(4,dtype=np.float64)
        frame[:3,0]=[dx/length,dy/length,0.]
        frame[:3,1]=[-dy/length,dx/length,0.]
        frame[:3,3]=[x1,y1,z1]
        ifcopenshell.api.geometry.edit_object_placement(model,product=wall,matrix=frame)
        ifcopenshell.api.spatial.assign_container(model,products=[wall],relating_structure=storey)
    elif operation=="DELETE_WALL":
        wall=_entity(model,target_guid)
        if not wall.is_a("IfcWall"):
            raise ValueError("Deletion target was not a native IfcWall")
        ifcopenshell.api.root.remove_product(model,product=wall)
    elif operation=="ADD_CONNECTION":
        a=_entity(model,first_guid)
        b=_entity(model,second_guid)
        if not (a.is_a("IfcWall") and b.is_a("IfcWall")):
            raise ValueError("Reference connection endpoints are not walls")
        model.create_entity("IfcRelConnectsElements",GlobalId=new_guid,
                            RelatingElement=a,RelatedElement=b)
    elif operation=="REMOVE_CONNECTION":
        relation=_entity(model,target_guid)
        if not relation.is_a("IfcRelConnectsElements"):
            raise ValueError("Reference target was not a wall connection")
        model.remove(relation)
    else:
        raise ValueError("Unknown manual IFC reference operation")
    model.write(str(destination))
    return destination
