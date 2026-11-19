"""Zenodo/GNI official metadata and confidential source-steward handoff.

Syntactic positive tests never certify licenses, legal persons, GT, fresh
samples, reviewer signatures or provider-data export.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools import bibimbap_v066_zenodo_source_handoff as z
from tools import audit_bibimbap_v066_zenodo_handoff as audit
from tools.bibimbap_matched25_tools import file_hash

REPORT_SHA="f089801dd7131338bc3b45821d319424cbd6ba4dc28287f07346aaf5cd9ed631"


class FrozenZenodoRights066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(audit.REPORT.read_text("utf8"))

    def test_01_canonical_SHA(self):
        self.assertEqual(file_hash(audit.REPORT),REPORT_SHA)

    def test_02_byte_identical_canonical_report(self):
        self.assertEqual(audit.REPORT.read_bytes(),z.canonical(self.report))

    def test_03_prior_public_paper_report_unmodified(self):
        self.assertEqual(file_hash(audit.p.REPORT),audit.PUBLIC_SHA)

    def test_04_prior_31_source_rights_report_unmodified(self):
        self.assertEqual(file_hash(audit.prior.REPORT),audit.RIGHTS_SHA)

    def test_05_correct_official_record_DOI(self):
        self.assertEqual(z.VERSION_DOI,"10.5281/zenodo.19722012")
        self.assertEqual(self.report["doi_role_correction"][
            "correct_record_version_DOI"],z.VERSION_DOI)

    def test_06_correct_official_concept_DOI(self):
        self.assertEqual(z.CONCEPT_DOI,"10.5281/zenodo.19722011")
        self.assertEqual(self.report["doi_role_correction"][
            "correct_record_concept_DOI"],z.CONCEPT_DOI)

    def test_07_previous_inverted_labels_frozen_not_modified(self):
        self.assertTrue(self.report["doi_role_correction"][
            "old_document_inverted_roles"])
        self.assertTrue(self.report["doi_role_correction"][
            "old_document_unchanged_under_prior_frozen_SHA"])

    def test_08_version_date_licence_pinned(self):
        data=self.report["official_zenodo_record_metadata_only"]
        self.assertEqual(data["record_version"],"1.0.0")
        self.assertEqual(data["publication_date"],"2026-04-24")
        self.assertEqual(data["license_identifier"],"cc-by-4.0")

    def test_09_official_zenodo_endpoint(self):
        self.assertEqual(self.report["official_zenodo_record_metadata_only"][
            "official_zenodo_metadata_URL"],
            "https://zenodo.org/api/records/19722012")

    def test_10_all_exact_seven_files(self):
        data=self.report["official_zenodo_record_metadata_only"]
        self.assertEqual(data["public_total_files"],7)
        self.assertEqual(len(data["public_file_manifest"]),7)

    def test_11_archives_exact_two(self):
        self.assertEqual(self.report["official_zenodo_record_metadata_only"][
            "original_zip_archive_count"],2)

    def test_12_archive_sizes_exact(self):
        data=self.report["official_zenodo_record_metadata_only"]
        self.assertEqual(data["original_zip_archive_total_bytes"],724338765)

    def test_13_all_files_total_size_exact(self):
        self.assertEqual(self.report["official_zenodo_record_metadata_only"][
            "all_public_record_files_bytes"],726248247)

    def test_14_zip_2025_exact_MD5(self):
        data=self.report["official_zenodo_record_metadata_only"]
        file=next(x for x in data["public_file_manifest"]
                  if x["name"]=="2025_BIMfundamentals.zip")
        self.assertEqual(file["bytes"],503285210)
        self.assertEqual(file["md5"],"md5:bab737c3cfb3ff0443f1cc43355b589c")

    def test_15_zip_2026_exact_MD5(self):
        data=self.report["official_zenodo_record_metadata_only"]
        file=next(x for x in data["public_file_manifest"]
                  if x["name"]=="2026_BIMprojects.zip")
        self.assertEqual(file["bytes"],221053555)
        self.assertEqual(file["md5"],"md5:bc4bfb90313162c68a3ec4e24a0d33cf")

    def test_16_zip_MD5_not_individual_IFC_SHA(self):
        data=self.report["official_zenodo_record_metadata_only"]
        self.assertTrue(data["archive_MD5_is_NOT_individual_IFC_SHA256"])
        self.assertFalse(data["individual_IFC_SHA256_computed"])

    def test_17_no_archive_or_ifc_download(self):
        self.assertEqual(self.report["official_zenodo_record_metadata_only"][
            "original_archive_or_individual_IFC_downloads"],0)
        self.assertEqual(self.report["IFC_zip_archive_files_downloaded"],0)
        self.assertEqual(self.report["individual_IFC_files_opened"],0)

    def test_18_zero_blind_sources(self):
        self.assertEqual(self.report[
            "source_file_legal_and_safety_limits"]["new_independently_blind_source_count"],0)

    def test_19_zero_real_external_signatures(self):
        self.assertEqual(self.report["real_external_signatures_received"],0)
        self.assertFalse(self.report["trust_anchor_registry_for_external_signatures_configured"])

    def test_20_model_training_nonexposure_not_proven(self):
        self.assertFalse(self.report["source_file_legal_and_safety_limits"][
            "LLM_training_nonexposure_proven"])

    def test_21_external_provider_rights_not_proven(self):
        self.assertFalse(self.report["source_file_legal_and_safety_limits"][
            "external_provider_specific_transfer_retention_authorization"])

    def test_22_original_scorer_remains_unproven(self):
        self.assertFalse(self.report["paper_scorer_git_release_crosswalk_completed"])

    def test_23_no_author_gt_private_file_reads(self):
        self.assertEqual(self.report["original_author_grader_or_GT_files_opened"],0)
        self.assertEqual(self.report["private_task_or_reference_evaluator_files_opened"],0)

    def test_24_no_external_model_calls_and_uploads(self):
        self.assertEqual(self.report["provider_or_model_calls"],0)
        self.assertEqual(self.report["paid_trials_or_external_IFC_uploads"],0)

    def test_25_external_steward_roles_exactly_five(self):
        self.assertEqual(len(self.report["external_steward_required_roles"]),5)
        self.assertEqual(self.report["external_steward_required_roles"],list(z.STEWARDS))


class MetadataMutation066(unittest.TestCase):
    def setUp(self):
        self.raw=z.frozen_reduced_metadata()

    def verify(self,raw=None):
        return z.metadata_snapshot(self.raw if raw is None else raw)

    def test_26_pinned_metadata_succeeds_without_external_network(self):
        r=self.verify()
        self.assertEqual(r["public_total_files"],7)

    def test_27_swapped_concept_and_version_doi_denied(self):
        self.raw["doi"],self.raw["conceptdoi"]=(
            self.raw["conceptdoi"],self.raw["doi"])
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_28_wrong_record_id_denied(self):
        self.raw["id"]=19722011
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_29_wrong_license_denied(self):
        self.raw["license"]="CC0-1.0"
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_30_wrong_publication_version_denied(self):
        self.raw["version"]="2.0.0"
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_31_archive_sha256_misrepresented_as_md5_denied(self):
        self.raw["files"][0]["checksum"]="sha256:"+"f"*64
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_32_archive_size_off_by_one_denied(self):
        self.raw["files"][0]["size"]+=1
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_33_extra_file_denied(self):
        self.raw["files"].append({"name":"unexpected.ifc",
                                  "size":10,"checksum":"md5:"+"f"*32})
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_34_one_file_missing_denied(self):
        self.raw["files"].pop()
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_35_duplicate_file_denied(self):
        self.raw["files"][-1]=self.raw["files"][0].copy()
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_36_file_order_irrelevant(self):
        self.raw["files"].reverse()
        self.assertEqual(self.verify()["public_total_files"],7)

    def test_37_download_URL_injection_denied(self):
        self.raw["files"][0]["download_url"]="https://untrusted.example/download"
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_38_unknown_external_key_denied(self):
        self.raw["access_token"]="SECRET"
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_39_metadata_null_invalid(self):
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            self.verify(None if False else [])
    def test_40_boolean_replacing_integer_denied(self):
        self.raw["id"]=True
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()

    def test_41_noninteger_file_size_denied(self):
        self.raw["files"][0]["size"]="503285210"
        with self.assertRaises(z.ZenodoHandoffBlocked066):self.verify()


class HandoffRoleSeparation066(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=audit.historical_31()
        cls.source="f"*64
        assert cls.source not in cls.old

    def make_claim(self,role,index=0):
        return {
            "role":role,
            "steward_pseudonym":"steward-"+role.replace("_","-"),
            "source_ifc_sha256":self.source,
            "evidence_document_sha256":
                hashlib.sha256((role+"|FAKE_NOT_SIGNED").encode()).hexdigest(),
            "scope_revision":z.SCOPES[role],
        }

    def test_42_empty_claims_incomplete(self):
        r=z.public_receipt([],self.old)
        self.assertEqual(r["status"],z.STATUS_INCOMPLETE)
        self.assertEqual(len(r["missing_roles"]),5)

    def test_43_single_claim_incomplete(self):
        r=z.public_receipt([self.make_claim(z.STEWARDS[0])],self.old)
        self.assertEqual(len(r["missing_roles"]),4)

    def test_44_fake_all_five_still_no_admission(self):
        r=z.public_receipt([self.make_claim(x) for x in z.STEWARDS],self.old)
        self.assertEqual(r["status"],z.STATUS_UNVERIFIED)
        self.assertFalse(r["independent_blind_sample_admitted"])
        self.assertFalse(r["model_or_provider_run_permitted"])
        self.assertFalse(r["trusted_reviewer_signatures_verified"])

    def test_45_same_actor_two_roles_denied(self):
        roles=[self.make_claim(x) for x in z.STEWARDS]
        roles[1]["steward_pseudonym"]=roles[0]["steward_pseudonym"]
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt(roles,self.old)

    def test_46_duplicate_role_denied(self):
        roles=[self.make_claim(x) for x in z.STEWARDS]
        roles[1]["role"]=roles[0]["role"]
        roles[1]["scope_revision"]=roles[0]["scope_revision"]
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt(roles,self.old)

    def test_47_historical_IFC_reuse_all_31_denied(self):
        for sha in self.old:
            doc=self.make_claim(z.STEWARDS[0])
            doc["source_ifc_sha256"]=sha
            with self.assertRaises(z.ZenodoHandoffBlocked066):
                z.public_receipt([doc],self.old)

    def test_48_different_new_source_sha_between_roles_denied(self):
        roles=[self.make_claim(x) for x in z.STEWARDS]
        roles[1]["source_ifc_sha256"]="e"*64
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt(roles,self.old)

    def test_49_private_GT_field_must_fail_closed(self):
        doc=self.make_claim(z.STEWARDS[0])
        for illegal in ("private_answer","target_guid","ifc_file_bytes",
                        "source_filepath","scorer_code","api_key"):
            altered=dict(doc,**{illegal:"LEAK"})
            with self.assertRaises(z.ZenodoHandoffBlocked066):
                z.public_receipt([altered],self.old)

    def test_50_invalid_evidence_hash_denied(self):
        doc=self.make_claim(z.STEWARDS[0])
        doc["evidence_document_sha256"]="not-a-sha"
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt([doc],self.old)

    def test_51_wrong_steward_scope_denied(self):
        doc=self.make_claim(z.STEWARDS[0])
        doc["scope_revision"]=z.SCOPES[z.STEWARDS[1]]
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt([doc],self.old)

    def test_52_untrusted_real_identity_or_full_name_denied(self):
        doc=self.make_claim(z.STEWARDS[0])
        doc["steward_pseudonym"]="Jane Doe <private@example.com>"
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt([doc],self.old)

    def test_53_bad_historical_sha_registry_denied(self):
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt([],{"invalid"})

    def test_54_excessive_6_or_more_claims_denied(self):
        docs=[self.make_claim(x) for x in z.STEWARDS]
        docs.append(dict(docs[0]))
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt(docs,self.old)

    def test_55_false_any_approval_not_accepted(self):
        doc=self.make_claim(z.STEWARDS[0])
        doc["rights_verified"]=True
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.public_receipt([doc],self.old)

    def test_56_no_model_launch_even_forged_true(self):
        with self.assertRaises(z.ZenodoHandoffBlocked066):
            z.refuse_trial(source=self.source,authenticated_signatures=True,
                           owner_approval=True,provider_budget_USD=9999)

    def test_57_all_FIVE_responds_only_public_hashes(self):
        docs=[self.make_claim(x) for x in z.STEWARDS]
        raw=z.canonical(z.public_receipt(docs,self.old))
        self.assertNotIn(b"private_answer",raw)
        self.assertNotIn(b"source_filepath",raw)
        self.assertNotIn(b"GT IFC",raw)
        self.assertNotIn(b"model_api_key",raw)
        self.assertFalse(json.loads(raw)["LLM_training_nonexposure_verified"])

    def test_58_metadata_receipt_does_not_prove_real_rights(self):
        x=json.loads(audit.REPORT.read_text("utf8"))
        self.assertFalse(x["source_file_legal_and_safety_limits"][
            "third_party_embedded_family_rights_and_attribution_verified"])
        self.assertFalse(x["new_owner_approval_to_launch"])

    def test_59_deterministic_archive_filename_member_count_separation(self):
        x=z.metadata_snapshot(z.frozen_reduced_metadata())
        self.assertEqual(x["published_original_IFC_count_claim"],224)
        self.assertFalse(x["individual_IFC_names_inspected"])

    def test_60_contract_has_no_network_or_ifc_import(self):
        source=Path(z.__file__).read_text(encoding="utf8")
        self.assertNotIn("import ifcopenshell",source)
        self.assertNotIn("from openai import",source)
        self.assertNotIn("requests.get(",source)
        self.assertNotIn("urllib.request.urlopen(",source)
        self.assertNotIn("zipfile.ZipFile(",source)


if __name__=="__main__":
    unittest.main()
