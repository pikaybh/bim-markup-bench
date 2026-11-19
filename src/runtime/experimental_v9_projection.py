"""Prospective IFC4X3 native complex v0.9 partial declarative source view.

This extends read-only v0.7 *only* with BooleanClipping original IfcWalls
whose ORIGINAL world native meshes are exactly a complete orthogonal box.
Their STEP body (IfcBooleanClippingResult, half-space, connections) remains
SOURCE-OWNED OPAQUE. The XML exposes a stable axis for safely attaching a
new hosted Opening + Door, not authorization to reshape/rebuild Walls.

Earlier v0.1-v0.8 code and frozen paper data remain unchanged.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np
from lxml import etree

from src.runtime.experimental_v7_projection import (
    project_ifc_v7,_mesh_exact_axis_box,V7CompatError,
)
from src.runtime.ifc_projection import (
    _id,_number,UnsupportedIFCGeometry,
)
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.xml_parser import parse_xml
from src.runtime.markup_normal_form import NS

EPS=2e-5


class ComplexV9ProjectionError(ValueError):
    pass


def _boolean_wall_attrs(model,wall,level_id):
    if wall.Representation is None:
        raise ComplexV9ProjectionError("Native Boolean Wall lacks representation")
    bodies=[it for rep in wall.Representation.Representations
            if rep.RepresentationType=="Clipping" for it in rep.Items]
    if (len(bodies)!=1 or not bodies[0].is_a("IfcBooleanClippingResult")
        or not bodies[0].SecondOperand.is_a("IfcPolygonalBoundedHalfSpace")
        or not bodies[0].FirstOperand.is_a("IfcExtrudedAreaSolid")):
        raise ComplexV9ProjectionError("Only original single-halfspace BooleanClipping IfcWall")
    if any(r.is_a("IfcRelVoidsElement") or r.is_a("IfcRelSpaceBoundary")
           for r in model.get_inverse(wall)):
        raise ComplexV9ProjectionError("Already hosted or bounded native Wall is opaque")
    low,high=_mesh_exact_axis_box(wall)  # actual original native 8 corner/12 face
    low,high=np.asarray(low),np.asarray(high)
    ext=high-low
    if (abs(ext[2])<.25 or ext[2]>100 or
        sum(ext[:2]>.5)!=1 or sum(ext[:2]<.5)!=1):
        raise ComplexV9ProjectionError("Boolean Wall physical extents not a long straight prism")
    horizontal=int(np.argmax(ext[:2]))
    thickness=float(ext[1-horizontal])
    length=float(ext[horizontal])
    if not .05<thickness<=.5 or not .5<length<=100:
        raise ComplexV9ProjectionError("Boolean Wall dimensions outside original native bounds")
    # The original Curve2D Wall baseline must agree with the long physical
    # world axis; the XML is an envelope centerline, not a fake extrusion.
    axis=[x for rep in wall.Representation.Representations
          if rep.RepresentationType=="Curve2D"
          for x in rep.Items if x.is_a("IfcPolyline") and len(x.Points)==2]
    if len(axis)!=1:
        raise ComplexV9ProjectionError("Boolean Wall missing unique original line-axis")
    transform=np.asarray(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement))
    if not np.allclose(transform[:3,:3].T@transform[:3,:3],np.eye(3),atol=1e-7):
        raise ComplexV9ProjectionError("Original Boolean Wall source frame not rigid")
    endpoints=[]
    for p in axis[0].Points:
        local=p.Coordinates
        if len(local)!=2:
            raise ComplexV9ProjectionError("Original native Wall line axis not 2D")
        endpoints.append((transform@np.array([float(local[0]),float(local[1]),0.,1.]))[:3])
    segment=np.asarray(endpoints[1])-np.asarray(endpoints[0])
    if (abs(segment[2])>EPS or
        abs(segment[1-horizontal])>EPS or
        abs(segment[horizontal])<.5):
        raise ComplexV9ProjectionError("Native original Wall line inconsistent with physical rectangular axis")
    # The original Boolean clipping may shorten an axis but may not invent a
    # new physically editable Wall. Report the exact native mesh envelope.
    centerline=(low+high)/2
    a=centerline.copy();b=centerline.copy()
    a[horizontal]=low[horizontal]
    b[horizontal]=high[horizontal]
    a[2]=b[2]=low[2]
    if not (np.min(np.abs([x[1-horizontal]-centerline[1-horizontal] for x in endpoints]))<EPS):
        raise ComplexV9ProjectionError("Original axis and native physical centerline do not agree")
    return {
        "id":_id(wall),"ifcGuid":wall.GlobalId,"level":level_id,
        "x1":_number(a[0]),"y1":_number(a[1]),"z1":_number(a[2]),
        "x2":_number(b[0]),"y2":_number(b[1]),"z2":_number(b[2]),
        "height":_number(ext[2]),"thickness":_number(thickness),
    }


def project_ifc_v9(source:Path):
    original=project_ifc_v7(source)
    model=ifcopenshell.open(str(source))
    if model.schema!="IFC4X3":
        raise ComplexV9ProjectionError("v0.9 is native IFC4X3 only")
    source_sha=original.source.source_sha256
    root=etree.fromstring(original.xml)
    elements=root.find("{"+NS+"}Elements")
    levelids={
        el.get("ifcGuid"):el.get("id")
        for el in root.findall("./{"+NS+"}Levels/{"+NS+"}Level")
    }
    known=dict(original.projected_global_ids)
    added=[]
    for wall in sorted(model.by_type("IfcWall"),key=lambda e:e.GlobalId):
        if wall.GlobalId in known:
            continue
        storey=ifcopenshell.util.element.get_container(wall)
        if storey is None or storey.GlobalId not in levelids:
            continue
        try:
            attrs=_boolean_wall_attrs(model,wall,levelids[storey.GlobalId])
        except (ComplexV9ProjectionError,V7CompatError,UnsupportedIFCGeometry,
                ValueError,AttributeError,RuntimeError,TypeError):
            continue
        if attrs["id"] in known.values():
            raise ComplexV9ProjectionError("Original Boolean Wall local stable-ID collision")
        etree.SubElement(elements,"{"+NS+"}Wall",attrib=attrs)
        known[wall.GlobalId]=attrs["id"]
        added.append(wall.GlobalId)
    if not added:
        return original  # v0.7 was already sufficient; exact old XML bytes
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=True)
    parse_xml(xml,expected_source_sha256=source_sha)
    counts=Counter(dict(original.supported_class_counts))
    opaque=Counter(dict(original.unsupported_class_counts))
    if opaque["IfcWall"]<len(added):
        raise ComplexV9ProjectionError("Source-native opaque Wall inventory mismatch")
    counts["IfcWall"]+=len(added)
    opaque["IfcWall"]-=len(added)
    if opaque["IfcWall"]==0:
        del opaque["IfcWall"]
    result=replace(
        original,
        xml=xml,
        projected_global_ids=tuple(sorted(known.items())),
        opaque_references=tuple(x for x in original.opaque_references
                                if x.ifc_guid not in added),
        supported_class_counts=tuple(sorted(counts.items())),
        unsupported_class_counts=tuple(sorted(opaque.items())),
        opaque_relation_reasons=tuple(sorted(set(original.opaque_relation_reasons)|{
            "Original native BooleanClipping Wall STEP and original connection geometry remain source-owned opaque"
        })),
    )
    if snapshot_source(source).source_sha256!=source_sha:
        raise ComplexV9ProjectionError("Original IFC source changed during read-only v0.9 projection")
    return result
