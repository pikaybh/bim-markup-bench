"""v0.42 independent exact original-mm native Slab source mesh XML oracle.

No imports from the v0.42 projection/compiler, no author evaluation, no
hidden GT. Verifies original source ordered vertices, original indexed
triangles, class, name, floor type, actual native source Storey/rel GUID.
Then an independent original source-vs-candidate physical IFC gate from v0.41
also verifies every original physical product, including these opaque Slabs.
"""
from __future__ import annotations

from hashlib import sha256
from math import isfinite
from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
from lxml import etree

from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v041_p3_native_oracle import verify_p3_original_native_add

Q="{urn:bim-markup-bench:toy:v0}"
PIN={
  "topological_test_02":(
    "8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72",
    {"3_DHXxtdb3wRKlXgyMiHCa":("1ZGO8hrFCHqw0v0026FpFv","1ZGO8hrFCHqw0v0066FpFv"),
     "3_DHXxtdb3wRKlXgyMiHD0":("2JF4e6axWHqu3u0C1FZlmi","2JF4e6axWHqu3u0C5FZlmi")}),
  "topological_test_04":(
    "29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5",
    {"3_DHXxtdb3wRKlXgyMiHCa":("1ZGO8hrFCHqw0v0026FpFv","1ZGO8hrFCHqw0v0066FpFv")}),
}


class IndependentNativeSlab042Error(ValueError):
    pass


def require(value,why):
    if not value:raise IndependentNativeSlab042Error(why)


def _num(value):
    number=float(value)
    require(isfinite(number),"Original native mesh coordinate not finite")
    formatted=f"{number:.6f}".rstrip("0").rstrip(".")
    return "0" if formatted in ("","-0") else formatted


def _mesh_native_mm(source):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    # Keep the owning C++ geometry shape alive while reading mesh buffers.
    # A dangling temporary .geometry may return invalid native arrays.
    shape=ifcopenshell.geom.create_shape(settings,source)
    mesh=shape.geometry
    raw=list(mesh.verts)
    face=list(mesh.faces)
    require(len(raw)%3==0 and len(face)%3==0
            and 8<=len(raw)//3<=100
            and 12<=len(face)//3<=200,
            "Independent original source mesh not within known safe bounds")
    points=[tuple(_num(raw[i+j]) for j in range(3))
            for i in range(0,len(raw),3)]
    triangles=[tuple(int(face[i+j]) for j in range(3))
               for i in range(0,len(face),3)]
    require(all(0<=a<len(points) and 0<=b<len(points)
                and 0<=c<len(points) and len({a,b,c})==3
                for a,b,c in triangles),
            "Independent native original source triangle indices invalid")
    return points,triangles,sha256(repr((points,triangles)).encode("ascii")).hexdigest()


