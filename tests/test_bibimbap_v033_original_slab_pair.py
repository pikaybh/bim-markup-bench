"""v0.33 original-public Slab CREATE D0/I0 native and negative controls.

This suite evaluates nonblinded developer native feasibility, not LLM scoring.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.util.unit
import numpy as np

from tools import audit_bibimbap_v033_original_slab_pair as audit
from tools import bibimbap_v033_original_slab_i0 as i0
from tools.bibimbap_matched25_tools import file_hash

BASE = Path(os.environ.get(
    "BIBIMBAP_EXPERIMENT_BASE", r"D:\\문서\\D__1_Projects\\202611"
))
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
SOURCE=DATA/"ifc"/"basic_tasks.ifc"
REPORT=audit.ROOT/"reports"/"bibimbap_v033_original_test02_slab_D0_I0_semantic_pair_20261117.json"
REPORT_SHA="998064e23a0b3955b20a0ca1a7cabcb4424a612af1d633e42cd179f5e68ce660"


class V033OriginalSlabPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=json.loads(REPORT.read_text(encoding="utf8"))

    def setUp(self):
        work=tempfile.TemporaryDirectory(prefix="bmb-v033-unit-")
        self.addCleanup(work.cleanup)
        self.work=Path(work.name)

    def test_01_exact_original_population_and_question(self):
        r=self.frozen
        self.assertEqual(r["original_public45_denominator_unchanged"],45)
        self.assertEqual(r["original_public_test_id"],"test_02")
        self.assertEqual(r["original_public_question_sha256"],audit.QUESTION_SHA)
        self.assertEqual(r["original_public_source_ifc_sha256"],i0.SOURCE_SHA)
        self.assertEqual(r["predeclared_public_slab_xyz_dimensions_thickness_m"],
                         [-35.,-2.5,0.,10.,5.,.2])

    def test_02_create_semantic_not_byte_or_causal_result(self):
        r=self.frozen
        self.assertFalse(r["native_entire_D0_I0_IFC_byte_equal"])
        self.assertEqual(r["prior_11_original_native_full_IFC_byte_equal_developer_cases_unchanged"],11)
        self.assertEqual(r["new_original_native_full_IFC_byte_equal_developer_cases"],11)
        self.assertEqual(r["original_CREATE_semantic_only_developer_pairs_after_v033"],2)
        self.assertEqual(r["original_CREATE_cases_without_test_specific_semantic_pair"],13)
        self.assertEqual(r["original45_full_source_information_equivalence_proven"],0)
        self.assertEqual(r["original45_full_native_write_capability_equivalence_proven"],0)
        self.assertEqual(r["matched_real_D_I_LLM_trials"],0)
        self.assertEqual(r["paid_model_requests"],0)
        self.assertFalse(r["causal_source_representation_effect_claim_permitted"])

    def test_03_actual_original_author_both_arms_scored_after_native_checks(self):
        a=self.frozen["original_author_D0_score"]
        b=self.frozen["original_author_I0_score"]
        self.assertEqual(a,b)
        self.assertEqual(a["status"],"AUTHOR_SCORED")
        self.assertEqual(a["original_author_score"],1.)
        self.assertEqual(a["original_author_metrics"],{
            "object_exists":1.,"right_location":1.,
            "right_dimensions":1.,"integrity_constraint":1.,
        })
        self.assertTrue(a["original_author_full_mark"])

    def test_04_existing_native_scene_preserved(self):
        r=self.frozen["native_independent_slab_verification_both_arms"]
        self.assertEqual(r["original_native_root_count"],358)
        self.assertEqual(r["original_native_product_count"],43)
        self.assertEqual(r["original_native_product_world_shapes_verified"],39)
        self.assertEqual(r["original_native_products_without_shape"],4)
        self.assertEqual(r["native_new_slab_bbox_m"],
                         [-35.,-2.5,0.,-25.,2.5,.2])
        self.assertEqual(r["native_new_slab_extrusion_thickness_mm"],200.)
        self.assertEqual(r["new_native_slab_PredefinedType"],"FLOOR")
        self.assertTrue(r["all_original_product_native_world_shapes_preserved"])
        self.assertTrue(r["all_original_product_native_world_triangle_meshes_preserved"])
        self.assertEqual(r["original_product_triangle_faces_independently_compared"],1652)
        self.assertTrue(r["original_storey_L1_containment_preserved_extended_by_one"])

    def test_05_pinned_raw_and_previous_reports_unchanged(self):
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)
        self.assertEqual(file_hash(REPORT),REPORT_SHA)
        for p,digest in (audit.REPORT_V031,audit.REPORT_V032,audit.REPORT_HISTORICAL_D0):
            self.assertEqual(file_hash(audit.ROOT/p),digest)

    def test_06_standalone_I0_writer_never_imports_D0_or_author_grader(self):
        code=Path(i0.__file__).read_text(encoding="utf8")
        tree=ast.parse(code)
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module:
                imports.append(node.module)
            if isinstance(node,ast.Import):
                imports.extend(x.name for x in node.names)
        forbidden=("experimental_v4","ifc_projection","xml_parser","binder",
                   "matched25_cli","grade_author","author_worker",
                   "original_slab_translate","audit_bibimbap_v033")
        self.assertFalse([m for m in imports if any(x in m for x in forbidden)])
        self.assertEqual(i0.SPEC_METRES,(-35.,-2.5,0.,10.,5.,.2))

    def test_07_native_I0_creates_actual_original_IFC(self):
        before=file_hash(SOURCE)
        output=self.work/"new_slab.ifc"
        r=i0.create_independent_original_test02_i0(SOURCE,output)
        self.assertEqual(r["candidate_original_mm_ifc_sha256"],file_hash(output))
        check=audit.verify_original_native_slab_create(
            SOURCE,output,expected_new_guid=r["new_native_slab_guid"])
        self.assertEqual(check["native_new_slab_bbox_m"],list(i0.EXPECTED_BBOX_METRES))
        self.assertEqual(file_hash(SOURCE),before)

    def test_08_i0_rejects_mutated_source(self):
        bad=self.work/"tampered.ifc"
        shutil.copy2(SOURCE,bad)
        bad.write_bytes(bad.read_bytes()+b" ")
        out=self.work/"must_not_create.ifc"
        with self.assertRaisesRegex(i0.NativePublicSlabI0Blocked,"SHA mismatch"):
            i0.create_independent_original_test02_i0(bad,out)
        self.assertFalse(out.exists())

    def test_09_i0_rejects_existing_candidate_path(self):
        path=self.work/"existing.ifc"
        path.write_bytes(b"KEEP")
        with self.assertRaisesRegex(i0.NativePublicSlabI0Blocked,"output fresh"):
            i0.create_independent_original_test02_i0(SOURCE,path)
        self.assertEqual(path.read_bytes(),b"KEEP")

    def test_10_i0_rejects_source_as_destination(self):
        with self.assertRaisesRegex(i0.NativePublicSlabI0Blocked,"output fresh"):
            i0.create_independent_original_test02_i0(SOURCE,SOURCE)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_11_native_oracle_rejects_no_new_slab(self):
        unchanged=self.work/"unchanged.ifc"
        shutil.copy2(SOURCE,unchanged)
        with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,"Exactly one new native IFC product"):
            audit.verify_original_native_slab_create(SOURCE,unchanged)

    def test_12_native_oracle_rejects_false_new_GUID(self):
        out=self.work/"real.ifc"
        i0.create_independent_original_test02_i0(SOURCE,out)
        with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,"writer claim"):
            audit.verify_original_native_slab_create(
                SOURCE,out,expected_new_guid="0"*22)

    def test_13_native_oracle_rejects_wrong_slab_position(self):
        out=self.work/"shifted.ifc"
        s=i0.create_independent_original_test02_i0(SOURCE,out)
        native=ifcopenshell.open(str(out))
        metres=ifcopenshell.util.unit.convert_file_length_units(native,"METER")
        slab=metres.by_guid(s["new_native_slab_guid"])
        moved=np.eye(4)
        moved[:3,3]=[-25.,0.,0.]
        ifcopenshell.api.geometry.edit_object_placement(
            metres,product=slab,matrix=moved)
        ifcopenshell.util.unit.convert_file_length_units(
            metres,"MILLIMETER").write(str(out))
        with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,"physical.*geometry|Physical slab geometry"):
            audit.verify_original_native_slab_create(SOURCE,out)

    def test_14_native_oracle_rejects_wrong_footprint_or_thickness(self):
        out=self.work/"wrong_size.ifc"
        s=i0.create_independent_original_test02_i0(SOURCE,out)
        native=ifcopenshell.open(str(out))
        slab=native.by_guid(s["new_native_slab_guid"])
        solid=next(x for rep in slab.Representation.Representations
                   for x in rep.Items if x.is_a("IfcExtrudedAreaSolid"))
        solid.Depth=125.0
        native.write(str(out))
        with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,"200 mm"):
            audit.verify_original_native_slab_create(SOURCE,out)

    def test_15_pinned_prior_report_tampering_blocks_audit(self):
        bogus=self.work/"reports"
        bogus.mkdir()
        report=bogus/Path(audit.REPORT_V032[0]).name
        report.write_bytes(b"altered")
        with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,"pinned|Pinned"):
            audit._pinned_json(self.work,audit.REPORT_V032)

    def test_16_independent_author_score_spoof_is_refused(self):
        from tools import bibimbap_matched25_cli as grader
        with patch.object(grader,"grade_author",return_value={
            "status":"AUTHOR_SCORED","original_author_score":.5,
            "original_author_full_mark":False,"original_author_metrics":{},
        }):
            with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,
                                        "scores unequal or not full"):
                audit.audit_original_public_test02(audit.ROOT,AUTHOR,DATA)

    def test_17_actual_original_pair_replay_invariants_hold(self):
        second=audit.audit_original_public_test02(audit.ROOT,AUTHOR,DATA)
        self.assertEqual(second["native_independent_slab_verification_both_arms"],
                         self.frozen["native_independent_slab_verification_both_arms"])
        self.assertEqual(second["original_author_D0_score"],
                         self.frozen["original_author_D0_score"])
        self.assertEqual(second["original_author_I0_score"],
                         self.frozen["original_author_I0_score"])
        self.assertEqual(second["native_entire_D0_I0_IFC_byte_equal"],False)
        self.assertEqual(file_hash(SOURCE),i0.SOURCE_SHA)

    def test_19_mesh_triangle_fingerprint_drift_rejected_even_when_bbox_matches(self):
        output=self.work/"created_native.ifc"
        i0.create_independent_original_test02_i0(SOURCE,output)
        original=audit._original_product_world_mesh_fingerprints
        call_count=[0]
        def changed_candidate_meshes(model):
            call_count[0]+=1
            signatures=original(model)
            if call_count[0]==2:
                first=next(g for g,v in signatures.items() if v[1])
                class_name,had_rep,_,count=signatures[first]
                signatures[first]=(class_name,had_rep,"f"*64,count)
            return signatures
        with patch.object(audit,"_original_product_world_mesh_fingerprints",
                          side_effect=changed_candidate_meshes):
            with self.assertRaisesRegex(audit.OriginalSlabV033Blocked,
                                        "world-space triangle mesh changed"):
                audit.verify_original_native_slab_create(SOURCE,output)

    def test_18_no_hidden_answers_or_source_IFC_serialized(self):
        output=REPORT.read_text(encoding="utf8").lower()
        for forbidden in ("hidden_target","ground_truth","full_prompt_body",
                          "original_public_question_text","private_target_guid",
                          "grader_secret","credential"):
            self.assertNotIn(forbidden,output)
        self.assertLess(REPORT.stat().st_size,16000)


if __name__=="__main__":
    unittest.main()
