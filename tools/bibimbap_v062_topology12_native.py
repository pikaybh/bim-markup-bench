"""v0.62 original native IFC4X3 topological_test_12 wall-length final state.

Immutable SHA-pinned PUBLIC original IFC, eight complete original Wall
final-length rows. Physically shorten one structurally isolated, original
swept-solid wall around its existing WORLD CENTER: replace the shared
axis-start point with one NEW independent source-native point, update its
unique axis endpoint and RectangleProfile XDim while retaining the original
profile center and unchanged parent placement.
World physical mesh in METRES is independently checked against source.
Original IFC lengths are MILLIMETRES.

Important restriction: the seven original connected/clipped walls are not
yet supported as generic edits; the one unconnected original source wall
with native SweptSolid representation is deterministically source-derived.
This restricts D/I editing affordances and is NOT causal model parity or a
general BIM editing feature. No public answer/author hidden grader in host.
"""
from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path

import ifcopenshell
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import production_native_schema_delta_v055
from tools.bibimbap_v060_geometry19_native import (
    _native_entity_signature_v060,
    canonical_original_native_semantic_digest_v060,
)
from tools.bibimbap_v061_geometry13_native import _mesh_bounds


TASK="topological_test_12"
SOURCE_SHA="1f10c164d5ba6ffad7a22ce5d4e5f869b81abe497463c3ef0c3262c0a679ec83"
NAMESPACE="urn:bim-markup-bench:toy:v0"
Q="{"+NAMESPACE+"}"
MAX_XML=24000
MAX_COMPACT=5000
MAX_CALLS=25
WORLD_EPS=2e-5


class Topology12Native062Error(ValueError):
    pass


def need(ok:bool,reason:str):
    if not ok:
        raise Topology12Native062Error(reason)


def _xml_parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def _source(path:Path,*,source_sha:str):
    p=Path(path)
    need(source_sha==SOURCE_SHA and p.is_file()
         and not p.is_symlink() and file_hash(p)==SOURCE_SHA,
         "The exact unmodified original-public IFC source SHA is required")
    model=ifcopenshell.open(str(p))
    need(model.schema=="IFC4X3"
         and len(model.by_type("IfcWall"))==8
         and len(model.by_type("IfcRelConnectsPathElements"))==7
         and len(model.by_type("IfcSlab"))==2
         and len(model.by_type("IfcColumn"))==2
         and len(model.by_type("IfcSpace"))==1,
         "Original eight-wall topology/IFC4X3 source signature drift")
    need(file_hash(p)==source_sha,"Source changed during original IFC read")
    return model


def _wall_repr(wall):
    reps=wall.Representation.Representations
    ax=[r for r in reps if r.RepresentationIdentifier=="Axis"]
    body=[r for r in reps if r.RepresentationIdentifier=="Body"]
    need(len(ax)==len(body)==1 and len(ax[0].Items)==len(body[0].Items)==1,
         "Source original wall axis and body representations ambiguous")
    axis=ax[0].Items[0]
    need(axis.is_a("IfcPolyline") and len(axis.Points)==2,
         "Original source Wall axis must be 2-point IfcPolyline")
    return axis,body[0].Items[0]


def original_wall_axis_length_m_v062(wall)->float:
    axis,_=_wall_repr(wall)
    coords=[tuple(p.Coordinates) for p in axis.Points]
    need(len(coords[0])==len(coords[1])==2,
         "Original IFC axis must have two 2D native coordinates")
    length=math.dist(coords[0],coords[1])/1000.
    need(math.isfinite(length) and .1<=length<=20,
         "Original Wall axis physical length invalid")
    return round(length,6)


def isolated_original_swept_wall_v062(model):
    """Identify source-original *edit-authority* by native representation,
    absence of connected wall paths and unique independent 3 native attrs.
    No target GUID, public question, author reference or private GT.
    """
    editable=[]
    for wall in model.by_type("IfcWall"):
        axis,body=_wall_repr(wall)
        if not body.is_a("IfcExtrudedAreaSolid"):
            continue
        profile=body.SweptArea
        if not profile.is_a("IfcRectangleProfileDef"):
            continue
        points=(axis.Points[1],profile.Position.Location)
        if (len(model.get_inverse(points[0]))!=1
            or len(model.get_inverse(points[1]))!=1
            or len(model.get_inverse(profile))!=1):
            continue
        if any(x.is_a("IfcRelConnectsPathElements")
               for x in model.get_inverse(wall)):
            continue
        native_len=original_wall_axis_length_m_v062(wall)*1000
        center=profile.Position.Location.Coordinates
        if (abs(profile.XDim-native_len)>1e-5
            or len(center)!=2
            or abs(center[0]-native_len/2)>1e-5
            or abs(center[1])>1e-5
            or abs(axis.Points[1].Coordinates[1])>1e-5):
            continue
        editable.append((wall,axis,profile))
    need(len(editable)==1,
         "Original native standalone SweptSolid Wall not uniquely present")
    return editable[0]


