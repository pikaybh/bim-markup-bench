"""Run first-match source-only IFC rubric preflight; NEVER release paid model runs.

Fixed three post-hoc developer-authored D0/I0 IFC pairs, 36-candidate
denominator, independent surrogate only. Every data, budget and
worker admission gate remains blocked. CLI exits 2 intentionally.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.first_pilot_release_preflight import run_first_pilot_preflight


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args(argv)
    report=run_first_pilot_preflight()
    if args.output_json:
        file=args.output_json
        if file.exists() or file.is_symlink() or not file.parent.is_dir():
            parser.error("Output report exists, linked, or missing parent")
        with file.open("x",encoding="utf8",newline="\n") as out:
            json.dump(report,out,indent=2,sort_keys=True)
            out.write("\n")
    print(json.dumps({
        "status":report["status"],
        "source_only_native_ifcs_checked":report["offline_native_outputs_scored_by_surrogate"],
        "source_relative_rubric_passed":report["surrogate_postconditions_passed"],
        "official_tasks_scored":report["official_bim_edit_scores_computed"],
        "actual_llm_attempts":report["model_generated_attempts"],
        "paid_calls_authorized":report["real_matched_llm_trial_allowed"],
        "worker_linux_engine_available":report["worker_linux_engine_available"],
    },sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
