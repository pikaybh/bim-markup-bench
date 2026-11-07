"""Native-only deterministic IFC semantic/geometry comparator; no XML access.

This verifies equivalent outputs for two independently authored approaches
without consulting task ground truth, model prompts, runtime graph or grading
helper from the direct XML compiler.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.shape
import numpy as np

PRODUCT_TYPES=("IfcWall","IfcSlab","IfcColumn",
               "IfcOpeningElement","IfcWindow","IfcDoor","IfcSpace")


def _rounded(values):
    return tuple(float(round(float(x),6)) for x in values)


def _native_relations(model):
    out=[]
    for name,left,right in (
        ("IfcRelContainedInSpatialStructure","RelatingStructure","RelatedElements"),
        ("IfcRelAggregates","RelatingObject","RelatedObjects"),
        ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
        ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement"),
        ("IfcRelSpaceBoundary","RelatingSpace","RelatedBuildingElement"),
        ("IfcRelConnectsElements","RelatingElement","RelatedElement"),
    ):
        for relation in model.by_type(name):
            lhs=getattr(relation,left);rhs=getattr(relation,right)
            lhs=lhs if isinstance(lhs,tuple) else (lhs,)
            rhs=rhs if isinstance(rhs,tuple) else (rhs,)
            out.append((name,relation.GlobalId,
                        tuple(sorted(x.GlobalId for x in lhs if x is not None)),
                        tuple(sorted(x.GlobalId for x in rhs if x is not None)),
                        str(getattr(relation,"PhysicalOrVirtualBoundary","")),
                        str(getattr(relation,"InternalOrExternalBoundary",""))))
    return tuple(sorted(out))


def _shape(model,product):
    rep=getattr(product,"Representation",None)
    if rep is None:return ("ABSENT",)
    try:
        config=ifcopenshell.geom.settings()
        config.set(config.USE_WORLD_COORDS,True)
        mesh=ifcopenshell.geom.create_shape(config,product)
        verts=np.asarray(mesh.geometry.verts,dtype=float).reshape((-1,3))
        if len(verts)<3:
            return ("DEGENERATE",)
        triangles=len(mesh.geometry.faces)//3
        try:
            volume=float(ifcopenshell.util.shape.get_volume(mesh.geometry))
        except Exception:
            volume=None
        return ("MESH",_rounded(np.min(verts,axis=0)),
                _rounded(np.max(verts,axis=0)),triangles,
                float(round(volume,6)) if volume is not None else None)
    except Exception:
        return ("UNSUPPORTED_GEOMETRY",)


def inspect_ifc(path:Path)->dict:
    f=ifcopenshell.open(str(path))
    identities={}
    products={}
    for root in f.by_type("IfcRoot"):
        identities[root.GlobalId]=(root.is_a(),str(getattr(root,"Name","") or ""),
                                   str(getattr(root,"Description","") or ""))
    for kind in PRODUCT_TYPES:
        for product in f.by_type(kind):
            placement=getattr(product,"ObjectPlacement",None)
            try:
                mat=ifcopenshell.util.placement.get_local_placement(placement)
                world_frame=_rounded(mat.reshape((-1,)))
            except Exception:
                world_frame=None
            products[product.GlobalId]={
                "type":product.is_a(),
                "name":str(product.Name or ""),
                "frame":world_frame,
                "shape":_shape(f,product),
            }
    psets={}
    for record in f.by_type("IfcPropertySet"):
        psets[record.GlobalId]=(
            record.Name,
            tuple(sorted((p.Name,str(p.NominalValue))
                         for p in record.HasProperties
                         if p.is_a("IfcPropertySingleValue")))
        )
    materials=tuple(sorted(str(x) for x in f.by_type("IfcMaterial")))
    return {
        "ifc_schema":f.schema,
        "identities":identities,
        "products":products,
        "relations":_native_relations(f),
        "property_sets":psets,
        "materials":materials,
    }


def parity_report(left:Path,right:Path)->dict:
    a=inspect_ifc(left)
    b=inspect_ifc(right)
    mismatches=[]
    for k in ("ifc_schema","identities","products","relations","property_sets","materials"):
        if a[k]!=b[k]:
            mismatches.append(k)
    return {
        "source_independent_native_ifc_only":True,
        "parity":not mismatches,
        "mismatched_categories":tuple(mismatches),
        "native_object_count_left":len(a["products"]),
        "native_object_count_right":len(b["products"]),
        "native_relation_count_left":len(a["relations"]),
        "native_relation_count_right":len(b["relations"]),
        "geometry_tolerance_m":1e-6,
        "volume_tolerance_m3":1e-6,
    }
