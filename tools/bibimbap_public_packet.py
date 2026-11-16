"""Prepare ONE original BIBIMBAP public-task XML-only context, without grader access.

This entrypoint deliberately does not import author test modules, read private
targets or permit execution of an LLM/model-generated code. It emits only
a hash/provenance summary; the public model-facing packet is ephemeral.
The adapter is an IFC-backed *partial projection*, not native BIXML.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit

from src.runtime.ifc_projection import project_ifc
from src.security.agent_boundary import validate_agent_payload, SecurityBoundaryError

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_GRAMMAR = ROOT / "spec" / "toy_markup_v0.md"
DATA_COMMIT = "f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
CSV_SHA256 = "21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b"
PILOT_TASK_ID = "test_05"
PILOT_PUBLIC_ID = "BIBI-XML-PRECHECK-0001"
PILOT_IFC = "basic_tasks.ifc"
PILOT_IFC_SHA256 = "9ef1235e49d5b0359c1d44fd95a7afad7755149362109ca8b875d0427dc487ca"
MAX_PUBLIC_PROMPT_CHARS = 12000
MAX_ORIGINAL_SOURCE_BYTES = 64 * 1024 * 1024


class PublicPacketBlocked(ValueError):
    pass


def sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def public_task_input(*, task_id: str, instruction: str, input_file: str = "input.ifc",
                      **unexpected: object) -> dict[str, str]:
    """No arbitrary dataset/evaluator fields may cross the model-facing seam."""
    payload = {"task_id": task_id, "instruction": instruction, "input_file": input_file}
    if unexpected:
        payload.update(unexpected)
    try:
        verified = validate_agent_payload(payload)
    except SecurityBoundaryError as exc:
        raise PublicPacketBlocked("Rejected nonpublic/unsafe model-facing field") from exc
    if len(verified["instruction"]) > MAX_PUBLIC_PROMPT_CHARS:
        raise PublicPacketBlocked("Public question exceeds frozen pilot bound")
    return verified


def read_public_pilot(dataset: Path) -> tuple[dict, Path]:
    dataset = dataset.resolve(strict=True)
    if not (dataset / ".git").exists():
        raise PublicPacketBlocked("Expected pinned Git dataset checkout")
    try:
        head = subprocess.run(
            ["git", "-C", str(dataset), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
        modified = subprocess.run(
            ["git", "-C", str(dataset), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise PublicPacketBlocked("Dataset Git provenance unavailable") from exc
    if head != DATA_COMMIT or modified:
        raise PublicPacketBlocked("Dataset commit or cleanliness mismatch")
    csv_path = dataset / "prompts" / "all_questions.csv"
    if csv_path.is_symlink() or not csv_path.is_file() or sha(csv_path.read_bytes()) != CSV_SHA256:
        raise PublicPacketBlocked("Original public question CSV digest mismatch")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        entries = list(csv.DictReader(f))
    if len(entries) != 100:
        raise PublicPacketBlocked("Public task population changed")
    counts = Counter(x.get("CRUD", "").lower().strip() for x in entries)
    if counts != {"retrieve": 55, "create": 15, "update": 15, "delete": 15}:
        raise PublicPacketBlocked("Public CRUD distribution changed")
    matches = [x for x in entries if x.get("test") == PILOT_TASK_ID]
    if len(matches) != 1 or matches[0].get("CRUD", "").lower().strip() != "create":
        raise PublicPacketBlocked("Pilot public task identity changed")
    entry = matches[0]
    if entry.get("ifc-file") != PILOT_IFC:
        raise PublicPacketBlocked("Original pilot source changed")
    # NEVER read or forward original CSV's 'structured-output' or any other
    # column. The caller is given an explicit allowlist only.
    payload = public_task_input(task_id=PILOT_PUBLIC_ID,
                                instruction=entry.get("question", "").strip())
    inp = dataset / "ifc" / PILOT_IFC
    if inp.is_symlink() or not inp.is_file() or not (32 <= inp.stat().st_size <= MAX_ORIGINAL_SOURCE_BYTES):
        raise PublicPacketBlocked("Original IFC input invalid/too large")
    if sha(inp.read_bytes()) != PILOT_IFC_SHA256:
        raise PublicPacketBlocked("Original input IFC digest changed")
    return payload, inp


def make_public_packet(dataset: Path) -> tuple[dict, dict]:
    """Only explicit public question, XML projection and public language spec."""
    public, inp = read_public_pilot(dataset)
    if PUBLIC_GRAMMAR.is_symlink() or not PUBLIC_GRAMMAR.is_file():
        raise PublicPacketBlocked("Public experimental XML grammar missing")
    with TemporaryDirectory(prefix="bibi-public-pilot-") as td:
        model = ifcopenshell.open(str(inp))
        if model.schema != "IFC4X3":
            raise PublicPacketBlocked("IFC schema not supported")
        original_scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        if abs(original_scale - 0.001) > 1e-12:
            raise PublicPacketBlocked("Original pilot IFC millimetre units unexpectedly changed")
        normalized = ifcopenshell.util.unit.convert_file_length_units(model, "METER")
        normalized_file = Path(td) / "normalized-source.ifc"
        normalized.write(str(normalized_file))
        projection = project_ifc(normalized_file, strict_on_opaque=False)
        normalized_sha = sha(normalized_file.read_bytes())
        xml = projection.xml.decode("utf-8")
    # The LLM can write only an XML document state. No Python tools/commands.
    packet = {
        "instructions": (
            "Edit the provided declarative building.xml document state to "
            "perform the PUBLIC TASK. Return only the COMPLETE updated XML. "
            "Keep every unrelated supported element unchanged. "
            "Do not write Python, tool calls, or XML operation commands. "
            "The separate trusted runtime will compile the final XML later."
        ),
        "input": (
            "PUBLIC TASK:\n" + public["instruction"] +
            "\n\nPUBLIC SOURCE PROJECTION (building.xml):\n" + xml +
            "\n\nPUBLIC EXPERIMENTAL XML GRAMMAR:\n" +
            PUBLIC_GRAMMAR.read_text(encoding="utf-8") +
            "\n\nReturn only the complete edited building.xml."
        ),
    }
    if any(x in packet for x in ("target", "evaluation", "grader", "ground_truth_ifc")):
        raise PublicPacketBlocked("Unexpected private packet schema")
    if len(packet["instructions"].encode("utf-8")) + len(packet["input"].encode("utf-8")) > 120000:
        raise PublicPacketBlocked("Prompt exceeds fixed byte budget")
    summary = {
        "status": "PUBLIC_PACKET_PREPARED_OFFLINE_ONLY",
        "public_trial_id": PILOT_PUBLIC_ID,
        "dataset_commit_sha": DATA_COMMIT,
        "public_csv_sha256": CSV_SHA256,
        "original_ifc_sha256": PILOT_IFC_SHA256,
        "normalized_input_ifc_sha256": normalized_sha,
        "public_question_sha256": sha(public["instruction"].encode("utf-8")),
        "language_spec_sha256": sha(PUBLIC_GRAMMAR.read_bytes()),
        "public_xml_sha256": sha(xml.encode("utf-8")),
        "model_packet_sha256": sha(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode("utf-8")),
        "packet_keys": sorted(packet),
        "model_visible_original_gt": False,
        "model_visible_author_scorer": False,
        "model_visible_api_tools": False,
        "llm_calls": 0,
        "model_tokens": None,
        "paid_spend_usd": 0,
        "source_is_partial_xml_overlay": True,
        "note": "Only a public prompt plus a projected XML state; does not imply benchmark scoring or launch permission.",
    }
    return packet, summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output-json", type=Path)
    args = p.parse_args()
    try:
        _packet, report = make_public_packet(args.dataset)
    except (PublicPacketBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED_PUBLIC_CONTEXT", "reason_type": type(exc).__name__}))
        return 2
    if args.output_json:
        path = args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            p.error("Refuse overwrite or missing destination parent")
        with path.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
