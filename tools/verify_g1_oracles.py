#!/usr/bin/env python3
"""Re-run the frozen local D0-vs-I0 non-LLM parity suite and write evidence.

This tests only own tiny IFC fixtures, has no network, no key, no model calls,
and intentionally CANNOT unblock official 324-task/paid-model evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

import ifcopenshell

from src.runtime.compiler import compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report

FROZEN_SCENARIOS=(
    "IfcWall.create_with_native_storey",
    "IfcWall.update_height",
    "IfcWall.delete_standalone",
    "IfcOpeningElement.move_with_window",
    "IfcWindow.delete_fill_preserve_void",
    "IfcRelConnectsElements.create",
)


def _static_case_checksums(source:Path)->dict:
    """Actual D0/I0 written IFC bytes and native semantic comparisons."""
    suites={}
    original=parse_xml(project_ifc(source).xml)
    for case in ("update_wall_height","move_hosted_opening",
                 "delete_hosted_window","create_standalone_wall"):
        changed=Path("tests/oracles/xml")/(case+".xml")
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            direct=temp/"D0_result.ifc"
            python=temp/"I0_result.ifc"
            report=compile_declarative_xml(source,changed.read_bytes(),direct)
            if case=="update_wall_height":
                guid=next(n.ifc_guid for n in original.elements if n.kind=="Wall")
                manual_ifc_reference(source,python,"UPDATE_WALL_HEIGHT",
                                     target_guid=guid,height=3.3)
            elif case=="move_hosted_opening":
                guid=next(n.ifc_guid for n in original.elements
                          if n.kind=="Opening" and str(n.attrs().get("offset"))=="1.6")
                manual_ifc_reference(source,python,"MOVE_OPENING",
                                     target_guid=guid,delta_x=0.5)
            elif case=="delete_hosted_window":
                guid=next(n.ifc_guid for n in original.elements if n.kind=="Window")
                manual_ifc_reference(source,python,"DELETE_WINDOW",target_guid=guid)
            elif case=="create_standalone_wall":
                local_id="oracle_wall"
                sha=hashlib.sha256(source.read_bytes()).hexdigest()
                guid=ifcopenshell.guid.compress(uuid.uuid5(
                    uuid.UUID("9218e3de-9b55-4960-b9b0-e4dddf796ebd"),
                    f"bim-markup-v0.1:{sha}:IfcWall:{local_id}").hex)
                storey=ifcopenshell.open(str(source)).by_type("IfcBuildingStorey")[0].GlobalId
                manual_ifc_reference(source,python,"CREATE_WALL",
                                     new_guid=guid,storey_guid=storey)
            parity=parity_report(direct,python)
            if not parity["parity"]:
                raise ValueError("Native source/imperative oracle outputs differ")
            suites[case]={
                "input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                "D0_output_sha256":hashlib.sha256(direct.read_bytes()).hexdigest(),
                "I0_output_sha256":hashlib.sha256(python.read_bytes()).hexdigest(),
                "native_ifc_parity":True,
                "native_relation_count":parity["native_relation_count_left"],
                "untouched_root_objects_verified":report.untouched_root_objects_verified,
                "intended_operations":[op.operation for op in report.operations],
                "unintended_root_changes":list(report.unexpected_root_changes),
            }
    return suites


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,
                   default=Path("reports/deterministic_ceiling.json"))
    a=p.parse_args()
    source=Path("tests/fixtures/synthetic/input.ifc")
    if not source.exists():
        print(json.dumps({"status":"BLOCKED_MISSING_SYNTHETIC_IFC"}))
        return 2
    run=subprocess.run([sys.executable,"-m","unittest","tests.test_oracle_parity","-q"],
                       capture_output=True,text=True,timeout=45)
    observed=run.stdout+run.stderr
    count=re.search(r"Ran (\d+) tests?",observed)
    actual_count=int(count.group(1)) if count else 0
    success=run.returncode==0 and actual_count==6 and "FAILED" not in observed and "skipped=" not in observed
    source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    report={
        "schema_version":"g1-08-independent-synthetic-oracle-v0.1",
        "status":"PASS_SYNTHETIC_ONLY" if success else "FAILED_SYNTHETIC_ORACLE",
        "own_fixture":"tests/fixtures/synthetic/input.ifc",
        "own_fixture_sha256":source_sha,
        "D0":"Trusted compiler from declarative XML-only edits",
        "I0":"Separate manually authored IfcOpenShell reference; no compiler helper imports",
        "scenarios":list(FROZEN_SCENARIOS),
        "scenarios_verified":len(FROZEN_SCENARIOS) if success else 0,
        "unit_tests_executed":actual_count,
        "all_scenarios_native_ifc_semantic_parity":bool(success),
        "independent_checker":"tests/oracles/python/independent_ifc_checker.py",
        "checks":[
            "IFC schema and IfcRoot GlobalId/class inventories",
            "Native storey/void/fill/space/connect IFC relationships",
            "IFC world placements and B-rep-derived triangulated bounding boxes/volumes",
            "Psets and source material records",
            "Byte-identical IFC no-op and unchanged source",
        ],
        "world_geometry_tolerance_m":1e-6,
        "official_bim_edit_tasks_tested":0,
        "official_full_324_engine_ceiling":None,
        "paid_model_pilot_ready":False,
        "release_gate":"BLOCKED_PILOT_UNTIL_G0_G1_G2_EVIDENCE",
        "blocked_reasons":[
            "Only own synthetic IFC input was used for paired deterministic oracle",
            "Most official six-class CRUD operations remain unsupported",
            "Pinned official IFC asset content audit and blind evaluator incomplete",
            "Matched model observation and secured trial execution pending",
        ],
        "api_model_calls":0,
    }
    if success:
        try:
            report["four_static_case_output_proofs"]=_static_case_checksums(source)
        except Exception as exc:
            print(json.dumps({
                "status":"FAILED_STATIC_CASE_OUTPUT_PROOF",
                "error_type":type(exc).__name__
            }))
            return 2
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({key:report[key] for key in (
        "status","scenarios_verified","unit_tests_executed",
        "official_bim_edit_tasks_tested","paid_model_pilot_ready",
    )},indent=2))
    return 0 if success else 2

if __name__=="__main__":
    raise SystemExit(main())
