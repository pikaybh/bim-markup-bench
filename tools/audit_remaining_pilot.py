"""Plan remaining IFC acquisition from pinned metadata only; never downloads."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.data.remaining_pilot_gate import build_remaining_gate

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    a=parser.parse_args()
    result=build_remaining_gate()
    if a.output_json:
        p=a.output_json
        if p.exists() or p.is_symlink() or not p.parent.is_dir():
            parser.error("Refuse existing/symlink output or missing parent")
        with p.open("x",encoding="utf-8",newline="\n") as f:
            f.write(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2

if __name__=="__main__":
    raise SystemExit(main())
