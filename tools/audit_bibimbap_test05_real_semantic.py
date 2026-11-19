"""Offline semantic-diff audit for the first actual BIBIMBAP XML LLM output.

Uses only the exact raw model output and original public IFC-derived XML,
never model inference, grader code, private oracle/target fields or files.
Does not modify the generated source to improve a score.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from lxml import etree

from tools.bibimbap_public_packet import make_public_packet, sha

ROOT = Path(__file__).resolve().parents[1]
FIXED_PROMPT_SHA = "2a483f97bf36726c2930ed9df8e80e1106f34bde460416a0c0b11fb3ea736959"
SOURCE_START = "PUBLIC SOURCE PROJECTION (building.xml):\n"
SOURCE_END = "\n\nPUBLIC EXPERIMENTAL XML GRAMMAR:"


def _xml(source: bytes):
    # XXE and external entities rejected (no recover, no network)
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    return etree.fromstring(source, parser=parser)


def _items(root) -> dict[str, tuple[str, tuple]]:
    items = {}
    for node in root.iter():
        key = node.get("id")
        if key:
            if key in items:
                raise ValueError("Duplicate XML state ID")
            items[key] = (
                etree.QName(node).localname,
                tuple(sorted(node.attrib.items())),
            )
    return items


def _nonid_nodes(root) -> tuple:
    return tuple(
        (etree.QName(e).localname, tuple(sorted(e.attrib.items())))
        for e in root.iter() if e.get("id") is None
    )


def analyze(original: bytes, generation: bytes) -> dict:
    source = _xml(original)
    edited = _xml(generation)
    if etree.QName(source).localname != "Building" or etree.QName(edited).localname != "Building":
        raise ValueError("Expected declarative Building root")
    old = _items(source)
    new = _items(edited)
    added = sorted(set(new) - set(old))
    dropped = sorted(set(old) - set(new))
    modified = sorted(k for k in set(old) & set(new) if old[k] != new[k])
    relation_and_metadata_unchanged = (_nonid_nodes(source) == _nonid_nodes(edited)
                                       and dict(source.attrib) == dict(edited.attrib))
    sections_unchanged = (
        [etree.QName(e).localname for e in source] ==
        [etree.QName(e).localname for e in edited])
    new_wall_attributes = None
    new_wall_geometry_matches_public = False
    if len(added) == 1 and new[added[0]][0] == "Wall":
        wall = dict(new[added[0]][1])
        try:
            x1, y1, x2, y2 = [float(wall[k]) for k in ("x1", "y1", "x2", "y2")]
            length = math.hypot(x2-x1, y2-y1)
            new_wall_geometry_matches_public = (all(map(math.isfinite, (x1, y1, x2, y2, length)))
                                                  and abs(x1) < 1e-6 and abs(y1+10) < 1e-6
                                                  and abs(length-15) < 0.05)
            new_wall_attributes = {
                "level_reference_present": bool(wall.get("level")),
                "declared_x1": x1, "declared_y1": y1,
                "declared_x2": x2, "declared_y2": y2,
                "declared_centerline_length_m": length,
                "declared_height_m": float(wall.get("height", "nan")),
                "declared_thickness_m": float(wall.get("thickness", "nan")),
            }
        except (ValueError, KeyError):
            pass
    return {
        "semantic_source_id_count": len(old),
        "semantic_model_id_count": len(new),
        "new_id_count": len(added),
        "new_element_types": [new[k][0] for k in added],
        "dropped_existing_id_count": len(dropped),
        "modified_existing_id_count": len(modified),
        "old_relation_container_and_nonid_nodes_unchanged": relation_and_metadata_unchanged,
        "section_order_unchanged": sections_unchanged,
        "new_wall_geometry_matches_public": new_wall_geometry_matches_public,
        "new_wall_declared_geometry": new_wall_attributes,
        "source_only_add_one_wall": (
            len(added) == 1 and new[added[0]][0] == "Wall" and not dropped
            and not modified and relation_and_metadata_unchanged and sections_unchanged
        ),
    }


def audit(dataset: Path, raw_output: Path, safe_score: Path) -> dict:
    packet, p = make_public_packet(dataset)
    if p["model_packet_sha256"] != FIXED_PROMPT_SHA:
        raise ValueError("Immutable original public prompt drift")
    text = packet["input"]
    original = text.split(SOURCE_START, 1)[1].split(SOURCE_END, 1)[0].encode("utf8")
    output = raw_output.read_bytes()
    saved = json.loads(safe_score.read_text(encoding="utf8"))
    if (saved.get("raw_model_output_sha256") != sha(output) or
            saved.get("public_packet_sha256") != FIXED_PROMPT_SHA or
            saved.get("actual_api_calls_attempted") != 1):
        raise ValueError("Raw model bytes do not match frozen one-shot trial")
    diff = analyze(original, output)
    return {
        "status": "REAL_ONE_SHOT_SOURCE_SEMANTIC_DIFF_REPRODUCED",
        "original_model_prompt_sha256": FIXED_PROMPT_SHA,
        "model_output_exact_sha256": sha(output),
        "original_source_xml_sha256": sha(original),
        "model_calls_this_audit": 0,
        "grader_consulted_this_audit": False,
        "raw_model_output_edited_or_corrected": False,
        "actual_luna_attempts_in_source_report": 1,
        "difference": diff,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--raw-output", type=Path, required=True)
    p.add_argument("--score-report", type=Path, required=True)
    p.add_argument("--output-json", type=Path)
    a = p.parse_args()
    result = audit(a.dataset, a.raw_output, a.score_report)
    if a.output_json:
        if a.output_json.exists() or a.output_json.is_symlink() or not a.output_json.parent.is_dir():
            p.error("Refuse overwrite or absent parent directory")
        with a.output_json.open("xb") as f:
            f.write((json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False)+"\n").encode("utf8"))
    print(json.dumps({ "status": result["status"], "original_ids": result["difference"]["semantic_source_id_count"],
        "edited_ids": result["difference"]["semantic_model_id_count"],
        "new_wall_only": result["difference"]["source_only_add_one_wall"],
        "correct_public_declared_geometry": result["difference"]["new_wall_geometry_matches_public"],
        "llm_calls_this_audit": result["model_calls_this_audit"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
