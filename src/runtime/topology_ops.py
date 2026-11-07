"""Conservative, testable IFC topology operations behind a declarative XML source.

Supported G1 slice: remove a single existing Window (not its opening or wall),
move a rectangular hosted Opening and its relative Window/Door placement, and
add/remove simple no-geometry IfcRelConnectsElements between meeting walls.

Unrepresented IfcSpace semantics and complex hosted geometry remain blockers.
None of these functions are exposed to the model authoring XML.
"""
from __future__ import annotations

import math
import uuid

import ifcopenshell
import ifcopenshell.api.root
import ifcopenshell.util.placement
import numpy as np

from src.runtime.ast import BuildingDocument
from src.runtime.binder import BindingEvidence
from src.runtime.ifc_mutations import Mutation, UnsupportedIFCMutation, by_guid_or_none
from src.runtime.semantic_graph import GraphDelta, GraphEdge
from src.runtime.ifc_projection import _body_extrusion, _rect_extents, _m, _world

REL_NAMESPACE=uuid.UUID("38502454-46ea-44b8-8e87-6c6a7e66c111")
TOL=1e-6


def _native_connections(f):
    return [r for r in f.by_type("IfcRelConnectsElements")]


def _one_connection(f,source_guid:str,target_guid:str):
    found=[r for r in _native_connections(f)
           if r.RelatingElement and r.RelatedElement
           and r.RelatingElement.GlobalId==source_guid
           and r.RelatedElement.GlobalId==target_guid]
    if len(found)>1:
        raise UnsupportedIFCMutation("Duplicate native wall connection endpoints")
    return found[0] if found else None


def _native_host(opening):
    rel=list(opening.VoidsElements)
    if len(rel)!=1 or not rel[0].RelatingBuildingElement.is_a("IfcWall"):
        raise UnsupportedIFCMutation("Opening must have one native wall void host")
    return rel[0].RelatingBuildingElement


def _plain_opening_local_frame(opening,wall):
    place=opening.ObjectPlacement
    if not place or not place.is_a("IfcLocalPlacement") or place.PlacementRelTo!=wall.ObjectPlacement:
        raise UnsupportedIFCMutation("Opening placement must be relative to its native Wall placement")
    frame=place.RelativePlacement
    if not frame or not frame.is_a("IfcAxis2Placement3D"):
        raise UnsupportedIFCMutation("Unsupported opening placement frame")
    if frame.Axis and not np.allclose(frame.Axis.DirectionRatios,(0,0,1),atol=TOL):
        raise UnsupportedIFCMutation("Tilted hosted Opening not supported")
    if frame.RefDirection and not np.allclose(frame.RefDirection.DirectionRatios,(1,0,0),atol=TOL):
        raise UnsupportedIFCMutation("Rotated hosted Opening not supported")
    if not np.allclose(_m(wall)[:3,:3],np.eye(3),atol=TOL):
        raise UnsupportedIFCMutation("Host Wall world rotation requires geometry-aware frame update")
    return frame.Location


def _validate_opening_move_preflight(f,opening,expected_opening_attrs,all_openings):
    host=_native_host(opening)
    position=_plain_opening_local_frame(opening,host)
    if len(position.Coordinates)!=3:
        raise UnsupportedIFCMutation("Hosted opening point must be 3D")
    fills=list(opening.HasFillings)
    if len(fills)>1:
        raise UnsupportedIFCMutation("Multiple fills per Opening not supported")
    for rel in fills:
        filling=rel.RelatedBuildingElement
        if not filling or not filling.is_a() in ("IfcWindow","IfcDoor"):
            raise UnsupportedIFCMutation("Unsupported hosted filling type")
        pl=filling.ObjectPlacement
        if not pl or not pl.is_a("IfcLocalPlacement") or pl.PlacementRelTo!=opening.ObjectPlacement:
            raise UnsupportedIFCMutation("Window/Door is not hosted in movable Opening frame")
    if any(inv.is_a("IfcRelSpaceBoundary") for inv in f.get_inverse(opening)):
        raise UnsupportedIFCMutation("Opening has native SpaceBoundary dependencies")
    new_offset=float(expected_opening_attrs["offset"])
    new_width=float(expected_opening_attrs["width"])
    if new_offset<0 or new_width<=0:
        raise UnsupportedIFCMutation("Invalid requested Opening offset/width")
    # Avoid collisions with other source wall openings; not a universal clash
    # algorithm. This is a hard bounded gate for the simple fixture.
    for other in all_openings:
        if other.GlobalId==opening.GlobalId:
            continue
        try:
            other_host=_native_host(other)
        except UnsupportedIFCMutation:
            continue
        if other_host.GlobalId!=host.GlobalId:
            continue
        native_pos=_plain_opening_local_frame(other,host).Coordinates
        try:
            other_profile=_body_extrusion(other).SweptArea
            a,b,c,d=_rect_extents(other_profile)
        except Exception as exc:
            raise UnsupportedIFCMutation("Cannot bound another hosted Opening for clash detection") from exc
        old_start=float(native_pos[0])+a
        old_end=float(native_pos[0])+c
        if max(new_offset,old_start)<min(new_offset+new_width,old_end)-TOL:
            raise UnsupportedIFCMutation("Moved Opening would overlap another wall void")
    return host,position


