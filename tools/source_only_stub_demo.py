#!/usr/bin/env python3
"""Non-billing demonstration: fake file-text editor -> trusted IFC4X3 wall edit.

The fake "agent" edits XML source text only; it is not a real LLM. The trusted
compiler is invoked separately, OUTSIDE the fake agent's file-tool interface.
No network, OpenAI API usage or hidden official dataset is involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from src.direct_markup.agent_runner import (
    SourceOnlySettings,SourceFileEdit,stage_source_only_workspace,
    TrustedCompilationController,
)

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-ifc",type=Path,
        default=Path("tests/fixtures/synthetic/input.ifc"))
    parser.add_argument("--output-ifc",type=Path,required=True,
        help="A NEW output IFC path, not the original input IFC")
    args=parser.parse_args()
    payload={
        "task_id":"OWN-G2-SOURCE-ONLY-SYNTHETIC-001",
        "instruction":"Change the first North Wall height from 3 m to 3.3 m by editing building.xml only",
        "input_file":"input.ifc",
    }
    with tempfile.TemporaryDirectory(prefix="bim-markup-source-only-") as tmp:
        session=stage_source_only_workspace(
            args.input_ifc,Path(tmp)/"workspace",payload,SourceOnlySettings()
        )
        context=session.agent_visible_context()
        old='height="3" thickness="0.2"'
        if context.xml_text.count(old)!=1:
            print(json.dumps({"status":"BLOCKED_UNEXPECTED_FIXTURE","model_calls":0}))
            return 2
        proposal=SourceFileEdit(
            "building.xml",context.xml_byte_sha256,
            "surgical_patch",old,'height="3.3" thickness="0.2"'
        )
        response=session.attempt(proposal)
        if response["status"]!="ACCEPTED_VALID_XML":
            print(json.dumps({"status":"BLOCKED_INVALID_SOURCE","model_calls":0}))
            return 2
        output=TrustedCompilationController.compile_accepted(
            session,args.input_ifc,args.output_ifc
        )
        trace=session.trace()
        print(json.dumps({
            "status":"OFFLINE_STUB_COMPILED_IFC",
            "model_calls":0,
            "trusted_compiler_visible_to_agent":False,
            "input_ifc_sha256":output.source_sha256,
            "output_ifc_sha256":output.result_sha256,
            "changed_native_operations":[item.operation for item in output.operations],
            "source_file_edit_count":trace["attempt_count"],
            "file_tool_trace_operations":[x["operation"] for x in trace["events"]],
            "actual_model_tokens":None,
            "OS_sandbox_implemented":False,
            "official_benchmark_scored":False,
        },indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
