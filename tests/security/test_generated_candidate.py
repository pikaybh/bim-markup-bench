"""OWN synthetic-only dynamic Python worker: negative and actual kernel proof.

No paid provider is called; live tests require a cached immutable worker image.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

import ifcopenshell

from src.runner.docker_isolation import DockerIsolationError
from src.runner.generated_candidate import (
    candidate_content_sha256,_recover_ifc,_trusted_separate_own_grader,
    run_offline_own_generated_candidate,MAX_SOURCE_BYTES
)
from src.runner.ifc_worker import OWN_SOURCE,_docker_cli
from src.runner.own_grader_container import (
    inspect_own_grader,TRUSTED_GRADER_PROGRAM,run_own_isolated_grader
)
from unittest.mock import patch
import copy

IMAGE=os.environ.get("BIM_BENCH_IFC_WORKER_IMAGE_SHA","")

# The following code is owned by this repository but NOT present in the
# worker's hardcoded TRUSTED_CASES. It enters as opaque untrusted script bytes.
OWN_DYNAMIC_PROGRAM=b'''import ifcopenshell
model=ifcopenshell.open("/input/input.ifc")
wall=model.by_type("IfcWall")[0]
solid=next(item for rep in wall.Representation.Representations
           for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
solid.Depth=3.3
model.write("/output/result.ifc")
'''

OWN_ATTACK_PROGRAM=b'''import os,socket,subprocess
from pathlib import Path
assert not Path("/grader/ground_truth.ifc").exists()
assert not Path("/var/run/docker.sock").exists()
assert os.getenv("OPENAI_API_KEY") is None
try:
 Path("/input/input.ifc").write_bytes(b"ATTACK")
 raise RuntimeError("Original source writable")
except OSError:
 pass
try:
 socket.create_connection(("1.1.1.1",443),timeout=1)
 raise RuntimeError("Network unexpectedly permitted")
except OSError:
 pass
try:
 subprocess.run(["/bin/sh","-c","id"],timeout=2,check=True)
 raise RuntimeError("Child process unexpectedly permitted")
except (OSError,subprocess.SubprocessError):
 pass
import ifcopenshell
model=ifcopenshell.open("/input/input.ifc")
solid=next(item for rep in model.by_type("IfcWall")[0].Representation.Representations
           for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
solid.Depth=3.3
model.write("/output/result.ifc")
'''


class DynamicCandidateOfflineSecurityTests(unittest.TestCase):
    def test_source_digest_and_binary_format_fail_closed_without_docker(self):
        for source in (b"", b"\x00", b"\xff", b"A"*(MAX_SOURCE_BYTES+1)):
            with self.subTest(length=len(source)),self.assertRaises(DockerIsolationError):
                candidate_content_sha256(source)
        self.assertEqual(candidate_content_sha256(b"print(5)"),
                         sha256(b"print(5)").hexdigest())

    def test_missing_or_forged_worker_output_refused(self):
        with self.assertRaises(DockerIsolationError):
            _recover_ifc('{"trusted_small_ifc_b64":"YQ=="}')
        with self.assertRaises(DockerIsolationError):
            _recover_ifc('{"status":"fake"}')
        valid=base64.b64encode(b"ISO-10303-21;\nDATA;\n").decode()
        fake=json.dumps({"trusted_small_ifc_b64":valid})
        with self.assertRaises(DockerIsolationError):
            _recover_ifc(fake+"\n"+fake)
        with self.assertRaises(DockerIsolationError):
            _recover_ifc('{"trusted_small_ifc_b64":"'+("A"*400000)+'"}')

    def test_own_native_grader_is_separate_without_candidate_import(self):
        with TemporaryDirectory() as tmp:
            temp=Path(tmp)
            original=temp/"source.ifc"
            result=temp/"result.ifc"
            original.write_bytes(OWN_SOURCE.read_bytes())
            f=ifcopenshell.open(str(OWN_SOURCE))
            solid=next(item for rep in f.by_type("IfcWall")[0].Representation.Representations
                       for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
            solid.Depth=3.3
            f.write(str(result))
            score=_trusted_separate_own_grader(original,result)
            self.assertEqual(score["status"],"OWN_WALL_EDIT_VERIFIED")
            self.assertEqual(score["result_wall_depth"],3.3)
            self.assertEqual(score["official_tasks_scored"],0)
            self.assertTrue(score["only_expected_swept_wall_step_changed"])
            f.by_type("IfcWall")[0].Name="UNAUTHORIZED_CHANGED_NAME"
            f.write(str(result))
            with self.assertRaises(DockerIsolationError):
                _trusted_separate_own_grader(original,result)
            result.write_bytes(b"MALICIOUS_NON_IFC")
            with self.assertRaises(DockerIsolationError):
                _trusted_separate_own_grader(original,result)

    def test_grader_config_prestart_refuses_script_mount_gt_rw_and_secret(self):
        image="sha256:"+"b"*64
        allowed={
            "Image":image,
            "HostConfig":{
                "NetworkMode":"none","ReadonlyRootfs":True,
                "Privileged":False,"CapDrop":["ALL"],
                "SecurityOpt":["no-new-privileges:true"],
                "IpcMode":"none","PidsLimit":1,
                "Memory":536870912,"MemorySwap":536870912,
                "NanoCpus":750000000,
                "Tmpfs":{"/tmp":"rw,nosuid,nodev,noexec,size=16m"},
            },
            "Config":{
                "User":"65534:65534",
                "Entrypoint":["/usr/local/bin/python3"],
                "Cmd":["-c",TRUSTED_GRADER_PROGRAM],
                "Env":["HOME=/tmp","OPENBLAS_NUM_THREADS=1"],
            },
            "Mounts":[
                {"Destination":dest,"RW":False,"Type":"bind"}
                for dest in ("/source","/submission","/ground_truth")
            ],
        }
        def check(settings,blocked):
            r=subprocess.CompletedProcess(
                ["docker","inspect"],0,json.dumps([settings]),"")
            with patch("src.runner.own_grader_container._run",return_value=r):
                if blocked:
                    with self.assertRaises(DockerIsolationError):
                        inspect_own_grader("own-grader",image)
                else:
                    inspect_own_grader("own-grader",image)
        check(allowed,False)
        for mutate in ("script","writable_gt","missing_gt","secret","bad_command"):
            changed=copy.deepcopy(allowed)
            if mutate=="script":
                changed["Mounts"].append(
                    {"Destination":"/task","RW":False,"Type":"bind"})
            if mutate=="writable_gt":
                changed["Mounts"][-1]["RW"]=True
            if mutate=="missing_gt":
                changed["Mounts"].pop()
            if mutate=="secret":
                changed["Config"]["Env"].append("OPENAI_API_KEY=FORBIDDEN")
            if mutate=="bad_command":
                changed["Config"]["Cmd"]=["-c","print('forged grader')"]
            with self.subTest(mutation=mutate):
                check(changed,True)

    def test_unauthorized_candidate_is_rejected_before_invoking_image(self):
        with self.assertRaises(DockerIsolationError):
            run_offline_own_generated_candidate(
                "sha256:"+"0"*64,OWN_DYNAMIC_PROGRAM,"incorrect")
        with self.assertRaises(DockerIsolationError):
            run_offline_own_generated_candidate(
                "sha256:"+"0"*64,OWN_DYNAMIC_PROGRAM,
                sha256(OWN_DYNAMIC_PROGRAM).hexdigest(),seed=-1)
        from src.runner.sandbox import execute_untrusted_candidate,SandboxNotReady
        with self.assertRaises(SandboxNotReady):
            execute_untrusted_candidate(OWN_DYNAMIC_PROGRAM)


@unittest.skipUnless(IMAGE,"Real Linux AMD64 Docker image must be explicitly pinned")
class DynamicCandidateRealDockerTests(unittest.TestCase):
    def test_opaque_dynamic_python_program_runs_only_in_own_isolated_container(self):
        source_before=sha256(OWN_SOURCE.read_bytes()).hexdigest()
        digest=sha256(OWN_DYNAMIC_PROGRAM).hexdigest()
        a=run_offline_own_generated_candidate(IMAGE,OWN_DYNAMIC_PROGRAM,digest,seed=13)
        b=run_offline_own_generated_candidate(IMAGE,OWN_DYNAMIC_PROGRAM,digest,seed=13)
        self.assertEqual(a["status"],"OWN_SYNTHETIC_DYNAMIC_CANDIDATE_VERIFIED")
        self.assertEqual(a["run_id"],b["run_id"])
        self.assertEqual(a["output_sha256"],b["output_sha256"])
        self.assertEqual(a["independent_own_grader"]["result_wall_depth"],3.3)
        self.assertTrue(a["separate_OS_grader_container_verified"])
        self.assertEqual(a["isolated_own_grader"]["status"],"OWN_ISOLATED_GRADER_PASS")
        self.assertTrue(a["isolated_own_grader"]["GT_mounted_in_separate_grader_only"])
        self.assertFalse(a["isolated_own_grader"]["candidate_script_mounted_in_grader"])
        self.assertFalse(a["pilot_ready"])
        self.assertEqual(a["official_tasks_scored"],0)
        self.assertEqual(a["paid_model_calls"],0)
        self.assertEqual(sha256(OWN_SOURCE.read_bytes()).hexdigest(),source_before)

    def test_embedded_attacks_blocked_and_no_GT_or_key_visible(self):
        a=run_offline_own_generated_candidate(
            IMAGE,OWN_ATTACK_PROGRAM,sha256(OWN_ATTACK_PROGRAM).hexdigest(),seed=14)
        self.assertEqual(a["status"],"OWN_SYNTHETIC_DYNAMIC_CANDIDATE_VERIFIED")
        self.assertFalse(a["GT_accessible_inside_candidate_container"])
        self.assertTrue(a["original_source_unchanged"])
        self.assertTrue(a["separate_OS_grader_container_verified"])

    def test_no_output_and_unbounded_stdout_fail_closed(self):
        for code in (
            b'print("Hello, but no IFC output")\n',
            b'import os\nwhile True: os.write(1,b"X"*65536)\n',
        ):
            with self.subTest(source_sha=sha256(code).hexdigest()):
                with self.assertRaises(DockerIsolationError):
                    run_offline_own_generated_candidate(
                        IMAGE,code,sha256(code).hexdigest(),seed=16,wall_seconds=5)

    def test_wrong_own_gt_not_accepted_by_os_isolated_grader(self):
        # Same source/output, but substitute a known OWN synthetic reference
        # with wall height 3.0 rather than the correct 3.3.
        with TemporaryDirectory() as folder:
            source=Path(folder)/"input.ifc"
            out=Path(folder)/"result.ifc"
            source.write_bytes(OWN_SOURCE.read_bytes())
            f=ifcopenshell.open(str(source))
            solid=next(item for rep in f.by_type("IfcWall")[0].Representation.Representations
                       for item in rep.Items if item.is_a("IfcExtrudedAreaSolid"))
            solid.Depth=3.3
            f.write(str(out))
            with patch("src.runner.own_grader_container.OWN_GT",OWN_SOURCE):
                with self.assertRaises(DockerIsolationError):
                    run_own_isolated_grader(IMAGE,source,out)

    def test_only_own_dynamic_containers_are_removed(self):
        proc=subprocess.run(
            [_docker_cli(),"ps","-a","--filter","name=bim-bench-own-dynamic",
             "--format","{{.Names}}"],
            capture_output=True,text=True,timeout=12,
        )
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(proc.stdout.strip(),"")
        grader=subprocess.run(
            [_docker_cli(),"ps","-a","--filter","name=bim-bench-own-grader",
             "--format","{{.Names}}"],
            capture_output=True,text=True,timeout=12,
        )
        self.assertEqual(grader.returncode,0,grader.stderr)
        self.assertEqual(grader.stdout.strip(),"")


if __name__=="__main__":
    unittest.main()
