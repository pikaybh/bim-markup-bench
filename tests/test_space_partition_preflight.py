"""G1 #15: read-only native IFC4X3 SpaceBoundary surface reconciliation.

The positive source is the frozen, SHA-pinned public IFC *input*; generated
new walls remain in temporary directories. Never imports official GT or scorer.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from src.runtime.compiler import compile_declarative_xml
from src.runtime.space_partition_preflight import (
    UnsupportedSpacePartition,plan_rectangular_space_partition,
)
from tests.test_native_t_path_junction import authored_markup,_new_guid


def own_input_and_provisional_wall(folder:Path):
    source,refs,geom,xml=authored_markup()
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    output=folder/"provisional_unpartitioned.ifc"
    report=compile_declarative_xml(source,xml,output)
    assert [op.operation for op in report.operations]==[
        "CREATE_WALL","ADD_WALL_PATH_CONNECTION","ADD_WALL_PATH_CONNECTION"]
    return source,refs[2],_new_guid(before),output,before


class SourceSpacePartitionPreflightTests(unittest.TestCase):
    def test_real_public_input_all_seven_native_oriented_surfaces_accounted_for(self):
        with TemporaryDirectory(prefix="g1-source-only-space-preflight-") as d:
            source,room_guid,new_guid,output,sha=own_input_and_provisional_wall(Path(d))
            source_f=ifcopenshell.open(str(source))
            candidate_f=ifcopenshell.open(str(output))
            plan=plan_rectangular_space_partition(source_f,candidate_f,room_guid,new_guid)
            audit=plan.audit()
            self.assertEqual(audit["original_boundary_count"],7)
            self.assertEqual(audit["keep_near_count"],2)
            self.assertEqual(audit["rehome_far_count"],1)
            self.assertEqual(audit["split_both_count"],4)
            self.assertEqual(audit["required_new_partition_boundary_count"],2)
            self.assertEqual(audit["expected_total_boundary_count_after_split"],13)
            self.assertEqual(audit["original_room_volume_m3"],38.9375)
            self.assertEqual(audit["near_room_volume_m3"],29.066065)
            self.assertEqual(audit["far_room_volume_m3"],7.690935)
            self.assertEqual(audit["partition_wall_volume_m3"],2.1805)
            self.assertEqual(audit["near_room_bbox_min"],[.175,2.9,0.])
            self.assertEqual(audit["near_room_bbox_max"],[4.625,5.23275,2.8])
            self.assertEqual(audit["far_room_bbox_min"],[.175,5.40775,0.])
            self.assertEqual(audit["far_room_bbox_max"],[4.625,6.025,2.8])
            self.assertEqual(
                sorted((p.source_related_class,p.action,p.plane_axis)
                       for p in plan.boundary_patches),
                sorted((
                    ("VIRTUAL","KEEP_NEAR","y"),
                    ("IfcDoor","KEEP_NEAR","x"),
                    ("IfcWall","REHOME_FAR","y"),
                    ("IfcWall","SPLIT_BOTH","x"),
                    ("IfcWall","SPLIT_BOTH","x"),
                    ("IfcSlab","SPLIT_BOTH","z"),
                    ("IfcSlab","SPLIT_BOTH","z"),
                )))
            self.assertEqual([s[3] for s in plan.required_new_partition_surfaces],
                             [(0.,1.,0.),(0.,-1.,0.)])
            self.assertFalse(audit["native_ifc_writes_performed"])
            self.assertFalse(audit["new_ifc_space_boundaries_committed"])
            self.assertFalse(audit["official_task_succeeded"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_native_source_missing_boundary_surface_is_never_inferred(self):
        with TemporaryDirectory(prefix="g1-source-only-missing-surface-") as d:
            source,room,new_wall,output,original=own_input_and_provisional_wall(Path(d))
            f=ifcopenshell.open(str(source))
            rel=f.by_guid(room).BoundedBy[0]
            rel.ConnectionGeometry=None
            with self.assertRaisesRegex(UnsupportedSpacePartition,"no supported oriented surface"):
                plan_rectangular_space_partition(f,ifcopenshell.open(str(output)),room,new_wall)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)

    def test_reversed_source_surface_normal_denied(self):
        with TemporaryDirectory(prefix="g1-source-only-reversed-surface-") as d:
            source,room,new_wall,output,original=own_input_and_provisional_wall(Path(d))
            f=ifcopenshell.open(str(source))
            virtual=next(r for r in f.by_guid(room).BoundedBy
                         if str(r.PhysicalOrVirtualBoundary)=="VIRTUAL")
            curve=virtual.ConnectionGeometry.SurfaceOnRelatingElement.SweptCurve.Curve
            curve.Points=tuple(reversed(curve.Points))
            with self.assertRaisesRegex(UnsupportedSpacePartition,"outward-oriented"):
                plan_rectangular_space_partition(f,ifcopenshell.open(str(output)),room,new_wall)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)

    def test_partially_height_partition_wall_denied(self):
        with TemporaryDirectory(prefix="g1-source-only-partial-height-") as d:
            source,room,new_wall,output,original=own_input_and_provisional_wall(Path(d))
            candidate=ifcopenshell.open(str(output))
            wall=candidate.by_guid(new_wall)
            solid=wall.Representation.Representations[0].Items[0]
            self.assertTrue(solid.is_a("IfcExtrudedAreaSolid"))
            solid.Depth=float(solid.Depth)*0.5
            with self.assertRaisesRegex(UnsupportedSpacePartition,"full-width/full-height"):
                plan_rectangular_space_partition(ifcopenshell.open(str(source)),
                                                 candidate,room,new_wall)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)

    def test_invalid_boundary_relation_does_not_create_a_new_space(self):
        with TemporaryDirectory(prefix="g1-source-only-unsupported-physical-") as d:
            source,room,new_wall,output,original=own_input_and_provisional_wall(Path(d))
            f=ifcopenshell.open(str(source))
            virtual=next(r for r in f.by_guid(room).BoundedBy
                         if str(r.PhysicalOrVirtualBoundary)=="VIRTUAL")
            virtual.PhysicalOrVirtualBoundary="PHYSICAL"
            with self.assertRaisesRegex(UnsupportedSpacePartition,"Missing physical"):
                plan_rectangular_space_partition(f,ifcopenshell.open(str(output)),room,new_wall)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)


if __name__=="__main__":
    unittest.main()
