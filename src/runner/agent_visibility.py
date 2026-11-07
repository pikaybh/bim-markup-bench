"""Checked, minimal model-visible bundle built without grader/GT context."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

from src.data.bim_edit import agent_view
from src.direct_markup.agent_runner import (
    SourceOnlySettings,stage_source_only_workspace,
)
from src.security.agent_boundary import validate_agent_payload,SecurityBoundaryError

_SECRET=re.compile(r'(sk-[A-Za-z0-9_-]{10,}|OPENAI_API_KEY|/grader/|/private/gt/)',
                   re.IGNORECASE)

class VisibilityError(ValueError):
    pass


def validate_minimal_agent_bundle(bundle:dict)->dict:
    required={"task_id","instruction","model_xml_text","toy_language_spec",
              "source_ifc_sha256","source_filename"}
    if set(bundle)!=required:
        raise VisibilityError("Agent-visible bundle has unapproved keys")
    if bundle["source_filename"]!="input.ifc":
        raise VisibilityError("Agent source path must be synthetic basename input.ifc")
    for key in required:
        if not isinstance(bundle[key],str) or not bundle[key]:
            raise VisibilityError("Agent-visible field must be present and textual")
    if not re.fullmatch(r"[0-9a-f]{64}",bundle["source_ifc_sha256"]):
        raise VisibilityError("Invalid source IFC content SHA-256")
    for key in ("task_id","instruction","model_xml_text","toy_language_spec"):
        if _SECRET.search(bundle[key]):
            raise VisibilityError("A possible hidden GT/secret token crossed model boundary")
    if any(x in bundle["instruction"] for x in ("../","/Users/","/etc/")):
        raise VisibilityError("Untrusted task refers to host-absolute paths")
    return dict(bundle)


def neutral_model_bundle(source_ifc:Path,task_payload:dict)->dict:
    """Trusted offline snapshot. No raw public task GT row is accepted."""
    view=validate_agent_payload(task_payload)
    from src.runtime.ifc_projection import project_ifc
    from src.direct_markup.agent_runner import LANGUAGE_SPEC
    projected=project_ifc(source_ifc)
    raw={
        "task_id":view["task_id"],"instruction":view["instruction"],
        "model_xml_text":projected.xml.decode("utf-8"),
        "toy_language_spec":LANGUAGE_SPEC.read_text(encoding="utf-8"),
        "source_ifc_sha256":projected.source.source_sha256,
        "source_filename":"input.ifc",
    }
    return validate_minimal_agent_bundle(raw)
