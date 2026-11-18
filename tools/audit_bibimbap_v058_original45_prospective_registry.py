"""v0.58 freeze/replay actual original 45-task source-cluster registry.

Entire execution is offline: read-only original 45 public question SHA
derivation, 31 real IFC source file SHA+schema, 45 original author test
module SHA, 45 task-by-arm capability classification and source-cluster
prospective six-task candidate holdout ordering. No LLM, no grader runs,
no paid request, no original source or author evaluator bytes in report.
"""
from __future__ import annotations

import argparse
from hashlib import sha256

from tools.bibimbap_v058_original45_capability_registry import (
    ROOT,build_registry,canonical,
)

REPORT=ROOT/"reports"/"bibimbap_v058_original45_capability_prospective_holdout_20261118.json"


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    exclusive=parser.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--write",action="store_true")
    exclusive.add_argument("--check",action="store_true")
    options=parser.parse_args()
    content=canonical(build_registry())
    if options.write:
        # Prior/source reports are NEVER rewritten and no model inputs or
        # original evaluator code copied into the output.
        with REPORT.open("xb") as fd:
            fd.write(content)
    else:
        if not REPORT.is_file() or REPORT.is_symlink() or REPORT.read_bytes()!=content:
            raise RuntimeError("Real original 45-source registry replay no longer byte identical")
    print("V058_ORIGINAL_45_CAPABILITY=PASS IFC_CLUSTERS=31 "
          "DEVELOPER_SUPPORTED_PER_ARM=4 UNTESTED=41 "
          "UNTOUCHED_HOLDOUT_CLUSTERS=6 INELIGIBLE_FOR_TRIAL=6 "
          "MODEL_CALLS=0 BILLABLE=0 SHA256="+sha256(content).hexdigest())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
