"""Read-only author per-task CSV reaggregation; NOT an official scorer.

Only 14 exact pinned public text resources: 7 x per_task.csv/summary.json.
No IFC files, GT files, edited model outputs, Python evaluator or raw
per-task reports are saved in this repository. Task prompts and GT paths
inside the CSV remain grader-private in transient memory, never exported.

Exit code 2 means the official evaluator and independent parity remain blocked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen

from src.evaluation.official_release_provenance import (
    PINNED_RUNS_SHA,RUNS_MODELS
)
from src.evaluation.published_per_task_audit import (
    audit_published_model_set,MAX_CSV_BYTES,MAX_SUMMARY_BYTES
)

ROOT="https://huggingface.co/datasets/BIM-Edit/BIM-Edit-runs/resolve/"
ALLOWED_REDIRECT_HOSTS={"huggingface.co","us.aws.cdn.hf.co"}


def _get(model:str,kind:str)->bytes:
    if model not in RUNS_MODELS or kind not in ("csv","summary"):
        raise ValueError("Unexpected public release resource")
    path="eval/per_task.csv" if kind=="csv" else "eval/summary.json"
    limit=MAX_CSV_BYTES if kind=="csv" else MAX_SUMMARY_BYTES
    url=ROOT+PINNED_RUNS_SHA+"/"+model+"/"+path
    request=Request(url,headers={
        "User-Agent":"bim-markup-bench-author-public-score-audit/0.1",
        "Accept":"text/csv, application/json",
    })
    with urlopen(request,timeout=25) as f:
        parsed=urlsplit(f.geturl())
        if (parsed.scheme!="https" or
                parsed.hostname not in ALLOWED_REDIRECT_HOSTS):
            raise ValueError("Public score URL redirected outside approved HF CDN")
        content=f.read(limit+1)
    if not content or len(content)>limit:
        raise ValueError("Public score data missing/oversized")
    return content


def run_published_per_task_audit()->dict:
    pairs={}
    for model in sorted(RUNS_MODELS):
        csv_bytes=_get(model,"csv")
        summary_bytes=_get(model,"summary")
        summary=json.loads(summary_bytes.decode("utf8"))
        pairs[model]=(csv_bytes,summary)
    return audit_published_model_set(pairs)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    options=parser.parse_args()
    report=run_published_per_task_audit()
    if options.output_json:
        path=options.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refusing evidence overwrite/symlink/nonexistent parent")
        with path.open("x",encoding="utf8",newline="\n") as handle:
            handle.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
