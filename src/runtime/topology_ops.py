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
import ifcopenshell.geom
import ifcopenshell.api.root
import ifcopenshell.util.placement
import numpy as np

from src.runtime.ast import BuildingDocument
from src.runtime.binder import BindingEvidence
from src.runtime.ifc_mutations import Mutation, UnsupportedIFCMutation, by_guid_or_none
from src.runtime.semantic_graph import GraphDelta, GraphEdge
from src.runtime.ifc_projection import _m

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
    rotation=_m(wall)[:3,:3]
    # A horizontal wall azimuth changes the world vector of an unchanged
    # parent-relative X edit. Tilt/reflection requires a different policy.
    if (not np.allclose(rotation[2,:],(0.,0.,1.),atol=TOL)
            or not math.isclose(float(np.linalg.det(rotation)),1.,abs_tol=TOL)):
        raise UnsupportedIFCMutation("Tilted/reflected host Wall frame is unsupported")
    return frame.Location


def _opening_axis_bounds(opening,host):
    """True native void interval in metres along host Wall-local X (world)."""
    try:
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        # Hold the shape wrapper alive while reading its SWIG vertex buffer.
        shape=ifcopenshell.geom.create_shape(settings,opening)
        vertices=np.asarray(shape.geometry.verts,dtype=np.float64).reshape((-1,3))
    except Exception as exc:
        raise UnsupportedIFCMutation("Cannot inspect native Opening geometry") from exc
    if len(vertices)<4 or not np.isfinite(vertices).all():
        raise UnsupportedIFCMutation("Native Opening has missing/nonfinite geometry")
    host_frame=_m(host)
    along=(vertices-host_frame[:3,3])@host_frame[:3,0]
    lo=float(np.min(along))
    hi=float(np.max(along))
    if not (math.isfinite(lo) and math.isfinite(hi) and hi-lo>TOL):
        raise UnsupportedIFCMutation("Native Opening has degenerate horizontal extent")
    return lo,hi


def _validate_opening_move_preflight(f,opening,expected_opening_attrs,all_openings,
                                     *,source_offset=None):
    host=_native_host(opening)
    position=_plain_opening_local_frame(opening,host)
    if len(position.Coordinates)!=3:
        raise UnsupportedIFCMutation("Hosted opening point must be 3D")
    # Changing this CartesianPoint must never shift unrelated placements.
    position_owners=f.get_inverse(position)
    frame=opening.ObjectPlacement.RelativePlacement
    if len(position_owners)!=1 or next(iter(position_owners)).id()!=frame.id():
        raise UnsupportedIFCMutation("Opening placement point has shared/unexpected owners")
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
    old_native_offset=float(position.Coordinates[0])
    if (source_offset is not None and
            not math.isclose(float(source_offset),old_native_offset,rel_tol=0.,abs_tol=TOL)):
        raise UnsupportedIFCMutation("Projected Opening offset differs from native local X")
    delta=new_offset-old_native_offset
    prior_start,prior_end=_opening_axis_bounds(opening,host)
    new_start,new_end=prior_start+delta,prior_end+delta
    # Source sweeps may encode vertical height along profile X and wall
    # thickness along extrusion Depth. Compare true void geometry projected
    # onto the host Wall's world-space longitudinal axis, never raw profile X.
    for other in all_openings:
        if other.GlobalId==opening.GlobalId:
            continue
        try:
            other_host=_native_host(other)
        except UnsupportedIFCMutation:
            continue
        if other_host.GlobalId!=host.GlobalId:
            continue
        _plain_opening_local_frame(other,host)
        other_start,other_end=_opening_axis_bounds(other,host)
        if max(new_start,other_start)<min(new_end,other_end)-TOL:
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


