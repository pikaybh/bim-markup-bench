"""Prospective read-only, source-pinned IFC compatibility v0.7.

IFC4X3 native metre input:
  1. Retain proven older v0.4 projected content unchanged when available.
  2. If v0.1 had no managed elements, bootstrap an *honest partial* XML
     with only exact native world axis-aligned 8-corner+12-triangle mapped
     Columns and directly-extruded prism Slabs. All native other geometry,
     Boolean Walls and relationships remain source-pinned opaque passthrough.

IFC2X3 / IFC4 original source:
  Read-only native structural admission + lossless original file hash only.
  NEVER claim these source schemas are editable IFC4X3 or fabricate the
  missing storey elevation. Their v0.1 XML schema explicitly forbids them.

This module never mutates IFC, source data, old versions, or paid results.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.runtime.ifc_projection import (
    Projection,OpaqueReference,UnsupportedIFCGeometry,_id,_number,
)
from src.runtime.experimental_v4_projection import (
    project_ifc_v4,_source_slab_solid,
)
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.xml_parser import parse_xml
from src.runtime.markup_normal_form import NS

TOL=1e-6


class V7CompatError(ValueError):
    pass


def native_source_admission_v7(source:Path)->dict:
    """Read-only native schema evidence; not converted data or model-facing XML."""
    snap=snapshot_source(source)
    f=ifcopenshell.open(str(source))
    scale=float(ifcopenshell.util.unit.calculate_unit_scale(f))
    if not math.isfinite(scale) or scale<=0:
        raise V7CompatError("Native IFC has invalid length unit scale")
    storeys=f.by_type("IfcBuildingStorey")
    elevations={s.GlobalId:(
        float(s.Elevation)*scale if s.Elevation is not None else None
    ) for s in storeys}
    if any(v is not None and not math.isfinite(v) for v in elevations.values()):
        raise V7CompatError("IFC storey has nonfinite native elevation")
    if snapshot_source(source).source_sha256!=snap.source_sha256:
        raise V7CompatError("Original source IFC mutated during compatibility admission")
    return {
        "status":"READ_ONLY_NATIVE_IFC_SOURCE_ADMITTED",
        "ifc_schema":f.schema,
        "source_sha256":snap.source_sha256,
        "native_entity_count":snap.entity_count,
        "native_globalid_count":len(snap.global_ids),
        "native_step_graph_fingerprint":snap.graph_fingerprint,
        "native_length_unit_metres_per_native_unit":scale,
        "storey_count":len(storeys),
        "storeys_with_explicit_elevation":sum(s.Elevation is not None for s in storeys),
        "storeys_missing_explicit_elevation":sum(s.Elevation is None for s in storeys),
        "v01_xml_editing_supported":f.schema=="IFC4X3" and math.isclose(scale,1.0,abs_tol=1e-8),
        "legacy_source_schema_losslessly_converted_to_IFC4X3":False,
        "full_IFC_geometry_serialized_in_XML":False,
        "native_file_never_mutated":True,
    }


def _mesh_exact_axis_box(product_entity):
    """Exact native triangulated prism, not an AABB-only approximation.

    8 original vertices + 12 triangles + six rectangular face checks.
    The model's original opaque IFC geometry remains the authority.
    """
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        mesh=ifcopenshell.geom.create_shape(settings,product_entity)
        points=np.asarray(mesh.geometry.verts,dtype=float).reshape((-1,3))
        triangles=np.asarray(mesh.geometry.faces,dtype=int).reshape((-1,3))
    except Exception as exc:
        raise V7CompatError("Native IFC world mesh missing") from exc
    if (len(points)!=8 or len(triangles)!=12
        or not np.isfinite(points).all()
        or np.any(triangles<0) or np.any(triangles>=len(points))):
        raise V7CompatError("Shape is not a complete native 8-corner 12-triangle box")
    lo=points.min(axis=0)
    hi=points.max(axis=0)
    extent=hi-lo
    if any(not 0.01<float(d)<=10000 for d in extent):
        raise V7CompatError("Native source solid not a bounded nondegenerate box")
    required=np.array(list(product(*zip(lo,hi))),dtype=float)
    # Bijection of the eight actual source IFC vertices to the 8 corners.
    hits=np.array([
        [np.max(np.abs(p-q))<=TOL for q in required] for p in points
    ],dtype=bool)
    if not (np.all(hits.sum(axis=0)==1) and np.all(hits.sum(axis=1)==1)):
        raise V7CompatError("Rotated/skewed/missing native prism corner")
    counts={(axis,side):0 for axis in range(3) for side in (0,1)}
    areas={key:0. for key in counts}
    corners={key:set() for key in counts}
    for tri in triangles:
        abc=points[tri]
        area=np.linalg.norm(np.cross(abc[1]-abc[0],abc[2]-abc[0]))/2.
        if not math.isfinite(float(area)) or area<=TOL:
            raise V7CompatError("Degenerate IFC box triangle")
        faces=[(axis,side) for axis in range(3)
               for side,bound in ((0,lo[axis]),(1,hi[axis]))
               if np.all(np.abs(abc[:,axis]-bound)<=TOL)]
        if len(faces)!=1:
            raise V7CompatError("Native source solid contains sloped/nonboundary triangles")
        k=faces[0]
        counts[k]+=1
        areas[k]+=float(area)
        corners[k].update(int(index) for index in tri)
    for (axis,side),count in counts.items():
        other=[i for i in range(3) if i!=axis]
        area=float(extent[other[0]]*extent[other[1]])
        if (count!=2 or len(corners[(axis,side)])!=4
            or not math.isclose(areas[(axis,side)],area,abs_tol=1e-5,rel_tol=1e-8)):
            raise V7CompatError("Native source AABB omits or overlaps a face")
    return (tuple(float(x) for x in lo),
            tuple(float(x) for x in hi))


def _native_supported(source:Path,model,storeys):
    by_guid={}
    reasons={}
    for typ in ("IfcColumn","IfcSlab"):
        for entity in sorted(model.by_type(typ),key=lambda x:x.GlobalId):
            try:
                containing=ifcopenshell.util.element.get_container(entity)
                if containing is None or containing.GlobalId not in storeys:
                    raise V7CompatError("Original native Column/Slab lacks a pinned supported storey")
                if typ=="IfcSlab":
                    _source_slab_solid(model,entity)  # original direct extrusion, not a Boolean or mapped Slab
                elif not any(
                    item.is_a("IfcMappedItem")
                    for rep in entity.Representation.Representations
                    for item in rep.Items
                ):
                    raise V7CompatError("V7 bootstrap accepts Column only as original opaque mapped geometry")
                lo,hi=_mesh_exact_axis_box(entity)
                attrs={
                    "id":_id(entity),"ifcGuid":entity.GlobalId,
                    "level":storeys[containing.GlobalId],
                    "x":_number(lo[0]),"y":_number(lo[1]),"z":_number(lo[2]),
                    "width":_number(hi[0]-lo[0]),
                    "depth":_number(hi[1]-lo[1]),
                }
                if typ=="IfcSlab":
                    attrs["thickness"]=_number(hi[2]-lo[2])
                else:
                    attrs["height"]=_number(hi[2]-lo[2])
                by_guid[entity.GlobalId]=(typ.removeprefix("Ifc"),attrs)
            except (V7CompatError,UnsupportedIFCGeometry,ValueError,TypeError,
                    AttributeError,RuntimeError) as exc:
                reasons[entity.GlobalId]=str(exc)[:140]
    return by_guid,reasons


def project_ifc_v7(source:Path)->Projection:
    """Valid partial v0.1 XML on original IFC4X3 *metre clone* only.

    If older projection can already succeed, preserve it byte-for-byte.
    A zero-managed-element prior failure is the sole bootstrap trigger.
    """
    original=snapshot_source(source)
    f=ifcopenshell.open(str(source))
    if f.schema!="IFC4X3":
        raise V7CompatError("Legacy source is only read-only admission; do not relabel IFC2X3/IFC4 as IFC4X3 XML")
    if abs(float(ifcopenshell.util.unit.calculate_unit_scale(f))-1.)>1e-8:
        raise V7CompatError("Native metre-unit IFC4X3 clone required; raw mm input cannot be relabelled")
    try:
        old=project_ifc_v4(source)
    except UnsupportedIFCGeometry as exc:
        if "No editable geometry could be projected" not in str(exc):
            raise
    else:
        return old  # exact older semantics preserved

    root=etree.Element("{"+NS+"}Building",nsmap={None:NS},attrib={
        "version":"0.1","sourceModelSha256":original.source_sha256,
        "units":"m","ifcSchema":"IFC4X3",
    })
    levels=etree.SubElement(root,"{"+NS+"}Levels")
    elements=etree.SubElement(root,"{"+NS+"}Elements")
    etree.SubElement(root,"{"+NS+"}Relations")
    levelids={}
    opaque=[]
    unsupported=Counter()
    supported=Counter()
    for s in sorted(f.by_type("IfcBuildingStorey"),key=lambda x:x.GlobalId):
        if s.Elevation is None:
            opaque.append(OpaqueReference(s.GlobalId,"IfcBuildingStorey","Missing native storey elevation"))
            unsupported["IfcBuildingStorey"]+=1
            continue
        attrs={
            "id":_id(s),"ifcGuid":s.GlobalId,
            "elevation":_number(float(s.Elevation)),
        }
        etree.SubElement(levels,"{"+NS+"}Level",attrib=attrs)
        levelids[s.GlobalId]=attrs["id"]
        supported["IfcBuildingStorey"]+=1
    if not levelids:
        raise V7CompatError("No original explicit native building storey; no invented elevation permitted")
    by_guid,reasons=_native_supported(source,f,levelids)
    if not by_guid:
        raise V7CompatError("No native exact mapped Column or direct Slab can be safely projected")
    projected={}
    for guid,(kind,attrs) in sorted(by_guid.items()):
        etree.SubElement(elements,"{"+NS+"}"+kind,attrib=attrs)
        projected[guid]=attrs["id"]
        supported["Ifc"+kind]+=1
    # Storeys also have exact source identities; other IFC products remain
    # opaque, including Boolean/Clipping Walls, partial Spaces, hosts, etc.
    for typ in ("IfcWall","IfcSlab","IfcColumn","IfcSpace",
                "IfcOpeningElement","IfcWindow","IfcDoor"):
        for entity in sorted(f.by_type(typ),key=lambda x:x.GlobalId):
            if entity.GlobalId in projected:
                continue
            why=reasons.get(entity.GlobalId,
                "Original IFC geometry/relations unavailable as safe typed XML; source is authoritative")
            opaque.append(OpaqueReference(entity.GlobalId,entity.is_a(),why))
            unsupported[typ]+=1
    for entity in sorted(f.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        if entity.GlobalId in projected or any(x.ifc_guid==entity.GlobalId for x in opaque):
            continue
        opaque.append(OpaqueReference(entity.GlobalId,entity.is_a(),
                                       "Unmanaged native IFC product source-pinned opaque"))
    known=set(projected)|set(levelids)
    unrepresented=[]
    for rel in f.by_type("IfcRelConnectsElements"):
        if (rel.RelatingElement.GlobalId not in projected
            or rel.RelatedElement.GlobalId not in projected):
            unrepresented.append("IfcRelConnectsElements remains source-owned opaque; never fabricate XML edges")
    for rel in f.by_type("IfcRelSpaceBoundary"):
        unrepresented.append("IfcRelSpaceBoundary remains source-owned opaque")
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=True)
    parse_xml(xml,expected_source_sha256=original.source_sha256)
    result=Projection(
        source=original,xml=xml,
        projected_global_ids=tuple(sorted([
            (guid,levelids[guid]) for guid in levelids
        ]+list(projected.items()))),
        opaque_references=tuple(sorted(opaque,key=lambda x:(x.ifc_class,x.ifc_guid))),
        supported_class_counts=tuple(sorted(supported.items())),
        unsupported_class_counts=tuple(sorted(unsupported.items())),
        opaque_relation_reasons=tuple(sorted(set(unrepresented))),
    )
    if snapshot_source(source).source_sha256!=original.source_sha256:
        raise V7CompatError("Original source changed during native source bootstrap")
    return result
