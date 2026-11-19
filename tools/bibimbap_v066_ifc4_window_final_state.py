"""v0.66 OFFLINE, source-neutral declarative Window group MOVE / DELETE.

No task ID, target GUID, author scorer, private expected result, operation XML
or callable mutator exposed to the agent. Model-facing output is a complete
BuildingState XML (or complete managed final-state XML); trusted runtime
deduces one supported edit by comparing source/final physical element states.

Supported: IFC4/IFC4X3 metre/mm with hosted Window/Opening and optionally geometric
detail proxies unambiguously grouped by window center. Moving group translates
Opening and independent detail placements, Window inherits Opening. Removing
group cleans native detail, Window, Opening and attached source relations.

Not a general IFC editor. Reject shared detail placement and ambiguous proxy
association, mixed operations, arbitrary geometry, unsynchronized assemblies.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.api
import ifcopenshell.util.unit
import ifcopenshell.util.placement
from lxml import etree
import numpy as np

from src.security.agent_boundary import check_xml_bytes
from tools.bibimbap_matched25_tools import file_hash
def _mesh_bounds(entity):
    """Generic native IFC product shape in physical world metres, no task ID."""
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,entity)
    xyz=list(shape.geometry.verts)
    require(xyz and len(xyz)%3==0
            and all(math.isfinite(float(x)) and abs(float(x)) < 1e4 for x in xyz),
            "Missing/bad original IFC physical native mesh")
    return tuple((round(min(xyz[k::3]),6),round(max(xyz[k::3]),6))
                 for k in range(3))


NS = "urn:bim-markup-bench:source-neutral:window-final-state:v066"
Q = "{" + NS + "}"
MAX_XML = 240000
MAX_MANAGED = 35000
MAX_WORLD_SHIFT_M = 1.0
STATUS = "V066_SYNTHETIC_IFC4_WINDOW_FINAL_STATE_COMPLETE_MOVE_DELETE_PASS"


class FinalWindow066Error(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FinalWindow066Error(message)


def _xml_parser():
    return etree.XMLParser(resolve_entities=False, load_dtd=False,
                           no_network=True, huge_tree=False, recover=False)


def _number(value):
    x = float(value)
    require(math.isfinite(x) and abs(x) < 100000,
            "Unbounded source or candidate world coordinate")
    return f"{x:.6f}"


def source(source_path: Path, source_sha: str):
    path = Path(source_path)
    require(path.is_file() and not path.is_symlink()
            and len(source_sha) == 64 and file_hash(path) == source_sha,
            "Immutable SHA-verified original IFC required")
    model = ifcopenshell.open(str(path))
    require(model.schema in ("IFC4", "IFC4X3")
            and ifcopenshell.util.unit.calculate_unit_scale(model) in (1., .001),
            "Only supported IFC4/IFC4X3 metre/millimetre source allowed")
    require(len(model.by_type("IfcWindow")) >= 2,
            "Need at least two original Windows for nontrivial independent scope")
    return model


def groups(source_model):
    """Find complete nonoverlapping hosted Window+Opening(+aligned details)."""
    result = {}
    windows = sorted(source_model.by_type("IfcWindow"),
                     key=lambda w: w.GlobalId)
    proxies = list(source_model.by_type("IfcBuildingElementProxy"))
    allocated = set()
    for w in windows:
        require(len(w.FillsVoids) == 1
                and w.FillsVoids[0].RelatingOpeningElement.is_a("IfcOpeningElement"),
                "Exactly one source hosted Window -> Opening")
        op = w.FillsVoids[0].RelatingOpeningElement
        require(len(op.VoidsElements) == 1
                and len(op.HasFillings) == 1
                and op.HasFillings[0].RelatedBuildingElement == w
                and op.VoidsElements[0].RelatingBuildingElement.is_a("IfcWall"),
                "Source Opening/Window/host Wall native topology invalid")
        require(w.ObjectPlacement is not None
                and op.ObjectPlacement is not None
                and w.ObjectPlacement.PlacementRelTo == op.ObjectPlacement,
                "Source Window must inherit exclusive Opening object placement")
        center = sum(_mesh_bounds(w)[0]) / 2
        linked = sorted(
            [p for p in proxies
             if abs(sum(_mesh_bounds(p)[0])/2-center) < .015],
            key=lambda p: p.GlobalId,
        )
        require(not {p.GlobalId for p in linked} & allocated,
                "Source detail ambiguous between hosted Windows")
        allocated.update(p.GlobalId for p in linked)
        members = (w, op, *linked)
        points = []
        for p in members[1:]:
            require(p.ObjectPlacement is not None
                    and p.ObjectPlacement.is_a("IfcLocalPlacement")
                    and p.ObjectPlacement.RelativePlacement is not None
                    and p.ObjectPlacement.RelativePlacement.is_a("IfcAxis2Placement3D"),
                    "Only original local 3D placement supported")
            point = p.ObjectPlacement.RelativePlacement.Location
            require(len(point.Coordinates) == 3
                    and len(source_model.get_inverse(point)) == 1,
                    "Original Opening/detail placement point must be exclusive")
            points.append(point)
        require(len(set(p.id() for p in points)) == len(points),
                "Source shared Window detail point forbidden")
        result[w.GlobalId] = {
            "window": w, "opening": op, "details": tuple(linked),
            "members": members, "points": tuple(points),
            "host": op.VoidsElements[0].RelatingBuildingElement,
        }
    require(all(p.GlobalId in allocated for p in proxies)
            and len({p.GlobalId for group in result.values()
                     for p in group["members"]}) == sum(
                         len(g["members"]) for g in result.values()),
            "Ambiguous/unmanaged original Window detail/proxy set")
    return result


def _member_records(model, assembly):
    for g in assembly.values():
        for e in g["members"]:
            box = _mesh_bounds(e)
            yield e, {
                "ifcGuid": e.GlobalId, "ifcClass": e.is_a(),
                "present": "true",
                "finalWorldMinXM": _number(box[0][0]),
                "finalWorldMinYM": _number(box[1][0]),
                "finalWorldMinZM": _number(box[2][0]),
            }


def _base(source_path, source_sha):
    f = source(source_path, source_sha)
    g = groups(f)
    root = etree.Element(Q+"BuildingState", nsmap={None: NS}, attrib={
        "version": "0.66",
        "representation": "D_COMPLETE_SOURCE_WINDOW_FINAL_STATE",
        "originalIFCSha256": source_sha,
        "sourceIFCSchema": f.schema,
        "sourceLengthUnit": "MILLIMETRE" if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)<1e-12 else "METRE",
        "worldCoordinates": "METRE",
        "managedBoundary": "ALL_SOURCE_WINDOW_OPENING_AND_ASSOCIATED_DETAIL_PRODUCTS",
    })
    opaque = etree.SubElement(root, Q+"OriginalNativeIFCSource", attrib={
        "sourceIFCSha256": source_sha,
        "sourceRootCount": str(len(f.by_type("IfcRoot"))),
    })
    for e in sorted(f.by_type("IfcProduct"), key=lambda x:x.GlobalId):
        attrs = {"ifcGuid": e.GlobalId, "ifcClass": e.is_a(),
                 "originalName": str(e.Name or "")}
        if e.Representation is not None:
            bbox = _mesh_bounds(e)
            for axis, j in zip("XYZ", range(3)):
                attrs[f"originalMin{axis}M"] = _number(bbox[j][0])
                attrs[f"originalMax{axis}M"] = _number(bbox[j][1])
        if e.is_a("IfcWindow"):
            op = e.FillsVoids[0].RelatingOpeningElement
            attrs["hostedOpeningGuid"] = op.GlobalId
            attrs["hostWallGuid"] = op.VoidsElements[0].RelatingBuildingElement.GlobalId
        etree.SubElement(opaque, Q+"SourceProduct", attrib=attrs)
    roster = etree.SubElement(root, Q+"ManagedElements", attrib={
        "boundary": "ALL_SOURCE_WINDOW_OPENING_AND_ASSOCIATED_DETAIL_PRODUCTS",
    })
    for _, attrs in sorted(_member_records(f, g), key=lambda item:item[0].GlobalId):
        etree.SubElement(roster, Q+"Element", attrib=attrs)
    return f, g, root


def full_source_state(source_path: Path, source_sha: str) -> bytes:
    _, _, doc = _base(source_path, source_sha)
    raw = etree.tostring(doc, xml_declaration=True, encoding="utf8")
    require(len(raw) <= MAX_XML, "Source full state exceeds XML size bound")
    return raw


def managed_source_state(source_path: Path, source_sha: str) -> bytes:
    full = full_source_state(source_path, source_sha)
    state = etree.fromstring(full, _xml_parser())
    root = etree.Element(Q+"ManagedFinalState", nsmap={None: NS}, attrib={
        "version": "0.66",
        "representation": "D_MANAGED_SOURCE_WINDOW_FINAL_STATE",
        "originalIFCSha256": source_sha,
        "sourceBuildingStateSha256": sha256(full).hexdigest(),
        "managedBoundary": "ALL_SOURCE_WINDOW_OPENING_AND_ASSOCIATED_DETAIL_PRODUCTS",
    })
    for e in state[1]:
        etree.SubElement(root, Q+"Element", attrib=dict(e.attrib))
    data = etree.tostring(root, xml_declaration=True, encoding="utf8")
    require(len(data) <= MAX_MANAGED, "Source managed state exceeds XML size bound")
    return data


def _parse_roster(original_entries, submitted, assembly):
    old = list(original_entries)
    new = list(submitted)
    require(len(old) == len(new), "Source-managed physical state omitted entities")
    before = {}
    after = {}
    for prev, nxt in zip(old, new):
        require(prev.tag == Q+"Element" and nxt.tag == Q+"Element"
                and len(nxt) == 0
                and not (nxt.text or "").strip()
                and not (nxt.tail or "").strip()
                and set(nxt.attrib) == set(prev.attrib)
                and nxt.get("ifcGuid") == prev.get("ifcGuid")
                and nxt.get("ifcClass") == prev.get("ifcClass")
                and nxt.get("present") in ("true", "false"),
                "Source physical roster class/GUID/attributes/order changed")
        for k in ("finalWorldMinXM", "finalWorldMinYM", "finalWorldMinZM"):
            require(nxt.get(k) == _number(nxt.get(k)),
                    "Noncanonical world-coordinate edited XML")
        guid = prev.get("ifcGuid")
        before[guid] = prev
        after[guid] = nxt
    changes = []
    for guid, group in sorted(assembly.items()):
        members = [p.GlobalId for p in group["members"]]
        flags = [after[p].get("present") for p in members]
        require(len(set(flags)) == 1,
                "Window/Opening/associated detail objects must share final presence")
        if flags[0] == "false":
            require(all(
                after[p].get(k) == before[p].get(k)
                for p in members
                for k in ("finalWorldMinXM", "finalWorldMinYM","finalWorldMinZM")
            ), "Deleted group cannot simultaneously move")
            changes.append(("delete", guid, (0., 0., 0.)))
            continue
        deltas = [
            tuple(round(float(after[p].get(k))-float(before[p].get(k)), 6)
                  for k in ("finalWorldMinXM", "finalWorldMinYM","finalWorldMinZM"))
            for p in members
        ]
        require(all(v == deltas[0] for v in deltas),
                "Window/Opening/details must translate together in final world state")
        require(deltas[0][2] == 0.,
                "Only horizontal hosted Window assemblies may translate")
        if any(v != 0. for v in deltas[0]):
            require(0.01 <= math.hypot(*deltas[0][:2]) <= MAX_WORLD_SHIFT_M,
                    "Nontrivial bounded world Window motion required")
            changes.append(("move", guid, deltas[0]))
    require(len(changes) == 1, "Exactly one source assembly changes final state")
    return {"kind": changes[0][0],
            "window_guid": changes[0][1],
            "world_m": changes[0][2]}


def parse_full_state(source_path:Path, source_sha:str, raw:bytes):
    require(isinstance(raw,bytes) and 0 < len(raw) <= MAX_XML,
            "Edited full XML bytes invalid or exceed size bound")
    check_xml_bytes(raw)
    _, groups_source, doc = _base(source_path, source_sha)
    edited = etree.fromstring(raw, _xml_parser())
    require(edited.tag == doc.tag
            and dict(edited.attrib) == dict(doc.attrib)
            and len(edited) == 2
            and not (edited.text or "").strip()
            and etree.tostring(edited[0],method="c14n")
            == etree.tostring(doc[0],method="c14n")
            and edited[1].tag == doc[1].tag
            and dict(edited[1].attrib) == dict(doc[1].attrib),
            "Original native source opaque provenance changed")
    return _parse_roster(doc[1], edited[1], groups_source)


def expand_managed_state(source_path:Path, source_sha:str, raw:bytes):
    require(isinstance(raw,bytes) and 0 < len(raw) <= MAX_MANAGED,
            "Managed XML bytes invalid or exceed size bound")
    check_xml_bytes(raw)
    full = full_source_state(source_path, source_sha)
    old = etree.fromstring(full, _xml_parser())
    node = etree.fromstring(raw, _xml_parser())
    require(node.tag == Q+"ManagedFinalState"
            and dict(node.attrib) == {
                "version": "0.66",
                "representation": "D_MANAGED_SOURCE_WINDOW_FINAL_STATE",
                "originalIFCSha256": source_sha,
                "sourceBuildingStateSha256": sha256(full).hexdigest(),
                "managedBoundary": "ALL_SOURCE_WINDOW_OPENING_AND_ASSOCIATED_DETAIL_PRODUCTS",
            } and not (node.text or "").strip()
            and not (node.tail or "").strip(),
            "Managed XML source anchoring changed")
    g = groups(source(source_path, source_sha))
    parsed = _parse_roster(old[1], node, g)
    for item, new in zip(old[1], node):
        item.attrib.update(new.attrib)
    expanded = etree.tostring(old, xml_declaration=True, encoding="utf8")
    require(parse_full_state(source_path, source_sha, expanded) == parsed,
            "Managed final-state expansion changed source physical semantics")
    return expanded, parsed


def _native_apply_move(model, group, world_m):
    """Trusted compiler only: original local coordinates, not XML commands."""
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    delta = np.array(world_m, dtype=float) / scale
    for part in group["members"][1:]:
        place = part.ObjectPlacement
        parent = place.PlacementRelTo
        parent_rotation = (ifcopenshell.util.placement.get_local_placement(parent)
                           [:3, :3] if parent else np.eye(3))
        local_delta = np.linalg.solve(parent_rotation, delta)
        point = place.RelativePlacement.Location
        values = np.array(point.Coordinates,dtype=float)+local_delta
        require(np.all(np.isfinite(values))
                and np.max(np.abs(values)) < 1e7,
                "Native placement translation unbounded")
        point.Coordinates = tuple(float(v) for v in values)


def _native_apply_delete(model, group):
    """Trusted runtime only: cascade geometries, fill/void and other relations."""
    for product in (*group["details"], group["window"], group["opening"]):
        ifcopenshell.api.run("root.remove_product", model, product=product)


def compile_final_state(source_path:Path, source_sha:str, edited_xml:bytes,
                        output_path:Path, *,managed=False):
    out = Path(output_path)
    require(out.parent.is_dir() and not out.parent.is_symlink()
            and not out.exists() and not out.is_symlink()
            and out.resolve() != Path(source_path).resolve(),
            "New isolated source-preserving native IFC output required")
    if managed:
        _, parsed = expand_managed_state(source_path, source_sha, edited_xml)
    else:
        parsed = parse_full_state(source_path, source_sha, edited_xml)
    f = source(source_path,source_sha)
    g = groups(f)
    selection = g[parsed["window_guid"]]
    if parsed["kind"] == "move":
        _native_apply_move(f, selection, parsed["world_m"])
    else:
        _native_apply_delete(f, selection)
    f.write(str(out))
    require(out.is_file() and file_hash(source_path) == source_sha,
            "Trusted IFC compiler altered source")
    return parsed
