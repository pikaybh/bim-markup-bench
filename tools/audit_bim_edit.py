#!/usr/bin/env python3
"""Pinned metadata-only BIM-Edit audit; NEVER downloads bulk IFC assets."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from src.data.bim_edit import AuditError, metadata_audit, read_tasks, verify_local_assets

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fetch-metadata-only", action="store_true",
                   help="Allows downloading only 180KB task records and remote API JSON inventory, NOT IFC assets.")
    p.add_argument("--verify-local-assets", type=Path, help="Optional OFFLINE full referenced corpus byte check; requires downloaded licensed IFC under the specified root.")
    args = p.parse_args()
    try:
        result = metadata_audit(
            task_path=Path("data/tasks.jsonl"),
            output_path=Path("data/bim_edit_remote_audit.json"),
            allow_network=args.fetch_metadata_only,
        )
    except (AuditError, OSError, ValueError) as exc:
        print("AUDIT_BLOCKED:", str(exc))
        return 2
    if args.verify_local_assets is not None:
        rows = read_tasks(Path("data/tasks.jsonl"))
        tree = json.loads(Path("data/bim_edit_remote_tree.json").read_text())
        try:
            verified = verify_local_assets(rows, tree, args.verify_local_assets)
        except (AuditError, OSError) as exc:
            print("IFC_CONTENT_VERIFICATION_BLOCKED:", str(exc))
            return 2
        print("IFC_CONTENT_BYTE_VERIFICATION:", json.dumps(verified, sort_keys=True))
        print("NOTE: IfcOpenShell element-level source/GT delta verification remains a separate gate.")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("STATUS: REMOTE_METADATA_ONLY — NOT A FULL IFC BENCHMARK DATA AUDIT")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
