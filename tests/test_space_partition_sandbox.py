"""G1: bounded in-memory Space split proof. Does not expose an XML API.

The source is a pinned public IFC *input*; the split output is created and
reopened ONLY in a TemporaryDirectory. This is not an I0/D0 paired oracle
for spatial partitioning, official evaluation or a scored task success.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell
import numpy as np

from src.runtime.space_partition_preflight import (
    UnsupportedSpacePartition,plan_rectangular_space_partition,
    _surface_polygon,_exact_box,
)
from src.runtime.space_partition_sandbox import sandbox_native_space_split
from tests.test_space_partition_preflight import own_input_and_provisional_wall


def _assert_surface(test,space,rel,low,high,normal):
    current_min,current_max,axis,direction=_surface_polygon(space,rel)
    test.assertTrue(np.allclose(current_min,low,atol=1e-6,rtol=0),
                    msg=f"Boundary minimum changed: {current_min} expected {low}")
    test.assertTrue(np.allclose(current_max,high,atol=1e-6,rtol=0))
    test.assertTrue(np.allclose(direction,normal,atol=1e-6,rtol=0))


def _run_split(temp_dir:Path):
    source,room_guid,new_wall_guid,joined,sha=own_input_and_provisional_wall(temp_dir)
    original=ifcopenshell.open(str(source))
    candidate=ifcopenshell.open(str(joined))
    plan=plan_rectangular_space_partition(original,candidate,room_guid,new_wall_guid)
    report=sandbox_native_space_split(candidate,plan,source_sha=sha)
    destination=temp_dir/"native_space_split.ifc"
    candidate.write(str(destination))
    return source,joined,destination,plan,report,sha


class NativeBoundedSpaceSplitTests(unittest.TestCase):
    def test_source_only_native_space_rebuild_after_save_and_reopen(self):
        with TemporaryDirectory(prefix="g1-sandbox-spatial-reconciliation-") as td:
            source,joined,destination,plan,report,sha=_run_split(Path(td))
            f=ifcopenshell.open(str(destination))
            base=ifcopenshell.open(str(joined))
            orig=ifcopenshell.open(str(source))
            original_space=orig.by_guid(plan.existing_space_id)
            near=f.by_guid(plan.existing_space_id)
            far=f.by_guid(report["new_space_guid"])
            wall=f.by_guid(plan.new_wall_id)
            self.assertTrue(all(x is not None for x in (near,far,wall)))
            self.assertEqual(len(f.by_type("IfcSpace")),len(base.by_type("IfcSpace"))+1)
            self.assertTrue(report["source_space_id_preserved"])
            self.assertFalse(report["compiler_or_llm_interface_exposed"])
            self.assertEqual(len(near.BoundedBy),7)
            self.assertEqual(len(far.BoundedBy),6)
            self.assertTrue(np.allclose(_exact_box(near,kind="IfcSpace")[0],plan.near_box_min,atol=1e-6))
            self.assertTrue(np.allclose(_exact_box(near,kind="IfcSpace")[1],plan.near_box_max,atol=1e-6))
            self.assertTrue(np.allclose(_exact_box(far,kind="IfcSpace")[0],plan.far_box_min,atol=1e-6))
            self.assertTrue(np.allclose(_exact_box(far,kind="IfcSpace")[1],plan.far_box_max,atol=1e-6))
            before_relation_ids={r.GlobalId for r in base.by_type("IfcRelSpaceBoundary")}
            current_relation_ids={r.GlobalId for r in f.by_type("IfcRelSpaceBoundary")}
            self.assertTrue(before_relation_ids.issubset(current_relation_ids))
            self.assertEqual(len(current_relation_ids-before_relation_ids),6)
            self.assertEqual(len(report["added_boundary_guids"]),6)
            self.assertEqual(set(report["added_boundary_guids"]),
                             current_relation_ids-before_relation_ids)
            for patch in plan.boundary_patches:
                original=f.by_guid(patch.boundary_id)
                self.assertIsNotNone(original)
                original_rel=orig.by_guid(patch.boundary_id)
                self.assertEqual(
                    original.RelatedBuildingElement.GlobalId if original.RelatedBuildingElement else None,
                    original_rel.RelatedBuildingElement.GlobalId if original_rel.RelatedBuildingElement else None)
                if patch.action=="KEEP_NEAR":
                    self.assertEqual(original.RelatingSpace.GlobalId,near.GlobalId)
                    _assert_surface(self,near,original,
                                    patch.original_extent_min,patch.original_extent_max,patch.normal)
                elif patch.action=="REHOME_FAR":
                    self.assertEqual(original.RelatingSpace.GlobalId,far.GlobalId)
                    _assert_surface(self,far,original,
                                    patch.original_extent_min,patch.original_extent_max,patch.normal)
                else:
                    self.assertEqual(patch.action,"SPLIT_BOTH")
                    self.assertEqual(original.RelatingSpace.GlobalId,near.GlobalId)
                    _assert_surface(self,near,original,
                                    patch.near_extent_min,patch.near_extent_max,patch.normal)
                    newly=[r for r in far.BoundedBy
                           if r.GlobalId in report["added_boundary_guids"]
                           and r.RelatedBuildingElement
                           and r.RelatedBuildingElement.GlobalId==
                           original.RelatedBuildingElement.GlobalId]
                    self.assertEqual(len(newly),1)
                    _assert_surface(self,far,newly[0],
                                    patch.far_extent_min,patch.far_extent_max,patch.normal)
                    self.assertEqual(str(newly[0].PhysicalOrVirtualBoundary),"PHYSICAL")
            for label,min_pt,max_pt,normal in plan.required_new_partition_surfaces:
                space=near if label=="NEAR_PARTITION_FACE" else far
                joins=[r for r in space.BoundedBy
                       if r.RelatedBuildingElement
                       and r.RelatedBuildingElement.GlobalId==wall.GlobalId]
                self.assertEqual(len(joins),1)
                self.assertEqual(str(joins[0].PhysicalOrVirtualBoundary),"PHYSICAL")
                self.assertEqual(str(joins[0].InternalOrExternalBoundary),"INTERNAL")
                _assert_surface(self,space,joins[0],min_pt,max_pt,normal)
            # The other source Space and its six original boundary *identities*
            # were never changed, moved or accidentally assigned to the new Space.
            other_space=next(sp for sp in orig.by_type("IfcSpace")
                             if sp.GlobalId!=plan.existing_space_id)
            out_other=f.by_guid(other_space.GlobalId)
            self.assertEqual({r.GlobalId for r in other_space.BoundedBy},
                             {r.GlobalId for r in out_other.BoundedBy})
            self.assertTrue(np.allclose(_exact_box(out_other,kind="IfcSpace")[0],
                                        _exact_box(other_space,kind="IfcSpace")[0],atol=1e-6))
            # Input source original remains immutable; no output IFC is committed.
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_split_preview_is_projectable_and_unedited_xml_roundtrips(self):
        from src.runtime.ifc_projection import project_ifc
        from src.runtime.xml_parser import parse_xml
        from src.runtime.binder import bind_document
        from src.runtime.compiler import compile_declarative_xml
        with TemporaryDirectory(prefix="g1-split-xml-projection-sanity-") as td:
            source,joined,destination,plan,report,sha=_run_split(Path(td))
            saved_bytes=destination.read_bytes()
            projected=project_ifc(destination)
            parsed=parse_xml(projected.xml)
            self.assertEqual(sum(x.kind=="Space" for x in parsed.elements),3)
            self.assertEqual(sum(x.kind=="SpaceBoundary" for x in parsed.relations),10)
            binding=bind_document(parsed,projection=projected)
            self.assertTrue(binding.report()["all_ifc_relation_contracts_satisfied"])
            unchanged=Path(td)/"preview_unchanged_roundtrip.ifc"
            result=compile_declarative_xml(destination,projected.xml,unchanged)
            self.assertEqual(result.operations,())
            self.assertEqual(unchanged.read_bytes(),saved_bytes)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_saved_native_schema_validation_does_not_add_new_error_categories(self):
        from collections import Counter
        import ifcopenshell.validate
        with TemporaryDirectory(prefix="g1-native-split-schema-") as td:
            source,joined,destination,plan,report,sha=_run_split(Path(td))
            errors={}
            for label,path in (("source",source),("split",destination)):
                log=ifcopenshell.validate.json_logger()
                ifcopenshell.validate.validate(str(path),log,express_rules=False)
                errors[label]=Counter((e.get("type"),e.get("attribute"),e.get("message"))
                                      for e in log.statements if e.get("level")=="error")
            self.assertTrue(errors["split"])
            for category,count in errors["split"].items():
                self.assertLessEqual(count,errors["source"][category],
                                     msg=f"New IFC schema error category: {category}")
            # Source IFC already has invalid missing virtual boundary elements
            # and unset plane InnerBoundaries. The native sandbox prototype
            # does not claim fully valid IFC until source defects are handled.
            self.assertEqual(sum(errors["source"].values()),6)
            self.assertEqual(sum(errors["split"].values()),4)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_tampered_or_stale_space_plan_is_rejected_before_ifc_mutation(self):
        with TemporaryDirectory(prefix="g1-reject-stale-partition-") as td:
            source,room,new_wall,joined,sha=own_input_and_provisional_wall(Path(td))
            f=ifcopenshell.open(str(joined))
            plan=plan_rectangular_space_partition(ifcopenshell.open(str(source)),
                                                  f,room,new_wall)
            before_space_count=len(f.by_type("IfcSpace"))
            broken=replace(plan,near_box_max=(4.625,5.1,2.8))
            with self.assertRaisesRegex(UnsupportedSpacePartition,"stale or forged"):
                sandbox_native_space_split(f,broken,source_sha=sha)
            self.assertEqual(len(f.by_type("IfcSpace")),before_space_count)
            self.assertEqual(len(f.by_type("IfcRelSpaceBoundary")),13)

    def test_save_reopen_retains_preexisting_type_and_virtual_boundary(self):
        with TemporaryDirectory(prefix="g1-verify-source-semantics-") as td:
            source,joined,destination,plan,report,sha=_run_split(Path(td))
            baseline=ifcopenshell.open(str(source))
            output=ifcopenshell.open(str(destination))
            prior=baseline.by_guid(plan.existing_space_id)
            saved=output.by_guid(plan.existing_space_id)
            self.assertEqual({x.GlobalId for x in prior.IsTypedBy},
                             {x.GlobalId for x in saved.IsTypedBy})
            self.assertEqual({x.GlobalId for x in prior.IsDefinedBy},
                             {x.GlobalId for x in saved.IsDefinedBy})
            virtual=[rel for rel in saved.BoundedBy
                     if str(rel.PhysicalOrVirtualBoundary)=="VIRTUAL"]
            self.assertEqual(len(virtual),1)
            self.assertIsNone(virtual[0].RelatedBuildingElement)
            original_virtual=next(r for r in prior.BoundedBy
                                  if str(r.PhysicalOrVirtualBoundary)=="VIRTUAL")
            self.assertEqual(virtual[0].GlobalId,original_virtual.GlobalId)
            # A new Space has not been assigned an independently justified
            # type/quantity/Pset identity. This is why full-task status BLOCKS.
            far=output.by_guid(report["new_space_guid"])
            self.assertEqual(len(far.IsTypedBy),0)
            self.assertEqual(len(far.IsDefinedBy),0)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)


if __name__=="__main__":
    unittest.main()
