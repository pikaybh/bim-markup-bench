"""Research-only v0.8 read-only partial native IFC2X3/IFC4 XML source view.

Unlike frozen IFC4X3 toy v0.1–v0.7, the *actual original native schema*
is explicitly and honestly encoded as sourceIfcSchema; missing original
storey Elevation is marked MISSING (not fabricated from placementZ).
Original IFC source is authoritative, unrepresented products are opaque.
No IFC edits occur anywhere in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.experimental_v7_projection import _mesh_exact_axis_box

NS="urn:bim-markup-bench:legacy:v0.8"
Q="{"+NS+"}"
SCHEMAS=frozenset(("IFC2X3","IFC4"))
NUMERIC=frozenset((
    "elevation","placementZ","x1","y1","z1","x2","y2","z2",
    "x","y","z","width","depth","height","thickness","offset","sill",
))


class LegacyV8Error(ValueError):
    pass


@dataclass(frozen=True)
class LegacyViewV8:
    source_sha256:str
    native_schema:str
    xml:bytes
    projected_guids:tuple[str,...]
    native_opaque_product_guids:tuple[str,...]
    native_class_counts:tuple[tuple[str,int],...]
    source_fingerprint:str

    def report(self):
        return {
            "source_sha256":self.source_sha256,
            "native_ifc_schema_preserved":self.native_schema,
            "original_ifc4x3_relabelled":False,
            "editable_partial_xml_element_guid_count":len(self.projected_guids),
            "opaque_native_product_count":len(self.native_opaque_product_guids),
            "native_product_classes":dict(self.native_class_counts),
            "source_step_graph_fingerprint":self.source_fingerprint,
            "original_source_is_immutable":True,
            "full_45_native_edit_parity":False,
        }


def _id(kind:str,guid:str)->str:
    return kind+"_"+sha256(guid.encode("ascii")).hexdigest()[:14]


def _n(value)->str:
    f=float(value)
    if not math.isfinite(f) or abs(f)>100000:
        raise LegacyV8Error("Native source coordinate out of bounded range")
    s=format(f,".9f").rstrip("0").rstrip(".")
    return "0" if s in ("","-0") else s


def _schema():
    location=Path(__file__).resolve().parents[2]/"spec/experimental_native_legacy_v08.xsd"
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,huge_tree=False)
    root=etree.parse(str(location),parser=parser)
    if root.find(".//{http://www.w3.org/2001/XMLSchema}include") is not None:
        raise LegacyV8Error("External XSD includes forbidden")
    if root.find(".//{http://www.w3.org/2001/XMLSchema}import") is not None:
        raise LegacyV8Error("External XSD imports forbidden")
    return etree.XMLSchema(root)


def parse_v8(xml:bytes,*,source_sha256:str,native_schema:str):
    check_xml_bytes(xml)
    if native_schema not in SCHEMAS:
        raise LegacyV8Error("Only native IFC2X3 or IFC4 allowed")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,
                          huge_tree=False,remove_comments=True,remove_pis=True)
    try:
        root=etree.fromstring(xml,parser=parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise LegacyV8Error("Unsafe or syntactically invalid legacy declarative XML") from exc
    if root.getroottree().docinfo.doctype:
        raise LegacyV8Error("DOCTYPE forbidden in research legacy XML")
    if root.tag!=Q+"Building":
        raise LegacyV8Error("Unexpected v0.8 research declarative XML namespace")
    if (root.get("sourceModelSha256")!=source_sha256
        or root.get("sourceIfcSchema")!=native_schema
        or root.get("version")!="0.8"
        or root.get("units")!="m"):
        raise LegacyV8Error("Original immutable IFC source hash/schema/units mismatch")
    if not _schema().validate(root):
        raise LegacyV8Error("Invalid v0.8 declarative source XSD: "+
                            str(_schema().error_log.last_error)[:180])
    for item in root.findall("./"+Q+"Levels/"+Q+"Level"):
        has=item.get("elevation") is not None
        if item.get("elevationState")!=("EXPLICIT" if has else "MISSING"):
            raise LegacyV8Error("Original native Storey elevation state cannot be invented")
    return root


def _wall_attrs(wall,level_id):
    reps=wall.Representation.Representations if wall.Representation else []
    axes=[item for rep in reps if rep.RepresentationType=="Curve2D"
          for item in rep.Items if item.is_a("IfcPolyline") and len(item.Points)==2]
    solids=[item for rep in reps if rep.RepresentationType=="SweptSolid"
            for item in rep.Items if item.is_a("IfcExtrudedAreaSolid")]
    if len(axes)!=1 or len(solids)!=1:
        raise LegacyV8Error("IFC2X3 Wall requires original native simple swept solid and line axis")
    solid=solids[0]
    if not solid.SweptArea.is_a("IfcRectangleProfileDef"):
        raise LegacyV8Error("Original native Wall has unsupported complex profile")
    if len(solid.ExtrudedDirection.DirectionRatios)!=3 or not np.allclose(
        solid.ExtrudedDirection.DirectionRatios,(0,0,1),atol=1e-9
    ):
        raise LegacyV8Error("Wall has nonvertical extrusion")
    frame=np.asarray(ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement),dtype=float)
    if frame.shape!=(4,4) or not np.allclose(frame[:3,:3].T@frame[:3,:3],np.eye(3),atol=1e-6):
        raise LegacyV8Error("Original Wall object placement is not rigid")
    endpoints=[]
    for point in axes[0].Points:
        xy=point.Coordinates
        if len(xy)!=2:
            raise LegacyV8Error("Original native Wall line axis not planar")
        xyzw=frame@np.array((float(xy[0]),float(xy[1]),0.,1.))
        endpoints.append(xyzw[:3])
    a,b=endpoints
    delta=b-a
    span=float(np.linalg.norm(delta))
    if span<=0.1 or abs(delta[2])>1e-7:
        raise LegacyV8Error("Wall horizontal axis unsupported")
    native_low,native_high=_mesh_exact_axis_box(wall)
    native_low=np.asarray(native_low)
    native_high=np.asarray(native_high)
    height=float(native_high[2]-native_low[2])
    length=float(solid.SweptArea.XDim)
    thickness=float(solid.SweptArea.YDim)
    if (not math.isclose(length,span,rel_tol=0,abs_tol=1e-5)
        or not math.isclose(height,float(solid.Depth),rel_tol=0,abs_tol=1e-5)
        or abs(a[2]-native_low[2])>1e-5
        or not (0.05<thickness<=10 and 0.1<height<=1000)):
        raise LegacyV8Error("Native original Wall shape/line/profile geometry mismatch")
    # Enforce that the original wall is horizontal-axis aligned and native
    # footprint equals axis bounds expanded by half the original thickness.
    vector=delta/span
    if not (abs(vector[0])>1-1e-8 and abs(vector[1])<1e-8
            or abs(vector[1])>1-1e-8 and abs(vector[0])<1e-8):
        raise LegacyV8Error("Oblique IFC2X3 wall cannot be represented exactly")
    if abs(vector[0])>0.5:
        corners=[min(a[0],b[0]),max(a[0],b[0]),
                 a[1]-thickness/2,a[1]+thickness/2]
    else:
        corners=[a[0]-thickness/2,a[0]+thickness/2,
                 min(a[1],b[1]),max(a[1],b[1])]
    if not np.allclose(np.asarray(corners),
                       (native_low[0],native_high[0],native_low[1],native_high[1]),
                       atol=1e-5,rtol=0):
        raise LegacyV8Error("Native wall mesh outside represented axis+thickness")
    return dict(
        id=_id("wall",wall.GlobalId),ifcGuid=wall.GlobalId,level=level_id,
        x1=_n(a[0]),y1=_n(a[1]),z1=_n(a[2]),
        x2=_n(b[0]),y2=_n(b[1]),z2=_n(b[2]),
        height=_n(height),thickness=_n(thickness),
    )


def project_legacy_v8(source:Path)->LegacyViewV8:
    snap=snapshot_source(source)
    f=ifcopenshell.open(str(source))
    if f.schema not in SCHEMAS:
        raise LegacyV8Error("Native IFC4X3 and others must keep using previous frozen projection")
    scale=float(ifcopenshell.util.unit.calculate_unit_scale(f))
    if not math.isclose(scale,1.,abs_tol=1e-8,rel_tol=0):
        raise LegacyV8Error("Legacy v0.8 input must be a metre-normalized clone preserving original schema")
    root=etree.Element(Q+"Building",nsmap={None:NS},attrib={
        "version":"0.8","sourceModelSha256":snap.source_sha256,
        "sourceIfcSchema":f.schema,"units":"m",
    })
    levels=etree.SubElement(root,Q+"Levels")
    elements=etree.SubElement(root,Q+"Elements")
    storey_ids={}
    for storey in sorted(f.by_type("IfcBuildingStorey"),key=lambda s:s.GlobalId):
        if storey.ObjectPlacement is None:
            raise LegacyV8Error("Original native storey lacks placement")
        placement=ifcopenshell.util.placement.get_local_placement(storey.ObjectPlacement)
        if not np.allclose(placement[:3,:3].T@placement[:3,:3],np.eye(3),atol=1e-8):
            raise LegacyV8Error("Original native storey coordinate frame invalid")
        attrs={
            "id":_id("level",storey.GlobalId),"ifcGuid":storey.GlobalId,
            "elevationState":"EXPLICIT" if storey.Elevation is not None else "MISSING",
            "placementZ":_n(placement[2,3]),
        }
        if storey.Elevation is not None:
            attrs["elevation"]=_n(storey.Elevation)
        etree.SubElement(levels,Q+"Level",attrib=attrs)
        storey_ids[storey.GlobalId]=attrs["id"]
    if not storey_ids:
        raise LegacyV8Error("No original native Storey; source cannot be projected")
    projected=[]
    for wall in sorted(f.by_type("IfcWallStandardCase"),key=lambda w:w.GlobalId):
        if f.schema!="IFC2X3":
            continue
        storey=ifcopenshell.util.element.get_container(wall)
        if storey is None or storey.GlobalId not in storey_ids:
            continue
        try:
            attrs=_wall_attrs(wall,storey_ids[storey.GlobalId])
        except (LegacyV8Error,TypeError,ValueError,RuntimeError):
            continue
        etree.SubElement(elements,Q+"Wall",attrib=attrs)
        projected.append(wall.GlobalId)
    if f.schema=="IFC2X3":
        for col in sorted(f.by_type("IfcColumn"),key=lambda c:c.GlobalId):
            storey=ifcopenshell.util.element.get_container(col)
            if storey is None or storey.GlobalId not in storey_ids:
                continue
            try:
                low,high=_mesh_exact_axis_box(col)
                low=np.asarray(low);high=np.asarray(high)
                dims=high-low
                attrs={
                    "id":_id("column",col.GlobalId),
                    "ifcGuid":col.GlobalId,
                    "level":storey_ids[storey.GlobalId],
                    "x":_n(low[0]),"y":_n(low[1]),"z":_n(low[2]),
                    "width":_n(dims[0]),"depth":_n(dims[1]),"height":_n(dims[2]),
                }
            except (LegacyV8Error,TypeError,ValueError,RuntimeError):
                continue
            etree.SubElement(elements,Q+"Column",attrib=attrs)
            projected.append(col.GlobalId)
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=True)
    parse_v8(xml,source_sha256=snap.source_sha256,native_schema=f.schema)
    all_products=f.by_type("IfcProduct")
    counts={}
    for prod in all_products:
        counts[prod.is_a()]=counts.get(prod.is_a(),0)+1
    opaque=tuple(sorted(x.GlobalId for x in all_products
                        if x.GlobalId not in projected))
    if snapshot_source(source).source_sha256!=snap.source_sha256:
        raise LegacyV8Error("Native source was modified during read-only projection")
    return LegacyViewV8(
        source_sha256=snap.source_sha256,native_schema=f.schema,xml=xml,
        projected_guids=tuple(sorted(projected)),
        native_opaque_product_guids=opaque,
        native_class_counts=tuple(sorted(counts.items())),
        source_fingerprint=snap.graph_fingerprint,
    )
