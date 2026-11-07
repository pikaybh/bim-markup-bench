"""Narrow physical IFC wall thickness operations, independent of LLM authoring.

A supported wall has a unique extruded rectangular body and no hosted, spatial
boundary, connected, type/material or other geometry-affecting dependencies.
Anything requiring void/host/space propagation fails CLOSED until G1 #15.
"""
from __future__ import annotations
from decimal import Decimal
import math
from typing import Any

import ifcopenshell
import ifcopenshell.geom

from src.runtime.ifc_projection import _body_extrusion, _rect_extents
from src.runtime.ifc_mutations import UnsupportedIFCMutation, _unique_wall_representation

_MAX_DIMENSION_M = 1000.
_EPS=1e-8

def wall_thickness_eligibility(model:ifcopenshell.file, wall:Any) -> tuple[Any,int]:
    if wall is None or not wall.is_a("IfcWall"):
        raise UnsupportedIFCMutation("Thickness edit requires native IfcWall")
    # Even a connection with no explicit ConnectionGeometry can need
    # junction regeneration; conservative until relationship rules are frozen.
    for relationship in model.get_inverse(wall):
        if relationship.is_a("IfcRelContainedInSpatialStructure"):
            continue
        raise UnsupportedIFCMutation(
            "Thickness editing a wall with host, connection, space boundary, "
            "material/type or other dependencies requires a future graph-aware compiler"
        )
    item=_unique_wall_representation(model,wall)
    profile=item.SweptArea
    try:
        a,b,c,d=_rect_extents(profile)
    except Exception as exc:
        raise UnsupportedIFCMutation("Only exact axis-aligned rectangular IFC wall profile supported") from exc
    if not (d-b>_EPS and c-a>_EPS):
        raise UnsupportedIFCMutation("Invalid original wall profile dimensions")
    # An IfcProfileDef may be reused by many solids. Mutating a shared
    # profile would silently alter unrelated geometry even when wall
    # ProductDefinitionShape ownership is otherwise unique.
    profile_users=[x for x in model.get_inverse(profile) if x.is_a("IfcExtrudedAreaSolid")]
    if len(profile_users)!=1 or profile_users[0].id()!=item.id():
        raise UnsupportedIFCMutation("IFC wall swept profile is shared by other geometry")
    if profile.is_a("IfcRectangleProfileDef"):
        # IfcRectangleProfileDef.YDim is the actual wall thickness.
        # A Revit wall can reference the same shape from a PresentationLayer;
        # it is safe if there is exactly one IfcProductDefinitionShape owner.
        return profile,profile.id()
    if not profile.is_a("IfcArbitraryClosedProfileDef"):
        raise UnsupportedIFCMutation("Wall is not a supported rectangular swept solid")
    curve=profile.OuterCurve
    if not curve.is_a("IfcIndexedPolyCurve"):
        raise UnsupportedIFCMutation("Unsupported IFC rectangular boundary encoding")
    if len([x for x in model.get_inverse(curve) if x.is_a("IfcArbitraryClosedProfileDef")])!=1:
        raise UnsupportedIFCMutation("Wall profile boundary is shared by other geometry")
    coords=curve.Points
    # Only one shape profile can own this point list. Other geometry reference
    # would make a shared edit affect unrelated objects.
    if len([x for x in model.get_inverse(coords) if x.is_a("IfcIndexedPolyCurve")])!=1:
        raise UnsupportedIFCMutation("Wall boundary points are shared across geometry objects")
    return profile,coords.id()


def edit_wall_thickness(model:ifcopenshell.file,wall:Any,requested:Decimal) -> int:
    thickness=float(requested)
    if not math.isfinite(thickness) or thickness<=_EPS or thickness>_MAX_DIMENSION_M:
        raise UnsupportedIFCMutation("Invalid wall thickness")
    profile,entity_id=wall_thickness_eligibility(model,wall)
    a,b,c,d=_rect_extents(profile)
    current=d-b
    if math.isclose(current,thickness,rel_tol=0.,abs_tol=1e-8):
        raise UnsupportedIFCMutation("No-op thickness change should be removed by semantic diff")
    if profile.is_a("IfcRectangleProfileDef"):
        profile.YDim=thickness
    else:
        curve=profile.OuterCurve
        points=tuple(tuple(float(v) for v in point) for point in curve.Points.CoordList)
        if len(points)!=5 or points[0]!=points[-1]:
            raise UnsupportedIFCMutation("Only five-point closed rectangle is supported")
        # Preserve the original min-Y profile edge; widen towards max-Y.
        max_y=b+thickness
        new=tuple((x,b if abs(y-b)<=1e-8 else max_y) for x,y in points)
        curve.Points.CoordList=new
    actual=_rect_extents(profile)
    if not math.isclose(actual[3]-actual[1],thickness,rel_tol=0,abs_tol=1e-7):
        raise UnsupportedIFCMutation("Actual IFC profile thickness mismatch after edit")
    try:
        shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),wall)
    except Exception as exc:
        raise UnsupportedIFCMutation("Wall geometry kernel cannot mesh modified thickness") from exc
    if len(shape.geometry.faces)<6 or len(shape.geometry.verts)<9:
        raise UnsupportedIFCMutation("Modified wall is degenerate")
    return entity_id
