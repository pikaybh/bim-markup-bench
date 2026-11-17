"""Research-only, 25-tool-call state sessions for paired BIBIMBAP editing.

Both arms receive the original public IFC and question. In the XML arm the
LLM may inspect/edit whole XML state and receive trusted compiler feedback.
In the imperative arm Python code runs ONLY in a pinned local Linux Docker
container with the paper's ifc/ifcopenshell/api/util/result/commit() globals.

Neither model arm can access original grader/GT or BIXML/Xim product source.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Protocol
from uuid import uuid4

import ifcopenshell
import ifcopenshell.util.unit

from src.runtime.ifc_projection import project_ifc
from src.runtime.compiler import compile_declarative_xml
from src.runner.local_docker_transport import pinned_local_docker_argv

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/"tools"/"bibimbap_docker_ifc_code_worker.py"
PINNED_DOCKER_IMAGE="sha256:2ce0d57dff6ea443c7f5ffffd29cf8b1b50a141b77574aae5ca4646f45f3a1ee"
MAX_CODE_BYTES=64000
MAX_XML_BYTES=300000

class UnsupportedArm(RuntimeError):
    """Experimental representation/backend cannot handle original input."""

class SecurityGate(RuntimeError):
    pass

def file_hash(path:Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()

def _no_overwrite(p:Path,data:bytes):
    with p.open("xb") as f:
        f.write(data)

def _stateless_result(status:str, **kw)->dict:
    return {"status":status, **kw}

class ToolSession(Protocol):
    output_ifc: Path | None
    def call(self,name:str,arguments:dict)->dict: ...
    @property
    def tools(self)->list[dict]: ...

class XmlSourceEditSession:
    """Authoring model controls only complete XML text, never IFC mutator APIs."""

    def __init__(self, original_ifc:Path, folder:Path, *,
                 experimental_original_legacy_v08:bool=False,
                 experimental_original_complex_v039:bool=False,
                 experimental_original_room_v040:bool=False,
                 experimental_original_p3_v041:bool=False,
                 experimental_original_native_slab_v042:bool=False,
                 experimental_original_native_readonly_v044:bool=False,
                 experimental_original_native_mutations_v045:bool=False):
        if folder.exists():
            raise ValueError("XML session destination already exists")
        if not original_ifc.is_file() or original_ifc.is_symlink():
            raise ValueError("Source IFC unavailable")
        self.original_ifc=original_ifc.resolve(strict=True)
        self.folder=folder
        folder.mkdir(parents=True)
        self.output_ifc=None
        self.submissions=0
        self.source_sha=file_hash(self.original_ifc)
        original=ifcopenshell.open(str(original_ifc))
        self.experimental_original_legacy_v08=experimental_original_legacy_v08
        self.experimental_original_complex_v039=experimental_original_complex_v039
        self.experimental_original_room_v040=experimental_original_room_v040
        self.experimental_original_p3_v041=experimental_original_p3_v041
        self.experimental_original_native_slab_v042=experimental_original_native_slab_v042
        self.experimental_original_native_readonly_v044=experimental_original_native_readonly_v044
        self.experimental_original_native_mutations_v045=experimental_original_native_mutations_v045
        self.original_native_schema=original.schema
        self.legacy_original_task_id=None
        self.complex_original_task_id=None
        self.room_original_task_id=None
        self.p3_original_task_id=None
        self.slab_original_task_id=None
        self.native_readonly_original_task_id=None
        self.native_mutation_original_task_id=None
        if sum(bool(v) for v in (
            experimental_original_legacy_v08,experimental_original_complex_v039,
            experimental_original_room_v040,experimental_original_p3_v041,
            experimental_original_native_slab_v042,
            experimental_original_native_readonly_v044,
            experimental_original_native_mutations_v045))>1:
            raise UnsupportedArm("Original XML experimental opt-ins are mutually exclusive")
        if experimental_original_native_mutations_v045:
            from src.runtime.experimental_v45_original_native_mutations import (
                check_source)
            try:
                self.native_mutation_original_task_id=check_source(
                    self.original_ifc,self.source_sha,original)
            except Exception as exc:
                raise UnsupportedArm(str(exc)) from exc
        elif experimental_original_native_readonly_v044:
            from src.runtime.experimental_v44_original_native_step_readonly import (
                check_original_native_readonly_source,NativeSourceReadOnly044Error)
            try:
                self.native_readonly_original_task_id=check_original_native_readonly_source(
                    self.original_ifc,self.source_sha,original)
            except NativeSourceReadOnly044Error as exc:
                raise UnsupportedArm(str(exc)) from exc
        elif experimental_original_native_slab_v042:
            from src.runtime.experimental_v42_native_slab_readonly import (
                check_original_slab_source,OriginalSlabEvidence042Error)
            try:
                self.slab_original_task_id=check_original_slab_source(
                    self.original_ifc,self.source_sha,original)
            except OriginalSlabEvidence042Error as exc:
                raise UnsupportedArm(str(exc)) from exc
        elif experimental_original_p3_v041:
            from src.runtime.experimental_v41_p3_column_slab import (
                check_p3_original_source,P3NativeCreateError)
            try:
                self.p3_original_task_id=check_p3_original_source(
                    self.original_ifc,self.source_sha,original)
            except P3NativeCreateError as exc:
                raise UnsupportedArm(str(exc)) from exc
        elif experimental_original_room_v040:
            from src.runtime.experimental_v40_native_room_evidence import (
                check_original_native_room_input,NativeRoomV040Error)
            try:
                self.room_original_task_id=check_original_native_room_input(
                    self.original_ifc,self.source_sha,original)
            except NativeRoomV040Error as exc:
                raise UnsupportedArm(str(exc)) from exc
        elif experimental_original_complex_v039:
            from src.runtime.experimental_v39_complex_overlay import (
                check_pinned_original,ComplexV039Error)
            try:
                task,kind=check_pinned_original(
                    self.original_ifc,self.source_sha,original)
            except ComplexV039Error as exc:
                raise UnsupportedArm(str(exc)) from exc
            self.complex_original_task_id=task
        elif experimental_original_legacy_v08:
            # Source-pinned and explicitly opt-in; no general IFC version
            # conversion, model-visible mutator or pretrained answer surface.
            from tools.bibimbap_v038_legacy_live_gate import (
                check_original_legacy_source,LegacyLiveGateError)
            try:
                task,schema,klass=check_original_legacy_source(
                    self.original_ifc,self.source_sha,original)
            except LegacyLiveGateError as exc:
                raise UnsupportedArm(str(exc)) from exc
            self.legacy_original_task_id=task
        elif original.schema!="IFC4X3":
            raise UnsupportedArm("XML source compiler only accepts IFC4X3")
        unit=ifcopenshell.util.unit.calculate_unit_scale(original)
        if not abs(unit-.001)<1e-12:
            raise UnsupportedArm("XML compiler requires original millimetres")
        if (self.native_readonly_original_task_id is not None
                or self.native_mutation_original_task_id is not None):
            # No normalized-metre copy for source-native-mm read/edit modes.
            # No temporary new IFC file is needed for a purely model-visible
            # original-native-mm STEP read. Keep all prior authoring modes as is.
            self.normalized=None
        else:
            meter=ifcopenshell.util.unit.convert_file_length_units(original,"METER")
            self.normalized=folder/"normalized_original_m.ifc"
            meter.write(str(self.normalized))
        try:
            if self.native_mutation_original_task_id is not None:
                from src.runtime.experimental_v45_original_native_mutations import (
                    project_original_native_mutations_v045)
                snapshot=project_original_native_mutations_v045(
                    self.original_ifc,source_sha=self.source_sha)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("v0.45 original native IFC4X3 schema changed")
            elif self.native_readonly_original_task_id is not None:
                from src.runtime.experimental_v44_original_native_step_readonly import (
                    project_native_readonly_source_v044)
                snapshot=project_native_readonly_source_v044(
                    self.original_ifc,original_native_sha256=self.source_sha)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("v0.44 original native IFC4X3 schema mismatch")
            elif self.slab_original_task_id is not None:
                from src.runtime.experimental_v42_native_slab_readonly import project_original_slab_v042
                snapshot=project_original_slab_v042(
                    self.normalized,original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("v0.42 original Slab source IFC native schema mismatch")
            elif self.p3_original_task_id is not None:
                from src.runtime.experimental_v41_p3_column_slab import project_p3_source
                snapshot=project_p3_source(
                    self.normalized,original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("P3 original IFC4X3 native schema changed")
            elif self.room_original_task_id is not None:
                from src.runtime.experimental_v40_native_room_evidence import project_native_room_v040
                snapshot=project_native_room_v040(
                    self.normalized,original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
                if snapshot.source_ifc_schema!=self.original_native_schema:
                    raise ValueError("Original source P2 native IFC4X3 schema changed")
            elif self.complex_original_task_id is not None:
                from src.runtime.experimental_v39_complex_overlay import project_complex_v039
                snapshot=project_complex_v039(
                    self.normalized,original_input_sha256=self.source_sha)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("Original complex IFC4X3 native schema changed")
            elif self.legacy_original_task_id is not None:
                from src.runtime.experimental_v8_legacy_projection import project_legacy_v8
                snapshot=project_legacy_v8(self.normalized)
                if snapshot.native_schema!=self.original_native_schema:
                    raise ValueError("Original IFC2X3/IFC4 schema changed during opt-in projection")
            else:
                snapshot=project_ifc(
                    self.normalized,strict_on_opaque=False,
                    allow_original_flipped_slab=(
                        os.environ.get("BMB_V029_ORIGINAL_SLAB_TRANSLATE")=="1"
                        and file_hash(self.normalized)==
                        "16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac"
                    ),
                )
        except Exception as exc:
            raise UnsupportedArm(type(exc).__name__) from exc
        self.original_xml=snapshot.xml
        if not self.original_xml or len(self.original_xml)>MAX_XML_BYTES:
            raise UnsupportedArm("No bounded declarative input projection")
        self.current_xml=self.original_xml
        self.snapshot_sha=hashlib.sha256(snapshot.xml).hexdigest()
        self.compiler_supported_subset_only=True

    @property
    def tools(self):
        if self.native_mutation_original_task_id is not None:
            return [
                {
                    "type":"function","name":"read_building_xml",
                    "description":"Read original source immutable native STEP/metadata/world geometry with editable NativeEditPlan; source evidence is never editable, original author evaluator and correct answer unavailable.",
                    "parameters":{"type":"object","properties":{},"additionalProperties":False},"strict":True,
                },
                {
                    "type":"function","name":"submit_building_xml",
                    "description":"Submit COMPLETE XML with exactly one typed NativeEditPlan. Only original task-associated Slab dimensions, Column move, shared column depth, or list of original Column GUIDs to delete; trusted native source-mm writer followed by INDEPENDENT physical IFC oracle, otherwise last valid state preserved. Editing does NOT imply original public task correctness or original benchmark score.",
                    "parameters":{"type":"object","properties":{"xml_text":{"type":"string","description":"Whole original XML with unchanged original source section and one typed NativeEditPlan command"}},"required":["xml_text"],"additionalProperties":False},"strict":True,
                },
            ]
        if self.native_readonly_original_task_id is not None:
            return [
                {
                    "type":"function", "name":"read_building_xml",
                    "description":"Read the complete immutable original IFC4X3 native STEP DATA records, GUIDs, materials, properties, source relationships, placements and world meshes as XML. Every source fact is READ ONLY; no original question answer or grader included.",
                    "parameters":{"type":"object","properties":{},"additionalProperties":False},"strict":True,
                },
                {
                    "type":"function", "name":"submit_building_xml",
                    "description":"NATIVE IFC UPDATE/DELETE IS UNSUPPORTED for this read-only source-only research variant. Every submit is rejected with explicit failure. This tool cannot write a native IFC or edit the original source.",
                    "parameters":{"type":"object","properties":{"xml_text":{"type":"string","description":"Full replacement source XML; always rejected"}},"required":["xml_text"],"additionalProperties":False},"strict":True,
                },
            ]
        return [
            {
                "type":"function", "name":"read_building_xml",
                "description":"Read the complete current editable declarative building.xml state, including IDs, levels, geometry and relations. This is source text, not an IFC API or a read of the private benchmark evaluator.",
                "parameters":{"type":"object","properties":{},"additionalProperties":False},"strict":True,
            },
            {
                "type":"function","name":"submit_building_xml",
                "description":"Submit COMPLETE updated building.xml source text; trusted external compiler tries to compile it to a native IFC, returning success/error feedback. On failure the last valid source and IFC remain intact. You may fix XML and resubmit. Do not write commands or Python.",
                "parameters":{"type":"object","properties":{"xml_text":{"type":"string","description":"Full replacement declarative building.xml document, not a patch"}},"required":["xml_text"],"additionalProperties":False},"strict":True,
            },
        ]

    def call(self,name:str,arguments:dict)->dict:
        if name=="read_building_xml":
            if arguments:
                return _stateless_result("error",error="Unexpected read arguments")
            return _stateless_result("ok",xml=self.current_xml.decode("utf8"),
                                     current_xml_sha256=hashlib.sha256(self.current_xml).hexdigest(),
                                     native_candidate_available=self.output_ifc is not None)
        if name!="submit_building_xml":
            return _stateless_result("error",error="Tool unavailable to XML arm")
        if set(arguments)!={"xml_text"} or not isinstance(arguments["xml_text"],str):
            return _stateless_result("error",error="Complete xml_text string required")
        payload=arguments["xml_text"].encode("utf8")
        self.submissions+=1
        if self.native_readonly_original_task_id is not None:
            # No attempt directory, compiler, writer, or false-success artifact.
            return _stateless_result(
                "error",error_type="UnsupportedArm",
                error="V044_READ_ONLY_ORIGINAL_NATIVE_SOURCE_UPDATE_DELETE_MUTATION_UNSUPPORTED",
                native_ifc_committed=False,native_candidate_available=False,
                last_valid_xml_preserved=True,
                original_source_unchanged=file_hash(self.original_ifc)==self.source_sha)
        candidate_dir=self.folder/f"attempt_{self.submissions:02d}"
        candidate_dir.mkdir()
        _no_overwrite(candidate_dir/"submitted_exact.xml",payload)
        if not 0<len(payload)<=MAX_XML_BYTES:
            return _stateless_result("error",error="XML payload size exceeded")
        if self.native_mutation_original_task_id is not None:
            # v0.45 writer consumes and outputs ORIGINAL native IFC4X3 millimetres.
            # Never send it through the old normalise/convert-to-mm writer path.
            native_mm=candidate_dir/"candidate_original_native_mm.ifc"
            try:
                from src.security.agent_boundary import check_xml_bytes
                check_xml_bytes(payload)
                from src.runtime.experimental_v45_original_native_mutations import (
                    compile_original_native_mutation_v045)
                compilation=compile_original_native_mutation_v045(
                    self.original_ifc,payload,native_mm,source_sha=self.source_sha)
                from tools.bibimbap_v045_independent_native_mutation_oracle import (
                    verify_original_native_mutation_v045)
                oracle=verify_original_native_mutation_v045(
                    self.original_ifc,native_mm,submitted_xml=payload,
                    source_sha=self.source_sha,
                    task_id=self.native_mutation_original_task_id)
                if file_hash(self.original_ifc)!=self.source_sha:
                    raise SecurityGate("Original public native IFC mutated by editor")
                self.current_xml=payload
                self.output_ifc=native_mm
                return _stateless_result(
                    "ok",native_ifc_committed=True,
                    native_ifc_sha256=file_hash(native_mm),
                    current_xml_sha256=hashlib.sha256(payload).hexdigest(),
                    compile_status=compilation.as_dict()["status"],
                    independent_native_oracle_status=oracle["status"],
                    original_author_benchmark_task_success_claimed=False,
                    original_source_unchanged=True,model_can_revise_again=True)
            except Exception as exc:
                if native_mm.is_file():
                    native_mm.unlink()
                return _stateless_result(
                    "error",error_type=type(exc).__name__,
                    error=str(exc)[:900],native_ifc_committed=False,
                    last_valid_xml_preserved=True,
                    original_source_unchanged=file_hash(self.original_ifc)==self.source_sha,
                    current_xml_sha256=hashlib.sha256(self.current_xml).hexdigest())
        candidate_m=candidate_dir/"candidate_m.ifc"
        try:
            from src.security.agent_boundary import check_xml_bytes
            check_xml_bytes(payload)
            if self.slab_original_task_id is not None:
                from src.runtime.experimental_v42_native_slab_readonly import compile_original_slab_v042
                compilation=compile_original_slab_v042(
                    self.normalized,payload,candidate_m,
                    original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
            elif self.p3_original_task_id is not None:
                from src.runtime.experimental_v41_p3_column_slab import compile_p3_create
                compilation=compile_p3_create(
                    self.normalized,payload,candidate_m,
                    original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
            elif self.room_original_task_id is not None:
                from src.runtime.experimental_v40_native_room_evidence import compile_native_room_v040
                compilation=compile_native_room_v040(
                    self.normalized,payload,candidate_m,
                    original_native_sha256=self.source_sha,
                    original_source_mm=self.original_ifc)
            elif self.complex_original_task_id is not None:
                from src.runtime.experimental_v39_complex_overlay import compile_complex_v039
                compilation=compile_complex_v039(
                    self.normalized,payload,candidate_m,
                    original_input_sha256=self.source_sha)
            elif self.legacy_original_task_id is None:
                compilation=compile_declarative_xml(self.normalized,payload,candidate_m)
            else:
                from src.runtime.experimental_v8_legacy_compiler import compile_declarative_xml_v8
                compilation=compile_declarative_xml_v8(
                    self.normalized,payload,candidate_m)
            if not candidate_m.is_file():
                raise ValueError("Trusted compiler produced no IFC result")
            candidate_native=ifcopenshell.util.unit.convert_file_length_units(
                ifcopenshell.open(str(candidate_m)),"MILLIMETER"
            )
            candidate_mm=candidate_dir/"candidate_mm.ifc"
            candidate_native.write(str(candidate_mm))
            reread=ifcopenshell.open(str(candidate_mm))
            if abs(ifcopenshell.util.unit.calculate_unit_scale(reread)-.001)>1e-12:
                raise ValueError("Native IFC units not restored")
            if self.slab_original_task_id is not None:
                from tools.bibimbap_v042_native_slab_source_oracle import (
                    verify_v042_output_original_native)
                verify_v042_output_original_native(
                    self.original_ifc,candidate_mm,
                    task_id=self.slab_original_task_id,submitted_xml=payload)
            if self.p3_original_task_id is not None:
                from tools.bibimbap_v041_p3_native_oracle import verify_p3_original_native_add
                verify_p3_original_native_add(
                    self.original_ifc,candidate_mm,
                    task_id=self.p3_original_task_id,submitted_xml=payload)
            if self.room_original_task_id is not None:
                from tools.bibimbap_v040_native_room_oracle import verify_p2_native_wall_create
                verify_p2_native_wall_create(
                    self.original_ifc,candidate_mm,
                    task_id=self.room_original_task_id,submitted_xml=payload)
            if self.complex_original_task_id is not None:
                from tools.bibimbap_v039_complex_native_oracle import verify_complex_original_restored
                verify_complex_original_restored(
                    self.original_ifc,candidate_mm,
                    task_id=self.complex_original_task_id,submitted_xml=payload)
            if self.legacy_original_task_id is not None:
                from tools.bibimbap_v038_legacy_live_gate import verify_native_original_restored
                verify_native_original_restored(
                    self.original_ifc,candidate_mm,
                    task_id=self.legacy_original_task_id,
                    expected_schema=self.original_native_schema)
            if file_hash(self.original_ifc)!=self.source_sha:
                raise SecurityGate("Source IFC changed during XML trial")
            self.current_xml=payload
            self.output_ifc=candidate_mm
            return _stateless_result("ok",native_ifc_committed=True,
                current_xml_sha256=hashlib.sha256(payload).hexdigest(),
                compile_status=compilation.as_dict().get("status"),
                native_ifc_sha256=file_hash(candidate_mm),
                model_can_revise_again=True,
            )
        except Exception as exc:
            return _stateless_result("error",native_ifc_committed=False,
                error_type=type(exc).__name__,
                error=str(exc)[:500],
                last_valid_xml_preserved=True,
                model_can_revise_again=True,
            )

def build_pinned_docker_command(image:str,name:str, workspace:Path) -> list[str]:
    """Pure audited Docker arg builder. Never runs source on host."""
    if image != PINNED_DOCKER_IMAGE or not re.fullmatch(r"bibi-ifc-[0-9a-f]{16}",name):
        raise SecurityGate("Unpinned image or invalid container name")
    if not workspace.is_absolute() or workspace.is_symlink() or not workspace.is_dir():
        raise SecurityGate("Docker workspace must be an existing isolated directory")
    if not WORKER.is_file() or WORKER.is_symlink():
        raise SecurityGate("Trusted worker path missing")
    docker=shutil.which("docker")
    if not docker:
        raise SecurityGate("Docker not installed")
    return pinned_local_docker_argv([
        docker,"create","--pull=never","--name",name,"--network=none",
        "--read-only","--cap-drop=ALL","--security-opt=no-new-privileges:true",
        "--user=65534:65534","--cgroupns=private","--ipc=none",
        "--pids-limit=32","--memory=768m","--memory-swap=768m",
        "--cpus=1","--ulimit=nofile=64:64",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=64m",
        "--mount=type=bind,source="+str(workspace)+",target=/workspace",
        "--mount=type=bind,source="+str(WORKER)+",target=/worker.py,readonly",
        "--workdir=/workspace","--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=HOME=/tmp","--entrypoint=/usr/local/bin/python3",
        image,"/worker.py",
    ])

class DockerIFCExecutor:
    """One isolated Linux container per submitted code snippet, no host exec."""

    def __init__(self,image:str=PINNED_DOCKER_IMAGE,timeout:int=45):
        if image!=PINNED_DOCKER_IMAGE or not 1<=timeout<=45:
            raise SecurityGate("Only fixed local Docker image and 45s tool timeout allowed")
        self.image=image
        self.timeout=timeout

    @staticmethod
    def _call(argv:list[str],timeout:int) -> subprocess.CompletedProcess:
        # Host executes only Docker CLI; model source file is read by a
        # non-root container whose only writable bind is task scratch.
        return subprocess.run(argv,capture_output=True,text=True,encoding="utf8",
                              errors="replace",timeout=timeout,check=False)

    def run(self,folder:Path,code:str)->dict:
        if not isinstance(code,str) or not 0<len(code.encode("utf8"))<=MAX_CODE_BYTES:
            return _stateless_result("error",error="Python code length outside bounded tool input")
        if not (folder/"current.ifc").is_file():
            return _stateless_result("error",error="Sandbox IFC clone missing")
        payload=folder/"submitted_code.json"
        result=folder/"execution_result.json"
        if payload.exists() or result.exists():
            raise SecurityGate("Executor requires a fresh per-call directory")
        _no_overwrite(payload,json.dumps({"code":code},ensure_ascii=False).encode("utf8"))
        name="bibi-ifc-"+uuid4().hex[:16]
        command=build_pinned_docker_command(self.image,name,folder)
        docker=command[0]
        host=command[1:3]
        # Independent Docker local daemon/image attestation before create.
        inspect=self._call([docker,*host,"image","inspect",self.image],timeout=15)
        if inspect.returncode or json.loads(inspect.stdout)[0].get("Id")!=self.image:
            raise SecurityGate("Pinned local Linux image digest not found")
        created=False
        try:
            made=self._call(command,timeout=20)
            if made.returncode:
                return _stateless_result("error",error="Sandbox Docker create failed",
                    error_type="DockerCreateError")
            created=True
            metadata=self._call([docker,*host,"inspect",name],timeout=15)
            if metadata.returncode:
                raise SecurityGate("Cannot attest created container")
            box=json.loads(metadata.stdout)[0]
            hc=box.get("HostConfig") or {}
            mounts=box.get("Mounts") or []
            if not (
                hc.get("NetworkMode")=="none" and hc.get("ReadonlyRootfs") is True
                and hc.get("Privileged") is False
                and "ALL" in (hc.get("CapDrop") or [])
                and hc.get("PidsLimit")==32 and hc.get("Memory")==768*1024*1024
                and len(mounts)==2
                and {(m.get("Destination"),m.get("RW")) for m in mounts}
                    == {("/workspace",True),("/worker.py",False)}
                and box.get("Config",{}).get("User")=="65534:65534"
            ):
                raise SecurityGate("Sandbox host configuration failed attestation")
            try:
                started=self._call([docker,*host,"start","--attach",name],
                                   timeout=self.timeout+12)
            except subprocess.TimeoutExpired:
                return _stateless_result("error",error="Sandbox execution timeout",error_type="Timeout")
            if started.returncode and not result.is_file():
                return _stateless_result("error",error="Sandbox execution failed",
                                         error_type="DockerExecutionError")
            if not result.is_file():
                return _stateless_result("error",error="Sandbox returned no output",
                                         error_type="MissingResult")
            response=json.loads(result.read_text(encoding="utf8"))
            allowed={key:response.get(key) for key in (
                "status","committed","result","stdout","stderr","error_type","error","traceback","backend"
            ) if key in response}
            if len(json.dumps(allowed,ensure_ascii=False,default=repr))>18000:
                allowed["stdout"]=str(allowed.get("stdout",""))[:2000]
                allowed["stderr"]=str(allowed.get("stderr",""))[:1500]
            return allowed
        finally:
            if created:
                self._call([docker,*host,"rm","--force",name],timeout=15)

class PythonIfcCodeSession:
    """Paper-compatible execute_ifc_code facade, isolated clone, no GT mount."""

    def __init__(self,original_ifc:Path,folder:Path,executor:DockerIFCExecutor):
        if folder.exists() or original_ifc.is_symlink() or not original_ifc.is_file():
            raise ValueError("Unique folder and regular original IFC required")
        self.original_ifc=original_ifc.resolve(strict=True)
        self.source_sha=file_hash(original_ifc)
        self.folder=folder
        self.executor=executor
        self.calls=0
        folder.mkdir(parents=True)
        self.current=folder/"current.ifc"
        shutil.copyfile(original_ifc,self.current)
        self.output_ifc=self.current
        self.committed=False

    @property
    def tools(self)->list[dict]:
        return [{
            "type":"function","name":"execute_ifc_code",
            "description":"Execute Python code against the current IFC model. The IFC is preloaded as ifc (ifcopenshell.file). Also available: ifcopenshell, api (ifcopenshell.api), util, element_util, guid, result and commit(). Assign to result for tool response. Call commit() to save changes; no auto-save.",
            "parameters":{"type":"object","properties":{"code":{"type":"string"}},"required":["code"],"additionalProperties":False},"strict":True,
        }]

    def call(self,name:str,arguments:dict)->dict:
        if name!="execute_ifc_code":
            return _stateless_result("error",error="No such Python arm tool")
        if set(arguments)!={"code"} or not isinstance(arguments["code"],str):
            return _stateless_result("error",error="Python code string required")
        self.calls+=1
        call_dir=self.folder/f"call_{self.calls:02d}"
        call_dir.mkdir()
        shutil.copyfile(self.current,call_dir/"current.ifc")
        result=self.executor.run(call_dir,arguments["code"])
        # commit persists across calls, including errors AFTER commit().
        if result.get("committed") and (call_dir/"current.ifc").is_file():
            trial=call_dir/"current.ifc"
            try:
                ifcopenshell.open(str(trial))
                self.current.write_bytes(trial.read_bytes())
                self.committed=True
            except Exception:
                return _stateless_result("error",error="Committed IFC cannot be reopened")
        if file_hash(self.original_ifc)!=self.source_sha:
            raise SecurityGate("External original IFC mutated")
        result["staged_ifc_sha256"]=file_hash(self.current)
        return result
