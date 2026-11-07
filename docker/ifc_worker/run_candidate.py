"""Isolated WORKER entrypoint: bounded execution of task-local solution.py.

This file is only called *inside* the Linux kernel sandbox. Candidate code
is never imported on the host. A parent trusted controller must pin image,
verify mounts/seccomp/env, and enforce a hard elapsed timeout+cleanup before
calling this with a model-generated script. No API keys or GT are mounted.
"""
from __future__ import annotations
import os
from pathlib import Path
import resource
import runpy
import sys

# Hard as well as soft caps (unprivileged worker cannot increase hard cap).
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024*1024,32*1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_CPU,(25,25))
# No candidate code may be executed outside a task-local read-only script.
candidate=Path("/task/solution.py")
if candidate.is_symlink() or not candidate.is_file():
    raise RuntimeError("Missing ordinary task-local Python script")
os.chdir("/output")
sys.argv=[str(candidate)]
runpy.run_path(str(candidate),run_name="__main__")
