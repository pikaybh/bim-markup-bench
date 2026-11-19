"""G2 #20: GT-free 36-case frozen source-context fairness coverage.

This is an offline observation audit, NOT a model experiment or score.
Exit 2 intentionally even if all available source text comparisons succeed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runner.frozen_context_parity import audit_frozen_source_contexts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    report = audit_frozen_source_contexts()
    if args.output_json is not None:
        dest = args.output_json
        if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
            parser.error("Refusing overwrite/link/nonexistent output parent")
        with dest.open("x", encoding="utf8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, sort_keys=True, indent=2)
            fh.write("\n")
    # Do not dump raw task instructions, IFC paths, GUIDs or GT artifacts.
    print(json.dumps({
        "version": report["version"],
        "research_gate": report["research_gate"],
        "tasks_total": report["tasks_total"],
        "status_counts": report["status_counts"],
        "model_calls": 0,
        "official_benchmark_tasks_scored": 0,
    }, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
