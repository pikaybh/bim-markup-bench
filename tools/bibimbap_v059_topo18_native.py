"""v0.59 first NEW untouched-source holdout task: original topo18 IFC space deletion.

Source-native IFC4X3/mm, all three original IfcSpace identities, source-only
geometry and exact immutable source SHA. Nothing from author scorer, GT,
model provider or developer positive-target fixture enters this host.

The D arm authors COMPLETE final state (3 explicit true/false records);
the I arm runs arbitrary genuine pinned Linux Docker Python. Both must pass
the SAME independent source-derived native IFC semantic/scope+schema gate.
The conservative native scope oracle accepts only IFC semantically equal to
source with ONE IfcSpace removed via full linked-product cleanup. It can
reject alternative otherwise-valid IFC encodings; this is disclosed.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import (
    NativeSourceSchema055Error,
    production_native_schema_delta_v055,
)

SOURCE_SHA="cd731db3ca41f3f18840aafb3fbfcb5a7d1b734a5961d06cb797563502d592d0"
TASK="topological_test_18"
NAMESPACE="urn:bim-markup-bench:toy:v0"
Q="{"+NAMESPACE+"}"
MAX_XML=200000
MAX_COMPACT=4096
MAX_CALLS=25


class Topo18Native059Error(ValueError):
    pass


def need(ok:bool,reason:str)->None:
    if not ok:
        raise Topo18Native059Error(reason)


def _parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def _source(path:Path,sha:str):
    path=Path(path)
    need(sha==SOURCE_SHA and path.is_file() and not path.is_symlink()
         and file_hash(path)==SOURCE_SHA,
         "Original source sha and exact file required")
    model=ifcopenshell.open(str(path))
    need(model.schema=="IFC4X3"
         and len(model.by_type("IfcSpace"))==3
         and len(model.by_type("IfcWall"))==7,
         "Original untouched IFC4X3 task signature has changed")
    need(file_hash(path)==sha,"Source modified while reading")
    return model


def _mesh_points(obj):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,obj)
    vertices=list(shape.geometry.verts)  # retain shape until native buffer copied
    need(len(vertices)>=9 and len(vertices)%3==0,
         "Missing source-native world mesh geometry")
    values=[tuple(float(vertices[k+i]) for i in range(3))
            for k in range(0,len(vertices),3)]
    need(all(math.isfinite(x) and abs(x)<1e4 for p in values for x in p),
         "Unbounded native geometry values")
    return values


def _bounds(obj):
    pts=_mesh_points(obj)
    return tuple((round(min(p[i] for p in pts),6),
                  round(max(p[i] for p in pts),6)) for i in range(3))


def _num(value:float)->str:
    need(math.isfinite(value) and abs(value)<1e5,
         "Invalid source geometry coordinate")
    return f"{value:.6f}"


def source_full_state_v059(source_ifc:Path,*,source_sha:str)->bytes:
    """Source-only full native source/projected managed state for BOTH arms."""
    original=_source(source_ifc,source_sha)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},
        attrib={
            "version":"0.59",
            "representation":"D_COMPLETE_XML_V059",
            "sourceOriginalIFCSha256":source_sha,
            "nativeSchema":"IFC4X3",
            "nativeUnit":"MILLIMETER",
            "managedSemantics":"ALL_ORIGINAL_SPACES_ONLY",
        })
    source=etree.SubElement(root,Q+"OriginalNativeIFCSource",
        {"ifcSHA256":source_sha,
         "rootGUIDCount":str(len(original.by_type("IfcRoot")))})
    products=etree.SubElement(source,Q+"Products")
    for entity in sorted(original.by_type("IfcProduct"),
                         key=lambda e:e.GlobalId):
        attributes={
            "ifcGuid":entity.GlobalId,
            "ifcClass":entity.is_a(),
            "name":str(entity.Name or ""),
        }
        if entity.Representation is not None:
            bounds=_bounds(entity)
            for axis,i in zip("XYZ",range(3)):
                attributes[f"min{axis}M"]=_num(bounds[i][0])
                attributes[f"max{axis}M"]=_num(bounds[i][1])
        etree.SubElement(products,Q+"SourceProduct",attributes)
    managed=etree.SubElement(root,Q+"ManagedElements",
        {"boundary":"ALL_THREE_ORIGINAL_IFCSPACE_GLOBALIDS"})
    for room in sorted(original.by_type("IfcSpace"),
                       key=lambda e:e.GlobalId):
        etree.SubElement(managed,Q+"Space",
                         {"ifcGuid":room.GlobalId,"present":"true"})
    raw=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(raw)<=MAX_XML,"Source XML exceeds checked transport")
    return raw


def compact_original_state_v059(source_ifc:Path,*,source_sha:str)->bytes:
    full=source_full_state_v059(source_ifc,source_sha=source_sha)
    root=etree.fromstring(full,_parser())
    compact=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},
        attrib={
            "version":"0.59",
            "representation":"D_MANAGED_FINAL_STATE_V059",
            "sourceOriginalIFCSha256":source_sha,
            "sourceBuildingStateSha256":sha256(full).hexdigest(),
            "managedBoundary":"ALL_THREE_ORIGINAL_IFCSPACE_GLOBALIDS",
        })
    for old in root[1]:
        etree.SubElement(compact,Q+"Space",dict(old.attrib))
    return etree.tostring(compact,encoding="utf8",xml_declaration=True)


def _validate_plain_tree(root,expected_tag:str,expected_attributes:dict,
                         child_tags:tuple[str,...]):
    need(root.tag==Q+expected_tag
         and dict(root.attrib)==expected_attributes
         and not (root.text or "").strip()
         and not (root.tail or "").strip()
         and len(root)==len(child_tags),
         "Untrusted final-state XML root/children/anchors")
    for element,tag in zip(root,child_tags):
        need(element.tag==Q+tag and not len(element)
             and not (element.text or "").strip()
             and not (element.tail or "").strip(),
             "Unexpected final-state child or nested data")


def _roster(source_root,managed):
    expected=list(source_root[1])
    need(len(expected)==len(managed)==3,
         "Complete original IfcSpace roster required")
    absent=[]
    for orig,sub in zip(expected,managed):
        _validate_plain_tree(sub,"Space",
            {"ifcGuid":orig.get("ifcGuid"),
             "present":sub.get("present")},
             ())
        need(set(sub.attrib)=={"ifcGuid","present"}
             and sub.get("present") in {"true","false"},
             "Invalid original GlobalId/final state membership")
        if sub.get("present")=="false":
            absent.append(sub.get("ifcGuid"))
    need(len(absent)==1,"Exactly one original room may be absent")
    return absent[0]


def parse_full_final_state_v059(source_ifc:Path,xml:bytes,*,source_sha:str)->str:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML,
         "Native whole final-state XML required")
    check_xml_bytes(xml)
    initial=source_full_state_v059(source_ifc,source_sha=source_sha)
    base=etree.fromstring(initial,_parser())
    candidate=etree.fromstring(xml,_parser())
    need(candidate.tag==Q+"BuildingState"
         and dict(candidate.attrib)==dict(base.attrib)
         and len(candidate)==2 and
         not (candidate.text or "").strip()
         and not (candidate.tail or "").strip(),
         "Original native source state root replaced")
    need(candidate[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(candidate[0],method="c14n")==
             etree.tostring(base[0],method="c14n"),
         "Immutable original products/bounds/relationships changed")
    need(candidate[1].tag==Q+"ManagedElements"
         and dict(candidate[1].attrib)==dict(base[1].attrib),
         "Invalid original complete space roster boundary")
    absent=_roster(base,candidate[1])
    need(file_hash(source_ifc)==source_sha,
         "Original IFC source changed during parse")
    return absent


def restore_compact_final_state_v059(source_ifc:Path,compact:bytes,
                                     *,source_sha:str)->tuple[bytes,str]:
    need(isinstance(compact,bytes) and 0<len(compact)<=MAX_COMPACT,
         "Compact managed final-state UTF-8 size invalid")
    check_xml_bytes(compact)
    original=source_full_state_v059(source_ifc,source_sha=source_sha)
    base=etree.fromstring(original,_parser())
    doc=etree.fromstring(compact,_parser())
    _validate_plain_tree(doc,"ManagedFinalState",{
        "version":"0.59",
        "representation":"D_MANAGED_FINAL_STATE_V059",
        "sourceOriginalIFCSha256":source_sha,
        "sourceBuildingStateSha256":sha256(original).hexdigest(),
        "managedBoundary":"ALL_THREE_ORIGINAL_IFCSPACE_GLOBALIDS",
    },("Space","Space","Space"))
    absent=_roster(base,doc)
    for src,new in zip(base[1],doc):
        src.set("present",new.get("present"))
    full=etree.tostring(base,encoding="utf8",xml_declaration=True)
    need(parse_full_final_state_v059(
         source_ifc,full,source_sha=source_sha)==absent,
         "Reconstructed entire final state changed native task intent")
    return full,absent


def compile_space_deletion_v059(source_ifc:Path,out:Path,
                                *,source_sha:str,absent_guid:str)->None:
    file=_source(source_ifc,source_sha)
    spaces={e.GlobalId:e for e in file.by_type("IfcSpace")}
    need(absent_guid in spaces,"Only original IfcSpace target")
    dest=Path(out)
    need(not dest.exists() and dest.parent.is_dir()
         and not dest.parent.is_symlink()
         and dest.resolve()!=Path(source_ifc).resolve(),
         "Fresh original native IFC output required")
    ifcopenshell.api.run("root.remove_product",file,
                        product=spaces[absent_guid])
    file.write(str(dest))
    need(dest.is_file() and not dest.is_symlink()
         and file_hash(source_ifc)==source_sha,
         "Failed original IFC non-mutating native write")


def _value(v):
    # IFC STEP text round-tripping normalizes floating-point literals.
    # Preserve actual native geometry/placements at sub-micrometre
    # precision while not treating harmless 1e-12 binary noise as edits.
    if isinstance(v,float):
        return round(v,6)
    if isinstance(v,ifcopenshell.entity_instance):
        return ("entity",v.is_a(),v.id(),getattr(v,"GlobalId",None))
    if isinstance(v,(tuple,list)):
        return tuple(_value(x) for x in v)
    return v


def _entity_signature(entity):
    return (entity.is_a(),tuple(sorted(
        (key,_value(value))
        for key,value in entity.get_info(include_identifier=False).items()
    )))


def native_space_delete_scope_v059(source_ifc:Path,candidate_ifc:Path,
                                    *,source_sha:str)->dict:
    """Independent real original/native IFCSpace cleanup/scope admission.

    Does NOT rely on model tool call, the submitted code, declarative diff,
    answer target GUIDs or the author scorer. It reconstructs a generic
    source-only IFC API cleanup reference for *whichever original IfcSpace
    was deleted*, then compares native surviving STEP-entity semantics.
    Strict admissible encoding constraint disclosed in research methods.
    """
    src=_source(source_ifc,source_sha)
    candpath=Path(candidate_ifc)
    need(candpath.is_file() and not candpath.is_symlink()
         and candpath.resolve()!=Path(source_ifc).resolve(),
         "Candidate must be separate real native IFC file")
    candidate_sha=file_hash(candpath)
    final=ifcopenshell.open(str(candpath))
    need(final.schema==src.schema,"Original schema must be preserved")
    original_spaces={x.GlobalId for x in src.by_type("IfcSpace")}
    final_spaces={x.GlobalId for x in final.by_type("IfcSpace")}
    removed=original_spaces-final_spaces
    need(len(removed)==1
         and not (final_spaces-original_spaces)
         and len(final_spaces)==2,
         "Exactly one original IfcSpace absent, none added")
    guid=next(iter(removed))
    expected=_source(source_ifc,source_sha)
    ifcopenshell.api.run("root.remove_product",
                        expected,product=expected.by_guid(guid))
    # All surviving IFC entity IDs/classes/direct referenced attributes
    # remain source-native canonical; only the removed space and its
    # precisely linked roots/subgraph are permitted to vanish.
    a={x.id():x for x in expected}
    z={x.id():x for x in final}
    need(set(a)==set(z),"Unexpected extra/missing original STEP entities")
    for eid in a:
        need(_entity_signature(a[eid])==_entity_signature(z[eid]),
             "Off-target IFC native entity, geometry or relation changed")
    # The same actual source-vs-output schema delta gate used by v0.55.
    schema=production_native_schema_delta_v055(
        source_ifc,candpath,source_sha=source_sha)
    need(schema["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS",
         "New IFC4X3 validator error in candidate")
    need(file_hash(source_ifc)==source_sha
         and file_hash(candpath)==candidate_sha,
         "TOCTOU source/candidate mutation")
    return {
        "status":"V059_SOURCE_ONLY_ORIGINAL_SPACE_NATIVE_SCOPE_AND_SCHEMA_PASS",
        "candidate_sha256":candidate_sha,
        "deleted_original_IfcSpace_count":1,
        "original_root_cleanup_verified_against_source_api":True,
        "all_surviving_ifc_entities_unchanged":True,
        "new_schema_errors":0,
        "author_repository_score":None,
        "published_paper_official_score":None,
    }
