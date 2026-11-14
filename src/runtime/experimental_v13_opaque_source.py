"""Prospective original-IFC source-faithful v0.13 *READ-ONLY* view.

This is NOT a native write compiler and NOT an editable BIM authoring API.
The independent preexisting typed XML source schema cannot truthfully express
some original Revit IFC4X3 hosted openings extending outside their projected
source Wall centerline, or complex original IFC Space/Beam/Wall geometry.

Never clamp an invalid opening, expand a Wall, flatten a native mesh into
fake editable geometry, invent a missing relationship or change source IFC.
Repair only the READ VIEW: omit precisely proven source-original offending
Opening and its original filled Window/Door from the bounded typed XML and
put *all* original native source Products/selected native relations into a
separate source-SHA-pinned READ-ONLY reference catalog XML. The catalog is NOT
an input to any trusted native writer and cannot be edited to modify IFC.

Never revise frozen v0.1–v0.12 projection/compiler/source/original D0.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass,replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import math
import struct

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v8_legacy_projection import project_legacy_v8,parse_v8
from src.runtime.ifc_projection import OpaqueReference
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.markup_normal_form import NS
from src.runtime.semantic_graph import BindingError
from src.runtime.ifc_snapshot import snapshot_source

Q="{"+NS+"}"
CATALOG_NS="urn:bim-markup-bench:original-native-source:readonly:v0.13"
R="{"+CATALOG_NS+"}"
TOLERANCE=Decimal("0.000001")
SOURCE_LIMIT=2000


class NativeReadV13Error(ValueError):
    pass


@dataclass(frozen=True)
class NativeReadV13:
    projection:object  # frozen Projection from existing v0.9
    source_catalog_xml:bytes
    demoted_opening_guids:tuple[str,...]
    demoted_fill_guids:tuple[str,...]
    native_source_sha256:str
    source_original_ifc_schema:str
    protected_original_product_count:int

    def report(self):
        return {
            "status":"SOURCE_ORIGINAL_NATIVE_IFC_READONLY_SAFE_TYPED_XML_PLUS_NATIVE_CATALOG_V013",
            "native_source_sha256":self.native_source_sha256,
            "native_source_ifc_schema":self.source_original_ifc_schema,
            "typed_xml_sha256":sha256(self.projection.xml).hexdigest(),
            "read_only_catalog_xml_sha256":sha256(self.source_catalog_xml).hexdigest(),
            "readonly_native_original_product_count":self.protected_original_product_count,
            "bad_source_openings_demoted_to_readonly":self.demoted_opening_guids,
            "source_fills_of_bad_openings_demoted_to_readonly":self.demoted_fill_guids,
            "original_source_not_modified":True,
            "original_IfcVoids_IfcFills_native_relationships_unchanged":True,
            "read_only_catalog_is_NOT_a_native_edit_compiler_input":True,
            "original_entire_IFC_serialized_losslessly_to_XML":False,
            "semantic_native_write_supported_for_demoted_elements":False,
            "full_original_45_task_edit_parity":False,
            "new_model_requests":0,
        }


def _number(v:float)->str:
    if not math.isfinite(float(v)) or abs(float(v))>1e9:
        raise NativeReadV13Error("Nonfinite/out of bounds original source native coordinate")
    text=format(float(v),".9f").rstrip("0").rstrip(".")
    return "0" if text in ("","-0") else text


def _native_mesh_summary(product):
    """Native source geometry is opaque; report actual mesh facts or unavailable.

    A box/envelope is a *read-only observation*, never an editable shape
    approximation or an IFC shape replacement.
    """
    if product.Representation is None:
        return {"state":"NO_NATIVE_REPRESENTATION"}
    options=ifcopenshell.geom.settings()
    options.set(options.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(options,product)
        verts=np.asarray(shape.geometry.verts,dtype=np.float64).reshape(-1,3)
        faces=np.asarray(shape.geometry.faces,dtype=np.int64).reshape(-1,3)
    except Exception:
        return {"state":"NATIVE_MESH_NOT_AVAILABLE"}
    if (len(verts)==0 or len(faces)==0 or
        not np.all(np.isfinite(verts)) or
        np.max(np.abs(verts))>1e9 or np.any(faces<0) or
        np.any(faces>=len(verts))):
        return {"state":"NATIVE_MESH_NOT_AVAILABLE"}
    h=sha256()
    # Exact source-generated geometry in deterministic original C++ shape
    # order. Fixed decimal vertices avoid architecture-dependent -0.
    canonical=np.round(verts,8)
    canonical[canonical==0.]=0.
    h.update(canonical.astype("<f8").tobytes(order="C"))
    h.update(faces.astype("<i8").tobytes(order="C"))
    lower=verts.min(axis=0);upper=verts.max(axis=0)
    return {
        "state":"ORIGINAL_NATIVE_TRIANGULATION_READONLY",
        "worldMeshVertexCount":str(len(verts)),
        "worldMeshTriangleCount":str(len(faces)),
        "worldMeshSha256":h.hexdigest(),
        "worldMinX":_number(lower[0]),
        "worldMinY":_number(lower[1]),
        "worldMinZ":_number(lower[2]),
        "worldMaxX":_number(upper[0]),
        "worldMaxY":_number(upper[1]),
        "worldMaxZ":_number(upper[2]),
    }


def _catalog_xml(f,*,source_sha:str,typed_guids:set[str],
                 demoted:set[str])->bytes:
    native_products=sorted(f.by_type("IfcProduct"),key=lambda p:p.GlobalId)
    if not native_products or len(native_products)>SOURCE_LIMIT:
        raise NativeReadV13Error("Original IFC source Product catalog exceeds read-only bounds")
    root=etree.Element(
        R+"OriginalNativeSourceCatalog",nsmap={None:CATALOG_NS},
        attrib={
            "version":"0.13",
            "sourceModelSha256":source_sha,
            "sourceIfcSchema":f.schema,
            "originalNativeUnits":"m",
            "catalogMode":"READ_ONLY_NO_COMPILER_AUTHORITY",
            "typedXmlIsPartial":"true",
            "catalogIsNotEditableBIMState":"true",
            "geometryEnvelopesAreNotEditableShapes":"true",
        }
    )
    products=etree.SubElement(root,R+"Products")
    product_map={x.GlobalId:x for x in native_products}
    for obj in native_products:
        attrs={
            "ifcGuid":obj.GlobalId,
            "ifcClass":obj.is_a(),
            "nativeStepId":str(obj.id()),
            "typedXmlRepresentation":(
                "YES_PARTIAL_TYPED_SOURCE" if obj.GlobalId in typed_guids
                else "NO_READONLY_NATIVE_SOURCE_ONLY"),
            "compilerEditPermission":"NONE_FROM_THIS_CATALOG",
            "originalSourceOwnership":"IMMUTABLE_ORIGINAL_NATIVE_IFC",
        }
        if obj.GlobalId in demoted:
            attrs["readonlyReason"]="SOURCE_ORIGINAL_HOSTED_OPENING_OUTSIDE_TYPED_WALL_EXTENT"
        elif obj.GlobalId not in typed_guids:
            attrs["readonlyReason"]="SOURCE_NATIVE_ELEMENT_NOT_SUPPORTED_BY_TYPED_XML"
        if hasattr(obj,"Name") and obj.Name:
            # Exact untrusted original IFC name: preserve as pure XML attr,
            # never interpret this as a runtime/script instruction.
            attrs["originalSourceName"]=str(obj.Name)[:256]
        container=ifcopenshell.util.element.get_container(obj)
        if container is not None and hasattr(container,"GlobalId"):
            attrs["originalContainmentStoreyGuid"]=container.GlobalId
        aggregate=ifcopenshell.util.element.get_aggregate(obj)
        if aggregate is not None and hasattr(aggregate,"GlobalId"):
            attrs["originalAggregationParentGuid"]=aggregate.GlobalId
        p=etree.SubElement(products,R+"Product",attrib=attrs)
        etree.SubElement(p,R+"SourceWorldMesh",attrib=_native_mesh_summary(obj))
    rels=etree.SubElement(root,R+"OriginalNativeRelationshipEvidence",
                          attrib={"scope":"BOUND_EXPLICIT_IFC_RELATIONS_NOT_ALL_IFC_RELATION_CLASSES"})
    # Directly emit only original explicit IFC relationships, no inferred
    # proximity/contact. Every link is rooted to real source GUID evidence.
    known=set(product_map)
    relations=[]
    for rel in f.by_type("IfcRelVoidsElement"):
        relations.append(("IfcRelVoidsElement",rel.GlobalId,
                          rel.RelatingBuildingElement.GlobalId,
                          rel.RelatedOpeningElement.GlobalId))
    for rel in f.by_type("IfcRelFillsElement"):
        relations.append(("IfcRelFillsElement",rel.GlobalId,
                          rel.RelatingOpeningElement.GlobalId,
                          rel.RelatedBuildingElement.GlobalId))
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        for obj in rel.RelatedElements:
            relations.append(("IfcRelContainedInSpatialStructure",rel.GlobalId,
                              rel.RelatingStructure.GlobalId,obj.GlobalId))
    for rel in f.by_type("IfcRelAggregates"):
        for obj in rel.RelatedObjects:
            if hasattr(rel.RelatingObject,"GlobalId") and hasattr(obj,"GlobalId"):
                relations.append(("IfcRelAggregates",rel.GlobalId,
                                  rel.RelatingObject.GlobalId,obj.GlobalId))
    for rel in f.by_type("IfcRelSpaceBoundary"):
        if rel.RelatingSpace is not None and rel.RelatedBuildingElement is not None:
            relations.append(("IfcRelSpaceBoundary",rel.GlobalId,
                              rel.RelatingSpace.GlobalId,rel.RelatedBuildingElement.GlobalId))
    # Some explicit original relations link spatial hierarchy/metadata; they
    # are true original GUIDs even if outside original IfcProduct catalog.
    all_roots={x.GlobalId for x in f.by_type("IfcRoot")}
    for kind,rel_guid,src,dst in sorted(set(relations)):
        if src not in all_roots or dst not in all_roots:
            raise NativeReadV13Error("Original explicit IFC relation source root missing")
        etree.SubElement(rels,R+"Relation",attrib={
            "ifcClass":kind,"ifcGuid":rel_guid,
            "originalRelatingGuid":src,"originalRelatedGuid":dst,
            "relationshipEvidence":"EXPLICIT_ORIGINAL_IFC_ONLY",
            "compilerEditPermission":"NONE_FROM_THIS_CATALOG",
        })
    return etree.tostring(root,encoding="utf8",xml_declaration=True,
                          pretty_print=True)


def project_original_ifc_v13(source:Path)->NativeReadV13:
    """Read original IF4X3 source, never open/writes a native IFC candidate.

    Any unsupported other binder failure remains an exception. The v0.13
    opt-in source view cannot be passed to earlier native editors as proof
    that demoted source objects are editable. The catalog is read-only.
    """
    if (not source.is_file() or source.is_symlink()):
        raise NativeReadV13Error("Original IFC source path invalid")
    model=ifcopenshell.open(str(source))
    if model.schema!="IFC4X3" or abs(
        ifcopenshell.util.unit.calculate_unit_scale(model)-1.
    )>1e-8:
        raise NativeReadV13Error("Native original IFC4X3 metre-normalized source required")
    old=project_ifc_v9(source)
    original_hash=old.source.source_sha256
    raw=old.xml
    source_xml_root=etree.fromstring(raw)
    elements=source_xml_root.find(Q+"Elements")
    if elements is None:
        raise NativeReadV13Error("Original native typed XML Elements missing")
    typed_walls={
        x.get("id"):x for x in elements if x.tag==Q+"Wall"
    }
    invalid=[]
    for op in elements:
        if op.tag!=Q+"Opening":
            continue
        host=typed_walls.get(op.get("host"))
        if host is None:
            raise NativeReadV13Error(
                "Original hosted Opening references missing typed Wall; cannot safely demote"
            )
        ax=Decimal(host.get("x2"))-Decimal(host.get("x1"))
        ay=Decimal(host.get("y2"))-Decimal(host.get("y1"))
        length=(ax*ax+ay*ay).sqrt()
        offset=Decimal(op.get("offset"))
        width=Decimal(op.get("width"))
        if width<=0:
            raise NativeReadV13Error("Source original Opening has invalid width")
        if offset < 0 or offset+width>length+TOLERANCE:
            oid=op.get("ifcGuid")
            wallguid=host.get("ifcGuid")
            orig=model.by_guid(oid)
            if not orig.is_a("IfcOpeningElement"):
                raise NativeReadV13Error("Original source Opening IFC class mismatch")
            rel=[
                r for r in model.by_type("IfcRelVoidsElement")
                if r.RelatedOpeningElement.GlobalId==oid
            ]
            if len(rel)!=1 or rel[0].RelatingBuildingElement.GlobalId!=wallguid:
                raise NativeReadV13Error(
                    "Cannot demote host Opening without exactly verified original IfcRelVoidsElement"
                )
            invalid.append(oid)
    demoted_op=set(invalid)
    demoted_fills=set()
    if demoted_op:
        for opguid in sorted(demoted_op):
            fills=[
                rel.RelatedBuildingElement.GlobalId
                for rel in model.by_type("IfcRelFillsElement")
                if rel.RelatingOpeningElement.GlobalId==opguid
            ]
            for guid in fills:
                if not model.by_guid(guid).is_a() in ("IfcWindow","IfcDoor"):
                    raise NativeReadV13Error("Source Opening has unexpected filling IFC class")
                demoted_fills.add(guid)
        # The *source is unchanged*. We only hide these original hosted
        # elements from a typed XML whose geometry preconditions they
        # genuinely violate; all are shown in native catalog with real links.
        deleted=demoted_op|demoted_fills
        allowed_typed={"Opening","Window","Door"}
        removed_typed=set()
        for node in list(elements):
            if node.get("ifcGuid") in deleted:
                kind=etree.QName(node).localname
                if kind not in allowed_typed:
                    raise NativeReadV13Error("Demotion unexpectedly selected unrelated native kind")
                if kind in ("Door","Window"):
                    op=next(
                        (x for x in elements if x.tag==Q+"Opening"
                         and x.get("id")==node.get("opening")),None
                    )
                    # For fills attached to demoted opening, the
                    # projection's exact fill ref is checked. One original
                    # IFC Filling relation alone cannot authorize removal
                    # of another unrelated typed source object.
                    related_original=[
                        x for x in model.by_type("IfcRelFillsElement")
                        if x.RelatedBuildingElement.GlobalId==node.get("ifcGuid")
                    ]
                    if (len(related_original)!=1
                        or related_original[0].RelatingOpeningElement.GlobalId not in demoted_op):
                        raise NativeReadV13Error("Original source filling relation mismatch")
                removed_typed.add(node.get("ifcGuid"))
                elements.remove(node)
        if removed_typed!=deleted:
            # If original filling is unprojected already, this must not
            # incorrectly demand adding it to typed XML.
            projected_guids={x.get("ifcGuid") for x in source_xml_root.find(Q+"Elements")}
            if removed_typed!=demoted_op|(demoted_fills&{
                g for g,lid in old.projected_global_ids
                if g in demoted_fills
            }):
                raise NativeReadV13Error("Source demotion did not match exact existing XML nodes")
        xml=etree.tostring(source_xml_root,encoding="utf8",
                           xml_declaration=True,pretty_print=True)
        removed_count=Counter(
            model.by_guid(g).is_a() for g in removed_typed
        )
        current_count=Counter(dict(old.supported_class_counts))
        opaque_count=Counter(dict(old.unsupported_class_counts))
        for cls,count in removed_count.items():
            if current_count[cls]<count:
                raise NativeReadV13Error("Original supported class demotion inventory mismatch")
            current_count[cls]-=count
            opaque_count[cls]+=count
            if current_count[cls]==0:
                del current_count[cls]
        new_opaque=list(old.opaque_references)
        for guid in sorted(removed_typed):
            new_opaque.append(OpaqueReference(
                guid,model.by_guid(guid).is_a(),
                "Native opening horizontal footprint outside typed Wall / dependent native fill; source owned READ ONLY",
            ))
        old=replace(
            old,
            xml=xml,
            projected_global_ids=tuple(
                (g,lid) for g,lid in old.projected_global_ids
                if g not in removed_typed
            ),
            opaque_references=tuple(new_opaque),
            supported_class_counts=tuple(sorted(current_count.items())),
            unsupported_class_counts=tuple(sorted(opaque_count.items())),
            opaque_relation_reasons=tuple(sorted(set(
                old.opaque_relation_reasons
            )|{
                "Original host Opening offset extends beyond the projected native Wall line: read-only preservation, not editable geometry manipulation",
            })),
        )
    # The old strict IFC4X3 geometry and native relation binder is STILL
    # applied to every surviving typed original node.
    ast=parse_xml(old.xml,expected_source_sha256=original_hash)
    bound=bind_document(ast,projection=old)
    if bound.missing_source_relation_edges:
        raise NativeReadV13Error("Original native source IFC relationship missing")
    typed_guids={
        el.get("ifcGuid") for el in etree.fromstring(old.xml).find(Q+"Elements")
        if el.get("ifcGuid")
    }
    catalog=_catalog_xml(
        model,source_sha=original_hash,typed_guids=typed_guids,
        demoted=demoted_op|demoted_fills,
    )
    if snapshot_source(source).source_sha256!=original_hash:
        raise NativeReadV13Error("Original IFC source bytes changed during read-only source projection")
    return NativeReadV13(
        projection=old,source_catalog_xml=catalog,
        demoted_opening_guids=tuple(sorted(demoted_op)),
        demoted_fill_guids=tuple(sorted(demoted_fills)),
        native_source_sha256=original_hash,
        source_original_ifc_schema=model.schema,
        protected_original_product_count=len(model.by_type("IfcProduct")),
    )


def project_original_native_v13(source:Path)->NativeReadV13:
    """Source-faithful read-only v0.13 catalog across all original schemas.

    IFC4X3 gets the repaired strict original v0.9 typed binder when needed.
    IFC2X3/IFC4 use the original distinct v0.8 legacy typed XML/XSD and a
    native source-backed readonly product/relation/mesh catalog. Neither
    view is a general native writer or complete lossless editable BIM XML.
    """
    if source.is_symlink() or not source.is_file():
        raise NativeReadV13Error("Original source IFC must be an existing ordinary file")
    f=ifcopenshell.open(str(source))
    if f.schema=="IFC4X3":
        return project_original_ifc_v13(source)
    if f.schema not in ("IFC2X3","IFC4") or abs(
        ifcopenshell.util.unit.calculate_unit_scale(f)-1.
    )>1e-8:
        raise NativeReadV13Error("Only actual original IFC2X3/IFC4/IFC4X3 metre sources")
    old=project_legacy_v8(source)
    parsed=parse_v8(old.xml,source_sha256=old.source_sha256,
                    native_schema=f.schema)
    typed_guids={
        node.get("ifcGuid")
        for node in parsed.find("{urn:bim-markup-bench:legacy:v0.8}Elements")
        if node.get("ifcGuid")
    }
    if old.source_sha256!=snapshot_source(source).source_sha256:
        raise NativeReadV13Error("Original native-schema source changed across legacy read")
    cat=_catalog_xml(
        f,source_sha=old.source_sha256,typed_guids=typed_guids,demoted=set()
    )
    if snapshot_source(source).source_sha256!=old.source_sha256:
        raise NativeReadV13Error("Original source changed during read-only legacy catalog")
    return NativeReadV13(
        projection=old,source_catalog_xml=cat,
        demoted_opening_guids=(),demoted_fill_guids=(),
        native_source_sha256=old.source_sha256,
        source_original_ifc_schema=f.schema,
        protected_original_product_count=len(f.by_type("IfcProduct")),
    )