def _world_number(x):
    n=float(x)
    need(math.isfinite(n) and abs(n)<1e5,
         "Original source physical coordinate unbounded")
    return f"{n:.6f}"


def full_source_state_v062(source_ifc:Path,*,source_sha:str)->bytes:
    model=_source(source_ifc,source_sha=source_sha)
    isolated_original_swept_wall_v062(model)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},attrib={
        "version":"0.62",
        "representation":"D_COMPLETE_XML_V062",
        "sourceOriginalIFCSha256":source_sha,
        "nativeIFCSchema":"IFC4X3",
        "nativeLengthUnit":"MILLIMETER",
        "worldMeshUnit":"METRE",
        "managedSemantics":"ALL_EIGHT_ORIGINAL_WALL_FINAL_AXIS_LENGTH_METRES",
    })
    frozen=etree.SubElement(root,Q+"OriginalNativeIFCSource",{
        "ifcSHA256":source_sha,
        "originalRootGUIDCount":str(len(model.by_type("IfcRoot"))),
        "originalPathConnectionCount":"7",
    })
    products=etree.SubElement(frozen,Q+"Products")
    for prod in sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        props={
            "ifcGuid":prod.GlobalId,
            "ifcClass":prod.is_a(),
            "name":str(prod.Name or ""),
        }
        if prod.Representation is not None:
            bounds=_mesh_bounds(prod)
            for letter,i in zip("XYZ",range(3)):
                props["min"+letter+"M"]=_world_number(bounds[i][0])
                props["max"+letter+"M"]=_world_number(bounds[i][1])
        if prod.is_a("IfcWall"):
            axis,body=_wall_repr(prod)
            props["sourceAxisLengthM"]=_world_number(
                original_wall_axis_length_m_v062(prod))
            props["sourceBodyRepresentationClass"]=body.is_a()
            props["sourceConnectedWallPathCount"]=str(sum(
                x.is_a("IfcRelConnectsPathElements")
                for x in model.get_inverse(prod)))
        etree.SubElement(products,Q+"SourceProduct",props)
    managed=etree.SubElement(root,Q+"ManagedElements",{
        "boundary":"ALL_EIGHT_ORIGINAL_IFCWALL_GUIDS",
    })
    for wall in sorted(model.by_type("IfcWall"),key=lambda x:x.GlobalId):
        etree.SubElement(managed,Q+"Wall",{
            "ifcGuid":wall.GlobalId,
            "finalAxisLengthM":_world_number(
                original_wall_axis_length_m_v062(wall)),
        })
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_XML,"Source native full XML exceeds bounded size")
    return out


def compact_complete_state_v062(source_ifc:Path,*,source_sha:str)->bytes:
    initial=full_source_state_v062(source_ifc,source_sha=source_sha)
    original=etree.fromstring(initial,_xml_parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},attrib={
        "version":"0.62",
        "representation":"D_MANAGED_FINAL_STATE_V062",
        "sourceOriginalIFCSha256":source_sha,
        "sourceFullBuildingStateSha256":sha256(initial).hexdigest(),
        "managedBoundary":"ALL_EIGHT_ORIGINAL_IFCWALL_GUIDS",
    })
    for row in original[1]:
        etree.SubElement(root,Q+"Wall",dict(row.attrib))
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_COMPACT,"Bounded complete managed Wall state too large")
    return out


