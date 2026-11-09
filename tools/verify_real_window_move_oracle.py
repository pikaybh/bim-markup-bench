"""Trusted, source-only D0 XML / I0 Python oracle for ONE frozen real input.

Never reads GT, publishes candidate IFC, invokes a model, or scores a task.
Manual deterministic source mutation is NOT evidence of LLM comprehension.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np
from lxml import etree

from src.data.bim_edit import read_tasks,repo_asset_path,verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.runtime.compiler import compile_declarative_xml
from src.runtime.ifc_projection import project_ifc
from src.runtime.topology_ops import native_topology_inventory
from tests.oracles.python.independent_ifc_oracle import manual_ifc_reference
from tests.oracles.python.independent_ifc_checker import parity_report

ROOT=Path(__file__).resolve().parents[1]
FROZEN_TASK="WIN-UPD-DIR-A-002"


def verified_real_source_oracle()->dict:
    records={row["task_id"]:row for row in read_tasks(ROOT/"data/tasks.jsonl")}
    task=records[FROZEN_TASK]
    remote=json.loads((ROOT/"data/bim_edit_remote_tree.json").read_text(encoding="utf-8"))
    by_path={row["path"]:row for row in remote if row.get("type")=="file"}
    name=repo_asset_path(task["input_ifc"])
    source=_files_in_root(ROOT/"data/ifc",name)
    verify_local_asset_bytes(source,by_path[name])
    original=hashlib.sha256(source.read_bytes()).hexdigest()

    f=ifcopenshell.open(str(source))
    window=f.by_guid(task["target"]["guids"][0])
    if not window.is_a("IfcWindow") or len(window.FillsVoids)!=1:
        raise ValueError("Frozen native Window target not uniquely hosted")
    opening=window.FillsVoids[0].RelatingOpeningElement
    host=opening.VoidsElements[0].RelatingBuildingElement
    host_frame=ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)
    expected_global=np.array((0.,1.,0.),dtype=float)
    if not np.allclose(host_frame[:3,0],expected_global,atol=1e-6):
        raise ValueError("Frozen 1m world-Y task is not 1m in native host local X")

    original_placement=np.asarray(ifcopenshell.util.placement.get_local_placement(
        window.ObjectPlacement)[:3,3],dtype=float)
    prior=native_topology_inventory(f)
    xml=etree.fromstring(project_ifc(source).xml)
    match=[node for node in xml.iter()
           if isinstance(node.tag,str) and node.get("ifcGuid")==opening.GlobalId]
    if len(match)!=1:
        raise ValueError("Frozen native Opening not uniquely projected")
    offset=Decimal(match[0].get("offset"))
    match[0].set("offset",str(offset+Decimal("1")))
    edited=etree.tostring(xml,encoding="utf-8",xml_declaration=True)

    with TemporaryDirectory(prefix="g1-trusted-real-task-oracle-") as tmp:
        work=Path(tmp)
        (work/"D0").mkdir()
        (work/"I0").mkdir()
        d0=work/"D0"/"candidate.ifc"
        i0=work/"I0"/"candidate.ifc"
        compiled=compile_declarative_xml(source,edited,d0)
        manual_ifc_reference(source,i0,"MOVE_OPENING",
                             target_guid=opening.GlobalId,delta_x=1.)
        if [action.operation for action in compiled.operations]!=["MOVE_OPENING_WITH_FILLING"]:
            raise ValueError("Unrecognized native operation in source-only oracle")
        model=ifcopenshell.open(str(d0))
        final_placement=np.asarray(ifcopenshell.util.placement.get_local_placement(
            model.by_guid(window.GlobalId).ObjectPlacement)[:3,3],dtype=float)
        delta=final_placement-original_placement
        if not np.allclose(delta,expected_global,atol=1e-6):
            raise ValueError("Native Window world translation is wrong")
        if native_topology_inventory(model)!=prior:
            raise ValueError("Native source relation inventory changed unexpectedly")
        if compiled.unexpected_root_changes:
            raise ValueError("Unexpected native IFC root mutations")
        parity=parity_report(d0,i0)
        if not parity["parity"]:
            raise ValueError("Independent D0/I0 IFC observation mismatch")
        hashes=(hashlib.sha256(d0.read_bytes()).hexdigest(),
                hashlib.sha256(i0.read_bytes()).hexdigest())

    if hashlib.sha256(source.read_bytes()).hexdigest()!=original:
        raise ValueError("Frozen public source IFC mutated")
    return {
        "status":"PASS_ONE_TRUSTED_MANUAL_REAL_SOURCE_ORACLE_NOT_AN_LLM_EXPERIMENT",
        "task_id":FROZEN_TASK,
        "original_input_sha256":original,
        "declarative_candidate_sha256":hashes[0],
        "imperative_candidate_sha256":hashes[1],
        "candidate_saved_to_repository":False,
        "source_bytes_unchanged":True,
        "world_translation_m":[float(round(value,6)) for value in delta],
        "native_topology_inventory_preserved":True,
        "native_root_changes_unexpected_count":0,
        "paired_independent_ifc_observation_parity":True,
        "shared_pinned_input":True,
        "trusted_manual_target_selection":True,
        "model_interpreted_instruction":False,
        "ground_truth_ifc_opened":False,
        "official_evaluator_executed":False,
        "official_tasks_scored":0,
        "paid_model_calls":0,
        "fixed_36_sample_unchanged":True,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json",type=Path)
    args=parser.parse_args()
    report=verified_real_source_oracle()
    if args.output_json:
        path=args.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Refuse overwrite/symlink or missing output parent")
        with path.open("x",encoding="utf-8",newline="\n") as file:
            file.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
