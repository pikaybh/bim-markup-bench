"""Two independently prepared IFC positive controls for original BIBIMBAP grader.

Not LLM-generated and not BIMX/XML results. Purpose: demonstrate author
scorer distinguishes a real edit from no edit. Never alters upstream IFC.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.root

from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, _head, _sha
from tools.audit_bibimbap_author import WORKER


def create_edited_copy(original: Path, dest: Path, task: str) -> None:
    model = ifcopenshell.open(str(original))
    if task == "test_16":
        target = model.by_guid("22hyxvAPr65PFt9WZfHS2x")
        if not target or not target.is_a("IfcColumn"):
            raise ValueError("Pinned column missing")
        ifcopenshell.api.root.remove_product(model, product=target)
    elif task == "test_15":
        target = model.by_guid("22hyxvAPr65PFt9WZfHSMu")
        if not target or not target.is_a("IfcColumn"):
            raise ValueError("Pinned column missing")
        p = target.ObjectPlacement.RelativePlacement.Location
        coords = list(p.Coordinates)
        coords[1] -= 3000.0  # author test compares ObjectPlacement / 1000 to meters
        p.Coordinates = coords
    else:
        raise ValueError("Unsupported own positive witness")
    model.write(str(dest))


def run_positive(author: Path, data: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(data) != DATA_SHA:
        raise ValueError("Upstream revisions drifted")
    path = data / "ifc" / "basic_tasks.ifc"
    digest = _sha(path)
    observations = []
    for task in ("test_15", "test_16"):
        with TemporaryDirectory(prefix="bibimbap-own-positive-") as tmp:
            original = Path(tmp) / "source.ifc"
            edited = Path(tmp) / "edited.ifc"
            shutil.copy2(path, original)
            create_edited_copy(original, edited, task)
            result = subprocess.run(
                [sys.executable, "-I", str(WORKER),
                 "--author-repo", str(author), "--test", task,
                 "--source-ifc", str(original), "--edited-ifc", str(edited)],
                capture_output=True, text=True, timeout=30,
            )
            output = json.loads(result.stdout.splitlines()[-1]) if result.stdout else {}
            if _sha(original) != digest or _sha(path) != digest:
                raise ValueError("Original IFC modified by positive witness")
            observations.append({
                "test_id": task,
                "source_original_unchanged": True,
                "result": output,
                "worker_exit": result.returncode,
            })
    return {
        "mode": "developer_controlled_author_IFC_positive_witness_not_llm",
        "author_sha": AUTHOR_SHA,
        "dataset_sha": DATA_SHA,
        "n": 2,
        "observations": observations,
        "claims_author_paper_reproduction": False,
        "model_calls": 0,
    }


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--author-repo", type=Path, required=True)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output-json", type=Path)
    args = p.parse_args()
    result = run_positive(args.author_repo, args.dataset)
    if args.output_json:
        path = args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            p.error("Output exists or directory missing")
        with path.open("x", encoding="utf8", newline="\n") as out:
            json.dump(result, out, indent=2, sort_keys=True)
            out.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if all(x["result"].get("status") == "SCORED" for x in result["observations"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