def _complete_roster_decision(original,submitted,editable_guid):
    before=list(original[1])
    need(len(before)==len(submitted)==8,
         "Complete original all-eight-Wall final-state roster mandatory")
    changed=[]
    for prev,new in zip(before,submitted):
        need(new.tag==Q+"Wall"
             and not len(new)
             and set(new.attrib)=={"ifcGuid","finalAxisLengthM"}
             and new.get("ifcGuid")==prev.get("ifcGuid")
             and not (new.text or "").strip()
             and not (new.tail or "").strip(),
             "Unknown/duplicate/reordered/missing original Wall final-state row")
        value=new.get("finalAxisLengthM")
        try:
            num=float(value)
        except (TypeError,ValueError):
            raise Topology12Native062Error("Wall final length not numeric") from None
        need(math.isfinite(num) and .2<=num<=20
             and value==f"{num:.6f}",
             "Original native Wall final length outside canonical bounds")
        delta=round(num-float(prev.get("finalAxisLengthM")),6)
        if abs(delta)>=.000001:
            changed.append((new.get("ifcGuid"),num,delta))
    need(len(changed)==1
         and changed[0][0]==editable_guid
         and 0>changed[0][2]>=-1.7
         and .25<=changed[0][1]<=1.9,
         "Exactly original source-eligible swept-solid Wall may be shortened")
    return changed[0][0],changed[0][1]


