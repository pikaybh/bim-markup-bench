"""Independent source-native IFC4X3 complex geometry oracle, not a compiler.

Reopens original and compiled IFC; imports neither projection, binder,
semantic-diff/compiler module nor original-author grader. Checks complete
source STEP/Root identity, original-world native IFC meshes, exact original
rotated Slab/profile and shared Column/Boolean Wall native topology, physics
and connected/voided/filling relationships. Not 45/45 task parity.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
import ifcopenshell.util.element
import numpy as np


EPS=2e-5


class IndependentComplexV9Error(ValueError):
    pass


def _sha(path):
    h=sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _native_world(product):
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        sh=ifcopenshell.geom.create_shape(settings,product)
        vertices=np.asarray(sh.geometry.verts,dtype=float).reshape(-1,3)
        triangles=np.asarray(sh.geometry.faces,dtype=int).reshape(-1,3)
        volume=float(ifcopenshell.util.shape.get_volume(sh.geometry))
    except Exception as exc:
        raise IndependentComplexV9Error("Independent native world geometry kernel failed") from exc
    if not (len(vertices)>=8 and len(triangles)>=12 and
            np.all(np.isfinite(vertices)) and math.isfinite(volume)):
        raise IndependentComplexV9Error("Native original IFC4X3 world mesh is missing/invalid")
    return vertices,triangles,volume


def _open_pair(source,candidate):
    if (source.resolve()==candidate.resolve() or not source.is_file()
        or not candidate.is_file() or source.is_symlink() or candidate.is_symlink()):
        raise IndependentComplexV9Error("Source and candidate IFC must be distinct files")
    a=ifcopenshell.open(str(source))
    b=ifcopenshell.open(str(candidate))
    if a.schema!="IFC4X3" or b.schema!=a.schema:
        raise IndependentComplexV9Error("Original IFC4X3 schema changed or missing")
    return a,b


def _inventory(a,b,*,changed_steps:set[int],new_guids=(),containment_only=False):
    oldsteps={x.id():str(x) for x in a}
    newsteps={x.id():str(x) for x in b}
    if not set(oldsteps)<=set(newsteps):
        raise IndependentComplexV9Error("Original native IFC STEP objects were deleted")
    actual={id for id in oldsteps if oldsteps[id]!=newsteps[id]}
    if actual!=changed_steps:
        raise IndependentComplexV9Error("Unapproved old original IFC STEP changed: "+
                                        str(sorted(actual^changed_steps)))
    roots0={r.GlobalId:r for r in a.by_type("IfcRoot")}
    roots1={r.GlobalId:r for r in b.by_type("IfcRoot")}
    if not set(roots0)<=set(roots1) or not set(new_guids)<=set(roots1)-set(roots0):
        raise IndependentComplexV9Error("Original source native IFC Roots changed")
    for guid,root in roots0.items():
        cur=roots1[guid]
        if root.is_a()!=cur.is_a():
            raise IndependentComplexV9Error("Original IFC Root class changed")
        if str(root)!=str(cur):
            if not containment_only or not root.is_a("IfcRelContainedInSpatialStructure"):
                raise IndependentComplexV9Error("Unrelated source Root metadata changed")
            before={x.GlobalId for x in root.RelatedElements}
            after={x.GlobalId for x in cur.RelatedElements}
            if not before<=after or after-before!=set(new_guids)&after:
                raise IndependentComplexV9Error("Unrelated source Storey membership altered")
    return {
        "original_step_count_preserved":len(oldsteps),
        "original_root_globalids_preserved":len(roots0),
        "new_root_count":len(set(roots1)-set(roots0)),
        "only_declared_native_step_changes":True,
    }


def _unchanged_mesh(a,b,except_guids):
    src={x.GlobalId:x for x in a.by_type("IfcProduct")}
    dst={x.GlobalId:x for x in b.by_type("IfcProduct")}
    if not set(src)<=set(dst):
        raise IndependentComplexV9Error("Original IFC Product removed")
    checked=0
    for guid,obj in src.items():
        other=dst[guid]
        if obj.is_a()!=other.is_a() or str(obj)!=str(other):
            raise IndependentComplexV9Error("Original IFC Product identity/metadata changed")
        if guid in except_guids or obj.Representation is None:
            continue
        pa,fa,_=_native_world(obj)
        pb,fb,_=_native_world(other)
        if (pa.shape!=pb.shape or fa.shape!=fb.shape
            or not np.allclose(pa,pb,atol=EPS,rtol=0)):
            raise IndependentComplexV9Error("Original non-target product native mesh changed")
        checked+=1
    return checked


def verify_v09_rotated_slab_square(source,candidate,guid):
    a,b=_open_pair(source,candidate)
    try:
        slab=a.by_guid(guid)
        new=b.by_guid(guid)
    except RuntimeError as exc:
        raise IndependentComplexV9Error("Original public native Slab GUID missing") from exc
    if not slab.is_a("IfcSlab") or not new.is_a("IfcSlab"):
        raise IndependentComplexV9Error("Expected native IfcSlab original GUID")
    solids=[it for rep in slab.Representation.Representations for it in rep.Items
            if it.is_a("IfcExtrudedAreaSolid")]
    if len(solids)!=1 or not solids[0].SweptArea.is_a("IfcRectangleProfileDef"):
        raise IndependentComplexV9Error("Original native Slab was not single rectangular swept solid")
    oldsolid=solids[0]
    newsolid=b.by_id(oldsolid.id())
    profile=oldsolid.SweptArea
    nxt=newsolid.SweptArea
    if (not math.isclose(float(profile.XDim),8.5,abs_tol=EPS)
        or not math.isclose(float(profile.YDim),10.,abs_tol=EPS)
        or not math.isclose(float(nxt.XDim),10.,abs_tol=EPS)
        or not math.isclose(float(nxt.YDim),10.,abs_tol=EPS)
        or not math.isclose(nxt.Position.Location.Coordinates[0]
                            -profile.Position.Location.Coordinates[0],.75,abs_tol=EPS)):
        raise IndependentComplexV9Error("Source-native rotated Slab profile was rebuilt or dimensions incorrect")
    points_old,_,_= _native_world(slab)
    points_new,triangles,volume=_native_world(new)
    lo0=points_old.min(0);lo=points_new.min(0);hi=points_new.max(0)
    if (len(points_new)!=8 or len(triangles)!=12
        or not np.allclose(lo0,lo,atol=EPS,rtol=0)
        or not np.allclose(hi-lo,(10.,10.,.3),atol=EPS,rtol=0)
        or not math.isclose(volume,30.,abs_tol=.001)):
        raise IndependentComplexV9Error("Original Slab geometry not square or original anchor moved")
    inventory=_inventory(a,b,changed_steps={profile.id(),profile.Position.Location.id()})
    other=_unchanged_mesh(a,b,{guid})
    return {
        "status":"INDEPENDENT_ORIGINAL_ROTATED_IFC4X3_SLAB_SQUARE_PASS",
        "source_sha256":_sha(source),
        "candidate_sha256":_sha(candidate),
        "original_native_slab_guid":guid,
        "original_source_profile_XDim_m":float(profile.XDim),
        "original_native_profile_axis_maintained":True,
        "result_native_world_box_min_m":list(lo),
        "result_native_world_box_max_m":list(hi),
        "result_native_slab_volume_cubic_m":volume,
        "other_original_native_world_meshes_preserved":other,
        **inventory,
        "all45_equivalence_proven":False,
    }


def verify_v09_shared_columns_touch_slab(source,candidate,column_guids,slab_guid):
    a,b=_open_pair(source,candidate)
    guids=set(column_guids)
    if len(guids)!=2:
        raise IndependentComplexV9Error("Original two mapped native Columns required")
    source_columns={x.GlobalId for x in a.by_type("IfcColumn")}
    if guids!=source_columns:
        raise IndependentComplexV9Error("Missing or extraneous source columns")
    native_items=[]
    for guid in guids:
        col=a.by_guid(guid)
        rep=col.Representation.Representations[0]
        if len(rep.Items)!=1 or not rep.Items[0].is_a("IfcMappedItem"):
            raise IndependentComplexV9Error("Original Column not source IfcMappedItem")
        mp=rep.Items[0].MappingSource
        solid=mp.MappedRepresentation.Items[0]
        if not solid.is_a("IfcExtrudedAreaSolid"):
            raise IndependentComplexV9Error("Original mapped shared extrusion missing")
        native_items.append((mp.id(),solid.id()))
    if len(set(native_items))!=1:
        raise IndependentComplexV9Error("Original Columns not sharing one source type")
    solid_id=native_items[0][1]
    s0=a.by_id(solid_id);s1=b.by_id(solid_id)
    if not math.isclose(float(s0.Depth),1.5,abs_tol=EPS) or not math.isclose(
        float(s1.Depth),2.7,abs_tol=EPS
    ):
        raise IndependentComplexV9Error("Shared native source mapped Column extrusion not extended to original slab")
    slab=a.by_guid(slab_guid)
    if not slab.is_a("IfcSlab"):
        raise IndependentComplexV9Error("Original named upper native Slab missing")
    slab_bottom=_native_world(slab)[0].min(0)[2]
    if abs(float(slab_bottom)-2.7)>.01:
        raise IndependentComplexV9Error("Original named Slab underside not at new Column top")
    centers=[]
    for guid in guids:
        before,triangles0,_=_native_world(a.by_guid(guid))
        after,triangles1,_=_native_world(b.by_guid(guid))
        if (len(before)!=len(after) or len(triangles0)!=len(triangles1)
            or not np.allclose(before.min(0),after.min(0),atol=EPS)
            or not np.allclose(before.max(0)[:2],after.max(0)[:2],atol=EPS)
            or abs(after.max(0)[2]-2.7)>EPS):
            raise IndependentComplexV9Error("Both native Columns failed to extend vertically in place")
        centers.append(tuple(after.mean(0)))
    inventory=_inventory(a,b,changed_steps={solid_id})
    other=_unchanged_mesh(a,b,guids)
    return {
        "status":"INDEPENDENT_SOURCE_SHARED_MAPPED_COLUMNS_TOUCH_ORIGINAL_SLAB_PASS",
        "source_sha256":_sha(source),
        "candidate_sha256":_sha(candidate),
        "original_source_named_slab_guid":slab_guid,
        "original_native_slab_underside_m":float(slab_bottom),
        "new_native_column_top_m":2.7,
        "source_shared_extrusion_step_id":solid_id,
        "source_column_guids":sorted(guids),
        "other_original_native_meshes_preserved":other,
        **inventory,
        "all45_equivalence_proven":False,
    }


def verify_v09_boolean_host_door(source,candidate,host_guid,opening_guid,door_guid):
    a,b=_open_pair(source,candidate)
    orig_host=a.by_guid(host_guid)
    curr_host=b.by_guid(host_guid)
    if not orig_host.is_a("IfcWall") or not curr_host.is_a("IfcWall"):
        raise IndependentComplexV9Error("Native original Wall host class incorrect")
    if any(not rep.RepresentationType=="Clipping"
           for rep in orig_host.Representation.Representations
           if rep.RepresentationIdentifier=="Body"):
        raise IndependentComplexV9Error("Original host is not BooleanClipping geometry")
    if any(rep.RepresentationType=="Clipping" for rep in curr_host.Representation.Representations)==False:
        raise IndependentComplexV9Error("Original Boolean clipping representation was replaced")
    old_products={x.GlobalId for x in a.by_type("IfcProduct")}
    new_products={x.GlobalId for x in b.by_type("IfcProduct")}
    if new_products-old_products!={opening_guid,door_guid}:
        raise IndependentComplexV9Error("Native hosted edit created unexpected original IFC Products")
    opening=b.by_guid(opening_guid);door=b.by_guid(door_guid)
    if not opening.is_a("IfcOpeningElement") or not door.is_a("IfcDoor"):
        raise IndependentComplexV9Error("Native IFC4X3 Door+Opening typed entities missing")
    if (len(opening.VoidsElements)!=1 or len(door.FillsVoids)!=1
        or opening.VoidsElements[0].RelatingBuildingElement.GlobalId!=host_guid
        or door.FillsVoids[0].RelatingOpeningElement.GlobalId!=opening_guid):
        raise IndependentComplexV9Error("Native Boolean Wall Opening void/fill relationships missing")
    p0,t0,v0=_native_world(orig_host)
    p1,t1,v1=_native_world(curr_host)
    if (len(p1)!=16 or len(t1)!=28 or len(p0)!=8 or len(t0)!=12
        or not np.allclose(p0.min(0),p1.min(0),atol=EPS)
        or not np.allclose(p0.max(0),p1.max(0),atol=EPS)
        or not math.isclose(v0-v1,.42,abs_tol=2e-4,rel_tol=0)):
        raise IndependentComplexV9Error("Original BooleanClipping Wall physical cut has incorrect geometry/volume")
    pv,pt,_=_native_world(opening)
    dv,dt,_=_native_world(door)
    if (len(pv)!=8 or len(pt)!=12 or
        not np.allclose(pv.min(0),(3.,-.15,0.),atol=EPS)
        or not np.allclose(pv.max(0),(4.,.35,2.1),atol=EPS)
        or not np.allclose(dv.min(0),(3.,.06,0.),atol=EPS)
        or not np.allclose(dv.max(0),(4.,.14,2.1),atol=EPS)):
        raise IndependentComplexV9Error("New Door/Opening does not cut through actual external Wall at source-only site")
    if not (pv.min(0)[1]<p0.min(0)[1] and pv.max(0)[1]>p0.max(0)[1]):
        raise IndependentComplexV9Error("Door opening does not connect exterior/interior across full Wall thickness")
    storey=ifcopenshell.util.element.get_container(door)
    original_storeys={x.GlobalId for x in a.by_type("IfcBuildingStorey")}
    if storey is None or storey.GlobalId not in original_storeys:
        raise IndependentComplexV9Error("New native Door lacks original source Storey containment")
    allowed={
        r.id() for r in a.by_type("IfcRelContainedInSpatialStructure")
        if door_guid in {x.GlobalId for x in b.by_guid(r.GlobalId).RelatedElements}
    }
    if len(allowed)!=1:
        raise IndependentComplexV9Error("New Door did not join exactly one original containment relation")
    inv=_inventory(a,b,changed_steps=allowed,new_guids=(opening_guid,door_guid),containment_only=True)
    # Original path connections and all other source native product geometry
    # remain unchanged, not merely Root identity.
    paths0={r.GlobalId:str(r) for r in a.by_type("IfcRelConnectsPathElements")}
    paths1={r.GlobalId:str(r) for r in b.by_type("IfcRelConnectsPathElements")}
    if paths0!=paths1:
        raise IndependentComplexV9Error("Original source native Wall path connectivity changed")
    untouched=_unchanged_mesh(a,b,{host_guid})
    return {
        "status":"INDEPENDENT_SOURCE_BOOLEAN_WALL_NATIVE_EXTERIOR_DOOR_PASS",
        "source_sha256":_sha(source),
        "candidate_sha256":_sha(candidate),
        "source_existing_clipped_wall_guid":host_guid,
        "new_native_Opening_guid":opening_guid,
        "new_native_Door_guid":door_guid,
        "actual_Wall_volume_removed_cubic_m":float(v0-v1),
        "original_native_clipping_body_preserved":True,
        "original_source_wall_connections_preserved":len(paths0),
        "full_thickness_exterior_to_interior_opening":True,
        "all_other_original_products_meshes_preserved":untouched,
        **inv,
        "all45_equivalence_proven":False,
    }
