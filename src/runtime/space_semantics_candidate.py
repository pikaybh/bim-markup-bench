"""Separately versioned *candidate* source IFC Space semantics overlay.

Only read-only inspection and XSD-validated presentation of native source
IfcSpace metadata. This file intentionally does NOT alter:
  - frozen toy v0.1 schema / source projection / compiler,
  - sampled tasks or model-facing runtime contracts,
  - official evaluation, scoring, or native Space mutation behavior.

The overlay is not an agent-editable feature yet: changes fail closed until
a versioned experimental protocol and independent native compiler exist.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal,InvalidOperation
import hashlib
import re

import ifcopenshell
from lxml import etree

from src.runtime.ifc_projection import project_ifc
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.space_metadata_gate import preflight_source_room_semantics
from src.security.agent_boundary import check_xml_bytes

ROOT=Path(__file__).resolve().parents[2]
SCHEMA_FILE=ROOT/"spec/space_semantics_v0_2_candidate.xsd"
NS="urn:bim-markup-bench:space-semantics:v0.2-candidate"
MAX_CANDIDATE_BYTES=2*1024*1024
GUID_CHARS=re.compile(r"^[0-9A-Za-z_$]{22}$")
VALUE_TYPES={
    "IfcIdentifier","IfcLabel","IfcText","IfcBoolean","IfcInteger","IfcReal",
}


class UnsupportedSpaceSemanticCandidate(ValueError):
    """Source IFC contains information this candidate profile cannot express."""


@dataclass(frozen=True)
class SpaceSemanticsCandidate:
    xml:bytes
    source_sha256:str
    source_space_count:int
    source_type_count:int
    source_pset_count:int
    source_reference_count:int

    def report(self)->dict:
        return {
            "profile":"space-semantics-v0.2-candidate",
            "source_sha256":self.source_sha256,
            "xml_sha256":hashlib.sha256(self.xml).hexdigest(),
            "source_space_count":self.source_space_count,
            "source_type_count":self.source_type_count,
            "source_instance_pset_count":self.source_pset_count,
            "source_reference_property_count":self.source_reference_count,
            "read_only_semantic_projection_validated":True,
            "model_facing_protocol_promoted":False,
            "official_evaluation_eligible":False,
            "new_space_type_or_reference_inferred":False,
        }


def _xsd():
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                           no_network=True,huge_tree=False)
    doc=etree.parse(str(SCHEMA_FILE),parser)
    if doc.find(".//{http://www.w3.org/2001/XMLSchema}include") is not None:
        raise UnsupportedSpaceSemanticCandidate("Candidate XSD includes disallowed")
    if doc.find(".//{http://www.w3.org/2001/XMLSchema}import") is not None:
        raise UnsupportedSpaceSemanticCandidate("Candidate XSD imports disallowed")
    return etree.XMLSchema(doc)


def _typed_value(value):
    if value is None or not isinstance(value,ifcopenshell.entity_instance):
        raise UnsupportedSpaceSemanticCandidate("Null/native-less property value")
    kind=value.is_a()
    if kind not in VALUE_TYPES:
        raise UnsupportedSpaceSemanticCandidate("Unsupported native IfcValue type")
    raw=value.wrappedValue
    if kind=="IfcBoolean":
        return kind,"true" if raw else "false"
    if kind=="IfcInteger":
        if isinstance(raw,bool) or not isinstance(raw,int):
            raise UnsupportedSpaceSemanticCandidate("Invalid IFC integer property")
        return kind,str(raw)
    if kind=="IfcReal":
        try:
            n=Decimal(str(raw))
        except (InvalidOperation,ValueError,TypeError) as exc:
            raise UnsupportedSpaceSemanticCandidate("Invalid IFC real property") from exc
        if not n.is_finite():
            raise UnsupportedSpaceSemanticCandidate("Nonfinite IFC real property")
        return kind,format(n,"f")
    if not isinstance(raw,str):
        raise UnsupportedSpaceSemanticCandidate("Unsupported IFC textual property")
    return kind,raw


def _field(entity,attribute):
    val=getattr(entity,attribute,None)
    if not isinstance(val,str) or not val or len(val)>255:
        raise UnsupportedSpaceSemanticCandidate("Required native Space/Type string missing")
    return val


def _make_source_spaces(model,projected):
    mapping=dict(projected.projected_global_ids)
    spaces=sorted(model.by_type("IfcSpace"),key=lambda sp:sp.GlobalId)
    if not spaces or len(spaces)>512:
        raise UnsupportedSpaceSemanticCandidate("No Space or excessive source Space count")
    if any(sp.GlobalId not in mapping for sp in spaces):
        raise UnsupportedSpaceSemanticCandidate(
            "Cannot claim Space metadata coverage if an IfcSpace is unprojected")
    count_type=count_pset=count_ref=0
    tuples=[]
    for space in spaces:
        preflight_source_room_semantics(model,space.GlobalId)
        if (space.Description is not None or space.ObjectType is not None
                or space.ElevationWithFlooring is not None):
            raise UnsupportedSpaceSemanticCandidate(
                "Native source Space has additional unsupported attributes")
        if not GUID_CHARS.fullmatch(space.GlobalId):
            raise UnsupportedSpaceSemanticCandidate("Malformed native Space GlobalId")
        base={
            "localId":mapping[space.GlobalId],
            "ifcGuid":space.GlobalId,
            "name":_field(space,"Name"),
            "predefinedType":str(space.PredefinedType),
            "compositionType":str(space.CompositionType),
            "status":"SOURCE_OBSERVED",
        }
        if space.LongName is not None:
            if len(str(space.LongName))>1024:
                raise UnsupportedSpaceSemanticCandidate("Oversized Space LongName")
            base["longName"]=str(space.LongName)
        type_info=None
        links=list(space.IsTypedBy)
        if links:
            link=links[0]
            typ=link.RelatingType
            if (typ.Description is not None or typ.ApplicableOccurrence is not None
                    or typ.ElementType is not None or typ.HasPropertySets):
                raise UnsupportedSpaceSemanticCandidate(
                    "SpaceType has properties/metadata omitted by candidate")
            type_info={
                "relationGuid":link.GlobalId,
                "typeGuid":typ.GlobalId,
                "name":_field(typ,"Name"),
                "predefinedType":str(typ.PredefinedType),
            }
            count_type+=1
        property_sets=[]
        for link in sorted(space.IsDefinedBy,key=lambda r:r.GlobalId):
            pset=link.RelatingPropertyDefinition
            if pset.Description is not None:
                raise UnsupportedSpaceSemanticCandidate(
                    "IFC Pset description cannot be represented")
            if len(pset.HasProperties)>64:
                raise UnsupportedSpaceSemanticCandidate("Too many IFC Pset properties")
            attrs={
                "relationGuid":link.GlobalId,
                "psetGuid":pset.GlobalId,
                "name":_field(pset,"Name"),
            }
            properties=[]
            seen=set()
            for item in sorted(pset.HasProperties,key=lambda p:p.Name):
                name=_field(item,"Name")
                if name in seen:
                    raise UnsupportedSpaceSemanticCandidate("Duplicate IFC property name")
                seen.add(name)
                if getattr(item,"Description",None) is not None or item.Unit is not None:
                    raise UnsupportedSpaceSemanticCandidate(
                        "Unrepresented native property description/unit")
                typ,value=_typed_value(item.NominalValue)
                if len(value)>1024:
                    raise UnsupportedSpaceSemanticCandidate("Property value exceeds candidate schema")
                properties.append({"name":name,"valueType":typ,"value":value})
                if name=="Reference":
                    count_ref+=1
            if not properties:
                raise UnsupportedSpaceSemanticCandidate("Pset without properties unsupported")
            property_sets.append((attrs,properties))
            count_pset+=1
        tuples.append((base,type_info,property_sets))
    return tuples,count_type,count_pset,count_ref


def _build_document(semantics,source_sha):
    root=etree.Element("{"+NS+"}SpaceSemantics",
                       nsmap={None:NS},
                       attrib={
                           "version":"0.2-candidate",
                           "sourceModelSha256":source_sha,
                           "baseSchema":"toy:v0.1",
                           "ifcSchema":"IFC4X3",
                           "policy":"SOURCE_OBSERVATION_ONLY",
                       })
    for attrs,type_info,sets in semantics:
        room=etree.SubElement(root,"{"+NS+"}Space",attrib=attrs)
        if type_info is not None:
            etree.SubElement(room,"{"+NS+"}Type",attrib=type_info)
        prop_container=etree.SubElement(room,"{"+NS+"}PropertySets")
        for pset,properties in sets:
            parent=etree.SubElement(prop_container,"{"+NS+"}PropertySet",
                                    attrib=pset)
            for property_attrs in properties:
                etree.SubElement(parent,"{"+NS+"}Property",attrib=property_attrs)
        etree.SubElement(room,"{"+NS+"}Quantities",
                         attrib={"status":"NONE_IN_SOURCE"})
    return etree.tostring(root,encoding="UTF-8",
                          xml_declaration=True,pretty_print=True)


def _validate_candidate(raw,sha):
    if not isinstance(raw,bytes) or len(raw)>MAX_CANDIDATE_BYTES:
        raise UnsupportedSpaceSemanticCandidate("Oversized/invalid candidate XML")
    try:
        check_xml_bytes(raw)
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,huge_tree=False)
        tree=etree.fromstring(raw,parser=parser)
        _xsd().assertValid(tree)
    except Exception as exc:
        raise UnsupportedSpaceSemanticCandidate(
            "Candidate XML rejected by secure local XSD") from exc
    if tree.get("sourceModelSha256")!=sha:
        raise UnsupportedSpaceSemanticCandidate(
            "Candidate source digest differs from immutable IFC")
    return tree


def project_space_semantics_candidate(source:Path)->SpaceSemanticsCandidate:
    """Produce read-only versioned experimental candidate from public input."""
    initial=snapshot_source(source)
    if initial.ifc_schema!="IFC4X3":
        raise UnsupportedSpaceSemanticCandidate("Candidate requires IFC4X3")
    base=project_ifc(source)
    if base.source.source_sha256!=initial.source_sha256:
        raise UnsupportedSpaceSemanticCandidate("IFC source changed during projection")
    native=ifcopenshell.open(str(source))
    records,num_types,num_psets,num_references=_make_source_spaces(native,base)
    xml=_build_document(records,initial.source_sha256)
    _validate_candidate(xml,initial.source_sha256)
    if snapshot_source(source).source_sha256!=initial.source_sha256:
        raise UnsupportedSpaceSemanticCandidate("IFC source mutated during observation")
    return SpaceSemanticsCandidate(
        xml,initial.source_sha256,len(records),num_types,num_psets,num_references)


def verify_unedited_space_semantics_candidate(source:Path,raw:bytes)->dict:
    """Fail closed on a forged/stale/new-room metadata declaration.

    This is a *read-only* candidate. It does not approve editing XML to
    assign a new IfcSpaceType, Pset, number or QTO to an added room.
    """
    expected=project_space_semantics_candidate(source)
    incoming=_validate_candidate(raw,expected.source_sha256)
    canonical=_validate_candidate(expected.xml,expected.source_sha256)
    def normalized(node):
        return (node.tag,tuple(sorted(node.attrib.items())),
                tuple(normalized(child) for child in node),
                (node.text or "").strip())
    if normalized(incoming)!=normalized(canonical):
        raise UnsupportedSpaceSemanticCandidate(
            "Semantic candidate edited or contains invented native Space metadata")
    return {
        **expected.report(),
        "source_semantic_observation_matches_exact_ifc":True,
        "unedited_candidate_verified":True,
        "new_space_metadata_authoring_supported":False,
    }