def check_window_deletion(f,window_guid:str):
    window=by_guid_or_none(f,window_guid)
    if window is None or not window.is_a("IfcWindow"):
        raise UnsupportedIFCMutation("Window deletion requires existing IfcWindow")
    fills=list(window.FillsVoids)
    if len(fills)!=1:
        raise UnsupportedIFCMutation("Window must fill exactly one existing Opening")
    rel=fills[0]
    opening=rel.RelatingOpeningElement
    if not opening or len(opening.VoidsElements)!=1:
        raise UnsupportedIFCMutation("Window must have one Opening with a Wall host")
    for inverse in f.get_inverse(window):
        if not inverse.is_a() in ("IfcRelFillsElement","IfcRelContainedInSpatialStructure"):
            raise UnsupportedIFCMutation("Window has unsupported type/material/other relations")
    return window,rel,opening


def connection_guid(source_sha:str,a_guid:str,b_guid:str)->str:
    uid=uuid.uuid5(REL_NAMESPACE,f"connect-v0.1:{source_sha}:{a_guid}:{b_guid}")
    return ifcopenshell.guid.compress(uid.hex)


def _meet_at_endpoint(left_attrs:dict,right_attrs:dict)->bool:
    pa=[(float(left_attrs["x1"]),float(left_attrs["y1"]),float(left_attrs["z1"])),
        (float(left_attrs["x2"]),float(left_attrs["y2"]),float(left_attrs["z2"]))]
    pb=[(float(right_attrs["x1"]),float(right_attrs["y1"]),float(right_attrs["z1"])),
        (float(right_attrs["x2"]),float(right_attrs["y2"]),float(right_attrs["z2"]))]
    return any(math.dist(a,b)<TOL for a in pa for b in pb)


def _native_endpoint_guids(old_graph,new_graph,xml_endpoints:str):
    a,b=xml_endpoints.split("|",1)
    graph=new_graph if a in new_graph.by_id() and b in new_graph.by_id() else old_graph
    nodes=graph.by_id()
    if a not in nodes or b not in nodes:
        raise UnsupportedIFCMutation("Missing native wall connection endpoints")
    if nodes[a].kind!="Wall" or nodes[b].kind!="Wall":
        raise UnsupportedIFCMutation("Connection requires typed Wall endpoints")
    return a,b,nodes[a].ifc_guid,nodes[b].ifc_guid


