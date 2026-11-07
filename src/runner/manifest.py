"""Immutable per-attempt JSON record and deterministic paired-arm scheduling."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re


TASK_ID_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,110}$")
ARMS=("direct_xml","imperative_python")

class RunManifestError(ValueError):
    pass

@dataclass(frozen=True)
class TrialSlot:
    task_id:str
    arm:str
    seed:int
    attempt:int
    run_id:str


def make_run_id(experiment_id:str,task_id:str,arm:str,
                seed:int,attempt:int,input_sha256:str)->str:
    if not TASK_ID_RE.fullmatch(task_id) or not TASK_ID_RE.fullmatch(experiment_id):
        raise RunManifestError("Invalid task/experiment identifier")
    if arm not in ARMS or type(seed) is not int or seed<0 or type(attempt) is not int or attempt<0:
        raise RunManifestError("Invalid arm, seed or attempt")
    if not re.fullmatch(r"[0-9a-f]{64}",input_sha256):
        raise RunManifestError("Input IFC SHA-256 invalid")
    content=f"g2-manifest-v0:{experiment_id}:{task_id}:{arm}:{seed}:{attempt}:{input_sha256}"
    return "r-"+hashlib.sha256(content.encode()).hexdigest()[:32]


def paired_schedule(tasks:list[dict],seeds:tuple[int,...],
                    experiment_id:str,input_sha256:str,attempt:int=0,
                    shuffle_seed:int=0)->tuple[TrialSlot,...]:
    if not tasks or not seeds:
        raise RunManifestError("Empty mock task/seed set")
    sorted_tasks=sorted(tasks,key=lambda r:r["task_id"])
    if len({t["task_id"] for t in sorted_tasks})!=len(sorted_tasks):
        raise RunManifestError("Duplicate task ID in mock scheduler")
    slots=[]
    for task in sorted_tasks:
        for seed in sorted(set(seeds)):
            arms=list(ARMS)
            # Randomized arm order with deterministic seeded draw; the
            # shuffled run order is fixed per task/seed/experiment.
            source=f"{shuffle_seed}:{experiment_id}:{task['task_id']}:{seed}"
            rand_seed=int(hashlib.sha256(source.encode()).hexdigest()[:16],16)
            random.Random(rand_seed).shuffle(arms)
            for arm in arms:
                slots.append(TrialSlot(
                    task_id=task["task_id"],arm=arm,seed=seed,
                    attempt=attempt,
                    run_id=make_run_id(experiment_id,task["task_id"],
                                       arm,seed,attempt,input_sha256),
                ))
    return tuple(slots)


def persist_record(root:Path,record:dict)->Path:
    if root.is_symlink():
        raise RunManifestError("Manifest root must not be a symlink")
    root.mkdir(parents=True,exist_ok=True)
    run_id=record["run_id"]
    if not re.fullmatch(r"r-[a-f0-9]{32}",run_id):
        raise RunManifestError("Invalid run ID in record")
    location=root/(run_id+".json")
    # Exclusive creation is atomic. No retry overwrites prior data.
    try:
        with location.open("x",encoding="utf-8") as stream:
            json.dump(record,stream,indent=2,sort_keys=True)
            stream.write("\n")
            stream.flush()
    except FileExistsError as exc:
        raise RunManifestError("Duplicate trial already persisted") from exc
    return location


def read_existing(root:Path,run_id:str)->dict|None:
    target=root/(run_id+".json")
    if target.is_symlink():
        raise RunManifestError("Recorded manifest must not be a symlink")
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise RunManifestError("Recorded run is not a regular file")
    data=json.loads(target.read_text(encoding="utf-8"))
    if data.get("run_id")!=run_id:
        raise RunManifestError("Recorded run ID mismatch")
    return data


def verify_record_artifacts(output_root:Path,record:dict)->None:
    """Verify all immutable artifacts on resume/report; never trust references.

    This is an offline integrity test, not a secure operating-system boundary.
    """
    refs=record.get("artifact_refs")
    hashes=record.get("artifact_sha256s")
    if not isinstance(refs,dict) or not isinstance(hashes,dict) or set(refs)!=set(hashes):
        raise RunManifestError("Incomplete recorded artifact hash inventory")
    if output_root.is_symlink() or not output_root.is_dir():
        raise RunManifestError("Unsafe output root")
    for key,path in refs.items():
        if not isinstance(path,str) or not path.startswith("trials/"+record["run_id"]+"/"):
            raise RunManifestError("Artifact ref escaped trial directory")
        file=output_root/path
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(output_root.resolve()):
            raise RunManifestError("Recorded artifact is missing or escaped")
        observed=hashlib.sha256(file.read_bytes()).hexdigest()
        if observed!=hashes[key]:
            raise RunManifestError("Immutable artifact hash mismatch")
    if hashes["source"]!=record["source_artifact_sha256"]:
        raise RunManifestError("Source artifact digest and manifest disagree")
    if hashes["raw_response"]!=record["raw_response_sha256"]:
        raise RunManifestError("Raw model response digest and manifest disagree")
    if hashes["model_context"]!=record["model_input_sha256"]:
        raise RunManifestError("Model input digest and manifest disagree")
