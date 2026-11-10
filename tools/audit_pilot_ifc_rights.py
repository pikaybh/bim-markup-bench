"""G0 #3: offline IFC HEADER provenance and content-rights triage.

This CLI is an audit, not legal clearance, official grading or a live pilot.
It returns exit code 2 when expected blockers are preserved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.pilot_ifc_rights import audit_pilot_ifc_rights


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-json", type=Path)
    args = ap.parse_args()
    record = audit_pilot_ifc_rights()
    if args.output_json is not None:
        p = args.output_json
        if p.exists() or p.is_symlink() or not p.parent.is_dir():
            ap.error("Refusing overwrite, symlink or missing destination directory")
        with p.open("x", encoding="utf8", newline="\n") as stream:
            json.dump(record, stream, sort_keys=True, indent=2, ensure_ascii=False)
            stream.write("\n")
    print(json.dumps({
        "gate_status": record["gate_status"],
        "tasks_total": record["tasks_total"],
        "status_counts": record["status_counts"],
        "unique_remaining_file_count": record["unique_remaining_file_count"],
        "unique_remaining_file_bytes": record["unique_remaining_file_bytes"],
        "individual_model_license_documents_verified": 0,
        "LLM_calls": 0,
        "official_tasks_scored": 0,
    }, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
