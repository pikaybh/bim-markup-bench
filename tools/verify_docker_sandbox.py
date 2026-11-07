#!/usr/bin/env python3
"""Trusted Docker kernel isolation proof for synthetic scratch data only.

Uses only a cached exact-sha256 Linux image. Never runs model-generated
Python, mounts benchmark GT, reads API keys, calls providers, or pulls images.
Even successful probe does not authorize paid/live model execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runner.docker_isolation import (
    DockerProbePolicy,DockerIsolationError,run_trusted_docker_probe
)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id",required=True,
        help="Exact local Docker image ID sha256:... ; NOT a tag or mutable image name")
    parser.add_argument("--output-json",type=Path,
        help="Write a new sanitized evidence JSON; fail rather than overwrite")
    parser.add_argument("--enforce-live",action="store_true",
        help="Always return code 2: full approved Python worker and model broker absent")
    options=parser.parse_args()
    try:
        data=run_trusted_docker_probe(DockerProbePolicy(options.image_id))
    except (DockerIsolationError,OSError,ValueError,KeyError,TypeError):
        data={
            "status":"BLOCKED_OS_PROBE_FAILED",
            "probe_id":"g2-docker-kernel-probe-v0.1",
            "worker_image_scientifically_approved":False,
            "production_scored_python_enabled":False,
            "real_model_provider_called":False,
            "paid_model_pilot_ready":False,
        }
    text=json.dumps(data,sort_keys=True,indent=2)+"\n"
    if options.output_json is not None:
        destination=options.output_json
        if destination.exists() or destination.is_symlink():
            raise SystemExit("Refusing to overwrite existing probe evidence")
        if not destination.parent.is_dir():
            raise SystemExit("Probe evidence parent directory must preexist")
        with destination.open("x",encoding="utf-8") as output:
            output.write(text)
    print(text,end="")
    if data["status"]!="KERNEL_ISOLATION_PROBE_PASS":
        return 2
    return 2 if options.enforce_live else 0


if __name__=="__main__":
    raise SystemExit(main())
