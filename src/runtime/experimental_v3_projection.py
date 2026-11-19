"""Prospective v0.3 READ-ONLY projection of original mapped Column envelopes.

An IfcColumn omitted by v0.1 because its shape uses a Revit mapped solid can
still be TRANSLATED or DELETED safely while its underlying opaque shape stays
native. We expose an *axis-aligned world-space bounding envelope*, NOT a
lossless IFC profile/shape reconstruction. Never execute a box re-creation of
a mapped source merely because it is projected by this module.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
from lxml import etree

from src.runtime.ifc_projection import (
    Projection,OpaqueReference,UnsupportedIFCGeometry,project_ifc,
    _id,_number,
)
from src.runtime.markup_normal_form import NS
from src.runtime.xml_parser import parse_xml
from src.runtime.ifc_snapshot import snapshot_source
from src.runtime.experimental_v2_column import _world_bbox


class V3ProjectionError(ValueError):
    pass


def project_ifc_v3(source:Path)->Projection:
    original=project_ifc(source)
    root=etree.fromstring(original.xml)
    elements=root.find("{"+NS+"}Elements")
    level_ids={
        x.attrib["ifcGuid"]:x.attrib["id"]
        for x in root.findall(".//{"+NS+"}Level")
    }
    by_guid=dict(original.projected_global_ids)
    f=ifcopenshell.open(str(source))
    included=[]
    for column in sorted(f.by_type("IfcColumn"),key=lambda c:c.GlobalId):
        if column.GlobalId in by_guid:
            continue
        if column.ObjectPlacement is None or column.Representation is None:
            continue
        storey=ifcopenshell.util.element.get_container(column)
        if storey is None or storey.GlobalId not in level_ids:
            continue
        try:
            low,high=_world_bbox(column)
            dims=[high[i]-low[i] for i in range(3)]
            if any(dim<=0.02 or dim>1000 for dim in dims):
                continue
            attrs={
                "id":_id(column),
                "ifcGuid":column.GlobalId,
                "level":level_ids[storey.GlobalId],
                "x":_number(low[0]),"y":_number(low[1]),"z":_number(low[2]),
                "width":_number(dims[0]),"depth":_number(dims[1]),
                "height":_number(dims[2]),
            }
            if attrs["id"] in by_guid.values():
                raise V3ProjectionError("Existing projected ID collision")
            etree.SubElement(elements,"{"+NS+"}Column",attrib=attrs)
            by_guid[column.GlobalId]=attrs["id"]
            included.append(column.GlobalId)
        except V3ProjectionError:
            raise
        except (UnsupportedIFCGeometry,ValueError,RuntimeError,TypeError,AttributeError):
            # Unmanaged opaque IFC source remains protected; never fabricate
            # a projected local ID from unreadable or nonfinite geometry.
            continue

    if not included:
        return original
    xml=etree.tostring(root,encoding="utf8",xml_declaration=True,pretty_print=True)
    parse_xml(xml,expected_source_sha256=original.source.source_sha256)
    unsupported=Counter(dict(original.unsupported_class_counts))
    supported=Counter(dict(original.supported_class_counts))
    if unsupported["IfcColumn"]<len(included):
        raise V3ProjectionError("Reported v0.1 opaque Column inventory mismatch")
    unsupported["IfcColumn"]-=len(included)
    if not unsupported["IfcColumn"]:
        del unsupported["IfcColumn"]
    supported["IfcColumn"]+=len(included)
    out=replace(
        original,xml=xml,
        projected_global_ids=tuple(sorted(by_guid.items())),
        opaque_references=tuple(x for x in original.opaque_references
                                if x.ifc_guid not in included),
        supported_class_counts=tuple(sorted(supported.items())),
        unsupported_class_counts=tuple(sorted(unsupported.items())),
    )
    if snapshot_source(source).source_sha256!=original.source.source_sha256:
        raise V3ProjectionError("Input source changed during v0.3 read-only projection")
    return out
