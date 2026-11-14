"""Research v0.19: host-only, offline, sealed *single-shot* Docker IFC writer.

Reads pinned original PUBLIC IFC into a disposable source-only read-only mount.
Runs ONE explicitly developer-authored offline fixture, never a model script,
inside an already cached full-SHA immutable OWN IFC worker image. Captures
untrusted candidate stdout/stderr in bounded host-only memory and NEVER
exposes it to the LLM. Results reach host-only validation after termination.

Reuses historical audited Docker CLI local endpoint and pre-start HostConfig
validation from src.runner.ifc_worker, and bounded attach from
src.runner.generated_candidate.  None of their older OWN-synthetic success
claims are relabeled as original-source or model-scored results.

WARNING: Linux Docker Desktop containers are OS-isolated, not independently
audited VM-grade hostile-code confinement. This does NOT itself certify all
source observation equality, native write parity, or authorize paid LLM trials.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
import uuid

from src.runner.docker_isolation import DockerIsolationError
from src.runner.ifc_worker import (
    _run, _verify_local_image, _inspect_config,
)
from src.runner.generated_candidate import _limited_attach, _recover_ifc


PINNED_LOCAL_IMAGE = (
    "sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee"
)
MAX_PUBLIC_IFC_BYTES = 256 * 1024
MAX_DEVELOPER_FIXTURE_BYTES = 64 * 1024
OUTPUT_LIMIT_BYTES = 256 * 1024
DEFAULT_WALL_SECONDS = 18
_ORIGINAL_SHA = re.compile(r"^[0-9a-f]{64}$")
_BAD_SECRET_MARKERS = (
    "OPENAI_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET", "SSH_AUTH_SOCK",
)


class SealedWorkerBlocked(ValueError):
    pass


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class PrivateSealedOutcome:
    """HOST TRUSTED ONLY: NEVER attach this object to LLM/model context."""
    worker_image_sha256: str
    native_source_sha256: str
    developer_candidate_sha256: str
    output_ifc_sha256: str | None
    source_mount_unchanged: bool
    docker_prestart_policy_verified: bool
    direct_model_feedback_allowed: bool
    real_LLM_submitted_script: bool
    host_private_candidate_ifc_bytes: bytes | None
    owned_fixture_id: str
    host_private_kernel_probe_checks: dict | None


def terminal_model_visible_receipt() -> dict:
    """A future terminal LLM tool can return this before termination only.

    Must never include execution status, candidate hash, source bytes, task
    grade, error messages or timing metrics; host execution outcome is private.
    """
    return {
        "status": "SEALED_ONE_SHOT_SUBMISSION_RECORDED",
        "execution_feedback_available": False,
        "tool_continuation_allowed": False,
    }


def validate_original_source_and_owned_fixture(
    original_source: Path, original_source_sha256: str, code: bytes,
    image_id: str, wall_seconds: int,
) -> None:
    if (not isinstance(original_source, Path)
        or not original_source.is_file() or original_source.is_symlink()
        or original_source.suffix.lower() != ".ifc"):
        raise SealedWorkerBlocked("Expected non-symlink real pinned public IFC")
    if (not isinstance(original_source_sha256, str)
        or not _ORIGINAL_SHA.fullmatch(original_source_sha256)
        or _sha(original_source.read_bytes()) != original_source_sha256):
        raise SealedWorkerBlocked("Original PUBLIC IFC exact SHA-256 mismatch")
    if not 0 < original_source.stat().st_size <= MAX_PUBLIC_IFC_BYTES:
        raise SealedWorkerBlocked("Source exceeds bounded offline IFC demo budget")
    if (not isinstance(code, bytes) or not 0 < len(code) <= MAX_DEVELOPER_FIXTURE_BYTES
        or b"\x00" in code):
        raise SealedWorkerBlocked("Owned fixture must be a bounded nonempty Python UTF-8 script")
    try:
        code.decode("utf8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SealedWorkerBlocked("Owned fixture is not UTF-8") from exc
    if image_id != PINNED_LOCAL_IMAGE:
        raise SealedWorkerBlocked("Only SHA-pinned local audited old OWN image allowed")
    if wall_seconds not in range(3, 26):
        raise SealedWorkerBlocked("Strict per-trial wall limit 3..25 seconds")


def build_sealed_docker_create_args(
    image_id: str, name: str, input_dir: Path, script_dir: Path
) -> list[str]:
    """Deterministic security policy; no host output bind or secrets."""
    if image_id != PINNED_LOCAL_IMAGE:
        raise SealedWorkerBlocked("Worker image SHA mismatch")
    if not re.fullmatch(r"bmb-v019-sealed-[a-f0-9]{16}", name):
        raise SealedWorkerBlocked("Unexpected container name")
    for folder in (input_dir, script_dir):
        if (not folder.is_absolute() or folder.is_symlink() or not folder.is_dir()
            or any(x in str(folder) for x in (",", "\n", "\r"))):
            raise SealedWorkerBlocked("Invalid original source or code mount folder")
    return [
        "docker", "create", "--pull=never", "--name=" + name,
        "--network=none", "--read-only", "--user=65534:65534",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--pids-limit=1", "--memory=512m", "--memory-swap=512m",
        "--cpus=0.75", "--ipc=none", "--cgroupns=private",
        "--ulimit=nofile=64:64", "--ulimit=fsize=33554432:33554432",
        "--ulimit=core=0:0",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=16m",
        "--tmpfs=/output:rw,nosuid,nodev,noexec,size=64m",
        # No untrusted candidate stdout/stderr stored by Docker engine.
        # Host bounded attach holds it only in memory, never returned to LLM.
        "--log-driver=none",
        "--mount=type=bind,source=" + str(input_dir) + ",target=/input,readonly",
        "--mount=type=bind,source=" + str(script_dir) + ",target=/task,readonly",
        "--env=HOME=/tmp", "--env=OPENBLAS_NUM_THREADS=1",
        "--env=OMP_NUM_THREADS=1", "--env=MKL_NUM_THREADS=1",
        "--env=NUMEXPR_NUM_THREADS=1",
        "--entrypoint=/usr/local/bin/python3", image_id,
        "/opt/ifc_worker/run_candidate.py",
    ]


def run_owned_original_sealed(
    original_source: Path,
    expected_public_source_sha256: str,
    owned_developer_script: bytes,
    *,
    image_id: str = PINNED_LOCAL_IMAGE,
    wall_seconds: int = DEFAULT_WALL_SECONDS,
    expects_ifc_result: bool = True,
    original_public_question: str | None = None,
) -> PrivateSealedOutcome:
    """HOST-only offline developer fixture. No arbitrary model code accepted.

    A public future model runner MUST NOT call this directly to run generated
    code: admission of developer fixtures requires independent trusted
    caller SHA pin and a separate agent/model-budget authorization workflow.
    """
    validate_original_source_and_owned_fixture(
        original_source, expected_public_source_sha256,
        owned_developer_script, image_id, wall_seconds,
    )
    owned_cases = {
        _sha(OWN_SECURITY_TEST_SCRIPT): ("owned-os-denial-probe", False),
        _sha(OWN_LEAK_OUTPUT_SCRIPT): ("owned-output-redaction-probe", True),
        _sha(OWN_INFINITE_LOOP_SCRIPT): ("owned-infinite-timeout-probe", False),
    }
    if original_public_question is not None:
        known = original_public_column15_owned_script(original_public_question)
        owned_cases[_sha(known)] = ("owned-original-public-test15-column-move", True)
    fixture = owned_cases.get(_sha(owned_developer_script))
    if fixture is None or fixture[1] is not expects_ifc_result:
        raise SealedWorkerBlocked("Only exact independent developer-owned fixture admitted; never LLM source")
    fixture_id = fixture[0]
    _verify_local_image(image_id)
    name = "bmb-v019-sealed-" + uuid.uuid4().hex[:16]
    sealed_out: bytes | None = None
    host_kernel_checks: dict | None = None
    with tempfile.TemporaryDirectory(prefix="bmb-v019-original-sealed-") as tmp:
        root = Path(tmp)
        source_dir = root / "input"
        script_dir = root / "task"
        source_dir.mkdir()
        script_dir.mkdir()
        stage_source = source_dir / "input.ifc"
        shutil.copyfile(original_source, stage_source)
        stage_source.chmod(0o444)
        (script_dir / "solution.py").write_bytes(owned_developer_script)
        (script_dir / "solution.py").chmod(0o444)
        before = _sha(stage_source.read_bytes())
        if before != expected_public_source_sha256:
            raise SealedWorkerBlocked("Staged source IFC SHA does not match original")
        container_id: str | None = None
        try:
            created = _run(
                build_sealed_docker_create_args(
                    image_id, name, source_dir, script_dir
                ), timeout=15,
            )
            if created.returncode:
                raise SealedWorkerBlocked("Docker container creation blocked")
            container_id = created.stdout.strip()
            if not re.fullmatch(r"[a-f0-9]{64}", container_id):
                raise SealedWorkerBlocked("Docker returned noncanonical container ID")
            # Historical pre-start validator enforces EXACT HostConfig and
            # exactly /input /task read-only binds, no output host mount.
            _inspect_config(container_id, image_id, with_task=True)
            inspected = _run(["docker", "inspect", container_id], timeout=12)
            if inspected.returncode:
                raise SealedWorkerBlocked("Docker prestart config audit unavailable")
            details = json.loads(inspected.stdout)
            if (len(details) != 1
                or details[0]["HostConfig"]["LogConfig"]["Type"] != "none"):
                raise SealedWorkerBlocked("Untrusted native candidate Docker logs must not persist")
            # This may return no artifact on code failure or timeout.
            # Never forward any Docker output or exception to a model.
            started = _limited_attach(container_id, wall_seconds)
            if started.returncode != 0:
                raise SealedWorkerBlocked("Sealed original native worker failed")
            if expects_ifc_result:
                try:
                    sealed_out = _recover_ifc(started.stdout)
                except DockerIsolationError as exc:
                    raise SealedWorkerBlocked("No valid bounded IFC artifact from worker") from exc
                if not 0 < len(sealed_out) <= OUTPUT_LIMIT_BYTES:
                    raise SealedWorkerBlocked("Sealed candidate IFC exceeded output size")
            else:
                # No output IFC allowed in a negative kernel probe; never
                # retain arbitrary candidate stdout/stderr in evidence.
                if "trusted_small_ifc_b64" in started.stdout:
                    raise SealedWorkerBlocked("Expected no output IFC")
                if fixture_id == "owned-os-denial-probe":
                    messages = []
                    for line in started.stdout.splitlines():
                        if line.startswith("{") and len(line) < 5000:
                            try:
                                messages.append(json.loads(line))
                            except (ValueError, TypeError):
                                continue
                    probes = [m.get("v019_os_probe_results") for m in messages
                              if isinstance(m, dict) and "v019_os_probe_results" in m]
                    expected = {
                        "uid_nonroot", "input_readable", "source_readonly",
                        "own_code_readonly", "secrets_absent", "gt_unmounted",
                        "host_user_hidden", "docker_socket_absent", "network_denied",
                        "spawn_denied", "root_readonly", "seccomp_active",
                        "capabilities_zero", "no_new_privs",
                    }
                    if (len(probes) != 1 or not isinstance(probes[0], dict)
                        or set(probes[0]) != expected
                        or not all(probes[0][key] is True for key in expected)):
                        raise SealedWorkerBlocked("Original source Docker kernel security probes failed")
                    host_kernel_checks = dict(sorted(probes[0].items()))
            if _sha(stage_source.read_bytes()) != before:
                raise SealedWorkerBlocked("Original read-only source mount changed")
            if _sha(original_source.read_bytes()) != before:
                raise SealedWorkerBlocked("Pinned public IFC changed during execution")
        finally:
            # Remove only our own unique, previously allocated name.
            # If cleanup fails, abort evidence; never pass an orphaned
            # sandbox as a green execution to future research gates.
            cleaned = _run(["docker", "rm", "--force", name], timeout=15)
            if cleaned.returncode:
                raise SealedWorkerBlocked("Failed to remove isolated Docker worker")
    return PrivateSealedOutcome(
        worker_image_sha256=image_id,
        native_source_sha256=expected_public_source_sha256,
        developer_candidate_sha256=_sha(owned_developer_script),
        output_ifc_sha256=_sha(sealed_out) if sealed_out is not None else None,
        source_mount_unchanged=True,
        docker_prestart_policy_verified=True,
        direct_model_feedback_allowed=False,
        real_LLM_submitted_script=False,
        host_private_candidate_ifc_bytes=sealed_out,
        owned_fixture_id=fixture_id,
        host_private_kernel_probe_checks=host_kernel_checks,
    )


def original_public_column15_owned_script(public_question: str) -> bytes:
    """Trusted developer-only one-shot fixture, derived from PUBLIC question."""
    from tools.bibimbap_v016_original_column_i0 import _parse_public_instruction
    operation, public_guid = _parse_public_instruction("test_15", public_question)
    if operation != "MOVE_COLUMN_Y_MINUS_3M":
        raise SealedWorkerBlocked("Wrong frozen original public Column task")
    # GUID from the publicly named source target is data, never original
    # hidden scorer targets. No project tools/author GT imported in container.
    return ("""
