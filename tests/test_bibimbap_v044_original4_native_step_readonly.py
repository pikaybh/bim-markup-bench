"""v0.44 original4 complete native source read-only positive/negative tests.

Research-only: 45 original task/source/question immutable, 4 literal native IFC
DATA STEP sources read through the actual model-facing tool, independent
oracle, and all real submission attempts explicitly unsupported without IFC.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from tools import audit_bibimbap_v044_original4_native_step_read as audit
from tools.bibimbap_matched25_tools import (
    XmlSourceEditSession,UnsupportedArm,file_hash)
from src.runtime.experimental_v44_original_native_step_readonly import (
    PINS,NativeSourceReadOnly044Error,project_native_readonly_source_v044,
    verify_original_v044_xml_exactly_readonly,XSD)
from tools.bibimbap_v044_independent_original_native_source_oracle import (
    ORIGINAL_PINS,IndependentV044Error,validate_original_v044_native_model_read)

BASE=Path(r"D:\문서\D__1_Projects\202611")
AUTHOR=BASE/"bibimbap-author-upstream"
DATA=BASE/"bibimbap-author-data"
REPORT=audit.ROOT/"reports"/"bibimbap_v044_original4_native_STEP_readonly_20261117.json"
FROZEN_SHA="dc58535db3dbec85ba610d3e8b9104c660c4bf0e3e019f9a20ee3a32a012281a"
N="{urn:bim-markup-bench:toy:v0}"


class OriginalFourNativeSourceV044(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(REPORT.read_text(encoding="utf8"))
        cls.originals=audit.original_45(AUTHOR,DATA)
        cls.rows={x["original_public_task_id"]:x for x in cls.report["rows"]}
        cls.tmp=TemporaryDirectory(prefix="v044-original4-read-source-test-")
        cls.sources={}
        cls.sessions={}
        cls.xml={}
        for i,(sha,pin) in enumerate(PINS.items()):
            tid=pin[0]
            p=DATA/"ifc"/cls.originals[tid]["original_source_ifc_relpath"]
            s=XmlSourceEditSession(
                p,Path(cls.tmp.name)/str(i),
                experimental_original_native_readonly_v044=True)
            cls.sources[tid]=p
            cls.sessions[tid]=s
            cls.xml[tid]=s.call("read_building_xml",{})["xml"].encode("utf8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.scratch=TemporaryDirectory(prefix="v044-poison-source-test-")
        self.addCleanup(self.scratch.cleanup)
        self.dir=Path(self.scratch.name)

    def root(self,tid="topological_test_11"):
        return etree.fromstring(self.xml[tid])

    def sections(self,root):
        return root.find(N+"OriginalNativeIFCSource")

    def native(self,root,which):
        return self.sections(root).find(N+which)

    def reject(self,action,*,tid="topological_test_11"):
        root=self.root(tid)
        action(root)
        altered=etree.tostring(root,encoding="utf8")
        with self.assertRaises(IndependentV044Error):
            validate_original_v044_native_model_read(
                self.sources[tid],altered,task_id=tid)
        self.assertEqual(file_hash(self.sources[tid]),
                         self.originals[tid]["original_ifc_sha256"])

    def test_01_frozen_v044_audit_report_exact_sha(self):
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_02_previous_v043_report_unchanged(self):
        self.assertEqual(file_hash(audit.ROOT/audit.PREVIOUS[0]),
                         audit.PREVIOUS[1])

    def test_03_original_author_git_sha_remains_pinned(self):
        self.assertEqual(audit._head(AUTHOR),audit.AUTHOR_SHA)

    def test_04_original_dataset_git_sha_remains_pinned(self):
        self.assertEqual(audit._head(DATA),audit.DATA_SHA)

    def test_05_original_45_public_questions_csv_sha_pinned(self):
        self.assertEqual(file_hash(DATA/"prompts/all_questions.csv"),
                         audit.QUESTION_CSV_SHA)

    def test_06_original_45_ITT_15_each_original_crud(self):
        self.assertEqual(len(self.originals),45)
        self.assertEqual(Counter(t["crud"] for t in self.originals.values()),
                         {"create":15,"update":15,"delete":15})

    def test_07_original_unique_source_IFC_files_31(self):
        self.assertEqual(len({t["original_ifc_sha256"]
                              for t in self.originals.values()}),31)

    def test_08_all_original_questions_hashes_and_4_source_SHAs(self):
        for sha,(tid,crud,q,entities,products) in PINS.items():
            t=self.originals[tid]
            self.assertEqual(t["original_ifc_sha256"],sha)
            self.assertEqual(t["public_question_sha256"],q)
            self.assertEqual(t["crud"],crud)
            self.assertEqual(file_hash(self.sources[tid]),sha)
            self.assertEqual(ORIGINAL_PINS[tid],(sha,entities,products))

    def test_09_prior_4_benchmark_source_reads_really_unsupported(self):
        for row in self.rows.values():
            self.assertEqual(row["previous_v043_default_model_read_status"],
                             "UNSUPPORTED_BACKEND_NOT_MODEL_FAILURE")

    def test_10_four_current_true_read_building_xml_calls_all_succeed(self):
        self.assertEqual(len(self.sessions),4)
        self.assertEqual(set(self.sessions),set(ORIGINAL_PINS))
        for tid,s in self.sessions.items():
            r=s.call("read_building_xml",{})
            self.assertEqual(r["status"],"ok")
            self.assertEqual(r["xml"].encode("utf8"),self.xml[tid])
            self.assertFalse(r["native_candidate_available"])

    def test_11_all_four_native_original_ifc_sources_are_IFC4X3_mm(self):
        for tid,p in self.sources.items():
            f=ifcopenshell.open(str(p))
            self.assertEqual(f.schema,"IFC4X3")
            self.assertAlmostEqual(ifcopenshell.util.unit.calculate_unit_scale(f),.001)

    def test_12_all_1304_native_IFC_STEP_DATA_lines_exactly_visible(self):
        self.assertEqual(
            self.report["totals_for_exact_four_unique_original_sources"][
                "source_original_native_STEP_DATA_entities_exactly_model_visible"],1304)

    def test_13_all_47_original_IFC_products_guid_and_class_exact(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_IfcProduct_GUIDs_with_exact_class_name_and_source_step_visible"],47)

    def test_14_all_192_native_relationships_and_endpoint_source_ids_exact(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_IfcRelationship_GUIDs_and_exact_source_endpoints_visible"],192)

    def test_15_all_150_original_property_sets_and_values_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_IfcPropertySet_names_Guids_properties_visible"],150)

    def test_16_all_7_original_ifc_materials_names_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_IfcMaterial_names_visible"],7)

    def test_17_all_47_original_IfcLocalPlacement_matrices_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_IfcLocalPlacement_matrices_visible"],47)

    def test_18_all_30_original_native_world_meshes_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_original_physical_product_world_mesh_visible"],30)
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_native_original_physical_world_mesh_unavailable_explicit"],0)

    def test_19_all_252_original_world_1um_vertices_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_original_world_mesh_ordered_vertices_visible"],252)

    def test_20_all_384_original_world_indexed_source_triangles_visible(self):
        self.assertEqual(self.report["totals_for_exact_four_unique_original_sources"][
            "source_original_world_mesh_ordered_triangles_visible"],384)

    def test_21_model_facing_original_source_read_stays_under_XML_cap(self):
        for xml in self.xml.values():
            self.assertLessEqual(len(xml),300000)

    def test_22_model_facing_XML_is_strictly_dedicated_valid_XSD(self):
        schema=etree.XMLSchema(etree.parse(str(XSD)))
        for xml in self.xml.values():
            self.assertTrue(schema.validate(etree.fromstring(xml)))

    def test_23_independent_source_oracle_four_real_original_IFCs_pass(self):
        for tid,p in self.sources.items():
            o=validate_original_v044_native_model_read(
                p,self.xml[tid],task_id=tid)
            self.assertEqual(o["task_id"],tid)
            self.assertTrue(o["all_original_source_STEP_DATA_entity_lines_byte_text_and_order_match"])
            self.assertFalse(o["original_IFC_native_update_delete_mutation_available"])

    def test_24_host_and_independent_separate_projector_source_proofs(self):
        for tid,p in self.sources.items():
            verify_original_v044_xml_exactly_readonly(
                p,self.xml[tid],original_native_sha256=self.originals[tid]["original_ifc_sha256"])

    def test_25_all_four_return_exact_same_source_on_repeat_reprojection(self):
        for tid,p in self.sources.items():
            projected=project_native_readonly_source_v044(
                p,original_native_sha256=self.originals[tid]["original_ifc_sha256"])
            self.assertEqual(projected.xml,self.xml[tid])

    def test_26_four_original_source_CUD_fail_closed_even_unchanged_XML(self):
        for tid,s in self.sessions.items():
            result=s.call("submit_building_xml",{"xml_text":self.xml[tid].decode("utf8")})
            self.assertEqual(result["status"],"error")
            self.assertEqual(result["error_type"],"UnsupportedArm")
            self.assertEqual(result["error"],
                "V044_READ_ONLY_ORIGINAL_NATIVE_SOURCE_UPDATE_DELETE_MUTATION_UNSUPPORTED")
            self.assertFalse(result["native_ifc_committed"])
            self.assertTrue(result["last_valid_xml_preserved"])
            self.assertIsNone(s.output_ifc)
            self.assertEqual(s.current_xml,self.xml[tid])

    def test_27_real_changed_XML_submit_fails_closed(self):
        for tid,s in self.sessions.items():
            fake=self.xml[tid].decode("utf8").replace("MILLIMETER_NATIVE","SPOOF_UNIT")
            r=s.call("submit_building_xml",{"xml_text":fake})
            self.assertEqual(r["status"],"error")
            self.assertFalse(r["native_ifc_committed"])
            self.assertTrue(r["last_valid_xml_preserved"])
            self.assertEqual(s.current_xml,self.xml[tid])

    def test_28_no_candidate_native_IFC_in_model_workspaces_after_rejects(self):
        for s in self.sessions.values():
            self.assertIsNone(s.normalized)
            self.assertFalse((s.folder/"normalized_original_m.ifc").exists())
            self.assertIsNone(s.output_ifc)
            self.assertEqual(list(s.folder.rglob("candidate_*.ifc")),[])
            self.assertEqual(list(s.folder.glob("attempt_*")),[])

    def test_29_native_source_original_hash_preserved_after_all_submissions(self):
        for tid,p in self.sources.items():
            self.assertEqual(file_hash(p),self.originals[tid]["original_ifc_sha256"])

    def test_30_editor_tool_description_explicitly_warns_UNSUPPORTED(self):
        for s in self.sessions.values():
            names={item["name"]:item["description"] for item in s.tools}
            self.assertEqual(set(names),{"read_building_xml","submit_building_xml"})
            self.assertIn("UNSUPPORTED",names["submit_building_xml"])
            self.assertIn("IMMUTABLE",names["read_building_xml"].upper())

    def test_31_readonly_source_flag_mutually_exclusive_with_legacy(self):
        for key in (
                "experimental_original_legacy_v08",
                "experimental_original_complex_v039",
                "experimental_original_room_v040",
                "experimental_original_p3_v041",
                "experimental_original_native_slab_v042"):
            with self.assertRaisesRegex(UnsupportedArm,"mutually exclusive"):
                XmlSourceEditSession(self.sources["geometry_test_14"],
                    self.dir/key,
                    experimental_original_native_readonly_v044=True,
                    **{key:True})

    def test_32_source_nonpinned_original_IFC_refused(self):
        other=DATA/"ifc"/"01/02/01_02_002.ifc"
        self.assertTrue(other.is_file())
        with self.assertRaisesRegex(UnsupportedArm,"only exactly four"):
            XmlSourceEditSession(other,self.dir/"nonpin",
                experimental_original_native_readonly_v044=True)

    def test_33_mutated_original_source_clone_refused(self):
        f=ifcopenshell.open(str(self.sources["geometry_test_14"]))
        f.by_type("IfcBuilding")[0].Name="SPOOFED SOURCE"
        path=self.dir/"spoof.ifc"
        f.write(str(path))
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(path,self.dir/"mutated",
                experimental_original_native_readonly_v044=True)

    def test_34_native_source_unit_converted_to_metres_refused(self):
        f=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(self.sources["geometry_test_14"])),"METER")
        path=self.dir/"source-metres.ifc"
        f.write(str(path))
        with self.assertRaises(UnsupportedArm):
            XmlSourceEditSession(path,self.dir/"meters",
                experimental_original_native_readonly_v044=True)

    def test_35_original_question_sha_poisoned_pins_refused(self):
        item=next(iter(PINS.items()))
        sha,t=item
        invalid=dict(PINS);invalid[sha]=(t[0],t[1],"0"*64,t[3],t[4])
        with patch.object(audit,"PINS",invalid):
            with self.assertRaisesRegex(ValueError,"SHA preregistered"):
                audit.original_45(AUTHOR,DATA)

    def test_36_wrong_original_45_population_denominator_refused(self):
        with patch.object(audit,"public_45",return_value=[
            t for t in self.originals.values() if t["test_id"]!="geometry_test_14"]):
            with self.assertRaisesRegex(ValueError,"ITT"):
                audit.original_45(AUTHOR,DATA)

    def test_37_prior_original_v043_baseline_report_sha_poison_refused(self):
        with patch.object(audit,"PREVIOUS",(audit.PREVIOUS[0],"f"*64)):
            with self.assertRaisesRegex(ValueError,"v0.43"):
                audit.original_45(AUTHOR,DATA)

    def test_38_forged_xml_source_root_SHA_refused(self):
        self.reject(lambda r:r.set("sourceOriginalIFCSha256","0"*64))

    def test_39_forged_xml_source_schema_refused(self):
        self.reject(lambda r:r.set("sourceIfcSchema","IFC2X3"))

    def test_40_forged_xml_source_mutation_permission_refused(self):
        self.reject(lambda r:r.set("nativeMutationPermission","EDIT_ALLOWED"))

    def test_41_original_native_XML_source_section_deleted_refused(self):
        self.reject(lambda r:r.remove(r[0]))

    def test_42_original_native_XML_source_section_duplicate_refused(self):
        self.reject(lambda r:r.append(etree.fromstring(etree.tostring(r[0]))))

    def test_43_all_source_section_order_cannot_change(self):
        def poison(root):
            n=root[0]
            first=n[0];n.remove(first);n.append(first)
        self.reject(poison)

    def test_44_original_literal_STEP_line_changed_refused(self):
        self.reject(lambda r:self.native(r,"NativeStepRecords")[0].__setattr__(
            "text","#1=IFCCHANGEDSOURCE();"))

    def test_45_original_literal_STEP_line_deleted_refused(self):
        def poison(r):
            x=self.native(r,"NativeStepRecords");x.remove(x[0])
        self.reject(poison)

    def test_46_original_literal_STEP_line_added_refused(self):
        def poison(r):
            x=self.native(r,"NativeStepRecords")
            x.append(etree.fromstring(etree.tostring(x[0])))
        self.reject(poison)

    def test_47_original_literal_STEP_record_ID_changed_refused(self):
        self.reject(lambda r:self.native(r,"NativeStepRecords")[0].set(
            "sourceStepId","99999"))

    def test_48_original_literal_STEP_record_class_changed_refused(self):
        self.reject(lambda r:self.native(r,"NativeStepRecords")[0].set(
            "nativeIfcClass","IFCUNKNOWN"))

    def test_49_original_literal_STEP_entity_order_changed_refused(self):
        def poison(r):
            n=self.native(r,"NativeStepRecords")
            first=n[0];n.remove(first);n.append(first)
        self.reject(poison)

    def test_50_original_IFC_Product_GUID_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Products")[0].set("ifcGuid","0"*22))

    def test_51_original_IFC_Product_class_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Products")[0].set("nativeIfcClass","IfcSpace"))

    def test_52_original_IFC_Product_name_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Products")[0].set("originalName","BAD"))

    def test_53_original_IFC_Product_original_STEP_ID_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Products")[0].set("sourceStepId","9999"))

    def test_54_original_IFC_Product_readonly_permission_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Products")[0].set(
            "nativeMutationPermission","RW_EDIT"))

    def test_55_original_IFC_Product_original_list_drop_refused(self):
        def poison(r):
            n=self.native(r,"Products");n.remove(n[0])
        self.reject(poison)

    def test_56_original_IFC_relation_GUID_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Relations")[0].set("ifcGuid","0"*22))

    def test_57_original_IFC_relation_class_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Relations")[0].set(
            "nativeIfcClass","IfcRelSpaceBoundary"))

    def test_58_original_IFC_relation_endpoint_role_spoof_refused(self):
        self.reject(lambda r:next(x for x in self.native(r,"Relations")
                  if len(x)>0)[0].set("attribute","FALSIFIED_REL"))

    def test_59_original_IFC_relation_endpoint_original_STEP_ID_spoof_refused(self):
        self.reject(lambda r:next(x for x in self.native(r,"Relations")
                  if len(x)>0)[0].set("sourceStepId","9999"))

    def test_60_original_IFC_relation_endpoint_deleted_refused(self):
        def poison(r):
            n=next(x for x in self.native(r,"Relations") if len(x)>0)
            n.remove(n[0])
        self.reject(poison)

    def test_61_original_IFC_PropertySet_GUID_spoof_refused(self):
        self.reject(lambda r:self.native(r,"PropertySets")[0].set("ifcGuid","0"*22))

    def test_62_original_IFC_PropertySet_Name_spoof_refused(self):
        self.reject(lambda r:self.native(r,"PropertySets")[0].set(
            "originalName","FAKE_PROPERTY_SET"))

    def test_63_original_IFC_Property_name_spoof_refused(self):
        self.reject(lambda r:next(x for x in self.native(r,"PropertySets")
                  if len(x)>0)[0].set("originalName","FAKE_PROPERTY"))

    def test_64_original_IFC_Property_nominal_value_spoof_refused(self):
        def poison(r):
            target=next(x for s in self.native(r,"PropertySets")
                        for x in s if x.get("sourceNominalValue") is not None)
            target.set("sourceNominalValue","UNCHANGED_FAKE")
        self.reject(poison)

    def test_65_original_IFC_material_Name_spoof_refused(self):
        self.reject(lambda r:self.native(r,"Materials")[0].set(
            "originalName","FAKE_MATERIAL"))

    def test_66_original_IFC_material_deleted_refused(self):
        def poison(r):
            n=self.native(r,"Materials");n.remove(n[0])
        self.reject(poison)

    def test_67_original_IFC_local_placement_step_ID_spoof_refused(self):
        self.reject(lambda r:self.native(r,"LocalPlacements")[0].set(
            "sourceStepId","9999"))

    def test_68_original_IFC_local_placement_matrix_spoof_refused(self):
        self.reject(lambda r:self.native(r,"LocalPlacements")[0].set("m03","123.45"))

    def test_69_original_IFC_local_placement_parent_ref_spoof_refused(self):
        self.reject(lambda r:self.native(r,"LocalPlacements")[0].set(
            "parentPlacementStepId","9999"))

    def test_70_original_IFC_native_world_mesh_vertex_spoof_refused(self):
        self.reject(lambda r:next(x for x in self.native(r,"WorldGeometry")
                  if len(x)>0)[0][0].set("z","123.456"))

    def test_71_original_IFC_native_world_triangle_vertex_index_spoof_refused(self):
        self.reject(lambda r:next(x for x in self.native(r,"WorldGeometry")
                  if len(x)>0)[1][0].set("c","9999"))

    def test_72_original_IFC_native_world_mesh_sha_spoof_refused(self):
        self.reject(lambda r:self.native(r,"WorldGeometry")[0].set(
            "worldMeshSha256","f"*64))

    def test_73_original_IFC_native_world_mesh_bbox_spoof_refused(self):
        self.reject(lambda r:self.native(r,"WorldGeometry")[0].set("maxZ","500"))

    def test_74_original_IFC_native_world_mesh_subtree_deleted_refused(self):
        def poison(r):
            g=self.native(r,"WorldGeometry")[0]
            g.remove(g[0])
        self.reject(poison)

    def test_75_XXE_DTD_rejected_by_independent_oracle(self):
        xml=b'<!DOCTYPE Building [<!ENTITY e SYSTEM "file:///C:/secret">]><Building>&e;</Building>'
        with self.assertRaises(IndependentV044Error):
            validate_original_v044_native_model_read(
                self.sources["geometry_test_14"],xml,task_id="geometry_test_14")

    def test_76_source_input_SHA_poison_refused_by_independent_oracle(self):
        with self.assertRaises(IndependentV044Error):
            validate_original_v044_native_model_read(
                self.sources["geometry_test_14"],
                self.xml["geometry_test_15"],
                task_id="geometry_test_14")

    def test_77_original_native_source_absent_ifc_rejected(self):
        with self.assertRaises(IndependentV044Error):
            validate_original_v044_native_model_read(
                self.dir/"absent.ifc",self.xml["geometry_test_14"],
                task_id="geometry_test_14")

    def test_78_only_four_update_delete_source_input_flags_allowed(self):
        self.assertEqual(set(self.sessions),set(ORIGINAL_PINS))
        self.assertEqual({t["crud"] for t in self.originals.values()
                         if t["test_id"] in self.sessions},{"update","delete"})

    def test_79_all_XML_source_read_only_no_semantic_task_solution_or_evaluator(self):
        self.assertEqual(self.report["real_matched_LLM_XML_vs_Python_trials"],0)
        self.assertEqual(self.report["original_author_evaluator_calls"],0)
        self.assertEqual(self.report["paid_model_calls"],0)
        self.assertEqual(self.report["Docker_executions"],0)
        self.assertEqual(self.report["original_task_solutions_or_native_author_scores_proven"],0)

    def test_80_report_asserts_no_native_edit_permitted_four_new_cases(self):
        self.assertEqual(self.report[
            "new_four_original_previously_unsupported_source_tasks_native_editable"],0)
        self.assertEqual(self.report["new_four_native_IFC_commits"],0)
        self.assertFalse(self.report["full_original45_equal_native_edit_authority_proven"])

    def test_81_new_best_available_45_read_is_experimental_not_default(self):
        self.assertEqual(self.report["previous_v043_source_pinned_research_read_45"],41)
        self.assertEqual(self.report["new_best_available_research_source_read_45"],45)
        self.assertFalse(self.report["new_best_available_research_model_read_IS_default_provider_runner"])
        self.assertTrue(self.report["new_best_available_research_source_read_modes_are_separate_optins"])

    def test_82_explicit_native_authority_is_not_full_model_programmatic_parity(self):
        self.assertFalse(self.report["full_original45_equal_source_information_parity_proven"])
        self.assertFalse(self.report["equal_model_token_budget_or_python_api_ergonomics_proven"])

    def test_83_frozen_audit_report_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            with REPORT.open("xb") as out:out.write(b"NOT_ALLOWED")
        self.assertEqual(file_hash(REPORT),FROZEN_SHA)

    def test_84_full_4_task_original_source_read_audit_byte_exact_replay(self):
        fresh=audit.audit(AUTHOR,DATA)
        raw=(json.dumps(fresh,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf8")
        self.assertEqual(sha256(raw).hexdigest(),FROZEN_SHA)
        self.assertEqual(raw,REPORT.read_bytes())

    def test_85_no_original_question_text_in_frozen_machine_report(self):
        for t in self.originals.values():
            question=t["public_question"]
            if len(question)>60:
                self.assertNotIn(question,REPORT.read_text(encoding="utf8"))
        self.assertFalse(self.report["original_public_sources_or_evaluator_modified"])

    def test_86_original_default_schema_not_extended_by_v044(self):
        base_xsd=(audit.ROOT/"spec"/"toy_markup_v0.xsd").read_text(encoding="utf8")
        self.assertNotIn("NativeStepRecords",base_xsd)
        self.assertNotIn("OriginalNativeIFCSource",base_xsd)
        self.assertTrue(XSD.is_file())
        etree.XMLSchema(etree.parse(str(XSD)))


if __name__=="__main__":
    unittest.main()
