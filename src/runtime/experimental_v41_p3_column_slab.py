"""v0.41 original-public P3 trusted single Column/Slab whole-XML compiler.

Only exact three SHA-pinned original IFC4X3-mm source files.
External developer-owned native writer accepts a declarative ONE-object
additive graph diff, never Python, IFC mutator commands or guessed room edges.
Original IFC remains immutable, candidate IFC written to an unused path.
No original author evaluator, GT, LLM or task-solution geometry used.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.geometry
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

from src.runtime.ifc_projection import project_ifc
from src.runtime.xml_parser import parse_xml
from src.runtime.binder import bind_document
from src.runtime.semantic_graph import graph_diff
from src.runtime.transaction import stage_and_commit

PINS={
    "58833e0bdf80e2207b8c221fc8195e5411f9f94e0d7f1cb39633b3c447eb4767":
        ("geometry_test_02","Column",4,0),
    "8f1d9e885603f8680cb79f2a373fa36b4ecd52634ac920f2ec53c60ac465ad72":
        ("topological_test_02","Column",4,2),
    "29cd44b72639ba9573aa1698a4efab4adcfbc5461c19dd85259e6a9505d303e5":
        ("topological_test_04","Slab",7,1),
}
NS="{urn:bim-markup-bench:toy:v0}"


class P3NativeCreateError(ValueError):
    pass


@dataclass(frozen=True)
class P3View:
    xml:bytes
    task_id:str
    native_schema:str
    source_sha256:str
    original_native_sha256:str
    create_kind:str
    existing_native_slabs_not_model_visible:int


@dataclass(frozen=True)
class P3Commit:
    status:str
    task_id:str
    kind:str
    new_native_guid:str

    def as_dict(self)->dict:
        return {
            "status":self.status,
            "task_id":self.task_id,
            "new_native_kind":self.kind,
            "one_native_object_added":True,
            "only_complete_declarative_XML_authoring":True,
            "actual_original_task_solution":False,
        }


def _require(ok:bool,message:str):
    if not ok:raise P3NativeCreateError(message)


def file_hash(path:Path)->str:
    h=sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def check_p3_original_source(original_mm:Path,expected_sha:str,opened)->str:
    _require(
        Path(original_mm).is_file() and not Path(original_mm).is_symlink()
        and expected_sha in PINS and file_hash(original_mm)==expected_sha,
        "P3 must match exactly one of three immutable public original IFC SHA256 pins")
    _require(
        opened.schema=="IFC4X3" and abs(
            ifcopenshell.util.unit.calculate_unit_scale(opened)-.001)<1e-12,
        "P3 original source IFC must be IFC4X3 native millimetres")
    task,kind,walls,slabs=PINS[expected_sha]
    _require(len(opened.by_type("IfcWall"))==walls
             and len(opened.by_type("IfcSlab"))==slabs
             and len(opened.by_type("IfcBuildingStorey"))==2,
             "P3 pinned original native source Wall/Slab/Storey counts changed")
    _require(not opened.by_type("IfcRelSpaceBoundary"),
             "P3 source newly gained an unregistered explicit SpaceBoundary")
    return task


def project_p3_source(normalized_m:Path,*,original_native_sha256:str,
                      original_source_mm:Path)->P3View:
    original_source_mm=Path(original_source_mm)
    original=ifcopenshell.open(str(original_source_mm))
    task=check_p3_original_source(
        original_source_mm,original_native_sha256,original)
    normalized_m=Path(normalized_m)
    _require(normalized_m.is_file() and not normalized_m.is_symlink(),
             "P3 normalized native-metre source must be a real file")
    work=ifcopenshell.open(str(normalized_m))
    _require(work.schema=="IFC4X3" and abs(
        ifcopenshell.util.unit.calculate_unit_scale(work)-1.)<1e-12,
        "P3 normalized native worktree must be IFC4X3 metres")
    projected=project_ifc(normalized_m,strict_on_opaque=False)
    source_hash=file_hash(normalized_m)
    _require(projected.source.source_sha256==source_hash,
             "P3 projected source SHA changed mid-read")
    task_id,kind,expected_walls,opaque_slabs=PINS[original_native_sha256]
    root=etree.fromstring(projected.xml)
    _require(root.tag==NS+"Building"
             and root.get("sourceModelSha256")==source_hash,
             "P3 default full-declarative XML source lost exact root hash")
    elements=root.find(NS+"Elements")
    levels=root.find(NS+"Levels")
    _require(elements is not None and levels is not None
             and len(levels)==2
             and len(elements)==expected_walls
             and all(x.tag==NS+"Wall" and x.get("ifcGuid")
                     for x in elements),
             "P3 exact public source original typed Walls or native Slab opacity changed")
    _require(
        {x.get("ifcGuid") for x in elements}==
        {x.GlobalId for x in original.by_type("IfcWall")},
        "P3 source public Wall GUID coverage changed")
    _require(len(work.by_type("IfcSlab"))==opaque_slabs,
             "P3 normalized worktree native opaque Slab count drift")
    _require(file_hash(original_source_mm)==original_native_sha256,
             "P3 original immutable source changed during projection")
    return P3View(projected.xml,task,original.schema,
                  source_hash,original_native_sha256,kind,opaque_slabs)


def _native_body(model):
    contexts=[x for x in model.by_type("IfcGeometricRepresentationSubContext")
              if x.ContextIdentifier=="Body" and x.TargetView=="MODEL_VIEW"]
    _require(len(contexts)==1,
             "P3 original native IFC requires exactly one Body MODEL_VIEW context")
    return contexts[0]


def _preflight(source_m:Path,edited_xml:bytes,view:P3View):
    projected=project_ifc(source_m,strict_on_opaque=False)
    _require(projected.xml==view.xml,
             "P3 immutable original typed XML source projection changed")
    before_doc=parse_xml(view.xml,expected_source_sha256=view.source_sha256)
    after_doc=parse_xml(edited_xml,expected_source_sha256=view.source_sha256)
    before=bind_document(before_doc,projection=projected)
    after=bind_document(after_doc,projection=projected,verify_native_edges=False)
    delta=graph_diff(before.graph,after.graph)
    _require(len(delta.added_nodes)==1
             and not (delta.removed_nodes or delta.changed_nodes
                      or delta.removed_edges)
             and len(delta.added_edges)==1,
             "P3 requires exactly one new native Column/Slab and zero unrelated XML changes")
    name=delta.added_nodes[0]
    node=after.graph.by_id()[name]
    _require(node.kind==view.create_kind
             and node.provenance=="deterministic_new"
             and node.ifc_guid not in {x.ifc_guid for x in before.graph.nodes},
             "P3 only creates one deterministic native Column or Slab (no arbitrary GUID)")
    attrs=dict(node.attributes)
    _require(attrs.get("id")==name,"P3 stable declarative XML node id not preserved")
    edge=delta.added_edges[0]
    _require(edge.relation=="in_storey" and edge.target==name
             and edge.source==attrs.get("level") and edge.ownership=="derived",
             "P3 new IFC object must have one real original Storey relationship")
    level=before.graph.by_id().get(attrs["level"])
    _require(level is not None and level.kind=="Level"
             and level.provenance=="existing_source",
             "P3 new object must reference an original native storey")
    model=ifcopenshell.open(str(source_m))
    storey=model.by_guid(level.ifc_guid)
    _require(storey and storey.is_a("IfcBuildingStorey"),
             "P3 original native level GUID missing")
    _require(set(attrs)==(
        {"id","level","x","y","z","width","depth","height"}
        if node.kind=="Column" else
        {"id","level","x","y","z","width","depth","thickness"}),
        "P3 only accepts known declarative box dimensions and existing Storey")
    floats={}
    for key in ("x","y","z","width","depth",
                "height" if node.kind=="Column" else "thickness"):
        number=float(attrs[key])
        _require(math.isfinite(number) and abs(number)<=10000,
                 "P3 geometry cannot contain nonfinite or unbounded coordinates")
        floats[key]=number
    depth=floats.get("height",floats.get("thickness"))
    for key,value in (("width",floats["width"]),
                      ("depth",floats["depth"]),("height/thickness",depth)):
        _require(.01<=value<=50,
                 "P3 new box "+key+" must be physically bounded and non-degenerate")
    _require(file_hash(source_m)==view.source_sha256,
             "P3 normalized original source altered during preflight")
    return model,storey,node,floats


def compile_p3_create(
        source_m:Path,edited_xml:bytes,destination_m:Path,*,
        original_native_sha256:str,original_source_mm:Path)->P3Commit:
    source_m,destination_m=Path(source_m),Path(destination_m)
    _require(source_m.is_file() and not source_m.is_symlink()
             and not destination_m.exists() and not destination_m.is_symlink()
             and source_m.resolve()!=destination_m.resolve(),
             "P3 source/candidate IFC must be different existing/unused paths")
    view=project_p3_source(
        source_m,original_native_sha256=original_native_sha256,
        original_source_mm=original_source_mm)
    model,storey,node,attrs=_preflight(source_m,edited_xml,view)
    known_roots={x.GlobalId for x in model.by_type("IfcRoot")}
    _require(node.ifc_guid not in known_roots,
             "Deterministic newly created P3 IFC GUID already exists")
    body=_native_body(model)
    x,y,z=attrs["x"],attrs["y"],attrs["z"]
    width,depth=attrs["width"],attrs["depth"]
    high=attrs.get("height",attrs.get("thickness"))
    def writer(staging:Path):
        product=ifcopenshell.api.root.create_entity(
            model,ifc_class="Ifc"+node.kind,
            name="Research-only complete declarative XML "+node.kind)
        product.GlobalId=node.ifc_guid
        if node.kind=="Slab":
            product.PredefinedType="FLOOR"
        profile=model.createIfcRectangleProfileDef(
            "AREA",None,None,width,depth)
        representation=ifcopenshell.api.geometry.add_profile_representation(
            model,context=body,profile=profile,depth=high)
        ifcopenshell.api.geometry.assign_representation(
            model,product=product,representation=representation)
        matrix=np.eye(4)
        matrix[:3,3]=(x+width/2,y+depth/2,z)
        ifcopenshell.api.geometry.edit_object_placement(
            model,product=product,matrix=matrix,is_si=True)
        ifcopenshell.api.spatial.assign_container(
            model,products=[product],relating_structure=storey)
        model.write(str(staging))
    def validator(staging:Path):
        _require(file_hash(source_m)==view.source_sha256,
                 "P3 source normalized IFC altered during native writer")
        output=ifcopenshell.open(str(staging))
        _require(output.schema=="IFC4X3"
                 and len(output.by_type("Ifc"+node.kind))==
                     len(ifcopenshell.open(str(source_m)).by_type("Ifc"+node.kind))+1
                 and output.by_guid(node.ifc_guid) is not None,
                 "P3 native staged output omitted new original target class")
    stage_and_commit(destination_m,writer,validator)
    _require(file_hash(original_source_mm)==original_native_sha256,
             "P3 original immutable public source changed after native commit")
    return P3Commit(
        "COMMITTED_ORIGINAL_IFC4X3_P3_SINGLE_COLUMN_SLAB_NATIVE_XML_V041",
        view.task_id,node.kind,node.ifc_guid)
