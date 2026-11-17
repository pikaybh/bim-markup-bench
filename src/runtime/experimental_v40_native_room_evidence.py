"""v0.40 original-public P2: immutable native IfcSpace facts in whole-XML source.

Only exactly two SHA-pinned original IFC4X3-mm BIBIMBAP files. Source Spaces
stay as native IFC objects; their 3D mesh/real source relation facts are
visible but NOT editable rectangular Boxes. The old complete typed Wall XML
is still the only submitted source passed to the trusted native IFC compiler.

The public question says "room" even when two named GUIDs are true IfcWall.
Never silently reinterpret, rename or swap those GUIDs for IfcSpace IDs.
No IfcRelSpaceBoundary is invented: both original sources contain zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.ifc_projection import project_ifc
from src.runtime.compiler import compile_declarative_xml

NS="urn:bim-markup-bench:toy:v0"
Q="{"+NS+"}"
XSD=(Path(__file__).resolve().parents[2]/
     "spec"/"toy_markup_native_room_evidence_v040.xsd")
PINS={
    "2cb6cc753784c13fcd1f6f037b97431294cc3c91db9bcc75213ba61b8e3a18ac":
        ("topological_test_01",("3_DHXxtdb3wRKlXgyMiH4s",),1),
    "1035e999dd8579b7d2c33950498eea1f50bd9ff81e1816bdf4b9893901969466":
        ("topological_test_03",("0rMMWWDi1E0Qbe7dlPjRaK",
                                "0rMMWWDi1E0Qbe7dlPjRcx"),2),
}


class NativeRoomV040Error(ValueError):
    pass


@dataclass(frozen=True)
class NativeRoomView040:
    xml:bytes
    source_model_sha256:str
    original_native_sha256:str
    task_id:str
    source_ifc_schema:str
    spaces:tuple[str,...]
    named_classes:tuple[tuple[str,str],...]


@dataclass(frozen=True)
class NativeRoomCompile040:
    status:str
    task_id:str

    def as_dict(self)->dict:
        return {
            "status":self.status,
            "task_id":self.task_id,
            "original_native_IfcSpace_writes_permitted":False,
            "original_readonly_room_evidence_changed":False,
            "separate_original_IFC4X3_native_candidate":True,
        }


def file_hash(path:Path)->str:
    h=sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def check_original_native_room_input(path:Path,expected_sha:str,
                                     opened:ifcopenshell.file)->str:
    path=Path(path)
    if (not path.is_file() or path.is_symlink()
        or expected_sha not in PINS or file_hash(path)!=expected_sha):
        raise NativeRoomV040Error(
            "Only exact two pinned original public P2 IFC input SHA values allowed")
    if opened.schema!="IFC4X3":
        raise NativeRoomV040Error("P2 source IFC4X3 schema changed")
    unit=ifcopenshell.util.unit.calculate_unit_scale(opened)
    if not math.isfinite(unit) or abs(unit-.001)>1e-12:
        raise NativeRoomV040Error("P2 original native millimetre units required")
    return PINS[expected_sha][0]


def _num(x:float)->str:
    v=float(x)
    if not math.isfinite(v) or abs(v)>1e8:
        raise NativeRoomV040Error("Invalid real source IFC world coordinate")
    text=f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("","-0") else text


def _mesh(space)->tuple[list[tuple[str,str,str]],list[tuple[int,int,int]],str,
                         tuple[str,str,str],tuple[str,str,str]]:
    if space.Representation is None:
        raise NativeRoomV040Error("Original native IfcSpace has no physical representation")
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        generated=ifcopenshell.geom.create_shape(settings,space)
        raw=list(generated.geometry.verts)
        faces=list(generated.geometry.faces)
    except Exception as exc:
        raise NativeRoomV040Error("Original source IfcSpace physical mesh unavailable") from exc
    if len(raw)%3 or len(faces)%3:
        raise NativeRoomV040Error("Original IfcSpace mesh is malformed")
    vertices=[tuple(_num(raw[k+j]) for j in range(3))
              for k in range(0,len(raw),3)]
    triangles=[tuple(int(faces[k+j]) for j in range(3))
               for k in range(0,len(faces),3)]
    if not 8<=len(vertices)<=100 or not 12<=len(triangles)<=200:
        raise NativeRoomV040Error("Original IfcSpace native world triangle bounds invalid")
    if any(min(tri)<0 or max(tri)>=len(vertices) or len(set(tri))!=3
           for tri in triangles):
        raise NativeRoomV040Error("Original IfcSpace native triangle index invalid")
    digest=sha256(repr((vertices,triangles)).encode("ascii")).hexdigest()
    low=tuple(_num(min(float(v[j]) for v in vertices)) for j in range(3))
    high=tuple(_num(max(float(v[j]) for v in vertices)) for j in range(3))
    if any(float(high[j])-float(low[j])<.1 for j in range(3)):
        raise NativeRoomV040Error("Original IfcSpace physical world bounds degenerate")
    return vertices,triangles,digest,low,high


def _native_relations_for_spaces(f,spaceids:set[str]):
    result=[]
    for rel in f.by_type("IfcRelAggregates"):
        for obj in rel.RelatedObjects:
            if obj.GlobalId in spaceids:
                result.append((rel.is_a(),rel.GlobalId,
                    rel.RelatingObject.GlobalId,obj.GlobalId))
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        for obj in rel.RelatedElements:
            if obj.GlobalId in spaceids:
                result.append((rel.is_a(),rel.GlobalId,
                    rel.RelatingStructure.GlobalId,obj.GlobalId))
    for rel in f.by_type("IfcRelSpaceBoundary"):
        if rel.RelatingSpace.GlobalId in spaceids and rel.RelatedBuildingElement:
            result.append((rel.is_a(),rel.GlobalId,
                rel.RelatingSpace.GlobalId,rel.RelatedBuildingElement.GlobalId))
    if len(result)>100:
        raise NativeRoomV040Error("Original native Space relationship list too large")
    roots={x.GlobalId for x in f.by_type("IfcRoot")}
    if any(g not in roots or a not in roots or b not in roots
           for _,g,a,b in result):
        raise NativeRoomV040Error("Original native Space relation has unknown source Root")
    return sorted(set(result))


def _schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD)))


def _parse(xml:bytes)->etree._Element:
    if (not isinstance(xml,bytes) or not 0<len(xml)<=200000
        or b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper()):
        raise NativeRoomV040Error("P2 XML unsafe DTD, external entity or oversized document")
    parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,
        huge_tree=False,remove_comments=False)
    try:
        root=etree.fromstring(xml,parser)
    except etree.XMLSyntaxError as exc:
        raise NativeRoomV040Error("Malformed complete native-room declarative XML") from exc
    if any(isinstance(el,(etree._Comment,etree._ProcessingInstruction))
           for el in root.iter()):
        raise NativeRoomV040Error("P2 XML comments and processing instructions not allowed")
    if not _schema().validate(root):
        raise NativeRoomV040Error("Complete P2 XML violates pinned v0.40 room-evidence XSD")
    return root


def project_native_room_v040(normalized_m:Path,*,original_native_sha256:str,
                             original_source_mm:Path)->NativeRoomView040:
    """Project real source native Space data alongside unchanged v0.1 typed Wall state."""
    normalized_m=Path(normalized_m)
    if (not normalized_m.is_file() or normalized_m.is_symlink()
        or original_native_sha256 not in PINS):
        raise NativeRoomV040Error("Only pinned normalized P2 original source accepted")
    original_source_mm=Path(original_source_mm)
    if (not original_source_mm.is_file() or original_source_mm.is_symlink()
        or file_hash(original_source_mm)!=original_native_sha256):
        raise NativeRoomV040Error("P2 original source must be exact pinned native-mm IFC")
    source_original=ifcopenshell.open(str(original_source_mm))
    if (source_original.schema!="IFC4X3" or abs(
        ifcopenshell.util.unit.calculate_unit_scale(source_original)-.001)>1e-12):
        raise NativeRoomV040Error("P2 original source native-mm IFC4X3 units required")
    work=ifcopenshell.open(str(normalized_m))
    if (work.schema!="IFC4X3" or abs(
        ifcopenshell.util.unit.calculate_unit_scale(work)-1.)>1e-12):
        raise NativeRoomV040Error("P2 normalized source must be IFC4X3 metres")
    source_sha=file_hash(normalized_m)
    task,public_names,count=PINS[original_native_sha256]
    snapshot=project_ifc(normalized_m,strict_on_opaque=False)
    if snapshot.source.source_sha256!=source_sha:
        raise NativeRoomV040Error("P2 original source snapshot normalized SHA drift")
    root=etree.fromstring(snapshot.xml)
    if root.tag!=Q+"Building" or root.get("sourceModelSha256")!=source_sha:
        raise NativeRoomV040Error("P2 default typed XML source unavailable")
    if (len(root)!=3 or
        [x.tag for x in root] !=[Q+"Levels",Q+"Elements",Q+"Relations"]):
        raise NativeRoomV040Error("Default source typed Building schema changed")
    # Source mm body is authoritative for mesh triangle DIAGONALS and indices;
    # conversion to metre IFC can retessellate the same planar physical face.
    fspaces=sorted(source_original.by_type("IfcSpace"),key=lambda e:e.GlobalId)
    if (len(fspaces)!=count
        or {x.GlobalId for x in fspaces}!={x.GlobalId for x in work.by_type("IfcSpace")}
        or len(source_original.by_type("IfcRelSpaceBoundary"))!=0
        or len(work.by_type("IfcRelSpaceBoundary"))!=0):
        raise NativeRoomV040Error("Actual source Space count or explicit boundary assumption changed")
    product_guids={e.get("ifcGuid") for e in root.find(Q+"Elements")}
    if any(x.GlobalId in product_guids for x in fspaces):
        raise NativeRoomV040Error("Source IfcSpace unexpectedly typed/editable; opt-in must re-evaluate")
    native=etree.SubElement(root,Q+"OriginalNativeRoomEvidence",{
        "evidenceVersion":"0.40",
        "sourceModelSha256":source_sha,
        "originalIFCSha256":original_native_sha256,
        "sourceIfcSchema":"IFC4X3",
        "compilerEditPermission":"NONE_READ_ONLY",
        "sourceStateCompleteness":"PARTIAL_ORIGINAL_ROOM_REFERENCE_NOT_LOSSLESS_IFC",
        "originalExplicitSpaceBoundaryCount":"0",
    })
    spaces=etree.SubElement(native,Q+"NativeSpaces")
    ids=set()
    for space in fspaces:
        ids.add(space.GlobalId)
        agg=ifcopenshell.util.element.get_aggregate(space)
        if agg is None or not agg.is_a("IfcBuildingStorey"):
            raise NativeRoomV040Error("Original native IfcSpace has no explicit original aggregate Storey")
        if ifcopenshell.util.element.get_container(space) is not None:
            raise NativeRoomV040Error("Original Space unexpectedly separately contained")
        vertices,triangles,digest,low,high=_mesh(space)
        node=etree.SubElement(spaces,Q+"NativeSpace",{
            "ifcGuid":space.GlobalId,
            "nativeIfcClass":"IfcSpace",
            "originalName":str(space.Name or ""),
            "originalLongName":str(space.LongName or ""),
            "sourceAggregateStoreyGuid":agg.GlobalId,
            "originalSpaceBoundaryCount":str(len(space.BoundedBy)),
            "worldMeshSha256":digest,
            "worldMinX":low[0],"worldMinY":low[1],"worldMinZ":low[2],
            "worldMaxX":high[0],"worldMaxY":high[1],"worldMaxZ":high[2],
            "compilerEditPermission":"NONE_READ_ONLY",
        })
        pointroot=etree.SubElement(node,Q+"WorldVertices")
        for index,v in enumerate(vertices):
            etree.SubElement(pointroot,Q+"Vertex",{
                "index":str(index),"x":v[0],"y":v[1],"z":v[2]})
        faceroom=etree.SubElement(node,Q+"WorldTriangles")
        for a,b,c in triangles:
            etree.SubElement(faceroom,Q+"Triangle",{
                "a":str(a),"b":str(b),"c":str(c)})
    original_rels=_native_relations_for_spaces(source_original,ids)
    if len(original_rels)!=count:
        raise NativeRoomV040Error(
            "Original Space explicit aggregate-to-Storey relationship count drift")
    relations=etree.SubElement(native,Q+"OriginalExplicitSpaceRelations")
    for kind,guid,relating,related in original_rels:
        etree.SubElement(relations,Q+"Relation",{
            "ifcClass":kind,"relationGuid":guid,
            "originalRelatingGuid":relating,"originalRelatedGuid":related,
            "origin":"EXPLICIT_SOURCE_IFC_ONLY"})
    idsroot=etree.SubElement(native,Q+"PublicRoomIdentifiers")
    named=[]
    for guid in public_names:
        entity=source_original.by_guid(guid)
        if entity is None or not entity.is_a() in ("IfcWall","IfcSpace"):
            raise NativeRoomV040Error("Published named Room GUID not real native Wall/Space")
        classname=entity.is_a()
        classification=("PUBLIC_ROOM_NOUN_NATIVE_SPACE_MATCH"
                        if classname=="IfcSpace"
                        else "PUBLIC_ROOM_NOUN_NATIVE_WALL_MISMATCH")
        etree.SubElement(idsroot,Q+"PublicRoomReference",{
            "publicGuid":guid,"publicNoun":"room",
            "actualNativeIfcClass":classname,"classification":classification,
            "remappingOrInferredRoomGuidAllowed":"false"})
        named.append((guid,classname))
    output=etree.tostring(root,encoding="utf8",xml_declaration=True,
                          pretty_print=False)
    _parse(output)
    if (file_hash(normalized_m)!=source_sha
        or file_hash(original_source_mm)!=original_native_sha256):
        raise NativeRoomV040Error("Original native-mm or normalized IFC changed during Room projection")
    return NativeRoomView040(
        output,source_sha,original_native_sha256,task,source_original.schema,
        tuple(x.GlobalId for x in fspaces),tuple(named))


def strip_and_validate_room_evidence(
        source_m:Path,edited_xml:bytes,*,original_native_sha256:str,
        original_source_mm:Path)->bytes:
    """Remove ONLY verified immutable reference evidence; keep complete typed XML."""
    baseline=project_native_room_v040(
        source_m,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    submitted=_parse(edited_xml)
    original=_parse(baseline.xml)
    if dict(submitted.attrib)!=dict(original.attrib):
        raise NativeRoomV040Error("Original P2 full XML source/root SHA or schema changed")
    if len(submitted)!=4 or submitted[-1].tag!=Q+"OriginalNativeRoomEvidence":
        raise NativeRoomV040Error("Source Room catalog must remain the final native read-only section")
    submitted_ref=submitted.find(Q+"OriginalNativeRoomEvidence")
    original_ref=original.find(Q+"OriginalNativeRoomEvidence")
    if (submitted_ref is None or original_ref is None
        or etree.tostring(submitted_ref,method="c14n")!=
           etree.tostring(original_ref,method="c14n")):
        raise NativeRoomV040Error("Immutable native source Room mesh/relations/GUID evidence altered")
    submitted.remove(submitted_ref)
    body=etree.tostring(submitted,encoding="utf8",xml_declaration=True)
    # The old default v0.1 reader and binder remain the single compiler path,
    # so an invented typed Space/Room or any other unauthorized edit is refused.
    from src.runtime.xml_parser import parse_xml
    parse_xml(body,expected_source_sha256=baseline.source_model_sha256)
    return body


def compile_native_room_v040(
        source_m:Path,edited_xml:bytes,destination_m:Path,
        *,original_native_sha256:str,
        original_source_mm:Path)->NativeRoomCompile040:
    source_m,destination_m=Path(source_m),Path(destination_m)
    if not source_m.is_file() or destination_m.exists() or source_m.resolve()==destination_m.resolve():
        raise NativeRoomV040Error("P2 native source/candidate output paths not independent")
    body=strip_and_validate_room_evidence(
        source_m,edited_xml,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    report=compile_declarative_xml(source_m,body,destination_m)
    if (not destination_m.is_file()
        or file_hash(source_m)!=etree.fromstring(
            body).get("sourceModelSha256")):
        raise NativeRoomV040Error("Original native normalized source changed during compiler")
    return NativeRoomCompile040(
        "COMMITTED_ORIGINAL_IFC4X3_ROOM_NATIVE_REFERENCE_READONLY_V040",
        PINS[original_native_sha256][0])
