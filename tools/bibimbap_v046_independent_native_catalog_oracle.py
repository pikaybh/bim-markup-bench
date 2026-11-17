"""Independent original27 native IFC catalog/page oracle; NO v0.46 projector imports.

Directly reads original SOURCE IFC bytes with IfcOpenShell and original native
DATA text; independently validates every actual model-facing page and manifest
of original GUIDs, names, direct relationship endpoints, property-set values,
material values, placement, physical world meshes, and STEP text+SHA. No
author grader, task answers, model provider, compiler or native writer.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from lxml import etree

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
OLD=ROOT/"reports"/"bibimbap_v043_original45_native_XML_source_read_parity_20261117.json"
OLD_SHA="eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf"
Q="{urn:bim-markup-bench:toy:v0}"
CATALOGS=("roots","products","relationships","property_sets",
          "materials","placements","geometry","step")
STEP_RE=re.compile(r"^#([1-9][0-9]*)=([A-Z0-9_]+)\(.*\);$")
PAGE_SIZE=16


class IndependentOriginalCatalog046Error(ValueError):
    pass


def need(x,reason):
    if not x:raise IndependentOriginalCatalog046Error(reason)


def file_sha(path):
    stream=Path(path).open("rb")
    h=sha256()
    with stream:
        for b in iter(lambda:stream.read(65536),b""):
            h.update(b)
    return h.hexdigest()


def original_27_sources():
    need(file_sha(OLD)==OLD_SHA,"Frozen prior native original 45/31 audit tampered")
    r=json.loads(OLD.read_text(encoding="utf8"))
    need(r["original_public_ITT_task_count"]==45
         and r["original_source_IFC_unique_sha256_count"]==31,
         "Prior original45/31 population or denominator drift")
    blocked={"318fb45af8142c164c1fc53eeadc472008ff9c42e9c1b6398e9c95aa744374af",
             "67ac42ca988bdfd44a2afe3ebaff8be11da913b281338ec127f4897e3f42f6a3",
             "c85a8b90f1b2d22f1e27428e38c54ba7a0d1bdcfbd9d5cef8db06ad97712032e",
             "a052ec0377c437f28f0a1b8be4dd4ce4f78bf877bde7e51d10eb2d72310230bd"}
    all_rows={x["native_original_ifc_file_sha256"]:x
              for x in r["original_31_unique_native_source_rows"]}
    need(len(all_rows)==31 and blocked.issubset(all_rows),
         "v0.44 original four exclusions changed")
    out={sha:x for sha,x in all_rows.items() if sha not in blocked}
    need(len(out)==27,"v0.46 must independently validate exactly original27 unique sources")
    return out


def _fmt_num(x):
    f=round(float(x),6)
    need(math.isfinite(f) and abs(f)<1e9,"Invalid physical source number")
    return "0.000000" if f==0 else f"{f:.6f}"


def _text(x):return "" if x is None else str(x)


def _refs(x):
    if isinstance(x,ifcopenshell.entity_instance):
        yield x
    elif isinstance(x,(tuple,list)):
        for r in x:yield from _refs(r)


def _attr(x):
    ans={"sourceStepId":str(x.id()),"nativeIfcClass":x.is_a()}
    if x.is_a("IfcRoot"):
        ans.update({
            "ifcGuid":x.GlobalId,
            "originalName":_text(x.Name),
            "originalDescription":_text(x.Description),
        })
    return ans


def _world_shape(x,settings):
    if x.Representation is None:return {"meshStatus":"NO_ORIGINAL_REPRESENTATION"}
    try:
        owner=ifcopenshell.geom.create_shape(settings,x)
    except Exception as exc:
        return {"meshStatus":"UNAVAILABLE_NATIVE_GEOMETRY",
                "unavailableClass":type(exc).__name__}
    vertices=list(owner.geometry.verts)
    faces=list(owner.geometry.faces)
    need(vertices and faces and len(vertices)%3==0 and len(faces)%3==0,
         "Independent original IFCO physical mesh malformed")
    points=[tuple(_fmt_num(vertices[i+j]) for j in range(3))
            for i in range(0,len(vertices),3)]
    tris=[tuple(int(faces[i+j]) for j in range(3))
          for i in range(0,len(faces),3)]
    need(all(0<=min(t) and max(t)<len(points) for t in tris),
         "Original world physical face index invalid")
    digest=sha256(json.dumps({"vertices":points,"faces":tris},
             sort_keys=True,separators=(",",":")).encode("utf8")).hexdigest()
    bounds={
        "bboxMinX":_fmt_num(min(float(p[0]) for p in points)),
        "bboxMinY":_fmt_num(min(float(p[1]) for p in points)),
        "bboxMinZ":_fmt_num(min(float(p[2]) for p in points)),
        "bboxMaxX":_fmt_num(max(float(p[0]) for p in points)),
        "bboxMaxY":_fmt_num(max(float(p[1]) for p in points)),
        "bboxMaxZ":_fmt_num(max(float(p[2]) for p in points)),
    }
    return {"meshStatus":"REAL_SOURCE_NATIVE_WORLD_MESH_1UM",
            "worldVertexCount":str(len(points)),
            "worldTriangleCount":str(len(tris)),
            "worldMeshSHA256":digest,**bounds}


def _expected_catalog(source:Path,model)->dict:
    # Independent construction, NOT the v0.46 projector or builder.
    catalog={}
    def item(obj,attrs=None,fields=None,refs=None,original=None):
        return {"attrs":{**_attr(obj),**(attrs or {})},
                "fields":fields or [],
                "refs":refs or [],
                "text":original}
    catalog["roots"]=[item(x) for x in sorted(model.by_type("IfcRoot"),
                                               key=lambda x:x.GlobalId)]
    catalog["products"]=[]
    for p in sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        catalog["products"].append(item(p,fields=[
            ("originalObjectType",_text(getattr(p,"ObjectType",None))),
            ("originalPredefinedType",_text(getattr(p,"PredefinedType",None))),
            ("placementStepId",str(p.ObjectPlacement.id()) if p.ObjectPlacement else ""),
            ("representationStepId",str(p.Representation.id()) if p.Representation else ""),
        ]))
    catalog["relationships"]=[]
    for r in sorted(model.by_type("IfcRelationship"),key=lambda x:x.GlobalId):
        connected=[]
        for pos in range(len(r)):
            for ref in _refs(r[pos]):
                values={"role":r.attribute_name(pos),
                        "sourceStepId":str(ref.id()),
                        "nativeIfcClass":ref.is_a()}
                if ref.is_a("IfcRoot"):
                    values["ifcGuid"]=ref.GlobalId
                connected.append(values)
        catalog["relationships"].append(item(r,refs=connected))
    catalog["property_sets"]=[]
    for ps in sorted(model.by_type("IfcPropertySet"),key=lambda x:x.id()):
        fields=[]
        for prop in ps.HasProperties:
            val=prop.NominalValue if hasattr(prop,"NominalValue") else None
            fields.append(("property",json.dumps({
                "sourceStepId":prop.id(),"nativeIfcClass":prop.is_a(),
                "originalName":_text(prop.Name),
                "nominalValueClass":val.is_a() if val is not None else "",
                "originalNominalValue":_text(val.wrappedValue) if val is not None else "",
            },sort_keys=True,separators=(",",":"))))
        catalog["property_sets"].append(item(ps,fields=fields))
    catalog["materials"]=[]
    for m in sorted(model.by_type("IfcMaterial"),key=lambda x:x.id()):
        catalog["materials"].append(item(m,attrs={
            "originalName":_text(m.Name),
            "originalDescription":_text(getattr(m,"Description",None))},
            fields=[("category",_text(getattr(m,"Category",None)))]))
    catalog["placements"]=[]
    for place in sorted(model.by_type("IfcLocalPlacement"),key=lambda x:x.id()):
        matrix=ifcopenshell.util.placement.get_local_placement(place)
        fields=[(f"m{i}{j}",_fmt_num(matrix[i,j]))
                for i in range(4) for j in range(4)]
        fields+=[
            ("parentPlacementStepId",
             str(place.PlacementRelTo.id()) if place.PlacementRelTo else ""),
            ("relativePlacementStepId",str(place.RelativePlacement.id())),
        ]
        catalog["placements"].append(item(place,fields=fields))
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    catalog["geometry"]=[]
    for product in sorted(model.by_type("IfcProduct"),key=lambda x:x.GlobalId):
        catalog["geometry"].append(item(
            product,attrs=_world_shape(product,settings),
            fields=[("sourceRepresentationStepId",
                     str(product.Representation.id()) if product.Representation else "")]))
    # Direct original source STEP lines, no regenerated STEP/text or normalized m.
    lines=source.read_bytes().decode("utf8").splitlines()
    need(lines.count("DATA;")==1 and lines.count("ENDSEC;")==2,
         "Original public IFC STEP source DATA delimiters changed")
    begin=lines.index("DATA;")+1
    end=lines.index("ENDSEC;",begin)
    catalog["step"]=[]
    for literal in lines[begin:end]:
        matched=STEP_RE.fullmatch(literal)
        need(matched is not None,
             "Original public source STEP must be one entity on each literal line")
        ent=model.by_id(int(matched.group(1)))
        need(ent is not None and ent.is_a().upper()==matched.group(2),
             "Original native IFC STEP line class/stepID not in independent IFC")
        catalog["step"].append(item(ent,attrs={
            "literalSha256":sha256(literal.encode("utf8")).hexdigest()},
            original=literal))
    need(len(catalog["step"])==len(list(model))
         and len({r["attrs"]["sourceStepId"] for r in catalog["step"]})==
             len(catalog["step"]),
         "Original native STEP source coverage/repeated id mismatch")
    return catalog


def _parse(xml:bytes):
    need(isinstance(xml,bytes) and 0<len(xml)<=300000
         and b"<!DOCTYPE" not in xml.upper()
         and b"<!ENTITY" not in xml.upper(),
         "Unbounded native source model XML/DTD injection")
    parser=etree.XMLParser(load_dtd=False,resolve_entities=False,
                           no_network=True,huge_tree=False,recover=False)
    return etree.fromstring(xml,parser)


def _eq_dict(node,attrs,msg):
    need(dict(node.attrib)==attrs,msg)


def verify_native_catalog_046(source:Path,source_sha:str,
                              manifest_xml:bytes,pages:dict[str,list[bytes]])->dict:
    """Independent exact audit of ALL 8 catalogs + every page, not one sample."""
    source=Path(source)
    profile=original_27_sources()
    need(source_sha in profile and source.is_file() and not source.is_symlink()
         and file_sha(source)==source_sha,
         "Native source IFC SHA or original source27 pin invalid")
    model=ifcopenshell.open(str(source))
    prev=profile[source_sha]
    need(model.schema==prev["schema"]
         and abs(ifcopenshell.util.unit.calculate_unit_scale(model)-.001)<1e-12,
         "Source native IFC schema or millimetre units drift")
    expected=_expected_catalog(source,model)
    header={
        "version":"0.46","sourceOriginalIFCSha256":source_sha,
        "sourceNativeIfcSchema":model.schema,
        "sourceNativeLengthUnit":"MILLIMETER",
        "sourceMode":"IMMUTABLE_ORIGINAL_IFC_INDEX_READ_ONLY",
        "nativeMutationPermission":"NONE_READ_ONLY",
    }
    doc=_parse(manifest_xml)
    need(doc.tag==Q+"Building" and len(doc)==1
         and doc[0].tag==Q+"OriginalNativeSourceCatalog"
         and len(doc[0])==len(CATALOGS), "Original v0.46 native catalog manifest invalid")
    _eq_dict(doc,header,"Original native IFC manifest source header altered")
    need(set(pages)==set(CATALOGS),"Missing original source catalog page type")
    total=Counter()
    max_page=0
    rendered_pages=0
    for name,mnode in zip(CATALOGS,doc[0]):
        entries=expected[name]
        count=len(entries)
        pc=(count+PAGE_SIZE-1)//PAGE_SIZE
        digest=sha256(json.dumps(entries,sort_keys=True,
               ensure_ascii=False,separators=(",",":")).encode("utf8")).hexdigest()
        need(mnode.tag==Q+"Catalog","Original native source manifest catalog order changed")
        _eq_dict(mnode,{
            "name":name,"recordCount":str(count),
            "pageSize":str(PAGE_SIZE),"pageCount":str(pc),
            "canonicalSourceRecordsSha256":digest,
        },"Original catalog metadata count/source digest tampered")
        need(len(pages[name])==pc,"Native model-facing source page count incomplete")
        for index,raw in enumerate(pages[name]):
            doc_page=_parse(raw)
            need(doc_page.tag==Q+"OriginalNativeSourcePage"
                 and len(doc_page)==min(PAGE_SIZE,count-index*PAGE_SIZE),
                 "Original source catalog page/records missing")
            _eq_dict(doc_page,{**header,"catalog":name,
               "page":str(index),"pageSize":str(PAGE_SIZE),
               "totalPages":str(pc),"totalRecords":str(count)},
               "Native model-facing source page header/index altered")
            originals=entries[index*PAGE_SIZE:(index+1)*PAGE_SIZE]
            for actual,original in zip(doc_page,originals):
                need(actual.tag==Q+"Entry",
                     "Source IFC page entry type forged")
                _eq_dict(actual,original["attrs"],
                         "Source IFC original entity GUID/name/class/digest/bbox modified")
                fields=[(x.get("name"),x.get("value")) for x in actual
                        if x.tag==Q+"Field"]
                refs=[dict(x.attrib) for x in actual if x.tag==Q+"Ref"]
                literal=[x.text for x in actual if x.tag==Q+"LiteralStepText"]
                need(fields==original["fields"]
                     and refs==original["refs"]
                     and ([original["text"]] if original["text"] is not None else [])==literal
                     and [x.tag for x in actual]==(
                         [Q+"Field"]*len(original["fields"])+
                         [Q+"Ref"]*len(original["refs"])+
                         ([Q+"LiteralStepText"] if original["text"] is not None else [])),
                     "Source IFC original property/material/relations/placement/STEP text changed")
            max_page=max(max_page,len(raw))
            rendered_pages+=1
        total[name]=count
    need(total["roots"]==len(model.by_type("IfcRoot"))
         and total["products"]==len(model.by_type("IfcProduct"))
         and total["relationships"]==len(model.by_type("IfcRelationship"))
         and total["property_sets"]==len(model.by_type("IfcPropertySet"))
         and total["materials"]==len(model.by_type("IfcMaterial"))
         and total["placements"]==len(model.by_type("IfcLocalPlacement"))
         and total["step"]==len(list(model))
         and file_sha(source)==source_sha,
         "Source IFC or original native complete catalog inventory changed")
    return {
        "status":"V046_INDEPENDENT_ORIGINAL27_FULL_PAGED_NATIVE_SOURCE_ORACLE_PASS",
        "original_native_ifc_sha256":source_sha,
        "native_original_ifc_schema":model.schema,
        "native_original_length_unit":"millimetres",
        "manifest_sha256":sha256(manifest_xml).hexdigest(),
        "full_native_source_catalog_page_count":rendered_pages,
        "largest_model_facing_native_source_page_bytes":max_page,
        "full_source_step_literal_original_line_count":total["step"],
        "original_native_root_GUIDs":total["roots"],
        "original_native_product_GUIDs":total["products"],
        "original_native_relation_GUIDs_endpoint_lists":total["relationships"],
        "original_native_property_sets_named_values":total["property_sets"],
        "original_native_materials_original_names":total["materials"],
        "original_native_local_placement_matrices":total["placements"],
        "original_native_product_geometry_digests_or_explicit_unavailable":total["geometry"],
        "original_native_products_with_computed_physical_world_mesh":sum(
            item["attrs"].get("meshStatus")=="REAL_SOURCE_NATIVE_WORLD_MESH_1UM"
            for item in expected["geometry"]),
        "original_native_products_with_explicit_unavailable_world_geometry":sum(
            item["attrs"].get("meshStatus")=="UNAVAILABLE_NATIVE_GEOMETRY"
            for item in expected["geometry"]),
        "original_native_products_without_original_representation":sum(
            item["attrs"].get("meshStatus")=="NO_ORIGINAL_REPRESENTATION"
            for item in expected["geometry"]),
        "native_IFC_edit_authority_proven":False,
        "full_original_IFC_and_Python_API_execution_parity_proven":False,
        "original_task_answer_or_evaluator_score_proven":False,
    }
