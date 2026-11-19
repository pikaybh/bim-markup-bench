"""Purely OWN synthetic IFC replay attestation; no official benchmark score.

Uses frozen local mock fixtures, independently re-opens three real IFC files
per case twice, validates the existing scorer's JSON schema and immutability.
Deliberately exits 2: official BIM-Edit code/parity is NOT verified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.independent_replay_attestation import (
    run_own_ifc_replay_qualification,
)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-json",type=Path)
    opts=ap.parse_args()
    evidence=run_own_ifc_replay_qualification()
    if opts.output_json:
        p=opts.output_json
        if p.exists() or p.is_symlink() or not p.parent.is_dir():
            ap.error("Refuse to overwrite/symlink a report or create a parent")
        with p.open("x",encoding="utf8",newline="\n") as out:
            out.write(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
