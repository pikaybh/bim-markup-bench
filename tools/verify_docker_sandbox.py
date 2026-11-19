#!/usr/bin/env python3
"""Trusted Docker kernel proof for synthetic probes or ONE pinned source-input mount.

Uses only a cached exact-sha256 Linux image. Never runs model-generated
Python, mounts benchmark GT, reads API keys, calls providers, or pulls images.
Even successful probe does not authorize paid/live model execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.runner.docker_isolation import (
    DockerProbePolicy,DockerIsolationError,run_trusted_docker_probe,
    run_pinned_pilot_input_mount_probe,
)


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-id",required=True,
        help="Exact local Docker image ID sha256:... ; NOT a tag or mutable image name")
    parser.add_argument(
        "--python-entrypoint",
        choices=("/usr/bin/python3","/usr/local/bin/python3"),
        default="/usr/bin/python3",
        help="Select a fixed trusted Python path present in the pinned image; no arbitrary command",
    )
    parser.add_argument(
        "--pilot-stage-input-mount",
        action="store_true",
        help="Use one already-cached, SHA-pinned pilot INPUT for trusted 3-arm Docker mount proof; no LLM/GT",
    )
    parser.add_argument("--output-json",type=Path,
        help="Write a new sanitized evidence JSON; fail rather than overwrite")
    parser.add_argument("--enforce-live",action="store_true",
        help="Always return code 2: full approved Python worker and model broker absent")
    options=parser.parse_args()
    try:
        policy=DockerProbePolicy(
            options.image_id,python_entrypoint=options.python_entrypoint
        )
        if options.pilot_stage_input_mount:
            data=run_pinned_pilot_input_mount_probe(
                policy,Path(__file__).resolve().parents[1]
            )
        else:
            data=run_trusted_docker_probe(policy)
    except (DockerIsolationError,OSError,ValueError,KeyError,TypeError):
        data={
            "status":(
                "BLOCKED_PINNED_PILOT_INPUT_DOCKER_PROBE_FAILED"
                if options.pilot_stage_input_mount else "BLOCKED_OS_PROBE_FAILED"
            ),
            "probe_id":(
                "g2-pinned-bim-edit-input-mount-v0.1"
                if options.pilot_stage_input_mount else "g2-docker-kernel-probe-v0.1"
            ),
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
        with destination.open("x",encoding="utf-8",newline="\n") as output:
            output.write(text)
    print(text,end="")
    expected_status=(
        "PINNED_PILOT_DOCKER_INPUT_MOUNT_PROBE_PASS"
        if options.pilot_stage_input_mount else "KERNEL_ISOLATION_PROBE_PASS"
    )
    if data["status"]!=expected_status:
        return 2
    return 2 if options.enforce_live else 0


if __name__=="__main__":
    raise SystemExit(main())
