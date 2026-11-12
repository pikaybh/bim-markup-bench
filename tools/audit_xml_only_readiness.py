"""Fail-closed, no-network single-arm Direct XML BIM-Edit readiness report.

Example:
  python -m tools.audit_xml_only_readiness --task-jsonl PATH --output-json PATH
No LLMs, network, IFC GT model loading or numerical paper scores.
Exit code 2 means the live experiment remains blocked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.xml_only_readiness import ROOT, ReadinessEvidenceError, audit_xml_only


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, default=ROOT)
    parser.add_argument("--task-jsonl", type=Path,
                        help="Read-only 324-row pinned public task metadata; never provide GT IFC")
    parser.add_argument("--output-json", type=Path,
                        help="Write-once report path; refuses overwrite or symlink")
    args = parser.parse_args(argv)
    try:
        report = audit_xml_only(
            evidence_root=args.evidence_root, task_jsonl=args.task_jsonl,
        )
    except (ReadinessEvidenceError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "EVIDENCE_INVALID", "reason": str(exc)}, sort_keys=True))
        return 2

    if args.output_json is not None:
        path = args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse overwrite, symlink or missing parent directory")
        with path.open("x", encoding="utf8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps({
        "status": report["status"],
        "task_population": report["published_population_size"],
        "candidate_denominator": report["existing_candidate_size"],
        "candidate_dispositions": report["candidate_readiness_dispositions"],
        "official_score_computed": False,
        "model_calls": 0,
        "launch_blockers": report["launch_blockers"],
    }, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
