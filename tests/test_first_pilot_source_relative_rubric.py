"""Independent source-relative native rubric: real IFC positive/negative tests.

Every grader input comes ONLY from pinned public instruction + original IFC
and ephemeral developer-authored D0/I0 IFC. No reference/GT IFC and no LLM.
The rubric is post-hoc engineering validation; not an official task result.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from src.evaluation.three_case_source_rubric import (
    SourceRubricBlocked, score_source_relative,
)
from tools.verify_prompt_grounded_window_pair import verify_prompt_grounded_window_pair
from tools.verify_prompt_grounded_spatial_wall import verify_prompt_grounded_spatial_wall
from tools.verify_public_door_delete_gate import verify_public_door_delete_gate
from tools.verify_prompt_grounded_window_pair import verified_public_task_and_source
from tools.verify_prompt_grounded_spatial_wall import verified_public_input
from tools.verify_public_door_delete_gate import verified_public_source


class NativeSourceRelativeRubricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=TemporaryDirectory(prefix="g1-independent-rubric-")
        base=Path(cls.tmp.name)
        cls.source={}
        cls.public={}
        cls.candidates={}
        cls.positives={}

        def paired(case):
            def evaluate(source,d0,i0,prompt):
                cls.source[case]=source
                cls.public[case]=prompt
                for arm,filename in (("D0",d0),("I0",i0)):
                    copy=base / f"{case}-{arm}.ifc"
                    shutil.copyfile(filename,copy)
                    cls.candidates[(case,arm)]=copy
                    cls.positives[(case,arm)]=score_source_relative(
                        case,source,copy,prompt)
                return {"rubric_is_external_to_model":True}
            return evaluate
        verify_prompt_grounded_window_pair(
            physical_observer=paired("WIN-UPD-DIR-A-002"))
        verify_prompt_grounded_spatial_wall(
            physical_observer=paired("WAL-CRE-SPA-A-003"))

        def door_check(source,candidate,prompt):
            case="DOR-DEL-DIR-A-001"
            cls.source[case]=source
            cls.public[case]=prompt
            arm="D0" if (case,"D0") not in cls.candidates else "I0"
            copy=base / f"{case}-{arm}.ifc"
            shutil.copyfile(candidate,copy)
            cls.candidates[(case,arm)]=copy
            cls.positives[(case,arm)]=score_source_relative(
                case,source,copy,prompt)
            return {"rubric_is_external_to_model":True}
        verify_public_door_delete_gate(spatial_observer=door_check)
        cls.source_digests={
            c:sha256(p.read_bytes()).hexdigest() for c,p in cls.source.items()
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _check(self,case,arm="D0",candidate=None,prompt=None,source=None):
        return score_source_relative(
            case,source or self.source[case],
            candidate or self.candidates[(case,arm)],
            prompt if prompt is not None else self.public[case])

    def _corrupt(self,case,mutate,arm="D0"):
        with TemporaryDirectory(prefix="g1-corrupt-native-") as td:
            file=Path(td)/"tampered.ifc"
            model=ifcopenshell.open(str(self.candidates[(case,arm)]))
            mutate(model)
            model.write(str(file))
            with self.assertRaises(SourceRubricBlocked):
                self._check(case,arm,candidate=file)

    def test_all_six_independent_real_ifc_results_pass_bounded_rubric(self):
        self.assertEqual(len(self.positives),6)
        for (case,arm),r in self.positives.items():
            with self.subTest(case=case,arm=arm):
                self.assertEqual(r["case"],case)
                self.assertEqual(r["metric_origin"],"surrogate")
                self.assertTrue(r["source_relative_native_checks_pass"])
                self.assertFalse(r["full_instruction_specific_task_success_approved"])
                self.assertFalse(r["benchmark_author_evaluator_used"])
                self.assertFalse(r["original_ifc_model_rights_cleared"])
                self.assertTrue(r["posthoc_developed_not_preregistered"])
                self.assertFalse(r["candidate_origin_verified_by_grader"])
                self.assertFalse(r["grader_itself_called_model_provider"])
                self.assertEqual(r["grader_provider_calls"],0)
                self.assertIsNone(r["official_bim_edit_score"])
                self.assertEqual(r["candidate_ifc_sha256"],
                                 sha256(self.candidates[(case,arm)].read_bytes()).hexdigest())

    def test_window_d0_i0_have_identical_output_and_source_relative_scores(self):
        case="WIN-UPD-DIR-A-002"
        self.assertEqual(self.positives[(case,"D0")]["candidate_ifc_sha256"],
                         self.positives[(case,"I0")]["candidate_ifc_sha256"])
        self.assertEqual(self.positives[(case,"D0")]["source_only_criterion"],
                         "WORLD_TRANSLATION_AND_PRESERVED_SEMANTICS")

    def test_wall_native_pair_independently_scores_path_joins(self):
        case="WAL-CRE-SPA-A-003"
        self.assertEqual(self.positives[(case,"D0")]["source_only_criterion"],
                         "WALL_GEOMETRY_AND_TWO_JOINS_NO_UNREQUESTED_ROOT_CHANGE")
        self.assertEqual(self.positives[(case,"D0")]["unresolved_full_task_condition"],
                         "ROOM_PARTITION_AND_METADATA_NOT_ORACLE_PROVEN")

    def test_door_native_pair_independently_scores_dependency_cleanup(self):
        case="DOR-DEL-DIR-A-001"
        self.assertEqual(self.positives[(case,"D0")]["source_only_criterion"],
                         "TEN_NATIVE_ROOT_DELETIONS_AND_UNRELATED_MESH_PRESERVATION")
        self.assertEqual(self.positives[(case,"D0")]["unresolved_full_task_condition"],
                         "UNMENTIONED_BOUNDARY_POLICY_AND_ABSENT_OPENING_STOREY_UNKNOWN")

    def test_noop_ifc_fails_all_three_rubrics(self):
        for case in self.source:
            with self.subTest(case=case):
                with TemporaryDirectory(prefix="g1-noop-rubric-") as td:
                    no_op=Path(td)/"unchanged.ifc"
                    shutil.copyfile(self.source[case],no_op)
                    with self.assertRaises(SourceRubricBlocked):
                        self._check(case,candidate=no_op)

    def test_window_wrong_world_move_is_rejected(self):
        case="WIN-UPD-DIR-A-002"
        def modify(model):
            opening=next(x for x in model.by_type("IfcOpeningElement"))
            point=opening.ObjectPlacement.RelativePlacement.Location
            coords=list(point.Coordinates)
            coords[0]+=0.4
            point.Coordinates=coords
        self._corrupt(case,modify)

    def test_window_extra_unrelated_product_is_rejected(self):
        case="WIN-UPD-DIR-A-002"
        def modify(model):
            model.create_entity("IfcWall",GlobalId=ifcopenshell.guid.new())
        self._corrupt(case,modify)

    def test_wall_missing_one_path_join_is_rejected(self):
        case="WAL-CRE-SPA-A-003"
        def modify(model):
            model.remove(model.by_type("IfcRelConnectsPathElements")[0])
        self._corrupt(case,modify)

    def test_wall_wrong_thickness_is_rejected(self):
        case="WAL-CRE-SPA-A-003"
        source=ifcopenshell.open(str(self.source[case]))
        baseline={x.GlobalId for x in source.by_type("IfcWall")}
        def modify(model):
            new_wall=next(x for x in model.by_type("IfcWall")
                          if x.GlobalId not in baseline)
            shape=new_wall.Representation.Representations[0].Items[0]
            # Change native sweep depth, altering the checked product bbox.
            shape.Depth=float(shape.Depth)*0.72
        self._corrupt(case,modify)

    def test_door_missing_actual_delete_is_rejected(self):
        case="DOR-DEL-DIR-A-001"
        with TemporaryDirectory(prefix="g1-door-noop-") as td:
            unchanged=Path(td)/"unchanged.ifc"
            shutil.copyfile(self.source[case],unchanged)
            with self.assertRaises(SourceRubricBlocked):
                self._check(case,candidate=unchanged)

    def test_door_added_unrelated_ifc_root_rejected(self):
        case="DOR-DEL-DIR-A-001"
        def modify(model):
            model.create_entity("IfcWall",GlobalId=ifcopenshell.guid.new())
        self._corrupt(case,modify)

    def test_public_instruction_modified_rejected_for_each_case(self):
        for case in self.source:
            with self.subTest(case=case):
                with self.assertRaisesRegex(SourceRubricBlocked,
                                            "instruction changed"):
                    self._check(case,prompt=self.public[case]+" extra")

    def test_cross_task_case_substitution_refused(self):
        with self.assertRaises(SourceRubricBlocked):
            score_source_relative("WIN-UPD-DIR-A-002",
                self.source["WAL-CRE-SPA-A-003"],
                self.candidates[("WAL-CRE-SPA-A-003","D0")],
                self.public["WAL-CRE-SPA-A-003"])

    def test_malformed_ifc_rejected(self):
        with TemporaryDirectory(prefix="g1-invalid-out-") as td:
            invalid=Path(td)/"invalid.ifc"
            invalid.write_bytes(b"NOT IFC")
            with self.assertRaises(SourceRubricBlocked):
                self._check("WIN-UPD-DIR-A-002",candidate=invalid)

    def test_source_and_outputs_immutable_after_negative_trials(self):
        self.assertEqual(self.source_digests,{
            c:sha256(p.read_bytes()).hexdigest() for c,p in self.source.items()
        })
        for pair,result in self.positives.items():
            self.assertEqual(
                sha256(self.candidates[pair].read_bytes()).hexdigest(),
                result["candidate_ifc_sha256"])


if __name__=="__main__":
    unittest.main()
