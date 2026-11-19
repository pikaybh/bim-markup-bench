"""Isolated read-only native-source XML projection worker for v0.12.

Not an IFC authoring tool or editor. Invoked per unique original native IFC
source as a separate subprocess so a native OCC fault cannot contaminate the
45-case study or other results. Emit only public source SHA, original rooted
IFC GUIDs, schema, projected class/GUID counts, precise parser/binder and
source-reference evidence, and safe failure category. Never emit input IFC.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from hashlib import sha256
import argparse
import json
import tempfile
import sys

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v9_projection import project_ifc_v9
from src.runtime.experimental_v8_legacy_projection import project_legacy_v8
from src.runtime.markup_normal_form import NS
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document

Q="{"+NS+"}"


def _sha(p:Path)->str:
    h=sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(original:Path,expected_sha:str)->dict:
    if not original.is_file() or original.is_symlink() or _sha(original)!=expected_sha:
        raise ValueError("INPUT_SOURCE_SHA_OR_FILE_INVALID")
    f=ifcopenshell.open(str(original))
    schema=f.schema
    original_product={obj.GlobalId:obj.is_a()
                      for obj in f.by_type("IfcProduct")}
    original_roots={obj.GlobalId for obj in f.by_type("IfcRoot")}
    out={
        "original_ifc_sha256":expected_sha,
        "original_native_schema":schema,
        "original_product_guids":sorted(original_product),
        "original_product_class_by_guid":dict(sorted(original_product.items())),
        "original_source_root_guid_count":len(original_roots),
        "original_source_product_count":len(original_product),
        "original_length_unit_scale_to_m":float(
            ifcopenshell.util.unit.calculate_unit_scale(f)),
    }
    if schema not in ("IFC2X3","IFC4","IFC4X3"):
        out.update({
            "projection_state":"FAIL_CLOSED",
            "projection_failure_code":"ORIGINAL_IFC_SCHEMA_UNSUPPORTED",
        })
        return out
    with tempfile.TemporaryDirectory(prefix="bibi138-readonly-") as temp:
        normalized=Path(temp)/"original_native_schema_metres.ifc"
        if ifcopenshell.util.unit.calculate_unit_scale(f)<=0:
            raise ValueError("SOURCE_UNIT_INVALID")
        ifcopenshell.util.unit.convert_file_length_units(
            f,"METER").write(str(normalized))
        converted=ifcopenshell.open(str(normalized))
        if converted.schema!=schema or abs(
            ifcopenshell.util.unit.calculate_unit_scale(converted)-1.
        )>1e-8:
            raise ValueError("NATIVE_SCHEMA_OR_UNITS_INVALID_AFTER_NORMALIZE")
        out["native_normalized_clone_sha256"]=_sha(normalized)
        out["normalized_original_schema_preserved"]=True
        try:
            if schema=="IFC4X3":
                view=project_ifc_v9(normalized)
                builder="experimental_v9_projection_on_IFC4X3"
            else:
                view=project_legacy_v8(normalized)
                builder="experimental_v8_legacy_projection_on_native_schema"
            rawxml=view.xml
            if not rawxml:
                raise ValueError("EMPTY_PROJECTED_XML")
            root=etree.fromstring(rawxml)
            actual_ns=etree.QName(root).namespace
            expected_ns=(
                NS if schema=="IFC4X3"
                else "urn:bim-markup-bench:legacy:v0.8"
            )
            if actual_ns!=expected_ns or etree.QName(root).localname!="Building":
                raise ValueError("INVALID_PROJECTED_XML_ROOT")
            if root.get("sourceModelSha256")!=out["native_normalized_clone_sha256"]:
                raise ValueError("PROJECTED_SOURCE_HASH_MISMATCH")
            # Note: partial source view does not serialize all IFC Roots/STEP
            # and must NOT be described as native editable model parity.
            local="{"+expected_ns+"}"
            elements=root.find(local+"Elements")
            levels=root.find(local+"Levels")
            if elements is None or levels is None:
                raise ValueError("MISSING_PROJECTED_ELEMENTS_OR_LEVELS")
            ifc_guid_nodes={}
            managed_classes=Counter()
            for node in list(elements):
                name=etree.QName(node).localname
                managed_classes[name]+=1
                guid=node.get("ifcGuid")
                if guid:
                    if guid in ifc_guid_nodes:
                        raise ValueError("DUPLICATE_ORIGINAL_IFC_GUID_IN_XML")
                    if guid not in original_product:
                        raise ValueError("PROJECTED_IFC_GUID_NOT_AN_ORIGINAL_PRODUCT")
                    ifc_guid_nodes[guid]=name
            for node in list(levels):
                guid=node.get("ifcGuid")
                if guid and guid not in original_roots:
                    raise ValueError("PROJECTED_LEVEL_GUID_NOT_IN_ORIGINAL_SOURCE")
            if schema=="IFC4X3":
                # In IFC4X3 the original graph binder validates source
                # immutable GUID identity, XML references and relationships.
                ast=parse_xml(rawxml,expected_source_sha256=
                              out["native_normalized_clone_sha256"])
                bound=bind_document(ast,projection=view)
                if bound is None:
                    raise ValueError("NATIVE_XML_GRAPH_BINDING_EMPTY")
                binding_status="ORIGINAL_SOURCE_ID_GRAPH_BOUND"
            else:
                # Existing v0.8 native-schema projection may use fields
                # not admitted by the frozen IFC4X3 schema binder.
                binding_status="SCHEMA_NATIVE_LEGACY_READONLY_XML_NOT_IFC4X3_BINDER"
            out.update({
                "projection_state":"PASSED_NATIVE_PARTIAL_SOURCE_READ",
                "projection_builder":builder,
                "projection_xml_sha256":sha256(rawxml).hexdigest(),
                "projection_xml_immutable_source_hash_verified":True,
                "source_stable_id_binding_status":binding_status,
                "projected_native_existing_product_count":len(ifc_guid_nodes),
                "projected_native_existing_guids":sorted(ifc_guid_nodes),
                "projected_existing_product_xml_type_by_guid":
                    dict(sorted(ifc_guid_nodes.items())),
                "projected_model_classes":{
                    name:int(count) for name,count in
                    sorted(managed_classes.items())
                },
                "original_native_products_not_in_XML":sorted(
                    set(original_product)-set(ifc_guid_nodes)
                ),
                "original_native_products_not_in_XML_count":len(
                    set(original_product)-set(ifc_guid_nodes)
                ),
                "partial_projection_not_full_IFC_source_SERIALIZATION":True,
                "no_native_write_operation_executed":True,
            })
        except Exception as exc:
            # Safe categorical reason inferred only from the actual
            # source XML binder's exact known invariant, not by a hidden
            # target or model/scorer feedback. Raw IFC or stack trace
            # and arbitrary exception text never enter Git reports.
            failure_class=type(exc).__name__
            failure_code=(
                "HOSTED_OPENING_OUTSIDE_SOURCE_WALL_XML_BINDER_EXTENT"
                if failure_class=="BindingError" and
                "Opening is outside the hosted wall's horizontal extent"
                in str(exc)
                else failure_class
            )
            out.update({
                "projection_state":"FAIL_CLOSED",
                "projection_builder":(
                    "experimental_v9_projection_on_IFC4X3" if schema=="IFC4X3"
                    else "experimental_v8_legacy_projection_on_native_schema"),
                "projection_failure_code":failure_code,
                "projection_failure_class":failure_class,
                "partial_projection_not_full_IFC_source_SERIALIZATION":True,
                "no_native_write_operation_executed":True,
            })
    if _sha(original)!=expected_sha:
        raise ValueError("ORIGINAL_SOURCE_MUTATED_DURING_PROJECTION")
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-source",required=True,type=Path)
    p.add_argument("--original-sha256",required=True)
    args=p.parse_args()
    try:
        obj=inspect(args.original_source.resolve(strict=True),
                    args.original_sha256)
        print(json.dumps({"status":"SOURCE_PROJECTION_INSPECTED","inspection":obj},
                         sort_keys=True))
    except Exception as exc:
        print(json.dumps({
            "status":"INSPECTION_WORKER_FAILED",
            "failure_code":type(exc).__name__,
        },sort_keys=True))
        raise SystemExit(3)


if __name__=="__main__":
    main()
