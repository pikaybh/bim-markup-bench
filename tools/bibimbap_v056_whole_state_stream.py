"""v0.56 EXPERIMENTAL full-final-state XML STREAM transport (D-state only).

The stream carries the WHOLE final declarative XML snapshot byte-for-byte.
It is NOT an operation script, XML edit plan, patch or differential command.
No prefix is compiled or committed. On the final chunk, call the already
frozen v0.55 full-state compiler, original IFC scope oracle and real
schema-delta admission. No author evaluator, GT or provider is imported.

IMPORTANT: this changes the D-arm TOOL schema and feedback. It is NOT the
same causal interface as the v0.55 one-shot D arm or an approved equal-budget
model benchmark. The official paid-pair experiment must remain BLOCKED.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from src.runtime.experimental_v50_original_declarative_state import (
    MAX_CALLS,MAX_XML_BYTES,
)
from tools.bibimbap_matched25_tools import file_hash
from tools.bibimbap_v055_transactional_primary_DI_sessions import (
    SchemaGuardedDirectStateSession055,
)

MAX_CHUNK_UTF8_BYTES=8192
MAX_CHUNKS_PER_COMPLETE_STATE=24


class WholeStateStream056Error(ValueError):
    pass


def split_whole_final_state_utf8_v056(xml_text:str,*,max_chunk_bytes:int=MAX_CHUNK_UTF8_BYTES)->list[str]:
    """Only a developer-side transport splitter; no edits or commands inferred."""
    if (not isinstance(xml_text,str) or not 0<max_chunk_bytes<=MAX_CHUNK_UTF8_BYTES):
        raise WholeStateStream056Error("Invalid complete state or chunk bound")
    try:
        data=xml_text.encode("utf8","strict")
    except UnicodeEncodeError as exc:
        raise WholeStateStream056Error("State text has invalid UTF-8") from exc
    if not 0<len(data)<=MAX_XML_BYTES:
        raise WholeStateStream056Error("Whole final XML outside immutable compiler bound")
    chunks=[]
    while data:
        # Use maximal UTF-8-valid prefix, without altering even one byte.
        stop=min(len(data),max_chunk_bytes)
        while stop:
            try:
                piece=data[:stop].decode("utf8","strict")
                break
            except UnicodeDecodeError:
                stop-=1
        if not stop:
            raise WholeStateStream056Error("Unable to split UTF-8 without loss")
        chunks.append(piece)
        data=data[stop:]
    if len(chunks)>MAX_CHUNKS_PER_COMPLETE_STATE:
        raise WholeStateStream056Error("Whole source state exceeds 25-call trial budget")
    if "".join(chunks)!=xml_text:
        raise WholeStateStream056Error("Changed final state during segmentation")
    return chunks


class WholeStateStreamDirectSession056(SchemaGuardedDirectStateSession055):
    """A WHOLE state streaming transport, never a typed Bim API command."""

    def __init__(self,original_ifc:Path,folder:Path):
        super().__init__(original_ifc,folder)
        self._chunks:list[str]=[]
        self._pending_bytes=0

    @property
    def tools(self)->list[dict]:
        original=super().tools
        return [
            original[0],
            {
                "type":"function",
                "name":"submit_complete_building_xml_chunk",
                "description":(
                    "Transmit the COMPLETE final declarative building-state "
                    "XML snapshot as consecutive UTF-8 chunks. Do not send "
                    "edits, diffs, patches, commands or Python. Each chunk "
                    "has at most 8192 UTF-8 bytes; sequence starts at zero "
                    "and increments by one. Set final=true ONLY on the last "
                    "chunk. The host concatenates every character exactly "
                    "and compiles/validates/commits ONLY the fully assembled "
                    "final state. All prior source evidence is immutable; "
                    "rejected streams never overwrite last valid XML/IFC. "
                    "Streaming changes token and tool-call budgets relative "
                    "to one-shot XML and executed Python."
                ),
                "parameters":{
                    "type":"object",
                    "properties":{
                        "sequence":{"type":"integer"},
                        "chunk_text":{"type":"string"},
                        "final":{"type":"boolean"},
                    },
                    "required":["sequence","chunk_text","final"],
                    "additionalProperties":False,
                },
                "strict":True,
            },
        ]

    def _discard(self)->None:
        self._chunks.clear()
        self._pending_bytes=0

    def _reject_chunk(self,kind:str)->dict:
        self._discard()
        return {
            "status":"error",
            "error_type":kind,
            "native_ifc_committed":False,
            "last_valid_xml_preserved":True,
            "last_valid_ifc_preserved":True,
            "pending_complete_state_bytes":0,
        }

    def call(self,name:str,arguments:dict)->dict:
        if name=="submit_building_xml":
            # Prevent bypass of the streaming-interface fairness measurement.
            if self.calls_used>=MAX_CALLS:
                return {
                    "status":"error",
                    "error_type":"ToolBudgetExhausted",
                    "max_tool_calls":MAX_CALLS,
                    "native_ifc_committed":False,
                }
            self.calls_used+=1
            return self._reject_chunk("OneShotToolUnavailableInStreamArm")
        if name!="submit_complete_building_xml_chunk":
            # This delegates source read (which returns last-COMMITTED XML)
            # and preserves the original 25-call limit.
            return super().call(name,arguments)
        if self.calls_used>=MAX_CALLS:
            return {
                "status":"error",
                "error_type":"ToolBudgetExhausted",
                "max_tool_calls":MAX_CALLS,
                "native_ifc_committed":False,
            }
        if file_hash(self.original_ifc)!=self.source_sha:
            self.calls_used+=1
            return self._reject_chunk("OriginalSourceChanged")
        if (not isinstance(arguments,dict)
            or set(arguments)!={"sequence","chunk_text","final"}
            or type(arguments["sequence"]) is not int
            or type(arguments["final"]) is not bool
            or not isinstance(arguments["chunk_text"],str)):
            self.calls_used+=1
            return self._reject_chunk("InvalidWholeStateChunkInput")
        idx=arguments["sequence"]
        text=arguments["chunk_text"]
        final=arguments["final"]
        try:
            byte_len=len(text.encode("utf8","strict"))
        except UnicodeEncodeError:
            self.calls_used+=1
            return self._reject_chunk("InvalidChunkUTF8")
        if (idx!=len(self._chunks)
            or not 0<byte_len<=MAX_CHUNK_UTF8_BYTES
            or len(self._chunks)>=MAX_CHUNKS_PER_COMPLETE_STATE
            or self._pending_bytes+byte_len>MAX_XML_BYTES
            or (not final and self.calls_used+1>=MAX_CALLS)):
            self.calls_used+=1
            return self._reject_chunk("ChunkOrderLengthOrCallBudgetRejected")
        self._chunks.append(text)
        self._pending_bytes+=byte_len
        if not final:
            self.calls_used+=1
            return {
                "status":"ok",
                "native_ifc_committed":False,
                "complete_final_state_received":False,
                "accepted_sequence":idx,
                "pending_complete_state_bytes":self._pending_bytes,
                "remaining_tool_calls":MAX_CALLS-self.calls_used,
                "original_author_benchmark_score":None,
            }
        # IMPORTANT: this last chunk costs exactly ONE call. Do not add an
        # extra tool call to compile after finalization; this delegates the
        # final call increment to the original v0.55 atomic host transaction.
        whole="".join(self._chunks)
        self._discard()
        completed=SchemaGuardedDirectStateSession055.call(
            self,"submit_building_xml",{"xml_text":whole})
        if completed.get("status")=="ok":
            return {
                **completed,
                "complete_final_state_received":True,
                "stream_payload_sha256":sha256(whole.encode("utf8")).hexdigest(),
                "streaming_transport":"WHOLE_XML_REASSEMBLED_BEFORE_DIFF",
            }
        return {
            **completed,
            "complete_final_state_received":True,
            "streaming_transport":"WHOLE_XML_REJECTED_NO_COMMIT",
        }
