"""BIBIMBAP v0.21: non-destructive cold/warm Docker readiness audit.

This diagnostic performs READ-ONLY operations on exact local executables and
already-pinned repos/image. It does not start a model, container, Python
candidate, or grade IFC, and never restarts Docker/WSL services. One
slow first Docker inspection may be harmless cold-start; a subsequent
quick attested inspection is required before running the old 12-second
v0.19 image-inspection path. The result is momentary host readiness only,
NOT native write parity, VM-grade attestation or paid-model launch approval.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Callable

AUTHOR_SHA = "667004e16bd38fd7d538bcee56191465429fd975"
DATA_SHA = "f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
IMAGE_ID = "sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee"
LOCAL_DOCKER_EXE = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
LOCAL_GIT_EXE = r"C:\Program Files\Git\cmd\git.exe"
DOCKER_ENGINE = "npipe:////./pipe/dockerDesktopLinuxEngine"
READINESS_SCHEMA = "bibimbap.original_public.v021_nondestructive_readiness"
EXPECTED_DOCKER_IMAGE_ID = IMAGE_ID
FORBIDDEN_DOCKER_ARGS = frozenset((
    "run", "create", "exec", "restart", "stop", "start", "kill", "rm",
    "rmi", "pull", "push", "build", "prune", "system", "compose",
))
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class HostReadinessBlocked(ValueError):
    pass


@dataclass(frozen=True)
class Observation:
    name: str
    returncode: int | None
    elapsed_seconds: float
    output: str
    timed_out: bool = False


def _assert(statement: bool, code: str) -> None:
    if not statement:
        raise HostReadinessBlocked(code)


def _command(name: str, argv: list[str], timeout: int) -> Observation:
    """Actual read-only probes: output is HOST-private, not model-visible."""
    _assert(name in PROBE_NAMES, "PROBE_NAME_NOT_ALLOWED")
    _assert((argv == PROBE_COMMANDS[name]) if name in PROBE_COMMANDS
            else (name in {"author_sha","data_sha","author_clean","data_clean","venv_import"}),
            "NON_READONLY_OR_UNEXPECTED_HOST_COMMAND")
    _assert(timeout in range(3, 27), "UNSAFE_PROBE_TIMEOUT")
    begin = time.monotonic()
    try:
        result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout, check=False)
        raw = result.stdout
        return Observation(
            name=name, returncode=result.returncode,
            elapsed_seconds=round(time.monotonic()-begin, 3),
            output=raw.decode("utf8", "replace").strip()[:1024],
        )
    except (subprocess.TimeoutExpired, OSError):
        return Observation(
            name=name, returncode=None,
            elapsed_seconds=round(time.monotonic()-begin, 3),
            output="", timed_out=True,
        )


DOCKER_ARGS = [LOCAL_DOCKER_EXE, "--host", DOCKER_ENGINE]
INSPECT_ARGS = DOCKER_ARGS + [
    "image", "inspect", IMAGE_ID, "--format", "{{.Id}}",
]
INFO_ARGS = DOCKER_ARGS + ["info", "--format", "{{.OSType}}|{{.Architecture}}"]
ORPHANS_ARGS = DOCKER_ARGS + [
    "ps", "--all", "--filter", "name=bmb-v019-sealed-", "--format", "{{.ID}}",
]
PROBE_COMMANDS = {
    "cold_image": INSPECT_ARGS,
    "warm_image": INSPECT_ARGS,
    "docker_info": INFO_ARGS,
    "old_worker_orphans": ORPHANS_ARGS,
}
PROBE_NAMES = frozenset(PROBE_COMMANDS) | frozenset({
    "author_sha", "data_sha", "author_clean", "data_clean", "venv_import",
})


def validate_command_plan() -> None:
    for name, argv in PROBE_COMMANDS.items():
        _assert(argv[:3] == DOCKER_ARGS, "HOST_DOCKER_ENDPOINT_CHANGED")
        _assert(not any(arg in FORBIDDEN_DOCKER_ARGS for arg in argv[3:]),
                "DESTRUCTIVE_DOCKER_COMMAND_DETECTED")
    _assert(IMAGE_ID.startswith("sha256:") and len(IMAGE_ID) == 71,
            "IMAGE_PIN_INVALID")
    _assert(DOCKER_ENGINE == "npipe:////./pipe/dockerDesktopLinuxEngine",
            "UNEXPECTED_DOCKER_ENDPOINT")


def verify_observations(probes: dict[str, Observation]) -> dict:
    """Pure guard: tests can submit forged/slow observations to fail closed."""
    required = PROBE_NAMES
    _assert(set(probes) == required, "INCOMPLETE_NONDESTRUCTIVE_HOST_AUDIT")
    for k, p in probes.items():
        _assert(isinstance(p, Observation) and p.name == k
                and isinstance(p.elapsed_seconds, (int,float))
                and 0 <= p.elapsed_seconds < 1000
                and not p.timed_out and p.returncode == 0,
                "HOST_AUDIT_EXECUTION_UNAVAILABLE_" + k.upper())
    cold = probes["cold_image"]
    warm = probes["warm_image"]
    _assert(cold.output == IMAGE_ID and warm.output == IMAGE_ID,
            "IMMUTABLE_CACHED_DOCKER_IMAGE_ID_MISMATCH")
    _assert(warm.elapsed_seconds < 10.0,
            "WARM_IMAGE_INSPECT_LATENCY_EXCEEDS_FROZEN_WORKER_MARGIN")
    _assert(probes["docker_info"].output.split("|")[0].lower() == "linux",
            "DOCKER_ENGINE_NOT_LINUX")
    _assert(probes["old_worker_orphans"].output == "",
            "POSSIBLE_PREVIOUS_WORKER_CONTAINER_LEFT_BEHIND")
    _assert(probes["author_sha"].output == AUTHOR_SHA,
            "PINNED_ORIGINAL_AUTHOR_SHA_MISMATCH")
    _assert(probes["data_sha"].output == DATA_SHA,
            "PINNED_ORIGINAL_DATA_SHA_MISMATCH")
    _assert(probes["author_clean"].output == "" and
            probes["data_clean"].output == "",
            "ORIGINAL_BENCHMARK_SOURCE_WORKTREES_DIRTY")
    _assert(probes["venv_import"].output == "0.8.4.post1",
            "IFCOPENSHELL_LOCAL_VERSION_UNPINNED")
    return {
        "status": "READY_FOR_SCOPED_OFFLINE_ORIGINAL_DOCKER_REGRESSION_ONLY",
        "docker_first_image_inspect_seconds": cold.elapsed_seconds,
        "docker_second_image_inspect_seconds": warm.elapsed_seconds,
        "docker_first_probe_exceeded_prior_12_second_limit":
            cold.elapsed_seconds > 12.0,
        "pinned_local_image_sha256": IMAGE_ID,
        "pinned_original_author_sha": AUTHOR_SHA,
        "pinned_original_data_sha": DATA_SHA,
        "windows_venv_IfcOpenShell_version": "0.8.4.post1",
        "docker_linux_engine_attested_by_readonly_info": True,
        "v019_container_orphan_detected": False,
        "docker_cli_actually_started_or_modified_containers": False,
        "docker_desktop_or_wsl_service_restarted": False,
        "original_sources_or_scorer_modified": False,
        "host_readiness_is_a_point_in_time_not_availability_guarantee": True,
        "actual_code_execution_or_original_author_scoring_in_this_preflight": False,
        "no_real_LLM_trial_or_paid_model_run_authorized": True,
        "total_original_intention_to_test": 45,
        "causal_pure_representation_comparison_ready": False,
    }


def run_host_probe(base: Path, run: Callable[[str, list[str], int], Observation] = _command) -> dict:
    validate_command_plan()
    _assert(base.is_dir(), "ORIGINAL_EXPERIMENT_BASE_MISSING")
    git = LOCAL_GIT_EXE
    author = base / "bibimbap-author-upstream"
    data = base / "bibimbap-author-data"
    venv = base / "bim-markup-bench" / ".venv" / "Scripts" / "python.exe"
    _assert(author.is_dir() and data.is_dir() and venv.is_file(),
            "ORIGINAL_PUBLIC_AUTHOR_DATA_OR_PYTHON_VENV_NOT_PRESENT")
    fixed = {
        "author_sha": [git, "-C", str(author), "rev-parse", "HEAD"],
        "data_sha": [git, "-C", str(data), "rev-parse", "HEAD"],
        "author_clean": [git, "-C", str(author), "status", "--porcelain"],
        "data_clean": [git, "-C", str(data), "status", "--porcelain"],
        "venv_import": [str(venv), "-c",
                        "import ifcopenshell;print(ifcopenshell.version)"],
    }
    for key, argv in fixed.items():
        _assert(argv == fixed[key], "UNEXPECTED_PROBE_COMMAND")
    probes = {}
    for key, args, timeout in (
        ("cold_image", INSPECT_ARGS, 25),
        ("warm_image", INSPECT_ARGS, 18),
        ("docker_info", INFO_ARGS, 18),
        ("old_worker_orphans", ORPHANS_ARGS, 18),
        ("author_sha", fixed["author_sha"], 12),
        ("data_sha", fixed["data_sha"], 12),
        ("author_clean", fixed["author_clean"], 12),
        ("data_clean", fixed["data_clean"], 12),
        ("venv_import", fixed["venv_import"], 15),
    ):
        probes[key] = run(key, args, timeout)
    return verify_observations(probes)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error("Refuse to overwrite existing immutable audit")
    result = run_host_probe(a.base)
    result["schema"] = READINESS_SCHEMA
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print("V021_READINESS", result["status"])
    print("COLD_SECONDS", result["docker_first_image_inspect_seconds"],
          "WARM_SECONDS", result["docker_second_image_inspect_seconds"])
    print("RESULT_SHA256", sha256(a.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
