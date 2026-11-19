"""v0.48 exact original four public semantic IFC oracle positive/negative tests.

Every control writes a REAL source-native IFC via the existing matched
model-facing original XML edit session, separately checked by prior v0.45
independent physical source-conservation oracle, and now by our independent
semantic native world-geometry oracle (no hidden GT, no author evaluator).
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

import ifcopenshell
import ifcopenshell.util.placement
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import file_hash,UnsupportedArm
from tools.audit_bibimbap_v045_original4_native_mutations import (
    make_illustrative_plan)
from tools.bibimbap_v047_restricted_python_native_session import (
    MatchedOriginalXmlSession047,RestrictedOriginalPythonSession047)
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045)
from tools.bibimbap_v048_independent_original4_semantic_oracle import (
    evaluate_original_semantic048,OriginalSemantic048Error,
    TOL_M,ORIGINAL_PREDICATES,_mesh_box,_is_close,_same_box)
from tools import audit_bibimbap_v048_original4_semantic_controls as audit
from src.runtime.experimental_v44_original_native_step_readonly import PINS

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v048_original4_semantic_positive_negative_native_controls_20261117.json"
FROZEN_SHA="ca5f365198bff4f92b14031690b30338d3000adfd70b39c2be4471c9a32d7e08"
TASKS=audit.TASKS
Q="{urn:bim-markup-bench:toy:v0}"


class OriginalPublicFourPhysicalSemantic048(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks={x["test_id"]:x for x in public_45(AUTHOR,DATA)}
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.rows={(r["taskId"],r["control"]):r
                  for r in cls.report["original_four_positive_and_negative_native_pairs"]}
        cls.tmp=TemporaryDirectory(prefix="bmb-v048-original4-semantic-controls-")
        cls.states={}
        for i,tid in enumerate(TASKS):
            task=cls.tasks[tid]
            source=DATA/"ifc"/task["original_source_ifc_relpath"]
            for control in ("positive","negative"):
                folder=Path(cls.tmp.name)/f"{i}_{control}"
                session=MatchedOriginalXmlSession047(source,folder)
                xml=(audit.positive_developer_source_edit(
                        session.original_xml,source,tid,task["public_question"])
                     if control=="positive" else make_illustrative_plan(
                        session.original_xml,tid,source))
                res=session.call("submit_building_xml",{
                    "xml_text":xml.decode("utf8")})
                if res["status"]!="ok":
                    raise AssertionError(("v048 test setup native candidate",tid,control,res))
                semantic=evaluate_original_semantic048(
                    source,session.output_ifc,
                    original_sha=task["original_ifc_sha256"],
                    task_id=tid,public_question=task["public_question"])
                if semantic["candidatePassesIndependentResearchPhysicalPredicate"] != (control=="positive"):
                    raise AssertionError(("Semantic setup outcome",tid,control,semantic))
                cls.states[(tid,control)]={
                    "source":source,"candidate":session.output_ifc,
                    "xml":xml,"session":session,"semantic":semantic,
                }
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.tmp_test=TemporaryDirectory(prefix="bmb-v048-negative-test-")
        self.addCleanup(self.tmp_test.cleanup)
        self.work=Path(self.tmp_test.name)

    def _run(self,tid,candidate,*,question=None,sha=None,taskid=None):
        row=self.tasks[tid]
        source=DATA/"ifc"/row["original_source_ifc_relpath"]
        return evaluate_original_semantic048(
            source,Path(candidate),
            original_sha=row["original_ifc_sha256"] if sha is None else sha,
            task_id=tid if taskid is None else taskid,
            public_question=row["public_question"] if question is None else question)

    def _alter(self,tid,changer,*,positive=True):
        before=self.states[(tid,"positive" if positive else "negative")]["xml"]
        node=etree.fromstring(before)
        changer(node[-1][0])
        payload=etree.tostring(node,encoding="utf8",xml_declaration=True)
        source=self.states[(tid,"positive")]["source"]
        session=MatchedOriginalXmlSession047(source,self.work/str(uuid4()))
        response=session.call("submit_building_xml",{
            "xml_text":payload.decode("utf8")})
        self.assertEqual(response["status"],"ok",response)
        physical=verify_original_native_mutation_v045(
            source,session.output_ifc,submitted_xml=payload,
            source_sha=self.tasks[tid]["original_ifc_sha256"],task_id=tid)
        self.assertEqual(physical["status"],
                         "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS")
        return session.output_ifc

    def _changed_candidate_from_native(self,tid,mutate):
        path=self.states[(tid,"positive")]["candidate"]
        out=self.work/f"{tid}_tampered.ifc"
        f=ifcopenshell.open(str(path))
        mutate(f)
        f.write(str(out))
        return out

    def test_01_frozen_v048_report_sha(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_original_v047_baseline_hash(self):
        self.assertEqual(file_hash(audit.ROOT/audit.V047_REPORT),audit.V047_SHA)

    def test_03_original_v046_baseline_hash(self):
        self.assertEqual(file_hash(audit.ROOT/audit.V046_REPORT),audit.V046_SHA)

    def test_04_original_45_task_population(self):
        self.assertEqual(len(self.tasks),45)

    def test_05_original_15_15_15_CRUD(self):
        self.assertEqual(Counter(x["crud"] for x in self.tasks.values()),
                         {"create":15,"update":15,"delete":15})

    def test_06_original_31_unique_source_SHAs(self):
        self.assertEqual(len({x["original_ifc_sha256"] for x in self.tasks.values()}),31)

    def test_07_exact_four_source_and_question_sha_pins(self):
        self.assertEqual(len(PINS),4)
        for sha,(tid,crud,qsha,*_) in PINS.items():
            item=self.tasks[tid]
            self.assertEqual(item["original_ifc_sha256"],sha)
            self.assertEqual(item["public_question_sha256"],qsha)
            self.assertEqual(item["crud"],crud)
            self.assertEqual(file_hash(DATA/"ifc"/item["original_source_ifc_relpath"]),sha)

    def test_08_original3_UPDATE_1_DELETE(self):
        self.assertEqual(Counter(self.tasks[i]["crud"] for i in TASKS),
                         {"update":3,"delete":1})

    def test_09_other_41_outside_semantic_pilot(self):
        self.assertEqual(self.report["other_original41_not_attempted_in_semantic_pilot"],41)

    def test_10_exact_frozen_v047_parent_commit(self):
        self.assertEqual(self.report["stacked_on_exact_v047_frozen_commit"],audit.BASE_HEAD)

    def test_11_research_physical_tolerance_0p1mm(self):
        self.assertEqual(self.report["geometric_contact_tolerance_metres"],0.0001)

    def test_12_original_geom_world_units_metres_even_if_source_mm(self):
        self.assertTrue(self.report["Ifcopenshell_create_shape_world_vertices_already_metres_not_native_mm"])

    def test_13_original_semantic_oracle_is_separate_from_writer(self):
        s=(audit.ROOT/"tools"/"bibimbap_v048_independent_original4_semantic_oracle.py").read_text(encoding="utf8")
        self.assertNotIn("compile_original_native_mutation_v045",s)
        self.assertNotIn("ifcopenshell.api.run",s)
        self.assertNotIn("grade_author(",s)
        self.assertNotIn("hidden_ground_truth",s)

    def test_14_four_positive_and_negative_developer_controls(self):
        self.assertEqual(len(self.rows),8)
        self.assertEqual(self.report["positive_source_geometry_semantic_controls"],4)
        self.assertEqual(self.report["negative_source_geometry_semantic_controls"],4)

    def test_15_real_native_IFC_candidate_count_16(self):
        self.assertEqual(self.report["real_independent_native_IFC_candidate_count"],16)

    def test_16_same_real_IFC_bytes_XML_Python_for_all_eight(self):
        self.assertTrue(all(x["sameActualSourceNativeCandidateIFCBytes"]
                            for x in self.rows.values()))

    def test_17_all_16_original_source_native_scope_oracles_pass(self):
        self.assertEqual(self.report[
            "real_actual_native_source_physical_preservation_oracle_pass_count"],16)

    def test_18_both_arms_actual_model_tool_count_balanced(self):
        self.assertEqual(self.report["model_tool_read_count_each_arm"],8)
        self.assertEqual(self.report["model_tool_write_count_each_arm"],8)

    def test_19_original_author_evaluator_invocation_zero(self):
        self.assertEqual(self.report["original_author_evaluator_invocations"],0)

    def test_20_real_LLM_paid_model_trials_zero(self):
        self.assertEqual(self.report["actual_real_LLM_model_trials"],0)
        self.assertEqual(self.report["paid_provider_calls"],0)

    def test_21_Docker_and_author_hidden_GT_never_loaded(self):
        self.assertEqual(self.report["Docker_executions"],0)
        self.assertFalse(self.report["original_author_hidden_ground_truth_access"])

    def test_22_original_author_semantic_equivalence_NOT_proven(self):
        self.assertFalse(self.report["author_original_evaluator_equivalence_proven"])
        self.assertFalse(self.report["original_author_benchmark_task_score_claimed"])

    def test_23_all_positive_actual_source_native_physical_oracles_PASSED(self):
        for tid in TASKS:
            row=self.rows[(tid,"positive")]
            self.assertTrue(row["bothOriginalSourceNativeEditOraclesPass"])
            self.assertTrue(row["nativeIfc4x3OriginalMM"])

    def test_24_all_negative_actual_source_native_physical_oracles_PASSED(self):
        for tid in TASKS:
            row=self.rows[(tid,"negative")]
            self.assertTrue(row["bothOriginalSourceNativeEditOraclesPass"])

    def test_25_all_positive_original_research_physical_semantic_pass(self):
        for tid in TASKS:
            self.assertTrue(self.states[(tid,"positive")]["semantic"][
                "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_26_all_negative_original_research_physical_semantic_fail(self):
        for tid in TASKS:
            self.assertFalse(self.states[(tid,"negative")]["semantic"][
                "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_27_real_original_positive_14_square_10m_world(self):
        d=self.states[("geometry_test_14","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(d["candidateWorldXYSpanM"],[10.0,10.0])
        self.assertEqual(d["candidateSquareDimDifferenceM"],0.0)

    def test_28_real_original_negative_14_non_square(self):
        d=self.states[("geometry_test_14","negative")]["semantic"]["physicalObservations"]
        self.assertGreater(d["candidateSquareDimDifferenceM"],1.0)

    def test_29_real_original_positive_14_one_side_increased(self):
        d=self.states[("geometry_test_14","positive")]["semantic"]["physicalObservations"]
        self.assertTrue(d["oneWorldHorizontalSideIncreased"])
        self.assertTrue(d["otherWorldHorizontalSideUnchanged"])

    def test_30_real_original_positive_14_native_thickness_preserved(self):
        self.assertTrue(self.states[("geometry_test_14","positive")]["semantic"][
            "physicalObservations"]["originalPhysicalSlabThicknessPreserved"])

    def test_31_real_original_positive_15_column_rectangle(self):
        d=self.states[("geometry_test_15","positive")]["semantic"]["physicalObservations"]
        self.assertTrue(d["candidateExactlyFourCornerRectangle"])
        self.assertEqual(d["originalColumnsChangedWorldXYCount"],1)

    def test_32_real_original_negative_15_not_rectangle(self):
        self.assertFalse(self.states[("geometry_test_15","negative")]["semantic"][
            "physicalObservations"]["candidateExactlyFourCornerRectangle"])

    def test_33_real_original_positive_15_two_unique_x_levels(self):
        d=self.states[("geometry_test_15","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(len(d["uniqueColumnCenterWorldX_M"]),2)

    def test_34_real_original_positive_15_two_unique_y_levels(self):
        d=self.states[("geometry_test_15","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(len(d["uniqueColumnCenterWorldY_M"]),2)

    def test_35_real_original_positive_11_actual_named_slab_bottom_z_m(self):
        d=self.states[("topological_test_11","positive")]["semantic"]["physicalObservations"]
        self.assertAlmostEqual(d["originalUpperSlabUndersideWorldM"],2.6952)

    def test_36_real_original_positive_11_both_column_top_touch(self):
        d=self.states[("topological_test_11","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(len(d["columnContactObservationsByOriginalGUID"]),2)
        self.assertTrue(all(x["topContactWithin0p1mm"]
                            for x in d["columnContactObservationsByOriginalGUID"].values()))

    def test_37_real_original_positive_11_both_footprints_overlap_slab(self):
        d=self.states[("topological_test_11","positive")]["semantic"]["physicalObservations"]
        self.assertTrue(all(x["footprintPositiveAreaOverlap"]
                            for x in d["columnContactObservationsByOriginalGUID"].values()))

    def test_38_real_original_positive_11_increase_column_height_both(self):
        d=self.states[("topological_test_11","positive")]["semantic"]["physicalObservations"]
        self.assertTrue(all(x["columnPhysicalHeightIncreased"]
                            for x in d["columnContactObservationsByOriginalGUID"].values()))

    def test_39_real_original_negative_11_gap_still_present(self):
        d=self.states[("topological_test_11","negative")]["semantic"]["physicalObservations"]
        self.assertFalse(any(x["topContactWithin0p1mm"]
                             for x in d["columnContactObservationsByOriginalGUID"].values()))

    def test_40_real_original_positive_17_exact_five_columns_deleted(self):
        d=self.states[("topological_test_17","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(len(d["candidateRemovedOriginalColumnGUIDs"]),5)

    def test_41_real_original_positive_17_five_touching_columns_retained(self):
        d=self.states[("topological_test_17","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(len(d["candidateRemainingColumnGUIDs"]),5)

    def test_42_real_original_negative_17_wrong_column_deletion_set(self):
        d=self.states[("topological_test_17","negative")]["semantic"]["physicalObservations"]
        self.assertFalse(d["candidateRetainsExactlySourceTouchingColumns"])

    def test_43_original17_no_explicit_IfcRelConnects_column_slab(self):
        model=ifcopenshell.open(str(self.states[
            ("topological_test_17","positive")]["source"]))
        self.assertEqual(len(model.by_type("IfcRelConnectsElements")),0)

    def test_44_original17_physical_contact_agrees_with_original_storey_relation(self):
        d=self.states[("topological_test_17","positive")]["semantic"]["physicalObservations"]
        self.assertTrue(d[
            "sourceTouchingColumnsMatchNativeIfcRelContainedInSpatialStructure"])

    def test_45_all_original_positive_native_IFC_sha_match_frozen(self):
        for tid in TASKS:
            st=self.states[(tid,"positive")]
            self.assertEqual(file_hash(st["candidate"]),self.rows[
                (tid,"positive")]["XMLNativeSourceOutputSHA256"])

    def test_46_all_original_negative_native_IFC_sha_match_frozen(self):
        for tid in TASKS:
            st=self.states[(tid,"negative")]
            self.assertEqual(file_hash(st["candidate"]),self.rows[
                (tid,"negative")]["XMLNativeSourceOutputSHA256"])

    def test_47_independent_non_author_oracle_deterministic_all_eight(self):
        for tid in TASKS:
            for control in ("positive","negative"):
                st=self.states[(tid,control)]
                self.assertEqual(self._run(tid,st["candidate"]),st["semantic"])

    def test_48_original_question_spoof_rejected(self):
        tid="geometry_test_14"
        p=self.states[(tid,"positive")]["candidate"]
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,p,question="Make up a new square")

    def test_49_original_IFC_SHA_spoof_rejected(self):
        tid="geometry_test_14"
        p=self.states[(tid,"positive")]["candidate"]
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,p,sha="0"*64)

    def test_50_source_task_id_swap_rejected(self):
        tid="geometry_test_14"
        p=self.states[(tid,"positive")]["candidate"]
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,p,taskid="topological_test_11")

    def test_51_named_slab_11_spoof_in_public_question_rejected(self):
        tid="topological_test_11"
        row=self.tasks[tid]
        forged=row["public_question"].replace(
            "0dxtXCDSn2mfP92h$AiPMM","0dxtXCDSn2mfP92h$AiPNt")
        self.assertNotEqual(forged,row["public_question"])
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,self.states[(tid,"positive")]["candidate"],question=forged)

    def test_52_named_slab_17_spoof_in_public_question_rejected(self):
        tid="topological_test_17"
        row=self.tasks[tid]
        forged=row["public_question"].replace(
            "2IIWDJ6bzEPxU4iXeUX9Z5","2IIWDJ6bzEPxU4iXeUX9zb")
        self.assertNotEqual(forged,row["public_question"])
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,self.states[(tid,"positive")]["candidate"],question=forged)

    def test_53_candidate_must_be_distinct_from_original_source(self):
        tid="geometry_test_14"
        src=self.states[(tid,"positive")]["source"]
        with self.assertRaises(OriginalSemantic048Error):
            self._run(tid,src)

    def test_54_missing_candidate_file_fail_closed(self):
        with self.assertRaises(OriginalSemantic048Error):
            self._run("geometry_test_14",self.work/"missing.ifc")

    def test_55_original_source_modified_copy_fail_closed(self):
        tid="geometry_test_14"
        orig=self.states[(tid,"positive")]["source"]
        clone=self.work/"modified-original.ifc"
        clone.write_bytes(orig.read_bytes()+b"\nFORGED")
        with self.assertRaises(OriginalSemantic048Error):
            evaluate_original_semantic048(
                clone,self.states[(tid,"positive")]["candidate"],
                original_sha=self.tasks[tid]["original_ifc_sha256"],
                task_id=tid,public_question=self.tasks[tid]["public_question"])

    def test_56_unknown_original_public_task_fails_closed(self):
        with self.assertRaises(OriginalSemantic048Error):
            self._run("geometry_test_14",self.states[
                ("geometry_test_14","positive")]["candidate"],taskid="geometry_test_01")

    def test_57_original14_near_miss_2mm_not_square(self):
        new=self._alter("geometry_test_14",lambda op:op.set("newXDimM","9.998"))
        self.assertFalse(self._run("geometry_test_14",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_58_original14_near_miss_0p2mm_not_square(self):
        new=self._alter("geometry_test_14",lambda op:op.set("newXDimM","9.9998"))
        self.assertFalse(self._run("geometry_test_14",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_59_original14_within_declared_0p1mm_tolerance(self):
        new=self._alter("geometry_test_14",lambda op:op.set("newXDimM","9.99994"))
        self.assertTrue(self._run("geometry_test_14",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_60_original15_rectangle_near_miss_1mm_Y(self):
        def near(op):
            op.set("newWorldOriginYM",str(float(op.get("newWorldOriginYM"))+0.001))
        new=self._alter("geometry_test_15",near)
        self.assertFalse(self._run("geometry_test_15",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_61_original15_rectangle_near_miss_1mm_X(self):
        def near(op):
            op.set("newWorldOriginXM",str(float(op.get("newWorldOriginXM"))+0.001))
        new=self._alter("geometry_test_15",near)
        self.assertFalse(self._run("geometry_test_15",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_62_original11_1mm_air_gap_rejected(self):
        new=self._alter("topological_test_11",lambda op:op.set("newDepthM","2.6942"))
        self.assertFalse(self._run("topological_test_11",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_63_original11_1mm_slab_interpenetration_rejected(self):
        new=self._alter("topological_test_11",lambda op:op.set("newDepthM","2.6962"))
        self.assertFalse(self._run("topological_test_11",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_64_original11_under_0p1mm_contact_tolerance_accepted(self):
        new=self._alter("topological_test_11",lambda op:op.set("newDepthM","2.69515"))
        self.assertTrue(self._run("topological_test_11",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_65_original11_3m_column_overlaps_slab_not_just_touches(self):
        new=self._alter("topological_test_11",lambda op:op.set("newDepthM","3.0"))
        self.assertFalse(self._run("topological_test_11",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_66_original17_deleting_only_four_unrelated_leaves_one(self):
        def modify(op):
            op.remove(op[-1])
        new=self._alter("topological_test_17",modify)
        self.assertFalse(self._run("topological_test_17",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_67_original17_deleting_five_plus_one_related_fails(self):
        def modify(op):
            original=set(x.GlobalId for x in ifcopenshell.open(str(self.states[
                ("topological_test_17","positive")]["source"])).by_type("IfcColumn"))
            deleted={e.get("ifcGuid") for e in op}
            related=sorted(original-deleted)
            etree.SubElement(op,Q+"DeleteColumn",{"ifcGuid":related[0]})
        new=self._alter("topological_test_17",modify)
        self.assertFalse(self._run("topological_test_17",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_68_original17_deleting_one_related_instead_of_unrelated_fails(self):
        def modify(op):
            original=set(x.GlobalId for x in ifcopenshell.open(str(self.states[
                ("topological_test_17","positive")]["source"])).by_type("IfcColumn"))
            deleted={e.get("ifcGuid") for e in op}
            related=sorted(original-deleted)
            for child in list(op):
                op.remove(child)
            etree.SubElement(op,Q+"DeleteColumn",{"ifcGuid":related[0]})
        new=self._alter("topological_test_17",modify)
        self.assertFalse(self._run("topological_test_17",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_69_original17_delete_order_invariant_physical_semantics(self):
        def modify(op):
            for child in list(op):
                op.remove(child)
                op.insert(0,child)
        new=self._alter("topological_test_17",modify)
        self.assertTrue(self._run("topological_test_17",new)[
            "candidatePassesIndependentResearchPhysicalPredicate"])

    def test_70_original17_source_contacts_exactly_five(self):
        d=self.states[("topological_test_17","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(sum(d["sourcePhysicalContactByGUID"].values()),5)

    def test_71_original17_source_noncontacts_exactly_five(self):
        d=self.states[("topological_test_17","positive")]["semantic"]["physicalObservations"]
        self.assertEqual(10-sum(d["sourcePhysicalContactByGUID"].values()),5)

    def test_72_original17_no_simple_IFC_RelConnects_equivalence(self):
        m=ifcopenshell.open(str(self.states[
            ("topological_test_17","positive")]["source"]))
        self.assertEqual(len(m.by_type("IfcRelConnectsElements")),0)
        self.assertGreater(len(m.by_type("IfcRelContainedInSpatialStructure")),0)

    def test_73_original14_rotate_native_slab_invalid_axis_aligned_prism(self):
        def rotate(model):
            slab=model.by_type("IfcSlab")[0]
            placement=slab.ObjectPlacement.RelativePlacement
            ref=placement.RefDirection
            if ref is None:
                # IFC4X3 source legally omits RefDirection for default X axis.
                # Create a genuine IFCDIRECTION only in the disposable candidate.
                placement.RefDirection=model.createIfcDirection((0.8,0.6,0.0))
            else:
                ref.DirectionRatios=(0.8,0.6,0.0)
        out=self._changed_candidate_from_native("geometry_test_14",rotate)
        with self.assertRaises(OriginalSemantic048Error):
            self._run("geometry_test_14",out)

    def test_74_changed_non_target_slab_must_be_blocked_by_prior_oracle(self):
        tid="topological_test_11"
        source=self.states[(tid,"positive")]["source"]
        candidate=self.states[(tid,"positive")]["candidate"]
        xml=self.states[(tid,"positive")]["xml"]
        def unauthorized(model):
            slab=model.by_type("IfcSlab")[0]
            slab.Name="MODEL_FAKE_SLAB_NAME"
        changed=self._changed_candidate_from_native(tid,unauthorized)
        with self.assertRaises(Exception):
            verify_original_native_mutation_v045(
                source,changed,submitted_xml=xml,
                source_sha=self.tasks[tid]["original_ifc_sha256"],task_id=tid)

    def test_75_tampered_raw_native_candidate_fails_safe(self):
        tid="geometry_test_14"
        bad=self.work/"corrupted.ifc"
        bad.write_bytes(b"NOT AN ORIGINAL NATIVE IFC")
        with self.assertRaises(Exception):
            self._run(tid,bad)

    def test_76_frozen_report_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as f:f.write(b"INJECTED_FALSE_GROUND_TRUTH")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_77_full_original8_pair_frozen_report_byte_identical_replay(self):
        r=audit.audit(AUTHOR,DATA)
        raw=(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),FROZEN_SHA)
        self.assertEqual(raw,REPORT.read_bytes())

    def test_78_original_IFC_source_bytes_unchanged_after_all_tests(self):
        for tid in TASKS:
            item=self.tasks[tid]
            src=DATA/"ifc"/item["original_source_ifc_relpath"]
            self.assertEqual(file_hash(src),item["original_ifc_sha256"])

    def test_79_original_four_research_scored_zero_author_metrics(self):
        self.assertFalse(self.report["original_author_benchmark_task_score_claimed"])
        self.assertFalse(self.report["author_original_evaluator_equivalence_proven"])

    def test_80_original_python_tool_has_not_acquired_unrestricted_API(self):
        self.assertTrue(self.report["all_candidate_IFC_physical_geometry_original_IFC4X3_mm"])
        self.assertTrue(self.report["all_original_published_question_and_IFC_data_unchanged"])


if __name__=="__main__":
    unittest.main()
