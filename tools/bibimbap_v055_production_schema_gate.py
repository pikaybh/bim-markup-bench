"""v0.55 production-only independent IFC4X3 source-error-delta admission.

This intentionally does not import evaluator/source author tests, developer
fixtures, original GT, prospective study or v0.54 audit scripts. Fail-closed
model-facing host gate applied *before* native IFC candidate promotion.

IfcOpenShell validate(express_rules=False) covers attributes/type/inverse
cardinality, NOT all EXPRESS WHERE or geometric constraints. It is an
additional source-delta gate, never an official author benchmark scorer.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import ifcopenshell
import ifcopenshell.validate

from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v051_independent_native_python_oracle import (
    verify_independent_native_python_v051,
)


class NativeSourceSchema055Error(ValueError):
    """Non-revealing failure for model-facing transaction host."""


def _require_regular(path:Path)->None:
    if (not path.is_file() or path.is_symlink()
            or not path.resolve(strict=True).is_file()):
        raise NativeSourceSchema055Error("Native IFC source/candidate is not a regular file")


def _schema_error_counter(path:Path)->Counter:
    """Hash validator findings; avoid exposing IFC IDs, scorer hints or GT."""
    _require_regular(path)
    logger=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(path),logger,express_rules=False)
    count=Counter()
    for item in logger.statements:
        if item.get("level")!="error":
            raise NativeSourceSchema055Error("Unexpected original IFC schema validator status")
        kind=str(item.get("type") or "")
        attr=str(item.get("attribute") or "")
        text=str(item.get("message") or "")
        count[(kind,attr,sha256(text.encode("utf8")).hexdigest())]+=1
    return count


def production_native_schema_delta_v055(
    source_ifc:Path,candidate_ifc:Path,*,source_sha:str,
)->dict:
    """Non-mutating, genuine source-native schema error delta.

    The original original-public IFC has an inherited issue. A zero-total-
    errors requirement is not usable; compare multiset source/candidate.
    """
    source_ifc=Path(source_ifc)
    candidate_ifc=Path(candidate_ifc)
    _require_regular(source_ifc)
    _require_regular(candidate_ifc)
    if (len(source_sha)!=64 or file_hash(source_ifc)!=source_sha
            or source_ifc.resolve()==candidate_ifc.resolve()):
        raise NativeSourceSchema055Error("Unverified source SHA or candidate alias")
    candidate_sha=file_hash(candidate_ifc)
    initial=_schema_error_counter(source_ifc)
    final=_schema_error_counter(candidate_ifc)
    introduced=final-initial
    source_is_ifc4x3=ifcopenshell.open(str(source_ifc)).schema=="IFC4X3"
    candidate_is_ifc4x3=ifcopenshell.open(str(candidate_ifc)).schema=="IFC4X3"
    if (not source_is_ifc4x3 or not candidate_is_ifc4x3
            or file_hash(source_ifc)!=source_sha
            or file_hash(candidate_ifc)!=candidate_sha):
        raise NativeSourceSchema055Error("Source/candidate schema or native hashes invalid")
    return {
        "status":("PASS_NO_NEW_SCHEMA_FINDINGS" if not introduced else
                  "REJECT_NEW_SCHEMA_FINDINGS"),
        "source_schema_error_count":sum(initial.values()),
        "candidate_schema_error_count":sum(final.values()),
        "introduced_schema_error_count":sum(introduced.values()),
        "ifc4x3_source_and_candidate":True,
        "source_sha256_preserved":True,
        "candidate_sha256":candidate_sha,
    }


def validate_production_native_commit_v055(
    source_ifc:Path,candidate_ifc:Path,*,source_sha:str,task_id:str,
)->dict:
    """Raise on newly introduced schema errors or independent source scope violations.

    Does not inspect private author grader, model output or trial verdict.
    Candidate is never promoted by this function; the calling transaction
    must assign last-valid output ONLY after this function returns.
    """
    delta=production_native_schema_delta_v055(
        source_ifc,candidate_ifc,source_sha=source_sha)
    if delta["status"]!="PASS_NO_NEW_SCHEMA_FINDINGS":
        raise NativeSourceSchema055Error("NativeSchemaDeltaRejected")
    physical=verify_independent_native_python_v051(
        source_ifc,candidate_ifc,source_sha=source_sha,task_id=task_id)
    if physical["status"]!="V051_INDEPENDENT_SOURCE_NATIVE_IFC_SCOPE_ORACLE_PASS":
        raise NativeSourceSchema055Error("NativeSourceScopeRejected")
    if (file_hash(source_ifc)!=source_sha
            or file_hash(candidate_ifc)!=delta["candidate_sha256"]):
        raise NativeSourceSchema055Error("NativeCandidateChangedDuringReview")
    return {
        "status":"V055_SOURCE_SCHEMA_AND_NATIVE_SCOPE_ADMITTED",
        "source_schema_error_count":delta["source_schema_error_count"],
        "candidate_schema_error_count":delta["candidate_schema_error_count"],
        "introduced_schema_error_count":0,
        "candidate_sha256":delta["candidate_sha256"],
        "original_author_score":None,
        "published_paper_score":None,
    }
