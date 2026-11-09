"""Restricted, fully read-only IFC4X3 -> declarative v0.1 XML projection.

Only explicit, verified straight-axis geometry and typed host relations are
managed. Everything else remains immutable as opaque data in the original
binary IFC. It is not a lossless stand-alone XML representation and does not
implement editing/exporting IFC deltas.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from lxml import etree
import numpy as np

from src.runtime.ifc_snapshot import IFCSnapshot, snapshot_source
from src.runtime.xml_parser import parse_xml
from src.runtime.markup_normal_form import NS

ELEMENT_ORDER = ("IfcWall","IfcSlab","IfcColumn","IfcSpace","IfcOpeningElement","IfcWindow","IfcDoor")
PREFIXES = {"IfcWall":"wall","IfcSlab":"slab","IfcColumn":"column","IfcSpace":"space",
            "IfcOpeningElement":"opening","IfcWindow":"window","IfcDoor":"door","IfcBuildingStorey":"level"}

class UnsupportedIFCGeometry(ValueError):
    pass

@dataclass(frozen=True)
class OpaqueReference:
    ifc_guid: str
    ifc_class: str
    reason: str

    def as_dict(self) -> dict:
        return {"ifc_guid":self.ifc_guid,"ifc_class":self.ifc_class,"reason":self.reason}

@dataclass(frozen=True)
class Projection:
    source: IFCSnapshot
    xml: bytes
    projected_global_ids: tuple[tuple[str,str], ...]  # (existing IFC GUID, XML local ID)
    opaque_references: tuple[OpaqueReference,...]
    supported_class_counts: tuple[tuple[str,int], ...]
    unsupported_class_counts: tuple[tuple[str,int], ...]
    opaque_relation_reasons: tuple[str,...]

    def report(self) -> dict:
        # Backend-only audit; do not send the complete manifest to the LLM.
        return {
            "source_sha256":self.source.source_sha256,
            "ifc_schema":self.source.ifc_schema,
            "projected_count":len(self.projected_global_ids),
            "opaque_count":len(self.opaque_references),
            "supported_counts":dict(self.supported_class_counts),
            "unsupported_counts":dict(self.unsupported_class_counts),
            "opaque_relation_reasons":list(self.opaque_relation_reasons),
            "has_opaque_source_data":bool(self.opaque_references or self.opaque_relation_reasons),
            "source_file_preserved":True,
            "full_bim_model_editing_supported":False,
        }


def _id(entity: Any) -> str:
    return PREFIXES[entity.is_a()]+"_"+hashlib.sha256(entity.GlobalId.encode("ascii")).hexdigest()[:14]


def _number(x: float) -> str:
    """Bounded decimal projection of SI metres for the pinned XML schema.

    IFC placement matrices introduce near-zero floating-point noise. The
    libxml2 xs:decimal validator can reject long float expansions. Nine
    fractional digits limit rounding error to at most 0.5 nanometres,
    below the 1 micrometre geometry tolerance. Never emit exponent or -0.
    Values too large for this restricted projection fail closed.
    """
    value=float(x)
    if not math.isfinite(value) or abs(value)>100_000_000:
        raise UnsupportedIFCGeometry("Nonfinite/out-of-range IFC dimensions or placement")
    lexical=format(value,".9f").rstrip("0").rstrip(".")
    return "0" if lexical in ("", "-0") else lexical


def _sub(parent: etree._Element, tag: str, attributes: dict[str,str]) -> None:
    etree.SubElement(parent, "{"+NS+"}"+tag, attrib=attributes)


def _m(entity: Any) -> np.ndarray:
    if getattr(entity,"ObjectPlacement",None) is None:
        raise UnsupportedIFCGeometry("Missing IFC object placement")
    p=np.asarray(ifcopenshell.util.placement.get_local_placement(entity.ObjectPlacement),dtype=np.float64)
    if p.shape != (4,4) or not np.all(np.isfinite(p)):
        raise UnsupportedIFCGeometry("Invalid IFC global placement")
    if not np.allclose(p[:3,:3].T@p[:3,:3],np.eye(3),atol=1e-5):
        raise UnsupportedIFCGeometry("Non-orthonormal IFC placement not safely supported")
    return p


def _world(p: np.ndarray, x: float, y: float, z: float) -> tuple[float,float,float]:
    out=p@np.array([x,y,z,1.0],dtype=np.float64)
    return tuple(float(v) for v in out[:3])


def _body_extrusion(entity: Any) -> Any:
    reps=getattr(entity,"Representation",None)
    if reps is None:
        raise UnsupportedIFCGeometry("IFC product lacks explicit geometric representation")
    candidates=[]
    for rep in reps.Representations:
        if rep.RepresentationType != "SweptSolid":
            continue
        for item in rep.Items:
            if item.is_a("IfcExtrudedAreaSolid"):
                candidates.append(item)
    if len(candidates)!=1:
        raise UnsupportedIFCGeometry("Expected exactly one simple swept solid; mapped/boolean geometry unsupported")
    item=candidates[0]
    dr=item.ExtrudedDirection.DirectionRatios
    if not np.allclose(dr,(0.,0.,1.),atol=1e-6):
        raise UnsupportedIFCGeometry("Non-vertical extrusion or tilted roof/element")
    if not (0<float(item.Depth)<10000):
        raise UnsupportedIFCGeometry("Invalid IFC extrusion depth")
    return item


def _rect_extents(profile: Any) -> tuple[float,float,float,float]:
    if profile.is_a("IfcRectangleProfileDef"):
        xdim=float(profile.XDim);ydim=float(profile.YDim)
        if not (xdim>0 and ydim>0):
            raise UnsupportedIFCGeometry("IFC rectangle profile has zero dimension")
        center=(0.,0.)
        if profile.Position is not None:
            loc=profile.Position.Location.Coordinates
            center=(float(loc[0]),float(loc[1]))
            # Rotated profiles are unsupported; a rectangular axis is required.
            if profile.Position.RefDirection is not None:
                vec=profile.Position.RefDirection.DirectionRatios
                if not (abs(abs(float(vec[0]))-1.0)<1e-6 and abs(float(vec[1]))<1e-6):
                    raise UnsupportedIFCGeometry("Oblique 2D rectangle profile unsupported")
        return (center[0]-xdim/2,center[1]-ydim/2,
                center[0]+xdim/2,center[1]+ydim/2)
    if not profile.is_a("IfcArbitraryClosedProfileDef"):
        raise UnsupportedIFCGeometry("Unsupported IFC profile type")
    curve=profile.OuterCurve
    if not curve.is_a("IfcIndexedPolyCurve"):
        raise UnsupportedIFCGeometry("Only simple indexed rectangle profile is supported")
    pts=list(curve.Points.CoordList)
    if len(pts)>1 and pts[0]==pts[-1]:
        pts=pts[:-1]
    if len(pts)!=4 or any(len(p)!=2 for p in pts):
        raise UnsupportedIFCGeometry("Nonrectangular or complex IFC polyline profile")
    xs=sorted(set(float(p[0]) for p in pts))
    ys=sorted(set(float(p[1]) for p in pts))
    if len(xs)!=2 or len(ys)!=2 or xs[1]<=xs[0] or ys[1]<=ys[0]:
        raise UnsupportedIFCGeometry("Non-axis-aligned IFC rectangle profile")
    corners={(xs[0],ys[0]),(xs[0],ys[1]),(xs[1],ys[0]),(xs[1],ys[1])}
    if {(float(p[0]),float(p[1])) for p in pts}!=corners:
        raise UnsupportedIFCGeometry("IFC polygon is not an axis-aligned rectangle")
    return xs[0],ys[0],xs[1],ys[1]


def _extrusion_offset(item: Any) -> tuple[float,float,float]:
    pos=item.Position
    if pos is None:return (0.,0.,0.)
    if pos.Axis is not None and not np.allclose(pos.Axis.DirectionRatios,(0.,0.,1.),atol=1e-6):
        raise UnsupportedIFCGeometry("Tilted swept extrusion frame unsupported")
    if pos.RefDirection is not None and not np.allclose(pos.RefDirection.DirectionRatios,(1.,0.,0.),atol=1e-6):
        raise UnsupportedIFCGeometry("Rotated swept extrusion frame unsupported")
    c=pos.Location.Coordinates
    return float(c[0]),float(c[1]),float(c[2])


def _level(entity: Any, known_levels: dict[str,str]) -> str:
    storey=ifcopenshell.util.element.get_container(entity)
    if storey is None or not storey.is_a("IfcBuildingStorey"):
        # Spaces are often aggregated under storeys rather than contained.
        parent=ifcopenshell.util.element.get_aggregate(entity)
        if parent is not None and parent.is_a("IfcBuildingStorey"):
            storey=parent
    if storey is None or storey.GlobalId not in known_levels:
        raise UnsupportedIFCGeometry("No unambiguous supported IfcBuildingStorey association")
    return known_levels[storey.GlobalId]


def _wall_attrs(entity: Any, known_levels: dict[str,str], scale: float) -> dict[str,str]:
    item=_body_extrusion(entity)
    a,b,c,d=_rect_extents(item.SweptArea)
    length=c-a
    thickness=d-b
    p=_m(entity)
    extr=_extrusion_offset(item)
    if item.SweptArea.is_a("IfcRectangleProfileDef"):
        # Revit-style IFC walls often include an explicit Curve2D local axis.
        axis=[]
        for rep in entity.Representation.Representations:
            if rep.RepresentationType != "Curve2D":continue
            for curve in rep.Items:
                if curve.is_a("IfcPolyline") and len(curve.Points)==2:
                    axis.append(curve)
        if len(axis)!=1:
            raise UnsupportedIFCGeometry("Rectangle wall missing unique explicit line axis")
        x1,y1=[float(v) for v in axis[0].Points[0].Coordinates[:2]]
        x2,y2=[float(v) for v in axis[0].Points[1].Coordinates[:2]]
        if abs(math.dist((x1,y1),(x2,y2))-length)>1e-5:
            raise UnsupportedIFCGeometry("Wall axis and rectangle profile length differ")
    else:
        x1,y1=a,b
        x2,y2=c,b
    start=_world(p,x1+extr[0],y1+extr[1],extr[2])
    finish=_world(p,x2+extr[0],y2+extr[1],extr[2])
    if math.dist(start,finish) < 0.01:
        raise UnsupportedIFCGeometry("Degenerate wall axis")
    return dict(id=_id(entity),ifcGuid=entity.GlobalId,
        level=_level(entity,known_levels),
        x1=_number(start[0]*scale),y1=_number(start[1]*scale),z1=_number(start[2]*scale),
        x2=_number(finish[0]*scale),y2=_number(finish[1]*scale),z2=_number(finish[2]*scale),
        height=_number(float(item.Depth)*scale),thickness=_number(thickness*scale))


def _world_axis_aligned_space_box(entity: Any, known_levels: dict[str,str],
                                  scale: float) -> dict[str,str]:
    """Project a Space only when its native mesh is *exactly* a world AABB.

    A rotated IFC swept-solid placement can still yield an axis-aligned
    cuboid.  The bounding box alone is not sufficient: verify eight corners,
    all twelve triangles and the six complete rectangular faces so an
    oblique shape is never silently replaced by a larger AABB.
    """
    try:
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        shape=ifcopenshell.geom.create_shape(settings,entity)
        points=np.asarray(shape.geometry.verts,dtype=np.float64).reshape((-1,3))
        triangles=np.asarray(shape.geometry.faces,dtype=np.int64).reshape((-1,3))
    except Exception as exc:
        raise UnsupportedIFCGeometry("Native Space mesh unavailable for exact cuboid projection") from exc
    if (len(points)!=8 or len(triangles)!=12 or
            not np.isfinite(points).all() or
            np.any(triangles<0) or np.any(triangles>=len(points))):
        raise UnsupportedIFCGeometry("Space is not a complete eight-vertex cuboid")
    low=points.min(axis=0)
    high=points.max(axis=0)
    sizes=high-low
    tol=1e-7
    if not np.all(np.isfinite(sizes)) or np.any(sizes<=tol) or np.any(sizes>10000):
        raise UnsupportedIFCGeometry("Space has degenerate or excessive world extents")
    from itertools import product
    expected=np.array(list(product(*zip(low,high))),dtype=np.float64)
    if any(not np.any(np.all(np.abs(points-corner)<=tol,axis=1))
           for corner in expected):
        raise UnsupportedIFCGeometry("Space rotated or skewed outside world AABB")
    # A complete box surface has two nondegenerate triangles per face.
    # Require four distinct corners per face and full face area; simply
    # checking the bounding box would falsely accept tilted shapes.
    counts={(axis,side):0 for axis in range(3) for side in (0,1)}
    face_corners={key:set() for key in counts}
    face_areas={key:0. for key in counts}
    for triangle in triangles:
        face=points[triangle]
        area=np.linalg.norm(np.cross(face[1]-face[0],face[2]-face[0]))/2.
        if not math.isfinite(float(area)) or area<=tol:
            raise UnsupportedIFCGeometry("Space has degenerate mesh triangles")
        candidates=[(axis,side) for axis in range(3) for side,bound in
                    ((0,low[axis]),(1,high[axis]))
                    if np.all(np.abs(face[:,axis]-bound)<=tol)]
        if len(candidates)!=1:
            raise UnsupportedIFCGeometry("Space mesh has an oblique/interior face")
        key=candidates[0]
        counts[key]+=1
        face_areas[key]+=float(area)
        face_corners[key].update(tuple(np.round(pt,7)) for pt in face)
    for (axis,side),count in counts.items():
        axes=[idx for idx in range(3) if idx!=axis]
        expected_area=float(sizes[axes[0]]*sizes[axes[1]])
        if (count!=2 or len(face_corners[(axis,side)])!=4 or
                not math.isclose(face_areas[(axis,side)],expected_area,
                                 abs_tol=1e-6,rel_tol=1e-8)):
            raise UnsupportedIFCGeometry("Space native cuboid faces incomplete or overlapped")
    return dict(id=_id(entity),ifcGuid=entity.GlobalId,
        level=_level(entity,known_levels),
        x=_number(low[0]*scale),y=_number(low[1]*scale),z=_number(low[2]*scale),
        width=_number(sizes[0]*scale),depth=_number(sizes[1]*scale),
        height=_number(sizes[2]*scale))


def _box_attrs(entity: Any, known_levels: dict[str,str], scale: float,
               kind: str) -> dict[str,str]:
    item=_body_extrusion(entity)
    x0,y0,x1,y1=_rect_extents(item.SweptArea)
    p=_m(entity)
    # Boxes in v0.1 have axis-aligned horizontal footprints.
    if not np.allclose(p[:3,:3],np.eye(3),atol=1e-6):
        if kind=="Space":
            return _world_axis_aligned_space_box(entity,known_levels,scale)
        raise UnsupportedIFCGeometry("Oriented 3D box unsupported by rectangular v0.1 XML")
    try:
        ex,ey,ez=_extrusion_offset(item)
    except UnsupportedIFCGeometry as exc:
        if kind!="Space" or "Rotated swept extrusion frame" not in str(exc):
            raise
        return _world_axis_aligned_space_box(entity,known_levels,scale)
    x,y,z=_world(p,x0+ex,y0+ey,ez)
    # For centered rectangle column, XML origin is the lower-left
    # footprint corner; not necessarily the IFC ObjectPlacement origin.
    attrs=dict(id=_id(entity),ifcGuid=entity.GlobalId,level=_level(entity,known_levels),
        x=_number(x*scale),y=_number(y*scale),z=_number(z*scale),
        width=_number((x1-x0)*scale),depth=_number((y1-y0)*scale))
    if kind=="Slab":
        attrs["thickness"]=_number(float(item.Depth)*scale)
    else:
        attrs["height"]=_number(float(item.Depth)*scale)
    return attrs


def _opening_world_dimensions(entity: Any, axis: np.ndarray, scale: float) -> tuple[float,float]:
    """Native IFC void mesh: wall-parallel width and world-vertical height.

    The extrusion depth often measures wall thickness, not opening height.
    This is a read-only bounded IFC projection; it is not a geometry mutator.
    """
    try:
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        shape=ifcopenshell.geom.create_shape(settings,entity)
        points=np.asarray(shape.geometry.verts,dtype=np.float64).reshape((-1,3))
    except Exception as exc:
        raise UnsupportedIFCGeometry("Opening world geometry unavailable") from exc
    if len(points)<4 or not np.isfinite(points).all():
        raise UnsupportedIFCGeometry("Opening mesh empty or nonfinite")
    width=float(np.ptp(points@axis))*scale
    height=float(np.ptp(points[:,2]))*scale
    normal=np.array([-axis[1],axis[0],0.],dtype=np.float64)
    thickness=float(np.ptp(points@normal))*scale
    if not all(math.isfinite(v) and 1e-7<v<10000 for v in (width,height,thickness)):
        raise UnsupportedIFCGeometry("Opening world dimensions degenerate")
    return width,height


def _opening_attrs(entity: Any, known: dict[str,Any], scale: float) -> dict[str,str]:
    hosts=[r.RelatingBuildingElement for r in entity.VoidsElements] if hasattr(entity,"VoidsElements") else []
    if len(hosts)!=1 or hosts[0].is_a()!="IfcWall" or hosts[0].GlobalId not in known:
        raise UnsupportedIFCGeometry("Opening lacks a unique managed IfcWall host")
    host=hosts[0]
    item=_body_extrusion(entity)
    x0,y0,x1,y1=_rect_extents(item.SweptArea)
    if min(x1-x0,y1-y0)<1e-9:
        raise UnsupportedIFCGeometry("Opening void has degenerate profile")
    p=_m(entity)
    hostinfo=known[host.GlobalId]
    start=np.array([float(hostinfo[c]) for c in ("x1","y1","z1")])
    finish=np.array([float(hostinfo[c]) for c in ("x2","y2","z2")])
    axis=finish-start
    length=float(np.linalg.norm(axis))
    if length<1e-6:
        raise UnsupportedIFCGeometry("Hosted wall has degenerate axis")
    axis/=length
    width,height=_opening_world_dimensions(entity,axis,scale)
    origin=np.asarray(_world(p,0,0,0))*scale
    delta=origin-start
    offset=float(np.dot(delta,axis))
    sill=float(origin[2]-start[2])
    if not (-1e-6<=offset<=length and -1e-6<=sill):
        raise UnsupportedIFCGeometry("Opening is out of supported host geometry bounds")
    return dict(id=_id(entity),ifcGuid=entity.GlobalId,
        host=_id(host),offset=_number(max(0,offset)),sill=_number(max(0,sill)),
        width=_number(width),height=_number(height))


def _filling_attrs(entity: Any, openings: dict[str,dict[str,str]], scale: float) -> dict[str,str]:
    fills=list(entity.FillsVoids) if hasattr(entity,"FillsVoids") else []
    if len(fills)!=1:
        raise UnsupportedIFCGeometry("Window/door missing a unique IfcRelFillsElement")
    opening=fills[0].RelatingOpeningElement
    if opening.GlobalId not in openings:
        raise UnsupportedIFCGeometry("Window/door filling references unsupported opening")
    try:
        width=float(entity.OverallWidth)
        height=float(entity.OverallHeight)
    except (TypeError,ValueError) as exc:
        raise UnsupportedIFCGeometry("Window/door missing exact OverallWidth/OverallHeight") from exc
    if width<=0 or height<=0:
        raise UnsupportedIFCGeometry("Window/door has nonpositive width/height")
    return dict(id=_id(entity),ifcGuid=entity.GlobalId,opening=_id(opening),
                width=_number(width*scale),height=_number(height*scale))


def project_ifc(source: Path, *, strict_on_opaque: bool=False) -> Projection:
    snapshot=snapshot_source(source)
    if snapshot.ifc_schema != "IFC4X3":
        raise UnsupportedIFCGeometry("Current experimental grammar supports IFC4X3 only")
    model=ifcopenshell.open(str(source))
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    if not (math.isfinite(scale) and abs(scale-1.)<1e-9):
        raise UnsupportedIFCGeometry("Only meter-unit IFC model projection is currently supported")
    root=etree.Element("{"+NS+"}Building",nsmap={None:NS},
        attrib={"version":"0.1","sourceModelSha256":snapshot.source_sha256,
                "units":"m","ifcSchema":"IFC4X3"})
    levels=etree.SubElement(root,"{"+NS+"}Levels")
    elements=etree.SubElement(root,"{"+NS+"}Elements")
    relations=etree.SubElement(root,"{"+NS+"}Relations")
    known_levels={}
    opaque=[]
    projected={}
    attrs_by_guid={}
    support_counts=Counter()
    unsupported_counts=Counter()
    for storey in sorted(model.by_type("IfcBuildingStorey"),key=lambda e:e.GlobalId):
        if storey.Elevation is None:
            opaque.append(OpaqueReference(storey.GlobalId,storey.is_a(),"Missing explicit storey elevation"))
            unsupported_counts[storey.is_a()]+=1
            continue
        attrs={"id":_id(storey),"ifcGuid":storey.GlobalId,"elevation":_number(float(storey.Elevation)*scale)}
        _sub(levels,"Level",attrs)
        known_levels[storey.GlobalId]=attrs["id"]
        projected[storey.GlobalId]=attrs["id"]
        support_counts[storey.is_a()]+=1
    if not known_levels:
        raise UnsupportedIFCGeometry("No supported explicit building storey; cannot construct a valid source document")
    for typ in ELEMENT_ORDER:
        for entity in sorted(model.by_type(typ),key=lambda e:e.GlobalId):
            try:
                if typ=="IfcWall":
                    attrs=_wall_attrs(entity,known_levels,scale)
                elif typ in ("IfcSlab","IfcColumn","IfcSpace"):
                    attrs=_box_attrs(entity,known_levels,scale,typ.removeprefix("Ifc"))
                elif typ=="IfcOpeningElement":
                    attrs=_opening_attrs(entity,attrs_by_guid,scale)
                elif typ in ("IfcWindow","IfcDoor"):
                    attrs=_filling_attrs(entity,attrs_by_guid,scale)
                else:
                    raise UnsupportedIFCGeometry("Unhandled IFC class")
                if attrs["id"] in projected.values():
                    raise UnsupportedIFCGeometry("Local identifier collision")
                # Must project fully typed fields; do not fabricate missing
                # geometry, hosts or space relationships.
                _sub(elements,typ.removeprefix("Ifc").replace("OpeningElement","Opening"),attrs)
                projected[entity.GlobalId]=attrs["id"]
                attrs_by_guid[entity.GlobalId]=attrs
                support_counts[typ]+=1
            except (UnsupportedIFCGeometry,AttributeError,TypeError,IndexError,ValueError) as exc:
                opaque.append(OpaqueReference(entity.GlobalId,typ,str(exc)[:140]))
                unsupported_counts[typ]+=1
    unrepresented_relations=[]
    for rel in sorted(model.by_type("IfcRelSpaceBoundary"),key=lambda e:e.GlobalId):
        space=rel.RelatingSpace
        wall=rel.RelatedBuildingElement
        if (space and wall and space.GlobalId in projected and wall.GlobalId in projected
            and wall.is_a()=="IfcWall" and space.is_a()=="IfcSpace"
            and rel.PhysicalOrVirtualBoundary == "PHYSICAL"):
            _sub(relations,"SpaceBoundary",{"space":projected[space.GlobalId],
                "element":projected[wall.GlobalId],"kind":"PHYSICAL"})
        else:
            unrepresented_relations.append("IfcRelSpaceBoundary: endpoint missing from editable subset")
    for rel in sorted(model.by_type("IfcRelConnectsElements"),key=lambda e:e.GlobalId):
        left=rel.RelatingElement;right=rel.RelatedElement
        if (left and right and left.is_a()=="IfcWall" and right.is_a()=="IfcWall"
            and left.GlobalId in projected and right.GlobalId in projected
            and rel.ConnectionGeometry is None):
            _sub(relations,"Connects",{"from":projected[left.GlobalId],
                                        "to":projected[right.GlobalId]})
        else:
            unrepresented_relations.append("IfcRelConnectsElements: unprojected or unsupported endpoint")
    # Additional existing IFC products and relationships stay opaque; they
    # are immutable and not deleted due to their omission from XML.
    for product in model.by_type("IfcProduct"):
        if product.GlobalId not in projected and not any(x.ifc_guid==product.GlobalId for x in opaque):
            opaque.append(OpaqueReference(product.GlobalId,product.is_a(),"Unmanaged IFC product passed through verbatim"))
    if len(elements)==0:
        detail=opaque[0].reason if opaque else "No supported source elements"
        raise UnsupportedIFCGeometry("No editable geometry could be projected: " + detail)
    xml=etree.tostring(root,encoding="utf-8",xml_declaration=True,pretty_print=True)
    parsed=parse_xml(xml,expected_source_sha256=snapshot.source_sha256)
    # Unmanaged site/building hierarchy is normal; strict mode rejects
    # missing *editable* elements and opaque typed relationships.
    if strict_on_opaque and (unsupported_counts or unrepresented_relations):
        raise UnsupportedIFCGeometry("Unsupported editable elements/relations in strict projection mode")
    # The second IfcOpenShell open must not silently race with an altered source.
    # The XML digest is only valid for the exact model hash already recorded.
    if snapshot_source(source).source_sha256 != snapshot.source_sha256:
        raise UnsupportedIFCGeometry("Immutable IFC changed while projecting to XML")
    return Projection(
        source=snapshot,
        xml=xml,
        projected_global_ids=tuple(sorted(projected.items())),
        opaque_references=tuple(sorted(opaque,key=lambda x:(x.ifc_class,x.ifc_guid))),
        supported_class_counts=tuple(sorted(support_counts.items())),
        unsupported_class_counts=tuple(sorted(unsupported_counts.items())),
        opaque_relation_reasons=tuple(sorted(unrepresented_relations)),
    )