def _verified_new_wall_t_path(host_node,branch_node,source_f)->str:
    """Classify a bounded old-host-path to new-wall endpoint surface contact.

    The XML `Connects` declaration is a *relationship state*, not an
    instruction to blindly create a join. Native geometry and explicit
    source/new identity must establish the right-angled T connection.
    The fixed IFC4X3 source subtype is IfcRelConnectsPathElements.
    """
    if (host_node.kind!="Wall" or branch_node.kind!="Wall" or
            host_node.provenance!="existing_source" or
            branch_node.provenance!="deterministic_new"):
        raise UnsupportedIFCMutation("T join requires existing host and newly authored Wall")
    a=dict(host_node.attributes); b=dict(branch_node.attributes)
    if a["level"]!=b["level"]:
        raise UnsupportedIFCMutation("T join crosses IFC building storeys")
    host=by_guid_or_none(source_f,host_node.ifc_guid)
    if host is None or not host.is_a("IfcWall"):
        raise UnsupportedIFCMutation("Existing T-host wall missing")
    hp=np.array((float(a["x1"]),float(a["y1"])))
    hq=np.array((float(a["x2"]),float(a["y2"])))
    bp=np.array((float(b["x1"]),float(b["y1"])))
    bq=np.array((float(b["x2"]),float(b["y2"])))
    hl=float(np.linalg.norm(hq-hp)); bl=float(np.linalg.norm(bq-bp))
    host_th=float(a["thickness"]); branch_th=float(b["thickness"])
    if (hl<0.5 or bl<0.5 or not math.isfinite(host_th+branch_th)
            or host_th<=0 or branch_th<=0):
        raise UnsupportedIFCMutation("T join has invalid host/new wall dimensions")
    hu=(hq-hp)/hl; bu=(bq-bp)/bl
    if abs(float(np.dot(hu,bu)))>1e-6:
        raise UnsupportedIFCMutation("Wall connection must join actual endpoints or a perpendicular T path")
    hn=np.array((-hu[1],hu[0]))
    # Host geometry is checked against native IFC, not only XML annotations.
    try:
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        shape=ifcopenshell.geom.create_shape(settings,host)
        vertices=np.asarray(shape.geometry.verts,dtype=np.float64).reshape(-1,3)
    except Exception as exc:
        raise UnsupportedIFCMutation("T host native mesh unavailable") from exc
    if len(vertices)<8 or not np.isfinite(vertices).all():
        raise UnsupportedIFCMutation("T host has untrusted mesh geometry")
    hproj=(vertices[:,:2]-hp)@hu
    nproj=(vertices[:,:2]-hp)@hn
    if (abs(float(hproj.min()))>1e-5 or abs(float(hproj.max())-hl)>1e-5
            or abs(float(nproj.min())+host_th/2.)>1e-5
            or abs(float(nproj.max())-host_th/2.)>1e-5):
        raise UnsupportedIFCMutation("T host native wall geometry disagrees with XML path")
    if (abs(float(vertices[:,2].min())-float(a["z1"]))>1e-5
            or abs(float(vertices[:,2].max())-(float(a["z1"])+float(a["height"])))>1e-5
            or abs(float(b["z1"])-float(a["z1"]))>1e-5
            or abs(float(b["z2"])-float(a["z2"]))>1e-5
            or abs(float(b["height"])-float(a["height"]))>1e-5):
        raise UnsupportedIFCMutation("T join requires matching native wall vertical span")
    accepted=[]
    for end,label,toward in ((bp,"ATSTART",bu),(bq,"ATEND",-bu)):
        pos=end-hp
        signed=float(pos@hn)
        station=float(pos@hu)
        # New wall occupies one native strip measured from its axis to the
        # left; the entire face must lie strictly inside the host's path.
        other_station=station+branch_th*float(np.dot(np.array((-bu[1],bu[0])),hu))
        if (abs(abs(signed)-host_th/2.)>1e-5
                or min(station,other_station)<=1e-5
                or max(station,other_station)>=hl-1e-5
                or float(np.dot(toward,hn))*signed<=0):
            continue
        # Prevent connecting a new wall through an existing hosted void.
        intersects_opening=False
        for rel in host.HasOpenings:
            opening=rel.RelatedOpeningElement
            try:
                void_shape=ifcopenshell.geom.create_shape(settings,opening)
                void_pts=np.asarray(void_shape.geometry.verts,dtype=np.float64).reshape(-1,3)
            except Exception as exc:
                raise UnsupportedIFCMutation("T host opening collision cannot be checked") from exc
            lo,hi=float(((void_pts[:,:2]-hp)@hu).min()),float(((void_pts[:,:2]-hp)@hu).max())
            if max(min(station,other_station),lo)<min(max(station,other_station),hi)-1e-6:
                intersects_opening=True
                break
        if not intersects_opening:
            accepted.append(label)
    if len(accepted)!=1:
        raise UnsupportedIFCMutation("T join must contact one unobstructed host side at a new Wall endpoint")
    return accepted[0]


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
        _validate_opening_move_preflight(f,opening,rhs,f.by_type("IfcOpeningElement"),
                                         source_offset=lhs["offset"])
        result.append(Mutation("MOVE_OPENING_WITH_FILLING",name,prior.ifc_guid,
                  new_xml[name].span.line,fields,"local host void translation propagates fill"))
    for edge in delta.added_edges:
        if edge.relation!="connects":
            continue
        lhs=new[edge.source];rhs=new[edge.target]
        if lhs.id==rhs.id or dict(lhs.attributes)["level"]!=dict(rhs.attributes)["level"]:
            raise UnsupportedIFCMutation("Invalid native wall connection endpoint/storey")
        if lhs.provenance=="existing_source" and rhs.provenance=="deterministic_new":
            branch_end=_verified_new_wall_t_path(lhs,rhs,f)
            operation="ADD_WALL_PATH_CONNECTION"
            reason="native T path junction: host ATPATH, new Wall "+branch_end
        elif _meet_at_endpoint(dict(lhs.attributes),dict(rhs.attributes)):
            operation="ADD_WALL_CONNECTION"
            reason="typed meeting-endpoint wall connection"
        else:
            raise UnsupportedIFCMutation("Wall connection must join actual endpoints or verified T path")
        a_guid,b_guid=lhs.ifc_guid,rhs.ifc_guid
        if _one_connection(f,a_guid,b_guid) is not None:
            raise UnsupportedIFCMutation("Wall connection already exists in IFC input")
        rel_guid=connection_guid(before_doc.source_model_sha256,a_guid,b_guid)
        if by_guid_or_none(f,rel_guid) is not None:
            raise UnsupportedIFCMutation("Generated native wall relation GUID collision")
        line=next((r.span.line for r in after_doc.relations
                   if r.kind=="Connects" and
                   r.attrs().get("from")==edge.source and r.attrs().get("to")==edge.target),None)
        if line is None:
            raise UnsupportedIFCMutation("Wall connection declaration lacks an exact XML source node")
        result.append(Mutation(operation,edge.source+"|"+edge.target,
               rel_guid,line,("from","to"),reason))
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
        source_xml=old_graph.by_id()[op.xml_id]
        host,position=_validate_opening_move_preflight(
            f,opening,expected,f.by_type("IfcOpeningElement"),
            source_offset=dict(source_xml.attributes)["offset"])
        x,y,z=tuple(float(v) for v in position.Coordinates)
        # This frame's x starts at zero on the native wall. The stable
        # original position+delta is only valid when wall local starts at x=0.
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
    elif op.operation=="ADD_WALL_PATH_CONNECTION":
        _,_,host_guid,branch_guid=_native_endpoint_guids(old_graph,new_graph,op.xml_id)
        a=by_guid_or_none(f,host_guid); b=by_guid_or_none(f,branch_guid)
        if a is None or b is None or not a.is_a("IfcWall") or not b.is_a("IfcWall"):
            raise UnsupportedIFCMutation("Cannot create T junction to missing IFC Walls")
        if _one_connection(f,host_guid,branch_guid) is not None:
            raise UnsupportedIFCMutation("Duplicate native T junction")
        end=_verified_new_wall_t_path(
            old_graph.by_id()[op.xml_id.split("|",1)[0]],
            new_graph.by_id()[op.xml_id.split("|",1)[1]],
            f)
        f.create_entity("IfcRelConnectsPathElements",GlobalId=op.ifc_guid,
                        RelatingElement=a,RelatedElement=b,
                        RelatingConnectionType="ATPATH",RelatedConnectionType=end,
                        RelatingPriorities=(),RelatedPriorities=())
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
            concrete=(rel.is_a() if relation_class=="IfcRelConnectsElements"
                      else relation_class)
            out[rel.GlobalId]=(concrete,a,b)
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
        elif op.operation=="ADD_WALL_PATH_CONNECTION":
            permitted_created.add(op.ifc_guid)
            _,_,a,b=_native_endpoint_guids(old_graph,new_graph,op.xml_id)
            expected[op.ifc_guid]=("IfcRelConnectsPathElements",(a,),(b,))
            relation=by_guid_or_none(result_f,op.ifc_guid)
            if relation is None or not relation.is_a("IfcRelConnectsPathElements"):
                raise UnsupportedIFCMutation("New native T junction has wrong relation class")
            end=_verified_new_wall_t_path(
                old_graph.by_id()[op.xml_id.split("|",1)[0]],
                new_graph.by_id()[op.xml_id.split("|",1)[1]],
                source_f)
            if (str(relation.RelatingConnectionType)!="ATPATH"
                    or str(relation.RelatedConnectionType)!=end
                    or relation.ConnectionGeometry is not None
                    or tuple(relation.RelatingPriorities)!=()
                    or tuple(relation.RelatedPriorities)!=()):
                raise UnsupportedIFCMutation("Native T path connection subtype/placement mismatch")
            # Validate the actual saved wall mesh, not merely a declarative
            # contact claim that a geometry writer could fail to realize.
            branch_attrs=dict(new_graph.by_id()[op.xml_id.split("|",1)[1]].attributes)
            bp=np.array((float(branch_attrs["x1"]),float(branch_attrs["y1"])))
            bq=np.array((float(branch_attrs["x2"]),float(branch_attrs["y2"])))
            vec=bq-bp
            leng=float(np.linalg.norm(vec))
            if leng<=TOL:
                raise UnsupportedIFCMutation("Saved T branch Wall degenerate")
            normal=np.array((-vec[1],vec[0]))/leng
            depth=float(branch_attrs["thickness"])
            corners=np.array((bp,bq,bp+normal*depth,bq+normal*depth))
            exp_min=np.array((float(corners[:,0].min()),float(corners[:,1].min()),
                              float(branch_attrs["z1"])))
            exp_max=np.array((float(corners[:,0].max()),float(corners[:,1].max()),
                              float(branch_attrs["z1"])+float(branch_attrs["height"])))
            try:
                settings=ifcopenshell.geom.settings()
                settings.set(settings.USE_WORLD_COORDS,True)
                shape=ifcopenshell.geom.create_shape(settings,relation.RelatedElement)
                points=np.asarray(shape.geometry.verts,dtype=np.float64).reshape(-1,3)
            except Exception as exc:
                raise UnsupportedIFCMutation("Saved native T branch has no valid IFC shape") from exc
            if (len(points)<8 or not np.isfinite(points).all()
                    or not np.allclose(points.min(axis=0),exp_min,atol=1e-6,rtol=0)
                    or not np.allclose(points.max(axis=0),exp_max,atol=1e-6,rtol=0)):
                raise UnsupportedIFCMutation("Saved native T branch geometry differs from declarative Wall")
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
                host_before=_native_host(a)
                host_after=_native_host(b)
                rotation_before=_m(host_before)[:3,:3]
                rotation_after=_m(host_after)[:3,:3]
                if not np.allclose(rotation_before,rotation_after,atol=1e-7):
                    raise UnsupportedIFCMutation("Host Wall placement changed during Opening move")
                expected_world_delta=rotation_before[:,0]*d
                if not np.allclose(b_xyz-a_xyz,expected_world_delta,atol=1e-6):
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
