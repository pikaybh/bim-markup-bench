"""Offline XML projection admission audit for all 45 original BIBIMBAP edits.

Projection success DOES NOT imply the proposed task can be executed or scored.
Original millimetre IFCs are normalized to metre units on temporary copies.
No LLM, no authoring, no modified IFC output and no original data in report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit

from src.runtime.ifc_projection import project_ifc
from tools.audit_bibimbap_author import read_original_tasks, _sha


def audit_projectability(author: Path, data: Path) -> dict:
    tasks, pinned = read_original_tasks(author, data)
    records = []
    cache = {}
    for index, task in enumerate(tasks, 1):
        print(f"XML_PROJECTION {index}/45 {task['test_id']}", file=sys.stderr, flush=True)
        key = task["ifc_relpath"]
        if key not in cache:
            src = data / "ifc" / key
            if _sha(src) != task["ifc_sha256"]:
                raise ValueError(f"Original IFC modified: {task['test_id']}")
            f = ifcopenshell.open(str(src))
            observed_schema = f.schema
            record = {
                "schema": observed_schema,
                "original_units_to_meters": ifcopenshell.util.unit.calculate_unit_scale(f),
                "xml_projection_passed": False,
                "source_ifc4x3_compatible": observed_schema == "IFC4X3",
            }
            if observed_schema != "IFC4X3":
                record["reason"] = "ORIGINAL_SOURCE_NOT_IFC4X3"
            else:
                try:
                    with TemporaryDirectory(prefix="bibi-projection-") as temp:
                        normalized = ifcopenshell.util.unit.convert_file_length_units(
                            f, target_units="METER",
                        )
                        meter = Path(temp) / "meter.ifc"
                        normalized.write(str(meter))
                        projection = project_ifc(meter, strict_on_opaque=False)
                        counts = dict(projection.supported_class_counts)
                        record.update({
                            "xml_projection_passed": True,
                            "managed_entity_count": len(projection.projected_global_ids),
                            "opaque_entity_count": len(projection.opaque_references),
                            "managed_wall_count": counts.get("IfcWall", 0),
                            "managed_door_count": counts.get("IfcDoor", 0),
                            "managed_window_count": counts.get("IfcWindow", 0),
                            "managed_space_count": counts.get("IfcSpace", 0),
                            "managed_column_count": counts.get("IfcColumn", 0),
                            "managed_slab_count": counts.get("IfcSlab", 0),
                        })
                except Exception as exc:
                    record["reason"] = type(exc).__name__ + ": " + str(exc)[:130]
            cache[key] = record
        records.append({
            "test_id": task["test_id"],
            "crud": task["crud"],
            "category": task["category"],
            "source": cache[key],
        })
    counts = dict(sorted(Counter(
        "PROJECTABLE" if x["source"]["xml_projection_passed"] else x["source"].get("reason", "UNKNOWN")
        for x in records
    ).items()))
    return {
        "schema": "bibimbap-original-xml-projection-audit/v0.1",
        "author_commit_sha": pinned["author_commit_sha"],
        "dataset_commit_sha": pinned["data_commit_sha"],
        "assessed_editing_task_count": 45,
        "unique_editing_source_ifc_count": len(cache),
        "projection_dispositions": counts,
        "per_task": records,
        "notes": [
            "Original author IFCs are millimetre units",
            "Source projection success is a necessary, not sufficient, condition for an editable task",
            "Opaque IFC entities are retained in the IFC source, not editable XML",
            "No LLM, no XML task completion, no scored authoring trial in this audit",
        ],
        "llm_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    report = audit_projectability(args.author_repo, args.dataset)
    if args.output_json:
        p = args.output_json
        if p.exists() or p.is_symlink() or not p.parent.is_dir():
            parser.error("Refuse overwrite or missing directory")
        with p.open("x", encoding="utf8", newline="\n") as out:
            json.dump(report, out, indent=2, sort_keys=True)
            out.write("\n")
    print(json.dumps({
        "assessed_tasks": report["assessed_editing_task_count"],
        "unique_source_ifcs": report["unique_editing_source_ifc_count"],
        "dispositions": report["projection_dispositions"],
        "llm_calls": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
