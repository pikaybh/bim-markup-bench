"""Staged, exclusive and IFC-independent output commit for a tiny compiler slice.

The input IFC is only opened read-only; output appears only after re-import,
typed schema checks, intended GUID changes and unaffected-root checks.
"""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
from typing import Callable

from src.runtime.ifc_snapshot import SourceIntegrityError, snapshot_source

class TransactionError(ValueError):
    pass

def stage_and_commit(destination: Path, writer: Callable[[Path],None],
                     validator: Callable[[Path],None]) -> None:
    if destination.exists() or destination.is_symlink():
        raise TransactionError("Result IFC path already exists; overwrite refused")
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,staged=tempfile.mkstemp(prefix=".bim-compiler-",suffix=".ifc",
                               dir=destination.parent)
    os.close(fd)
    stage=Path(staged)
    try:
        writer(stage)
        if not stage.is_file() or stage.stat().st_size==0:
            raise TransactionError("Missing or empty staged IFC")
        # Ensure source already checksummed by the caller, and verify the
        # staged file independently before making it visible to other users.
        snapshot_source(stage)
        validator(stage)
        with stage.open("rb") as file:
            os.fsync(file.fileno())
        try:
            os.link(stage,destination,follow_symlinks=False)
        except FileExistsError as exc:
            raise TransactionError("Result IFC appeared during stage; overwrite refused") from exc
    finally:
        if stage.exists():
            stage.unlink()
