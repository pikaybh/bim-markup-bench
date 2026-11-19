"""G1 #15: source-only D0/I0 Door+Opening native dependency slice.

Historical v0.1 report remains unchanged. This re-run emits v0.2 native
evidence on the new explicitly bounded D0 compiler policy. Neither arm's
developer-authored reference counts as official task success.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree

from src.data.bim_edit import read_tasks, repo_asset_path, verify_local_asset_bytes
from src.data.pilot_asset_audit import _files_in_root
from src.direct_markup.agent_runner import (
    SourceFileEdit, SourceOnlySettings, TrustedCompilationController,
    stage_source_only_workspace,
)
from src.runtime.compiler import CompilerError
from src.runner.offline_context_cost_gate import matched_shared_components
from src.imperative_control.agent_runner import create_matched_observations
from tests.oracles.python.independent_public_door_delete import native_door_opening_delete
from tests.oracles.python.public_door_delete_postconditions import (
    INPUT_SHA, PublicDoorDeleteBlocked, published_guids, check_native_i0_result,
)

ROOT = Path(__file__).resolve().parents[1]
CASE = "DOR-DEL-DIR-A-001"
TASKS_SHA = "9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83"
PILOT_SHA = "75b4847814dbefad95340556c0b62f9cda72cac319cd82ecb23ea4933c9ab694"
TREE_SHA = "f1b150a576f3d72045819768215c34fd84602ab4f6a5f4d2f0202a0ae3a92a39"


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise PublicDoorDeleteBlocked("Missing or linked frozen public evidence")
    return sha256(path.read_bytes()).hexdigest()


def verified_public_source(root: Path = ROOT):
    sources = (
        (root / "data/tasks.jsonl", TASKS_SHA),
        (root / "manifests/pilot_36_candidate_v0.json", PILOT_SHA),
        (root / "data/bim_edit_remote_tree.json", TREE_SHA),
    )
    if any(_sha(p) != digest for p, digest in sources):
        raise PublicDoorDeleteBlocked("Frozen task selection or remote IFC pin changed")
    pilot = json.loads(sources[1][0].read_text("utf8"))
    if (len(pilot["tasks"]) != 36
            or len({x["task_id"] for x in pilot["tasks"]}) != 36
            or sum(x["task_id"] == CASE for x in pilot["tasks"]) != 1):
        raise PublicDoorDeleteBlocked("Frozen candidate task population altered")
    rows = [x for x in read_tasks(sources[0][0]) if x["task_id"] == CASE]
    if len(rows) != 1:
        raise PublicDoorDeleteBlocked("Public deletion task ID missing or ambiguous")
    task = rows[0]
    public = {
        "task_id": CASE,
        "instruction": task["prompt"],
        "input_file": "input.ifc",
    }
    guids = published_guids(public["instruction"])
    tree = json.loads(sources[2][0].read_text("utf8"))
    index = {x["path"]: x for x in tree if x.get("type") == "file"}
    relative = repo_asset_path(task["input_ifc"])
    if relative not in index:
        raise PublicDoorDeleteBlocked("Source IFC missing from pinned public tree")
    source = _files_in_root(root / "data/ifc", relative)
    verify_local_asset_bytes(source, index[relative])
    if _sha(source) != INPUT_SHA:
        raise PublicDoorDeleteBlocked("Native pinned original IFC hash changed")
    # Never read task["ground_truth_ifc"], task["target"] or task["evaluation"].
    return public, guids, source


def _stage_and_probe_d0(original: Path, public: dict, guids: dict,
                        scratch: Path, *, spatial_observer=None) -> dict:
    session = stage_source_only_workspace(
        original, scratch / "D0_workspace", public, SourceOnlySettings())
    view = session.agent_visible_context()
    source_xml = etree.fromstring(view.xml_text.encode("utf8"))
    all_elements = [e for e in source_xml.iter() if isinstance(e.tag, str)]
    remove = [e for e in all_elements if e.get("ifcGuid") in (
        guids["door"], guids["opening"])]
    if (len(remove) != 2 or
            {etree.QName(e).localname for e in remove} != {"Door", "Opening"}):
        raise PublicDoorDeleteBlocked("Public Door/Opening not uniquely projected into XML")
    opening = next(e for e in remove if etree.QName(e).localname == "Opening")
    door = next(e for e in remove if etree.QName(e).localname == "Door")
    if door.get("opening") != opening.get("id"):
        raise PublicDoorDeleteBlocked("XML Door/Opening link does not match source")
    for node in remove:
        node.getparent().remove(node)
    xml = etree.tostring(source_xml, encoding="utf8", xml_declaration=True).decode("utf8")
    result = session.attempt(SourceFileEdit(
        "building.xml", view.xml_byte_sha256, "whole_file_rewrite", "",
        xml, False,
    ))
    if result["status"] != "ACCEPTED_VALID_XML":
        raise PublicDoorDeleteBlocked("Declarative source delete candidate was not accepted")
    candidate = scratch / "trusted-D0-output.ifc"
    compilation = TrustedCompilationController.compile_accepted(
        session, original, candidate)
    if (not candidate.is_file() or not compilation.write_committed
            or len(compilation.operations) != 1
            or compilation.operations[0].operation != "DELETE_HOSTED_DOOR_OPENING"):
        raise PublicDoorDeleteBlocked("Unexpected native D0 deletion plan/result")
    checked = check_native_i0_result(original, candidate, public["instruction"])
    if checked["official_tasks_scored"] != 0:
        raise PublicDoorDeleteBlocked("D0 native evidence misclassified as official")
    common = create_matched_observations(original, public)
    matched_shared_components(view, common, INPUT_SHA)
    spatial = (spatial_observer(original, candidate, public["instruction"])
               if spatial_observer is not None else None)
    result = {
        "D0_XML_both_public_objects_visible_and_removed": True,
        "D0_valid_declarative_snapshot_accepted": True,
        "D0_trusted_compiler_scoped_deletion_committed": True,
        "D0_native_output_written": True,
        "D0_independent_native_checker_passed": True,
        "D0_shared_public_source_view_bytes_matched_I0": True,
        "D0_XML_source_sha256": view.xml_byte_sha256,
        "D0_deletion_result_sha256": checked["i0_ifc_sha256"],
        "D0_IfcRoot_deleted": checked["native_IfcRoot_deleted"],
        "D0_host_wall_opening_void_closed": checked["host_wall_opening_void_closed"],
        "D0_native_unrelated_world_meshes_preserved":
            checked["native_unrelated_world_meshes_preserved"],
    }
    if spatial_observer is not None:
        result["trusted_D0_planar_boundary_evidence"] = spatial
    return result


def verify_public_door_delete_gate(root: Path = ROOT,
                                   *, spatial_observer=None) -> dict:
    public, guids, original = verified_public_source(root)
    original_sha = _sha(original)
    with TemporaryDirectory(prefix="G1-public-Door-Delete-") as td:
        scratch = Path(td)
        d0 = _stage_and_probe_d0(
            original, public, guids, scratch,
            spatial_observer=spatial_observer)
        i0_path = scratch / "trusted-I0.ifc"
        native_door_opening_delete(
            original, i0_path, guids["door"], guids["opening"])
        native = check_native_i0_result(original, i0_path, public["instruction"])
        spatial_i0 = (spatial_observer(original, i0_path, public["instruction"])
                      if spatial_observer is not None else None)
        if native["official_task_oracle_proven"] or native["official_tasks_scored"] != 0:
            raise PublicDoorDeleteBlocked("I0 observation incorrectly promoted to official task success")
    if _sha(original) != original_sha:
        raise PublicDoorDeleteBlocked("Original public IFC mutated during source-only preflight")
    result = {
        "version": "G1_PUBLIC_DOOR_DELETE_DEPENDENCY_GATE_V0.2",
        "frozen_task_id": CASE,
        "status": "PASS_BOUNDED_D0_I0_NATIVE_DELETION_OFFICIAL_TASK_BLOCKED",
        "source_only_observations": True,
        "input_ifc_sha256": original_sha,
        "public_instruction_sha256": sha256(public["instruction"].encode("utf8")).hexdigest(),
        **d0,
        **native,
        "status": "PASS_BOUNDED_D0_I0_NATIVE_DELETION_OFFICIAL_TASK_BLOCKED",
        "D0_I0_both_native_success_proven": True,
        "D0_I0_common_dependency_counts_match": (
            d0["D0_IfcRoot_deleted"] == native["native_IfcRoot_deleted"]
            and d0["D0_native_unrelated_world_meshes_preserved"]
                == native["native_unrelated_world_meshes_preserved"]
            and d0["D0_host_wall_opening_void_closed"]
                == native["host_wall_opening_void_closed"]),
        "unmentioned_space_boundary_cleanup_is_declared_native_policy": True,
        "source_Opening_direct_storey_assignment_does_not_exist": True,
        "I0_unmentioned_door_space_boundary_was_deleted": True,
        "I0_derived_dependency_cleanup_is_not_official_task_success": True,
        "full_task_oracle_proven": False,
        "model_visible_private_answer_metadata_used": False,
        "official_scorer_executed": False,
        "official_tasks_scored": 0,
        "LLM_calls": 0,
        "paid_spend_authorized": False,
        "G1_G2_G3_release_allowed": False,
    }
    if spatial_observer is not None:
        result["trusted_I0_planar_boundary_evidence"] = spatial_i0
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    report = verify_public_door_delete_gate()
    if args.output_json:
        path = args.output_json
        if path.is_symlink() or path.exists() or not path.parent.is_dir():
            parser.error("Refuse overwrite, symlink, or missing report directory")
        with path.open("x", encoding="utf8", newline="\n") as stream:
            json.dump(report, stream, sort_keys=True, indent=2)
            stream.write("\n")
    print(json.dumps({
        "status": report["status"],
        "frozen_task_id": CASE,
        "D0_trusted_compiler_scoped_deletion_committed":
            report["D0_trusted_compiler_scoped_deletion_committed"],
        "native_IfcRoot_deleted": report["native_IfcRoot_deleted"],
        "native_IfcRelSpaceBoundary_deleted": report["native_IfcRelSpaceBoundary_deleted"],
        "source_Opening_direct_storey_assignment_does_not_exist": True,
        "official_tasks_scored": 0,
        "LLM_calls": 0,
    }, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