def plan_topology_changes(
    before_doc:BuildingDocument,after_doc:BuildingDocument,
    before:BindingEvidence,after:BindingEvidence,delta:GraphDelta,
    f:ifcopenshell.file,
) -> tuple[Mutation,...]:
    old=before.graph.by_id(); new=after.graph.by_id()
    old_xml=before_doc.managed_by_id()
    new_xml=after_doc.managed_by_id()
    result=[]
    for name in delta.removed_nodes:
        node=old[name]
        if node.kind!="Window" or node.provenance!="existing_source":
            continue
        window,fill,opening=check_window_deletion(f,node.ifc_guid)
        result.append(Mutation("DELETE_WINDOW",name,node.ifc_guid,
                     old_xml[name].span.line,("entity","opening_fill"),"remove existing window but retain wall+void"))
    for name in delta.changed_nodes:
        prior=old[name]; current=new[name]
        if prior.kind!="Opening" or current.kind!="Opening" or prior.provenance!="existing_source":
            continue
        lhs=dict(prior.attributes);rhs=dict(current.attributes)
        fields=tuple(sorted(k for k in set(lhs)|set(rhs) if lhs.get(k)!=rhs.get(k)))
        if fields!=("offset",):
            continue
        opening=by_guid_or_none(f,prior.ifc_guid)
        if opening is None or not opening.is_a("IfcOpeningElement"):
            raise UnsupportedIFCMutation("Missing native Opening")
        _validate_opening_move_preflight(f,opening,rhs,f.by_type("IfcOpeningElement"))
        result.append(Mutation("MOVE_OPENING_WITH_FILLING",name,prior.ifc_guid,
                  new_xml[name].span.line,fields,"local host void translation propagates fill"))
    for edge in delta.added_edges:
        if edge.relation!="connects":
            continue
        lhs=new[edge.source];rhs=new[edge.target]
        if not _meet_at_endpoint(dict(lhs.attributes),dict(rhs.attributes)):
            raise UnsupportedIFCMutation("Wall connection must join actual endpoints")
        if lhs.id==rhs.id or dict(lhs.attributes)["level"]!=dict(rhs.attributes)["level"]:
            raise UnsupportedIFCMutation("Invalid native wall connection endpoint/storey")
        a_guid,b_guid=lhs.ifc_guid,rhs.ifc_guid
        if _one_connection(f,a_guid,b_guid) is not None:
            raise UnsupportedIFCMutation("Wall connection already exists in IFC input")
        rel_guid=connection_guid(before_doc.source_model_sha256,a_guid,b_guid)
        if by_guid_or_none(f,rel_guid) is not None:
            raise UnsupportedIFCMutation("Generated IfcRelConnectsElements GUID collision")
        line=next((r.span.line for r in after_doc.relations
                   if r.kind=="Connects" and
                   r.attrs().get("from")==edge.source and r.attrs().get("to")==edge.target),None)
        if line is None:
            raise UnsupportedIFCMutation("Wall connection declaration lacks an exact XML source node")
        result.append(Mutation("ADD_WALL_CONNECTION",edge.source+"|"+edge.target,
               rel_guid,line,("from","to"),"typed meeting-endpoint wall connection"))
    for edge in delta.removed_edges:
        if edge.relation!="connects":
            continue
        l=old[edge.source];r=old[edge.target]
        rel=_one_connection(f,l.ifc_guid,r.ifc_guid)
        if rel is None or rel.ConnectionGeometry is not None:
            raise UnsupportedIFCMutation("No unique editable simple wall connection in IFC source")
        line=next((r.span.line for r in before_doc.relations
                   if r.kind=="Connects" and
                   r.attrs().get("from")==edge.source and r.attrs().get("to")==edge.target),None)
        if line is None:
            raise UnsupportedIFCMutation("Removed wall connection has no native source declaration")
        result.append(Mutation("REMOVE_WALL_CONNECTION",edge.source+"|"+edge.target,
               rel.GlobalId,line,("from","to"),"remove explicit IFC wall connection"))
    return tuple(result)


