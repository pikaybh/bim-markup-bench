"""One mandatory LOCAL Docker daemon endpoint for inspection and execution.

Every Docker CLI operation in the OWN-only worker / grader / kernel-probe path
must use this same host selector. The caller cannot select a Docker context,
TCP daemon, SSH endpoint, TLS credentials, or a remote Docker socket.

This does NOT start a daemon, attest its OS security, authorize generated
code, or permit model/official benchmark execution. It only closes a CLI
routing gap between read-only admission and the actual Docker commands.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys


class LocalDockerTransportError(ValueError):
    """Missing fixed local engine or untrusted Docker global selector."""


_UNTRUSTED_GLOBAL_FLAGS=(
    "-H","--host","--context","--config","--tls","--tlscacert",
    "--tlscert","--tlskey","--tlsverify",
)


def _local_docker_endpoint()->str:
    """Return a fixed platform-owned local socket, ignoring env/context."""
    if os.name=="nt":
        return "npipe:////./pipe/dockerDesktopLinuxEngine"
    if sys.platform=="darwin":
        socket=Path.home()/".docker"/"run"/"docker.sock"
    elif sys.platform.startswith("linux"):
        socket=Path("/var/run/docker.sock")
    else:
        raise LocalDockerTransportError("Unsupported Docker control platform")
    if socket.is_symlink() or not socket.is_socket():
        raise LocalDockerTransportError(
            "Expected local Unix Docker socket is absent, symlinked or not a socket")
    return "unix://"+str(socket)


def pinned_local_docker_argv(argv:list[str])->list[str]:
    """Anchor the SAME local endpoint for inspect/create/start/attach/cleanup.

    Docker global client options are rejected rather than allowing callers
    to override --host through later options or inherited environments.
    This wrapper never invokes Docker and never executes task code.
    """
    if not isinstance(argv,list) or len(argv)<2 or not all(
            isinstance(x,str) and x for x in argv):
        raise LocalDockerTransportError("Malformed Docker CLI invocation")
    for arg in argv[1:]:
        if arg in _UNTRUSTED_GLOBAL_FLAGS or any(
                arg.startswith(flag+"=") for flag in _UNTRUSTED_GLOBAL_FLAGS):
            raise LocalDockerTransportError(
                "Explicit Docker host/context/config/TLS override is forbidden")
    # Always immediately after the executable, ahead of the verb.
    return [argv[0],"--host",_local_docker_endpoint(),*argv[1:]]