import ifcopenshell
import ifcopenshell.util.unit
import ifcopenshell.util.placement
import numpy as np
f=ifcopenshell.open('/input/input.ifc')
assert f.schema == 'IFC4X3'
column=f.by_guid(%r)
assert column.is_a('IfcColumn')
placement=column.ObjectPlacement
assert placement.is_a('IfcLocalPlacement')
frame=placement.RelativePlacement
point=frame.Location
assert frame.is_a('IfcAxis2Placement3D') and point.is_a('IfcCartesianPoint')
assert len(f.get_inverse(point)) == 1
assert len(f.get_inverse(frame)) == 1
assert all(x.id()==column.id() for x in f.get_inverse(placement))
if placement.PlacementRelTo is not None:
    parent=np.asarray(ifcopenshell.util.placement.get_local_placement(placement.PlacementRelTo),dtype=float)
    assert np.allclose(parent[:3,:3],np.eye(3),rtol=0,atol=1e-8)
scale=ifcopenshell.util.unit.calculate_unit_scale(f)
assert scale > 0
x,y,z=(float(v) for v in point.Coordinates)
point.Coordinates=(x, y - 3.0/scale, z)
f.write('/output/result.ifc')
""" % (public_guid,)).encode("utf8")


# All these scripts are developer-owned NEGATIVE OS probes.  They are NOT
# arbitrary LLM submissions, and are always executed inside Docker only.
OWN_SECURITY_TEST_SCRIPT = b"""
import os,socket,subprocess,json
from pathlib import Path
def denied(fn):
    try: fn(); return False
    except Exception: return True
