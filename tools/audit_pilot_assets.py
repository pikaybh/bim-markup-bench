#!/usr/bin/env python3
"""Offline check of only already-cached 36 pilot input/GT IFCs.

Never downloads an IFC, reads API keys or passes GT into LLM context.
The entire source/GT pair is required before native delta verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.bim_edit import AuditError
from src.data.pilot_asset_audit import audit_fixed_candidate


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata",type=Path,default=Path("data/tasks.jsonl"))
    p.add_argument("--remote-tree",type=Path,default=Path("data/bim_edit_remote_tree.json"))
    p.add_argument("--asset-root",type=Path,default=Path("data/ifc"))
    p.add_argument("--output-json",type=Path,
                   help="Write a new sanitized report; never overwrite an existing artifact")
    p.add_argument("--enforce",action="store_true",
                   help="Always exit 2 until full 324 content/official gate verified")
    args=p.parse_args()
    try:
        outcome=audit_fixed_candidate(
            task_file=args.metadata,tree_file=args.remote_tree,
            local_root=args.asset_root.absolute()
        )
    except (AuditError,ValueError,KeyError,OSError,TypeError):
        outcome={
            "status":"BLOCKED_INVALID_DATA_OR_ASSET_AUDIT",
            "official_scores_computed":0,
            "paid_model_calls":0,
            "full_324_IFC_content_audit_complete":False,
        }
    if args.output_json is not None:
        destination=args.output_json
        if destination.is_symlink() or destination.exists() or not destination.parent.is_dir():
            raise SystemExit("Refusing to overwrite, follow symlink or create unknown output parent")
        with destination.open("x",encoding="utf-8") as file:
            json.dump(outcome,file,sort_keys=True,indent=2)
            file.write("\n")
    print(json.dumps(outcome,indent=2,sort_keys=True,ensure_ascii=False))
    if outcome["status"].startswith("BLOCKED_INVALID"):
        return 2
    return 2 if args.enforce else 0

if __name__=="__main__":
    raise SystemExit(main())