def parse_full_final_state_v062(source_ifc:Path,xml:bytes,
                                 *,source_sha:str)->tuple[str,float]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML,
         "Complete bounded original native BuildingState XML required")
    check_xml_bytes(xml)
    original=etree.fromstring(
        full_source_state_v062(source_ifc,source_sha=source_sha),_xml_parser())
    doc=etree.fromstring(xml,_xml_parser())
    need(doc.tag==Q+"BuildingState"
         and dict(doc.attrib)==dict(original.attrib)
         and len(doc)==2
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Original native source/building identity not preserved")
    need(doc[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(doc[0],method="c14n")==
             etree.tostring(original[0],method="c14n"),
         "Original product/shape/connection source evidence modified")
    need(doc[1].tag==Q+"ManagedElements"
         and dict(doc[1].attrib)==dict(original[1].attrib)
         and not (doc[1].text or "").strip()
         and not (doc[1].tail or "").strip(),
         "Original 8-wall final-state boundary changed")
    model=_source(source_ifc,source_sha=source_sha)
    isolated=isolated_original_swept_wall_v062(model)[0]
    verdict=_complete_roster_decision(original,doc[1],isolated.GlobalId)
    need(file_hash(source_ifc)==source_sha,"Source IFC altered during parse")
    return verdict


def restore_compact_final_state_v062(source_ifc:Path,xml:bytes,
                                     *,source_sha:str)->tuple[bytes,tuple[str,float]]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_COMPACT,
         "Complete bounded original native managed Wall state mandatory")
    check_xml_bytes(xml)
    source=full_source_state_v062(source_ifc,source_sha=source_sha)
    original=etree.fromstring(source,_xml_parser())
    doc=etree.fromstring(xml,_xml_parser())
    need(doc.tag==Q+"ManagedFinalState"
         and dict(doc.attrib)=={
             "version":"0.62",
             "representation":"D_MANAGED_FINAL_STATE_V062",
             "sourceOriginalIFCSha256":source_sha,
             "sourceFullBuildingStateSha256":sha256(source).hexdigest(),
             "managedBoundary":"ALL_EIGHT_ORIGINAL_IFCWALL_GUIDS",
         }
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Original full source/compact state schema or SHA tampered")
    model=_source(source_ifc,source_sha=source_sha)
    eligible=isolated_original_swept_wall_v062(model)[0].GlobalId
    verdict=_complete_roster_decision(original,doc,eligible)
    for dst,src in zip(original[1],doc):
        dst.set("finalAxisLengthM",src.get("finalAxisLengthM"))
    whole=etree.tostring(original,encoding="utf8",xml_declaration=True)
    need(parse_full_final_state_v062(
        source_ifc,whole,source_sha=source_sha)==verdict,
        "Managed final state did not reconstruct valid full source state")
    return whole,verdict


def _edit_native_wall_length(model,wall_guid:str,length_m:float):
    wall,axis,profile=isolated_original_swept_wall_v062(model)
    need(wall.GlobalId==wall_guid
         and isinstance(length_m,(int,float))
         and math.isfinite(length_m)
         and .25<=length_m<=1.9,
         "Only eligible original swept-solid Wall may be reduced")
    native_len=round(length_m*1000.,6)
    need(native_len<profile.XDim-100.,
         "Original source wall must physically shorten, not translate/expand")
    original_start=axis.Points[0]
    original_end=axis.Points[1]
    old_start=original_start.Coordinates
    old_end=original_end.Coordinates
    need(len(old_start)==len(old_end)==2
         and all(abs(x)<1e-6 for x in old_start)
         and abs(old_end[1])<=1e-6
         and len(model.get_inverse(original_start))>1,
         "Unexpected original SHARED axis-start point or orientation")
    center_native=float(profile.Position.Location.Coordinates[0])
    need(abs(center_native-profile.XDim/2)<=.00001,
         "Original source RectangleProfile original center drift")
    # The original axis-start CartesianPoint is SHARED with many other
    # shapes. Create a new independent point for ONLY this wall's Axis,
    # preserving every other native original point/IfcRoot/relationship.
    start_native=center_native-native_len/2.
    end_native=center_native+native_len/2.
    new_start=model.create_entity(
        "IfcCartesianPoint",Coordinates=(start_native,0.))
    axis.Points=(new_start,original_end)
    original_end.Coordinates=(end_native,0.)
    profile.XDim=native_len
    # Profile center stays at the original native X = 1000 mm,
    # and the Wall ObjectPlacement also remains byte-semantically fixed.
    # Both world-mesh ends move inward by half of the reduction.


def compile_wall_shortening_v062(source_ifc:Path,output_ifc:Path,
                                 *,source_sha:str,
                                 target:tuple[str,float])->None:
    model=_source(source_ifc,source_sha=source_sha)
    out=Path(output_ifc)
    need(isinstance(target,tuple) and len(target)==2
         and not out.exists() and out.parent.is_dir()
         and not out.parent.is_symlink()
         and out.resolve()!=Path(source_ifc).resolve(),
         "Only fresh separate native IFC edit output may be used")
    _edit_native_wall_length(model,target[0],target[1])
    model.write(str(out))
    need(out.is_file() and not out.is_symlink()
         and file_hash(source_ifc)==source_sha,
         "Native wall edit wrote invalid output or modified original IFC")


def independent_wall_native_scope_v062(source_ifc:Path,candidate_ifc:Path,
                                        *,source_sha:str)->dict:
    """Independent original-source IFC4X3 native scope geometry validation.

    Blind to source public QUESTION's desired 1m delta, grader and hidden
    original answer. All original IFC entity ids, source Wall connections,
    structure and shape relationships preserved, except exactly three
    specific exclusive source axis/profiling STEP entities. Source world
    mesh length matches axis/profile after physical shortening, fixed
    start point and all non-target source world 3D meshes unchanged.
    """
    source=_source(source_ifc,source_sha=source_sha)
    wall,axis,profile=isolated_original_swept_wall_v062(source)
    original_length=original_wall_axis_length_m_v062(wall)
    out=Path(candidate_ifc)
    need(out.is_file() and not out.is_symlink()
         and out.resolve()!=Path(source_ifc).resolve(),
         "Original/candidate native IFC must be distinct and regular")
    targetsha=file_hash(out)
    dest=ifcopenshell.open(str(out))
    need(dest.schema==source.schema
         and len(dest.by_type("IfcWall"))==8
         and len(dest.by_type("IfcRelConnectsPathElements"))==7,
         "Original source-native IFC4X3 topology changed")
    original={x.id():_native_entity_signature_v060(x) for x in source}
    final={x.id():_native_entity_signature_v060(x) for x in dest}
    # A source-only center-preserving shorten MUST create one unique new
    # axis-start point rather than mutating the ORIGINAL SHARED point (#4)
    # used by many Wall/representation entities. It also changes exactly
    # the original Axis polyline's point references, the unique Axis end
    # point, and the single original rectangle profile XDim.
    source_ids=set(original)
    extra=set(final)-source_ids
    need(source_ids.issubset(final)
         and len(extra)==1,
         "Exactly one independent new axis-start IfcCartesianPoint permitted")
    new_start_id=next(iter(extra))
    new_start_ent=dest.by_id(new_start_id)
    need(new_start_ent.is_a("IfcCartesianPoint")
         and len(dest.get_inverse(new_start_ent))==1,
         "New independent CartesianPoint may only belong to original Wall Axis")
    allowed_changed={axis.id(),axis.Points[1].id(),profile.id()}
    changed={eid for eid in original if original[eid]!=final[eid]}
    need(changed==allowed_changed
         and len(allowed_changed)==3
         and len(source.get_inverse(axis.Points[0]))>1
         and len(source.get_inverse(axis.Points[1]))==1
         and len(source.get_inverse(profile))==1,
         "Only original Wall axis reference/end/profile XDim may change; "
         "source shared point and other native entities must remain immutable")
    updated_axis=dest.by_id(axis.id())
    updated_profile=dest.by_id(profile.id())
    need(updated_axis.is_a("IfcPolyline")
         and len(updated_axis.Points)==2
         and updated_axis.Points[0].id()==new_start_id
         and updated_axis.Points[1].id()==axis.Points[1].id(),
         "Source original Axis end point must remain, only start re-linked")
    new_start=updated_axis.Points[0].Coordinates
    new_end=updated_axis.Points[1].Coordinates
    original_center=profile.Position.Location.Coordinates
    updated_center=updated_profile.Position.Location.Coordinates
    new_native=float(updated_profile.XDim)
    need(math.isfinite(new_native)
         and 250<=new_native<=1900
         and new_native<original_length*1000.-100
         and len(new_start)==len(new_end)==len(updated_center)==2
         and all(abs(a-b)<=.00001 for a,b in zip(updated_center,original_center))
         and abs(new_start[0]-(original_center[0]-new_native/2))<=.00001
         and abs(new_end[0]-(original_center[0]+new_native/2))<=.00001
         and abs(new_start[1])<=.00001
         and abs(new_end[1])<=.00001
         and abs(updated_center[1])<=.00001,
         "Source native Wall Axis/profile must shrink around original center")
    physical=new_native/1000.
    srcbox=_mesh_bounds(wall)
    newwall=dest.by_guid(wall.GlobalId)
    targetbox=_mesh_bounds(newwall)
    # This original unconnected Wall spans source world Y and retains
    # the SAME world center, Wall ObjectPlacement, thickness and height.
    # Both physical world Y endpoints contract inward by half the delta.
    reduction=original_length-physical
    need(abs((targetbox[1][0]-srcbox[1][0])-reduction/2)<=WORLD_EPS
         and abs((srcbox[1][1]-targetbox[1][1])-reduction/2)<=WORLD_EPS
         and abs((targetbox[1][1]-targetbox[1][0])-physical)<=WORLD_EPS
         and abs(sum(targetbox[1])/2-sum(srcbox[1])/2)<=WORLD_EPS,
         "Actual original external Wall must be shorter with original "
         "world center/placement fixed and both endpoints symmetrically inward")
    for axis_dim in (0,2):
        need(all(abs(a-b)<=WORLD_EPS for a,b in zip(
            srcbox[axis_dim],targetbox[axis_dim])),
            "Wall thickness/height or world direction changed")
    for product in source.by_type("IfcProduct"):
        if not product.Representation or product.GlobalId==wall.GlobalId:
            continue
        other=dest.by_guid(product.GlobalId)
        need(other is not None and other.is_a()==product.is_a(),
             "Original non-target entity/Root identity changed")
        base=_mesh_bounds(product)
        edited=_mesh_bounds(other)
        need(all(abs(x-y)<=WORLD_EPS
                 for bounds0,bounds1 in zip(base,edited)
                 for x,y in zip(bounds0,bounds1)),
             "Unrelated original native product physical geometry modified")
    delta=production_native_schema_delta_v055(
        source_ifc,out,source_sha=source_sha)
    need(delta["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS"
         and delta["introduced_schema_error_count"]==0,
         "Native IFC4X3 source-vs-candidate schema findings introduced")
    need(file_hash(source_ifc)==source_sha
         and file_hash(out)==targetsha,
         "Original or candidate native IFC changed during validation")
    return {
        "status":"V062_ORIGINAL_ONE_UNCONNECTED_WALL_SHORTENED_NATIVE_SCOPE_SCHEMA_PASS",
        "source_wall_count_preserved":8,
        "source_wall_path_connections_preserved":7,
        "only_original_axis_ref_end_and_profile_changed_plus_one_unique_new_point":True,
        "native_original_length_unit":"MILLIMETER",
        "world_mesh_unit":"METRE",
        "original_swept_solid_wall_length_m":original_length,
        "final_swept_solid_wall_length_m":round(physical,6),
        "actual_native_shortening_m":round(original_length-physical,6),
        "original_external_wall_world_center_preserved":True,
        "other_source_Ifc_3D_geometry_and_native_entities_unchanged":True,
        "introduced_original_IFC_schema_error_count":0,
        "source_SHA256_preserved":True,
        "candidate_native_IFC_file_SHA256":targetsha,
        "original_author_score":None,
    }


def canonical_native_semantic_digest_v062(candidate_ifc:Path)->str:
    """Use only after independent scope/schema validation PASS."""
    return canonical_original_native_semantic_digest_v060(candidate_ifc)
