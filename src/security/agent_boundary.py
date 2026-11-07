"""Fail-closed file/action policy and sanitized model task input.

Not an OS security boundary. Future untrusted Python runs must execute under
a separate user/container/VM with actual network/process/filesystem isolation.
This module is only the G0 planning, validation and unit-test contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import json
import json
import jsonschema

ALLOWED_FILES = {"building.xml", "input.ifc", "language_spec.md"}
ALLOWED_ACTIONS = {"read", "edit_xml"}
NEVER_MODEL_FIELDS = {
    "target","ground_truth_ifc","evaluation","expected","expected_output",
    "gt_path","answer","source_dataset_path","reference_model","secrets"
}
SENSITIVE = re.compile(r"(sk-[A-Za-z0-9_-]{10,}|OPENAI_API_KEY\s*=|/grader/|\.\./|^/)",re.IGNORECASE)

class SecurityBoundaryError(ValueError):
    pass

def validate_agent_payload(payload: dict, *, schema_path: Path | None = None) -> dict:
    if not isinstance(payload,dict):
        raise SecurityBoundaryError("agent payload must be a dictionary")
    if NEVER_MODEL_FIELDS.intersection(payload):
        raise SecurityBoundaryError("grader-only fields supplied to agent")
    keys={"task_id","instruction","input_file"}
    if set(payload) != keys or payload["input_file"] != "input.ifc":
        raise SecurityBoundaryError("unexpected agent fields or input path")
    if not all(isinstance(payload[k],str) and payload[k] for k in keys):
        raise SecurityBoundaryError("invalid or empty task payload")
    if SENSITIVE.search(payload["instruction"]) or SENSITIVE.search(payload["task_id"]):
        raise SecurityBoundaryError("secret/path-looking string in agent payload")
    if schema_path is not None:
        jsonschema.validate(payload,json.loads(schema_path.read_text(encoding="utf-8")))
    return dict(payload)

@dataclass(frozen=True)
class FileAccessPolicy:
    workspace: Path

    def check(self, action: str, file: str) -> Path:
        if action not in ALLOWED_ACTIONS or file not in ALLOWED_FILES:
            raise SecurityBoundaryError("disallowed agent action or filename")
        if action=="edit_xml" and file != "building.xml":
            raise SecurityBoundaryError("agent may edit only declarative XML")
        root=self.workspace.resolve(strict=True)
        candidate=root / file
        if candidate.is_symlink() or not candidate.resolve(strict=False).is_relative_to(root):
            raise SecurityBoundaryError("symlink or escaped path")
        if not candidate.exists():
            raise SecurityBoundaryError("agent file not staged")
        return candidate

    def deny_network(self, url: str):
        raise SecurityBoundaryError("network access is forbidden inside agent task runner")

    def deny_shell(self, command: str):
        raise SecurityBoundaryError("shell/process execution is forbidden in direct XML agent")

@dataclass(frozen=True)
class LicenseRecord:
    source: str
    source_digest_sha256: str
    asset_rights: str
    rights_checked: bool
    redistribution_permitted: bool
    consent_documented: bool

    def authorize_redistribution(self) -> None:
        if not (self.rights_checked and self.redistribution_permitted and self.consent_documented):
            raise SecurityBoundaryError("rights for source IFC asset not positively verified")
        if not re.fullmatch(r"[0-9a-f]{64}",self.source_digest_sha256):
            raise SecurityBoundaryError("source IFC SHA-256 missing")
        if not self.asset_rights or self.asset_rights.upper() in {"UNKNOWN","UNVERIFIED","NONE"}:
            raise SecurityBoundaryError("source license unknown or unverified")

MAX_XML_BYTES = 2 * 1024 * 1024
MAX_XML_NESTING = 96

def check_xml_bytes(blob: bytes) -> None:
    """Conservative pre-parser size/DTD/XXE guard, NOT a complete XML parser."""
    if type(blob) is not bytes or not blob or len(blob)>MAX_XML_BYTES:
        raise SecurityBoundaryError("XML payload invalid or exceeds byte limit")
    upper=blob.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper or b"<![" in upper:
        raise SecurityBoundaryError("DTD, entity and conditional XML sections forbidden")
    # The runtime XML parser (#10) must independently enforce actual depth,
    # namespaces, attributes and no external resolver. Never rely on text alone.
