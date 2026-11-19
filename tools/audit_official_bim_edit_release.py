"""Read-only, bounded public BIM-Edit release inventory / score-origin audit.

Fetches ONLY two whitelisted small JSON resources:
  1) Hugging Face runs REPOSITORY FILE PATH metadata (no files/GT);
  2) one author's aggregate evaluation JSON at a PINNED revision.

No raw per-task examples, candidate outputs, model traces, IFCs, official
evaluator Python, GT, model API or billed calls are downloaded.
Exit 2 is EXPECTED: official executable scorer is not verified.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit

from src.evaluation.official_release_provenance import (
    PINNED_RUNS_SHA,combine_release_evidence,
)


BASE="https://huggingface.co"
WHITELIST={
    "runs_repo_metadata":BASE+"/api/datasets/BIM-Edit/BIM-Edit-runs",
    "one_published_aggregate":
        BASE+"/datasets/BIM-Edit/BIM-Edit-runs/resolve/"
        +PINNED_RUNS_SHA+"/claude-sonnet/eval/summary.json",
}
MAX_JSON_BYTES=2*1024*1024


def _fetch_named_json(name:str)->tuple[dict,str]:
    if name not in WHITELIST:
        raise ValueError("Unapproved public release URL; no arbitrary fetch")
    req=Request(WHITELIST[name],headers={
        "User-Agent":"bim-markup-bench-public-provenance-audit/0.1",
        "Accept":"application/json",
    })
    with urlopen(req,timeout=20) as response:
        final=response.geturl()
        # Pinned public summary is stored as Git LFS on Hugging Face's
        # official HTTPS CDN. The exact host was observed on 2026-11-10.
        # Never allow arbitrary redirects, external hosts or HTTP fallback.
        parsed=urlsplit(final)
        if (parsed.scheme!="https" or
                parsed.hostname not in {"huggingface.co","us.aws.cdn.hf.co"}):
            raise ValueError("Unapproved release CDN redirect forbidden")
        raw=response.read(MAX_JSON_BYTES+1)
    if not raw or len(raw)>MAX_JSON_BYTES:
        raise ValueError("Oversized/missing public metadata response")
    data=json.loads(raw.decode("utf8"))
    if not isinstance(data,dict):
        raise ValueError("Unrecognized public release JSON")
    return data,sha256(raw).hexdigest()


def run_public_release_audit()->dict:
    metadata,metadata_hash=_fetch_named_json("runs_repo_metadata")
    summary,summary_hash=_fetch_named_json("one_published_aggregate")
    report=combine_release_evidence(metadata,summary)
    report["source_content_integrity"]={
        "metadata_raw_json_sha256":metadata_hash,
        "claude_summary_raw_json_sha256":summary_hash,
        "two_whitelisted_public_JSON_requests":True,
        "source_version":"2026-11-10_PINNED_RUNS_SHA",
    }
    return report


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=run_public_release_audit()
    if args.output_json is not None:
        dest=args.output_json
        if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
            parser.error("Refuse overwrite/symlink/missing evidence directory")
        with dest.open("x",encoding="utf8",newline="\n") as handle:
            handle.write(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
