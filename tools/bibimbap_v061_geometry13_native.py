"""v0.61 original IFC4X3 geometry_test_13 declarative Window assembly move.

Source-only immutable original IFC SHA, native actual units millimetres and
IfcOpenShell's world mesh coordinates metres. Two source Window assemblies,
each with ONE hosted Opening and exactly THREE physically aligned proxy
details. Window's local placement origin is SHARED with other window/IFC
entities, so NEVER edit the window's shared local origin directly.

D_FULL and D_MANAGED represent COMPLETE original ten-product absolute world
X final states, no operation script. Compiler changes four independent native
placement CartesianPoints (opening + 3 details) by delta_m*1000. The
Window follows its parent Opening. The independent IFC admission accepts
either source assembly moved by any consistent bounded nonzero offset; the
PUBLIC QUESTION's >1.5m and exactly +3m predicates are evaluator-only.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import production_native_schema_delta_v055
from tools.bibimbap_v060_geometry19_native import (
    _native_entity_signature_v060,canonical_original_native_semantic_digest_v060,
)


SOURCE_SHA="a334c9f41e6d94307ecce9425647ce891b2b07321ab2b59020274ce683d46ee5"
TASK="geometry_test_13"
NAMESPACE="urn:bim-markup-bench:toy:v0"
Q="{"+NAMESPACE+"}"
MAX_XML=26000
MAX_COMPACT=4600
MAX_CALLS=25
EPS=2.0e-5


class Geometry13Native061Error(ValueError):
    pass


def need(ok:bool,why:str)->None:
    if not ok:
        raise Geometry13Native061Error(why)


def _parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def _mesh_bounds(entity):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,entity)
    values=list(shape.geometry.verts)  # shape retained while C++ buffer read
    need(values and len(values)%3==0 and all(
        math.isfinite(float(v)) and abs(float(v))<=1e4 for v in values),
        "Original native source world mesh unavailable/unbounded")
    return tuple(
        (round(min(values[axis::3]),6),
         round(max(values[axis::3]),6))
        for axis in range(3)
    )


def _source(path:Path,*,source_sha:str):
    path=Path(path)
    need(source_sha==SOURCE_SHA and path.is_file()
         and not path.is_symlink() and file_hash(path)==SOURCE_SHA,
         "Exact untouched original IFC source hash must match")
    f=ifcopenshell.open(str(path))
    need(f.schema=="IFC4X3"
         and len(f.by_type("IfcWindow"))==2
         and len(f.by_type("IfcOpeningElement"))==2
         and len(f.by_type("IfcBuildingElementProxy"))==6
         and len(f.by_type("IfcWall"))==1
         and len(f.by_type("IfcRelFillsElement"))==2
         and len(f.by_type("IfcRelVoidsElement"))==2,
         "Unexpected original two window / six detail native source schema")
    need(file_hash(path)==source_sha,"Original IFC changed while being read")
    return f


def original_assembly_groups_v061(file):
    """Derive physically associated assembly details from source world X.

    No author hidden answers or hardcoded target GUID. Name suffixes do
    not determine association; source window+opening links and native
    proxy meshes must give exactly three X-aligned source details per
    window. Reject wrong source and ambiguous relationships.
    """
    windows=sorted(file.by_type("IfcWindow"),key=lambda x:x.GlobalId)
    proxies=file.by_type("IfcBuildingElementProxy")
    groups={}
    used=set()
    for w in windows:
        need(len(w.FillsVoids)==1,"Original Window must have one hosted Opening")
        opening=w.FillsVoids[0].RelatingOpeningElement
        need(opening.is_a("IfcOpeningElement")
             and len(opening.VoidsElements)==1
             and len(opening.HasFillings)==1
             and opening.HasFillings[0].RelatedBuildingElement==w,
             "Invalid original Window/Opening/Wall links")
        bbox=_mesh_bounds(w)
        center=sum(bbox[0])/2
        op=_mesh_bounds(opening)
        need(abs(sum(op[0])/2-center)<0.015,
             "Original Window and Opening do not share X center")
        matched=[
            p for p in proxies
            if abs(sum(_mesh_bounds(p)[0])/2-center)<0.015
        ]
        need(len(matched)==3 and not ({p.GlobalId for p in matched}&used),
             "Original Window must have three independent geometry-aligned details")
        used.update(p.GlobalId for p in matched)
        # Window own relative Placement.Location is shared (X=0), while
        # Opening+3 details have four independent nonshared placement points.
        need(w.ObjectPlacement.PlacementRelTo==opening.ObjectPlacement,
             "Window must inherit parent native Opening placement")
        members=(w,opening,*sorted(matched,key=lambda x:x.GlobalId))
        points=[x.ObjectPlacement.RelativePlacement.Location
                for x in members[1:]]
        need(len({p.id() for p in points})==4
             and all(len(file.get_inverse(p))==1 for p in points),
             "Only 4 independent exclusive native placement points permitted")
        groups[w.GlobalId]={
            "window":w,
            "members":members,
            "placement_points":tuple(points),
            "source_window_bbox":bbox,
        }
    need(len(groups)==2 and len(used)==6,
         "Original source two disjoint original detail assemblies required")
    widths=sorted(round(v["source_window_bbox"][0][1]
                        -v["source_window_bbox"][0][0],3)
                  for v in groups.values())
    need(widths==[0.6,1.6],
         "Original geometry-derived two-window source width signature drift")
    return groups


def _x(value):
    number=float(value)
    need(math.isfinite(number) and abs(number)<=1e5,
         "Invalid original native-world coordinate")
    return f"{number:.6f}"


def full_source_final_state_v061(source_ifc:Path,*,source_sha:str)->bytes:
    original=_source(source_ifc,source_sha=source_sha)
    groups=original_assembly_groups_v061(original)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},
        attrib={
            "version":"0.61",
            "representation":"D_COMPLETE_XML_V061",
            "sourceOriginalIFCSha256":source_sha,
            "sourceNativeIFCSchema":"IFC4X3",
            "sourceNativeLengthUnit":"MILLIMETER",
            "geometryWorldCoordinateUnit":"METRE",
            "managedSemantics":"ALL_TEN_ORIGINAL_WINDOW_OPENING_DETAIL_ELEMENTS",
        })
    source=etree.SubElement(root,Q+"OriginalNativeIFCSource",attrib={
        "ifcSHA256":source_sha,
        "rootGUIDCount":str(len(original.by_type("IfcRoot"))),
    })
    products=etree.SubElement(source,Q+"Products")
    for prod in sorted(original.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        attrs={"ifcGuid":prod.GlobalId,"ifcClass":prod.is_a(),
               "name":str(prod.Name or "")}
        if prod.Representation is not None:
            box=_mesh_bounds(prod)
            for axis,index in zip("XYZ",range(3)):
                attrs["min"+axis+"M"]=_x(box[index][0])
                attrs["max"+axis+"M"]=_x(box[index][1])
        if prod.is_a("IfcWindow"):
            rel=prod.FillsVoids[0].RelatingOpeningElement
            attrs["sourceHostedOpeningGuid"]=rel.GlobalId
            attrs["sourceHostWallGuid"]=(rel.VoidsElements[0]
                                         .RelatingBuildingElement.GlobalId)
        if prod.is_a("IfcOpeningElement"):
            attrs["sourceHostWallGuid"]=(prod.VoidsElements[0]
                                         .RelatingBuildingElement.GlobalId)
            attrs["sourceWindowGuid"]=(prod.HasFillings[0]
                                       .RelatedBuildingElement.GlobalId)
        etree.SubElement(products,Q+"SourceProduct",attrs)
    managed=etree.SubElement(root,Q+"ManagedElements",
        {"boundary":"ALL_TEN_ORIGINAL_SOURCE_WINDOW_ASSEMBLY_ELEMENTS"})
    members=sorted(
        (p for group in groups.values() for p in group["members"]),
        key=lambda x:x.GlobalId,
    )
    need(len(members)==10 and len({p.GlobalId for p in members})==10,
         "Complete source assembly roster is not unique")
    for prod in members:
        etree.SubElement(managed,Q+"Element",attrib={
            "ifcGuid":prod.GlobalId,
            "ifcClass":prod.is_a(),
            "finalWorldMinXM":_x(_mesh_bounds(prod)[0][0]),
        })
    data=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(data)<=MAX_XML,"Bounded native source XML")
    return data


def compact_complete_final_state_v061(source_ifc:Path,*,source_sha:str)->bytes:
    whole=full_source_final_state_v061(source_ifc,source_sha=source_sha)
    orig=etree.fromstring(whole,_parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},attrib={
        "version":"0.61",
        "representation":"D_MANAGED_FINAL_STATE_V061",
        "sourceOriginalIFCSha256":source_sha,
        "sourceFullBuildingStateSha256":sha256(whole).hexdigest(),
        "managedBoundary":"ALL_TEN_ORIGINAL_SOURCE_WINDOW_ASSEMBLY_ELEMENTS",
    })
    for old in orig[1]:
        etree.SubElement(root,Q+"Element",dict(old.attrib))
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_COMPACT,"Source complete managed final state too large")
    return out


def _managed_change(source,entries,groups):
    reference=list(source[1])
    need(len(reference)==len(entries)==10,
         "All ten original Window/Opening/details explicit in complete state")
    delta_by_guid={}
    for old,new in zip(reference,entries):
        need(new.tag==Q+"Element"
             and not len(new)
             and not (new.text or "").strip()
             and not (new.tail or "").strip()
             and set(new.attrib)=={"ifcGuid","ifcClass","finalWorldMinXM"}
             and new.get("ifcGuid")==old.get("ifcGuid")
             and new.get("ifcClass")==old.get("ifcClass"),
             "Missing/reordered/unknown original native GUID or unapproved data")
        try:
            x=float(new.get("finalWorldMinXM"))
        except (ValueError,TypeError):
            raise Geometry13Native061Error("Invalid world final-state X value") from None
        need(math.isfinite(x) and abs(x)<=1e5 and
             new.get("finalWorldMinXM")==f"{x:.6f}",
             "All managed final X positions must use canonical 6 decimals")
        dx=round(x-float(old.get("finalWorldMinXM")),6)
        delta_by_guid[old.get("ifcGuid")]=dx
    selected=[]
    for guid,group in groups.items():
        values={delta_by_guid[ent.GlobalId] for ent in group["members"]}
        need(len(values)==1,
             "Whole original Window/Opening/three-details assembly not aligned")
        delta=next(iter(values))
        if abs(delta)>=0.000001:
            need(abs(delta)<=10 and delta!=0,
                 "Source world translation outside bounded native edit authority")
            selected.append((guid,delta))
    need(len(selected)==1,
         "Exactly one disjoint complete original Window assembly may move")
    return selected[0]


def parse_complete_final_state_v061(source_ifc:Path,xml:bytes,
                                     *,source_sha:str)->tuple[str,float]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML,
         "Complete final BuildingState XML is required")
    check_xml_bytes(xml)
    reference=etree.fromstring(
        full_source_final_state_v061(source_ifc,source_sha=source_sha),_parser())
    doc=etree.fromstring(xml,_parser())
    need(doc.tag==Q+"BuildingState"
         and dict(doc.attrib)==dict(reference.attrib)
         and len(doc)==2
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Original BuildingState source/representation identity changed")
    need(doc[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(doc[0],method="c14n")==
             etree.tostring(reference[0],method="c14n"),
         "Original immutable source native mesh/product/association modified")
    need(doc[1].tag==Q+"ManagedElements"
         and dict(doc[1].attrib)==dict(reference[1].attrib)
         and not (doc[1].text or "").strip()
         and not (doc[1].tail or "").strip(),
         "Original complete managed boundary changed")
    groups=original_assembly_groups_v061(
        _source(source_ifc,source_sha=source_sha))
    target=_managed_change(reference,doc[1],groups)
    need(file_hash(source_ifc)==source_sha,"Original IFC modified during parse")
    return target


def restore_compact_final_state_v061(source_ifc:Path,xml:bytes,
                                     *,source_sha:str)->tuple[bytes,tuple[str,float]]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_COMPACT,
         "Complete bounded managed XML required")
    check_xml_bytes(xml)
    original=full_source_final_state_v061(source_ifc,source_sha=source_sha)
    reference=etree.fromstring(original,_parser())
    doc=etree.fromstring(xml,_parser())
    need(doc.tag==Q+"ManagedFinalState"
         and dict(doc.attrib)=={
             "version":"0.61",
             "representation":"D_MANAGED_FINAL_STATE_V061",
             "sourceOriginalIFCSha256":source_sha,
             "sourceFullBuildingStateSha256":sha256(original).hexdigest(),
             "managedBoundary":"ALL_TEN_ORIGINAL_SOURCE_WINDOW_ASSEMBLY_ELEMENTS",
         }
         and not (doc.text or "").strip()
         and not (doc.tail or "").strip(),
         "Compact complete original source SHA/roster boundary altered")
    groups=original_assembly_groups_v061(
        _source(source_ifc,source_sha=source_sha))
    target=_managed_change(reference,doc,groups)
    for orig,new in zip(reference[1],doc):
        orig.set("finalWorldMinXM",new.get("finalWorldMinXM"))
    whole=etree.tostring(reference,encoding="utf8",xml_declaration=True)
    need(parse_complete_final_state_v061(
        source_ifc,whole,source_sha=source_sha)==target,
        "Trusted reconstruction of full declarative original source state failed")
    return whole,target


def _move_native_group(original,window_guid:str,dx_m:float)->None:
    groups=original_assembly_groups_v061(original)
    need(window_guid in groups and
         isinstance(dx_m,(int,float)) and
         math.isfinite(dx_m) and 0<abs(dx_m)<=10,
         "Only one original Window group with bounded nonzero displacement")
    group=groups[window_guid]
    delta_native=round(dx_m*1000.,6)  # source IFC original project MILLIMETRES
    for point in group["placement_points"]:
        pos=list(point.Coordinates)
        need(len(pos)>=3 and all(math.isfinite(v) for v in pos),
             "Invalid original native placement coordinates")
        pos[0]+=delta_native
        point.Coordinates=tuple(pos)


def compile_group_move_v061(source_ifc:Path,output_ifc:Path,
                            *,source_sha:str,
                            target:tuple[str,float])->None:
    model=_source(source_ifc,source_sha=source_sha)
    out=Path(output_ifc)
    need(not out.exists() and out.parent.is_dir()
         and not out.parent.is_symlink()
         and out.resolve()!=Path(source_ifc).resolve(),
         "Fresh independent candidate IFC output required")
    need(isinstance(target,tuple) and len(target)==2,
         "Complete state source-derived one-group move required")
    _move_native_group(model,target[0],target[1])
    model.write(str(out))
    need(out.is_file() and not out.is_symlink()
         and file_hash(source_ifc)==source_sha,
         "Failed native source output/source preservation")


def independent_assembly_world_scope_v061(source_ifc:Path,candidate_ifc:Path,
                                           *,source_sha:str)->dict:
    """Admit physical source-window assembly + bounded offset without answers.

    Strict source STEP provenance: exact original IFC IDs/Root/geometry and
    unchanged all other native attribute/relationship entities. Only the
    four independent placement point coordinates for one of the two original
    assembly groups may move in their native source X by a common bounded
    nonzero amount. All five products' actual reopened world meshes must
    translate by precisely that delta; other world meshes remain fixed.
    A different IFC encoding that rewrites STEP ids or placement graph may
    be equally valid but is not currently admitted by this conservative
    engineering oracle (to be treated as limitation, not model failure).
    """
    source=_source(source_ifc,source_sha=source_sha)
    src_groups=original_assembly_groups_v061(source)
    dest=Path(candidate_ifc)
    need(dest.is_file() and not dest.is_symlink()
         and dest.resolve()!=Path(source_ifc).resolve(),
         "Separate original native candidate IFC required")
    candidate_sha=file_hash(dest)
    candidate=ifcopenshell.open(str(dest))
    need(candidate.schema==source.schema,
         "Original IFC4X3 input/candidate native schema changed")
    before={x.id():_native_entity_signature_v060(x) for x in source}
    after={x.id():_native_entity_signature_v060(x) for x in candidate}
    need(set(before)==set(after),
         "Unexpected added/removed source native IFC STEP entity identity")
    point_to_group={}
    for guid,g in src_groups.items():
        for point in g["placement_points"]:
            need(point.id() not in point_to_group,
                 "Original IFC cartesian source points shared unexpectedly")
            point_to_group[point.id()]=guid
    deltas={}
    changed=[]
    for key in before:
        if before[key]==after[key]:
            continue
        need(key in point_to_group
             and before[key][0]==after[key][0]=="IfcCartesianPoint",
             "Unexpected off-target original native root/geometry/relationship edit")
        source_coords=source.by_id(key).Coordinates
        candidate_coords=candidate.by_id(key).Coordinates
        need(len(source_coords)==len(candidate_coords)==3
             and all(math.isfinite(float(x)) for x in candidate_coords),
             "Invalid original native STEP point coordinate")
        dx_native=candidate_coords[0]-source_coords[0]
        need(abs(dx_native)>0.00001
             and abs(dx_native)<=10000.
             and abs(candidate_coords[1]-source_coords[1])<=0.00001
             and abs(candidate_coords[2]-source_coords[2])<=0.00001,
             "Non-X source coordinate or unbounded movement")
        guid=point_to_group[key]
        deltas.setdefault(guid,[]).append(dx_native)
        changed.append(key)
    need(len(deltas)==1 and len(changed)==4,
         "Exactly four exclusive placement points of one source assembly must move")
    guid=next(iter(deltas))
    values=deltas[guid]
    need(len(values)==4 and max(values)-min(values)<=0.0001,
         "Window/Opening/3 detail native positions disagree")
    shift_m=round(sum(values)/4/1000.,6)
    need(0<abs(shift_m)<=10,"Source native mm vs world m translation invalid")
    expected_ids={x.id() for x in src_groups[guid]["placement_points"]}
    need(set(changed)==expected_ids,
         "Incomplete original assembly: Opening or proxy not displaced")
    # Source native product shapes, not merely fake placement edits, must
    # physically move the 5 expected products and no other original shapes.
    moved_ids={p.GlobalId for p in src_groups[guid]["members"]}
    all_products=source.by_type("IfcProduct")
    for prod in all_products:
        if prod.Representation is None:
            continue
        original_bbox=_mesh_bounds(prod)
        other=candidate.by_guid(prod.GlobalId)
        need(other.is_a()==prod.is_a(),
             "Original product identity/class changed")
        final_bbox=_mesh_bounds(other)
        expected_shift=shift_m if prod.GlobalId in moved_ids else 0.0
        for axis in range(3):
            shift=expected_shift if axis==0 else 0.0
            for bound in range(2):
                need(abs((final_bbox[axis][bound]-
                          original_bbox[axis][bound])-shift)<=EPS,
                     "Actual world IFC geometry/host/opening/detail translation mismatch")
    verdict=production_native_schema_delta_v055(
        source_ifc,dest,source_sha=source_sha)
    need(verdict["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS"
         and verdict["introduced_schema_error_count"]==0,
         "Actual source-native IFC4X3 validation introduced error")
    need(file_hash(source_ifc)==source_sha
         and file_hash(dest)==candidate_sha,
         "Actual original/source or candidate changed concurrently")
    return {
        "status":"V061_TWO_WINDOW_SOURCE_ONE_ASSEMBLY_NATIVE_MOVE_SCOPE_PASS",
        "source_original_native_IFC_SHA256_preserved":True,
        "original_one_assembly_moved":True,
        "native_four_placement_points_moved":4,
        "five_physical_products_world_X_moved":5,
        "other_world_meshes_and_native_entities_unchanged":True,
        "source_X_delta_magnitude":abs(shift_m),
        "source_x_direction":"POSITIVE" if shift_m>0 else "NEGATIVE",
        "native_IFC_source_length_unit":"MILLIMETER",
        "world_mesh_unit":"METRE",
        "original_IfcOpenShell_schema_errors_introduced":0,
        "native_candidate_file_sha256":candidate_sha,
        "author_repository_score":None,
        "original_paper_official_score":None,
    }


def semantic_digest_after_native_oracle_v061(candidate_ifc:Path)->str:
    """Meaningful only after independent original native oracle PASS."""
    return canonical_original_native_semantic_digest_v060(candidate_ifc)
