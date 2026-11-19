"""Independent I0 authoring versus D0 experimental typed-space IFC output.

Native-only comparison of actual IFC4X3 products, source/changed typed
relations, Psets and QTO attributes. No hidden GT, model API or official score.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import uuid

import ifcopenshell
import ifcopenshell.validate
import numpy as np

from src.runtime.binder import allocate_new_ifc_guid
from src.runtime.space_semantics_authoring_candidate import (
    compile_explicit_space_semantics_candidate,
)
from tests.test_space_semantics_v02_authoring import authored_new_space_metadata
from tests.test_declarative_space_partition_compiler import NEW_FAR_ID
from tests.test_native_t_path_junction import authored_markup
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report
from tests.oracles.python.independent_space_partition import (
    author_independent_space_partition,
)
from tests.oracles.python.independent_space_metadata_v02 import (
    independent_native_space_metadata,
)


def _typed_pset_qto_signature(native,source_guids):
    signature={}
    for space in native.by_type("IfcSpace"):
        links=[]
        for rel in space.IsTypedBy:
            t=rel.RelatingType
            links.append(("TYPE",rel.GlobalId,t.GlobalId,t.Name,
                          str(t.PredefinedType),tuple(sorted(
                              x.GlobalId for x in rel.RelatedObjects))))
        for rel in space.IsDefinedBy:
            definition=rel.RelatingPropertyDefinition
            if definition.is_a("IfcPropertySet"):
                properties=tuple(sorted((
                    x.Name,x.NominalValue.is_a(),
                    str(x.NominalValue.wrappedValue),str(x.Unit))
                    for x in definition.HasProperties))
                links.append(("PSET",rel.GlobalId,definition.GlobalId,
                              definition.Name,properties,tuple(sorted(
                                  x.GlobalId for x in rel.RelatedObjects))))
            elif definition.is_a("IfcElementQuantity"):
                quantities=tuple(sorted((
                    q.Name,q.is_a(),round(float(
                        q.AreaValue if q.is_a("IfcQuantityArea")
                        else q.VolumeValue),8)) for q in definition.Quantities))
                links.append(("QTO",rel.GlobalId,definition.GlobalId,
                              definition.Name,quantities,tuple(sorted(
                                  x.GlobalId for x in rel.RelatedObjects))))
            else:
                raise ValueError("Unknown native Space property definition")
        signature[space.GlobalId]=(space.Name,space.LongName,
                                   str(space.PredefinedType),
                                   str(space.CompositionType),
                                   tuple(sorted(links)))
    return signature


def independently_paired_v02_result():
    source,edited,observed,author=authored_new_space_metadata()
    _,refs,geom,_=authored_markup()
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    far_guid=allocate_new_ifc_guid(sha,"Space",NEW_FAR_ID,set())
    wall_guid=allocate_new_ifc_guid(sha,"Wall","g1_t_path_join_manual",set())
    with TemporaryDirectory(prefix="v02-independent-native-pair-") as td:
        tmp=Path(td)
        d0=tmp/"D0.ifc"
        iwall=tmp/"I0_wall.ifc"
        ijoin=tmp/"I0_joined.ifc"
        isplit=tmp/"I0_partitioned.ifc"
        i0=tmp/"I0_typed.ifc"
        dresult=compile_explicit_space_semantics_candidate(
            source,edited,observed,author,d0)
        manual_ifc_reference(
            source,iwall,"CREATE_WALL",
            new_guid=wall_guid,storey_guid=geom["storey_guid"],
            start=tuple(float(x) for x in geom["start"]),
            end=tuple(float(x) for x in geom["end"]),
            height=float(geom["height"]),thickness=float(geom["thickness"]))
        f=ifcopenshell.open(str(iwall))
        for host,endpoint in zip(refs[:2],("ATSTART","ATEND")):
            identity=f"connect-v0.1:{sha}:{host}:{wall_guid}"
            id_=ifcopenshell.guid.compress(uuid.uuid5(
                uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111"),
                identity).hex)
            f.createIfcRelConnectsPathElements(
                GlobalId=id_,RelatingElement=f.by_guid(host),
                RelatedElement=f.by_guid(wall_guid),
                RelatingConnectionType="ATPATH",
                RelatedConnectionType=endpoint,
                RelatingPriorities=(),RelatedPriorities=())
        f.write(str(ijoin))
        author_independent_space_partition(
            ijoin,isplit,source_sha=sha,
            source_space_guid=refs[2],new_wall_guid=wall_guid,
            new_space_guid=far_guid)
        independently_authored_ids=independent_native_space_metadata(
            isplit,i0,sha,far_guid,name="135",long_name="pilotroom",
            type_name="pilotroom 135:explicit partition",
            reference="pilotroom 135",
            net_area=2.7467625,net_volume=7.690935)
        cmp=parity_report(d0,i0)
        if not cmp["parity"]:
            raise ValueError(f"I0/D0 native comparison failed: {cmp}")
        a=ifcopenshell.open(str(d0));b=ifcopenshell.open(str(i0))
        expected=_typed_pset_qto_signature(a,refs)
        actual=_typed_pset_qto_signature(b,refs)
        if expected!=actual:
            raise ValueError("I0/D0 native type/Pset/QTO relations differ")
        source_native=ifcopenshell.open(str(source))
        source_signature=_typed_pset_qto_signature(source_native,refs)
        observed_old={x.GlobalId:source_signature[x.GlobalId]
                      for x in source_native.by_type("IfcSpace")}
        if any(expected[k]!=v for k,v in observed_old.items()):
            raise ValueError("Source room type/Pset/QTO metadata was changed")
        if len(a.by_guid(far_guid).IsTypedBy)!=1 or len(
                a.by_guid(far_guid).IsDefinedBy)!=3:
            raise ValueError("Authored metadata is not attached to far Space")
        # Compare actual IFC schema diagnostics with original source, not
        # just the six-category native semantic comparator (which omits QTO).
        issues={}
        for label,path in (("original",source),("D0",d0),("I0",i0)):
            logger=ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(str(path),logger,
                                          express_rules=False)
            issues[label]=Counter((
                str(entry.get("type")),str(entry.get("attribute")),
                str(entry.get("message")))
                for entry in logger.statements if entry.get("level")=="error")
        for label in ("D0","I0"):
            if any(count>issues["original"][key]
                   for key,count in issues[label].items()):
                raise ValueError("New IFC schema error introduced by typed Space authoring")
        report={
            "status":"PASS_EXPERIMENTAL_D0_I0_NATIVE_TYPED_SPACE_PARITY_NOT_OFFICIAL",
            "source_sha256":sha,
            "declarative_result_sha256":hashlib.sha256(d0.read_bytes()).hexdigest(),
            "imperative_result_sha256":hashlib.sha256(i0.read_bytes()).hexdigest(),
            "native_independent_six_category_parity":cmp["parity"],
            "native_all_space_type_pset_qto_relation_parity":expected==actual,
            "native_source_space_metadata_preserved":True,
            "original_ifc_schema_error_count":sum(issues["original"].values()),
            "declarative_ifc_schema_error_count":sum(issues["D0"].values()),
            "imperative_ifc_schema_error_count":sum(issues["I0"].values()),
            "introduced_ifc_schema_error_categories":0,
            "new_space_type_relation_count":len(a.by_guid(far_guid).IsTypedBy),
            "new_space_pset_and_qto_relation_count":len(a.by_guid(far_guid).IsDefinedBy),
            "new_source_metadata_guids_identical":True,
            "new_metadata_root_guid_count":len(independently_authored_ids),
            "model_facing_v02_promoted":False,
            "original_v01_schema_changed":False,
            "source_ifc_modified":hashlib.sha256(source.read_bytes()).hexdigest()!=sha,
            "official_tasks_scored":0,
            "model_calls":0,
        }
    return report


class IndependentTypedSpaceMetadataPairTests(unittest.TestCase):
    def test_full_independently_authored_native_metadata_pair(self):
        report=independently_paired_v02_result()
        self.assertTrue(report["native_independent_six_category_parity"])
        self.assertTrue(report["native_all_space_type_pset_qto_relation_parity"])
        self.assertEqual(report["new_metadata_root_guid_count"],8)
        self.assertFalse(report["source_ifc_modified"])
        self.assertEqual(report["official_tasks_scored"],0)
        self.assertFalse(report["model_facing_v02_promoted"])


if __name__=="__main__":
    unittest.main()
