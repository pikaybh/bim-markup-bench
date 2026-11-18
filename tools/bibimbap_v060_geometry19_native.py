"""v0.60 original source-native geometry_test_19: delete exactly two windows.

Real immutable original IFC4X3/mm, source only. Complete final 7-window
roster, full or compact source-anchored XML, real IFC window + associated
opening cleanup, independent native STEP entity and schema-delta acceptance.

Does not import public question scorer, original author hidden answer, trial
provider, a developer target list, or an operation/typed-plan XML. The native
scope oracle permits ANY two original windows so wrong solutions can be
graded SEPARATELY rather than leaking answer selection into model tools.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math
import time

import ifcopenshell
import ifcopenshell.api
from lxml import etree

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_production_schema_gate import (
    production_native_schema_delta_v055,
)
from tools.bibimbap_v059_topo18_native import _bounds,_value


SOURCE_SHA="9f492b328e18875ec1796259d8d29f429500f8003ebb1eead951e677996b230f"
TASK="geometry_test_19"
NAMESPACE="urn:bim-markup-bench:toy:v0"
Q="{"+NAMESPACE+"}"
MAX_XML_BYTES=22000
MAX_COMPACT_BYTES=4096
MAX_CALLS=25


class Geometry19Native060Error(ValueError):
    pass


def need(ok:bool,why:str)->None:
    if not ok:
        raise Geometry19Native060Error(why)


def _parser():
    return etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,recover=False,huge_tree=False)


def _source(path:Path,*,source_sha:str):
    path=Path(path)
    need(source_sha==SOURCE_SHA
         and path.is_file() and not path.is_symlink()
         and file_hash(path)==SOURCE_SHA,
         "Source identity must match exact original-public IFC source SHA")
    original=ifcopenshell.open(str(path))
    need(original.schema=="IFC4X3"
         and len(original.by_type("IfcWindow"))==7
         and len(original.by_type("IfcOpeningElement"))==7
         and len(original.by_type("IfcWall"))==8
         and len(original.by_type("IfcRelFillsElement"))==7
         and len(original.by_type("IfcRelVoidsElement"))==7,
         "Original exact seven-window and opening/host source signature invalid")
    for w in original.by_type("IfcWindow"):
        need(len(w.FillsVoids)==1,"Original window needs one filling")
        op=w.FillsVoids[0].RelatingOpeningElement
        need(op.is_a("IfcOpeningElement")
             and len(op.VoidsElements)==1
             and len(op.HasFillings)==1
             and op.HasFillings[0].RelatedBuildingElement==w,
             "Original window/opening/wall chain is not exactly one-to-one")
    need(file_hash(path)==source_sha,"Source changed during native read")
    return original


def _num(x):
    value=float(x)
    need(math.isfinite(value) and abs(value)<=1e5,
         "Native world geometry coordinate outside source limits")
    return f"{value:.6f}"


def source_full_state_v060(source_ifc:Path,*,source_sha:str)->bytes:
    original=_source(source_ifc,source_sha=source_sha)
    root=etree.Element(Q+"BuildingState",nsmap={None:NAMESPACE},
        attrib={
            "version":"0.60",
            "representation":"D_COMPLETE_XML_V060",
            "sourceOriginalIFCSha256":source_sha,
            "nativeSchema":"IFC4X3",
            "nativeUnit":"MILLIMETER",
            "managedSemantics":"ALL_SEVEN_ORIGINAL_WINDOWS_ONLY",
        })
    fixed=etree.SubElement(root,Q+"OriginalNativeIFCSource",
        {"ifcSHA256":source_sha,
         "rootGUIDCount":str(len(original.by_type("IfcRoot")))})
    products=etree.SubElement(fixed,Q+"Products")
    for entity in sorted(original.by_type("IfcProduct"),
                         key=lambda ent:ent.GlobalId):
        attr={
            "ifcGuid":entity.GlobalId,"ifcClass":entity.is_a(),
            "name":str(entity.Name or ""),
        }
        if entity.Representation is not None:
            bounds=_bounds(entity)
            for letter,index in zip("XYZ",range(3)):
                attr["min"+letter+"M"]=_num(bounds[index][0])
                attr["max"+letter+"M"]=_num(bounds[index][1])
        if entity.is_a("IfcWindow"):
            rel=entity.FillsVoids[0]
            opening=rel.RelatingOpeningElement
            attr["originalOpeningGuid"]=opening.GlobalId
            attr["originalHostWallGuid"]=opening.VoidsElements[0].RelatingBuildingElement.GlobalId
        if entity.is_a("IfcOpeningElement"):
            attr["originalHostWallGuid"]=entity.VoidsElements[0].RelatingBuildingElement.GlobalId
            attr["originalWindowGuid"]=entity.HasFillings[0].RelatedBuildingElement.GlobalId
        etree.SubElement(products,Q+"SourceProduct",attr)
    managed=etree.SubElement(root,Q+"ManagedElements",{
        "boundary":"ALL_SEVEN_ORIGINAL_IFCWINDOW_GUIDS"})
    for window in sorted(original.by_type("IfcWindow"),
                         key=lambda ent:ent.GlobalId):
        etree.SubElement(managed,Q+"Window",
                         {"ifcGuid":window.GlobalId,"present":"true"})
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_XML_BYTES,"Original XML source too large")
    return out


def compact_source_state_v060(source_ifc:Path,*,source_sha:str)->bytes:
    original=source_full_state_v060(source_ifc,source_sha=source_sha)
    state=etree.fromstring(original,_parser())
    root=etree.Element(Q+"ManagedFinalState",nsmap={None:NAMESPACE},attrib={
        "version":"0.60",
        "representation":"D_MANAGED_FINAL_STATE_V060",
        "sourceOriginalIFCSha256":source_sha,
        "sourceBuildingStateSha256":sha256(original).hexdigest(),
        "managedBoundary":"ALL_SEVEN_ORIGINAL_IFCWINDOW_GUIDS",
    })
    for old in state[1]:
        etree.SubElement(root,Q+"Window",dict(old.attrib))
    out=etree.tostring(root,encoding="utf8",xml_declaration=True)
    need(0<len(out)<=MAX_COMPACT_BYTES,"Managed complete roster too large")
    return out


def _roster(source:etree._Element,submitted)->tuple[str,str]:
    entries=list(source[1])
    need(len(entries)==len(submitted)==7,
         "All 7 original windows must be specified, no partial submission")
    absent=[]
    for prev,new in zip(entries,submitted):
        need(new.tag==Q+"Window" and not len(new)
             and dict(new.attrib)=={
                "ifcGuid":prev.get("ifcGuid"),
                "present":new.get("present"),
             }
             and new.get("present") in ("true","false")
             and not (new.text or "").strip()
             and not (new.tail or "").strip(),
             "Unknown/reordered/duplicated window or missing/extra state")
        if new.get("present")=="false":
            absent.append(new.get("ifcGuid"))
    need(len(absent)==2 and len(set(absent))==2,
         "Exactly two original Window GUIDs must be absent")
    return tuple(absent)


def parse_full_final_state_v060(source_ifc:Path,xml:bytes,
                                 *,source_sha:str)->tuple[str,str]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_XML_BYTES,
         "Bounded final-state XML required")
    check_xml_bytes(xml)
    base=etree.fromstring(
        source_full_state_v060(source_ifc,source_sha=source_sha),_parser())
    node=etree.fromstring(xml,_parser())
    need(node.tag==Q+"BuildingState"
         and dict(node.attrib)==dict(base.attrib)
         and len(node)==2
         and not (node.text or "").strip()
         and not (node.tail or "").strip(),
         "Original declarative BuildingState anchor changed")
    need(node[0].tag==Q+"OriginalNativeIFCSource"
         and etree.tostring(node[0],method="c14n")==
             etree.tostring(base[0],method="c14n"),
         "Original native source product/geometry and relationships mutated")
    need(node[1].tag==Q+"ManagedElements"
         and dict(node[1].attrib)==dict(base[1].attrib)
         and not (node[1].text or "").strip()
         and not (node[1].tail or "").strip(),
         "Complete original managed window boundary changed")
    missing=_roster(base,node[1])
    need(file_hash(source_ifc)==source_sha,"Source IFC mutated during parse")
    return missing


def restore_compact_final_state_v060(source_ifc:Path,xml:bytes,
                                     *,source_sha:str)->tuple[bytes,tuple[str,str]]:
    need(isinstance(xml,bytes) and 0<len(xml)<=MAX_COMPACT_BYTES,
         "Bounded complete managed state XML required")
    check_xml_bytes(xml)
    original=source_full_state_v060(source_ifc,source_sha=source_sha)
    base=etree.fromstring(original,_parser())
    node=etree.fromstring(xml,_parser())
    need(node.tag==Q+"ManagedFinalState"
         and dict(node.attrib)=={
             "version":"0.60",
             "representation":"D_MANAGED_FINAL_STATE_V060",
             "sourceOriginalIFCSha256":source_sha,
             "sourceBuildingStateSha256":sha256(original).hexdigest(),
             "managedBoundary":"ALL_SEVEN_ORIGINAL_IFCWINDOW_GUIDS",
         }
         and not (node.text or "").strip()
         and not (node.tail or "").strip(),
         "Compact complete state SHA/schema boundary violated")
    absent=_roster(base,node)
    for current,new in zip(base[1],node):
        current.set("present",new.get("present"))
    full=etree.tostring(base,encoding="utf8",xml_declaration=True)
    need(parse_full_final_state_v060(
        source_ifc,full,source_sha=source_sha)==absent,
        "Reconstructed original full native source state not valid")
    return full,absent


def compile_two_window_removal_v060(source_ifc:Path,
                                    output_ifc:Path,
                                    *,source_sha:str,
                                    absent_guids:tuple[str,str])->None:
    model=_source(source_ifc,source_sha=source_sha)
    original_windows={w.GlobalId:w for w in model.by_type("IfcWindow")}
    need(isinstance(absent_guids,tuple) and len(absent_guids)==2
         and len(set(absent_guids))==2
         and set(absent_guids).issubset(original_windows),
         "Must remove exactly two original Window identities")
    out=Path(output_ifc)
    need(not out.exists() and out.parent.is_dir()
         and not out.parent.is_symlink()
         and out.resolve()!=Path(source_ifc).resolve(),
         "Fresh separate native candidate IFC output required")
    for guid in absent_guids:
        win=model.by_guid(guid)
        opening=win.FillsVoids[0].RelatingOpeningElement
        ifcopenshell.api.run("root.remove_product",model,product=win)
        ifcopenshell.api.run("root.remove_product",model,product=opening)
    model.write(str(out))
    need(out.is_file() and not out.is_symlink()
         and file_hash(source_ifc)==source_sha,
         "Trusted native linked product deletion failed source preservation")


def _native_entity_signature_v060(entity):
    # IfcRelDefinesByType.RelatedObjects and other *SET*-valued inverse
    # relationship aggregates are unordered per IFC schema. Native writes
    # may reorder their STEP references without changing the semantics.
    # Other ordered attributes (including geometric paths) remain ordered.
    unordered_related={"RelatedObjects","RelatedElements","HasProperties"}
    fields=[]
    for key,val in entity.get_info(include_identifier=False).items():
        if key in unordered_related and isinstance(val,(tuple,list)):
            attr=tuple(sorted((_value(x) for x in val),key=repr))
        else:
            attr=_value(val)
        fields.append((key,attr))
    return (entity.is_a(),tuple(sorted(fields)))


def canonical_original_native_semantic_digest_v060(candidate_ifc:Path)->str:
    """Canonical stable *semantic* IFC digest, NOT raw file SHA256.

    IfcOpenShell writes unordered relationship SETs in different orders and
    native cleanup updates exactly IfcOwnerHistory.LastModifiedDate with
    real execution time. Only after the independent native oracle has
    admitted a candidate should this normalized semantic digest be used
    as the repeatable research report comparison artifact. Normalization
    is NOT permission to mutate metadata outside that native oracle.
    """
    file=ifcopenshell.open(str(candidate_ifc))
    rows=[]
    for entity in sorted(file,key=lambda x:x.id()):
        class_name,attributes=_native_entity_signature_v060(entity)
        if class_name=="IfcOwnerHistory":
            attributes=tuple((k,"NATIVE_CLEANUP_TIMESTAMP" if
                              k=="LastModifiedDate" else v)
                             for k,v in attributes)
        rows.append((entity.id(),class_name,attributes))
    return sha256(repr(rows).encode("utf8")).hexdigest()


def independent_two_window_native_scope_v060(
    source_ifc:Path,candidate_ifc:Path,*,source_sha:str,
)->dict:
    """Strict independent ORIGINAL IFC source-native relationship/scope.

    Blind to model code, author hidden answers, original public question and
    developer's desired pair. Reconstruct reference source cleanup for ANY
    two original Window GUIDs missing in candidate, and compare every
    surviving native STEP entity/linked reference plus schema error delta.
    """
    source=_source(source_ifc,source_sha=source_sha)
    candidate=Path(candidate_ifc)
    need(candidate.is_file() and not candidate.is_symlink()
         and candidate.resolve()!=Path(source_ifc).resolve(),
         "A native candidate separate from immutable source is mandatory")
    candidate_sha=file_hash(candidate)
    final=ifcopenshell.open(str(candidate))
    need(final.schema==source.schema,"Original native IFC4X3 schema changed")
    original_guids={w.GlobalId for w in source.by_type("IfcWindow")}
    final_guids={w.GlobalId for w in final.by_type("IfcWindow")}
    absent=original_guids-final_guids
    need(len(absent)==2 and len(final_guids)==5
         and not final_guids-original_guids
         and len(final.by_type("IfcOpeningElement"))==5,
         "Exactly two Windows and associated two Openings removed")
    # Derive expected cleanup from whichever original Windows are gone,
    # not a predetermined target answer, XML command, or evaluator code.
    reference=_source(source_ifc,source_sha=source_sha)
    for guid in sorted(absent):
        win=reference.by_guid(guid)
        opening=win.FillsVoids[0].RelatingOpeningElement
        ifcopenshell.api.run("root.remove_product",reference,product=win)
        ifcopenshell.api.run("root.remove_product",reference,product=opening)
    expected={entity.id():_native_entity_signature_v060(entity) for entity in reference}
    observed={entity.id():_native_entity_signature_v060(entity) for entity in final}
    need(set(expected)==set(observed),
         "Unexpected surviving/missing source native IFC entities")
    # IfcOpenShell's root.remove_product updates the shared, real native
    # IfcOwnerHistory.LastModifiedDate to time.time() in each independently
    # executed Windows/Docker process. This is benign source API metadata,
    # not an editing permission for arbitrary entities or owner attributes.
    # Accept only that one field, near BOTH native execution times, while
    # all other original STEP entities/references remain exactly equal.
    normalized_owner_timestamp_variances=0
    for eid in expected:
        left,right=expected[eid],observed[eid]
        if left==right:
            continue
        need(left[0]==right[0]=="IfcOwnerHistory",
             "Off-target IFC native entity/geometry/host relation changed")
        old=dict(left[1]);new=dict(right[1])
        prior=old.pop("LastModifiedDate",None)
        post=new.pop("LastModifiedDate",None)
        now=int(time.time())
        need(old==new and type(prior) is int and type(post) is int
             and abs(prior-post)<=300
             and abs(prior-now)<=300 and abs(post-now)<=300,
             "Unexpected source OwnerHistory attributes/timestamp")
        normalized_owner_timestamp_variances+=1
    need(normalized_owner_timestamp_variances<=1,
         "Too many unrelated OwnerHistory changes")
    source_schema=production_native_schema_delta_v055(
        source_ifc,candidate,source_sha=source_sha)
    need(source_schema["status"]=="PASS_NO_NEW_SCHEMA_FINDINGS"
         and source_schema["introduced_schema_error_count"]==0,
         "New IFC4X3 schema validation errors")
    need(file_hash(source_ifc)==source_sha
         and file_hash(candidate)==candidate_sha,
         "Candidate or source edited concurrently")
    return {
        "status":"V060_SOURCE_NATIVE_TWO_WINDOWS_OPENINGS_SCOPE_AND_SCHEMA_PASS",
        "deleted_original_windows":2,
        "deleted_linked_original_openings":2,
        "other_native_Ifc_entities_referentially_preserved":True,
        "source_sha256_preserved":True,
        "candidate_sha256":candidate_sha,
        "introduced_schema_error_count":0,
        "author_repository_score":None,
        "published_paper_score":None,
    }
