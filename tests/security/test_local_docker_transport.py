"""Offline verification of identical fixed LOCAL Docker daemon routing.

No real Docker, container, Python candidate, model or official evaluator is
launched by these tests. We intercept subprocess and check exact CLI argv.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import unittest

from src.runner.local_docker_transport import (
    LocalDockerTransportError,_local_docker_endpoint,pinned_local_docker_argv,
)
from src.runner.docker_isolation import DockerIsolationError,_invoke
from src.runner.ifc_worker import _run
from src.runner.generated_candidate import _limited_attach


WIN_ENGINE="npipe:////./pipe/dockerDesktopLinuxEngine"


def completed(argv,*,code=0):
    return subprocess.CompletedProcess(argv,code,"{}","")


class LocalDockerTransportTests(unittest.TestCase):
    def test_local_windows_endpoint_constant_never_uses_remote_context(self):
        with patch("src.runner.local_docker_transport.os.name","nt"):
            with patch.dict(os.environ,{
                "DOCKER_HOST":"tcp://external.example:2375",
                "DOCKER_CONTEXT":"remote-workspace",
                "DOCKER_TLS_VERIFY":"1",
            }):
                self.assertEqual(_local_docker_endpoint(),WIN_ENGINE)
                argv=pinned_local_docker_argv(
                    ["docker.exe","create","--network=none","sha256:"+"a"*64])
                self.assertEqual(argv[:4],
                                 ["docker.exe","--host",WIN_ENGINE,"create"])
                self.assertNotIn("remote-workspace"," ".join(argv))
                self.assertNotIn("tcp://"," ".join(argv))

    def test_all_own_worker_control_verbs_are_pinned(self):
        captured=[]
        def intercept(argv,**kwargs):
            captured.append((argv,kwargs["env"]))
            return completed(argv)
        with (
            patch("src.runner.ifc_worker._docker_cli",return_value=r"C:\Docker\docker.exe"),
            patch("src.runner.ifc_worker._host_docker_env",return_value={"PATH":r"C:\Docker"}),
            patch("src.runner.local_docker_transport.os.name","nt"),
            patch("src.runner.ifc_worker.subprocess.run",side_effect=intercept),
        ):
            for command in (
                ["docker","info","--format","{{.Architecture}}"],
                ["docker","image","inspect","sha256:"+"a"*64],
                ["docker","create","--pull=never","--name=bim-own-test"],
                ["docker","inspect","a"*64],
                ["docker","start","--attach","a"*64],
                ["docker","rm","-f","bim-own-test"],
                ["docker","ps","-a"],
            ):
                _run(command)
        self.assertEqual(len(captured),7)
        for argv,env in captured:
            self.assertEqual(argv[1:3],["--host",WIN_ENGINE])
            self.assertNotIn("DOCKER_CONTEXT",env)
            self.assertNotIn("OPENAI_API_KEY",env)

    def test_untrusted_local_executable_never_reaches_docker_subprocess(self):
        with (
            patch("src.runner.ifc_worker._docker_cli",return_value="docker.exe"),
            patch("src.runner.ifc_worker.subprocess.run",
                  side_effect=AssertionError("Never run anything")),
        ):
            for args in (["curl","http://remote"],["python","-c","print(1)"],
                         ["docker"],[],["other-docker.exe","info"]):
                with self.subTest(args=args),self.assertRaisesRegex(
                    DockerIsolationError,"trusted local Docker CLI"):
                    _run(args)

    def test_candidate_attached_stream_uses_same_daemon(self):
        seen={}
        def forbid(argv,**kwargs):
            seen["argv"]=argv
            seen["env"]=kwargs["env"]
            raise RuntimeError("sentinel: no subprocess actually started")
        with (
            patch("src.runner.generated_candidate._docker_cli",
                  return_value=r"C:\Docker\docker.exe"),
            patch("src.runner.ifc_worker._host_docker_env",
                  return_value={"PATH":r"C:\Docker"}),
            patch("src.runner.local_docker_transport.os.name","nt"),
            patch("src.runner.generated_candidate.subprocess.Popen",side_effect=forbid),
        ):
            with self.assertRaisesRegex(RuntimeError,"sentinel"):
                _limited_attach("a"*64,10)
        self.assertEqual(seen["argv"][1:],
                         ["--host",WIN_ENGINE,"start","--attach","a"*64])
        self.assertNotIn("DOCKER_HOST",seen["env"])

    def test_trusted_kernel_probe_invokes_explicit_same_host(self):
        seen={}
        def mock_runner(argv,**kwargs):
            seen["argv"]=argv
            seen["env"]=kwargs["env"]
            return completed(argv)
        with (
            patch("src.runner.local_docker_transport.os.name","nt"),
            patch("src.runner.docker_isolation.subprocess.run",side_effect=mock_runner),
        ):
            result=_invoke(["C:\\Docker\\docker.exe","inspect","a"*64])
        self.assertEqual(result.returncode,0)
        self.assertEqual(seen["argv"][1:3],["--host",WIN_ENGINE])
        self.assertEqual(seen["argv"][3],"inspect")
        self.assertNotIn("DOCKER_HOST",seen["env"])
        self.assertNotIn("DOCKER_CONTEXT",seen["env"])
        # Fake probe sentinel is CLI-only; existing HostConfig inspection
        # separately denies inherited credentials inside the container.

    def test_all_remote_context_and_tls_overrides_are_rejected(self):
        bad=(["docker","--host","tcp://attacker:2375","inspect","x"],
             ["docker","--context=remote","inspect","x"],
             ["docker","--config=/external","info"],
             ["docker","-H","ssh://external","info"],
             ["docker","--tlsverify","info"],
             ["docker","create","--host=tcp://remote:2375"])
        with patch("src.runner.local_docker_transport.os.name","nt"):
            for args in bad:
                with self.subTest(args=args),self.assertRaisesRegex(
                    LocalDockerTransportError,"override"):
                    pinned_local_docker_argv(args)
            for malformed in ([],["docker"],["", "info"],["docker",None]):
                with self.assertRaises(LocalDockerTransportError):
                    pinned_local_docker_argv(malformed)

    def test_worker_refuses_remote_context_in_arguments_before_subprocess(self):
        with (
            patch("src.runner.local_docker_transport.os.name","nt"),
            patch("src.runner.ifc_worker._docker_cli",return_value="docker.exe"),
            patch("src.runner.ifc_worker.subprocess.run",
                  side_effect=AssertionError("No Docker process allowed")),
        ):
            with self.assertRaisesRegex(DockerIsolationError,"fixed local engine"):
                _run(["docker","--context=remote","info"])

    def test_probe_refuses_remote_context_in_arguments_before_subprocess(self):
        with (
            patch("src.runner.local_docker_transport.os.name","nt"),
            patch("src.runner.docker_isolation.subprocess.run",
                  side_effect=AssertionError("No Docker process allowed")),
        ):
            with self.assertRaisesRegex(DockerIsolationError,"local Docker engine"):
                _invoke([r"C:\Docker\docker.exe","--host","tcp://remote:2375",
                         "inspect","a"*64])

    def test_unix_symlink_or_missing_socket_blocks_before_docker(self):
        # Construct the WindowsPath before mocking the Darwin platform, to
        # avoid trying to instantiate an unsupported PosixPath on Windows.
        fake_home=Path("C:/a-definitely-absent-docker-test-user")
        with (
            patch("src.runner.local_docker_transport.os.name","posix"),
            patch("src.runner.local_docker_transport.sys.platform","darwin"),
            patch("src.runner.local_docker_transport.Path.home",
                  return_value=fake_home),
        ):
            with self.assertRaisesRegex(LocalDockerTransportError,
                                        "socket is absent"):
                _local_docker_endpoint()

    def test_other_platform_rejected_without_host_fallback(self):
        with (
            patch("src.runner.local_docker_transport.os.name","posix"),
            patch("src.runner.local_docker_transport.sys.platform","winlegacy"),
        ):
            with self.assertRaises(LocalDockerTransportError):
                _local_docker_endpoint()


if __name__=="__main__":
    unittest.main()
