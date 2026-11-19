"""v0.44 source-SHA pinned ORIGINAL UPDATE/DELETE IFC4X3/mm read-only XML.

This is *not* an IFC editor or benchmark task solver. The original native IFC
DATA entities, relationships, type, property, materials, local placements and
observable world shapes are model-visible as immutable source facts. The host
MUST reject every submit_building_xml attempt on this variant, until a separate
matched native UPDATE/DELETE writer/oracle is frozen and tested.

Never loads original grader/GT, never calls paid LLM or Docker.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash

HERE=Path(__file__).resolve()
XSD=HERE.parents[2]/"spec"/"original_native_step_readonly_v044.xsd"
NS="urn:bim-markup-bench:toy:v0"
Q="{"+NS+"}"
PINS={
    "67ac42ca988bdfd44a2afe3ebaff8be11da913b281338ec127f4897e3f42f6a3":
        ("geometry_test_14","update","b59ec5fa8ade37d69b6c600022824415dfaf1e97b28facfc6998a4c95f91dfaa",119,5),
    "318fb45af8142c164c1fc53eeadc472008ff9c42e9c1b6398e9c95aa744374af":
        ("geometry_test_15","update","178269bc5998194ba8566140de75afd4e9f8e065cfe8f6561141156b739b4126",166,8),
    "c85a8b90f1b2d22f1e27428e38c54ba7a0d1bdcfbd9d5cef8db06ad97712032e":
        ("topological_test_11","update","ccacd1a116c22e55969394cde358ce4e831c1f26e9e78b87d72a5b7fbda5c311",579,17),
    "a052ec0377c437f28f0a1b8be4dd4ce4f78bf877bde7e51d10eb2d72310230bd":
        ("topological_test_17","delete","987c24e896b8cdeb609d4e2d167c642f3f4e7fd7f1c1744be326c54b72888a53",440,17),
}
MAX_XML_BYTES=300000
STEP_RE=re.compile(r"^#([1-9][0-9]*)=([A-Z0-9_]+)\(.*\);$")
SAFE_SHA_RE=re.compile(r"^[a-f0-9]{64}$")


class NativeSourceReadOnly044Error(ValueError):
    pass


@dataclass(frozen=True)
class NativeSourceView044:
    xml:bytes
    task_id:str
    native_schema:str
    original_native_sha256:str
    entity_count:int
    read_only:bool=True


def require(ok:bool,message:str)->None:
    if not ok:
        raise NativeSourceReadOnly044Error(message)


def check_original_native_readonly_source(source:Path,sha:str,opened)->str:
    source=Path(source)
    require(source.is_file() and not source.is_symlink()
            and sha in PINS and file_hash(source)==sha,
            "v0.44 only exactly four original pinned IFC source SHA256 input files are admitted")
    require(opened.schema=="IFC4X3"
            and abs(ifcopenshell.util.unit.calculate_unit_scale(opened)-.001)<1e-12,
            "v0.44 requires original native IFC4X3 in millimetres")
    task,crud,question_sha,entities,products=PINS[sha]
    require(crud in ("update","delete") and SAFE_SHA_RE.fullmatch(question_sha),
            "v0.44 original task original public question hash/profile changed")
    require(len(list(opened))==entities
            and len(opened.by_type("IfcProduct"))==products,
            "v0.44 original IFC source entity/product inventory differs from pre-registered file")
    return task


def original_native_step_records(source:Path,model)->list[tuple[int,str,str]]:
    """Read literal native IFC DATA lines, not reserialized normalized-metre IFC."""
    raw=Path(source).read_bytes()
    require(len(raw)<100000 and b"\x00" not in raw,
            "v0.44 source STEP bytes invalid or unexpectedly large")
    try:
        text=raw.decode("utf8")
    except UnicodeDecodeError as exc:
        raise NativeSourceReadOnly044Error("Native STEP source is not UTF-8 encoded") from exc
    sections=text.splitlines()
    require(sections.count("DATA;")==1 and sections.count("ENDSEC;")==2,
            "Expected exactly one complete IFC STEP native DATA section")
    start=sections.index("DATA;")
    stop=sections.index("ENDSEC;",start+1)
    records=[]
    seen=set()
    for line in sections[start+1:stop]:
        require(line and line==line.strip(),
                "Only one literal original native STEP entity per unindented DATA line")
        match=STEP_RE.fullmatch(line)
        require(match is not None,"Unexpected native STEP record or multiline source entity")
        id_=int(match.group(1))
        klass=match.group(2)
        require(id_ not in seen,"Native source STEP entity ID was duplicated")
        seen.add(id_)
        native=model.by_id(id_)
        require(native is not None and native.is_a().upper()==klass,
                "Native source literal STEP ID or IFC class differs from IfcOpenShell")
        records.append((id_,klass,line))
    require(len(records)==len(list(model))
            and set(seen)=={x.id() for x in model},
            "Literal original DATA records must cover EVERY source IfcOpenShell entity exactly")
    return records


def _txt(v)->str:
    return str(v) if v is not None else ""


def _num(v)->str:
    v=round(float(v),6)
    if not -1000000<=v<=1000000:
        raise NativeSourceReadOnly044Error("Unbounded original native physical coordinate")
    return "0.000000" if v==0 else f"{v:.6f}"


def _entity_refs(v):
    if isinstance(v,ifcopenshell.entity_instance):
        yield v
    elif isinstance(v,(list,tuple)):
        for x in v:
            yield from _entity_refs(x)


def _original_world_mesh(product,settings):
    if product.Representation is None:
        return None
    try:
        shape=ifcopenshell.geom.create_shape(settings,product)
    except Exception as exc:
        return {"status":"SOURCE_NATIVE_GEOMETRY_UNAVAILABLE",
                "reason":type(exc).__name__}
    data=shape.geometry
    verts=list(data.verts)
    faces=list(data.faces)
    require(len(verts)>0 and len(verts)%3==0
            and len(faces)>0 and len(faces)%3==0,
            "Original physical source world tessellation malformed")
    points=[tuple(_num(verts[i+j]) for j in range(3))
            for i in range(0,len(verts),3)]
    tri=[tuple(int(faces[i+j]) for j in range(3))
         for i in range(0,len(faces),3)]
    require(all(min(t)>=0 and max(t)<len(points) for t in tri),
            "Original source triangle vertex index outside source native renderer mesh")
    raw=json.dumps({"vertices":points,"faces":tri},sort_keys=True,
                   separators=(",",":")).encode("utf8")
    bounds_min=[_num(min(float(v[i]) for v in points)) for i in range(3)]
    bounds_max=[_num(max(float(v[i]) for v in points)) for i in range(3)]
    return {"status":"ORIGINAL_SOURCE_NATIVE_WORLD_MESH_1UM",
            "vertices":points,"triangles":tri,
            "sha256":sha256(raw).hexdigest(),
            "mins":bounds_min,"maxs":bounds_max}


def project_native_readonly_source_v044(original_native:Path,
                                         *,original_native_sha256:str)->NativeSourceView044:
    original_native=Path(original_native)
    require(original_native.is_file() and not original_native.is_symlink()
            and file_hash(original_native)==original_native_sha256,
            "Original native source SHA not pinned before reading XML")
    model=ifcopenshell.open(str(original_native))
    task=check_original_native_readonly_source(
        original_native,original_native_sha256,model)
    records=original_native_step_records(original_native,model)
    require(len(records)==PINS[original_native_sha256][3],
            "Original exact native STEP entity population changed")
    root=etree.Element(Q+"Building",nsmap={None:NS},attrib={
        "version":"0.44",
        "sourceOriginalIFCSha256":original_native_sha256,
        "sourceIfcSchema":"IFC4X3",
        "sourceLengthUnit":"MILLIMETER_NATIVE",
        "sourceCompleteness":"ALL_ORIGINAL_NATIVE_STEP_DATA_ENTITIES_EXACT_WITH_DERIVED_READONLY_MESH",
        "nativeMutationPermission":"NONE_READ_ONLY",
    })
    native=etree.SubElement(root,Q+"OriginalNativeIFCSource",attrib={
        "readOnly":"true",
        "sourceOriginalIFCSha256":original_native_sha256,
        "nativeIfcSchema":"IFC4X3",
        "nativeEntityCount":str(len(records)),
        "nativeProductCount":str(len(model.by_type("IfcProduct"))),
        "nativeRelationCount":str(len(model.by_type("IfcRelationship"))),
        "sourceDataLinesAreComplete":"true",
        "nativeMutationPermission":"NONE_READ_ONLY",
    })
    products=etree.SubElement(native,Q+"Products")
    relations=etree.SubElement(native,Q+"Relations")
    properties=etree.SubElement(native,Q+"PropertySets")
    materials=etree.SubElement(native,Q+"Materials")
    placements=etree.SubElement(native,Q+"LocalPlacements")
    geometry=etree.SubElement(native,Q+"WorldGeometry")
    steps=etree.SubElement(native,Q+"NativeStepRecords")

    p=sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId)
    for item in p:
        attrs={
            "ifcGuid":item.GlobalId,
            "nativeIfcClass":item.is_a(),
            "sourceStepId":str(item.id()),
            "originalName":_txt(item.Name),
            "originalDescription":_txt(item.Description),
            "nativeMutationPermission":"NONE_READ_ONLY",
        }
        for source_attr,xml_attr in (
                ("ObjectPlacement","sourceObjectPlacementStepId"),
                ("Representation","sourceRepresentationStepId")):
            obj=getattr(item,source_attr,None)
            if obj is not None:
                attrs[xml_attr]=str(obj.id())
        if getattr(item,"ObjectType",None) is not None:
            attrs["originalObjectType"]=_txt(item.ObjectType)
        if getattr(item,"PredefinedType",None) is not None:
            attrs["originalPredefinedType"]=_txt(item.PredefinedType)
        etree.SubElement(products,Q+"Product",attrs)

    allrels=sorted(model.by_type("IfcRelationship"),key=lambda x:x.GlobalId)
    for r in allrels:
        rn=etree.SubElement(relations,Q+"Relation",{
            "ifcGuid":r.GlobalId,
            "nativeIfcClass":r.is_a(),
            "sourceStepId":str(r.id()),
            "originalName":_txt(r.Name),
            "nativeMutationPermission":"NONE_READ_ONLY",
        })
        # Expose original named IFC relationship endpoints; never infer
        # adjacency/touch or attach an invented source relationship.
        for i in range(len(r)):
            role=r.attribute_name(i)
            for v in _entity_refs(r[i]):
                attrs={
                    "attribute":role,
                    "sourceStepId":str(v.id()),
                    "nativeIfcClass":v.is_a(),
                }
                if v.is_a("IfcRoot"):
                    attrs["ifcGuid"]=v.GlobalId
                etree.SubElement(rn,Q+"NativeRef",attrs)

    allsets=sorted(model.by_type("IfcPropertySet"),key=lambda x:x.id())
    for pset in allsets:
        sn=etree.SubElement(properties,Q+"PropertySet",{
            "ifcGuid":pset.GlobalId,
            "sourceStepId":str(pset.id()),
            "originalName":_txt(pset.Name),
            "originalDescription":_txt(pset.Description),
        })
        for property_ in pset.HasProperties:
            attrs={
                "sourceStepId":str(property_.id()),
                "nativeIfcClass":property_.is_a(),
                "originalName":_txt(property_.Name),
            }
            if hasattr(property_,"NominalValue") and property_.NominalValue is not None:
                value=property_.NominalValue
                attrs["nominalIfcClass"]=value.is_a()
                attrs["sourceNominalValue"]=_txt(value.wrappedValue)
            etree.SubElement(sn,Q+"Property",attrs)

    for material in sorted(model.by_type("IfcMaterial"),key=lambda x:x.id()):
        attrs={
            "sourceStepId":str(material.id()),
            "originalName":_txt(material.Name),
            "originalDescription":_txt(material.Description),
        }
        if hasattr(material,"Category") and material.Category is not None:
            attrs["originalCategory"]=_txt(material.Category)
        etree.SubElement(materials,Q+"Material",attrs)

    for place in sorted(model.by_type("IfcLocalPlacement"),key=lambda x:x.id()):
        attrs={"sourceStepId":str(place.id()),
               "relativePlacementStepId":str(place.RelativePlacement.id())}
        if place.PlacementRelTo is not None:
            attrs["parentPlacementStepId"]=str(place.PlacementRelTo.id())
        matrix=ifcopenshell.util.placement.get_local_placement(place)
        for i in range(4):
            for j in range(4):
                attrs[f"m{i}{j}"]=_num(matrix[i][j])
        etree.SubElement(placements,Q+"LocalPlacement",attrs)

    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    for item in p:
        if item.Representation is None:
            continue
        mesh=_original_world_mesh(item,settings)
        require(mesh is not None,"Native representation was unexpectedly null")
        attrs={
            "ifcGuid":item.GlobalId,
            "nativeIfcClass":item.is_a(),
            "sourceRepresentationStepId":str(item.Representation.id()),
            "meshStatus":mesh["status"],
        }
        if mesh["status"]!="ORIGINAL_SOURCE_NATIVE_WORLD_MESH_1UM":
            attrs["errorType"]=mesh["reason"]
            etree.SubElement(geometry,Q+"ProductGeometry",attrs)
            continue
        attrs["worldMeshSha256"]=mesh["sha256"]
        attrs["worldVertexCount"]=str(len(mesh["vertices"]))
        attrs["worldTriangleCount"]=str(len(mesh["triangles"]))
        for field,value in zip(
                ("minX","minY","minZ","maxX","maxY","maxZ"),
                (*mesh["mins"],*mesh["maxs"])):
            attrs[field]=value
        g=etree.SubElement(geometry,Q+"ProductGeometry",attrs)
        v=etree.SubElement(g,Q+"WorldVertices")
        for index,point in enumerate(mesh["vertices"]):
            etree.SubElement(v,Q+"V",{
                "index":str(index),"x":point[0],"y":point[1],"z":point[2]})
        f=etree.SubElement(g,Q+"WorldTriangles")
        for a,b,c in mesh["triangles"]:
            etree.SubElement(f,Q+"T",{
                "a":str(a),"b":str(b),"c":str(c)})

    for step_id,step_class,literal_line in records:
        node=etree.SubElement(steps,Q+"StepEntity",{
            "sourceStepId":str(step_id),"nativeIfcClass":step_class})
        node.text=literal_line

    data=etree.tostring(root,encoding="utf8",xml_declaration=True,
                        pretty_print=False)
    require(len(data)<=MAX_XML_BYTES,
            "Complete model-readable original native source XML exceeds safe size")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    parsed=etree.fromstring(data,parser)
    require(etree.XMLSchema(etree.parse(str(XSD))).validate(parsed),
            "Original v0.44 native STEP read-only XML violates research XSD")
    require(file_hash(original_native)==original_native_sha256,
            "Original native source unexpectedly mutated by metadata/geometry projection")
    return NativeSourceView044(
        data,task,model.schema,original_native_sha256,len(records))


def verify_original_v044_xml_exactly_readonly(
        original_native:Path,proposed_xml:bytes,
        *,original_native_sha256:str)->None:
    """Host defense: verifies exact whole source; never authorizes a writer."""
    from src.security.agent_boundary import check_xml_bytes
    check_xml_bytes(proposed_xml)
    expected=project_native_readonly_source_v044(
        original_native,original_native_sha256=original_native_sha256)
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    x=etree.fromstring(proposed_xml,parser)
    e=etree.fromstring(expected.xml,parser)
    require(etree.tostring(x,method="c14n")==etree.tostring(e,method="c14n"),
            "Original v0.44 source-step/metadata/native mesh XML was edited or forged")
