"""v0.38 opt-in, source-pinned original IFC2X3/IFC4 live XML-session gate.

Research tool HOST ONLY. The model still edits complete declarative v0.8 XML,
never a command list or Python. Existing legacy v0.8 trusted compiler and
independent native shapes are checked AFTER metre->original-mm restoration.
No public benchmark scorer, hidden GT, model provider or Docker access.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit


class LegacyLiveGateError(ValueError):
    pass


# Exact actual original 45 public IFC byte-level identities (v0.37 frozen).
# Do NOT expand to other files or treat arbitrary IFC2X3/IFC4 as supported.
SOURCE_PROFILES = {
    "88f315a0ec26c1e8bd5ea84fb254cf1d30b0ef143f03bbeffcee1dd8a69a2a59":
        ("geometry_test_03","IFC2X3","Opening+Door"),
    "d2d6a5e39dc144ef49a44baca8d4039c267cc3bb8b7bfc5eb473c1207b7a62ea":
        ("geometry_test_04","IFC2X3","Space"),
    "f637eceda5155c846f2c3f24e215ef2161151ccbff1ba2f9e098c71463322bcc":
        ("geometry_test_05","IFC4","Wall"),
}
TASKS=tuple(sorted(v[0] for v in SOURCE_PROFILES.values()))


def check_original_legacy_source(path:Path, file_sha:str,
                                 opened:ifcopenshell.file)->tuple[str,str,str]:
    path=Path(path)
    if not path.is_file() or path.is_symlink():
        raise LegacyLiveGateError("Opt-in original legacy source must be a regular file")
    if file_sha not in SOURCE_PROFILES:
        raise LegacyLiveGateError("Opt-in original legacy XML requires exact pinned source SHA")
    task,schema,klass=SOURCE_PROFILES[file_sha]
    if opened.schema != schema:
        raise LegacyLiveGateError("Pinned original legacy native IFC schema mismatch")
    scale=ifcopenshell.util.unit.calculate_unit_scale(opened)
    if not math.isfinite(scale) or abs(scale-.001)>1e-12:
        raise LegacyLiveGateError("Pinned original legacy input units must be native millimetres")
    actual=sha256(path.read_bytes()).hexdigest()
    if actual!=file_sha:
        raise LegacyLiveGateError("Pinned source bytes changed before original legacy session")
    return task,schema,klass


def _roots(f:ifcopenshell.file)->dict[str,ifcopenshell.entity_instance]:
    roots={e.GlobalId:e for e in f.by_type("IfcRoot")}
    if len(roots)!=len(f.by_type("IfcRoot")):
        raise LegacyLiveGateError("Original native IFC contains duplicate Root GlobalIds")
    return roots


def _world_mesh(product:ifcopenshell.entity_instance):
    """Independent physical *comparison* oracle for restored native output.

    IfcOpenShell geometry tessellates into metres (default convert-back-units
    is False), even if the IFC native file is in millimetres. Face order,
    winding, source geometry vertices and renderer diagonal are checked
    separately; signed negative zero is normalized before hashing.
    """
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    try:
        shape=ifcopenshell.geom.create_shape(settings,product)
    except Exception as exc:
        raise LegacyLiveGateError(
            "Original-product physical mesh cannot be safely verified") from exc
    raw=list(shape.geometry.verts)
    faces=list(shape.geometry.faces)
    if len(raw)%3 or len(faces)%3 or not raw or not faces:
        raise LegacyLiveGateError("Original source native product mesh is incomplete")
    vertices=[tuple(float(raw[i+j]) for j in range(3))
              for i in range(0,len(raw),3)]
    if not all(math.isfinite(x) for v in vertices for x in v):
        raise LegacyLiveGateError("Native product geometry contains nonfinite vertices")
    lo=tuple(min(v[j] for v in vertices) for j in range(3))
    hi=tuple(max(v[j] for v in vertices) for j in range(3))
    # 1 micrometre canonical world points, preserve multiplicity.
    def canonical(value:float,digits:int)->float:
        n=round(value,digits)
        return 0.0 if n==0.0 else n
    points=[tuple(canonical(x,6) for x in v) for v in vertices]
    triangles=[]
    surface_areas={}
    for a,b,c in zip(faces[::3],faces[1::3],faces[2::3]):
        if max(a,b,c)>=len(points) or min(a,b,c)<0:
            raise LegacyLiveGateError("Native triangle has invalid vertex index")
        triangles.append(tuple(sorted((points[a],points[b],points[c]))))
        va,vb,vc=vertices[a],vertices[b],vertices[c]
        ux,uy,uz=(vb[j]-va[j] for j in range(3))
        vx,vy,vz=(vc[j]-va[j] for j in range(3))
        n=[uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx]
        mag=math.sqrt(sum(t*t for t in n))
        if not mag>1e-14:
            raise LegacyLiveGateError("Native original surface triangle is degenerate")
        norm=[t/mag for t in n]
        first=next((x for x in norm if abs(x)>1e-8),0.)
        if first<0:norm=[-x for x in norm]
        plane=tuple(canonical(x,6) for x in norm)+(
            canonical(sum(norm[j]*va[j] for j in range(3)),5),)
        surface_areas[plane]=surface_areas.get(plane,0.)+mag/2.
    triangles.sort()
    triangles_sha=sha256(repr(triangles).encode("ascii")).hexdigest()
    vertex_sha=sha256(repr(sorted(points)).encode("ascii")).hexdigest()
    # Triangles may switch diagonal across native-mm->m->mm roundtrip while
    # representing the *same* planar closed surface. Verify each face plane's
    # total physical area and all native world vertex positions, not the
    # arbitrary triangulator's choice of diagonal. No blanket bbox allowance.
    area_hash=sha256(repr(sorted((plane,round(area,5))
            for plane,area in surface_areas.items())).encode("ascii")).hexdigest()
    return lo,hi,len(triangles),triangles_sha,vertex_sha,area_hash


def _member_map(f:ifcopenshell.file,classname:str,relation:str):
    return {
        e.GlobalId:frozenset(x.GlobalId for x in getattr(e,relation))
        for e in f.by_type(classname)
    }


def verify_native_original_restored(
        original_mm:Path, output_mm:Path, *,
        task_id:str,expected_schema:str)->dict:
    """Fail closed if restored original-native-mm IFC damages source evidence.

    This is an independent *source+output* IFC comparison. Does NOT claim
    byte-equality, full STEP metadata preservation, semantic reference
    correctness for benchmark answer, or full source/model information parity.
    """
    src=ifcopenshell.open(str(original_mm))
    out=ifcopenshell.open(str(output_mm))
    if src.schema!=out.schema or out.schema!=expected_schema:
        raise LegacyLiveGateError("Restored result changed original IFC schema")
    for f in (src,out):
        if abs(ifcopenshell.util.unit.calculate_unit_scale(f)-.001)>1e-12:
            raise LegacyLiveGateError("Original native millimetre unit not restored")
    old_roots=_roots(src)
    new_roots=_roots(out)
    if not set(old_roots)<=set(new_roots):
        raise LegacyLiveGateError("Previously existing IFC Root GlobalId disappeared")
    old_products={x.GlobalId:x for x in src.by_type("IfcProduct")}
    new_products={x.GlobalId:x for x in out.by_type("IfcProduct")}
    if not set(old_products)<=set(new_products):
        raise LegacyLiveGateError("Previously existing native IFC Product removed")
    new_objects={g:x for g,x in new_products.items() if g not in old_products}
    expected={
        "geometry_test_03":Counter({"IfcOpeningElement":1,"IfcDoor":1}),
        "geometry_test_04":Counter({"IfcSpace":1}),
        "geometry_test_05":Counter({"IfcWall":1}),
    }
    if task_id not in expected or Counter(x.is_a() for x in new_objects.values())!=expected[task_id]:
        raise LegacyLiveGateError("Native output added wrong IFC Product type/count")
    for gid,prior in old_roots.items():
        now=new_roots[gid]
        if prior.is_a()!=now.is_a():
            raise LegacyLiveGateError("Original native IfcRoot class mutated")
        for name in ("Name","Description"):
            if getattr(prior,name,None)!=getattr(now,name,None):
                raise LegacyLiveGateError("Original native IfcRoot identity/name/description altered")
    old_contained=_member_map(src,"IfcRelContainedInSpatialStructure","RelatedElements")
    new_contained=_member_map(out,"IfcRelContainedInSpatialStructure","RelatedElements")
    if not set(old_contained)<=set(new_contained):
        raise LegacyLiveGateError("Original native IFC containment relation disappeared")
    for gid,oldmembers in old_contained.items():
        newmembers=new_contained[gid]
        if not oldmembers<=newmembers or not (newmembers-oldmembers)<=set(new_objects):
            raise LegacyLiveGateError("Original source native containment membership changed")
    old_aggregated=_member_map(src,"IfcRelAggregates","RelatedObjects")
    new_aggregated=_member_map(out,"IfcRelAggregates","RelatedObjects")
    if not set(old_aggregated)<=set(new_aggregated):
        raise LegacyLiveGateError("Original source native aggregation relation disappeared")
    for gid,oldmembers in old_aggregated.items():
        newmembers=new_aggregated[gid]
        if not oldmembers<=newmembers or not (newmembers-oldmembers)<=set(new_objects):
            raise LegacyLiveGateError("Original source native aggregation membership changed")
    old_void={(x.RelatingBuildingElement.GlobalId,x.RelatedOpeningElement.GlobalId)
              for x in src.by_type("IfcRelVoidsElement")}
    new_void={(x.RelatingBuildingElement.GlobalId,x.RelatedOpeningElement.GlobalId)
              for x in out.by_type("IfcRelVoidsElement")}
    old_fill={(x.RelatingOpeningElement.GlobalId,x.RelatedBuildingElement.GlobalId)
              for x in src.by_type("IfcRelFillsElement")}
    new_fill={(x.RelatingOpeningElement.GlobalId,x.RelatedBuildingElement.GlobalId)
              for x in out.by_type("IfcRelFillsElement")}
    if not (old_void<=new_void and old_fill<=new_fill):
        raise LegacyLiveGateError("Original native void/fill topology relationship disappeared")
    host_guid=None
    if task_id=="geometry_test_03":
        openings={g for g,x in new_objects.items() if x.is_a("IfcOpeningElement")}
        doors={g for g,x in new_objects.items() if x.is_a("IfcDoor")}
        new_voices=new_void-old_void
        new_fills=new_fill-old_fill
        if len(new_voices)!=1 or len(new_fills)!=1:
            raise LegacyLiveGateError("Native Door requires one new source Wall void and one fill")
        host_guid,opening_guid=next(iter(new_voices))
        fill_opening,door_guid=next(iter(new_fills))
        if (host_guid not in old_products
                or old_products[host_guid].is_a()!="IfcWallStandardCase"
                or openings!={opening_guid}
                or fill_opening!=opening_guid or doors!={door_guid}):
            raise LegacyLiveGateError("Native Door does not void original source Wall")
    elif new_void!=old_void or new_fill!=old_fill:
        raise LegacyLiveGateError("Native simple CREATE unexpectedly introduced void/fill")
    unchanged_original_triangle_count=0
    retessellated_original_products=0
    for gid,original_product in old_products.items():
        current=new_products[gid]
        if original_product.is_a()!=current.is_a():
            raise LegacyLiveGateError("Original IFC Product class changed")
        if original_product.Representation is None:
            if current.Representation is not None:
                raise LegacyLiveGateError("Original unrepresented IFC Product changed into geometry")
            continue
        before=_world_mesh(original_product)
        after=_world_mesh(current)
        if gid==host_guid:
            if (any(abs(a-b)>1e-5 for a,b in zip(before[0],after[0]))
                    or any(abs(a-b)>1e-5 for a,b in zip(before[1],after[1]))
                    or after[2]<=before[2]):
                raise LegacyLiveGateError("Original native host Wall void geometry is not physical")
        else:
            if before[2]!=after[2] or before[4]!=after[4] or before[5]!=after[5]:
                raise LegacyLiveGateError(
                    "Unrelated native product world vertices or physical planar faces changed")
            if before[3]!=after[3]:
                retessellated_original_products+=1
            unchanged_original_triangle_count+=before[2]
    if task_id=="geometry_test_03":
        if not new_objects or not new_void-old_void or not new_fill-old_fill:
            raise LegacyLiveGateError("Native Door CREATE lacks required physical topology")
    # The existing v0.8 compiler checks the candidate in converted metres.
    # Independently verify all *new* physical products still exist and are
    # nondegenerate after restoring the original IFC2X3/IFC4 native mm file.
    # Never accept a restored product based on class + GUID alone.
    for new_guid,entity in new_objects.items():
        if entity.Representation is None:
            raise LegacyLiveGateError("Newly created native IFC physical representation missing")
        lo,hi,faces,*_= _world_mesh(entity)
        dims=tuple(hi[j]-lo[j] for j in range(3))
        if (faces<12 or any(not math.isfinite(d) or d<.05 or d>100.
                         for d in dims)):
            raise LegacyLiveGateError("Newly created native IFC restored physical shape invalid")
    return {
        "native_output_schema":out.schema,
        "native_output_length_unit_to_m":.001,
        "all_original_root_GUIDs_preserved":len(old_roots),
        "all_original_products_preserved":len(old_products),
        "new_native_products_by_class":dict(sorted(Counter(
            x.is_a() for x in new_objects.values()).items())),
        "unchanged_original_product_verified_surface_triangle_count":
            unchanged_original_triangle_count,
        "original_products_with_different_coplanar_triangle_diagonal":
            retessellated_original_products,
        "physical_surface_preservation_verified_by_vertex_multiset_and_planar_area":True,
        "full_same_triangle_vertex_triples_across_unit_roundtrip":
            retessellated_original_products==0,
        "original_wall_physically_voided":host_guid is not None,
        "source_original_units_and_schema_preserved":True,
        "full_original_step_text_byte_equality_proven":False,
        "full_original_IFC_information_parity_proven":False,
    }
