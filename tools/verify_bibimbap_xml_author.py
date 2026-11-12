"""Developer-authored *XML* positive witness on original BIBIMBAP test_05.

Not LLM performance. Uses external pinned author source/IFC and an isolated
working directory. A trusted unit conversion is applied before projection
and after compilation because all 45 original editing inputs are millimetres.
Does not overwrite source or vendor files or claim no collateral differences.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from math import hypot, isfinite
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
from tools.audit_bibimbap_author import (
    AUTHOR_SHA, DATA_SHA, WORKER, _head, _sha,
)

WALL_LOCAL_ID = "wall_bibimbap000001"


def run_witness(author: Path, dataset: Path, *, end_xy: tuple[float, float] = (15.0, -10.0)) -> dict:
    if len(end_xy) != 2 or not all(isfinite(float(x)) for x in end_xy) or hypot(end_xy[0], end_xy[1] + 10.0) <= 0:
        raise ValueError("A finite nonzero wall length is required")
    if _head(author) != AUTHOR_SHA or _head(dataset) != DATA_SHA:
        raise ValueError("Upstream source/data SHA drift")
    source = dataset / "ifc" / "basic_tasks.ifc"
    sha_before = _sha(source)
    with TemporaryDirectory(prefix="bibi-xml-positive-") as d:
        folder = Path(d)
        meter_source = folder / "source-meter.ifc"
        edited_xml = folder / "edited.xml"
        meter_result = folder / "result-meter.ifc"
        mm_result = folder / "result-mm.ifc"
        unchanged_mm = folder / "noop-mm.ifc"
        base = ifcopenshell.open(str(source))
        old_scale = ifcopenshell.util.unit.calculate_unit_scale(base)
        if abs(old_scale - 0.001) > 1e-12:
            raise ValueError("BIBIMBAP mm source was not pinned")
        normalized = ifcopenshell.util.unit.convert_file_length_units(base, "METER")
        normalized.write(str(meter_source))
        projection = project_ifc(meter_source, strict_on_opaque=False)
        xml_root = etree.fromstring(projection.xml)
        ns = etree.QName(xml_root).namespace
        levels = xml_root.find("{" + ns + "}Levels")
        elements = xml_root.find("{" + ns + "}Elements")
        if levels is None or elements is None or not len(levels):
            raise ValueError("No supported level/element containers")
        zero = [x for x in levels if x.get("elevation") == "0"]
        if len(zero) != 1:
            raise ValueError("No unique ground-floor level for test_05")
        chosen_level = zero[0].get("id")

        wall_attrs = {
            "id": WALL_LOCAL_ID,

            "level": chosen_level,
            "x1": "0", "y1": "-10", "z1": "0",
            "x2": format(end_xy[0], ".12g"), "y2": format(end_xy[1], ".12g"), "z2": "0",
            "height": "3.0", "thickness": "0.2",
        }
        etree.SubElement(elements, "{" + ns + "}Wall", attrib=wall_attrs)
        payload = etree.tostring(xml_root, encoding="utf-8", xml_declaration=True)
        edited_xml.write_bytes(payload)
        compilation = compile_declarative_xml(meter_source, payload, meter_result)
        # Original native IFC grading expects millimetres, so restore units.
        back = ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(meter_result)), "MILLIMETER",
        )
        back.write(str(mm_result))
        noop = ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(meter_source)), "MILLIMETER",
        )
        noop.write(str(unchanged_mm))
        observations = {}
        for label, output in (("unit_roundtrip_noop", unchanged_mm),
                              ("xml_wall_created", mm_result)):
            result = subprocess.run(
                [sys.executable, "-I", str(WORKER),
                 "--author-repo", str(author), "--test", "test_05",
                 "--source-ifc", str(source), "--edited-ifc", str(output)],
                capture_output=True, text=True, timeout=40,
            )
            observations[label] = {
                "worker_exit": result.returncode,
                "scorer": json.loads(result.stdout.splitlines()[-1]) if result.stdout else {
                    "status": "NO_WORKER_OUTPUT", "stderr": result.stderr[-200:],
                },
            }
        orig_guids = set(x.GlobalId for x in base.by_type("IfcRoot"))
        final_ifc = ifcopenshell.open(str(mm_result))
        final_guids = set(x.GlobalId for x in final_ifc.by_type("IfcRoot"))
        counts = {
            "source_wall": len(base.by_type("IfcWall")),
            "edited_wall": len(final_ifc.by_type("IfcWall")),
            "added_guids": len(final_guids - orig_guids),
            "lost_guids": len(orig_guids - final_guids),
        }
        report = {
            "status": "XML_AUTHOR_WITNESS_SCORED"
                if observations["xml_wall_created"]["scorer"].get("status") == "SCORED"
                else "XML_AUTHOR_WITNESS_BLOCKED",
            "task_id": "test_05",
            "developer_wall_start_xy_m": [0.0, -10.0],
            "developer_wall_end_xy_m": [float(end_xy[0]), float(end_xy[1])],
            "developer_wall_horizontal_length_m": hypot(end_xy[0], end_xy[1] + 10.0),
            "source_type": "external_original_BIBIMBAP",
            "edited_type": "DEVELOPER_AUTHORED_XML_NOT_LLM",
            "author_sha": AUTHOR_SHA, "dataset_sha": DATA_SHA,
            "input_source_hash_unmodified": sha_before == _sha(source),
            "original_ifc_scale": old_scale,
            "normalized_ifc_scale": 1.0,
            "restored_ifc_scale": ifcopenshell.util.unit.calculate_unit_scale(final_ifc),
            "projection_projected_count": len(projection.projected_global_ids),
            "projection_opaque_count": len(projection.opaque_references),
            "compile_status": compilation.as_dict()["status"],
            "root_inventory": counts,
            "observations": observations,
            "claimed_original_paper_comparison": False,
            "model_calls": 0,
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
            "status": "XML_AUTHOR_WITNESS_BLOCKED",
            "error_type": type(exc).__name__,
            "reason": str(exc)[:280],
        }, sort_keys=True))
        return 2
    if args.output_json:
        if args.output_json.exists() or args.output_json.is_symlink() or not args.output_json.parent.is_dir():
            p.error("Output exists or directory absent")
        with args.output_json.open("x", encoding="utf8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "XML_AUTHOR_WITNESS_SCORED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
