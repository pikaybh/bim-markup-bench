"""Source-only XML edit for original BIBIMBAP geometry_test_11.

Developer-authored engineering witness only: decrement the height of
every Wall hosted in the *source-visible* second storey by 0.5m.
Never read author grader source or target GUIDs to select objects.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.util.unit
from lxml import etree

from src.runtime.ifc_projection import project_ifc
from src.runtime.compiler import compile_declarative_xml
from tools.audit_bibimbap_author import AUTHOR_SHA, DATA_SHA, WORKER, _head, _sha


def run_witness(author: Path, dataset: Path) -> dict:
    if _head(author) != AUTHOR_SHA or _head(dataset) != DATA_SHA:
        raise ValueError("Original BIBIMBAP upstream revision changed")
    source = dataset / "ifc" / "01" / "01" / "01_01_011.ifc"
    digest = _sha(source)
    with TemporaryDirectory(prefix="bibi-xml-update-") as tmp:
        root = Path(tmp)
        meter_source = root / "source-m.ifc"
        meter_result = root / "result-m.ifc"
        mm_result = root / "result-mm.ifc"
        original = ifcopenshell.open(str(source))
        expected_unit = ifcopenshell.util.unit.calculate_unit_scale(original)
        if abs(expected_unit - 0.001) > 1e-12:
            raise ValueError("Original mm units changed")
        storeys = [x for x in original.by_type("IfcBuildingStorey") if x.Name == "L2"]
        if len(storeys) != 1:
            raise ValueError("No uniquely source-visible second storey L2")
        source_visible_level_guid = storeys[0].GlobalId
        normalized = ifcopenshell.util.unit.convert_file_length_units(original, "METER")
        normalized.write(str(meter_source))
        projection = project_ifc(meter_source, strict_on_opaque=False)
        tree = etree.fromstring(projection.xml)
        ns = etree.QName(tree).namespace
        level_nodes = tree.find("{" + ns + "}Levels")
        element_nodes = tree.find("{" + ns + "}Elements")
        second_levels = [
            x for x in level_nodes
            if x.get("ifcGuid") == source_visible_level_guid
        ]
        if len(second_levels) != 1:
            raise ValueError("Projected L2 association missing")
        local_level = second_levels[0].get("id")
        targets = [x for x in element_nodes if etree.QName(x).localname == "Wall"
                   and x.get("level") == local_level]
        if len(targets) != 6:
            raise ValueError(f"Source-derived second-storey wall count changed ({len(targets)})")
        for wall in targets:
            before = Decimal(wall.get("height"))
            after = before - Decimal("0.5")
            if after <= Decimal("0"):
                raise ValueError("Nonpositive wall height")
            wall.set("height", str(after))
        payload = etree.tostring(tree, encoding="utf-8", xml_declaration=True)
        compiled = compile_declarative_xml(meter_source, payload, meter_result)
        restored = ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(meter_result)), "MILLIMETER",
        )
        restored.write(str(mm_result))
        scored = subprocess.run(
            [sys.executable, "-I", str(WORKER),
             "--author-repo", str(author), "--test", "geometry_test_11",
             "--source-ifc", str(source), "--edited-ifc", str(mm_result)],
            capture_output=True, text=True, timeout=40,
        )
        result = json.loads(scored.stdout.strip().splitlines()[-1]) if scored.stdout.strip() \
            else {"status": "NO_WORKER_OUTPUT", "stderr": scored.stderr[-180:]}
        root_original = {x.GlobalId for x in original.by_type("IfcRoot")}
        root_new = {x.GlobalId for x in restored.by_type("IfcRoot")}
        report = {
            "status": "XML_AUTHOR_GEOMETRY11_SCORED" if result.get("status") == "SCORED"
                else "XML_AUTHOR_GEOMETRY11_BLOCKED",
            "task_id": "geometry_test_11",
            "condition": "DEVELOPER_AUTHORED_XML_NOT_LLM",
            "original_source_unmodified": _sha(source) == digest,
            "source_visible_level_name": "L2",
            "wall_changes_source_derived": len(targets),
            "compile_status": compiled.as_dict()["status"],
            "result_ifc_schema": restored.schema,
            "result_unit_scale": ifcopenshell.util.unit.calculate_unit_scale(restored),
            "original_guid_preserved": root_original.issubset(root_new),
            "added_root_guid_count": len(root_new - root_original),
            "removed_root_guid_count": len(root_original - root_new),
            "original_author_scorer": result,
            "author_sha": AUTHOR_SHA,
            "dataset_sha": DATA_SHA,
            "llm_calls": 0,
        }
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--author-repo", type=Path, required=True)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output-json", type=Path)
    args = p.parse_args()
    try:
        report = run_witness(args.author_repo, args.dataset)
    except Exception as exc:
        print(json.dumps({
            "status": "XML_AUTHOR_GEOMETRY11_BLOCKED",
            "type": type(exc).__name__, "reason": str(exc)[:280],
        }, sort_keys=True))
        return 2
    if args.output_json:
        if args.output_json.exists() or args.output_json.is_symlink() or not args.output_json.parent.is_dir():
            p.error("Output exists or directory missing")
        with args.output_json.open("x", encoding="utf8", newline="\n") as out:
            json.dump(report, out, indent=2, sort_keys=True)
            out.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "XML_AUTHOR_GEOMETRY11_SCORED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
