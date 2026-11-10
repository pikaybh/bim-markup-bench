"""Experimental v0.2 *declarative state* -> IFC Space metadata compiler.

Distinct from frozen toy v0.1 and both actual G2 LLM runners. The supplied
XML states the intended new-room name, unique reference, type, two Psets and
computed QTO. The trusted backend checks a read-only source semantic snapshot,
the v0.1 geometry state, native IFC solids, old relationship preservation and
all explicit new metadata BEFORE atomic publishing.

Never infer new room identities from source nor expose an imperative XML API.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import uuid

import ifcopenshell
from lxml import etree
import numpy as np

from src.runtime.binder import allocate_new_ifc_guid
from src.runtime.compiler import compile_declarative_xml
from src.runtime.transaction import stage_and_commit
from src.runtime.space_metadata_gate import (
    preflight_source_room_semantics,
)
from src.runtime.space_partition_preflight import _exact_box
from src.runtime.space_semantics_candidate import (
    project_space_semantics_candidate,verify_unedited_space_semantics_candidate,
)
from src.runtime.xml_parser import parse_xml
from src.security.agent_boundary import check_xml_bytes

NS="urn:bim-markup-bench:space-semantics:authoring:v0.2"
ROOT=Path(__file__).resolve().parents[2]
XSD=ROOT/"spec/space_semantics_v0_2_authoring.xsd"
GUID_NAMESPACE=uuid.UUID("ae7d2594-ff47-49fd-aefe-2827043dc649")
MAX_BYTES=65536


class UnsupportedExplicitSpaceSemantics(ValueError):
    """New-room IFC semantic identity or numeric value is unproven."""


def new_metadata_guid(source_sha:str,space_guid:str,kind:str)->str:
    """Published deterministic ID contract; no source-room GUID recycling."""
    return ifcopenshell.guid.compress(
        uuid.uuid5(GUID_NAMESPACE,
            f"v0.2-explicit-space-metadata:{source_sha}:{space_guid}:{kind}").hex)


@dataclass(frozen=True)
class SpaceMetadataState:
    local_id:str
    name:str
    long_name:str
    type_name:str
    reference:str
    area_m2:Decimal
    volume_m3:Decimal


def parse_authored_space_state(xml:bytes,source_sha:str,
                             source_observation_sha:str)->SpaceMetadataState:
    if not isinstance(xml,bytes) or not xml or len(xml)>MAX_BYTES:
        raise UnsupportedExplicitSpaceSemantics("Invalid or oversized metadata state")
    try:
        check_xml_bytes(xml)
        parser=etree.XMLParser(resolve_entities=False,load_dtd=False,
                               no_network=True,huge_tree=False)
        root=etree.fromstring(xml,parser=parser)
        schema=etree.XMLSchema(etree.parse(str(XSD),parser))
        schema.assertValid(root)
    except Exception as exc:
        raise UnsupportedExplicitSpaceSemantics("Invalid secure v0.2 authoring XML") from exc
    if (root.get("sourceModelSha256")!=source_sha or
            root.get("sourceObservationSha256")!=source_observation_sha):
        raise UnsupportedExplicitSpaceSemantics("Source IFC/semantic observation hash stale")
    if len(root)!=1 or root[0].tag!="{"+NS+"}Space":
        raise UnsupportedExplicitSpaceSemantics("Expected one new declarative Space state")
    room=root[0]
    typ=room.find("{"+NS+"}Type")
    sets=room.find("{"+NS+"}PropertySets")
    qty=room.find("{"+NS+"}Quantities")
    if typ is None or sets is None or qty is None:
        raise UnsupportedExplicitSpaceSemantics("Missing new Space type/Pset/QTO state")
    psets={}
    for pset in sets:
        key=pset.get("name")
        if key in psets:
            raise UnsupportedExplicitSpaceSemantics("Duplicate Space Pset name")
        members={}
        for prop in pset:
            name=prop.get("name")
            if name in members:
                raise UnsupportedExplicitSpaceSemantics("Duplicate property in Space Pset")
            members[name]=(prop.get("valueType"),prop.get("value"))
        psets[key]=members
    if set(psets)!={"Pset_SpaceCommon","Pset_SpaceHeaterTypeCommon"}:
        raise UnsupportedExplicitSpaceSemantics("Candidate requires two explicit source-compatible Psets")
    common=psets["Pset_SpaceCommon"]
    heater=psets["Pset_SpaceHeaterTypeCommon"]
    if (set(common)!={"Reference","IsExternal"} or set(heater)!={"Reference"}
            or common["Reference"]!=heater["Reference"]
            or common["Reference"][0]!="IfcIdentifier"
            or common["IsExternal"]!=("IfcBoolean","false")):
        raise UnsupportedExplicitSpaceSemantics(
            "Pset Reference/IsExternal values must be explicit and consistent")
    reference=common["Reference"][1]
    if (not reference or not reference.strip()
            or room.get("name").strip()=="" or typ.get("name").strip()==""):
        raise UnsupportedExplicitSpaceSemantics("Required new Space identifier missing")
    try:
        area=Decimal(qty.get("netFloorAreaM2"))
        volume=Decimal(qty.get("netVolumeM3"))
    except (InvalidOperation,TypeError) as exc:
        raise UnsupportedExplicitSpaceSemantics("Invalid Space quantity") from exc
    if not area.is_finite() or not volume.is_finite() or area<=0 or volume<=0:
        raise UnsupportedExplicitSpaceSemantics("Nonfinite or nonpositive new Space quantity")
    return SpaceMetadataState(
        local_id=room.get("localId"),
        name=room.get("name"),
        long_name=room.get("longName"),
        type_name=typ.get("name"),
        reference=reference,
        area_m2=area,volume_m3=volume)


def _native_shape_measure(space):
    low,high=_exact_box(space,kind="IfcSpace")
    dims=high-low
    if not np.isfinite(dims).all() or np.min(dims)<=0:
        raise UnsupportedExplicitSpaceSemantics("Native new room has degenerate body")
    return float(dims[0]*dims[1]),float(np.prod(dims))


def _assert_unique_new_space_semantics(model,far,state):
    if any(other.GlobalId!=far.GlobalId and other.Name==state.name
           for other in model.by_type("IfcSpace")):
        raise UnsupportedExplicitSpaceSemantics("New Space name conflicts with existing Space")
    if any(other.Name==state.type_name for other in model.by_type("IfcSpaceType")):
        raise UnsupportedExplicitSpaceSemantics("New SpaceType name conflicts with existing type")
    for existing in model.by_type("IfcSpace"):
        if existing.GlobalId==far.GlobalId:
            continue
        for rel in existing.IsDefinedBy:
            prop_set=rel.RelatingPropertyDefinition
            if not prop_set.is_a("IfcPropertySet"):
                continue
            for prop in prop_set.HasProperties:
                if prop.Name=="Reference" and prop.is_a("IfcPropertySingleValue"):
                    value=prop.NominalValue
                    if value is not None and str(value.wrappedValue)==state.reference:
                        raise UnsupportedExplicitSpaceSemantics(
                            "New Space Reference conflicts with original room identity")


def _metadata_ids(source_sha,far_guid):
    names=("TYPE","TYPE_REL","PSET_COMMON","PSET_COMMON_REL",
           "PSET_HEATER","PSET_HEATER_REL","QTO","QTO_REL")
    return {kind:new_metadata_guid(source_sha,far_guid,kind) for kind in names}


def apply_explicit_metadata_to_native(model,source_sha,far_guid,state):
    """Trusted D0 authoring backend; mutates ONLY temporary candidate IFC."""
    if model.schema!="IFC4X3":
        raise UnsupportedExplicitSpaceSemantics("Space metadata requires IFC4X3")
    try:
        far=model.by_guid(far_guid)
    except RuntimeError as exc:
        raise UnsupportedExplicitSpaceSemantics("New Space missing in bounded geometry result") from exc
    if not far.is_a("IfcSpace") or far.IsTypedBy or far.IsDefinedBy or far.HasAssociations:
        raise UnsupportedExplicitSpaceSemantics("New Space already has ambiguous metadata")
    _assert_unique_new_space_semantics(model,far,state)
    area,vol=_native_shape_measure(far)
    if (abs(area-float(state.area_m2))>1e-7 or
            abs(vol-float(state.volume_m3))>1e-7):
        raise UnsupportedExplicitSpaceSemantics("Declared area/volume not supported by IFC solid")
    ids=_metadata_ids(source_sha,far_guid)
    for guid in ids.values():
        try:
            model.by_guid(guid)
        except RuntimeError:
            pass
        else:
            raise UnsupportedExplicitSpaceSemantics("Deterministic metadata GlobalId collision")
    far.Name=state.name
    far.LongName=state.long_name
    far.PredefinedType="NOTDEFINED"
    far.CompositionType="ELEMENT"
    typ=model.createIfcSpaceType(GlobalId=ids["TYPE"],
                                 Name=state.type_name,
                                 PredefinedType="NOTDEFINED")
    model.createIfcRelDefinesByType(
        GlobalId=ids["TYPE_REL"],RelatedObjects=(far,),RelatingType=typ)
    def pset(label,name,values):
        props=[]
        for key,kind,value in values:
            v=(model.createIfcBoolean(value=="true")
               if kind=="IfcBoolean" else model.createIfcIdentifier(value))
            props.append(model.createIfcPropertySingleValue(
                Name=key,NominalValue=v,Unit=None))
        record=model.createIfcPropertySet(GlobalId=ids[label],Name=name,
                                          HasProperties=tuple(props))
        model.createIfcRelDefinesByProperties(
            GlobalId=ids[label+"_REL"],RelatedObjects=(far,),
            RelatingPropertyDefinition=record)
    pset("PSET_COMMON","Pset_SpaceCommon",
         (("Reference","IfcIdentifier",state.reference),
          ("IsExternal","IfcBoolean","false")))
    pset("PSET_HEATER","Pset_SpaceHeaterTypeCommon",
         (("Reference","IfcIdentifier",state.reference),))
    quant=model.createIfcElementQuantity(
        GlobalId=ids["QTO"],Name="Qto_SpaceBaseQuantities",
        Quantities=(
            model.createIfcQuantityArea(Name="NetFloorArea",AreaValue=area),
            model.createIfcQuantityVolume(Name="NetVolume",VolumeValue=vol),
        ))
    model.createIfcRelDefinesByProperties(
        GlobalId=ids["QTO_REL"],RelatedObjects=(far,),
        RelatingPropertyDefinition=quant)
    return ids


def _new_metadata_native_observation(model,source_sha,far_guid,state):
    far=model.by_guid(far_guid)
    ids=_metadata_ids(source_sha,far_guid)
    if (far.Name!=state.name or far.LongName!=state.long_name
            or str(far.PredefinedType)!="NOTDEFINED"
            or str(far.CompositionType)!="ELEMENT"):
        raise UnsupportedExplicitSpaceSemantics("New Space identity differs from authored state")
    if (len(far.IsTypedBy)!=1 or len(far.IsDefinedBy)!=3
            or len(far.HasAssociations)):
        raise UnsupportedExplicitSpaceSemantics("New Space metadata relationship inventory wrong")
    actual_type=far.IsTypedBy[0]
    if (actual_type.GlobalId!=ids["TYPE_REL"] or
            len(actual_type.RelatedObjects)!=1 or
            actual_type.RelatedObjects[0].GlobalId!=far_guid or
            actual_type.RelatingType.GlobalId!=ids["TYPE"] or
            actual_type.RelatingType.Name!=state.type_name or
            str(actual_type.RelatingType.PredefinedType)!="NOTDEFINED"):
        raise UnsupportedExplicitSpaceSemantics("Native SpaceType does not match XML state")
    expected_psets={
        "Pset_SpaceCommon":{
            "Reference":("IfcIdentifier",state.reference),
            "IsExternal":("IfcBoolean","false"),
        },
        "Pset_SpaceHeaterTypeCommon":{
            "Reference":("IfcIdentifier",state.reference),
        },
    }
    qto_found=0
    for rel in far.IsDefinedBy:
        record=rel.RelatingPropertyDefinition
        if record.is_a("IfcElementQuantity"):
            if (rel.GlobalId!=ids["QTO_REL"] or record.GlobalId!=ids["QTO"] or
                    record.Name!="Qto_SpaceBaseQuantities" or len(record.Quantities)!=2):
                raise UnsupportedExplicitSpaceSemantics("Native QTO metadata wrong")
            if len({x.Name for x in record.Quantities})!=len(record.Quantities):
                raise UnsupportedExplicitSpaceSemantics("Duplicate native QTO quantity name")
            values={x.Name:(x.is_a(),getattr(x,"AreaValue",getattr(x,"VolumeValue",None)))
                    for x in record.Quantities}
            native_area,native_volume=_native_shape_measure(far)
            expected_quantities={
                "NetFloorArea":("IfcQuantityArea",native_area),
                "NetVolume":("IfcQuantityVolume",native_volume),
            }
            if (set(values)!=set(expected_quantities) or
                    any(values[k][0]!=kind or abs(values[k][1]-v)>1e-7
                        for k,(kind,v) in expected_quantities.items())):
                raise UnsupportedExplicitSpaceSemantics("Native QTO does not equal geometric quantities")
            qto_found+=1
            continue
        if not record.is_a("IfcPropertySet") or record.Name not in expected_psets:
            raise UnsupportedExplicitSpaceSemantics("Unexpected new-room property definition")
        key="PSET_COMMON" if record.Name=="Pset_SpaceCommon" else "PSET_HEATER"
        if (record.GlobalId!=ids[key] or rel.GlobalId!=ids[key+"_REL"]
                or len(rel.RelatedObjects)!=1
                or rel.RelatedObjects[0].GlobalId!=far_guid
                or len(record.HasProperties)!=len(expected_psets[record.Name])):
            raise UnsupportedExplicitSpaceSemantics("New-room Pset identity/membership mismatch")
        from src.runtime.space_semantics_candidate import _typed_value
        values={x.Name:_typed_value(x.NominalValue) for x in record.HasProperties}
        if values!=expected_psets[record.Name]:
            raise UnsupportedExplicitSpaceSemantics("New-room Pset values mismatch")
    if qto_found!=1:
        raise UnsupportedExplicitSpaceSemantics("New-room QTO missing")
    return ids


def compile_explicit_space_semantics_candidate(source:Path,edited_v01_xml:bytes,
                                               observed_semantics_v02:bytes,
                                               authored_semantics_v02:bytes,
                                               destination:Path)->dict:
    """One source-backed independent *experiment* candidate; not a G2 runner.

    D0 edits two declarative STATE documents. Native implementation is a
    trusted post-processor outside the model's execution capabilities. This
    function does not alter original v0.1 compiler or scorer behavior.
    """
    source=Path(source);destination=Path(destination)
    original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    verified=verify_unedited_space_semantics_candidate(
        source,observed_semantics_v02)
    if verified["source_sha256"]!=original_sha:
        raise UnsupportedExplicitSpaceSemantics("Candidate source metadata digest stale")
    state=parse_authored_space_state(
        authored_semantics_v02,original_sha,
        hashlib.sha256(observed_semantics_v02).hexdigest())
    base_doc=parse_xml(edited_v01_xml,expected_source_sha256=original_sha)
    created=[x for x in base_doc.elements if x.kind=="Space" and x.id==state.local_id]
    if len(created)!=1 or created[0].ifc_guid is not None:
        raise UnsupportedExplicitSpaceSemantics(
            "Authored metadata must link exactly to new v0.1 Space local ID")
    far_guid=allocate_new_ifc_guid(original_sha,"Space",state.local_id,set())
    with TemporaryDirectory(prefix="v02-explicit-space-meta-") as tmp:
        geometric=Path(tmp)/"v01-geometric-split.ifc"
        geometry_report=compile_declarative_xml(source,edited_v01_xml,geometric)
        if not geometry_report.write_committed or sum(
            op.operation=="SPLIT_SPACE" for op in geometry_report.operations)!=1:
            raise UnsupportedExplicitSpaceSemantics("Native v0.1 bounded split not verified")
        original=ifcopenshell.open(str(source))
        # Reuse source-only metadata policy before any new semantic objects.
        for room in original.by_type("IfcSpace"):
            preflight_source_room_semantics(original,room.GlobalId)
        expected_ids=_metadata_ids(original_sha,far_guid)
        def writer(stage):
            f=ifcopenshell.open(str(geometric))
            apply_explicit_metadata_to_native(f,original_sha,far_guid,state)
            f.write(str(stage))
        def validator(stage):
            if hashlib.sha256(source.read_bytes()).hexdigest()!=original_sha:
                raise UnsupportedExplicitSpaceSemantics("Source IFC changed during candidate compile")
            result=ifcopenshell.open(str(stage))
            _new_metadata_native_observation(result,original_sha,far_guid,state)
            baseline=ifcopenshell.open(str(geometric))
            a={x.GlobalId:x for x in baseline.by_type("IfcRoot")}
            b={x.GlobalId:x for x in result.by_type("IfcRoot")}
            if (set(a)-set(b) or
                    set(b)-set(a)!=set(expected_ids.values())):
                raise UnsupportedExplicitSpaceSemantics("Unexpected IFC Root changes from metadata compile")
            for guid in a:
                if guid==far_guid:
                    continue
                if str(a[guid])!=str(b[guid]):
                    raise UnsupportedExplicitSpaceSemantics(
                        "Existing native IFC Root modified during metadata authoring")
            from src.runtime.space_metadata_gate import _space_metadata
            for room in original.by_type("IfcSpace"):
                if _space_metadata(room)!=_space_metadata(result.by_guid(room.GlobalId)):
                    raise UnsupportedExplicitSpaceSemantics(
                        "Source Space metadata changed in v0.2 candidate")
            if (not np.allclose(_exact_box(baseline.by_guid(far_guid),kind="IfcSpace")[0],
                                _exact_box(result.by_guid(far_guid),kind="IfcSpace")[0],atol=1e-7)
                    or not np.allclose(_exact_box(baseline.by_guid(far_guid),kind="IfcSpace")[1],
                                       _exact_box(result.by_guid(far_guid),kind="IfcSpace")[1],atol=1e-7)):
                raise UnsupportedExplicitSpaceSemantics("Native geometry changed during Space metadata authoring")
        stage_and_commit(destination,writer,validator)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=original_sha:
        raise UnsupportedExplicitSpaceSemantics("Source IFC mutated after prototype compile")
    return {
        "status":"EXPERIMENTAL_EXPLICIT_SPACE_SEMANTICS_COMPILED_NOT_MODEL_OR_OFFICIAL",
        "source_sha256":original_sha,
        "result_sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),
        "source_metadata_observation_verified":True,
        "new_space_type_declared_and_written":True,
        "new_space_two_psets_declared_and_written":True,
        "new_space_qto_explicit_and_native_geometry_checked":True,
        "original_room_type_and_psets_preserved":True,
        "result_new_root_semantic_count":len(expected_ids),
        "frozen_v01_compiler_unchanged":True,
        "official_task_success":False,
        "model_calls":0,
    }
