#!/usr/bin/env python3
"""Offline environment doctor: never opens .env, calls OpenAI, or exposes keys."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "ifcopenshell": "0.8.4.post1",
    "openai": "2.48.0",
    "python-dotenv": "1.2.1",
    "jsonschema": "4.25.1",
    "PyYAML": "6.0.3",
}

def check_environment() -> dict:
    report = {
        "status": "PASS",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "requirements": {},
        "ifc4_smoke": {"status": "NOT_RUN"},
        "paid_api_calls": 0,
    }
    py = sys.version_info
    if not (py.major == 3 and py.minor == 12):
        report["status"] = "FAIL"
        report["python_error"] = "Project requires Python 3.12"
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["requires-python"] != ">=3.12,<3.13":
        report["status"] = "FAIL"
        report["python_constraint_error"] = "Python constraint unexpectedly changed"
    for name, expected in REQUIRED.items():
        try:
            observed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            observed = None
        report["requirements"][name] = {"installed": observed, "expected": expected, "match": observed == expected}
        if observed != expected:
            report["status"] = "FAIL"
    if report["status"] == "FAIL":
        return report

    try:
        import ifcopenshell
        import ifcopenshell.guid

        model = ifcopenshell.file(schema="IFC4")
        model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="IndependentSyntheticSmoke")
        with tempfile.TemporaryDirectory(prefix="bim-markup-offline-") as tmpdir:
            p = Path(tmpdir) / "synthetic.ifc"
            model.write(str(p))
            restored = ifcopenshell.open(str(p))
            projects = restored.by_type("IfcProject")
            if len(projects) != 1 or projects[0].Name != "IndependentSyntheticSmoke":
                raise ValueError("IFC4 synthetic round-trip changed project identity or name")
        report["ifc4_smoke"] = {"status": "PASS", "schema": "IFC4", "projects": 1}
    except Exception as exc:
        report["status"] = "FAIL"
        report["ifc4_smoke"] = {"status": "FAIL", "error_type": type(exc).__name__, "detail": str(exc)[:160]}
    return report

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="Emit machine-readable output without secrets")
    args = p.parse_args()
    report = check_environment()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("Environment:", report["status"])
        print("Python:", report["python"], report["machine"])
        for k, v in report["requirements"].items():
            print(" ", k, v["installed"], "OK" if v["match"] else "MISMATCH")
        print("Synthetic IFC4 read/write:", report["ifc4_smoke"]["status"])
        print("Paid API calls:", report["paid_api_calls"])
        if "python_error" in report:
            print("ERROR:", report["python_error"])
    return 0 if report["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
