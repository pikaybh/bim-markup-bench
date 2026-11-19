"""v0.14 prospective original IFC4X3 Window-only source-native edit proof.

Actual original geometry_test_18/19 public IFC inputs, immutable original
source SHA, complete declarative Window substate, strict XSD and native
dependencies, positive one/multiple source original Windows, independent
IFC-only structural/mesh oracle, negative XML/ownership/geometry tests.

NO original hidden GT, no API calls or scoring in this module. D0 source
candidate is purely developer-authored, not a real LLM benchmark success.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from hashlib import sha256
import json
import os
import time
import unittest

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.experimental_v13_opaque_source import project_original_native_v13
from src.runtime.experimental_v14_native_window_delete import (
    NS,MAX_DELETED_WINDOWS,NativeWindowV14Error,
    native_full_window_state_v14,compile_native_hosted_windows_v14,
)
from tools.oracle_bibimbap_v14_window_delete import (
    verify_source_native_window_delete,OriginalNativeWindowOracleError,
)
from tools.bibimbap_matched25_tools import file_hash

BASE=Path(os.environ.get("BIBIMBAP_EXPERIMENT_BASE",
                         r"D:\문서\D__1_Projects\202611"))
DATA=BASE/"bibimbap-author-data"/"ifc"
Q="{"+NS+"}"
CASES={
    "geometry_test_18":"01/01/01_01_018.ifc",
    "geometry_test_19":"01/01/01_01_019.ifc",
}


def _remove_from_entire_declarative_state(xml:bytes,guids:tuple[str,...])->bytes:
    root=etree.fromstring(xml)
    windows=root.find(Q+"Windows")
    desired=set(guids)
    removed=set()
    for node in list(windows):
        if node.get("ifcGuid") in desired:
            removed.add(node.get("ifcGuid"))
            windows.remove(node)
    if removed!=desired:
        raise ValueError("Only original hosted IFC Window GUIDs may be removed from developer XML")
    return etree.tostring(root,encoding="utf8")


class V14RealOriginalCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if any(not (DATA/case).is_file() for case in CASES.values()):
            raise unittest.SkipTest("Pinned original public native IFC dataset not mounted")
        cls._td=tempfile.TemporaryDirectory(prefix="bibimbap-142-v14-native-")
        cls.root=Path(cls._td.name)
        cls.experiments={}
        for task,src_rel in CASES.items():
            folder=cls.root/task
            folder.mkdir()
            source=folder/"original_source_normalized_m.ifc"
            raw=DATA/src_rel
            cls.experiments[task]={
                "original_source_path":raw,
                "original_public_source_sha256":file_hash(raw),
                "source":source,
            }
            ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(raw)),"METER"
            ).write(str(source))
            stored=cls.experiments[task]
            stored["source_hash"]=file_hash(source)
            state=native_full_window_state_v14(source)
            stored["state"]=state
            original=project_original_native_v13(source)
            stored["v13"]=original
            allguids=[x.get("ifcGuid") for x in
                      etree.fromstring(state.xml).find(Q+"Windows")]
            original_demoted=list(original.demoted_fill_guids)
            allguids_to_fill=original_demoted+[
                x for x in allguids if x not in original_demoted
            ]
            stored["selected_one"]=tuple(original_demoted[:1])
            stored["selected_six"]=tuple(sorted(allguids_to_fill[:6]))
            if len(stored["selected_six"])!=6:
                raise RuntimeError("Only original full window inventory source changes are permitted")
            for name,guids in (
                ("single",stored["selected_one"]),
                ("six",stored["selected_six"]),
            ):
                xml=_remove_from_entire_declarative_state(state.xml,guids)
                output=folder/("candidate_"+name+".ifc")
                report=compile_native_hosted_windows_v14(source,xml,output)
                proof=verify_source_native_window_delete(
                    source,output,guids,
                    expected_original_source_sha256=report.source_sha256,
                    expected_output_sha256=report.output_sha256,
                )
                stored[name]={
                    "xml":xml,"output":output,"report":report,"oracle":proof,
                }

    @classmethod
    def tearDownClass(cls):
        try:
            for row in cls.experiments.values():
                assert file_hash(row["original_source_path"])==row["original_public_source_sha256"]
                assert file_hash(row["source"])==row["source_hash"]
        finally:
            cls._td.cleanup()

    def _source(self,key):
        return self.experiments[key]


class TestV14NativeWindowsPositive(V14RealOriginalCases):
    def test_real_original_source18_readonly_window_now_natively_deleted_once(self):
        row=self._source("geometry_test_18")
        case=row["single"]
        self.assertEqual(len(row["selected_one"]),1)
        self.assertEqual(case["report"].target_original_window_guids,
                         tuple(sorted(row["selected_one"])))
        self.assertTrue(set(row["selected_one"])<=set(row["v13"].demoted_fill_guids))
        self.assertTrue(case["report"].output_path.is_file())
        self.assertEqual(case["oracle"]["status"],
            "INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014")
        self.assertEqual(case["report"].independent_native_geometries_preserved,54)

    def test_real_original_source19_readonly_window_now_natively_deleted_once(self):
        row=self._source("geometry_test_19")
        case=row["single"]
        self.assertEqual(len(row["selected_one"]),1)
        self.assertTrue(set(row["selected_one"])<=set(row["v13"].demoted_fill_guids))
        self.assertEqual(case["report"].independent_native_geometries_preserved,21)
        self.assertEqual(case["oracle"]["status"],
            "INDEPENDENT_ORIGINAL_NATIVE_IFC4X3_WINDOW_ONLY_DELETE_ORACLE_PASS_V014")

    def test_real_original_geometry18_six_source_window_batch_delete_and_oracle(self):
        row=self._source("geometry_test_18")
        case=row["six"]
        self.assertEqual(len(row["selected_six"]),6)
        self.assertEqual(case["report"].target_original_window_guids,
                         row["selected_six"])
        self.assertEqual(len(case["report"].removed_original_native_root_guids),42)
        self.assertEqual(case["oracle"]["non_target_original_root_count_preserved"],315)
        self.assertEqual(case["oracle"]["actual_world_native_product_meshes_preserved"],49)

    def test_real_original_geometry19_six_window_batch_delete_and_oracle(self):
        row=self._source("geometry_test_19")
        case=row["six"]
        self.assertEqual(len(row["selected_six"]),6)
        self.assertEqual(len(case["report"].removed_original_native_root_guids),42)
        self.assertEqual(case["oracle"]["non_target_original_root_count_preserved"],129)
        self.assertEqual(case["oracle"]["actual_world_native_product_meshes_preserved"],16)

    def test_original_ifc4x3_host_wall_void_opening_is_never_deleted_or_closed(self):
        for key in CASES:
            with self.subTest(task=key):
                row=self._source(key)
                for name in ("single","six"):
                    case=row[name]
                    self.assertEqual(set(
                        case["report"].retained_original_opening_guids
                    ),set(case["oracle"][
                        "independently_original_source_openings_retained"]))
                    self.assertTrue(case["oracle"]["original_host_wall_opening_unchanged"])
                    self.assertTrue(case["oracle"][
                        "original_IfcRelVoids_and_Window_fill_semantics_preserved"])
                    self.assertFalse(case["oracle"][
                        "full_original45_semantic_edit_equivalence_proven"])

    def test_entire_original_window_inventory_explicitly_source_pinned(self):
        for key,expected in (("geometry_test_18",19),("geometry_test_19",7)):
            with self.subTest(task=key):
                row=self._source(key)
                v=row["state"]
                self.assertEqual(v.original_full_window_count,expected)
                root=etree.fromstring(v.xml)
                self.assertEqual(root.get("sourceModelSha256"),row["source_hash"])
                self.assertEqual(root.get("sourceCatalogSha256"),
                         sha256(row["v13"].source_catalog_xml).hexdigest())
                self.assertEqual(root.get("sourceIfcSchema"),"IFC4X3")
                self.assertEqual(root.get("editScope"),
                                 "FULL_ORIGINAL_WINDOW_INVENTORY_DELETE_ONLY")
                self.assertEqual(len(root.find(Q+"Windows")),expected)

    def test_delete_is_a_declarative_absence_not_an_imperative_tool_wrapper(self):
        row=self._source("geometry_test_19")
        old=etree.fromstring(row["state"].xml)
        after=etree.fromstring(row["single"]["xml"])
        self.assertEqual(len(old.find(Q+"Windows"))-len(after.find(Q+"Windows")),1)
        self.assertEqual(after.tag,Q+"NativeWindowState")
        self.assertTrue(all(x.tag==Q+"Window" for x in after.find(Q+"Windows")))
        self.assertEqual(after.find(".//"+Q+"Delete"),None)
        self.assertEqual(after.find(".//"+Q+"ToolCall"),None)
        self.assertTrue(row["single"]["report"].as_dict()[
            "source_original_ifc_unmodified"])

    def test_original_source_window_only_delete_restores_shared_type_metadata(self):
        for row in self.experiments.values():
            with self.subTest(task=row["source"].name):
                case=row["six"]
                proof=case["oracle"]
                self.assertEqual(
                    set(proof["independently_source_shared_membership_relation_guids"]),
                    set(case["report"].modified_original_shared_membership_relations))
                self.assertEqual(
                    proof["non_target_original_root_count_preserved"],
                    case["report"].independent_unrelated_roots_preserved)
                self.assertTrue(proof["source_original_ifc_schema_and_units_retained"])

    def test_source_and_original_author_data_are_immutable(self):
        for row in self.experiments.values():
            self.assertEqual(file_hash(row["original_source_path"]),
                             row["original_public_source_sha256"])
            self.assertEqual(file_hash(row["source"]),row["source_hash"])
            self.assertNotEqual(row["six"]["report"].output_sha256,
                                row["source_hash"])
            self.assertEqual(file_hash(row["six"]["output"]),
                             row["six"]["report"].output_sha256)

    def test_one_real_source_candidate_byte_determinism_after_clock_second(self):
        row=self._source("geometry_test_18")
        xml=row["single"]["xml"]
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"later_native.ifc"
            time.sleep(1.05)
            result=compile_native_hosted_windows_v14(row["source"],xml,output)
            self.assertEqual(result.output_sha256,
                             row["single"]["report"].output_sha256)
            self.assertEqual(file_hash(output),file_hash(row["single"]["output"]))
            oracle=verify_source_native_window_delete(
                row["source"],output,row["selected_one"])
            self.assertTrue(oracle["candidate_independent_native_scene_proof_not_original_author_grade"])

    def test_not_general_ifc_edit_support_or_real_model_benchmark(self):
        for row in self.experiments.values():
            for name in ("single","six"):
                record=row[name]["report"].as_dict()
                self.assertFalse(record["full_original45_semantic_write_parity"])
                self.assertFalse(record["editor_can_edit_original_IfcSpace_or_IfcBeam"])
                self.assertFalse(record["source_native_host_wall_and_opening_geometry_rebuilt"])
                self.assertEqual(record["LLM_or_paid_API_calls"],0)


class TestV14NativeWindowsNegative(V14RealOriginalCases):
    def _attempt(self,sourcekey,xml:bytes):
        row=self._source(sourcekey)
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"candidate.ifc"
            with self.assertRaises(NativeWindowV14Error):
                compile_native_hosted_windows_v14(row["source"],xml,output)
            self.assertFalse(output.exists())
            self.assertEqual(file_hash(row["source"]),row["source_hash"])

    def test_reject_declared_no_op_and_not_mutate_source(self):
        self._attempt("geometry_test_18",
                      self._source("geometry_test_18")["state"].xml)

    def test_reject_new_fabricated_IFC_globalid(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["state"].xml)
        node=root.find(Q+"Windows")[0]
        node.set("ifcGuid","0"*22)
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_renamed_original_host_wall_globalid(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["state"].xml)
        root.find(Q+"Windows")[0].set("originalHostWallGuid","1"*22)
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_renamed_original_opening_globalid(self):
        row=self._source("geometry_test_19")
        root=etree.fromstring(row["state"].xml)
        root.find(Q+"Windows")[0].set("originalOpeningGuid","1"*22)
        self._attempt("geometry_test_19",etree.tostring(root))

    def test_reject_duplicate_existing_Window_node(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["state"].xml)
        ws=root.find(Q+"Windows")
        ws.append(etree.fromstring(etree.tostring(ws[0])))
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_source_model_hash_tampering(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["single"]["xml"])
        root.set("sourceModelSha256","0"*64)
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_native_readonly_source_catalog_hash_tampering(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["single"]["xml"])
        root.set("sourceCatalogSha256","0"*64)
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_native_source_IFC_schema_alias(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["single"]["xml"])
        root.set("sourceIfcSchema","IFC4")
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_unrecognized_write_command_tag(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["single"]["xml"])
        etree.SubElement(root,Q+"Delete",attrib={"ifcGuid":row["selected_one"][0]})
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_arbitrary_window_modify_attribute(self):
        row=self._source("geometry_test_19")
        root=etree.fromstring(row["single"]["xml"])
        node=root.find(Q+"Windows")[0]
        node.set("x","1234")
        self._attempt("geometry_test_19",etree.tostring(root))

    def test_reject_doctype_and_external_entity(self):
        row=self._source("geometry_test_18")
        xml=row["single"]["xml"]
        malicious=(
            b'<!DOCTYPE NativeWindowState [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            +xml
        )
        self._attempt("geometry_test_18",malicious)

    def test_reject_more_than_eight_native_source_Window_deletions(self):
        row=self._source("geometry_test_18")
        root=etree.fromstring(row["state"].xml)
        ws=root.find(Q+"Windows")
        for node in list(ws)[:MAX_DELETED_WINDOWS+1]:
            ws.remove(node)
        self._attempt("geometry_test_18",etree.tostring(root))

    def test_reject_removal_of_all_7_windows_which_destroys_shared_relation(self):
        row=self._source("geometry_test_19")
        root=etree.fromstring(row["state"].xml)
        ws=root.find(Q+"Windows")
        for node in list(ws):
            ws.remove(node)
        self._attempt("geometry_test_19",etree.tostring(root))

    def test_reject_edit_of_original_opaque_catalog_instead_of_v14_state(self):
        row=self._source("geometry_test_18")
        self._attempt("geometry_test_18",row["v13"].source_catalog_xml)

    def test_reject_in_place_source_write_and_preexisting_output(self):
        row=self._source("geometry_test_18")
        with self.assertRaises(NativeWindowV14Error):
            compile_native_hosted_windows_v14(
                row["source"],row["single"]["xml"],row["source"])
        with tempfile.TemporaryDirectory() as td:
            existing=Path(td)/"existing.ifc"
            existing.write_text("do-not-overwrite")
            with self.assertRaises(NativeWindowV14Error):
                compile_native_hosted_windows_v14(
                    row["source"],row["single"]["xml"],existing)
            self.assertEqual(existing.read_text(),"do-not-overwrite")

    def test_independent_ifc_oracle_rejects_missing_original_void_wall(self):
        row=self._source("geometry_test_18")
        deleted=row["selected_one"]
        with tempfile.TemporaryDirectory() as td:
            candidate=Path(td)/"tampered.ifc"
            f=ifcopenshell.open(str(row["single"]["output"]))
            opguid=row["single"]["report"].retained_original_opening_guids[0]
            op=f.by_guid(opguid)
            # Tamper a retained native Window source hole explicitly:
            # fail independently before it could be mistaken for valid edit.
            f.remove(op.VoidsElements[0])
            f.write(str(candidate))
            with self.assertRaises(OriginalNativeWindowOracleError):
                verify_source_native_window_delete(
                    row["source"],candidate,deleted)

    def test_independent_ifc_oracle_rejects_modified_unrelated_host_wall_placement(self):
        row=self._source("geometry_test_19")
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/"moved_wall.ifc"
            f=ifcopenshell.open(str(row["single"]["output"]))
            host_guid=row["single"]["oracle"][
                "independently_original_host_wall_guids_preserved"][0]
            host=f.by_guid(host_guid)
            xyz=host.ObjectPlacement.RelativePlacement.Location
            xyz.Coordinates=tuple(
                float(n)+(0.6 if i==0 else 0.) for i,n in enumerate(xyz.Coordinates)
            )
            f.write(str(bad))
            with self.assertRaises(OriginalNativeWindowOracleError):
                verify_source_native_window_delete(
                    row["source"],bad,row["selected_one"])

    def test_independent_ifc_oracle_rejects_claimed_extra_window_target(self):
        row=self._source("geometry_test_18")
        bogus=(row["selected_one"][0],"0"*22)
        with self.assertRaises(OriginalNativeWindowOracleError):
            verify_source_native_window_delete(
                row["source"],row["single"]["output"],bogus)


if __name__=="__main__":
    unittest.main()
