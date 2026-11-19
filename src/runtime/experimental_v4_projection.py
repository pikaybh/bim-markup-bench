"""Experimental v0.4 READ-ONLY IFC4X3 Slab footprint envelope overlay.

Source native slab representation remains opaque. Only a unique rectangular
extrusion whose actual world-space mesh fills its axis-aligned bounding box
is projected. XML x,y,z represent the minimal native world-space corner;
width/depth/thickness represent its positive extents. The trusted mutation
backend owns conversions; the LLM sees no IfcOpenShell or imperative tools.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import numpy as np
from lxml import etree

from src.runtime.ifc_projection import (
    Projection,UnsupportedIFCGeometry,_id,_number,
)
from src.runtime.experimental_v3_projection import project_ifc_v3
from src.runtime.markup_normal_form import NS
from src.runtime.xml_parser import parse_xml
from src.runtime.ifc_snapshot import snapshot_source


class V4ProjectionError(ValueError):
    pass


def _slab_mesh_bbox(slab):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,slab)
    except Exception as exc:
        raise V4ProjectionError("Native IfcSlab mesh unavailable") from exc
    v=np.asarray(shape.geometry.verts,dtype=np.float64)
    if len(v)<24 or len(v)%3:
        raise V4ProjectionError("Native slab mesh incomplete")
    v=v.reshape((-1,3))
    if not np.all(np.isfinite(v)):
        raise V4ProjectionError("Nonfinite native slab geometry")
    low=v.min(axis=0);high=v.max(axis=0)
    extents=high-low
    if any(x<=0.01 or x>10000 for x in extents):
        raise V4ProjectionError("Slab dimension outside bounded native rectangle")
    # A general slab can have a void, partial solid, slope, polygon or nested
    # mapped geometry. NEVER replace those with its enclosing AABB.
    if not all(
        any(abs(float(p[i])-float(bound))<1e-5 for bound in (low[i],high[i]))
        for p in v for i in range(3)
    ):
        raise V4ProjectionError("Nonrectangular/rotated slab world-space mesh")
    corners={
        tuple(int(round((float(p[i])-low[i])/extents[i])) for i in range(3))
        for p in v
    }
    if len(corners)!=8 or any(any(bit not in (0,1) for bit in c) for c in corners):
        raise V4ProjectionError("Slab is not exactly a simple rectangular prism")
    return tuple(float(x) for x in low),tuple(float(x) for x in high)


def _source_slab_solid(model,slab):
    if slab.Representation is None:
        raise V4ProjectionError("Slab lacks native shape")
    reps=[x for rep in slab.Representation.Representations for x in rep.Items]
    if len(reps)!=1 or not reps[0].is_a("IfcExtrudedAreaSolid"):
        raise V4ProjectionError("No unique native slab direct extrusion")
    solid=reps[0]
    if not solid.SweptArea.is_a("IfcRectangleProfileDef"):
        raise V4ProjectionError("Slab's swept area not a native rectangle")
    if solid.Position is None or not solid.Position.is_a("IfcAxis2Placement3D"):
        raise V4ProjectionError("Native rectangle frame missing")
    return solid


def project_ifc_v4(source:Path)->Projection:
    previous=project_ifc_v3(source)
    model=ifcopenshell.open(str(source))
    root=etree.fromstring(previous.xml)
    elements=root.find("{"+NS+"}Elements")
    levels={
        elem.attrib["ifcGuid"]:elem.attrib["id"]
        for elem in root.findall(".//{"+NS+"}Level")
    }
    by_guid=dict(previous.projected_global_ids)
    included=[]
    for slab in sorted(model.by_type("IfcSlab"),key=lambda s:s.GlobalId):
        if slab.GlobalId in by_guid:
            continue
        storey=ifcopenshell.util.element.get_container(slab)
        if storey is None or storey.GlobalId not in levels:
            continue
        try:
            _source_slab_solid(model,slab)
            low,high=_slab_mesh_bbox(slab)
            attrs={
                "id":_id(slab),
                "ifcGuid":slab.GlobalId,
                "level":levels[storey.GlobalId],
                "x":_number(low[0]),"y":_number(low[1]),"z":_number(low[2]),
                "width":_number(high[0]-low[0]),
                "depth":_number(high[1]-low[1]),
                "thickness":_number(high[2]-low[2]),
            }
            if attrs["id"] in by_guid.values():
                raise V4ProjectionError("Existing native slab local ID collision")
            etree.SubElement(elements,"{"+NS+"}Slab",attrib=attrs)
            by_guid[slab.GlobalId]=attrs["id"]
            included.append(slab.GlobalId)
        except V4ProjectionError as exc:
            if "collision" in str(exc):
                raise
            continue
        except (ValueError,TypeError,RuntimeError,AttributeError,UnsupportedIFCGeometry):
            continue
    if not included:
        return previous
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=True)
    parse_xml(xml,expected_source_sha256=previous.source.source_sha256)
    unsupported=Counter(dict(previous.unsupported_class_counts))
    supported=Counter(dict(previous.supported_class_counts))
    if unsupported["IfcSlab"]<len(included):
        raise V4ProjectionError("Slab native projection counts differ from read-only source")
    unsupported["IfcSlab"]-=len(included)
    if not unsupported["IfcSlab"]:
        unsupported.pop("IfcSlab",None)
    supported["IfcSlab"]+=len(included)
    result=replace(
        previous,xml=xml,
        projected_global_ids=tuple(sorted(by_guid.items())),
        opaque_references=tuple(x for x in previous.opaque_references
                                if x.ifc_guid not in included),
        supported_class_counts=tuple(sorted(supported.items())),
        unsupported_class_counts=tuple(sorted(unsupported.items())),
    )
    if snapshot_source(source).source_sha256!=previous.source.source_sha256:
        raise V4ProjectionError("Source modified while creating declarative slab projection")
    return result