def verify_original_native_slab_evidence(
        original_mm:Path,model_visible_xml:bytes,*,task_id:str)->dict:
    require(task_id in PIN,"Unknown original-public slab read-only task")
    original_mm=Path(original_mm)
    original_sha,required=PIN[task_id]
    require(original_mm.is_file() and not original_mm.is_symlink()
            and file_hash(original_mm)==original_sha,
            "Independent original native-mm source IFC not pinned")
    original=ifcopenshell.open(str(original_mm))
    require(original.schema=="IFC4X3" and abs(
        ifcopenshell.util.unit.calculate_unit_scale(original)-.001)<1e-12,
        "Independent source IFC4X3 native-mm units altered")
    slabs={s.GlobalId:s for s in original.by_type("IfcSlab")}
    require(set(slabs)==set(required),"Independent native source existing Slab GUID set changed")
    doc=etree.fromstring(model_visible_xml)
    require(doc.tag==Q+"Building", "Actual model-facing XML is not complete Building")
    require(doc.get("ifcSchema")=="IFC4X3"
            and doc.get("units")=="m"
            and len(doc)==4,
            "Actual model-facing XML schema, metric unit or source section not correct")
    evidence=doc.find(Q+"OriginalNativeSlabEvidence")
    require(evidence is not None and evidence.get("originalIFCSha256")==original_sha
            and evidence.get("sourceIfcSchema")=="IFC4X3"
            and evidence.get("sourceModelSha256")==doc.get("sourceModelSha256")
            and evidence.get("compilerEditPermission")=="NONE_READ_ONLY"
            and evidence.get("evidenceVersion")=="0.42"
            and evidence.get("originalExplicitSpaceBoundaryCount")=="0",
            "Original source-Slab reference catalog missing, malformed or unfrozen")
    node_slabs=evidence.find(Q+"NativeSlabs")
    node_rels=evidence.find(Q+"OriginalExplicitSlabRelations")
    require(node_slabs is not None and node_rels is not None
            and len(node_slabs)==len(slabs)
            and len(node_rels)==len(slabs),
            "Actual XML must expose all and only original source Slabs/real relations")
    visible={n.get("ifcGuid"):n for n in node_slabs}
    require(len(visible)==len(slabs) and set(visible)==set(slabs),
            "Native original source Slab guid missing, duplicated or invented in XML")
    editable=doc.find(Q+"Elements")
    require(editable is not None
            and not set(slabs)&{n.get("ifcGuid") for n in editable},
            "Original native source Slab cannot silently masquerade as editable XML element")
    relations={n.get("originalRelatedGuid"):n for n in node_rels}
    require(len(relations)==len(slabs) and set(relations)==set(slabs),
            "Original native Slab source containment relations missing or duplicated")
    out=[]
    for guid in sorted(slabs):
        native=slabs[guid]
        node=visible[guid]
        storey,rel_id=required[guid]
        require(node.get("nativeIfcClass")=="IfcSlab"
                and node.get("originalName")==str(native.Name or "")
                and node.get("originalObjectType")==str(native.ObjectType or "")
                and node.get("originalPredefinedType")==native.PredefinedType=="FLOOR"
                and node.get("sourceContainedStoreyGuid")==storey
                and node.get("sourceContainmentRelationGuid")==rel_id
                and node.get("compilerEditPermission")=="NONE_READ_ONLY",
                "Original source Slab class, name, type, owner or READ-ONLY flag changed")
        source_rels=[r for r in original.by_type("IfcRelContainedInSpatialStructure")
                     if native in r.RelatedElements]
        require(len(source_rels)==1
                and source_rels[0].GlobalId==rel_id
                and source_rels[0].RelatingStructure.GlobalId==storey
                and source_rels[0].RelatingStructure.is_a()=="IfcBuildingStorey",
                "Actual original IFC native Slab Storey relationship not as declared")
        relation=relations[guid]
        require(relation.get("ifcClass")=="IfcRelContainedInSpatialStructure"
                and relation.get("relationGuid")==rel_id
                and relation.get("originalRelatingGuid")==storey
                and relation.get("originalRelatedGuid")==guid
                and relation.get("origin")=="EXPLICIT_SOURCE_IFC_ONLY",
                "Actual native original Slab relationship GUID/type/source/target differs")
        points,triangles,digest=_mesh_native_mm(native)
        pointroot=node.find(Q+"WorldVertices")
        faceroot=node.find(Q+"WorldTriangles")
        require(pointroot is not None and faceroot is not None
                and len(pointroot)==len(points)
                and len(faceroot)==len(triangles),
                "Native source Slab source-model XML mesh vertex/face counts differ")
        for i,(v,coordinates) in enumerate(zip(pointroot,points)):
            require(v.tag==Q+"Vertex" and v.get("index")==str(i)
                    and tuple(v.get(k) for k in ("x","y","z"))==coordinates,
                    "Original native-mm source Slab ordered triangle vertex coordinates differ")
        for triangle,indices in zip(faceroot,triangles):
            require(triangle.tag==Q+"Triangle"
                    and tuple(int(triangle.get(k)) for k in ("a","b","c"))==indices,
                    "Original native-mm indexed Slab triangle topology changed in model-visible XML")
        lo=tuple(_num(min(float(v[j]) for v in points)) for j in range(3))
        hi=tuple(_num(max(float(v[j]) for v in points)) for j in range(3))
        require(node.get("worldMeshSha256")==digest
                and tuple(node.get("worldMin"+k) for k in ("X","Y","Z"))==lo
                and tuple(node.get("worldMax"+k) for k in ("X","Y","Z"))==hi,
                "Native source Slab mesh bounds/digest not equal to real original-mm IFC")
        out.append({
            "original_native_slab_guid":guid,
            "native_ifc_class":"IfcSlab",
            "native_slab_predefined_type":native.PredefinedType,
            "original_name":str(native.Name or ""),
            "original_native_storey_guid":storey,
            "original_native_spatial_relation_guid":rel_id,
            "source_mm_ordered_vertices":len(points),
            "source_mm_ordered_index_triangles":len(triangles),
            "model_visible_triangle_indices_exact_match":True,
            "model_visible_ordered_world_vertices_exact_match_at_1um_decimal":True,
            "original_source_mesh_sha256":digest,
            "original_world_bounds_m":{
                "min":[float(x) for x in lo],
                "max":[float(x) for x in hi],
            },
            "source_ifc_slab_is_read_only_in_XML":True,
        })
    require(file_hash(original_mm)==original_sha,
            "Original source IFC data mutated during independent evidence audit")
    return {
        "status":"INDEPENDENT_V042_ORIGINAL_MM_SLAB_MESH_AND_RELATION_EVIDENCE_PASS",
        "task_id":task_id,
        "original_native_ifc_sha256":original_sha,
        "actual_model_facing_existing_native_slab_count":len(out),
        "source_native_slab_original_vertices_total":sum(x["source_mm_ordered_vertices"] for x in out),
        "source_native_slab_original_index_triangles_total":sum(x["source_mm_ordered_index_triangles"] for x in out),
        "no_fabricated_space_boundaries":True,
        "complete_original_source_information_parity_with_python":False,
        "slabs":out,
    }


def verify_v042_output_original_native(
        original_mm:Path,candidate_mm:Path,*,task_id:str,
        submitted_xml:bytes)->dict:
    source=verify_original_native_slab_evidence(
        original_mm,submitted_xml,task_id=task_id)
    native=verify_p3_original_native_add(
        original_mm,candidate_mm,task_id=task_id,
        submitted_xml=submitted_xml)
    require(native["all_original_opaque_native_Slab_physical_shapes_preserved"]==
                source["actual_model_facing_existing_native_slab_count"],
            "Original output native mm IFC failed to preserve source Slabs physically")
    return {
        "status":"INDEPENDENT_V042_READONLY_SOURCE_AND_ORIGINAL_NATIVE_IFC_CREATION_PASS",
        "source_native_slab_reference_evidence":source,
        "original_native_mm_output_physical_oracle":native,
    }
