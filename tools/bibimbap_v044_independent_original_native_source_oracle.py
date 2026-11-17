"""Independent v0.44 original IFC4X3/mm source/XML exact read oracle.

DOES NOT import v0.44 projector/session/compiler, original author grader, GT,
Docker or any model provider. Re-reads the immutable source bytes and compares
every original STEP DATA record plus actual XML model-visible structured source
GUIDs, relations, property values, materials, placement frames and native 1um
world mesh/ordered indexed triangles.
"""
from __future__ import annotations

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

Q="{urn:bim-markup-bench:toy:v0}"
ORIGINAL_PINS={
    "geometry_test_14":(
        "67ac42ca988bdfd44a2afe3ebaff8be11da913b281338ec127f4897e3f42f6a3",119,5),
    "geometry_test_15":(
        "318fb45af8142c164c1fc53eeadc472008ff9c42e9c1b6398e9c95aa744374af",166,8),
    "topological_test_11":(
        "c85a8b90f1b2d22f1e27428e38c54ba7a0d1bdcfbd9d5cef8db06ad97712032e",579,17),
    "topological_test_17":(
        "a052ec0377c437f28f0a1b8be4dd4ce4f78bf877bde7e51d10eb2d72310230bd",440,17),
}
PARTS=("Products","Relations","PropertySets","Materials",
       "LocalPlacements","WorldGeometry","NativeStepRecords")
STEP_RE=re.compile(r"^#([1-9][0-9]*)=([A-Z0-9_]+)\(.*\);$")


class IndependentV044Error(ValueError):
    pass


def require(ok,why):
    if not ok:
        raise IndependentV044Error(why)


