"""v0.42 ORIGINAL-public P3 source-native-mm Slab READ-ONLY XML evidence.

Source material and triangle indices come directly from the SHA-pinned native
millimetre IFC, not the independently normalized metre workbench that may
retriangulate shapes. The read-only section never converts into editable
Slab objects. The trusted one-object writer remains v0.41 outside the LLM.
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

from src.runtime.experimental_v41_p3_column_slab import (
    check_p3_original_source,project_p3_source,compile_p3_create,file_hash)
from src.runtime.xml_parser import parse_xml
from src.security.agent_boundary import check_xml_bytes

NS="urn:bim-markup-bench:toy:v0"
Q="{"+NS+"}"
XSD=(Path(__file__).resolve().parents[2]/
     "spec"/"toy_markup_original_native_slab_evidence_v042.xsd")
PINS={
    "8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72":
      ("topological_test_02",{
        "3_DHXxtdb3wRKlXgyMiHCa":
          ("1ZGO8hrFCHqw0v0026FpFv","1ZGO8hrFCHqw0v0066FpFv"),
        "3_DHXxtdb3wRKlXgyMiHD0":
          ("2JF4e6axWHqu3u0C1FZlmi","2JF4e6axWHqu3u0C5FZlmi"),
      }),
    "29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5":
      ("topological_test_04",{
        "3_DHXxtdb3wRKlXgyMiHCa":
          ("1ZGO8hrFCHqw0v0026FpFv","1ZGO8hrFCHqw0v0066FpFv"),
      }),
}


class OriginalSlabEvidence042Error(ValueError):
    pass


@dataclass(frozen=True)
class OriginalSlab042View:
    xml:bytes
    source_sha256:str
    original_native_sha256:str
    native_schema:str
    task_id:str
    native_slab_guids:tuple[str,...]


@dataclass(frozen=True)
class OriginalSlab042Compile:
    task_id:str
    kind:str
    native_guid:str

    def as_dict(self)->dict:
        return {
            "status":"COMMITTED_V042_ORIGINAL_NATIVE_SLAB_READONLY_XML_AND_REAL_P3_NATIVE_WRITER",
            "original_native_slab_readonly_evidence_verified":True,
            "source_native_geometry_authority":"original_mm_IFC_exact_indices",
            "actual_original_task_answer_proven":False,
            "model_can_edit_existing_source_Slabs":False,
        }


def require(ok:bool,message:str)->None:
    if not ok:raise OriginalSlabEvidence042Error(message)


def check_original_slab_source(original_mm:Path,expected_sha:str,opened)->str:
    require(expected_sha in PINS,"v0.42 only admits two original topological IFC source SHA pins")
    try:
        task=check_p3_original_source(original_mm,expected_sha,opened)
    except Exception as exc:
        raise OriginalSlabEvidence042Error("v0.42 immutable original source P3 preflight failed") from exc
    require(task==PINS[expected_sha][0],
            "v0.42 pinned original public P3 source task changed")
    source_slabs={x.GlobalId for x in opened.by_type("IfcSlab")}
    require(source_slabs==set(PINS[expected_sha][1]),
            "v0.42 expected original existing Slab GlobalId source set changed")
    return task


def _num(x:float)->str:
    n=float(x)
    require(math.isfinite(n) and abs(n)<100000000,
            "Original native-mm Slab mesh coordinate not finite/bounded")
    value=f"{n:.6f}".rstrip("0").rstrip(".")
    return "0" if value in ("","-0") else value


def _original_world_mesh(slab):
    require(slab.is_a()=="IfcSlab" and slab.Representation is not None,
            "Expected original physical IfcSlab with native geometry")
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,slab)
        raw=list(shape.geometry.verts)
        faces=list(shape.geometry.faces)
    except Exception as exc:
        raise OriginalSlabEvidence042Error(
            "Original native-mm physical IfcSlab rendering failed") from exc
    require(len(raw)%3==0 and len(faces)%3==0
            and 8<=len(raw)//3<=100 and 12<=len(faces)//3<=200,
            "Native Slab source world mesh vertices/triangles out of safe bounds")
    vertices=[tuple(_num(raw[i+j]) for j in range(3))
              for i in range(0,len(raw),3)]
    triangles=[tuple(int(faces[i+j]) for j in range(3))
               for i in range(0,len(faces),3)]
    require(all(min(t)>=0 and max(t)<len(vertices) and len(set(t))==3
                for t in triangles),
            "Native Slab source indexed triangles invalid")
    digest=sha256(repr((vertices,triangles)).encode("ascii")).hexdigest()
    lo=[_num(min(float(v[j]) for v in vertices)) for j in range(3)]
    hi=[_num(max(float(v[j]) for v in vertices)) for j in range(3)]
    require(all(float(hi[j])-float(lo[j])>=.1 for j in range(3)),
            "Original Slab physical bbox degenerate")
    return vertices,triangles,digest,lo,hi


def _original_slab_containment(model,slab,expected_storey,expected_rel):
    containers=[
        r for r in model.by_type("IfcRelContainedInSpatialStructure")
        if slab in r.RelatedElements
    ]
    require(len(containers)==1,"Original Slab not uniquely contained in source IFC")
    relation=containers[0]
    require(relation.is_a()=="IfcRelContainedInSpatialStructure"
            and relation.GlobalId==expected_rel
            and relation.RelatingStructure.GlobalId==expected_storey
            and relation.RelatingStructure.is_a()=="IfcBuildingStorey",
            "Original Slab actual source containment relationship GUID drift")
    require(ifcopenshell.util.element.get_container(slab) is not None
            and ifcopenshell.util.element.get_container(slab).GlobalId==expected_storey
            and ifcopenshell.util.element.get_aggregate(slab) is None,
            "Original Slab native Storey containment vs aggregate unexpectedly changed")
    return relation


def _schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD)))


def _parse(xml:bytes)->etree._Element:
    if not isinstance(xml,bytes) or not 0<len(xml)<=300000:
        raise OriginalSlabEvidence042Error("v0.42 complete XML payload invalid size/type")
    try:
        check_xml_bytes(xml)
    except Exception as exc:
        raise OriginalSlabEvidence042Error("v0.42 complete XML rejected by original XML security boundary") from exc
    parser=etree.XMLParser(
        resolve_entities=False,load_dtd=False,no_network=True,
        huge_tree=False,remove_comments=False)
    try:
        doc=etree.fromstring(xml,parser)
    except (etree.XMLSyntaxError,ValueError) as exc:
        raise OriginalSlabEvidence042Error("Malformed v0.42 full declarative source XML") from exc
    require(not any(isinstance(x,(etree._Comment,etree._ProcessingInstruction))
                    for x in doc.iter()),
            "v0.42 comment/PI markup forbidden inside read-only source catalog")
    require(doc.tag==Q+"Building" and _schema().validate(doc),
            "Full declarative XML violates dedicated v0.42 source-Slab XSD")
    return doc


def project_original_slab_v042(
        normalized_m:Path,*,original_native_sha256:str,
        original_source_mm:Path)->OriginalSlab042View:
    normalized_m,original_source_mm=Path(normalized_m),Path(original_source_mm)
    require(normalized_m.is_file() and not normalized_m.is_symlink()
            and original_source_mm.is_file() and not original_source_mm.is_symlink()
            and original_native_sha256 in PINS
            and file_hash(original_source_mm)==original_native_sha256,
            "v0.42 original native-mm/normalized sources not exact real pinned files")
    f=ifcopenshell.open(str(original_source_mm))
    task=check_original_slab_source(original_source_mm,original_native_sha256,f)
    base=project_p3_source(
        normalized_m,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    require(base.task_id==task and base.native_schema=="IFC4X3"
            and base.existing_native_slabs_not_model_visible==
                len(PINS[original_native_sha256][1]),
            "v0.42 original P3 complete typed source projection changed")
    root=etree.fromstring(base.xml)
    require(root.tag==Q+"Building"
            and len(root)==3
            and [r.tag for r in root]==
                [Q+"Levels",Q+"Elements",Q+"Relations"],
            "v0.42 original P3 default typed XML root layout changed")
    source_slabs=sorted(f.by_type("IfcSlab"),key=lambda x:x.GlobalId)
    require(len(source_slabs)==len(PINS[original_native_sha256][1]),
            "Original source Slab count wrong")
    current_guids={x.get("ifcGuid") for x in root.find(Q+"Elements")}
    require(not set(PINS[original_native_sha256][1]) & current_guids,
            "Existing Slabs already editable/projected: new source-only evidence not warranted")

    evidence=etree.SubElement(root,Q+"OriginalNativeSlabEvidence",{
        "evidenceVersion":"0.42",
        "sourceModelSha256":base.source_sha256,
        "originalIFCSha256":original_native_sha256,
        "sourceIfcSchema":"IFC4X3",
        "compilerEditPermission":"NONE_READ_ONLY",
        "sourceStateCompleteness":"PARTIAL_ORIGINAL_SLAB_REFERENCE_NOT_LOSSLESS_IFC",
        "originalExplicitSpaceBoundaryCount":str(len(f.by_type("IfcRelSpaceBoundary"))),
    })
    require(len(f.by_type("IfcRelSpaceBoundary"))==0,
            "Original source acquired unregistered explicit space boundaries")
    slabs=etree.SubElement(evidence,Q+"NativeSlabs")
    relations=etree.SubElement(evidence,Q+"OriginalExplicitSlabRelations")
    names=[]
    for slab in source_slabs:
        require(slab.PredefinedType=="FLOOR",
                "Original native Slab source unexpectedly changed FLO0R class")
        storey,relationship=PINS[original_native_sha256][1][slab.GlobalId]
        rel=_original_slab_containment(f,slab,storey,relationship)
        verts,tris,digest,lo,hi=_original_world_mesh(slab)
        node=etree.SubElement(slabs,Q+"NativeSlab",{
            "ifcGuid":slab.GlobalId,
            "nativeIfcClass":"IfcSlab",
            "originalName":str(slab.Name or ""),
            "originalObjectType":str(slab.ObjectType or ""),
            "originalPredefinedType":"FLOOR",
            "sourceContainedStoreyGuid":storey,
            "sourceContainmentRelationGuid":rel.GlobalId,
            "worldMeshSha256":digest,
            "worldMinX":lo[0],"worldMinY":lo[1],"worldMinZ":lo[2],
            "worldMaxX":hi[0],"worldMaxY":hi[1],"worldMaxZ":hi[2],
            "compilerEditPermission":"NONE_READ_ONLY",
        })
        vertices=etree.SubElement(node,Q+"WorldVertices")
        for i,point in enumerate(verts):
            etree.SubElement(vertices,Q+"Vertex",{
                "index":str(i),"x":point[0],"y":point[1],"z":point[2]})
        triangles=etree.SubElement(node,Q+"WorldTriangles")
        for a,b,c in tris:
            etree.SubElement(triangles,Q+"Triangle",{
                "a":str(a),"b":str(b),"c":str(c)})
        etree.SubElement(relations,Q+"Relation",{
            "ifcClass":"IfcRelContainedInSpatialStructure",
            "relationGuid":rel.GlobalId,
            "originalRelatingGuid":storey,
            "originalRelatedGuid":slab.GlobalId,
            "origin":"EXPLICIT_SOURCE_IFC_ONLY",
        })
        names.append(slab.GlobalId)
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=False)
    _parse(xml)
    require(file_hash(original_source_mm)==original_native_sha256
            and file_hash(normalized_m)==base.source_sha256,
            "v0.42 original native-mm/normalized source changed during physical read")
    return OriginalSlab042View(
        xml,base.source_sha256,original_native_sha256,
        f.schema,task,tuple(names))


def strip_verified_original_slab_evidence(
        source_m:Path,submitted_xml:bytes,*,original_native_sha256:str,
        original_source_mm:Path)->bytes:
    baseline=project_original_slab_v042(
        source_m,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    submitted=_parse(submitted_xml)
    original=_parse(baseline.xml)
    require(dict(submitted.attrib)==dict(original.attrib),
            "Original full source XML root/schema/unit SHA changed")
    require(len(submitted)==4
            and [x.tag for x in submitted]==[
                Q+"Levels",Q+"Elements",Q+"Relations",
                Q+"OriginalNativeSlabEvidence"],
            "Immutable original native Slab read-only section missing/reordered")
    reference=submitted[-1]
    expected=original[-1]
    require(etree.tostring(reference,method="c14n")==
            etree.tostring(expected,method="c14n"),
            "Original source Slab world-mesh/index/GUID/name/relations/read-only catalog tampered")
    submitted.remove(reference)
    body=etree.tostring(submitted,encoding="utf8",xml_declaration=True)
    parse_xml(body,expected_source_sha256=baseline.source_sha256)
    return body


def compile_original_slab_v042(
        source_m:Path,edited_xml:bytes,destination_m:Path,*,
        original_native_sha256:str,original_source_mm:Path)->OriginalSlab042Compile:
    body=strip_verified_original_slab_evidence(
        source_m,edited_xml,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    native=compile_p3_create(
        source_m,body,destination_m,
        original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    require(Path(destination_m).is_file()
            and file_hash(original_source_mm)==original_native_sha256,
            "Native v0.41 original P3 single-object writer or unchanged source not verified")
    return OriginalSlab042Compile(native.task_id,native.kind,native.new_native_guid)
