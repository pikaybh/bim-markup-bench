"""Independent developer-authored imperative native IFC Wall I0, v0.27.

This is a separate native IfcOpenShell implementation, NOT an alias/import
of the declarative XML trusted compiler or subprocess worker. Uses only the
public original IFC and the PUBLIC task's Wall GUID. It preserves the
original IFC4X3 millimetre file and creates a separate output.
No original benchmark scorer or hidden ground-truth imports.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.util.unit


class OriginalWallI0Blocked(ValueError):
    pass


def _sha(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def independent_original_connected_wall_i0(
    source:Path, public_wall_guid:str, output:Path,
)->dict:
    if (not source.is_file() or source.is_symlink()
        or output.exists() or output.is_symlink()):
        raise OriginalWallI0Blocked("Source input absent or result overwrite attempted")
    before=_sha(source)
    source_file=ifcopenshell.open(str(source))
    if (source_file.schema!="IFC4X3" or
        abs(ifcopenshell.util.unit.calculate_unit_scale(source_file)-.001)>1e-12):
        raise OriginalWallI0Blocked("Actual original public IFC is not IFC4X3 millimetres")
    try:
        subject=source_file.by_guid(public_wall_guid)
    except (RuntimeError,ValueError) as exc:
        raise OriginalWallI0Blocked("PUBLIC target Wall absent") from exc
    if not subject.is_a("IfcWall") or subject.HasOpenings:
        raise OriginalWallI0Blocked("PUBLIC target is not a plain original Wall")
    # Convert the same original file/unit envelope as the trusted
    # declarative IFC4X3 session before any native source edit.
    f=ifcopenshell.util.unit.convert_file_length_units(source_file,"METER")
    wall=f.by_guid(public_wall_guid)
    references=list(f.get_inverse(wall))
    paths=[r for r in references if r.is_a("IfcRelConnectsPathElements")]
    owned_properties=[r for r in references if r.is_a("IfcRelDefinesByProperties")]
    if (len(references)!=9 or len(paths)!=2 or len(owned_properties)!=3
        or not all(r.RelatedElement==wall and r.RelatingElement.is_a("IfcWall")
                   for r in paths)):
        raise OriginalWallI0Blocked("Native original public Wall relationships unexpected")
    for rel in owned_properties:
        prop_set=rel.RelatingPropertyDefinition
        if (tuple(rel.RelatedObjects)!=(wall,) or
            not prop_set.is_a("IfcPropertySet")
            or tuple(f.get_inverse(prop_set))!=(rel,)):
            raise OriginalWallI0Blocked("Original Wall properties are not privately owned")
    shape=wall.Representation
    placement=wall.ObjectPlacement
    if shape is None or placement is None or len(shape.Representations)!=2:
        raise OriginalWallI0Blocked("Original Wall physical representation is not verified")
    source_representations=list(shape.Representations)
    rep_ids={rep.id() for rep in source_representations}
    native_subtree={x.id() for x in f.traverse(shape)}
    native_subtree.update(x.id() for x in f.traverse(placement))
    protected_ids={x.id() for x in f.by_type("IfcRoot")}
    layers=[l for l in f.by_type("IfcPresentationLayerAssignment")
            if any(rep in l.AssignedItems for rep in source_representations)]
    if (len(layers)!=1 or
        len(layers[0].AssignedItems)<=2 or
        not rep_ids.issubset({item.id() for item in layers[0].AssignedItems})):
        raise OriginalWallI0Blocked("Original shared representation layer is not bounded")
    for rel in paths:
        f.remove(rel)
    for rel in owned_properties:
        ifcopenshell.api.pset.remove_pset(
            f,product=wall,pset=rel.RelatingPropertyDefinition)
    layer=layers[0]
    layer.AssignedItems=tuple(item for item in layer.AssignedItems
                              if item.id() not in rep_ids)
    f.remove(wall)
    # Independently written reference-count sweep: remove only the former
    # subject's exclusively unowned native nonroot geometry. Preserve every
    # shared representation/context/placement that another IFC entity uses.
    remaining=native_subtree-protected_ids
    while True:
        removed_this_round=0
        for entity_id in sorted(tuple(remaining),reverse=True):
            try:
                entity=f.by_id(entity_id)
            except RuntimeError:
                remaining.discard(entity_id)
                continue
            if f.get_total_inverses(entity)!=0:
                continue
            f.remove(entity)
            remaining.discard(entity_id)
            removed_this_round+=1
        if not removed_this_round:
            break
    with TemporaryDirectory(prefix="bmb-v027-independent-original-I0-") as temp:
        metric_path=Path(temp)/"native_m.ifc"
        f.write(str(metric_path))
        # Independent I0 restores original millimetre units after native edit,
        # without using or importing any declarative compiler implementation.
        output_file=ifcopenshell.util.unit.convert_file_length_units(
            ifcopenshell.open(str(metric_path)),"MILLIMETER")
        if (output_file.schema!="IFC4X3"
            or abs(ifcopenshell.util.unit.calculate_unit_scale(output_file)-.001)>1e-12):
            raise OriginalWallI0Blocked("Independent I0 native output lost original units")
        output.parent.mkdir(parents=True,exist_ok=True)
        output_file.write(str(output))
    if _sha(source)!=before:
        raise OriginalWallI0Blocked("Source original IFC was mutated")
    post=ifcopenshell.open(str(output))
    result_ids={entity.GlobalId for entity in post.by_type("IfcProduct")}
    return {
        "status":"INDEPENDENT_ORIGINAL_NATIVE_CONNECTED_WALL_DELETE",
        "original_source_sha256":before,
        "native_output_sha256":_sha(output),
        "original_public_wall_absent":public_wall_guid not in result_ids,
        "original_other_IFC_Product_count":len(result_ids),
    }


def main()->None:
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    opts=a.parse_args()
    guid=sys.stdin.readline().strip()
    if len(guid)!=22:
        a.error("Expected public original Wall GUID on stdin")
    print(json.dumps(
        independent_original_connected_wall_i0(opts.source,guid,opts.output),
        ensure_ascii=False,sort_keys=True
    ),flush=True)


if __name__=="__main__":
    main()
