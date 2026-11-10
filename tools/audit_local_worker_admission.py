"""Read-only local Docker readiness proof for OWN-synthetic worker #19.

Never starts or restarts Docker Desktop, WSL, a service or a container.
The separately curated historical OWN Docker test result is provenance
context only, NOT live readiness. Exits 2 even on healthy local Docker
because generated Python/paid G3 research execution remains unauthorized.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from src.runner.ifc_worker import OWN_SOURCE
from src.runner.worker_admission import (
    IMAGE_ID,offline_own_admission_audit,
)


ROOT=Path(__file__).resolve().parents[1]
OWN_AUDIT_CANDIDATE=b"print('STATIC_ONLY_NEVER_EXECUTED_BY_ADMISSION')\n"


def audit_local_worker_admission()->dict:
    historical=json.loads(
        (ROOT/"reports/dynamic_own_candidate_evidence.json").read_text(encoding="utf8"))
    candidate_id=historical.get("image_id")
    if not isinstance(candidate_id,str) or not IMAGE_ID.fullmatch(candidate_id):
        raise ValueError("Historical worker image id is malformed")
    source_sha=sha256(OWN_SOURCE.read_bytes()).hexdigest()
    code_sha=sha256(OWN_AUDIT_CANDIDATE).hexdigest()
    evidence=offline_own_admission_audit(
        candidate_id,OWN_AUDIT_CANDIDATE,code_sha,source_sha,seed=31)
    artifacts={}
    for rel in ("docker/ifc_worker/Dockerfile.amd64",
                "docker/ifc_worker/requirements.amd64.lock",
                "docker/ifc_worker/run_candidate.py"):
        path=ROOT/rel
        if path.is_symlink() or not path.is_file():
            raise ValueError("Curated worker source artifact missing or replaced by symlink")
        artifacts[rel]=sha256(path.read_bytes()).hexdigest()
    evidence.update({
        "historical_proof_image_id":candidate_id,
        "historical_proof_has_own_dynamic_isolation_record":
            historical.get("status")=="OWN_SYNTHETIC_DYNAMIC_SANDBOX_PROOF_PASS",
        "historical_proof_is_NOT_current_admission":True,
        "curated_worker_artifact_source_hashes":artifacts,
        "artifact_source_hashes_do_NOT_attest_cached_image_build":True,
        "live_worker_image_build_SBOM_verified":False,
        "Docker_or_WSL_services_started":False,
        "candidate_python_source_returned_in_evidence":False,
        "python_source_executed":False,
        "paid_model_provider_calls":0,
        "official_scorer_calls":0,
        "official_tasks_scored":0,
        "G2_paid_or_generated_model_worker_authorized":False,
    })
    return evidence


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    data=audit_local_worker_admission()
    if args.output_json is not None:
        dest=args.output_json
        if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
            parser.error("Refuse overwrite, symlink or missing directory")
        with dest.open("x",encoding="utf8",newline="\n") as handle:
            handle.write(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print(json.dumps(data,indent=2,sort_keys=True))
    return 2


if __name__=="__main__":
    raise SystemExit(main())
