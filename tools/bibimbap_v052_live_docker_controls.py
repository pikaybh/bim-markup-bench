"""v0.52 trusted developer-only source code for ACTUAL pinned Docker execution.

The returned text is Python executed by the existing Linux Docker worker against
the *actual* pinned original BIBIMBAP source IFC. It is not a hidden answer,
private grader, model-generated code, AST-only stub, or D XML edit plan.
Do not expose this module to the eventual LLM task prompt or worker mount.
"""
from __future__ import annotations

import re
from textwrap import dedent


TASKS = ("geometry_test_14", "geometry_test_15",
         "topological_test_11", "topological_test_17")


def question_named_slab_guid(public_question: str) -> str:
    ids = re.findall(r"\bid\s+([A-Za-z0-9_$]{22})(?=\W|$)",
                     public_question, flags=re.IGNORECASE)
    if len(ids) != 1:
        raise ValueError("Original public task must identify exactly one source Slab")
    return ids[0]


def developer_python_source(task_id: str, public_question: str,
                            *, positive: bool) -> str:
    """Source-conditioned developer controls, no original GT or private scorer."""
    if type(positive) is not bool or task_id not in TASKS:
        raise ValueError("Only frozen original four/public positive-negative controls")
    if task_id == "geometry_test_14":
        code = '''
slabs = ifc.by_type("IfcSlab")
assert len(slabs)==1
slab=slabs[0]
body=next(r for r in slab.Representation.Representations
          if r.RepresentationIdentifier=="Body")
assert len(body.Items)==1 and body.Items[0].is_a("IfcExtrudedAreaSolid")
solid=body.Items[0]
assert solid.SweptArea.is_a("IfcRectangleProfileDef")
dims=[float(solid.SweptArea.XDim),float(solid.SweptArea.YDim)]
assert abs(dims[0]-dims[1])>1e-4
target=max(dims) if CONTROL_POSITIVE else sum(dims)/2.0
if dims[0]<dims[1]:
    solid.SweptArea.XDim=target
else:
    solid.SweptArea.YDim=target
'''
    elif task_id == "geometry_test_15":
        code = '''
from itertools import product
import numpy as np
from ifcopenshell.util.placement import get_local_placement
columns=sorted(ifc.by_type("IfcColumn"), key=lambda c:c.GlobalId)
assert len(columns)==4
coords={c.GlobalId:tuple(round(float(get_local_placement(
    c.ObjectPlacement)[i,3])/1000,6) for i in (0,1)) for c in columns}
options=[]
for guid in sorted(coords):
    fixed={g:p for g,p in coords.items() if g!=guid}
    xs=sorted({p[0] for p in fixed.values()})
    ys=sorted({p[1] for p in fixed.values()})
    if len(xs)!=2 or len(ys)!=2: continue
    for target in product(xs,ys):
        if target==coords[guid]: continue
        if set(fixed.values())|{target} == set(product(xs,ys)):
            options.append((guid,target))
assert options
guid,desired=sorted(options)[0]
column=ifc.by_guid(guid)
old_world=get_local_placement(column.ObjectPlacement)
if not CONTROL_POSITIVE:
    desired=((desired[0]+coords[guid][0])/2,
             (desired[1]+coords[guid][1])/2)
parent=column.ObjectPlacement.PlacementRelTo
parent_matrix=get_local_placement(parent) if parent is not None else np.eye(4)
new_world=np.array([desired[0]*1000,desired[1]*1000,old_world[2,3],1.0])
local=np.linalg.inv(parent_matrix)@new_world
assert np.isfinite(local).all()
column.ObjectPlacement.RelativePlacement.Location.Coordinates=tuple(
    round(float(v),6) for v in local[:3])
'''
    elif task_id == "topological_test_11":
        guid = question_named_slab_guid(public_question)
        code = '''
import ifcopenshell.geom
slab=ifc.by_guid(NAMED_SLAB_GUID)
assert slab is not None and slab.is_a("IfcSlab")
settings=ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS,True)
slab_shape=ifcopenshell.geom.create_shape(settings,slab)
# Geom world vertices are already METRES even with original native-mm IFC.
slab_bottom=min(list(slab_shape.geometry.verts)[2::3])
columns=ifc.by_type("IfcColumn")
assert len(columns)==2
bases=[]
solids=[]
for column in columns:
    shape=ifcopenshell.geom.create_shape(settings,column)
    bases.append(min(list(shape.geometry.verts)[2::3]))
    body=next(r for r in column.Representation.Representations
              if r.RepresentationIdentifier=="Body")
    assert len(body.Items)==1 and body.Items[0].is_a("IfcMappedItem")
    mapped=body.Items[0].MappingSource.MappedRepresentation
    assert len(mapped.Items)==1 and mapped.Items[0].is_a("IfcExtrudedAreaSolid")
    solids.append(mapped.Items[0])
assert solids[0].id()==solids[1].id()
assert max(bases)-min(bases)<0.0001
source_depth=float(solids[0].Depth)/1000
desired=slab_bottom-bases[0]
new_depth=desired if CONTROL_POSITIVE else (desired+source_depth)/2
assert 0.2<new_depth<10 and abs(new_depth-source_depth)>0.001
solids[0].Depth=round(new_depth*1000,6)
'''
        code = "NAMED_SLAB_GUID=" + repr(guid) + "\n" + code
    else:
        guid = question_named_slab_guid(public_question)
        code = '''
slab=ifc.by_guid(NAMED_SLAB_GUID)
assert slab is not None and slab.is_a("IfcSlab")
containment={}
for rel in ifc.by_type("IfcRelContainedInSpatialStructure"):
    for entity in rel.RelatedElements:
        if entity.is_a("IfcColumn") or entity.is_a("IfcSlab"):
            assert entity.GlobalId not in containment
            containment[entity.GlobalId]=rel.RelatingStructure.GlobalId
assert slab.GlobalId in containment
all_columns=ifc.by_type("IfcColumn")
assert len(all_columns)==10
unrelated=sorted(c.GlobalId for c in all_columns if
                 containment.get(c.GlobalId)!=containment[slab.GlobalId])
assert len(unrelated)==5
for guid in (unrelated if CONTROL_POSITIVE else unrelated[:4]):
    api.run("root.remove_product",ifc,product=ifc.by_guid(guid))
'''
        code = "NAMED_SLAB_GUID=" + repr(guid) + "\n" + code
    # Audit the actual Linux sandbox process witness. This is not a supplied
    # benchmark task solution and deliberately does not expose correct targets.
    prefix = "CONTROL_POSITIVE=" + repr(positive) + "\n"
    suffix = '''
import os
result={
    "real_python_witness":True,
    "ifcopenshell_native_schema":ifc.schema,
    "linux_uid":os.getuid(),
    "linux_gid":os.getgid(),
    "has_pinned_readonly_worker":os.path.isfile("/worker.py"),
    "sandbox_source_clone_exists":os.path.isfile("/workspace/current.ifc"),
}
commit()
'''
    return (prefix + dedent(code).lstrip() + dedent(suffix).lstrip())


