"""Model-facing bounded direct XML STATE editing on four pinned original IFCs.

No native/edit API command surface, Python execution, answer/key/grader or
developer positive controls accessible via the two tools.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.runtime.experimental_v50_original_declarative_state import (
    MAX_CALLS, MAX_XML_BYTES,
    compile_original_declarative_state_v050,
    project_original_declarative_state_v050,
)
from src.runtime.experimental_v45_original_native_mutations import check_source
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v045_independent_native_mutation_oracle import (
    verify_original_native_mutation_v045,
)


class DirectOriginalStateSession050:
    """Separate experimental D-state interface; never treated as I-native parity."""

    def __init__(self, original_ifc: Path, folder: Path) -> None:
        self.original_ifc = Path(original_ifc)
        self.folder = Path(folder)
        if (not self.original_ifc.is_file() or self.original_ifc.is_symlink()
            or self.folder.exists() or self.folder.is_symlink()
            or not self.folder.parent.is_dir()):
            raise ValueError("Fresh isolated output folder and regular original IFC required")
        self.source_sha = file_hash(self.original_ifc)
        self.task_id = check_source(self.original_ifc, self.source_sha)
        self.original_xml = project_original_declarative_state_v050(
            self.original_ifc, source_sha=self.source_sha,
        ).xml
        self.current_xml = self.original_xml
        self.output_ifc: Path | None = None
        self.calls_used = 0
        self.submissions = 0
        self.folder.mkdir(exist_ok=False)

    @property
    def tools(self) -> list[dict]:
        return [
            {
                "type": "function", "name": "read_building_xml",
                "description": (
                    "Read the current full declarative building state XML. The "
                    "OriginalNativeIFCSource section is read-only public source "
                    "evidence; only ManagedElements' existing IfcSlab/IfcColumn "
                    "final state attributes or managed element presence may be "
                    "changed. The XML is an incomplete explicit IFC-backed state "
                    "overlay. No target answer or evaluator is provided."
                ),
                "parameters": {"type": "object", "properties": {},
                               "additionalProperties": False},
                "strict": True,
            },
            {
                "type": "function", "name": "submit_building_xml",
                "description": (
                    "Submit the COMPLETE modified declarative building state XML. "
                    "Change a managed final state, not a command or Python. A "
                    "trusted external compiler infers the semantic before/after "
                    "change and independently verifies a source-native IFC result. "
                    "Unsupported/invalid states fail without replacing last valid "
                    "XML/IFC. No author benchmark score is returned."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {"xml_text": {"type": "string"}},
                    "required": ["xml_text"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        ]

    def call(self, name: str, arguments: dict) -> dict:
        if self.calls_used >= MAX_CALLS:
            return {"status": "error", "error_type": "ToolBudgetExhausted",
                    "max_tool_calls": MAX_CALLS, "native_ifc_committed": False}
        self.calls_used += 1
        if file_hash(self.original_ifc) != self.source_sha:
            return {"status": "error", "error_type": "OriginalSourceChanged",
                    "native_ifc_committed": False, "last_valid_xml_preserved": True}
        if name == "read_building_xml":
            if arguments != {}:
                return {"status": "error", "error_type": "InvalidReadArguments"}
            return {
                "status": "ok",
                "xml": self.current_xml.decode("utf8"),
                "current_xml_sha256": sha256(self.current_xml).hexdigest(),
                "native_candidate_available": self.output_ifc is not None,
            }
        if name != "submit_building_xml":
            return {"status": "error", "error_type": "UnknownDirectStateTool"}
        if (not isinstance(arguments, dict) or set(arguments) != {"xml_text"}
            or not isinstance(arguments["xml_text"], str)):
            return {"status": "error", "error_type": "InvalidWriteArguments",
                    "last_valid_xml_preserved": True}
        payload = arguments["xml_text"].encode("utf8")
        if not 0 < len(payload) <= MAX_XML_BYTES:
            return {"status": "error", "error_type": "InvalidXMLSize",
                    "last_valid_xml_preserved": True}
        self.submissions += 1
        attempt = self.folder / f"attempt_{self.submissions:03d}"
        attempt.mkdir(exist_ok=False)
        (attempt / "submitted_state.xml").write_bytes(payload)
        candidate = attempt / "candidate_original_native_mm.ifc"
        try:
            diff = compile_original_declarative_state_v050(
                self.original_ifc, payload, candidate, source_sha=self.source_sha,
            )
            # This original source/native physical oracle is independent of both
            # the v0.50 state diff and the original v0.45 writer itself.
            oracle = verify_original_native_mutation_v045(
                self.original_ifc, candidate,
                submitted_xml=diff.internal_native_writer_xml,
                source_sha=self.source_sha,
                task_id=self.task_id,
            )
            if file_hash(self.original_ifc) != self.source_sha:
                raise ValueError("Immutable original IFC changed during compile")
            if oracle["status"] != "V045_INDEPENDENT_ORIGINAL_IFC_NATIVE_MUTATION_ORACLE_PASS":
                # Inspect actual oracle status in tests if version contracts change.
                raise ValueError("Independent native physical oracle did not pass")
            # Commit only after independent real IFC geometry/relationship pass.
            self.output_ifc = candidate
            self.current_xml = payload
            return {
                "status": "ok",
                "native_ifc_committed": True,
                "native_ifc_sha256": file_hash(candidate),
                "current_xml_sha256": sha256(payload).hexdigest(),
                "independent_original_native_ifc_physical_oracle": "PASS",
                "original_author_benchmark_score": None,
                "last_valid_state_committed": True,
            }
        except Exception as exc:
            if candidate.is_file():
                candidate.unlink()
            return {
                "status": "error",
                "error_type": type(exc).__name__,
                "native_ifc_committed": False,
                "last_valid_xml_preserved": True,
                "current_xml_sha256": sha256(self.current_xml).hexdigest(),
                "original_source_unchanged":
                    file_hash(self.original_ifc) == self.source_sha,
            }
