"""Read-only v0.13 original IFC source audit worker (one isolated process).

Tests actual native-schema source projection + independent IFC-only oracle.
All products, projected and opaque, must be verifiable from the original
source. Original IFC file remains immutable; no native candidate write.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import json
import tempfile

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v13_opaque_source import project_original_native_v13
from tools.oracle_bibimbap_v13_native_source import verify_v13_original_native_source

NATIVE="{urn:bim-markup-bench:original-native-source:readonly:v0.13}"


def _sha(path:Path):
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def inspect(original:Path,sha:str)->dict:
    if (not original.is_file() or original.is_symlink()
        or _sha(original)!=sha):
        raise ValueError("ORIGINAL_PUBLIC_IFC_SOURCE_HASH_OR_PATH_INVALID")
    native=ifcopenshell.open(str(original))
    if native.schema not in ("IFC2X3","IFC4","IFC4X3"):
        raise ValueError("ORIGINAL_PUBLIC_IFC_SOURCE_SCHEMA_NOT_SUPPORTED")
    with tempfile.TemporaryDirectory(prefix="bibimbap140-v13-readonly-") as folder:
        src=Path(folder)/"source_normalized_metres.ifc"
        ifcopenshell.util.unit.convert_file_length_units(
            native,"METER").write(str(src))
        model=ifcopenshell.open(str(src))
        if model.schema!=native.schema or abs(
            ifcopenshell.util.unit.calculate_unit_scale(model)-1
        )>1e-8:
            raise ValueError("ORIGINAL_NATIVE_SCHEMA_CHANGE_OR_UNNORMALIZED_CLONE")
        view=project_original_native_v13(src)
        oracle=verify_v13_original_native_source(
            src,view.projection.xml,view.source_catalog_xml)
        original_root=etree.fromstring(view.source_catalog_xml)
        nodes=original_root.findall("./"+NATIVE+"Products/"+NATIVE+"Product")
        allproducts={
            node.get("ifcGuid"):node.get("ifcClass") for node in nodes
        }
        typed={
            node.get("ifcGuid"):node.get("ifcClass")
            for node in nodes
            if node.get("typedXmlRepresentation")=="YES_PARTIAL_TYPED_SOURCE"
        }
        omitted={
            node.get("ifcGuid"):node.get("ifcClass")
            for node in nodes
            if node.get("typedXmlRepresentation")=="NO_READONLY_NATIVE_SOURCE_ONLY"
        }
        if len(nodes)!=len(allproducts) or (
            set(typed)|set(omitted)!=set(allproducts)
            or set(typed)&set(omitted)
        ):
            raise ValueError("ORIGINAL_NATIVE_PRODUCT_CATALOG_NOT_EXACT_PARTITION")
        source_schema=model.schema
        structured={
            "original_public_ifc_sha256":sha,
            "original_native_ifc_schema":source_schema,
            "original_metres_normalized_clone_sha256":_sha(src),
            "native_product_catalog_sha256":sha256(
                view.source_catalog_xml).hexdigest(),
            "native_typed_read_xml_sha256":sha256(
                view.projection.xml).hexdigest(),
            "actual_original_source_native_read_status":
                "READ_ONLY_SOURCE_AND_INDEPENDENT_NATIVE_CATALOG_ORACLE_PASS",
            "original_native_product_count":len(allproducts),
            "original_native_product_class_by_guid":
                dict(sorted(allproducts.items())),
            "source_native_original_product_typed_XML_class_by_guid":
                dict(sorted(typed.items())),
            "original_product_guids_readonly_catalog_only":
                dict(sorted(omitted.items())),
            "original_products_not_in_typed_XML_count":len(omitted),
            "original_products_not_in_typed_XML_class_counts":
                dict(sorted(Counter(omitted.values()).items())),
            "original_readonly_catalog_contains_all_source_product_guids":True,
            "native_readonly_source_catalog_read_permission":"READ_ONLY_NO_COMPILER_AUTHORITY",
            "original_openings_demoted_due_to_real_native_host_extent":
                list(view.demoted_opening_guids),
            "original_dependant_fills_demoted_due_to_real_native_host_extent":
                list(view.demoted_fill_guids),
            "original_IFC_explicit_relation_edges_independently_checked":
                oracle["original_native_explicit_source_relationship_edges"],
            "original_native_geometry_status_counts":
                oracle["original_native_shape_evidence_status"],
            "independent_original_IFC_only_oracle_status":oracle["status"],
            "independent_original_IFC_only_oracle_sha256":sha256(
                json.dumps(oracle,sort_keys=True).encode("utf8")
            ).hexdigest(),
            "source_original_product_names_and_opaque_geometry_not_fabricated":True,
            "typed_read_source_IFC4X3_binder_strict_for_all_retained_nodes":
                source_schema=="IFC4X3",
            "typed_read_source_legacy_native_XSD_schema_checked":
                source_schema in ("IFC2X3","IFC4"),
            "no_new_IFC_native_product_writes_or_LLM_invocations":True,
            "original_all45_task_semantic_write_equivalence":False,
        }
    if _sha(original)!=sha:
        raise ValueError("ORIGINAL_PUBLIC_IFC_SOURCE_MODIFIED_DURING_READ")
    return structured


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-source",required=True,type=Path)
    p.add_argument("--original-sha256",required=True)
    a=p.parse_args()
    try:
        record=inspect(a.original_source.resolve(strict=True),
                       a.original_sha256)
        print(json.dumps({
            "status":"V013_ORIGINAL_SOURCE_READ_INDEPENDENTLY_VERIFIED",
            "inspection":record,
        },sort_keys=True))
    except Exception as e:
        # Do not leak private paths, IFC content or raw exception messages.
        print(json.dumps({
            "status":"V013_ORIGINAL_SOURCE_READ_FAIL_CLOSED",
            "failure_class":type(e).__name__,
        },sort_keys=True))
        raise SystemExit(3)


if __name__=="__main__":
    main()
