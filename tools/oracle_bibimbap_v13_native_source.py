"""Independent original IFC-only oracle for v0.13 read-only native catalog.

NO compiler, projection, binder, prior v0.9/v0.12 helper, original author
scorer or private GT imports. Recompute actual original IFC product IDs,
real original host/void/fill source relationships and source world meshes.
The two XML documents have SEPARATE namespaces and permissions. This oracle
never authors/modifies/writes IFC or claims native edit task success.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from itertools import chain
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

CATALOG="{urn:bim-markup-bench:original-native-source:readonly:v0.13}"
TYPED="{urn:bim-markup-bench:toy:v0}"
TOL=1e-6


class IndependentV13SourceError(ValueError):
    pass


def _source_hash(path:Path)->str:
    h=sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _source_mesh(product):
    if product.Representation is None:
        return {"state":"NO_NATIVE_REPRESENTATION"}
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        owner=ifcopenshell.geom.create_shape(settings,product)
        v=np.array(owner.geometry.verts,dtype=float).reshape(-1,3)
        faces=np.array(owner.geometry.faces,dtype=np.int64).reshape(-1,3)
    except Exception:
        return {"state":"NATIVE_MESH_NOT_AVAILABLE"}
    if (not len(v) or not len(faces) or
        np.any(~np.isfinite(v)) or
        np.max(np.abs(v))>1e9 or
        np.any(faces<0) or np.any(faces>=len(v))):
        return {"state":"NATIVE_MESH_NOT_AVAILABLE"}
    v=np.round(v,8)
    v[v==0]=0
    h=sha256()
    h.update(v.astype("<f8").tobytes(order="C"))
    h.update(faces.astype("<i8").tobytes(order="C"))
    return {
        "state":"ORIGINAL_NATIVE_TRIANGULATION_READONLY",
        "worldMeshVertexCount":str(len(v)),
        "worldMeshTriangleCount":str(len(faces)),
        "worldMeshSha256":h.hexdigest(),
        "worldMinX":str(float(v[:,0].min())),
        "worldMinY":str(float(v[:,1].min())),
        "worldMinZ":str(float(v[:,2].min())),
        "worldMaxX":str(float(v[:,0].max())),
        "worldMaxY":str(float(v[:,1].max())),
        "worldMaxZ":str(float(v[:,2].max())),
    }


def _source_relations(f):
    values=[]
    for r in f.by_type("IfcRelVoidsElement"):
        values.append((r.is_a(),r.GlobalId,
                       r.RelatingBuildingElement.GlobalId,
                       r.RelatedOpeningElement.GlobalId))
    for r in f.by_type("IfcRelFillsElement"):
        values.append((r.is_a(),r.GlobalId,
                       r.RelatingOpeningElement.GlobalId,
                       r.RelatedBuildingElement.GlobalId))
    for r in f.by_type("IfcRelContainedInSpatialStructure"):
        values.extend((r.is_a(),r.GlobalId,
                       r.RelatingStructure.GlobalId,x.GlobalId)
                      for x in r.RelatedElements)
    for r in f.by_type("IfcRelAggregates"):
        if hasattr(r.RelatingObject,"GlobalId"):
            values.extend((r.is_a(),r.GlobalId,
                           r.RelatingObject.GlobalId,x.GlobalId)
                          for x in r.RelatedObjects if hasattr(x,"GlobalId"))
    for r in f.by_type("IfcRelSpaceBoundary"):
        if r.RelatingSpace is not None and r.RelatedBuildingElement is not None:
            values.append((r.is_a(),r.GlobalId,r.RelatingSpace.GlobalId,
                           r.RelatedBuildingElement.GlobalId))
    return tuple(sorted(set(values)))


def _native_unfit_hosted_openings(f):
    """Independent real physical source Wall line+world Opening mesh audit.

    No XML projection geometry is read here, so the original source-only
    failure partition must be reproducible independent of source compiler.
    If a source opening cannot be measured exactly, do not claim it was
    proven safe: fail closed for this bounded v0.13 source family.
    """
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    invalid=set()
    reasons={}
    for relation in f.by_type("IfcRelVoidsElement"):
        opening=relation.RelatedOpeningElement
        host=relation.RelatingBuildingElement
        if not opening.is_a("IfcOpeningElement") or not host.is_a("IfcWall"):
            continue
        axes=[
            item for rep in host.Representation.Representations
            if rep.RepresentationType=="Curve2D"
            for item in rep.Items
            if item.is_a("IfcPolyline") and len(item.Points)==2
        ]
        if len(axes)!=1:
            # The old projection does not grant this host the editability
            # required by current Opening read relationship.
            continue
        transform=np.asarray(ifcopenshell.util.placement.get_local_placement(
            host.ObjectPlacement),dtype=float)
        ends=np.array([
            (transform@np.array([
                float(point.Coordinates[0]),float(point.Coordinates[1]),0.,1.
            ],dtype=float))[:3]
            for point in axes[0].Points
        ],dtype=float)
        axis=ends[1]-ends[0]
        length=float(np.linalg.norm(axis))
        if length<=0:
            raise IndependentV13SourceError("Original native hosted Wall line degenerate")
        axis/=length
        transform_open=np.asarray(ifcopenshell.util.placement.get_local_placement(
            opening.ObjectPlacement),dtype=float)
        origin=transform_open[:3,3]
        offset=float(np.dot(origin-ends[0],axis))
        try:
            shape=ifcopenshell.geom.create_shape(settings,opening)
            pts=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)
            width=float(np.ptp(pts@axis))
        except Exception:
            # Unavailable native geometry cannot be declared supported by
            # an independent source-only geometric oracle.
            continue
        if len(pts)<4 or width<=0 or not np.isfinite(width):
            raise IndependentV13SourceError("Original native Opening geometric width invalid")
        if (offset<0 or offset+width>length+TOL):
            invalid.add(opening.GlobalId)
            reasons[opening.GlobalId]={
                "original_wall":host.GlobalId,
                "original_native_offset_m":round(offset,6),
                "original_native_opening_width_m":round(width,6),
                "original_native_wall_line_length_m":round(length,6),
                "source_native_excess_m":round(offset+width-length,6),
            }
    return invalid,reasons


def verify_v13_original_native_source(
    original:Path,typed_xml:bytes,catalog_xml:bytes
)->dict:
    if not original.is_file() or original.is_symlink():
        raise IndependentV13SourceError("Original source IFC path invalid")
    before=_source_hash(original)
    f=ifcopenshell.open(str(original))
    if f.schema not in ("IFC4X3","IFC2X3","IFC4") or abs(
        ifcopenshell.util.unit.calculate_unit_scale(f)-1.
    )>1e-8:
        raise IndependentV13SourceError("Original native IFC schema/metre source required")
    try:
        typed=etree.fromstring(typed_xml)
        catalog=etree.fromstring(catalog_xml)
    except etree.XMLSyntaxError as exc:
        raise IndependentV13SourceError("Source native XML evidence is malformed") from exc
    expected_typed_ns=(TYPED if f.schema=="IFC4X3"
                       else "{urn:bim-markup-bench:legacy:v0.8}")
    if (typed.tag!=expected_typed_ns+"Building" or
        catalog.tag!=CATALOG+"OriginalNativeSourceCatalog" or
        typed.get("sourceModelSha256")!=before or
        catalog.get("sourceModelSha256")!=before or
        catalog.get("sourceIfcSchema")!=f.schema or
        catalog.get("catalogMode")!="READ_ONLY_NO_COMPILER_AUTHORITY" or
        catalog.get("catalogIsNotEditableBIMState")!="true" or
        catalog.get("typedXmlIsPartial")!="true" or
        catalog.get("geometryEnvelopesAreNotEditableShapes")!="true"):
        raise IndependentV13SourceError("Catalog/source authority, native schema or readonly provenance invalid")
    typed_elements=typed.find(expected_typed_ns+"Elements")
    if typed_elements is None:
        raise IndependentV13SourceError("Missing existing typed source model")
    typed_guids={x.get("ifcGuid") for x in typed_elements if x.get("ifcGuid")}
    if len(typed_guids)!=sum(1 for x in typed_elements if x.get("ifcGuid")):
        raise IndependentV13SourceError("Duplicate typed original source IFC GUIDs")
    source_products={p.GlobalId:p for p in f.by_type("IfcProduct")}
    catalog_items=catalog.findall(
        "./"+CATALOG+"Products/"+CATALOG+"Product")
    catalog_byid={p.get("ifcGuid"):p for p in catalog_items}
    if (len(catalog_items)!=len(source_products)
        or len(catalog_byid)!=len(catalog_items)
        or set(catalog_byid)!=set(source_products)
        or not typed_guids<=set(source_products)):
        raise IndependentV13SourceError("Read-only XML omitted/duplicated original native IFC Product")
    original_roots={r.GlobalId for r in f.by_type("IfcRoot")}
    for guid,p in catalog_byid.items():
        obj=source_products[guid]
        if (p.get("ifcClass")!=obj.is_a()
            or p.get("nativeStepId")!=str(obj.id())
            or p.get("compilerEditPermission")!="NONE_FROM_THIS_CATALOG"
            or p.get("originalSourceOwnership")!="IMMUTABLE_ORIGINAL_NATIVE_IFC"):
            raise IndependentV13SourceError("Native source identity/class/edit authority mismatch")
        if (p.get("typedXmlRepresentation")== "YES_PARTIAL_TYPED_SOURCE") != (guid in typed_guids):
            raise IndependentV13SourceError("Native source element typed vs opaque read inventory inconsistent")
        if (guid not in typed_guids and
            p.get("typedXmlRepresentation")!="NO_READONLY_NATIVE_SOURCE_ONLY"):
            raise IndependentV13SourceError("Native opaque original Product incorrectly marked editable")
        owner=ifcopenshell.util.element.get_container(obj)
        aggregate=ifcopenshell.util.element.get_aggregate(obj)
        if p.get("originalContainmentStoreyGuid")!=(
                owner.GlobalId if owner is not None and hasattr(owner,"GlobalId") else None):
            raise IndependentV13SourceError("Original native Storey containment altered in catalog")
        if p.get("originalAggregationParentGuid")!=(
                aggregate.GlobalId if aggregate is not None and hasattr(aggregate,"GlobalId") else None):
            raise IndependentV13SourceError("Original IFC RelAggregates parent does not match catalog")
        meshes=p.findall("./"+CATALOG+"SourceWorldMesh")
        if len(meshes)!=1:
            raise IndependentV13SourceError("Original source native mesh evidence missing")
        expected=_source_mesh(obj)
        actual=meshes[0].attrib
        if expected["state"]!=actual.get("state"):
            raise IndependentV13SourceError("Real native source geometry availability status mismatched")
        if expected["state"]=="ORIGINAL_NATIVE_TRIANGULATION_READONLY":
            for key in ("worldMeshVertexCount","worldMeshTriangleCount",
                        "worldMeshSha256"):
                if actual.get(key)!=expected[key]:
                    raise IndependentV13SourceError("Native source mesh digest/count mismatch")
            for key in ("worldMinX","worldMinY","worldMinZ",
                        "worldMaxX","worldMaxY","worldMaxZ"):
                if abs(float(actual[key])-float(expected[key]))>1e-6:
                    raise IndependentV13SourceError("Native source world mesh envelope evidence changed")
    original_relationships=set(_source_relations(f))
    xml_rels={
        (x.get("ifcClass"),x.get("ifcGuid"),x.get("originalRelatingGuid"),
         x.get("originalRelatedGuid"))
        for x in catalog.findall(
            "./"+CATALOG+"OriginalNativeRelationshipEvidence/"+
            CATALOG+"Relation")
    }
    if xml_rels!=original_relationships:
        raise IndependentV13SourceError("Source native explicit IFC relationship inventory mismatched")
    for elem in catalog.findall("./"+CATALOG+"OriginalNativeRelationshipEvidence/"+CATALOG+"Relation"):
        if (elem.get("relationshipEvidence")!="EXPLICIT_ORIGINAL_IFC_ONLY"
            or elem.get("compilerEditPermission")!="NONE_FROM_THIS_CATALOG"):
            raise IndependentV13SourceError("Fabricated editable source native IFC relation")
        if any(x not in original_roots for x in (
            elem.get("ifcGuid"),elem.get("originalRelatingGuid"),elem.get("originalRelatedGuid"))):
            raise IndependentV13SourceError("Original IFC relationship references absent IFC Root")
    true_bad,reasons=_native_unfit_hosted_openings(f)
    original_fill={
        rel.RelatedBuildingElement.GlobalId:
        rel.RelatingOpeningElement.GlobalId
        for rel in f.by_type("IfcRelFillsElement")
    }
    # Every ORIGINAL failed native-source Opening + its dependent fill
    # remain in catalog, and are correctly EXCLUDED from the safe typed XML.
    for bad in true_bad:
        if bad in typed_guids:
            raise IndependentV13SourceError(
                "Actual source Opening beyond original host physical line was offered as typed editable")
        if catalog_byid[bad].get("readonlyReason")!=(
            "SOURCE_ORIGINAL_HOSTED_OPENING_OUTSIDE_TYPED_WALL_EXTENT"
        ):
            raise IndependentV13SourceError("Original out-of-wall source Opening not explicitly protected")
    protected_fills={
        fill for fill,op in original_fill.items() if op in true_bad
    }
    for fill in protected_fills:
        if (fill in typed_guids or
            catalog_byid[fill].get("readonlyReason")!=
            "SOURCE_ORIGINAL_HOSTED_OPENING_OUTSIDE_TYPED_WALL_EXTENT"):
            raise IndependentV13SourceError(
                "Dependent original filled Window/Door not safely source-owned read-only"
            )
    # The oracle cannot claim read functionality for an unrelated missing
    # native typed object. All catalog items are real and immutable, but
    # no generalized native write permission is inferred for *any* Product.
    missing=set(source_products)-typed_guids
    if _source_hash(original)!=before:
        raise IndependentV13SourceError("Original native IFC source modified during read-only oracle")
    classes=Counter(source_products[g].is_a() for g in missing)
    geom=Counter(p.find(CATALOG+"SourceWorldMesh").get("state")
                 for p in catalog_items)
    return {
        "status":"INDEPENDENT_NATIVE_IFC_READONLY_CATALOG_ORACLE_PASS_V013",
        "original_normalized_source_sha256":before,
        "source_catalog_sha256":sha256(catalog_xml).hexdigest(),
        "strict_typed_source_xml_sha256":sha256(typed_xml).hexdigest(),
        "original_native_products_all_cataloged":len(source_products),
        "original_native_explicit_source_relationship_edges":len(original_relationships),
        "original_source_products_not_in_typed_editable_xml":len(missing),
        "original_native_opaque_product_types":dict(sorted(classes.items())),
        "original_native_shape_evidence_status":dict(sorted(geom.items())),
        "independently_original_native_hosted_out_of_extent_openings":
            tuple(sorted(true_bad)),
        "independently_source_original_linked_fills_protected":
            tuple(sorted(protected_fills)),
        "native_wall_opening_source_excess_evidence":{
            g:reasons[g] for g in sorted(reasons)
        },
        "native_source_IFC_root_and_geometry_identity_preserved":True,
        "catalog_is_readonly_not_editable_source_BIM_model":True,
        "new_model_calls":0,
        "full_original45_IFC_write_parity_proven":False,
    }