def apply_topology_change(f,op:Mutation,old_graph,new_graph,after_doc):
    """Only apply operations already preflighted against immutable source."""
    if op.operation=="DELETE_WINDOW":
        window,rel,opening=check_window_deletion(f,op.ifc_guid)
        # CRITICAL: removed IfcOpenShell SWIG entity wrappers MUST NOT be
        # dereferenced after remove_product; record all required GUIDs first.
        fill_guid=rel.GlobalId
        opening_guid=opening.GlobalId
        ifcopenshell.api.root.remove_product(f,product=window)
        if by_guid_or_none(f,op.ifc_guid) is not None:
            raise UnsupportedIFCMutation("Native IfcWindow failed to delete")
        if by_guid_or_none(f,fill_guid) is not None:
            raise UnsupportedIFCMutation("Orphaned native IfcRelFillsElement after Window deletion")
        surviving_opening=by_guid_or_none(f,opening_guid)
        if surviving_opening is None or len(surviving_opening.VoidsElements)!=1:
            raise UnsupportedIFCMutation("Host wall void was corrupted during Window deletion")
    elif op.operation=="MOVE_OPENING_WITH_FILLING":
        opening=by_guid_or_none(f,op.ifc_guid)
        expected=dict(new_graph.by_id()[op.xml_id].attributes)
        host,position=_validate_opening_move_preflight(
            f,opening,expected,f.by_type("IfcOpeningElement"))
        x,y,z=tuple(float(v) for v in position.Coordinates)
        # This frame's x starts at zero on the native wall. The stable
        # original position+delta is only valid when wall local starts at x=0.
        source_xml=old_graph.by_id()[op.xml_id]
        old_offset=float(dict(source_xml.attributes)["offset"])
        requested=float(expected["offset"])
        position.Coordinates=(x+(requested-old_offset),y,z)
        if len(opening.VoidsElements)!=1 or len(opening.HasFillings)>1:
            raise UnsupportedIFCMutation("Hosted void/filling relationship changed unexpectedly")
    elif op.operation=="ADD_WALL_CONNECTION":
        _,_,a_guid,b_guid=_native_endpoint_guids(old_graph,new_graph,op.xml_id)
        a=by_guid_or_none(f,a_guid); b=by_guid_or_none(f,b_guid)
        if a is None or b is None or not a.is_a("IfcWall") or not b.is_a("IfcWall"):
            raise UnsupportedIFCMutation("Cannot create relation to missing IFC Walls")
        if _one_connection(f,a_guid,b_guid) is not None:
            raise UnsupportedIFCMutation("Duplicate wall connection")
        f.create_entity("IfcRelConnectsElements",GlobalId=op.ifc_guid,
                        RelatingElement=a,RelatedElement=b)
    elif op.operation=="REMOVE_WALL_CONNECTION":
        _,_,a_guid,b_guid=_native_endpoint_guids(old_graph,new_graph,op.xml_id)
        rel=_one_connection(f,a_guid,b_guid)
        if rel is None or rel.GlobalId!=op.ifc_guid:
            raise UnsupportedIFCMutation("Native wall connection identity changed")
        f.remove(rel)
    else:
        raise UnsupportedIFCMutation("Unknown topology operation")


def native_topology_inventory(f)->dict[str,tuple]:
    """Independent IFC-only typed relation multiset, no XML access."""
    out={}
    for relation_class,src_name,dst_name in (
        ("IfcRelContainedInSpatialStructure","RelatingStructure","RelatedElements"),
        ("IfcRelAggregates","RelatingObject","RelatedObjects"),
        ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
        ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement"),
        ("IfcRelSpaceBoundary","RelatingSpace","RelatedBuildingElement"),
        ("IfcRelConnectsElements","RelatingElement","RelatedElement"),
    ):
        for rel in f.by_type(relation_class):
            lhs=getattr(rel,src_name)
            rhs=getattr(rel,dst_name)
            if not isinstance(rhs,tuple):rhs=(rhs,)
            if not isinstance(lhs,tuple):lhs=(lhs,)
            a=tuple(sorted(x.GlobalId for x in lhs if x is not None and x.is_a("IfcRoot")))
            b=tuple(sorted(x.GlobalId for x in rhs if x is not None and x.is_a("IfcRoot")))
            out[rel.GlobalId]=(relation_class,a,b)
    return out


