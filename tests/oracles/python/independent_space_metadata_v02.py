"""Independent imperative IfcOpenShell v0.2 new Space metadata reference.

No imports or invocation of the D0 XML compiler, v0.2 XML parser,
Space metadata mutation implementation, or source-snapshot validator.
Accepts independently specified Python values; creates native IFC objects
directly. GlobalId derivation follows the shared, frozen cross-arm contract.
"""
from __future__ import annotations

import uuid

import ifcopenshell
import numpy as np

from tests.oracles.python.independent_space_partition import _bbox

_SEED=uuid.UUID("ae7d2594-ff47-49fd-aefe-2827043dc649")


def _guid(source_sha,space_guid,kind):
    return ifcopenshell.guid.compress(
        uuid.uuid5(_SEED,
            f"v0.2-explicit-space-metadata:{source_sha}:{space_guid}:{kind}").hex)


def independent_native_space_metadata(joined_ifc,output_ifc,source_sha,
                                      far_guid,*,name,long_name,type_name,
                                      reference,net_area,net_volume):
    """Imperative, independently authored, source-only native IFC reference."""
    f=ifcopenshell.open(str(joined_ifc))
    if f.schema!="IFC4X3":
        raise ValueError("I0 new room metadata only supports IFC4X3")
    try:
        far=f.by_guid(far_guid)
    except RuntimeError as exc:
        raise ValueError("I0 new Space missing") from exc
    if not far.is_a("IfcSpace") or far.IsTypedBy or far.IsDefinedBy:
        raise ValueError("I0 expected untyped newly partitioned Space")
    for old in f.by_type("IfcSpace"):
        if old.GlobalId==far_guid:continue
        if old.Name==name:
            raise ValueError("I0 new Space name not independently unique")
        for rel in old.IsDefinedBy:
            pset=rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet"):
                for prop in pset.HasProperties:
                    if prop.Name=="Reference" and prop.NominalValue:
                        if str(prop.NominalValue.wrappedValue)==reference:
                            raise ValueError("I0 room-specific Reference conflict")
    if type_name in {x.Name for x in f.by_type("IfcSpaceType")}:
        raise ValueError("I0 new SpaceType name not unique")
    lo,hi=_bbox(far)
    area=float((hi[0]-lo[0])*(hi[1]-lo[1]))
    volume=float(np.prod(hi-lo))
    if abs(area-net_area)>1e-7 or abs(volume-net_volume)>1e-7:
        raise ValueError("I0 QTO does not match independently measured geometry")
    types=("TYPE","TYPE_REL","PSET_COMMON","PSET_COMMON_REL",
           "PSET_HEATER","PSET_HEATER_REL","QTO","QTO_REL")
    ids={role:_guid(source_sha,far_guid,role) for role in types}
    for gid in ids.values():
        try:f.by_guid(gid)
        except RuntimeError:pass
        else:raise ValueError("I0 new-room GlobalId collision")
    far.Name=name
    far.LongName=long_name
    far.PredefinedType="NOTDEFINED"
    far.CompositionType="ELEMENT"
    room_type=f.createIfcSpaceType(
        GlobalId=ids["TYPE"],Name=type_name,PredefinedType="NOTDEFINED")
    f.createIfcRelDefinesByType(
        GlobalId=ids["TYPE_REL"],RelatedObjects=(far,),
        RelatingType=room_type)
    props_common=(
        f.createIfcPropertySingleValue(
            Name="Reference",NominalValue=f.createIfcIdentifier(reference)),
        f.createIfcPropertySingleValue(
            Name="IsExternal",NominalValue=f.createIfcBoolean(False)),
    )
    props_heat=(f.createIfcPropertySingleValue(
        Name="Reference",NominalValue=f.createIfcIdentifier(reference)),)
    for name_suffix,relation_suffix,pset_name,props in (
        ("PSET_COMMON","PSET_COMMON_REL","Pset_SpaceCommon",props_common),
        ("PSET_HEATER","PSET_HEATER_REL","Pset_SpaceHeaterTypeCommon",props_heat),
    ):
        pset=f.createIfcPropertySet(
            GlobalId=ids[name_suffix],Name=pset_name,HasProperties=props)
        f.createIfcRelDefinesByProperties(
            GlobalId=ids[relation_suffix],RelatingPropertyDefinition=pset,
            RelatedObjects=(far,))
    quantity=f.createIfcElementQuantity(
        GlobalId=ids["QTO"],Name="Qto_SpaceBaseQuantities",
        Quantities=(
            f.createIfcQuantityArea(Name="NetFloorArea",AreaValue=area),
            f.createIfcQuantityVolume(Name="NetVolume",VolumeValue=volume)))
    f.createIfcRelDefinesByProperties(
        GlobalId=ids["QTO_REL"],RelatingPropertyDefinition=quantity,
        RelatedObjects=(far,))
    f.write(str(output_ifc))
    return ids
