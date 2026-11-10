"""Offline-only G2/G3 source-input context-cost audit. Never starts a model.

Returns code 2 intentionally: byte-identical observations and source-backed
v0.2 metadata can be measured, but approved tokenizer, billing, model
transport, official scorer and I-arm OS isolation remain unverified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runner.offline_context_cost_gate import audit_one_frozen_real_context


ROOT=Path(__file__).resolve().parents[1]


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    options=parser.parse_args()
    report=audit_one_frozen_real_context(ROOT)
    if options.output_json is not None:
        path=options.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse overwrite, symlink or absent output directory")
        with path.open("x",encoding="utf8",newline="\n") as handle:
            handle.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
