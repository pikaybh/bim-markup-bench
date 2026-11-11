"""Three-case, SOURCE-RELATIVE native IFC outcome rubric (G1 #16).

Not the original BIM-Edit scorer; never accesses GT or private task target.
Not a general task oracle: the three supported source/prompt patterns were
chosen after development, and only a bounded list of IFC postconditions
is checked. A PASS is an engineering diagnostic, NOT a benchmark solve.

This grader sees only the original IFC, an authored IFC candidate, and
the *public* task instruction, not the D or I authoring implementation.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import math

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np

from tests.oracles.python.independent_ifc_checker import inspect_ifc
from tests.oracles.python.public_door_delete_postconditions import check_native_i0_result

CASE_SHA = {
    "WIN-UPD-DIR-A-002":(
        "c533767f850a7ba01b73caf4467fae7cc886807a72a900d65cd480e7b877bcc9",
        "ff98d90daafa34a4979fc942d4d3477a0128526a2cf7c918c419473319078efe",
    ),
    "WAL-CRE-SPA-A-003":(
        "e90e635629a85cf1942163db0f647a49edc6d24631ba72ec79a0381c9145a0de",
        "31a00588498f68ef6791a133b033cc3da442749d5a237e76f0f5817cf095d14d",
    ),
    "DOR-DEL-DIR-A-001":(
        "170d9ed9c10a31d86c3ff2207a450fd552166af21472486f11004f6e2b14defb",
        "8dc59cbf741dbbf626843eebd91972197fa9ff0b9cbea251d6b9a8d8cd0a752a",
    ),
}
GUID=r"([A-Za-z0-9_$]{22})"
WINDOW_RE=re.compile(
    rf"Move the window with ID {GUID} by 1m in positive y direction\. "
    rf"Also move the opening {GUID} the same and preserve all relationships\.",
    re.ASCII,
)
WALL_RE=re.compile(
    rf"create a wall that spans orthogonally between the wall with the ID {GUID} "
    rf"and {GUID} and begins at 1\.3025m in \+y direction from the right "
    rf"side of the door looking from inside of the room with the ID {GUID}\. "
    rf"It must have a thickness of 0\.175m and a height of 2\.800m\.",
    re.ASCII,
)
TOL=1e-6
RUBRIC="source-only-native-posthoc-v0.1"


class SourceRubricBlocked(ValueError):
    """Untrusted IFC, source drift, unsupported public prompt or failed criterion."""


def _require(ok, message):
    if not ok:
        raise SourceRubricBlocked(message)


def _sha(path:Path)->str:
    _require(path.is_file() and not path.is_symlink(), "Missing or linked IFC")
    return sha256(path.read_bytes()).hexdigest()


def _check_native(source:Path, output:Path,case:str,public:str):
    _require(case in CASE_SHA, "Unknown frozen case")
    source_sha,prompt_sha=CASE_SHA[case]
    _require(_sha(source)==source_sha,"Frozen public IFC source changed")
    _require(isinstance(public,str) and
             sha256(public.encode("utf8")).hexdigest()==prompt_sha,
             "Published task instruction changed")
    _require(source.resolve()!=output.resolve(), "Source and candidate must differ")
    output_sha=_sha(output)
    for checked in (source, output):
        with checked.open("rb") as stream:
            _require(stream.read(96).lstrip(b" \r\n\t").startswith(b"ISO-10303-21;"),
                     "Invalid STEP IFC header")
    try:
        a=ifcopenshell.open(str(source))
        b=ifcopenshell.open(str(output))
        _require(a.schema==b.schema=="IFC4X3","Unexpected IFC schema")
    except SourceRubricBlocked:
        raise
    except Exception as exc:
        raise SourceRubricBlocked("Invalid native result IFC") from exc
    return a,b,source_sha,output_sha


def _box(info):
    value=info["shape"]
    _require(value[0]=="MESH","Unsupported product world mesh")
    return np.asarray(value[1],dtype=float),np.asarray(value[2],dtype=float)


def _same_unrelated_products(before:dict,after:dict,excluded:set):
    pre=before["products"]
    post=after["products"]
    for k in pre.keys() & post.keys():
        if k not in excluded:
            _require(pre[k]==post[k], "Unrelated IFC product geometry or placement modified")


def _window(source_model,out_model,src:dict,dst:dict,prompt:str):
    match=WINDOW_RE.fullmatch(prompt)
    _require(match is not None, "Unknown public Window move grammar")
    win,opening=match.groups()
    for guid,kind in ((win,"IfcWindow"),(opening,"IfcOpeningElement")):
        _require(guid in src["products"] and guid in dst["products"],"Target not projected")
        _require(src["products"][guid]["type"]==kind
                 and dst["products"][guid]["type"]==kind,
                 "Changed target class")
    _require(src["identities"]==dst["identities"],"Original root identities changed")
    _require(src["relations"]==dst["relations"],"Original IFC relations changed")
    _require(src["property_sets"]==dst["property_sets"]
             and src["materials"]==dst["materials"],"Unrelated semantics changed")
    _require(src["products"].keys()==dst["products"].keys(),"Product added/deleted")
    _same_unrelated_products(src,dst,{win,opening})
    for guid in (win,opening):
        old=source_model.by_guid(guid)
        new=out_model.by_guid(guid)
        xyz0=np.asarray(ifcopenshell.util.placement.get_local_placement(
            old.ObjectPlacement))[:3,3]
        xyz1=np.asarray(ifcopenshell.util.placement.get_local_placement(
            new.ObjectPlacement))[:3,3]
        _require(np.allclose(xyz1-xyz0,(0,1,0),rtol=0,atol=TOL),
                 "Target world displacement differs from public instruction")
        lo0,hi0=_box(src["products"][guid])
        lo1,hi1=_box(dst["products"][guid])
        _require(np.allclose(lo1-lo0,(0,1,0),rtol=0,atol=TOL)
                 and np.allclose(hi1-hi0,(0,1,0),rtol=0,atol=TOL),
                 "Target world geometry did not translate intact")
    _require(len(out_model.by_guid(win).FillsVoids)==1
             and out_model.by_guid(win).FillsVoids[0].RelatingOpeningElement==
                 out_model.by_guid(opening),
             "Window disconnected from Opening")
    return ("WORLD_TRANSLATION_AND_PRESERVED_SEMANTICS",
            "NO_FULL_OFFICIAL_TASK_ORACLE")


def _wall(source_model,out_model,src:dict,dst:dict,prompt:str):
    match=WALL_RE.fullmatch(prompt)
    _require(match is not None, "Unknown spatial Wall instruction grammar")
    first,second,room=match.groups()
    original_roots=set(src["identities"])
    new_roots=set(dst["identities"])-original_roots
    _require(not(original_roots-set(dst["identities"]))
             and Counter(dst["identities"][k][0] for k in new_roots)==
             Counter({"IfcWall":1,"IfcRelConnectsPathElements":2}),
             "Unexpected new or deleted IfcRoot")
    new_wall=next(k for k in new_roots if dst["identities"][k][0]=="IfcWall")
    _require(set(dst["products"])-set(src["products"])=={new_wall}
             and not(set(src["products"])-set(dst["products"])),
             "Unexpected IFC product creation/deletion")
    _same_unrelated_products(src,dst,set())
    _require(src["property_sets"]==dst["property_sets"]
             and src["materials"]==dst["materials"],
             "Changed original Psets or material")
    for oldroot in original_roots:
        _require(src["identities"][oldroot]==dst["identities"][oldroot],
                 "Renamed/retyped original root")
    for host in (first,second):
        _require(host in src["products"]
                 and src["products"][host]["type"]=="IfcWall",
                 "Public host Wall missing")
    _require(room in src["products"] and
             src["products"][room]["type"]=="IfcSpace","Public Room missing")
    wall=out_model.by_guid(new_wall)
    contacts=[r for r in out_model.by_type("IfcRelConnectsPathElements")
              if r.RelatedElement==wall]
    _require(len(contacts)==2 and {
        (r.RelatingElement.GlobalId,str(r.RelatingConnectionType),
         str(r.RelatedConnectionType)) for r in contacts
    }=={(first,"ATPATH","ATSTART"),(second,"ATPATH","ATEND")},
             "Missing/incorrect source Wall junctions")
    before_rels={r[1]:r for r in src["relations"]}
    after_rels={r[1]:r for r in dst["relations"]}
    _require(not(set(before_rels)-set(after_rels)),"Deleted original IFC relation")
    for relation in contacts:
        _require(relation.GlobalId in after_rels
                 and relation.GlobalId not in before_rels,
                 "New source Wall junction did not originate with edit")
    for guid,old in before_rels.items():
        new=after_rels[guid]
        if old!=new:
            _require(old[0]=="IfcRelContainedInSpatialStructure"
                     and old[2]==new[2] and old[4:]==new[4:]
                     and set(new[3])-set(old[3])=={new_wall}
                     and not(set(old[3])-set(new[3])),
                     "Unrequested change to original IFC relation")
    _require(set(after_rels)-set(before_rels)=={
        r.GlobalId for r in contacts},"Unexpected added IFC relation")
    lo,hi=_box(dst["products"][new_wall])
    source_door=source_model.by_type("IfcDoor")
    _require(len(source_door)==1,"Ambiguous public door-relative offset")
    door_bbox=_box(src["products"][source_door[0].GlobalId])[0]
    room_bbox=_box(src["products"][room])[0]
    _require(math.isclose(float(lo[1]),float(door_bbox[1])+1.3025,
                           abs_tol=TOL,rel_tol=0)
             and math.isclose(float(hi[1]-lo[1]),0.175,
                              abs_tol=TOL,rel_tol=0)
             and math.isclose(float(hi[2]-lo[2]),2.8,
                              abs_tol=TOL,rel_tol=0)
             and math.isclose(float(lo[2]),float(room_bbox[2]),
                              abs_tol=TOL,rel_tol=0),
             "Wrong Wall offset, thickness, height or elevation")
    _require(hi[0]>lo[0]+TOL,"Degenerate new Wall")
    return ("WALL_GEOMETRY_AND_TWO_JOINS_NO_UNREQUESTED_ROOT_CHANGE",
            "ROOM_PARTITION_AND_METADATA_NOT_ORACLE_PROVEN")


def score_source_relative(case:str,source:Path,candidate:Path,public_prompt:str)->dict:
    """Fail closed, only aggregate source-only verdict; never expose raw IFC."""
    a,b,input_sha,result_sha=_check_native(source,candidate,case,public_prompt)
    if case=="DOR-DEL-DIR-A-001":
        try:
            native=check_native_i0_result(source,candidate,public_prompt)
            _require(native["native_IfcRoot_deleted"]==10
                     and native["native_unrelated_world_meshes_preserved"]==13
                     and native["official_tasks_scored"]==0,
                     "Native cascade does not meet fixed source-relative policy")
        except SourceRubricBlocked:
            raise
        except Exception as exc:
            raise SourceRubricBlocked("Delete candidate native dependencies incorrect") from exc
        criterion="TEN_NATIVE_ROOT_DELETIONS_AND_UNRELATED_MESH_PRESERVATION"
        caveat="UNMENTIONED_BOUNDARY_POLICY_AND_ABSENT_OPENING_STOREY_UNKNOWN"
    else:
        try:
            before=inspect_ifc(source)
            after=inspect_ifc(candidate)
            if case=="WIN-UPD-DIR-A-002":
                criterion,caveat=_window(a,b,before,after,public_prompt)
            else:
                criterion,caveat=_wall(a,b,before,after,public_prompt)
        except SourceRubricBlocked:
            raise
        except Exception as exc:
            raise SourceRubricBlocked("Native source-relative grading failed") from exc
    _require(_sha(source)==input_sha and _sha(candidate)==result_sha,
             "IFC changed during independent read-only postcondition audit")
    return {
        "case":case,
        "status":"PASS_SOURCE_RELATIVE_NATIVE_RUBRIC_NOT_BENCHMARK_TASK_SUCCESS",
        "source_only_criterion":criterion,
        "unresolved_full_task_condition":caveat,
        "input_ifc_sha256":input_sha,
        "candidate_ifc_sha256":result_sha,
        "metric_origin":"surrogate",
        "source_relative_native_checks_pass":True,
        "full_instruction_specific_task_success_approved":False,
        "official_bim_edit_score":None,
        "benchmark_author_evaluator_used":False,
        "posthoc_developed_not_preregistered":True,
        "original_ifc_model_rights_cleared":False,
        "candidate_origin_verified_by_grader":False,
        "grader_itself_called_model_provider":False,
        "grader_provider_calls":0,
        "rubric_version":RUBRIC,
    }
