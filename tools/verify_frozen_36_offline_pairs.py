"""Run THREE real offline D0/XML and I0/Python source-only IFC pairs.

Fixed 36 task candidates retained. Output is write-once and anonymized
for grader-only fields; contains only published task IDs and safe counts.
A passing native demonstration does not imply a scored benchmark trial.
CLI exit 2 is intentional while model, rights, grader and G2/G3 gates block.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.offline_three_pair_readiness import run_offline_three_pair_recheck


def main(argv: list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args(argv)
    report=run_offline_three_pair_recheck()
    if args.output_json is not None:
        path=args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse linked, overwritten, or directory-missing evidence")
        with path.open("x",encoding="utf8",newline="\n") as out:
            json.dump(report,out,indent=2,sort_keys=True)
            out.write("\n")
    print(json.dumps({
        "status":report["status"],
        "fixed_candidates":report["frozen_candidates"],
        "historically_verified_source_reference_pairs":
            report["frozen_source_reference_pairs_historically_verified"],
        "source_only_pairs_passed_now":report["posthoc_dev_native_pairs_passed_now"],
        "official_task_oracle_proofs":
            report["full_instruction_specific_D0_I0_task_oracles_proven"],
        "official_tasks_scored":report["official_bim_edit_tasks_scored"],
        "LLM_trials":report["actual_LLM_trials"],
        "G0_G1_G2_G3_live_allowed":
            report["G0_G1_G2_G3_live_experiment_release_allowed"],
    },sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