def deliberately_invalid_python(task_id: str, public_question: str,
                                case: str) -> str:
    """Real Docker failure controls: no sandbox escape, no private data."""
    if task_id != "geometry_test_14":
        raise ValueError("Negative transaction probes use pinned source Slab only")
    valid = developer_python_source(task_id, public_question, positive=True)
    if case == "without_commit":
        return valid.rsplit("commit()", 1)[0] + "result={'no_commit':True}\n"
    if case == "error_after_commit":
        return valid + "\nraise ValueError('deliberate_worker_error_after_commit')\n"
    if case == "unrelated_root":
        return (valid.rsplit("commit()", 1)[0] +
                "ifc.create_entity('IfcWall',GlobalId=ifcopenshell.guid.new(),"
                "Name='UNAUTHORIZED_RESEARCH_WALL')\ncommit()\n")
    if case == "source_noop":
        return "result={'original_unchanged':True}\ncommit()\n"
    if case == "sandbox_witness":
        # Uses the normal physically valid Slab mutation plus extra live
        # unprivileged process checks, no connection is attempted outside.
        return (valid.rsplit("commit()", 1)[0] +
                "import os\n"
                "result={'linux_uid':os.getuid(),"
                "'linux_gid':os.getgid(),"
                "'rootfs_write_denied':not os.access('/usr/bin',os.W_OK),"
                "'workspace_write_allowed':os.access('/workspace',os.W_OK),"
                "'unexpected_private_grader_mount':os.path.exists('/private-grader'),"
                "'worker_readable':os.access('/worker.py',os.R_OK)}\n"
                "commit()\n")
    raise ValueError("Unknown bounded source-native sandbox transaction probe")