facts={
 'uid_nonroot':os.geteuid()==65534,
 'input_readable':Path('/input/input.ifc').read_bytes().startswith(b'ISO-10303-21;'),
 'source_readonly':denied(lambda:Path('/input/input.ifc').write_bytes(b'EVIL')),
 'own_code_readonly':denied(lambda:Path('/task/solution.py').write_bytes(b'EVIL')),
 'secrets_absent':os.getenv('OPENAI_API_KEY') is None and os.getenv('GITHUB_TOKEN') is None,
 'gt_unmounted':not Path('/grader/ground_truth.ifc').exists(),
 'host_user_hidden':not Path('/unmounted_host/private_home_canary').exists(),
 'docker_socket_absent':not Path('/var/run/docker.sock').exists(),
 'network_denied':denied(lambda:socket.create_connection(('1.1.1.1',443),timeout=1)),
 'spawn_denied':denied(lambda:subprocess.run(['/bin/sh','-c','echo no'],check=True,timeout=2)),
 'root_readonly':denied(lambda:Path('/etc/v019-probe').write_text('EVIL')),
}
proc=Path('/proc/self/status').read_text()
facts['seccomp_active']='Seccomp:\t2' in proc
facts['capabilities_zero']='CapEff:\t0000000000000000' in proc
facts['no_new_privs']='NoNewPrivs:\t1' in proc
print(json.dumps({'v019_os_probe_results':facts},sort_keys=True))
"""

OWN_LEAK_OUTPUT_SCRIPT = b"""
from pathlib import Path
import ifcopenshell
# This intentionally tries to put information into stdout. The HOST must
# never give any of these output bytes to the LLM after sealed execution.
print('V019_FAKE_PRIVATE_CANARY_AND_IFC_DATA_LEAK')
print(Path('/input/input.ifc').read_text(encoding='utf8')[:120])
f=ifcopenshell.open('/input/input.ifc')
f.write('/output/result.ifc')
"""

OWN_INFINITE_LOOP_SCRIPT = b"while True:\n    pass\n"
