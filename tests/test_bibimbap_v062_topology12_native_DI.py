"""v0.62 original IFC4X3 isolated Wall centered shortening genuine D/I gates.

Evaluates source-native complete XML, complete compact final state and
independent native STEP/schema/physical geometry validator. The separate
frozen report's --check reruns actual OS-isolated pinned Linux Docker.

No provider/model calls, no changes to original author IFC, test or GT.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json

import ifcopenshell
from lxml import etree

from tools.bibimbap_matched25_cli import public_45
from tools.bibimbap_matched25_tools import DockerIFCExecutor,file_hash
from tools import audit_bibimbap_v062_topology12_native_DI as audit
from tools.bibimbap_v062_topology12_native import (
    SOURCE_SHA,TASK,MAX_CALLS,
    Topology12Native062Error,
    _source,_mesh_bounds,_wall_repr,
    isolated_original_swept_wall_v062,
    original_wall_axis_length_m_v062,
    full_source_state_v062,compact_complete_state_v062,
    parse_full_final_state_v062,restore_compact_final_state_v062,
    compile_wall_shortening_v062,independent_wall_native_scope_v062,
    canonical_native_semantic_digest_v062,
)
from tools.bibimbap_v062_topology12_sessions import (
    DirectFullState062,DirectManagedState062,LiveDockerPython062,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,refuse_all_model_trials_v057,
)


FROZEN_REPORT_SHA="c80b6d4c6b39c51eaac96177515f0f6cd93f36e37298bae973ae4f7e57c11842"


class SourceNativeOriginalWallDI062(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.row=next(x for x in public_45(audit.AUTHOR,audit.DATA)
                     if x["test_id"]==TASK)
        cls.source=audit.DATA/"ifc"/cls.row["original_source_ifc_relpath"]
        cls.model=_source(cls.source,source_sha=SOURCE_SHA)
        cls.eligible=isolated_original_swept_wall_v062(cls.model)[0].GlobalId
        cls.initial=full_source_state_v062(cls.source,source_sha=SOURCE_SHA)
        cls.managed=compact_complete_state_v062(cls.source,source_sha=SOURCE_SHA)
        cls.wall_guids=sorted(w.GlobalId for w in cls.model.by_type("IfcWall"))

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v062-wall-real-ifc-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def d(self):
        return DirectFullState062(self.source,self.folder/"D")

    def m(self):
        return DirectManagedState062(self.source,self.folder/"M")

    def i(self):
        return LiveDockerPython062(self.source,self.folder/"I")

    def full(self,length=1.):
        return audit._full_final(self.initial,self.eligible,length)

    def compact(self,length=1.):
        return audit._managed_final(self.managed,self.eligible,length)

    def bad_full(self,value):
        with self.assertRaises(Exception):
            parse_full_final_state_v062(
                self.source,value.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_compact(self,value):
        with self.assertRaises(Exception):
            restore_compact_final_state_v062(
                self.source,value.encode("utf8"),source_sha=SOURCE_SHA)

    def compile(self,length=1.,filename="candidate.ifc"):
        out=self.folder/filename
        compile_wall_shortening_v062(
            self.source,out,source_sha=SOURCE_SHA,
            target=(self.eligible,length))
        return out

    def test_01_frozen_actual_Linux_Docker_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_REPORT_SHA)

    def test_02_frozen_report_exact_canonical_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),
                         audit.canonical(self.report))

    def test_03_prior_v061_source_report_immutable(self):
        self.assertEqual(file_hash(audit.PARENT),audit.PARENT_SHA)

    def test_04_prior_v058_six_selection_immutable(self):
        self.assertEqual(file_hash(audit.FROZEN),audit.FROZEN_SHA)

    def test_05_fixed_original_six_task_ids_preserved(self):
        self.assertEqual(
            self.report["original_six_preselected_source_tasks_unchanged"],
            audit.FIXED_SIX)

    def test_06_exactly_one_new_v062_source_native_task(self):
        self.assertEqual(
            self.report["v062_new_original_native_task_supported"],[TASK])

    def test_07_exact_4_of_6_selected_and_two_NOT_supported(self):
        self.assertEqual(
            self.report["current_four_of_six_original_source_task_specific_native_developer_supported"],
            sorted(audit.SUPPORTED))
        self.assertEqual(
            self.report["remaining_two_original_fixed_tasks_not_yet_native_eligible"],
            sorted(set(audit.FIXED_SIX)-audit.SUPPORTED))
        self.assertEqual(len(self.report[
            "remaining_two_original_fixed_tasks_not_yet_native_eligible"]),2)

    def test_08_full_original_population_45_and_31_unchanged(self):
        self.assertEqual(self.report["original_45_public_task_population"],45)
        self.assertEqual(self.report["original_31_unique_source_IFC_population"],31)

    def test_09_original_IFC_SHA_fixed(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(self.row["original_ifc_sha256"],SOURCE_SHA)

    def test_10_original_IFC4X3_native_schema(self):
        self.assertEqual(self.model.schema,"IFC4X3")
        self.assertEqual(self.report["original_IFC_source_schema"],"IFC4X3")

    def test_11_source_8_walls_7_path_connections(self):
        self.assertEqual(len(self.model.by_type("IfcWall")),8)
        self.assertEqual(len(self.model.by_type("IfcRelConnectsPathElements")),7)

    def test_12_source_two_slabs_two_columns_one_space(self):
        self.assertEqual(len(self.model.by_type("IfcSlab")),2)
        self.assertEqual(len(self.model.by_type("IfcColumn")),2)
        self.assertEqual(len(self.model.by_type("IfcSpace")),1)

    def test_13_single_original_swept_wall_2_metres(self):
        wall,axis,profile=isolated_original_swept_wall_v062(self.model)
        self.assertEqual(wall.GlobalId,self.eligible)
        self.assertAlmostEqual(original_wall_axis_length_m_v062(wall),2.)
        self.assertAlmostEqual(profile.XDim,2000.)
        self.assertEqual(len(axis.Points),2)

    def test_14_original_swept_wall_has_no_path_joins(self):
        wall=self.model.by_guid(self.eligible)
        self.assertFalse(any(x.is_a("IfcRelConnectsPathElements")
                             for x in self.model.get_inverse(wall)))

    def test_15_original_other_connected_wall_body_clipping(self):
        self.assertEqual(sum(
            _wall_repr(w)[1].is_a("IfcBooleanClippingResult")
            for w in self.model.by_type("IfcWall")),7)

    def test_16_original_source_public_six_excluded_wall_ids(self):
        source=audit.public_source_exterior_wall_and_question_predicate_v062(
            self.source,self.row["public_question"])
        self.assertEqual(
            source["public_original_question_named_outer_wall_count"],6)
        self.assertEqual(
            source["outside_original_named_six_wall_count"],2)
        self.assertTrue(source[
            "one_omitted_original_wall_is_connected_to_six"])

    def test_17_source_axis_start_point_shared_must_NOT_mutate(self):
        axis,_=_wall_repr(self.model.by_guid(self.eligible))
        self.assertGreater(len(self.model.get_inverse(axis.Points[0])),1)
        self.assertEqual(tuple(axis.Points[0].Coordinates),(0.,0.))

    def test_18_source_swept_wall_profile_original_center(self):
        _,_,profile=isolated_original_swept_wall_v062(self.model)
        self.assertAlmostEqual(profile.Position.Location.Coordinates[0],1000.)

    def test_19_original_native_source_full_XML_size_5287(self):
        self.assertEqual(len(self.initial),5287)
        self.assertEqual(self.report[
            "all_three_arms_identical_initial_original_source_XML_bytes"],5287)

    def test_20_original_compact_all_eight_XML_size_955(self):
        self.assertEqual(len(self.managed),955)
        self.assertEqual(self.report[
            "original_complete_managed_eight_wall_initial_UTF8_bytes"],955)

    def test_21_source_exact_8_wall_complete_final_state_roster(self):
        state=etree.fromstring(self.initial)
        self.assertEqual(len(state[1]),8)
        self.assertEqual(
            [x.get("ifcGuid") for x in state[1]],self.wall_guids)

    def test_22_compact_exact_8_wall_complete_final_state_roster(self):
        state=etree.fromstring(self.managed)
        self.assertEqual(len(state),8)
        self.assertEqual(
            [x.get("ifcGuid") for x in state],self.wall_guids)

    def test_23_source_initial_read_byte_identical_three_arms(self):
        D,M,I=self.d(),self.m(),self.i()
        reads=[s.call("read_building_xml",{"query":"source"})
               for s in (D,M,I)]
        self.assertEqual([r["status"] for r in reads],["ok"]*3)
        self.assertEqual(reads[0]["xml"],reads[1]["xml"])
        self.assertEqual(reads[1]["xml"],reads[2]["xml"])
        self.assertEqual(reads[0]["xml"].encode("utf8"),self.initial)

    def test_24_tool_initial_read_schema_equal_three_arms(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(D.tools[0],M.tools[0])
        self.assertEqual(M.tools[0],I.tools[0])

    def test_25_real_D_full_managed_I_distinct_tool_schemas(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(
            [D.tools[1]["name"],M.tools[1]["name"],I.tools[1]["name"]],
            ["submit_building_xml","submit_managed_final_state",
             "execute_ifc_code"])

    def test_26_I_uses_real_exact_DockerIFCExecutor(self):
        self.assertIs(type(self.i().executor),DockerIFCExecutor)

    def test_27_real_D_full_native_wall_centered_1m_compile(self):
        D=self.d()
        result=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["actual_native_original_wall_shortening_m"],1.)
        self.assertEqual(result["introduced_original_IFC_schema_errors"],0)
        self.assertEqual(file_hash(D.output_ifc),result["native_ifc_sha256"])

    def test_28_real_D_managed_native_wall_centered_1m_compile(self):
        M=self.m()
        result=M.call("submit_managed_final_state",
                      {"xml_text":self.compact()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["actual_native_original_wall_shortening_m"],1.)

    def test_29_complete_D_full_and_managed_final_XML_exact_parity(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
            {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
            {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(D.current_xml,M.current_xml)

    def test_30_complete_managed_reconstruction_from_source_exact_bytes(self):
        final,target=restore_compact_final_state_v062(
            self.source,self.compact().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(final,self.full().encode("utf8"))
        self.assertEqual(target,(self.eligible,1.))

    def test_31_D_full_managed_same_semantic_IFC_digest(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
            {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
            {"xml_text":self.compact()})["status"],"ok")
        self.assertEqual(
            canonical_native_semantic_digest_v062(D.output_ifc),
            canonical_native_semantic_digest_v062(M.output_ifc))

    def test_32_actual_centered_1m_shortening_world_bbox(self):
        output=self.compile()
        grade=independent_wall_native_scope_v062(
            self.source,output,source_sha=SOURCE_SHA)
        self.assertTrue(grade["original_external_wall_world_center_preserved"])
        self.assertEqual(grade["actual_native_shortening_m"],1.)
        self.assertEqual(grade["introduced_original_IFC_schema_error_count"],0)

    def test_33_source_original_shared_axis_point_preserved_in_candidate(self):
        output=self.compile()
        source_wall,axis,_=isolated_original_swept_wall_v062(self.model)
        actual=ifcopenshell.open(str(output))
        self.assertEqual(
            self.model.by_id(axis.Points[0].id()).Coordinates,
            actual.by_id(axis.Points[0].id()).Coordinates)

    def test_34_exactly_one_independent_new_axis_point_is_added(self):
        output=self.compile()
        before={e.id() for e in self.model}
        edited=ifcopenshell.open(str(output))
        extra={e.id() for e in edited}-before
        self.assertEqual(len(extra),1)
        self.assertTrue(edited.by_id(next(iter(extra))).is_a("IfcCartesianPoint"))

    def test_35_two_wrong_lengths_still_valid_native_schema(self):
        for i,length in enumerate((1.5,.5)):
            out=self.compile(length,f"wrong_{i}.ifc")
            result=independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)
            self.assertEqual(result["introduced_original_IFC_schema_error_count"],0)
            self.assertNotEqual(result["actual_native_shortening_m"],1.)

    def test_36_three_genuine_Docker_native_developer_controls_frozen(self):
        self.assertEqual(self.report[
            "real_native_pinned_Linux_Docker_I_developer_cases"],3)
        self.assertEqual(len(self.report[
            "three_original_source_centered_Wall_developer_control_results"]),3)
        self.assertTrue(all(x[
            "actual_genuine_isolated_linux_Docker_Python_executed"]
            for x in self.report[
                "three_original_source_centered_Wall_developer_control_results"]))

    def test_37_total_9_actual_IFC_native_D_I_cases(self):
        self.assertEqual(self.report["real_native_D_full_source_IFC_developer_cases"],3)
        self.assertEqual(self.report[
            "real_native_D_complete_managed_source_IFC_developer_cases"],3)
        self.assertEqual(self.report["total_native_original_source_IFC_edits_admitted"],9)

    def test_38_correct_original_author_repository_score_one(self):
        outcome=self.report[
            "three_original_source_centered_Wall_developer_control_results"][0][
                "original_author_repository_evaluator_side_only"]
        self.assertEqual(outcome["status"],"EVALUATOR_RETURNED_BOOLEAN_METRICS")
        self.assertEqual(outcome["author_repository_mean_boolean_score"],1.)
        self.assertTrue(all(outcome["author_repository_boolean_metrics"].values()))

    def test_39_two_wrong_source_lengths_have_author_fractional_scores(self):
        for case in self.report[
                "three_original_source_centered_Wall_developer_control_results"][1:]:
            grade=case["original_author_repository_evaluator_side_only"]
            self.assertEqual(grade["author_repository_mean_boolean_score"],.666667)
            self.assertFalse(grade["author_repository_boolean_metrics"][
                "right_dimensions"])
            self.assertTrue(grade["author_repository_boolean_metrics"][
                "right_location"])

    def test_40_original_author_scores_not_proven_paper_official(self):
        self.assertFalse(self.report[
            "published_paper_official_scorer_equivalence_verified"])
        self.assertIsNone(self.report["original_paper_official_LLM_score"])

    def test_41_public_wall_target_not_in_committed_frozen_report(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.eligible,raw)
        self.assertTrue(all(x["original_author_target_wall_GUID_redacted"]
            for x in self.report[
                "three_original_source_centered_Wall_developer_control_results"]))

    def test_42_genuine_D_I_canonical_semantic_digest_agrees_each_case(self):
        outcomes=self.report[
            "three_original_source_centered_Wall_developer_control_results"]
        self.assertEqual(len({
            x["all_three_original_native_IFC_canonical_semantic_SHA256"]
            for x in outcomes}),3)
        self.assertTrue(self.report["all_three_D_I_semantic_digest_per_case_equal"])

    def test_43_actual_LLM_trials_and_paid_calls_zero(self):
        self.assertEqual(self.report["actual_LLM_generated_model_trials"],0)
        self.assertEqual(self.report["paid_provider_model_calls"],0)
        self.assertEqual(self.report["original_IFC_provider_uploads"],0)

    def test_44_unmodified_source_full_state_no_op_rejected(self):
        self.bad_full(self.initial.decode("utf8"))

    def test_45_unmodified_complete_managed_roster_no_op_rejected(self):
        self.bad_compact(self.managed.decode("utf8"))

    def test_46_missing_original_wall_in_complete_full_roster_rejected(self):
        root=etree.fromstring(self.full().encode("utf8"))
        root[1].remove(root[1][0])
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_47_missing_wall_in_complete_managed_roster_rejected(self):
        root=etree.fromstring(self.compact().encode("utf8"))
        root.remove(root[0])
        self.bad_compact(etree.tostring(root).decode("utf8"))

    def test_48_unknown_or_duplicate_source_wall_GUID_rejected(self):
        root=etree.fromstring(self.compact().encode("utf8"))
        root[0].set("ifcGuid","0"*22)
        self.bad_compact(etree.tostring(root).decode("utf8"))
        root=etree.fromstring(self.full().encode("utf8"))
        root[1][0].set("ifcGuid",root[1][1].get("ifcGuid"))
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_49_original_complete_roster_reordered_rejected(self):
        root=etree.fromstring(self.compact().encode("utf8"))
        root.insert(0,root[-1])
        self.bad_compact(etree.tostring(root).decode("utf8"))

    def test_50_original_IFC_source_SHA_tamper_rejected(self):
        root=etree.fromstring(self.full().encode("utf8"))
        root.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_51_compact_source_full_XML_SHA_tamper_rejected(self):
        root=etree.fromstring(self.compact().encode("utf8"))
        root.set("sourceFullBuildingStateSha256","f"*64)
        self.bad_compact(etree.tostring(root).decode("utf8"))

    def test_52_source_original_IFC_body_representation_tamper_rejected(self):
        root=etree.fromstring(self.full().encode("utf8"))
        wall=next(e for e in root[0][0]
                  if e.get("sourceBodyRepresentationClass")=="IfcExtrudedAreaSolid")
        wall.set("sourceBodyRepresentationClass","IfcBooleanClippingResult")
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_53_source_original_wall_path_count_tamper_rejected(self):
        root=etree.fromstring(self.full().encode("utf8"))
        wall=next(e for e in root[0][0]
                  if e.get("ifcClass")=="IfcWall")
        wall.set("sourceConnectedWallPathCount","999")
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_54_source_original_geometry_bbox_tamper_rejected(self):
        root=etree.fromstring(self.full().encode("utf8"))
        obj=next(e for e in root[0][0] if e.get("maxYM"))
        obj.set("maxYM","100.000000")
        self.bad_full(etree.tostring(root).decode("utf8"))

    def test_55_editing_original_connected_clipped_wall_refused(self):
        node=etree.fromstring(self.full().encode("utf8"))
        wrong=next(e for e in node[1] if e.get("ifcGuid")!=self.eligible)
        wrong.set("finalAxisLengthM",f"{float(wrong.get('finalAxisLengthM'))-1.:.6f}")
        self.bad_full(etree.tostring(node).decode("utf8"))

    def test_56_edit_two_original_walls_at_once_refused(self):
        node=etree.fromstring(self.full().encode("utf8"))
        wrong=next(e for e in node[1] if e.get("ifcGuid")!=self.eligible)
        wrong.set("finalAxisLengthM",f"{float(wrong.get('finalAxisLengthM'))-1.:.6f}")
        self.bad_full(etree.tostring(node).decode("utf8"))

    def test_57_expanding_original_wall_length_refused(self):
        self.bad_full(self.full(2.5))

    def test_58_noncanonical_7_decimal_wall_length_refused(self):
        node=etree.fromstring(self.full().encode("utf8"))
        target=next(e for e in node[1] if e.get("ifcGuid")==self.eligible)
        target.set("finalAxisLengthM","1.0000000")
        self.bad_full(etree.tostring(node).decode("utf8"))

    def test_59_nan_in_original_final_length_refused(self):
        node=etree.fromstring(self.full().encode("utf8"))
        target=next(e for e in node[1] if e.get("ifcGuid")==self.eligible)
        target.set("finalAxisLengthM","NaN")
        self.bad_full(etree.tostring(node).decode("utf8"))

    def test_60_xml_command_opcode_and_extra_properties_refused(self):
        node=etree.fromstring(self.compact().encode("utf8"))
        node[0].set("operation","shorten_wall")
        self.bad_compact(etree.tostring(node).decode("utf8"))
        node=etree.fromstring(self.full().encode("utf8"))
        etree.SubElement(node[1][0],"{urn:bim-markup-bench:toy:v0}NativeEditPlan")
        self.bad_full(etree.tostring(node).decode("utf8"))

    def test_61_XML_XXE_DTD_external_entity_refused(self):
        raw=self.full().encode("utf8")
        dtd=(b"<!DOCTYPE BuildingState ["
             b"<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>")
        self.bad_full(raw.replace(b"?>",b"?>"+dtd,1).decode("utf8"))

    def test_62_wrong_native_1000_m_v_mm_refused(self):
        with self.assertRaises(Topology12Native062Error):
            self.compile(1000.)

    def test_63_raw_native_only_axis_endpoint_shortened_refused(self):
        model=ifcopenshell.open(str(self.source))
        wall,axis,profile=isolated_original_swept_wall_v062(model)
        axis.Points[1].Coordinates=(1000.,0.)
        out=self.folder/"axis_only.ifc"
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_64_raw_native_only_rectangle_profile_changed_refused(self):
        model=ifcopenshell.open(str(self.source))
        wall,axis,profile=isolated_original_swept_wall_v062(model)
        profile.XDim=1000.
        out=self.folder/"profile_only.ifc"
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_65_original_shared_axis_start_must_not_change(self):
        model=ifcopenshell.open(str(self.source))
        wall,axis,profile=isolated_original_swept_wall_v062(model)
        axis.Points[0].Coordinates=(500.,0.)
        out=self.folder/"shared_source_point_corrupt.ifc"
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_66_off_target_wall_name_mutation_rejected(self):
        out=self.compile()
        model=ifcopenshell.open(str(out))
        wall=next(w for w in model.by_type("IfcWall")
                  if w.GlobalId!=self.eligible)
        wall.Name="CORRUPTED_UNRELATED_WALL"
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_67_add_unrelated_native_STEP_entity_rejected(self):
        out=self.compile()
        model=ifcopenshell.open(str(out))
        model.create_entity("IfcCartesianPoint",Coordinates=(123.,456.))
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_68_wall_profile_world_center_moved_rejected(self):
        out=self.compile()
        model=ifcopenshell.open(str(out))
        w,axis,profile=isolated_original_swept_wall_v062(self.model)
        altered=model.by_id(profile.Position.Location.id())
        coords=list(altered.Coordinates);coords[0]+=500.
        altered.Coordinates=tuple(coords)
        model.write(str(out))
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,out,source_sha=SOURCE_SHA)

    def test_69_original_source_as_output_alias_rejected(self):
        with self.assertRaises(Topology12Native062Error):
            independent_wall_native_scope_v062(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_70_wrong_source_SHA_never_loaded(self):
        with self.assertRaises(Topology12Native062Error):
            full_source_state_v062(self.source,source_sha="0"*64)

    def test_71_D_full_valid_then_invalid_keeps_last_native_XML(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",
                              {"xml_text":self.full()})["status"],"ok")
        prior=file_hash(D.output_ifc);xml=D.current_xml
        bad=D.call("submit_building_xml",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),prior)
        self.assertEqual(D.current_xml,xml)

    def test_72_D_managed_valid_then_invalid_keeps_last_native_XML(self):
        M=self.m()
        self.assertEqual(M.call("submit_managed_final_state",
                              {"xml_text":self.compact()})["status"],"ok")
        prior=file_hash(M.output_ifc);xml=M.current_xml
        bad=M.call("submit_managed_final_state",{"xml_text":"<Invalid/>"})
        self.assertEqual(bad["status"],"error")
        self.assertEqual(file_hash(M.output_ifc),prior)
        self.assertEqual(M.current_xml,xml)

    def test_73_same_D_full_final_state_replay_rejected(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",
                              {"xml_text":self.full()})["status"],"ok")
        before=file_hash(D.output_ifc)
        response=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(response["error_type"],"ExactFinalStateReplayRejected")
        self.assertEqual(file_hash(D.output_ifc),before)

    def test_74_strict_25_total_tool_calls_all_three_arms(self):
        D,M,I=self.d(),self.m(),self.i()
        for s in (D,M,I):
            for _ in range(MAX_CALLS):
                self.assertEqual(s.call("read_building_xml",
                    {"query":"source"})["status"],"ok")
            response=s.call("read_building_xml",{"query":"source"})
            self.assertEqual(response["error_type"],"ToolBudgetExhausted")

    def test_75_wrong_D_full_tool_cannot_bypass_compact(self):
        M=self.m()
        r=M.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(r["error_type"],"WrongDeclarativeFinalStateTool")

    def test_76_unavailable_Docker_refuses_without_executing_python(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v062_topology12_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"BLOCKED_RUNTIME","reason":"NO_LINUX"},
        ),patch.object(I.executor,"run") as fake:
            r=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(r["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertIsNone(I.output_ifc)

    def test_77_fake_Docker_success_does_not_attest_real_native_edit(self):
        I=self.i()
        with patch(
            "tools.bibimbap_v062_topology12_sessions.live_pinned_local_runtime_admission_v052",
            return_value={"status":"RUNTIME_ADMITTED"},
        ),patch.object(I.executor,"run",return_value={
            "status":"ok","committed":True,
            "backend":"linux_docker_sandbox",
        }):
            r=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(r["error_type"],"NativeWorkerOrScopeRejected")
        self.assertIsNone(I.output_ifc)

    def test_78_actual_Docker_adversarial_axis_only_rejected_in_frozen_audit(self):
        self.assertTrue(self.report[
            "actual_genuine_Docker_axis_only_native_invalid_rejected"])

    def test_79_actual_Docker_good_then_wrong_preserves_SHA_in_audit(self):
        self.assertTrue(self.report[
            "actual_genuine_Docker_good_then_offtarget_last_IFC_preserved"])

    def test_80_original_author_grader_never_imported_into_model_host(self):
        for name in ("bibimbap_v062_topology12_native.py",
                     "bibimbap_v062_topology12_sessions.py"):
            content=(audit.ROOT/"tools"/name).read_text(encoding="utf8")
            for forbidden in ("from data.tests","import data.tests",
                              "import openai","import anthropic",
                              "original_author_repo_only",
                              "public_source_exterior_wall_and_question_predicate_v062"):
                self.assertNotIn(forbidden,content)

    def test_81_still_no_provider_even_with_fake_permissions(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "rights":True,"provider":True,"budget":True,"approval":True,
            })
        self.assertEqual(self.report["paid_provider_model_calls"],0)

    def test_82_explicit_original_IFC_rights_and_model_approval_missing(self):
        self.assertFalse(self.report[
            "original_ifc_underlying_rights_and_provider_transfer_consent_verified"])
        self.assertIsNone(self.report["approved_paid_provider_model_snapshot_budget"])

    def test_83_frozen_report_does_not_overwrite(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):
                pass

    def test_84_original_source_file_still_unchanged_after_cases(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)


if __name__=="__main__":
    main()
