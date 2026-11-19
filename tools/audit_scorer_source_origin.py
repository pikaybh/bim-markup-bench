"""G0 #4 author-controlled vs third-party scorer provenance (offline).

Reads only a pinned *historical public report* and fixed, inspected GitHub
source references. No web code download, package import, model, GT or score.
Exit 2 is EXPECTED while original executable scorer is still unverified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.scorer_source_origin import audit_scorer_origin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args(argv)
    result=audit_scorer_origin()
    if args.output_json is not None:
        path=args.output_json
        if path.is_symlink() or path.exists() or not path.parent.is_dir():
            parser.error("Refuse existing/symlinked report or missing parent")
        with path.open("x",encoding="utf8",newline="\n") as fh:
            json.dump(result,fh,sort_keys=True,indent=2)
            fh.write("\n")
    print(json.dumps({
        "status":result["status"],
        "third_party_source":result["third_party_reimplementation"]["repository_full_name"],
        "third_party_origin":result["third_party_reimplementation"]["source_classification"],
        "original_author_cli_verified":result["author_original_evaluator_cli_entrypoint_verified"],
        "official_tasks_scored":result["official_tasks_scored"],
        "paid_model_calls":result["paid_model_calls"],
    },sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