def hash_file(file:Path)->str:
    h=sha256()
    with Path(file).open("rb") as stream:
        for b in iter(lambda:stream.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def _dict_equal(node,expected:dict,kind:str):
    require(dict(node.attrib)==expected,
            "Independent original native "+kind+" metadata/IFC identity mismatch")


def _txt(value)->str:
    return str(value) if value is not None else ""


def _num(value)->str:
    v=round(float(value),6)
    require(math.isfinite(v) and abs(v)<=1000000,
            "Original native source physical coordinate nonfinite/out of bounds")
    return "0.000000" if v==0 else f"{v:.6f}"


def _refs(value):
    if isinstance(value,ifcopenshell.entity_instance):
        yield value
    elif isinstance(value,(tuple,list)):
        for part in value:
            yield from _refs(part)


def _original_data_lines(file:Path,model):
    raw=Path(file).read_bytes()
    require(b"\x00" not in raw and len(raw)<100000,
            "Native immutable source IFC STEP invalid size/control")
    lines=raw.decode("utf8").splitlines()
    require(lines.count("DATA;")==1 and lines.count("ENDSEC;")==2,
            "Original source IFC STEP DATA/ENDSEC structure mismatch")
    pos=lines.index("DATA;")
    end=lines.index("ENDSEC;",pos+1)
    lines=lines[pos+1:end]
    result=[]
    for line in lines:
        match=STEP_RE.fullmatch(line)
        require(match is not None,
                "Original source STEP DATA contains non-entity or multiline record")
        step=int(match[1]);klass=match[2]
        ent=model.by_id(step)
        require(ent is not None and ent.is_a().upper()==klass,
                "Original source literal STEP record not in independent IFC model")
        result.append((str(step),klass,line))
    require(len(result)==len(list(model))
            and len({x[0] for x in result})==len(result),
            "Original source all DATA entity count/order uniqueness check failed")
    return result


def _original_mesh(obj,settings):
    try:
        shape=ifcopenshell.geom.create_shape(settings,obj)
    except Exception as exc:
        return {"status":"SOURCE_NATIVE_GEOMETRY_UNAVAILABLE",
                "errorType":type(exc).__name__}
    verts=list(shape.geometry.verts)
    faces=list(shape.geometry.faces)
    require(verts and not len(verts)%3 and faces and not len(faces)%3,
            "Independent original world geometry length invalid")
    points=[tuple(_num(verts[i+j]) for j in range(3))
            for i in range(0,len(verts),3)]
    tris=[tuple(int(faces[i+j]) for j in range(3))
          for i in range(0,len(faces),3)]
    require(all(0<=min(t) and max(t)<len(points) for t in tris),
            "Independent world triangle original vertex references invalid")
    content=json.dumps({"vertices":points,"faces":tris},
                       sort_keys=True,separators=(",",":")).encode("utf8")
    bbox=[_num(min(float(p[j]) for p in points)) for j in range(3)]
    bbox+=[_num(max(float(p[j]) for p in points)) for j in range(3)]
    return {"status":"ORIGINAL_SOURCE_NATIVE_WORLD_MESH_1UM",
            "vertices":points,"triangles":tris,
            "sha256":sha256(content).hexdigest(),"bbox":bbox}


def validate_original_v044_native_model_read(source:Path,xml:bytes,
                                            *,task_id:str)->dict:
    source=Path(source)
    require(task_id in ORIGINAL_PINS,"Source-native oracle task unregistered")
    expected_sha,expected_entities,expected_products=ORIGINAL_PINS[task_id]
    require(source.is_file() and not source.is_symlink()
            and hash_file(source)==expected_sha,
            "Independent source exact original SHA256 changed or symlinked")
    require(isinstance(xml,bytes) and 0<len(xml)<=300000,
            "Model-visible source XML absent/oversized")
    require(b"<!DOCTYPE" not in xml.upper()
            and b"<!ENTITY" not in xml.upper(),
            "Model-visible XML forbids any DTD/external entity")
    parser=etree.XMLParser(load_dtd=False,resolve_entities=False,
                           no_network=True,recover=False,huge_tree=False)
    root=etree.fromstring(xml,parser)
    _dict_equal(root,{
        "version":"0.44",
        "sourceOriginalIFCSha256":expected_sha,
        "sourceIfcSchema":"IFC4X3",
        "sourceLengthUnit":"MILLIMETER_NATIVE",
        "sourceCompleteness":"ALL_ORIGINAL_NATIVE_STEP_DATA_ENTITIES_EXACT_WITH_DERIVED_READONLY_MESH",
        "nativeMutationPermission":"NONE_READ_ONLY",
    },"XML Building source root")
    require(root.tag==Q+"Building" and len(root)==1
            and root[0].tag==Q+"OriginalNativeIFCSource"
            and [x.tag for x in root[0]]==[Q+x for x in PARTS],
            "Original 7 source content sections missing/forged/reordered")
    doc=root[0]
    native=ifcopenshell.open(str(source))
    require(native.schema=="IFC4X3"
            and abs(ifcopenshell.util.unit.calculate_unit_scale(native)-.001)<1e-12,
            "Original native IFC source schema/units mismatch")
    roots=native.by_type("IfcRoot")
    require(len({x.GlobalId for x in roots})==len(roots),
            "Original native IFC duplicate root GlobalId")
    products=sorted(native.by_type("IfcProduct"),key=lambda x:x.GlobalId)
    relations=sorted(native.by_type("IfcRelationship"),key=lambda x:x.GlobalId)
    psets=sorted(native.by_type("IfcPropertySet"),key=lambda x:x.id())
    mats=sorted(native.by_type("IfcMaterial"),key=lambda x:x.id())
    places=sorted(native.by_type("IfcLocalPlacement"),key=lambda x:x.id())
    _dict_equal(doc,{
        "readOnly":"true",
        "sourceOriginalIFCSha256":expected_sha,
        "nativeIfcSchema":"IFC4X3",
        "nativeEntityCount":str(expected_entities),
        "nativeProductCount":str(expected_products),
        "nativeRelationCount":str(len(relations)),
        "sourceDataLinesAreComplete":"true",
        "nativeMutationPermission":"NONE_READ_ONLY",
    },"XML NativeSource source header")
    require(len(products)==expected_products
            and len(list(native))==expected_entities,
            "Original native pinned product/entity population changed")
    tree_products,tree_rels,tree_psets,tree_mats,tree_places,tree_geos,tree_steps=list(doc)
    require(len(tree_products)==len(products)
            and len(tree_rels)==len(relations)
            and len(tree_psets)==len(psets)
            and len(tree_mats)==len(mats)
            and len(tree_places)==len(places),
            "Model-visible source original product/relation/property/material/placement counts incomplete")

    for node,item in zip(tree_products,products):
        require(node.tag==Q+"Product","XML Product source node type wrong")
        attrs={
            "ifcGuid":item.GlobalId,
            "nativeIfcClass":item.is_a(),
            "sourceStepId":str(item.id()),
            "originalName":_txt(item.Name),
            "originalDescription":_txt(item.Description),
            "nativeMutationPermission":"NONE_READ_ONLY",
        }
        if item.ObjectPlacement is not None:
            attrs["sourceObjectPlacementStepId"]=str(item.ObjectPlacement.id())
        if item.Representation is not None:
            attrs["sourceRepresentationStepId"]=str(item.Representation.id())
        if getattr(item,"ObjectType",None) is not None:
            attrs["originalObjectType"]=_txt(item.ObjectType)
        if getattr(item,"PredefinedType",None) is not None:
            attrs["originalPredefinedType"]=_txt(item.PredefinedType)
        _dict_equal(node,attrs,"IfcProduct")

    for node,r in zip(tree_rels,relations):
        require(node.tag==Q+"Relation","XML native Relationship missing")
        _dict_equal(node,{
            "ifcGuid":r.GlobalId,
            "nativeIfcClass":r.is_a(),
            "sourceStepId":str(r.id()),
            "originalName":_txt(r.Name),
            "nativeMutationPermission":"NONE_READ_ONLY",
        },"IfcRelationship original GUID")
        refs=[]
        for i in range(len(r)):
            role=r.attribute_name(i)
            for related in _refs(r[i]):
                attrs={
                    "attribute":role,"sourceStepId":str(related.id()),
                    "nativeIfcClass":related.is_a(),
                }
                if related.is_a("IfcRoot"):
                    attrs["ifcGuid"]=related.GlobalId
                refs.append(attrs)
        require(len(node)==len(refs),
                "Original relationship endpoint reference count incomplete")
        for actual,ref in zip(node,refs):
            require(actual.tag==Q+"NativeRef","Relationship related source node wrong")
            _dict_equal(actual,ref,"IfcRelationship original endpoint/role")

    for node,pset in zip(tree_psets,psets):
        require(node.tag==Q+"PropertySet","Native source IfcPropertySet XML missing")
        _dict_equal(node,{
            "ifcGuid":pset.GlobalId,
            "sourceStepId":str(pset.id()),
            "originalName":_txt(pset.Name),
            "originalDescription":_txt(pset.Description),
        },"IfcPropertySet name/GUID")
        expect=list(pset.HasProperties)
        require(len(node)==len(expect),"Native original property list incomplete")
        for x,p in zip(node,expect):
            require(x.tag==Q+"Property","Native original property type wrong")
            attrs={
                "sourceStepId":str(p.id()),
                "nativeIfcClass":p.is_a(),
                "originalName":_txt(p.Name),
            }
            if getattr(p,"NominalValue",None) is not None:
                value=p.NominalValue
                attrs["nominalIfcClass"]=value.is_a()
                attrs["sourceNominalValue"]=_txt(value.wrappedValue)
            _dict_equal(x,attrs,"Native original property name/value")

    for node,mat in zip(tree_mats,mats):
        require(node.tag==Q+"Material","Native original material XML missing")
        attrs={
            "sourceStepId":str(mat.id()),
            "originalName":_txt(mat.Name),
            "originalDescription":_txt(mat.Description),
        }
        if getattr(mat,"Category",None) is not None:
            attrs["originalCategory"]=_txt(mat.Category)
        _dict_equal(node,attrs,"IfcMaterial original name/details")

    for node,placement in zip(tree_places,places):
        require(node.tag==Q+"LocalPlacement",
                "Original native LocalPlacement reference XML missing")
        attrs={
            "sourceStepId":str(placement.id()),
            "relativePlacementStepId":str(placement.RelativePlacement.id()),
        }
        if placement.PlacementRelTo is not None:
            attrs["parentPlacementStepId"]=str(placement.PlacementRelTo.id())
        matrix=ifcopenshell.util.placement.get_local_placement(placement)
        for i in range(4):
            for j in range(4):
                attrs[f"m{i}{j}"]=_num(matrix[i][j])
        _dict_equal(node,attrs,"IfcLocalPlacement original matrix")

    visible_geometry_products=[p for p in products
                               if p.Representation is not None]
    require(len(tree_geos)==len(visible_geometry_products),
            "All original native product Representations must have model-visible mesh status")
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    fullmesh=0
    geom_error=0
    world_vertices=0
    world_tris=0
    for node,item in zip(tree_geos,visible_geometry_products):
        require(node.tag==Q+"ProductGeometry",
                "Original native geometry Product source order wrong")
        mesh=_original_mesh(item,settings)
        attrs={
            "ifcGuid":item.GlobalId,
            "nativeIfcClass":item.is_a(),
            "sourceRepresentationStepId":str(item.Representation.id()),
            "meshStatus":mesh["status"],
        }
        if mesh["status"]=="SOURCE_NATIVE_GEOMETRY_UNAVAILABLE":
            geom_error+=1
            attrs["errorType"]=mesh["errorType"]
            require(len(node)==0,"Unavailable original source geometry must not fake vertices")
        else:
            fullmesh+=1
            verts=mesh["vertices"];tri=mesh["triangles"]
            world_vertices+=len(verts);world_tris+=len(tri)
            attrs.update({
                "worldMeshSha256":mesh["sha256"],
                "worldVertexCount":str(len(verts)),
                "worldTriangleCount":str(len(tri)),
            })
            attrs.update(dict(zip(
                ("minX","minY","minZ","maxX","maxY","maxZ"),
                mesh["bbox"])))
            require([x.tag for x in node]==[Q+"WorldVertices",Q+"WorldTriangles"],
                    "Original world mesh children missing/reordered")
            vnodes=node[0];tnodes=node[1]
            require(len(vnodes)==len(verts) and len(tnodes)==len(tri),
                    "Original world mesh indexed vertex/triangle population wrong")
            for i,(v,point) in enumerate(zip(vnodes,verts)):
                require(v.tag==Q+"V","Original world vertex node wrong")
                _dict_equal(v,{
                    "index":str(i),"x":point[0],"y":point[1],"z":point[2]},
                    "Original physical world vertex index/coordinates")
            for t,(a,b,c) in zip(tnodes,tri):
                require(t.tag==Q+"T","Original world face triangle node wrong")
                _dict_equal(t,{
                    "a":str(a),"b":str(b),"c":str(c)},
                    "Original physical world triangle exact source index")
        _dict_equal(node,attrs,"Original native world physical mesh meta/bbox")

    records=_original_data_lines(source,native)
    require(len(tree_steps)==len(records)==expected_entities,
            "Original native DATA STEP records missing, added or duplicated")
    for xml_node,(sid,klass,literal_line) in zip(tree_steps,records):
        require(xml_node.tag==Q+"StepEntity"
                and not len(xml_node)
                and dict(xml_node.attrib)=={
                    "sourceStepId":sid,"nativeIfcClass":klass}
                and xml_node.text==literal_line,
                "Exact original native-mm STEP DATA line/ID/order/class tampered")
    require(hash_file(source)==expected_sha,
            "Original source IFC changed during independent oracle")
    return {
        "task_id":task_id,
        "original_source_ifc_sha256":expected_sha,
        "original_native_ifc_schema":"IFC4X3",
        "original_native_length_unit":"mm",
        "actual_read_only_model_xml_sha256":sha256(xml).hexdigest(),
        "actual_xml_source_bytes":len(xml),
        "source_original_native_STEP_DATA_entities_exactly_model_visible":len(records),
        "source_native_IfcProduct_GUIDs_with_exact_class_name_and_source_step_visible":len(products),
        "source_native_IfcRelationship_GUIDs_and_exact_source_endpoints_visible":len(relations),
        "source_native_IfcPropertySet_names_Guids_properties_visible":len(psets),
        "source_native_IfcMaterial_names_visible":len(mats),
        "source_native_IfcLocalPlacement_matrices_visible":len(places),
        "source_native_original_physical_product_world_mesh_visible":fullmesh,
        "source_native_original_physical_world_mesh_unavailable_explicit":geom_error,
        "source_original_world_mesh_ordered_vertices_visible":world_vertices,
        "source_original_world_mesh_ordered_triangles_visible":world_tris,
        "all_original_source_STEP_DATA_entity_lines_byte_text_and_order_match":True,
        "all_native_source_product_and_relation_and_property_and_material_and_placement_data_match":True,
        "original_IFC_native_update_delete_mutation_available":False,
        "full_native_ifcopenshell_python_execution_parity_proven":False,
        "actual_original_author_task_answer_or_score_proven":False,
    }
