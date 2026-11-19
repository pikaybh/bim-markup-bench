"""v0.29 verified read-only projection of physically axis-aligned flipped-Z Slab.

This opt-in addition uses the EXISTING typed <Slab x y z width depth thickness>
schema, without inventing a new native-geometry field or exposing an
unverified mesh bounding box as an editable rectangle. The source physical
representation is restricted to one exact rectangular IfcExtrudedAreaSolid,
no clipping, boolean, oblique, mapped, or layer deform operations. Compute
all eight native corners from both native placement transforms and require
all eight corners of an actual axis-aligned cuboid, with Z thickness matching
original native extrusion depth. No C++ geometry mutation or LLM is used.
"""
from __future__ import annotations

from itertools import product
import math

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np

def verified_flipped_slab_attrs(entity,known_levels,scale:float)->dict[str,str]:
    from src.runtime.ifc_projection import (
        UnsupportedIFCGeometry,_body_extrusion,_rect_extents,_m,
        _level,_id,_number,
    )
    def fail(message:str):
        raise UnsupportedIFCGeometry(message)
    if entity.is_a()!="IfcSlab" or entity.PredefinedType!="FLOOR":
        fail("Flipped native cuboid projection requires an existing floor Slab")
    shape=entity.Representation
    if (shape is None or len(shape.Representations)!=1
        or shape.Representations[0].RepresentationIdentifier!="Body"
        or shape.Representations[0].RepresentationType!="SweptSolid"
        or len(shape.Representations[0].Items)!=1):
        fail("Slab does not have exactly one unclipped swept solid Body")
    item=_body_extrusion(entity)
    if not item.SweptArea.is_a("IfcRectangleProfileDef"):
        fail("Slab swept profile is not exactly rectangular")
    profile=item.SweptArea
    if profile.Position is not None and profile.Position.RefDirection is not None:
        direction=profile.Position.RefDirection.DirectionRatios
        if not np.allclose(direction,(1.,0.),rtol=0,atol=1e-8):
            fail("Original native slab profile has unsupported rotated 2D frame")
    x0,y0,x1,y1=_rect_extents(profile)
    if item.Position is None:
        fail("Flipped native slab extrusion frame absent")
    transform=_m(entity) @ np.asarray(
        ifcopenshell.util.placement.get_axis2placement(item.Position),dtype=np.float64
    )
    if transform.shape!=(4,4) or not np.isfinite(transform).all():
        fail("Slab physical source transformation nonfinite")
    axes=transform[:3,:3]
    if (not np.allclose(axes.T@axes,np.eye(3),rtol=0,atol=1e-8)
        or not np.allclose(np.abs(axes).sum(axis=0),(1.,1.,1.),rtol=0,atol=1e-8)
        or not np.allclose(np.abs(axes).sum(axis=1),(1.,1.,1.),rtol=0,atol=1e-8)):
        fail("Slab native physical frame is not world-axis-aligned right-angle frame")
    if not np.allclose(axes[:,2],(0.,0.,-1.),rtol=0,atol=1e-8):
        fail("Slab extrusion Z is not precisely flipped downward")
    raw=np.array([
        transform@np.array((float(x),float(y),float(z),1.),dtype=np.float64)
        for x,y,z in product((x0,x1),(y0,y1),(0.,float(item.Depth)))
    ],dtype=np.float64)
    points=raw[:,:3]
    if len(points)!=8 or not np.isfinite(points).all():
        fail("Source slab did not produce eight native corners")
    low=np.min(points,axis=0)
    high=np.max(points,axis=0)
    dims=high-low
    if (np.any(dims<=1e-9) or np.any(dims>10000)
        or not math.isclose(dims[2],float(item.Depth),rel_tol=0,abs_tol=1e-8)):
        fail("Original slab native extrusion dimensions unsafe")
    expected=np.array(list(product(*zip(low,high))),dtype=np.float64)
    if any(not np.any(np.all(np.abs(points-corner)<1e-8,axis=1))
           for corner in expected):
        fail("Slab original eight source vertices do not form exact physical cuboid")
    return {
        "id":_id(entity),"ifcGuid":entity.GlobalId,
        "level":_level(entity,known_levels),
        "x":_number(low[0]*scale),
        "y":_number(low[1]*scale),
        "z":_number(low[2]*scale),
        "width":_number(dims[0]*scale),
        "depth":_number(dims[1]*scale),
        "thickness":_number(dims[2]*scale),
    }
