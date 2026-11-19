"""G1 #16: live source-only pilot crosswalk, always BLOCKED for paid trial.

Reads only fixed local evidence and the verified original cached public
input IFCS (via existing source preflight). Never opens a benchmark GT IFC
or runs an authoring arm or scorer. Does not start Docker/WSL or a model.

The output intentionally exits 2 regardless of passing internal audit
invariants: the frozen 36 are NOT ready for a legitimate LLM trial.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.frozen_pilot_readiness import (
    load_pinned_evidence,reconcile_pilot_evidence
)
from tools.audit_pilot_source_eligibility import audit_frozen_pilot
from tools.audit_local_worker_admission import audit_local_worker_admission


def audit_frozen_pilot_readiness()->dict:
    evidence=load_pinned_evidence()
    # Uses only originally cached public input IFC for each conditional
    # preflight. Private target metadata stay in a trusted process, while
    # existing report publishing sanitizes all details.
    live_source=audit_frozen_pilot()
    docker=audit_local_worker_admission()
    host=docker["host_observation"]
    host={**host,"status":docker["status"]}
    return reconcile_pilot_evidence(
        evidence,live_source,
        worker_observation=host,
        official_scorer=evidence["official"],
        budget=evidence["budget"],
    )


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-json",type=Path)
    opts=p.parse_args()
    result=audit_frozen_pilot_readiness()
    if opts.output_json:
        path=opts.output_json
        if path.is_symlink() or path.exists() or not path.parent.is_dir():
            p.error("Refusing preexisting/symlink result or unknown parent")
        with path.open("x",encoding="utf8",newline="\n") as f:
            f.write(json.dumps(result,sort_keys=True,indent=2)+"\n")
    # Only aggregate counters are printed, not model-context data,
    # target GUID, source/GT path or task prompts.
    print(json.dumps({
        key:result[key] for key in (
            "status","task_count","static_engine_unsupported_count",
            "currently_cached_conditional_input_probed_count",
            "missing_conditional_input_count",
            "historical_verified_input_and_reference_deltas_count",
            "historical_unavailable_source_or_GT_asset_count",
            "distinct_manual_source_only_pair_task_count",
            "full_instruction_specific_paired_D0_I0_task_oracles_proven",
            "official_task_scores","real_model_provider_calls",
            "docker_current_own_worker_admission","disposition_counts",
        )
    },sort_keys=True,indent=2))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