def verify_topology_result(source_f,result_f,operations,old_graph,new_graph):
    """Compare exact native IFC relation inventory with whitelist of deltas."""
    before=native_topology_inventory(source_f)
    after=native_topology_inventory(result_f)
    permitted_removed=set()
    permitted_created=set()
    permitted_changed=set()
    expected={}
    for op in operations:
        if op.operation=="DELETE_WINDOW":
            w=source_f.by_guid(op.ifc_guid)
            rel=list(w.FillsVoids)[0]
            permitted_removed.add(rel.GlobalId)
            for owner in w.ContainedInStructure:
                permitted_changed.add(owner.GlobalId)
            if by_guid_or_none(result_f,w.GlobalId) is not None:
                raise UnsupportedIFCMutation("Deleted Window still present after IFC reopen")
            target=rel.RelatingOpeningElement
            after_target=by_guid_or_none(result_f,target.GlobalId)
            if after_target is None or not after_target.VoidsElements:
                raise UnsupportedIFCMutation("IfcRelVoidsElement lost after Window deletion")
        elif op.operation=="ADD_WALL_CONNECTION":
            permitted_created.add(op.ifc_guid)
            _,_,a,b=_native_endpoint_guids(old_graph,new_graph,op.xml_id)
            expected[op.ifc_guid]=("IfcRelConnectsElements",(a,),(b,))
        elif op.operation=="REMOVE_WALL_CONNECTION":
            permitted_removed.add(op.ifc_guid)
        elif op.operation=="MOVE_OPENING_WITH_FILLING":
            a=source_f.by_guid(op.ifc_guid)
            b=by_guid_or_none(result_f,op.ifc_guid)
            if b is None:
                raise UnsupportedIFCMutation("Moved IfcOpeningElement missing")
            expected_attrs=dict(new_graph.by_id()[op.xml_id].attributes)
            from src.runtime.ifc_projection import _opening_attrs
            # Existing walls are needed for actual world projection.
            host=_native_host(b)
            p={host.GlobalId:dict(new_graph.by_id()[next(
                n.id for n in new_graph.nodes if n.ifc_guid==host.GlobalId)].attributes)}
            actual=_opening_attrs(b,p,1.0)
            if not math.isclose(float(actual["offset"]),float(expected_attrs["offset"]),abs_tol=1e-6):
                raise UnsupportedIFCMutation("Native moved opening offset does not match XML")
            prior_fill=[r.RelatedBuildingElement for r in a.HasFillings]
            final_fill=[r.RelatedBuildingElement for r in b.HasFillings]
            if [x.GlobalId for x in prior_fill]!=[x.GlobalId for x in final_fill]:
                raise UnsupportedIFCMutation("Move corrupted filling identities")
            for one,two in zip(prior_fill,final_fill):
                a_xyz=ifcopenshell.util.placement.get_local_placement(one.ObjectPlacement)[:3,3]
                b_xyz=ifcopenshell.util.placement.get_local_placement(two.ObjectPlacement)[:3,3]
                d=float(expected_attrs["offset"])-float(dict(old_graph.by_id()[op.xml_id].attributes)["offset"])
                if not np.allclose(b_xyz-a_xyz,(d,0.,0.),atol=1e-6):
                    raise UnsupportedIFCMutation("Move failed to propagate to filling global placement")
    removed_members={op.ifc_guid for op in operations
                     if op.operation in ("DELETE_WINDOW","DELETE_WALL")}
    added_members={}
    for op in operations:
        if op.operation!="CREATE_WALL":
            continue
        product=by_guid_or_none(result_f,op.ifc_guid)
        if product is None or len(product.ContainedInStructure)!=1:
            raise UnsupportedIFCMutation("Created Wall lacks unique native storey containment")
        relation=product.ContainedInStructure[0]
        added_members.setdefault(relation.GlobalId,set()).add(op.ifc_guid)
        if relation.GlobalId in before:
            permitted_changed.add(relation.GlobalId)
        else:
            permitted_created.add(relation.GlobalId)
            # This new storey relation can only contain newly created Walls.
            if set(after[relation.GlobalId][2])!=added_members[relation.GlobalId]:
                raise UnsupportedIFCMutation("New spatial containment includes unrelated products")
    for guid in set(before)&set(after):
        if before[guid]==after[guid]:
            continue
        if guid not in permitted_changed:
            raise UnsupportedIFCMutation("Unapproved native IFC relation endpoint mutation")
        rel_type,left,right=before[guid]
        if rel_type!="IfcRelContainedInSpatialStructure":
            raise UnsupportedIFCMutation("Unexpected noncontainment relation update")
        expected_right=tuple(sorted(
            (set(right)-removed_members)|added_members.get(guid,set())))
        if after[guid]!=(rel_type,left,expected_right):
            raise UnsupportedIFCMutation("Mutation changed unrelated storey containment members")
    removed=set(before)-set(after)
    added=set(after)-set(before)
    if removed!=permitted_removed or added!=permitted_created:
        raise UnsupportedIFCMutation("Unexpected native IFC relation creation/deletion")
    for guid,typed in expected.items():
        if after.get(guid)!=typed:
            raise UnsupportedIFCMutation("New wall IFC relation endpoints mismatch")
