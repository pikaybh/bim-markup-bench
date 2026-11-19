"""BIBIMBAP original-author scorer provenance and offline no-op audit (#102).

Official Python tests are loaded from an OUTSIDE Git clone pinned by commit.
IFC bytes are loaded from a separate OUTSIDE Hugging Face dataset clone.
Only per-task metadata and scores are committed: no third-party source/IFC.
NO network, LLM inference, generated code or ground-truth disclosure to a model.

The no-op negative control passes the *same unmodified IFC* twice to
author's original execute_test. It SHOULD get no credit for edits. Any
positive result highlights author-scorer behavior needing analysis.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

AUTHOR_SHA = "667004e16bd38fd7d538bcee56191465429fd975"
DATA_SHA = "f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca"
EDIT_TYPES = ("create", "update", "delete")
MODULE_PATTERN = re.compile(r"^(test|geometry_test|topological_test)_\d{2}$")
ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools" / "bibimbap_author_worker.py"


class AuthorAuditError(ValueError):
    pass


def _head(repo: Path) -> str:
    if not (repo / ".git").exists():
        # Supports a .git file for worktrees, but never picks another folder.
        if not (repo / ".git").is_file():
            raise AuthorAuditError(f"Git checkout missing: {repo.name}")
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=10, check=True,
    )
    return result.stdout.strip()


def _unchanged(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, timeout=10, check=True,
    )
    return not result.stdout.strip()


def _sha(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def read_original_tasks(author: Path, dataset: Path) -> tuple[list[dict], dict]:
    author, dataset = author.resolve(strict=True), dataset.resolve(strict=True)
    author_sha, data_sha = _head(author), _head(dataset)
    if author_sha != AUTHOR_SHA or data_sha != DATA_SHA:
        raise AuthorAuditError(
            "Author repository or dataset differs from prospective pinned commit"
        )
    if not _unchanged(author) or not _unchanged(dataset):
        raise AuthorAuditError("Original author source/data checkout is modified")
    csvfile = dataset / "prompts" / "all_questions.csv"
    if not csvfile.is_file() or csvfile.is_symlink():
        raise AuthorAuditError("Original 100-row benchmark question CSV not found")
    with csvfile.open(newline="", encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    if len(rows) != 100:
        raise AuthorAuditError("Expected exactly 100 original BIBIMBAP tasks")
    counts = Counter(row["CRUD"].strip().lower() for row in rows)
    if counts != {"create": 15, "update": 15, "delete": 15, "retrieve": 55}:
        raise AuthorAuditError(f"Unexpected original CRUD counts: {counts}")
    edited = []
    safe_ids = set()
    test_hashes = {}
    ifc_hashes = {}
    for index, row in enumerate(rows):
        ident = row.get("test", "").strip()
        if ident in safe_ids:
            raise AuthorAuditError(f"Duplicate task name: {ident}")
        safe_ids.add(ident)
        ifc_name = row.get("ifc-file", "").replace("\\", "/")
        model = (dataset / "ifc" / ifc_name).resolve()
        if not model.is_relative_to((dataset / "ifc").resolve()):
            raise AuthorAuditError("Path traversal in author IFC manifest")
        if not model.is_file() or model.is_symlink():
            raise AuthorAuditError(f"Missing physical author IFC: {ident}")
        if model.stat().st_size < 24:
            raise AuthorAuditError(f"Empty/LFS pointer IFC: {ident}")
        with model.open("rb") as ifc_input:
            header = ifc_input.read(32)
        if not header.lstrip().startswith(b"ISO-10303-21;"):
            raise AuthorAuditError(f"Not STEP IFC bytes: {ident}")
        ifc_hashes[ifc_name] = _sha(model)
        crud = row["CRUD"].strip().lower()
        if crud not in EDIT_TYPES:
            continue
        if MODULE_PATTERN.fullmatch(ident) is None:
            raise AuthorAuditError(f"Unexpected original edit test name: {ident}")
        if not row.get("question", "").strip():
            raise AuthorAuditError(f"Missing author task instruction: {ident}")
        module_path = author / "data" / "tests" / (ident + ".py")
        if not module_path.is_file() or module_path.is_symlink():
            raise AuthorAuditError(f"Missing original evaluator Python: {ident}")
        code = module_path.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(code, filename=ident + ".py")
        except SyntaxError as exc:
            raise AuthorAuditError(f"Invalid original scorer module: {ident}") from exc
        defs = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                and x.name == "execute_test"]
        if len(defs) != 1 or len(defs[0].args.args) < 3:
            raise AuthorAuditError(f"Missing/invalid execute_test: {ident}")
        test_hashes[ident] = _sha(module_path)
        edited.append({
            "index": index,
            "test_id": ident,
            "crud": crud,
            "category": ident.split("_test")[0] if "_test" in ident else "basic",
            "ifc_relpath": ifc_name,
            "test_sha256": test_hashes[ident],
            "ifc_sha256": ifc_hashes[ifc_name],
            "original_scorer_execute_test": True,
        })
    if len(edited) != 45 or len(test_hashes) != 45:
        raise AuthorAuditError("45 original author edit evaluators not present")
    if Counter(x["category"] for x in edited) != {
        "basic": 15, "geometry": 15, "topological": 15
    }:
        raise AuthorAuditError("Unexpected 45 editing task category distribution")
    return edited, {
        "author_commit_sha": author_sha,
        "data_commit_sha": data_sha,
        "original_csv_sha256": _sha(csvfile),
        "original_ifc_file_count": len(ifc_hashes),
        "original_edited_test_count": len(test_hashes),
        "source_license_file_present": (author / "LICENSE").is_file(),
    }


def run_negative_control(
    task: dict, author: Path, data: Path, *, timeout_seconds: int,
) -> dict:
    src = data / "ifc" / task["ifc_relpath"]
    if _sha(src) != task["ifc_sha256"]:
        raise AuthorAuditError(f"IFC changed during audit: {task['test_id']}")
    started = perf_counter()
    with TemporaryDirectory(prefix="bibimbap-noop-") as tmp:
        root = Path(tmp)
        a = root / "source.ifc"
        b = root / "unchanged.ifc"
        shutil.copy2(src, a)
        shutil.copy2(src, b)
        command = [
            sys.executable, "-I", str(WORKER),
            "--author-repo", str(author),
            "--test", task["test_id"],
            "--source-ifc", str(a),
            "--edited-ifc", str(b),
        ]
        try:
            outcome = subprocess.run(
                command, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout_seconds,
                check=False,
            )
            line = outcome.stdout.strip().splitlines()
            info = json.loads(line[-1]) if line else {"status": "NO_RESULT"}
            if not isinstance(info, dict):
                raise ValueError("Invalid worker response")
        except subprocess.TimeoutExpired:
            info = {"status": "TIMEOUT"}
            outcome = None
        except (ValueError, json.JSONDecodeError):
            info = {"status": "MALFORMED_WORKER_RESULT"}
            outcome = None
        if (_sha(a) != task["ifc_sha256"] or
                _sha(b) != task["ifc_sha256"] or _sha(src) != task["ifc_sha256"]):
            raise AuthorAuditError(f"Author test modified an input IFC: {task['test_id']}")
    safe = {
        "test_id": task["test_id"],
        "crud": task["crud"],
        "category": task["category"],
        "status": info.get("status", "NO_RESULT"),
        "elapsed_s": round(perf_counter() - started, 3),
        "original_and_edited_identical": True,
        "worker_exit": outcome.returncode if outcome else None,
    }
    if info.get("status") == "SCORED":
        safe["metrics"] = info.get("metrics", {})
        safe["author_noop_score"] = info.get("score")
    elif info.get("status") == "ERROR":
        safe["error_type"] = info.get("type", "UNKNOWN")
        safe["error_message"] = str(info.get("message", ""))[:180]
    else:
        safe["error_message"] = (outcome.stderr[-180:] if outcome else "")
    return safe


def run_audit(
    author: Path, data: Path, *, controls: bool = False, limit: int = 45,
    timeout_seconds: int = 20,
) -> dict:
    edited, pinned = read_original_tasks(author, data)
    report = {
        "schema": "bibimbap-original-author-grader-audit/v0.1",
        "research_mode": "XML_direct_editing_vs_published_external_baselines",
        "paper": "BIBIMBAP (Kujat et al., 2026)",
        "author_source": "https://github.com/nbharathik/bibimbap",
        "dataset_source": "https://huggingface.co/datasets/clemenskujat/bibimbap-data",
        "pinned": pinned,
        "task_population_total": 100,
        "original_editing_tasks": 45,
        "original_retrieval_tasks_excluded_from_edit_experiment": 55,
        "original_editing_distribution": {
            "operation": dict(sorted(Counter(t["crud"] for t in edited).items())),
            "category": dict(sorted(Counter(t["category"] for t in edited).items())),
        },
        "editing_tasks": edited,
        "author_evaluator_code_present_for_45": True,
        "original_scorer_runtime_tested": False,
        "xml_to_ifc_production_integration_verified": False,
        "llm_inference_count": 0,
        "claimed_author_baseline_reproduction": False,
        "code_license_unverified": not pinned["source_license_file_present"],
        "noncausal_external_paper_comparison_only": True,
    }
    if controls:
        selected = edited[:limit]
        observations = []
        for index, task in enumerate(selected, 1):
            print(f"AUTHOR_NOOP {index}/{len(selected)} {task['test_id']}", file=sys.stderr, flush=True)
            observations.append(run_negative_control(
                task, author, data, timeout_seconds=timeout_seconds,
            ))
        statuses = Counter(item["status"] for item in observations)
        positives = [
            t["test_id"] for t in observations
            if t["status"] == "SCORED" and float(t.get("author_noop_score", 0)) > 0.00001
        ]
        report["original_scorer_runtime_tested"] = True
        report["negative_control"] = {
            "mode": "identical_cloned_IFC_both_paths",
            "n": len(observations),
            "exhaustive_45": len(observations) == 45,
            "per_task_timeout_s": timeout_seconds,
            "statuses": dict(sorted(statuses.items())),
            "nonzero_author_score_on_unmodified_input_ids": positives,
            "observations": observations,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-repo", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--negative-controls", action="store_true")
    parser.add_argument("--limit", type=int, default=45)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--output-json", type=Path)
    opts = parser.parse_args(argv)
    if not 1 <= opts.limit <= 45 or not 3 <= opts.timeout_seconds <= 120:
        parser.error("limit must be 1-45, and timeout must be 3-120 sec")
    try:
        report = run_audit(
            opts.author_repo, opts.dataset, controls=opts.negative_controls,
            limit=opts.limit, timeout_seconds=opts.timeout_seconds,
        )
    except (AuthorAuditError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "EVIDENCE_INVALID", "reason": str(exc)}, sort_keys=True))
        return 2
    if opts.output_json:
        path = opts.output_json
        if path.exists() or path.is_symlink() or not path.parent.is_dir():
            parser.error("Evidence path exists, is a symlink or missing parent")
        with path.open("x", encoding="utf8", newline="\n") as out:
            json.dump(report, out, indent=2, sort_keys=True)
            out.write("\n")
    summary = {
        "status": "ORIGINAL_SCORER_AUDIT_ONLY_NOT_XML_INFERENCE",
        "author_commit": report["pinned"]["author_commit_sha"],
        "dataset_commit": report["pinned"]["data_commit_sha"],
        "editing_task_count": report["original_editing_tasks"],
        "author_evaluator_found": report["author_evaluator_code_present_for_45"],
        "test_run": report["original_scorer_runtime_tested"],
        "negative_control": report.get("negative_control", {}).get("statuses"),
        "llm_inference": 0,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
