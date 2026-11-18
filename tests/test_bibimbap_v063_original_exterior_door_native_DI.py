"""v0.63 original IFC4X3 exterior Door+Opening complete D/I native tests.

Original public source, IFC4X3 full CSG boolean-through-wall cut, native
schema/root closure, original exterior-envelope physical predicate,
original repository mixed bool+float scorer isolated evaluator, genuine
Docker attestation and transactional rollback. No LLM/provider requests.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from unittest.mock import patch
import json

import ifcopenshell
import ifcopenshell.api.root
from lxml import etree

from tools.bibimbap_matched25_tools import DockerIFCExecutor,file_hash
from tools import audit_bibimbap_v063_original_exterior_door_DI as audit
from tools.bibimbap_v063_exterior_door_native import (
    SOURCE_SHA,TASK,Q,BOUNDS,MAX_CALLS,
    OriginalDoorNative063Error,
    source_ifc,source_envelope_v063,initial_full_source_v063,
    initial_compact_source_v063,parse_full_final_v063,
    restore_managed_final_v063,
    compile_real_original_IFC_v063,
    independent_real_original_door_scope_v063,
    source_public_exterior_pass_v063,
    semantic_digest_after_native_oracle_v063,
)
from tools.bibimbap_v063_exterior_door_sessions import (
    DirectFullState063,DirectManagedState063,LiveDockerPython063,
)
from tools.bibimbap_v057_provenance import (
    ProviderTrialBlocked057,refuse_all_model_trials_v057,
)

FROZEN_SHA="77ea754501be7142319b425d31f17fd60b1ade9addb724ace4ecf7b70aba2437"


class GenuineOriginalExteriorDoor063(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text(encoding="utf8"))
        cls.row=next(r for r in audit.public_45(audit.AUTHOR,audit.DATA)
                     if r["test_id"]==TASK)
        cls.source=audit.DATA/"ifc"/cls.row["original_source_ifc_relpath"]
        cls.source_model=source_ifc(cls.source,source_sha=SOURCE_SHA)
        cls.outer,cls.outer_index=audit._source_host_by_category(
            cls.source_model,"OUTER")
        cls.inner,cls.inner_index=audit._source_host_by_category(
            cls.source_model,"INNER")
        cls.positive=audit._fixture(
            "FOCUSED_PUBLIC_OUTER_POSITIVE",cls.outer,"OUTER",.9,2.1)
        cls.internal=audit._fixture(
            "FOCUSED_PUBLIC_INNER_NEGATIVE",cls.inner,"INNER",.9,2.1)
        cls.small=audit._fixture(
            "FOCUSED_PUBLIC_OUTER_SMALL_NEGATIVE",cls.outer,"OUTER",.45,1.2)
        cls.initial=initial_full_source_v063(
            cls.source,source_sha=SOURCE_SHA)
        cls.compact=initial_compact_source_v063(
            cls.source,source_sha=SOURCE_SHA)
        cls.original_wall_guids=sorted(
            w.GlobalId for w in cls.source_model.by_type("IfcWall"))

    def setUp(self):
        self.temp=TemporaryDirectory(prefix="v063-original-CsgDoor-")
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def d(self):
        return DirectFullState063(self.source,self.folder/"D")

    def m(self):
        return DirectManagedState063(self.source,self.folder/"M")

    def i(self):
        return LiveDockerPython063(self.source,self.folder/"I")

    def full(self,state=None):
        return audit._populate_xml(
            self.initial,state or self.positive,managed=False)

    def managed(self,state=None):
        return audit._populate_xml(
            self.compact,state or self.positive,managed=True)

    def bad_full(self,xml):
        with self.assertRaises(Exception):
            parse_full_final_v063(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def bad_managed(self,xml):
        with self.assertRaises(Exception):
            restore_managed_final_v063(
                self.source,xml.encode("utf8"),source_sha=SOURCE_SHA)

    def candidate(self,state=None,name="positive.ifc"):
        parsed=parse_full_final_v063(
            self.source,self.full(state).encode("utf8"),source_sha=SOURCE_SHA)
        out=self.folder/name
        compile_real_original_IFC_v063(
            self.source,out,source_sha=SOURCE_SHA,state=parsed)
        return out

    def test_01_frozen_report_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),FROZEN_SHA)

    def test_02_frozen_report_canonical_exact_bytes(self):
        self.assertEqual(audit.REPORT.read_bytes(),audit.canonical(self.report))

    def test_03_parent_v062_report_immutable(self):
        self.assertEqual(file_hash(audit.PARENT),audit.PARENT_SHA)

    def test_04_preselected_v058_six_source_cohort_immutable(self):
        self.assertEqual(file_hash(audit.FROZEN),audit.FROZEN_SHA)

    def test_05_fixed_six_original_task_ids_preserved(self):
        self.assertEqual(self.report["v058_six_task_selection_preserved"],
                         audit.FIXED_SIX)

    def test_06_new_original_native_task_only_topology05(self):
        self.assertEqual(self.report["new_native_original_task_admitted_v063"],
                         [TASK])

    def test_07_current_exact_five_six_original_source_support(self):
        self.assertEqual(
            self.report["five_of_six_original_fixed_source_native_developer_supported"],
            sorted(audit.SUPPORTED))
        self.assertEqual(self.report["remaining_original_fixed_task_UNSUPPORTED"],
                         ["geometry_test_03"])

    def test_08_original_45_task_31_IFC_input_source_population(self):
        self.assertEqual(self.report["original_45_public_task_count"],45)
        self.assertEqual(self.report[
            "original_31_unique_IFC_source_model_count"],31)

    def test_09_original_source_exact_SHA_and_no_change(self):
        self.assertEqual(file_hash(self.source),SOURCE_SHA)
        self.assertEqual(self.row["original_ifc_sha256"],SOURCE_SHA)

    def test_10_original_native_IFC4X3_units_mm(self):
        self.assertEqual(self.source_model.schema,"IFC4X3")
        self.assertEqual(self.report["source_native_length_unit"],"MILLIMETER")

    def test_11_original_seven_walls_two_slabs_nine_path_joins(self):
        f=self.source_model
        self.assertEqual(len(f.by_type("IfcWall")),7)
        self.assertEqual(len(f.by_type("IfcSlab")),2)
        self.assertEqual(len(f.by_type("IfcRelConnectsPathElements")),9)

    def test_12_original_no_door_opening_or_explicit_space(self):
        f=self.source_model
        self.assertEqual(len(f.by_type("IfcDoor")),0)
        self.assertEqual(len(f.by_type("IfcOpeningElement")),0)
        self.assertEqual(len(f.by_type("IfcSpace")),0)

    def test_13_original_exact_416_STEP_entities_116_Roots(self):
        self.assertEqual(len(list(self.source_model)),416)
        self.assertEqual(len(self.source_model.by_type("IfcRoot")),116)

    def test_14_original_source_horizontal_envelope(self):
        self.assertEqual(source_envelope_v063(self.source_model),
                         (0.,7.7,0.,8.1))

    def test_15_actual_original_outer_host_is_boundary(self):
        self.assertAlmostEqual(
            self.outer.ObjectPlacement.RelativePlacement.Location.Coordinates[1],
            100.,places=3)

    def test_16_original_internal_host_not_boundary(self):
        self.assertAlmostEqual(
            self.inner.ObjectPlacement.RelativePlacement.Location.Coordinates[0],
            5000.,places=3)

    def test_17_full_source_XML_bytes_3971(self):
        self.assertEqual(len(self.initial),3971)
        self.assertEqual(self.report[
            "original_full_source_xml_utf8_bytes"],3971)

    def test_18_compact_managed_source_XML_bytes_974(self):
        self.assertEqual(len(self.compact),974)
        self.assertEqual(self.report[
            "original_compact_managed_source_xml_utf8_bytes"],974)

    def test_19_full_source_all_seven_original_Wall_roster(self):
        root=etree.fromstring(self.initial)
        self.assertEqual(
            [x.get("ifcGuid") for x in root[1]],self.original_wall_guids)
        self.assertEqual(len(root[2]),0)

    def test_20_compact_all_seven_original_Wall_roster(self):
        root=etree.fromstring(self.compact)
        self.assertEqual(
            [x.get("ifcGuid") for x in root[0]],self.original_wall_guids)
        self.assertEqual(len(root[1]),0)

    def test_21_exact_source_read_byte_identical_three_D_I_arms(self):
        D,M,I=self.d(),self.m(),self.i()
        value=[x.call("read_building_xml",{"query":"source"})
               for x in (D,M,I)]
        self.assertEqual([x["status"] for x in value],["ok"]*3)
        self.assertEqual(value[0]["xml"],value[1]["xml"])
        self.assertEqual(value[1]["xml"],value[2]["xml"])
        self.assertEqual(value[0]["xml"].encode("utf8"),self.initial)

    def test_22_read_tool_schema_identical_D_I(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual(D.tools[0],M.tools[0])
        self.assertEqual(M.tools[0],I.tools[0])

    def test_23_editing_tool_schemas_are_distinct(self):
        D,M,I=self.d(),self.m(),self.i()
        self.assertEqual([
            D.tools[1]["name"],M.tools[1]["name"],I.tools[1]["name"]],
            ["submit_building_xml","submit_managed_final_state","execute_ifc_code"])

    def test_24_real_I_native_worker_is_DockerIFCExecutor(self):
        self.assertIs(type(self.i().executor),DockerIFCExecutor)

    def test_25_full_and_compact_declarative_source_host_identity(self):
        whole,parsed=restore_managed_final_v063(
            self.source,self.managed().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(whole,self.full().encode("utf8"))
        self.assertEqual(parsed["host_guid"],self.outer.GlobalId)

    def test_26_declarative_new_ifc_Guids_and_rels_explicit(self):
        parsed=parse_full_final_v063(
            self.source,self.full().encode("utf8"),source_sha=SOURCE_SHA)
        self.assertEqual(parsed["door_guid"],self.positive["door_guid"])
        self.assertEqual(parsed["opening_guid"],self.positive["opening_guid"])

    def test_27_D_full_compiles_actual_native_CSG_door(self):
        D=self.d()
        grade=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(grade["status"],"ok")
        self.assertEqual(grade["actual_native_IfcDoor_added"],1)
        self.assertEqual(grade["actual_native_IfcOpeningElement_added"],1)
        self.assertTrue(grade["source_original_Wall_CSG_full_thickness_cut"])
        self.assertEqual(file_hash(D.output_ifc),grade["native_ifc_sha256"])

    def test_28_D_managed_compiles_actual_native_CSG_door(self):
        M=self.m()
        result=M.call("submit_managed_final_state",
                      {"xml_text":self.managed()})
        self.assertEqual(result["status"],"ok")
        self.assertTrue(result["native_ifc_committed"])
        self.assertEqual(result["original_IFC4X3_schema_error_delta"],0)

    def test_29_D_full_and_managed_complete_xml_equal(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
                         {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
                         {"xml_text":self.managed()})["status"],"ok")
        self.assertEqual(D.current_xml,M.current_xml)

    def test_30_D_full_and_managed_native_semantics_equal(self):
        D,M=self.d(),self.m()
        self.assertEqual(D.call("submit_building_xml",
                         {"xml_text":self.full()})["status"],"ok")
        self.assertEqual(M.call("submit_managed_final_state",
                         {"xml_text":self.managed()})["status"],"ok")
        digests=[]
        for session in (D,M):
            result=independent_real_original_door_scope_v063(
                self.source,session.output_ifc,source_sha=SOURCE_SHA)
            digests.append(semantic_digest_after_native_oracle_v063(result))
        self.assertEqual(digests[0],digests[1])

    def test_31_native_true_door_full_thickness_wall_CSG_volume(self):
        out=self.candidate()
        r=independent_real_original_door_scope_v063(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertEqual(r[
            "native_real_wall_full_thickness_boolean_volume_removed_m3"],.418)
        self.assertEqual(r["original_IFC4X3_schema_errors_introduced"],0)

    def test_32_all_416_source_STEP_entities_preserved(self):
        out=self.candidate()
        r=independent_real_original_door_scope_v063(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertEqual(r["original_source_STEP_entities_unchanged"],416)

    def test_33_new_original_Door_Opening_reopened(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        self.assertEqual(len(f.by_type("IfcDoor")),1)
        self.assertEqual(len(f.by_type("IfcOpeningElement")),1)

    def test_34_new_original_storey_containment_reopened(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        door=f.by_type("IfcDoor")[0]
        self.assertTrue(any(door in r.RelatedElements
                            for r in f.by_type("IfcRelContainedInSpatialStructure")))

    def test_35_native_good_outer_wall_public_exterior_pass(self):
        out=self.candidate()
        grade=source_public_exterior_pass_v063(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertTrue(grade["door_wall_is_outer_envelope_boundary"])
        self.assertTrue(grade["physically_outside_connection_proxy_pass"])

    def test_36_native_structurally_valid_internal_wall_public_fail(self):
        out=self.candidate(self.internal,"internal.ifc")
        structural=independent_real_original_door_scope_v063(
            self.source,out,source_sha=SOURCE_SHA)
        semantic=source_public_exterior_pass_v063(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertEqual(structural[
            "status"],"V063_ORIGINAL_CSG_DOOR_OPENING_NATIVE_SCOPE_AND_SCHEMA_PASS")
        self.assertFalse(semantic["door_wall_is_outer_envelope_boundary"])
        self.assertFalse(semantic["physically_outside_connection_proxy_pass"])

    def test_37_native_structurally_valid_small_door_public_fail(self):
        out=self.candidate(self.small,"small.ifc")
        structural=independent_real_original_door_scope_v063(
            self.source,out,source_sha=SOURCE_SHA)
        semantic=source_public_exterior_pass_v063(
            self.source,out,source_sha=SOURCE_SHA)
        self.assertEqual(structural["original_IFC4X3_schema_errors_introduced"],0)
        self.assertTrue(semantic["door_wall_is_outer_envelope_boundary"])
        self.assertFalse(semantic["new_door_reasonable_dimensions"])
        self.assertFalse(semantic["physically_outside_connection_proxy_pass"])

    def test_38_three_true_Docker_original_IFC_controls_report(self):
        self.assertEqual(self.report["real_pinned_Linux_Docker_I_native_IFC_cases"],3)
        self.assertTrue(all(row[
            "actual_pinned_isolated_Linux_Docker_general_Python_executed"]
            for row in self.report["developer_only_real_source_door_opening_controls"]))

    def test_39_nine_real_native_IFC_D_full_managed_Docker_cases(self):
        self.assertEqual(self.report[
            "actual_original_native_IFC_D_I_developer_cases"],9)
        self.assertEqual(self.report["real_D_FULL_original_native_IFC_cases"],3)
        self.assertEqual(self.report["real_D_MANAGED_original_native_IFC_cases"],3)

    def test_40_original_author_repo_valid_score_one(self):
        value=self.report["developer_only_real_source_door_opening_controls"][0][
            "original_author_repository_mixed_score_evaluator_only"]
        self.assertEqual(value["mean_score"],1.)
        self.assertEqual(value["original_repo_metrics"]["integrity_constraint"],1.)
        self.assertTrue(value["original_repo_metrics"]["right_location"])

    def test_41_original_author_internal_scores_same_one(self):
        rows=self.report["developer_only_real_source_door_opening_controls"]
        self.assertEqual(rows[1][
            "original_author_repository_mixed_score_evaluator_only"]["mean_score"],1.)
        self.assertFalse(rows[1][
            "public_source_exterior_physical_semantic_evaluator_only"][
                "physically_outside_connection_proxy_pass"])

    def test_42_author_scoring_does_not_enforce_exterior_semantics(self):
        self.assertTrue(self.report[
            "original_author_score_equal_for_valid_exterior_and_invalid_interior"])
        scores=[r["original_author_repository_mixed_score_evaluator_only"]["mean_score"]
            for r in self.report["developer_only_real_source_door_opening_controls"]]
        self.assertEqual(scores[:2],[1.,1.])

    def test_43_small_door_author_falls_to_three_quarters(self):
        row=self.report["developer_only_real_source_door_opening_controls"][2]
        grading=row["original_author_repository_mixed_score_evaluator_only"]
        self.assertEqual(grading["mean_score"],.75)
        self.assertFalse(grading["original_repo_metrics"]["right_dimensions"])
        self.assertTrue(grading["original_repo_metrics"]["right_location"])

    def test_44_original_repo_grader_has_float_integrity_not_boolean(self):
        row=self.report["developer_only_real_source_door_opening_controls"][0]
        v=row["original_author_repository_mixed_score_evaluator_only"][
            "original_repo_metrics"]["integrity_constraint"]
        self.assertIs(type(v),float)
        self.assertEqual(v,1.)

    def test_45_canonical_native_ifc_semantic_digest_same_all_three_arms(self):
        records=self.report["developer_only_real_source_door_opening_controls"]
        self.assertTrue(self.report[
            "all_three_D_I_original_native_semantic_DIGESTS_equal"])
        self.assertEqual(len({x["all_D_I_original_native_semantic_digest_SHA256"]
                              for x in records}),3)

    def test_46_actual_raw_file_SHA_equality_NOT_claimed(self):
        for r in self.report["developer_only_real_source_door_opening_controls"]:
            self.assertIsNotNone(r["all_D_I_original_native_semantic_digest_SHA256"])
        self.assertEqual(self.report["actual_model_generated_trials"],0)

    def test_47_report_public_solution_target_original_GUID_redacted(self):
        raw=audit.REPORT.read_text(encoding="utf8")
        self.assertNotIn(self.outer.GlobalId,raw)
        self.assertNotIn(self.inner.GlobalId,raw)
        self.assertTrue(all(x["host_original_Wall_GUID_redacted"]
            for x in self.report["developer_only_real_source_door_opening_controls"]))

    def test_48_original_paper_official_scorer_not_assumed_same(self):
        self.assertFalse(self.report[
            "published_paper_official_scoring_version_parity_verified"])
        self.assertIsNone(self.report["published_paper_official_model_score"])

    def test_49_original_no_source_IfcSpace_true_room_graph_unverifiable(self):
        self.assertTrue(self.report[
            "source_original_IFC_has_NO_IfcSpace_true_inside_room_graph_not_verifiable"])

    def test_50_initial_whole_source_no_created_products_refused(self):
        self.bad_full(self.initial.decode("utf8"))

    def test_51_initial_managed_no_created_products_refused(self):
        self.bad_managed(self.compact.decode("utf8"))

    def test_52_missing_one_of_new_Door_or_Opening_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2].remove(x[2][1])
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_53_swapped_new_Door_Opening_order_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2].insert(0,x[2][1])
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_54_changed_Door_fills_opening_refusal(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][1].set("fillsOpeningGuid","0"*22)
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_55_duplicate_new_IFC_door_opening_GUID_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][1].set("ifcGuid",x[2][0].get("ifcGuid"))
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_56_reuse_existing_original_source_Wall_GUID_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][1].set("ifcGuid",self.outer.GlobalId)
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_57_unknown_original_host_wall_GUID_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][0].set("hostOriginalWallGuid","0"*22)
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_58_bad_door_bbox_not_contained_in_opening_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][1].set("minYM","1.000000")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_59_Opening_not_through_wall_thickness_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][0].set("minYM","0.050000")
        x[2][0].set("maxYM","0.130000")
        x[2][1].set("minYM","0.060000")
        x[2][1].set("maxYM","0.105000")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_60_Door_too_far_from_original_host_wall_rejected(self):
        x=etree.fromstring(self.full().encode("utf8"))
        for element in x[2]:
            element.set("minXM",f"{float(element.get('minXM'))+20.:.6f}")
            element.set("maxXM",f"{float(element.get('maxXM'))+20.:.6f}")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_61_Opening_above_original_Wall_top_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][0].set("maxZM","3.000000")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_62_negative_unbounded_nonfinite_world_bbox_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][0].set("minXM","NaN")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_63_noncanonical_numeric_roundoff_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][0].set("minXM","3.6000000")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_64_incomplete_seven_original_Wall_roster_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[1].remove(x[1][0])
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_65_duplicate_reordered_original_roster_refused(self):
        x=etree.fromstring(self.managed().encode("utf8"))
        x[0].insert(0,x[0][-1])
        self.bad_managed(etree.tostring(x).decode("utf8"))

    def test_66_original_immutable_source_geometry_tamper_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        p=next(t for t in x[0][1] if t.get("minXM") is not None)
        p.set("minXM","123.000000")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_67_original_IFC_source_SHA_mutation_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x.set("sourceOriginalIFCSha256","f"*64)
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_68_compact_original_full_source_SHA_mutation_refused(self):
        x=etree.fromstring(self.managed().encode("utf8"))
        x.set("sourceFullBuildingStateSha256","f"*64)
        self.bad_managed(etree.tostring(x).decode("utf8"))

    def test_69_command_opcode_or_extra_new_attrs_refused(self):
        x=etree.fromstring(self.full().encode("utf8"))
        x[2][1].set("operation","create")
        self.bad_full(etree.tostring(x).decode("utf8"))

    def test_70_XXE_DTD_injection_refused(self):
        raw=self.full().encode("utf8")
        dtd=b"<!DOCTYPE BuildingState [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"
        self.bad_full(raw.replace(b"?>",b"?>"+dtd,1).decode("utf8"))

    def test_71_native_missing_IfcRelFills_chain_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.remove(f.by_type("IfcRelFillsElement")[0])
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_72_native_missing_Door_representation_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.by_type("IfcDoor")[0].Representation=None
        f.write(str(out))
        with self.assertRaises(Exception):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_73_native_new_Door_missing_storey_container_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        door=f.by_type("IfcDoor")[0]
        for rel in f.by_type("IfcRelContainedInSpatialStructure"):
            if door in rel.RelatedElements:
                f.remove(rel)
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_74_native_original_Wall_name_modified_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.by_guid(self.outer.GlobalId).Name="CORRUPTED_ORIGINAL_WALL"
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_75_native_additional_unrelated_Root_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        ifcopenshell.api.root.create_entity(f,ifc_class="IfcFurniture")
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_76_native_unreachable_anonymous_STEP_entity_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.create_entity("IfcCartesianPoint",Coordinates=(12.,35.,4.))
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_77_native_new_Door_OverallWidth_mm_spoof_refused(self):
        out=self.candidate()
        f=ifcopenshell.open(str(out))
        f.by_type("IfcDoor")[0].OverallWidth=900000.
        f.write(str(out))
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,out,source_sha=SOURCE_SHA)

    def test_78_native_source_original_alias_refused(self):
        with self.assertRaises(OriginalDoorNative063Error):
            independent_real_original_door_scope_v063(
                self.source,self.source,source_sha=SOURCE_SHA)

    def test_79_genuine_Docker_shallow_door_opening_rejected_in_report(self):
        self.assertTrue(self.report[
            "actual_Docker_shallow_non_through_wall_opening_rejected"])

    def test_80_genuine_Docker_unfilled_Door_relation_rejected_in_report(self):
        self.assertTrue(self.report[
            "actual_Docker_unfilled_door_relation_rejected"])

    def test_81_actual_Docker_good_then_second_Door_sha_preserved_in_report(self):
        self.assertTrue(self.report[
            "actual_Docker_valid_then_second_door_rejected_last_IFC_sha_preserved"])

    def test_82_D_full_good_then_bad_complete_roster_rollback(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",{
            "xml_text":self.full()})["status"],"ok")
        before_sha=file_hash(D.output_ifc)
        old_xml=D.current_xml
        wrong=D.call("submit_building_xml",{"xml_text":"<invalid/>"})
        self.assertEqual(wrong["status"],"error")
        self.assertEqual(file_hash(D.output_ifc),before_sha)
        self.assertEqual(D.current_xml,old_xml)

    def test_83_D_managed_good_then_bad_complete_roster_rollback(self):
        M=self.m()
        self.assertEqual(M.call("submit_managed_final_state",{
            "xml_text":self.managed()})["status"],"ok")
        before_sha=file_hash(M.output_ifc)
        old_xml=M.current_xml
        wrong=M.call("submit_managed_final_state",{"xml_text":"<invalid/>"})
        self.assertEqual(wrong["status"],"error")
        self.assertEqual(file_hash(M.output_ifc),before_sha)
        self.assertEqual(M.current_xml,old_xml)

    def test_84_identical_valid_D_final_state_replay_rejected(self):
        D=self.d()
        self.assertEqual(D.call("submit_building_xml",{
            "xml_text":self.full()})["status"],"ok")
        sha=file_hash(D.output_ifc)
        wrong=D.call("submit_building_xml",{"xml_text":self.full()})
        self.assertEqual(wrong["error_type"],"ExactFinalStateReplayRejected")
        self.assertEqual(file_hash(D.output_ifc),sha)

    def test_85_strict_max_25_tool_calls_all_D_I(self):
        for session in (self.d(),self.m(),self.i()):
            for _ in range(MAX_CALLS):
                self.assertEqual(session.call("read_building_xml",{
                    "query":"source"})["status"],"ok")
            self.assertEqual(session.call("read_building_xml",{
                "query":"source"})["error_type"],"ToolBudgetExhausted")

    def test_86_wrong_D_tool_not_invokable_via_compact(self):
        M=self.m()
        self.assertEqual(M.call("submit_building_xml",{
            "xml_text":self.full()})["error_type"],
            "WrongDeclarativeFinalStateTool")

    def test_87_blocked_Docker_never_executes_native_Python(self):
        I=self.i()
        with patch("tools.bibimbap_v063_exterior_door_sessions.live_pinned_local_runtime_admission_v052",
                   return_value={"status":"BLOCKED_RUNTIME","reason":"NO_DOCKER"}
                   ),patch.object(I.executor,"run") as fake:
            outcome=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(outcome["error_type"],"BLOCKED_RUNTIME")
        fake.assert_not_called()
        self.assertIsNone(I.output_ifc)

    def test_88_fake_Docker_success_without_real_IFC_CSG_edit_refused(self):
        I=self.i()
        with patch("tools.bibimbap_v063_exterior_door_sessions.live_pinned_local_runtime_admission_v052",
                   return_value={"status":"RUNTIME_ADMITTED"}
                   ),patch.object(I.executor,"run",return_value={
                       "status":"ok","committed":True,
                       "backend":"linux_docker_sandbox"}):
            outcome=I.call("execute_ifc_code",{"code":"commit()"})
        self.assertEqual(outcome["error_type"],"NativeDockerWorkerOrCSGScopeRejected")
        self.assertIsNone(I.output_ifc)

    def test_89_author_grader_private_targets_never_in_model_host(self):
        for name in ("bibimbap_v063_exterior_door_native.py",
                     "bibimbap_v063_exterior_door_sessions.py"):
            content=(audit.ROOT/"tools"/name).read_text(encoding="utf8")
            for forbidden in ("data.tests","original_author_repo_only",
                              "import anthropic","import openai",
                              "source_public_exterior_pass_v063("):
                if name=="bibimbap_v063_exterior_door_native.py" and forbidden=="source_public_exterior_pass_v063(":
                    # This source-only public evaluator is intentionally
                    # separated in this library but not called by native
                    # compilation nor the model-facing session.
                    continue
                self.assertNotIn(forbidden,content)
        session=(audit.ROOT/"tools"/"bibimbap_v063_exterior_door_sessions.py")
        self.assertNotIn("source_public_exterior_pass_v063",session.read_text("utf8"))

    def test_90_no_launch_even_all_fake_rights_model_money_approvals(self):
        with self.assertRaises(ProviderTrialBlocked057):
            refuse_all_model_trials_v057({
                "rights":True,"paid_budget":True,
                "model_snapshot":True,"approval":True})
        self.assertEqual(self.report["paid_provider_calls"],0)

    def test_91_original_source_rights_and_paid_model_not_assumed(self):
        self.assertFalse(self.report[
            "underlying_original_IFC_rights_and_provider_transfer_approval"])
        self.assertIsNone(self.report[
            "approved_model_snapshot_D_I_actual_tokens_cost_budget"])

    def test_92_frozen_report_exclusive_create_never_overwrite(self):
        with self.assertRaises(FileExistsError):
            with audit.REPORT.open("xb"):
                pass


if __name__=="__main__":
    main()
