"""Execute one pinned, original BIBIMBAP author test on cloned IFC files.

Isolated interpreter subprocess entrypoint. Does not edit upstream inputs,
generate LLM calls, or change the author's scoring semantics.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib
import json
import math
import re
import sys
import traceback
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-repo", type=Path, required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--source-ifc", type=Path, required=True)
    ap.add_argument("--edited-ifc", type=Path, required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"(?:test|geometry_test|topological_test)_\d{2}", args.test):
        raise SystemExit("Only original Create/Update/Delete author modules allowed")
    author = args.author_repo.resolve(strict=True)
    source = args.source_ifc.resolve(strict=True)
    edited = args.edited_ifc.resolve(strict=True)
    if source == edited or not source.is_file() or not edited.is_file():
        raise SystemExit("Two real, independently cloned IFC paths required")
    if not (author / "data" / "tests" / (args.test + ".py")).is_file():
        raise SystemExit("Original author test module not found")

    sys.path.insert(0, str(author))
    try:
        # All output from author tests is stderr; stdout is structured JSON only.
        with redirect_stdout(sys.stderr):
            module = importlib.import_module("data.tests." + args.test)
            answer = module.execute_test(str(source), str(edited), None)
        if not isinstance(answer, dict) or not answer:
            raise ValueError("Author scorer returned non-dict or empty metrics")
        metrics = {}
        for key, value in answer.items():
            if not isinstance(key, str) or not isinstance(value, (bool, int, float)):
                raise TypeError(f"Invalid metric type: {key!r}")
            v = float(value)
            if not math.isfinite(v):
                raise ValueError(f"Nonfinite metric: {key}")
            metrics[key] = v
        # Preserve the original author's arithmetic, even if it seems questionable.
        score = sum(metrics.values()) / len(metrics)
        print(json.dumps({"status": "SCORED", "metrics": metrics, "score": score}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "type": type(exc).__name__,
            "message": str(exc)[:260],
            "trace_tail": traceback.format_exc(limit=2)[-500:],
        }, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
