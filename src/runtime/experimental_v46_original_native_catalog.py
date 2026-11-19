"""v0.46 source-locked original27 IFC facts: paginated *read-only* native XML.

A source-preserving research alternative to 390KB+ monolithic STEP in a
single 300KB model-tool message. Offers exact original source IFC4X3/IFC2X3/
IFC4/mm ROOT, Product, Relationship, PropertySet, Material, LocalPlacement,
physical world shape digests, and full exact native STEP DATA lines *on demand*.

It is NOT an original-task native mutator, complete Python API parity,
an author solution or a model-scored benchmark. Original four v0.44/v0.45
sources are excluded; original public 45/31 input population unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash
from src.runtime.experimental_v44_original_native_step_readonly import PINS as FOUR_SOURCE_PINS

HERE=Path(__file__).resolve()
ROOT=HERE.parents[2]
PREVIOUS_REPORT=ROOT/"reports"/"bibimbap_v043_original45_native_XML_source_read_parity_20261117.json"
PREVIOUS_SHA="eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf"
SCHEMA_XSD=ROOT/"spec"/"original_native_catalog_readonly_v046.xsd"
NS="urn:bim-markup-bench:toy:v0"
Q="{"+NS+"}"
STEP_RE=re.compile(r"^#([1-9][0-9]*)=([A-Z0-9_]+)\(.*\);$")
CATALOGS=("roots","products","relationships","property_sets",
          "materials","placements","geometry","step")
PAGE_SIZE=16
MAX_TOOL_XML_BYTES=300000


class NativeCatalog046Error(ValueError):
    pass


def require(ok:bool,why:str)->None:
    if not ok:
        raise NativeCatalog046Error(why)


def source_profiles()->dict[str,dict[str,Any]]:
    """Actual frozen prior original-45 native source population; not mutable config."""
    require(file_hash(PREVIOUS_REPORT)==PREVIOUS_SHA,
            "Frozen original v0.43 native IFC/source-45 audit changed")
    report=json.loads(PREVIOUS_REPORT.read_text(encoding="utf8"))
    require(report["original_public_ITT_task_count"]==45
            and report["original_source_IFC_unique_sha256_count"]==31,
            "Frozen original 45/31 public task source population changed")
    out={}
    for row in report["original_31_unique_native_source_rows"]:
        sha=row["native_original_ifc_file_sha256"]
        if sha in FOUR_SOURCE_PINS:
            continue
        variants=row["actual_model_facing_source_variants"]
        require(any(x["status"]=="ACTUAL_MODEL_TOOL_XML_READ_OK"
                    for x in variants.values()),
                "Original27 source not previously verified readable")
        out[sha]={
            "schema":row["schema"],
            "nativeProducts":row["native_ifc_products_count"],
            "nativeRelations":row["native_ifc_relationship_count"],
            "nativePropertySets":row["native_ifc_ifc_property_set_count"],
            "nativeMaterials":row["native_ifc_material_count"],
            "nativePlacements":row["native_ifc_local_placement_count"],
        }
    require(len(out)==27
            and not set(out).intersection(FOUR_SOURCE_PINS)
            and set(row["native_original_ifc_file_sha256"]
                    for row in report["original_31_unique_native_source_rows"])==
                set(out)|set(FOUR_SOURCE_PINS),
            "Original27 SHA-pinned distinct source coverage changed")
    return out


def _check_source(source:Path,sha:str):
    profiles=source_profiles()
    source=Path(source)
    require(source.is_file() and not source.is_symlink()
            and sha in profiles and file_hash(source)==sha,
            "Only original publicly pinned 27 native IFC source bytes are admitted")
    model=ifcopenshell.open(str(source))
    profile=profiles[sha]
    require(model.schema==profile["schema"]
            and abs(ifcopenshell.util.unit.calculate_unit_scale(model)-.001)<1e-12
            and len(model.by_type("IfcProduct"))==profile["nativeProducts"]
            and len(model.by_type("IfcRelationship"))==profile["nativeRelations"]
            and len(model.by_type("IfcPropertySet"))==profile["nativePropertySets"]
            and len(model.by_type("IfcMaterial"))==profile["nativeMaterials"]
            and len(model.by_type("IfcLocalPlacement"))==profile["nativePlacements"],
            "Original27 native IFC schema/mm or physical metadata population drift")
    return model


def _txt(value:Any)->str:
    return "" if value is None else str(value)


def _num(value:Any)->str:
    num=round(float(value),6)
    require(math.isfinite(num) and abs(num)<1e9,
            "Original IFC coordinate out of bounded native research catalog")
    return "0.000000" if num==0 else f"{num:.6f}"


def _entity_refs(value):
    if isinstance(value,ifcopenshell.entity_instance):
        yield value
    elif isinstance(value,(list,tuple)):
        for x in value:
            yield from _entity_refs(x)


def _entries_from_step(source:Path,model)->list[dict]:
    raw=source.read_bytes()
    require(raw and b"\0" not in raw and len(raw)<1000000,
            "Original native STEP invalid bytes or unexpectedly large")
    lines=raw.decode("utf8").splitlines()
    require(lines.count("DATA;")==1 and lines.count("ENDSEC;")==2,
            "Original native IFC STEP source must have one literal complete DATA section")
    begin=lines.index("DATA;")
    end=lines.index("ENDSEC;",begin+1)
    result=[]
    for line in lines[begin+1:end]:
        match=STEP_RE.fullmatch(line)
        require(match is not None,"Original STEP DATA entity is not a literal single-line record")
        number=int(match.group(1))
        obj=model.by_id(number)
        require(obj is not None and obj.is_a().upper()==match.group(2),
                "Original native STEP entity id/class mismatch source")
        result.append(_entry(obj,{"literalSha256":sha256(line.encode("utf8")).hexdigest()},text=line))
    require(len(result)==len(list(model))
            and len({r["attrs"]["sourceStepId"] for r in result})==len(result),
            "Original native STEP DATA index must cover every unique source entity exactly")
    return result


def _entry(obj,extra:dict|None=None,fields:list[tuple[str,str]]|None=None,
           refs:list[dict]|None=None,text:str|None=None)->dict:
    attrs={"sourceStepId":str(obj.id()),"nativeIfcClass":obj.is_a()}
    if obj.is_a("IfcRoot"):
        attrs["ifcGuid"]=obj.GlobalId
        attrs["originalName"]=_txt(obj.Name)
        attrs["originalDescription"]=_txt(obj.Description)
    if extra:
        attrs.update(extra)
    return {"attrs":attrs,"fields":fields or [],"refs":refs or [],
            "text":text}


def _shape_info(product,settings)->dict:
    if product.Representation is None:
        return {"meshStatus":"NO_ORIGINAL_REPRESENTATION"}
    try:
        owner=ifcopenshell.geom.create_shape(settings,product)
    except Exception as exc:
        return {"meshStatus":"UNAVAILABLE_NATIVE_GEOMETRY",
                "unavailableClass":type(exc).__name__}
    geom=owner.geometry
    vs=list(geom.verts)
    fs=list(geom.faces)
    require(vs and fs and len(vs)%3==0 and len(fs)%3==0
            and all(0<=x<len(vs)//3 for x in fs),
            "Native source world tessellation returned malformed faces")
    point_list=[tuple(_num(vs[i+j]) for j in range(3))
                for i in range(0,len(vs),3)]
    triangles=[tuple(int(fs[i+j]) for j in range(3))
               for i in range(0,len(fs),3)]
    raw=json.dumps({"vertices":point_list,"faces":triangles},
                   sort_keys=True,separators=(",",":")).encode("utf8")
    return {
        "meshStatus":"REAL_SOURCE_NATIVE_WORLD_MESH_1UM",
        "worldVertexCount":str(len(point_list)),
        "worldTriangleCount":str(len(triangles)),
        "worldMeshSHA256":sha256(raw).hexdigest(),
        "bboxMinX":_num(min(float(v[0]) for v in point_list)),
        "bboxMinY":_num(min(float(v[1]) for v in point_list)),
        "bboxMinZ":_num(min(float(v[2]) for v in point_list)),
        "bboxMaxX":_num(max(float(v[0]) for v in point_list)),
        "bboxMaxY":_num(max(float(v[1]) for v in point_list)),
        "bboxMaxZ":_num(max(float(v[2]) for v in point_list)),
    }


def build_original_source_catalog(source:Path,*,sha:str):
    """One true immutable native source import. Can be paginated without rerender."""
    source=Path(source)
    model=_check_source(source,sha)
    catalog={}
    roots=sorted(model.by_type("IfcRoot"),key=lambda x:x.GlobalId)
    catalog["roots"]=[_entry(x) for x in roots]
    catalog["products"]=[
        _entry(x,fields=[
            ("originalObjectType",_txt(getattr(x,"ObjectType",None))),
            ("originalPredefinedType",_txt(getattr(x,"PredefinedType",None))),
            ("placementStepId",str(x.ObjectPlacement.id()) if x.ObjectPlacement else ""),
            ("representationStepId",str(x.Representation.id()) if x.Representation else ""),
        ]) for x in sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId)
    ]
    relations=[]
    for r in sorted(model.by_type("IfcRelationship"),key=lambda x:x.GlobalId):
        refs=[]
        for i in range(len(r)):
            role=r.attribute_name(i)
            for obj in _entity_refs(r[i]):
                row={"role":role,"sourceStepId":str(obj.id()),
                     "nativeIfcClass":obj.is_a()}
                if obj.is_a("IfcRoot"):
                    row["ifcGuid"]=obj.GlobalId
                refs.append(row)
        relations.append(_entry(r,refs=refs))
    catalog["relationships"]=relations
    ps=[]
    for x in sorted(model.by_type("IfcPropertySet"),key=lambda x:x.id()):
        fields=[]
        for prop in x.HasProperties:
            fields.append(("property",json.dumps({
                "sourceStepId":prop.id(),"nativeIfcClass":prop.is_a(),
                "originalName":_txt(prop.Name),
                "nominalValueClass":prop.NominalValue.is_a()
                    if hasattr(prop,"NominalValue") and prop.NominalValue is not None else "",
                "originalNominalValue":_txt(prop.NominalValue.wrappedValue)
                    if hasattr(prop,"NominalValue") and prop.NominalValue is not None else "",
            },sort_keys=True,separators=(",",":"))))
        ps.append(_entry(x,fields=fields))
    catalog["property_sets"]=ps
    catalog["materials"]=[
        _entry(x,extra={"originalName":_txt(x.Name),
                        "originalDescription":_txt(getattr(x,"Description",None))},
               fields=[("category",_txt(getattr(x,"Category",None)))])
        for x in sorted(model.by_type("IfcMaterial"),key=lambda x:x.id())
    ]
    placements=[]
    for p in sorted(model.by_type("IfcLocalPlacement"),key=lambda x:x.id()):
        mat=ifcopenshell.util.placement.get_local_placement(p)
        fields=[(f"m{i}{j}",_num(mat[i,j])) for i in range(4) for j in range(4)]
        fields.extend([
            ("parentPlacementStepId",str(p.PlacementRelTo.id()) if p.PlacementRelTo else ""),
            ("relativePlacementStepId",str(p.RelativePlacement.id())),
        ])
        placements.append(_entry(p,fields=fields))
    catalog["placements"]=placements
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    catalog["geometry"]=[
        _entry(p,extra=_shape_info(p,settings),
               fields=[("sourceRepresentationStepId",
                        str(p.Representation.id()) if p.Representation else "")])
        for p in sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId)
    ]
    catalog["step"]=_entries_from_step(source,model)
    require(set(catalog)==set(CATALOGS)
            and len(catalog["roots"])==len(model.by_type("IfcRoot"))
            and len(catalog["products"])==len(model.by_type("IfcProduct"))
            and len(catalog["relationships"])==len(model.by_type("IfcRelationship"))
            and len(catalog["property_sets"])==len(model.by_type("IfcPropertySet"))
            and len(catalog["materials"])==len(model.by_type("IfcMaterial"))
            and len(catalog["placements"])==len(model.by_type("IfcLocalPlacement")),
            "Original IFC model-visible source catalog entities incomplete")
    require(file_hash(source)==sha,
            "Original native source modified during read-only source catalog")
    return NativeCatalog046(sha,model.schema,catalog)


def _render_record(node,rec:dict):
    attrs=rec["attrs"]
    etree.SubElement(node,Q+"Entry",attrs)
    item=node[-1]
    for key,value in rec["fields"]:
        etree.SubElement(item,Q+"Field",{"name":key,"value":value})
    for ref in rec["refs"]:
        etree.SubElement(item,Q+"Ref",ref)
    if rec["text"] is not None:
        etree.SubElement(item,Q+"LiteralStepText").text=rec["text"]


def _schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(SCHEMA_XSD)))


@dataclass
class NativeCatalog046:
    source_sha:str
    schema:str
    catalog:dict[str,list[dict]]

    def _header(self,tag,extra:dict)->etree._Element:
        return etree.Element(Q+tag,nsmap={None:NS},attrib={
            "version":"0.46","sourceOriginalIFCSha256":self.source_sha,
            "sourceNativeIfcSchema":self.schema,"sourceNativeLengthUnit":"MILLIMETER",
            "sourceMode":"IMMUTABLE_ORIGINAL_IFC_INDEX_READ_ONLY",
            "nativeMutationPermission":"NONE_READ_ONLY",**extra,
        })

    def manifest(self)->bytes:
        root=self._header("Building",{})
        source=etree.SubElement(root,Q+"OriginalNativeSourceCatalog")
        for name in CATALOGS:
            rows=self.catalog[name]
            digest=sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False,
                        separators=(",",":")).encode("utf8")).hexdigest()
            etree.SubElement(source,Q+"Catalog",{
                "name":name,"recordCount":str(len(rows)),
                "pageSize":str(PAGE_SIZE),
                "pageCount":str((len(rows)+PAGE_SIZE-1)//PAGE_SIZE),
                "canonicalSourceRecordsSha256":digest,
            })
        return self._valid_bounded(root)

    def page(self,name:str,page:int)->bytes:
        require(name in CATALOGS and type(page) is int and 0<=page,
                "Unknown native source catalog or page out of range")
        total=len(self.catalog[name])
        pages=(total+PAGE_SIZE-1)//PAGE_SIZE
        require(page<pages,
                "Original IFC native catalog page not within source population")
        rows=self.catalog[name][page*PAGE_SIZE:(page+1)*PAGE_SIZE]
        root=self._header("OriginalNativeSourcePage",{
            "catalog":name,"page":str(page),"pageSize":str(PAGE_SIZE),
            "totalPages":str(pages),"totalRecords":str(total),
        })
        for row in rows:
            _render_record(root,row)
        return self._valid_bounded(root)

    def _valid_bounded(self,root)->bytes:
        data=etree.tostring(root,encoding="utf8",xml_declaration=True,
                            pretty_print=False)
        require(0<len(data)<=MAX_TOOL_XML_BYTES,
                "Native original XML page exceeds bounded model tool result")
        require(_schema().validate(root),
                "Native original source research catalog XSD invalid")
        return data
