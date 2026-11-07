"""BIM-Edit 324-task capacity ledger; NOT measured model success.

Task metadata and G1 static rules are only grader/planner side. Nothing here
contains task prompts, target GlobalIds, hidden IFC GT paths, or scores.
"""
from __future__ import annotations

import csv
from itertools import product
from pathlib import Path

from src.data.bim_edit import read_tasks
from src.evaluation.g1_coverage import (
    generate_coverage_ledger,STATIC_UNSUPPORTED,CONDITIONAL,
)

CLASSES=("IfcWall","IfcSlab","IfcSpace","IfcDoor","IfcWindow","IfcColumn")
OPERATIONS=("create","update","delete")
CATEGORIES=("direct","spatial","topological")
SCENES=("scene:A","scene:R")
FIELDS=(
    "target_class","operation","category","scene",
    "public_task_count","static_engine_unsupported",
    "source_dependent_unverified","verified_official_D0_tasks",
    "verified_official_I0_tasks","matched_official_scored_tasks",
    "synthetic_native_reference_exists","readiness",
)


def build_capability_rows(public_task_jsonl:Path)->list[dict]:
    metadata=read_tasks(public_task_jsonl)
    g1=generate_coverage_ledger(metadata)
    by={(kind,op,category,scene):[] for kind,op,category,scene
        in product(CLASSES,OPERATIONS,CATEGORIES,SCENES)}
    for task in g1["tasks"]:
        key=(task["target_class"],task["operation"],
             task["category"],task["scene"])
        by[key].append(task)
    native_synthetic=frozenset({
        ("IfcWall","create"),("IfcWall","update"),
        ("IfcWall","delete"),("IfcWindow","delete"),
    })
    result=[]
    for kind,op,category,scene in product(
        CLASSES,OPERATIONS,CATEGORIES,SCENES
    ):
        rows=by[(kind,op,category,scene)]
        result.append({
            "target_class":kind,
            "operation":op,
            "category":category,
            "scene":scene,
            "public_task_count":len(rows),
            "static_engine_unsupported":sum(
                r["engine_status"]==STATIC_UNSUPPORTED for r in rows),
            "source_dependent_unverified":sum(
                r["engine_status"]==CONDITIONAL for r in rows),
            "verified_official_D0_tasks":0,
            "verified_official_I0_tasks":0,
            "matched_official_scored_tasks":0,
            "synthetic_native_reference_exists":(
                "YES_NOT_NL_GROUNDED" if (kind,op) in native_synthetic else "NO"
            ),
            "readiness":"BLOCKED_NO_OFFICIAL_IFC_EVALUATION",
        })
    assert len(result)==108
    assert sum(row["public_task_count"] for row in result)==324
    assert sum(row["static_engine_unsupported"] for row in result)==246
    assert sum(row["source_dependent_unverified"] for row in result)==78
    return result


def write_capability_csv(records:list[dict],path:Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
