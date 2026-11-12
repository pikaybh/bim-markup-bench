"""Test IFC millimetre->metre->millimetre bridge against original author judges.

No model inference, no GPT provider, no editing of external source or model.
The original per-task unchanged-input scorer output is loaded as a baseline;
round-trip is expected to give exactly the same raw rubric values.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit

from tools.audit_bibimbap_author import (
    AUTHOR_SHA, DATA_SHA, WORKER, read_original_tasks, _sha,
)


def run_unit_audit(author: Path, data: Path, noops: dict) -> dict:
    tasks, pinned = read_original_tasks(author, data)
    if not noops.get("negative_control", {}).get("exhaustive_45", False):
        raise ValueError("Complete original 45-task no-op baseline absent")
    baselines = {
        x["test_id"]: x for x in noops["negative_control"]["observations"]
    }
    if set(baselines) != {x["test_id"] for x in tasks}:
        raise ValueError("Original baseline cohort differs")
    observations = []
    for pos, task in enumerate(tasks, 1):
        print(f"UNIT_ROUNDTRIP {pos}/45 {task['test_id']}", file=sys.stderr, flush=True)
        src = data / "ifc" / task["ifc_relpath"]
        if _sha(src) != task["ifc_sha256"]:
            raise ValueError(f"Source changed: {task['test_id']}")
        with TemporaryDirectory(prefix="bibi-mm-roundtrip-") as temp:
            final = Path(temp) / "roundtrip.ifc"
            original_ifc = ifcopenshell.open(str(src))
            a_scale = ifcopenshell.util.unit.calculate_unit_scale(original_ifc)
            if abs(a_scale - 0.001) > 1e-12:
                raise ValueError(f"Source not millimetre units: {task['test_id']}")
            meter = ifcopenshell.util.unit.convert_file_length_units(
                original_ifc, target_units="METER",
            )
            roundtrip = ifcopenshell.util.unit.convert_file_length_units(
                meter, target_units="MILLIMETER",
            )
            roundtrip.write(str(final))
            guids = lambda f: {x.GlobalId: x.is_a() for x in f.by_type("IfcRoot")}
            guid_parity = guids(original_ifc) == guids(roundtrip)
            test = subprocess.run(
                [sys.executable, "-I", str(WORKER),
                 "--author-repo", str(author), "--test", task["test_id"],
                 "--source-ifc", str(src), "--edited-ifc", str(final)],
                capture_output=True, text=True, timeout=40,
            )
            if not test.stdout.strip():
                result = {"status": "NO_RESULT", "error": test.stderr[-150:]}
            else:
                result = json.loads(test.stdout.strip().splitlines()[-1])
            ref = baselines[task["test_id"]]
            metric_parity = (
                test.returncode == 0 and result.get("status") == "SCORED"
                and result.get("metrics") == ref.get("metrics")
                and math.isclose(float(result["score"]),
                                 float(ref["author_noop_score"]),
                                 rel_tol=0, abs_tol=1e-9)
            )
            observations.append({
                "test_id": task["test_id"],
                "crud": task["crud"],
                "ifc_root_guid_class_parity": guid_parity,
                "original_source_unchanged": _sha(src) == task["ifc_sha256"],
                "schema": roundtrip.schema,
                "roundtrip_scale": ifcopenshell.util.unit.calculate_unit_scale(roundtrip),
                "original_noop_score": ref.get("author_noop_score"),
                "roundtrip_noop_score": result.get("score"),
                "raw_metric_parity": metric_parity,
                "worker_status": result.get("status"),
                "worker_exit": test.returncode,
            })
    passed = sum(
        x["raw_metric_parity"] and x["ifc_root_guid_class_parity"]
        and x["original_source_unchanged"]
        and abs(x["roundtrip_scale"] - 0.001) < 1e-12
        for x in observations
    )
    return {
        "status": "UNIT_BRIDGE_AUTHOR_RUBRIC_PARITY_ALL_45"
            if passed == 45 else "UNIT_BRIDGE_AUTHOR_RUBRIC_DRIFT",
        "author_sha": AUTHOR_SHA, "dataset_sha": DATA_SHA,
        "tasks": 45, "controls_matching": passed,
        "ifc4x3_compiler_compatible_schema_count": sum(
            x["schema"] == "IFC4X3" for x in observations
        ),
        "unsupported_source_schema_task_ids": [
            x["test_id"] for x in observations if x["schema"] != "IFC4X3"
        ],
        "failed_test_ids": [
            x["test_id"] for x in observations if not (
                x["raw_metric_parity"] and x["ifc_root_guid_class_parity"]
                and x["original_source_unchanged"]
                and abs(x["roundtrip_scale"] - 0.001) < 1e-12
            )
        ],
        "source_pinned": pinned,
        "observations": observations,
        "claim_full_IFC_geometric_equivalence": False,
        "author_score_parity_only_for_unmodified_IFC": True,
        "live_llm_calls": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-repo", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--baseline-json", type=Path, required=True)
    ap.add_argument("--output-json", type=Path)
    args = ap.parse_args()
    if not args.baseline_json.is_file():
        ap.error("Original no-op baseline missing")
    baseline = json.loads(args.baseline_json.read_text(encoding="utf8"))
    report = run_unit_audit(args.author_repo, args.dataset, baseline)
    if args.output_json:
        path = args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            ap.error("Refusing to overwrite missing/linked output")
        with path.open("x", encoding="utf8", newline="\n") as output:
            json.dump(report, output, indent=2, sort_keys=True)
            output.write("\n")
    print(json.dumps({
        "status": report["status"],
        "tasks": report["tasks"],
        "controls_matching": report["controls_matching"],
        "failed": report["failed_test_ids"],
    }, sort_keys=True))
    return 0 if report["controls_matching"] == 45 else 2


if __name__ == "__main__":
    raise SystemExit(main())
