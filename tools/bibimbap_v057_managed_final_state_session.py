"""v0.57 explicit experimental D_MANAGED_FINAL_STATE original IFC host session.

The initial model read is EXACTLY the v0.55 full XML read (as in I-native).
A different tool accepts a COMPLETE roster of compact final object states
and explicit present booleans, not a patch/edit command. Host restores the
immutable original subtree and calls the unchanged v0.55 real IFC commit
validators. This variant is NOT equivalent to previous D_COMPLETE_XML and
NOT authorized as a paid causal benchmark arm.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.runtime.experimental_v50_original_declarative_state import MAX_CALLS
from src.runtime.experimental_v57_compact_managed_state import (
    MAX_MANAGED_STATE_UTF8_BYTES,
    ManagedFinalState057Error,
    restore_complete_declarative_state_v057,
)
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
)


class ManagedFinalStateDirectSession057(SchemaGuardedDirectStateSession055):
    """Entire managed-state final-value declaration, anchored to source IFC."""

    @property
    def tools(self)->list[dict]:
        baseline=super().tools
        return [
            baseline[0],
            {
                "type":"function",
                "name":"submit_managed_final_state",
                "description":(
                    "Submit a COMPLETE declarative ManagedFinalState version "
                    "0.57 XML with sourceOriginalIFCSha256 and "
                    "sourceBuildingStateSha256 anchors. Include EVERY "
                    "original managed Slab/Column GUID in original order, "
                    "with all final numeric values and present=true/false "
                    "for each. This represents final object states, NOT "
                    "an edit command, patch, Python code, or an action list. "
                    "Original source IFC evidence is immutable and never "
                    "authored into this compact output. The trusted host "
                    "reconstructs the original full state and independently "
                    "validates physical IFC and schema before committing. "
                    "This is an experimental DIFFERENT D representation."
                ),
                "parameters":{
                    "type":"object",
                    "properties":{
                        "xml_text":{"type":"string"},
                    },
                    "required":["xml_text"],
                    "additionalProperties":False,
                },
                "strict":True,
            },
        ]

    def call(self,name:str,arguments:dict)->dict:
        if name not in ("submit_managed_final_state","submit_building_xml"):
            return super().call(name,arguments)
        if self.calls_used>=MAX_CALLS:
            return {
                "status":"error","error_type":"ToolBudgetExhausted",
                "max_tool_calls":MAX_CALLS,"native_ifc_committed":False,
            }
        if name=="submit_building_xml":
            self.calls_used+=1
            return self._rejected("OriginalWholeXmlToolNotInCompactArm")
        if file_hash(self.original_ifc)!=self.source_sha:
            self.calls_used+=1
            return self._rejected("OriginalSourceChanged")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"xml_text"}
            or not isinstance(arguments["xml_text"],str)):
            self.calls_used+=1
            return self._rejected("InvalidCompleteManagedStateArguments")
        try:
            compact=arguments["xml_text"].encode("utf8","strict")
            if not 0<len(compact)<=MAX_MANAGED_STATE_UTF8_BYTES:
                raise ManagedFinalState057Error("Compact size bound")
            # The original document's immutable source subtree and original
            # managed roster are restored inside HOST only, not sent by model.
            full=restore_complete_declarative_state_v057(
                self.original_ifc,compact,source_sha=self.source_sha)
        except Exception:
            self.calls_used+=1
            return self._rejected("InvalidCompleteManagedFinalState")
        # A byte-identical complete final state following a successful commit
        # is a semantic replay, not a new state change. Fail closed while
        # preserving every byte of the last accepted native IFC and XML.
        if self.output_ifc is not None and full==self.current_xml:
            self.calls_used+=1
            return self._rejected("UnchangedManagedFinalStateReplayRejected")
        # EXACTLY ONE call is consumed by the existing v0.55 atomic compiler.
        # It also runs original IFC native scope + IFC4X3 schema delta guards.
        answer=SchemaGuardedDirectStateSession055.call(
            self,"submit_building_xml",{"xml_text":full.decode("utf8")})
        if answer.get("status")=="ok":
            return {
                **answer,
                "representation":"D_MANAGED_FINAL_STATE",
                "original_model_read_unchanged":True,
                "managed_final_state_sha256":sha256(compact).hexdigest(),
                "source_full_state_reconstructed_inside_trusted_host":True,
                "actual_paper_official_score":None,
            }
        return {
            **answer,
            "representation":"D_MANAGED_FINAL_STATE",
            "source_full_state_reconstructed_inside_trusted_host":True,
        }

    def _rejected(self,kind:str)->dict:
        return {
            "status":"error",
            "error_type":kind,
            "native_ifc_committed":False,
            "last_valid_xml_preserved":True,
            "last_valid_ifc_preserved":True,
            "current_xml_sha256":sha256(self.current_xml).hexdigest(),
        }
