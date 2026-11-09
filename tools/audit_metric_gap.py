"""Print fail-closed, no-GT scorer gap evidence. Always returns 2 while official gate is blocked."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from src.evaluation.metric_gap_audit import audit_scorer_gap

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    a=parser.parse_args()
    report=audit_scorer_gap()
    if a.output_json:
        p=a.output_json
        if p.exists() or p.is_symlink() or not p.parent.is_dir():
            parser.error("Refuse evidence overwrite/symlink or missing parent")
        with p.open("x",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 2

if __name__=="__main__":
    raise SystemExit(main())
