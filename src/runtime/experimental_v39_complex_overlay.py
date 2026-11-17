"""Research-only v0.39 partial declarative XML overlay for two exact original IFC4X3 sources.

The existing Revit-native mapped column geometry and clipped Wall geometry
remain the sole authority: never fake them as editable rectangular XML.
The immutable original native source catalog (product meshes + source relations)
is read-only. The only authorable XML is 1 new Slab or an Opening+Door pair.
This is not a lossless IFC serialization or proof of D/I model input parity.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
import hashlib

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.root
import ifcopenshell.api.geometry
import ifcopenshell.api.spatial
import ifcopenshell.api.feature
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np
from lxml import etree

NS="urn:bim-markup-bench:complex-native:v0.39"
Q="{"+NS+"}"
XSD=Path(__file__).resolve().parents[2]/"spec"/"experimental_complex_native_overlay_v039.xsd"
PINS={
    "d7a0c0bda9572787b5b8e7a57b48f8157d898a9f444ac28978e9f9b9a8ff9702":
        ("geometry_test_01","IfcSlab"),
    "c0e0019d7224185d5872b80bdd3652da2bc960b819c1d8c0dd03b213b14847ca":
        ("topological_test_05","IfcOpeningElement+IfcDoor"),
}


class ComplexV039Error(ValueError):
    pass


@dataclass(frozen=True)
class ComplexV039View:
    xml:bytes
    source_sha256:str
    original_sha256:str
    native_schema:str
    task_id:str


@dataclass(frozen=True)
class ComplexV039CompileReport:
    status:str
    task_id:str
    native_schema:str
    created_classes:tuple[str,...]
    source_authoritative:bool=True

    def as_dict(self)->dict:
        return {
            "status":self.status,
            "task_id":self.task_id,
            "native_schema":self.native_schema,
            "created_classes":list(self.created_classes),
            "original_native_source_geometry_unchanged_by_projection":True,
            "partial_declarative_overlay_only":True,
            "source_opaque_geometry_edited":False,
        }


def file_hash(path:Path)->str:
    h=sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def check_pinned_original(original_mm:Path, actual_sha:str,
                          model:ifcopenshell.file)->tuple[str,str]:
    if (not original_mm.is_file() or original_mm.is_symlink()
        or file_hash(original_mm)!=actual_sha or actual_sha not in PINS):
        raise ComplexV039Error("Original complex source bytes not an exact pinned public IFC")
    if model.schema!="IFC4X3":
        raise ComplexV039Error("Original P1 IFC4X3 native schema required")
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    if not math.isfinite(scale) or abs(scale-.001)>1e-12:
        raise ComplexV039Error("Original P1 IFC native millimetre units required")
    return PINS[actual_sha]


def _format(value:float)->str:
    num=float(value)
    if not math.isfinite(num) or abs(num)>1e8:
        raise ComplexV039Error("Nonfinite or out-of-bound original native IFC coordinate")
    v=format(num,".6f").rstrip("0").rstrip(".")
    return "0" if v in ("","-0") else v


def _geom(product):
    if product.Representation is None:
        return None
    settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    shape=ifcopenshell.geom.create_shape(settings,product)
    coordinates=list(shape.geometry.verts)
    faces=list(shape.geometry.faces)
    if (len(coordinates)%3 or len(faces)%3
        or not coordinates or not faces):
        raise ComplexV039Error("Original complex native mesh cannot be captured faithfully")
    vertices=[tuple(round(float(coordinates[i+j]),6) or 0.
                    for j in range(3))
              for i in range(0,len(coordinates),3)]
    if not all(math.isfinite(c) for v in vertices for c in v):
        raise ComplexV039Error("Original complex IFC has invalid world mesh vertices")
    triangles=[]
    for i in range(0,len(faces),3):
        a,b,c=faces[i:i+3]
        if min(a,b,c)<0 or max(a,b,c)>=len(vertices):
            raise ComplexV039Error("Original source native triangle invalid")
        triangles.append(tuple(sorted((vertices[a],vertices[b],vertices[c]))))
    return {
        "vertices":vertices,
        "min":tuple(min(v[j] for v in vertices) for j in range(3)),
        "max":tuple(max(v[j] for v in vertices) for j in range(3)),
        "count":len(triangles),
        "vertices_sha":sha256(repr(sorted(vertices)).encode("ascii")).hexdigest(),
        "triangles_sha":sha256(repr(sorted(triangles)).encode("ascii")).hexdigest(),
    }


def _native_wall_axis(wall)->tuple[tuple[float,float],tuple[float,float]]:
    reps=wall.Representation.Representations
    ax=[r for r in reps if r.RepresentationIdentifier=="Axis"]
    if (len(ax)!=1 or len(ax[0].Items)!=1
        or not ax[0].Items[0].is_a("IfcPolyline")
        or len(ax[0].Items[0].Points)!=2):
        raise ComplexV039Error("Original clipped Wall straight source Axis unsupported")
    mat=np.asarray(ifcopenshell.util.placement.get_local_placement(
        wall.ObjectPlacement),dtype=float)
    axis=[]
    for point in ax[0].Items[0].Points:
        native=list(point.Coordinates)
        if len(native)!=2:
            raise ComplexV039Error("Original source Wall Axis is not XY 2D")
        v=mat@np.array([native[0],native[1],0.,1.])
        axis.append((float(v[0]),float(v[1])))
    if not all(math.isfinite(c) for v in axis for c in v):
        raise ComplexV039Error("Nonfinite original clipped Wall source Axis")
    return axis[0],axis[1]


def _source_relations(model):
    links=[]
    for typ,srcfield,dstfield in (
        ("IfcRelVoidsElement","RelatingBuildingElement","RelatedOpeningElement"),
        ("IfcRelFillsElement","RelatingOpeningElement","RelatedBuildingElement"),
    ):
        for rel in model.by_type(typ):
            links.append((typ,rel.GlobalId,
                getattr(rel,srcfield).GlobalId,getattr(rel,dstfield).GlobalId))
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        for obj in rel.RelatedElements:
            links.append((rel.is_a(),rel.GlobalId,
                rel.RelatingStructure.GlobalId,obj.GlobalId))
    for rel in model.by_type("IfcRelAggregates"):
        for obj in rel.RelatedObjects:
            if hasattr(obj,"GlobalId") and hasattr(rel.RelatingObject,"GlobalId"):
                links.append((rel.is_a(),rel.GlobalId,
                    rel.RelatingObject.GlobalId,obj.GlobalId))
    for rel in model.by_type("IfcRelSpaceBoundary"):
        if rel.RelatingSpace is not None and rel.RelatedBuildingElement is not None:
            links.append((rel.is_a(),rel.GlobalId,
                rel.RelatingSpace.GlobalId,rel.RelatedBuildingElement.GlobalId))
    rootids={x.GlobalId for x in model.by_type("IfcRoot")}
    for typ,guid,src,dst in links:
        if guid not in rootids or src not in rootids or dst not in rootids:
            raise ComplexV039Error("Actual native original IFC relation missing a Root")
    return sorted(set(links))


def _schema()->etree.XMLSchema:
    return etree.XMLSchema(etree.parse(str(XSD)))


def project_complex_v039(source_m:Path,*,original_input_sha256:str)->ComplexV039View:
    source_m=Path(source_m)
    if not source_m.is_file() or source_m.is_symlink():
        raise ComplexV039Error("Native normalized original source unavailable")
    if original_input_sha256 not in PINS:
        raise ComplexV039Error("Complex source overlay not allowed for arbitrary original IFC")
    f=ifcopenshell.open(str(source_m))
    if f.schema!="IFC4X3" or abs(
            ifcopenshell.util.unit.calculate_unit_scale(f)-1.)>1e-12:
        raise ComplexV039Error("Complex original source must be normalized native IFC4X3 metres")
    modelsha=file_hash(source_m)
    root=etree.Element(Q+"Building",nsmap={None:NS},attrib={
        "version":"0.39",
        "sourceModelSha256":modelsha,
        "originalIFCSha256":original_input_sha256,
        "sourceIfcSchema":"IFC4X3",
        "sourceLengthUnit":"METER_NORMALIZED",
        "sourceStateCompleteness":"PARTIAL_NATIVE_REFERENCE_OVERLAY_NOT_LOSSLESS_IFC",
    })
    native=etree.SubElement(root,Q+"OriginalNativeSource",attrib={
        "mode":"READ_ONLY_NATIVE_IFC_AUTHORITY",
        "editableGeometryComplete":"false"})
    products=etree.SubElement(native,Q+"Products")
    p=f.by_type("IfcProduct")
    if len(p)>2000 or not p:
        raise ComplexV039Error("Complex original native product list too large or empty")
    types={}
    for obj in sorted(p,key=lambda x:x.GlobalId):
        attrs={
            "ifcGuid":obj.GlobalId,
            "ifcClass":obj.is_a(),
            "originalSourceOwned":"true",
            "meshStatus":"NONE" if obj.Representation is None else "NATIVE_OPAQUE_WORLD_TRIANGLES",
        }
        if obj.Name:
            attrs["originalName"]=str(obj.Name)[:250]
        if obj.Representation:
            reps=[x for x in obj.Representation.Representations
                  if x.RepresentationIdentifier=="Body"]
            if reps:
                attrs["nativeBodyRepresentationType"]=reps[0].RepresentationType
            geo=_geom(obj)
            attrs["worldVerticesSha256"]=geo["vertices_sha"]
            attrs["worldTrianglesSha256"]=geo["triangles_sha"]
            attrs["worldTriangleCount"]=str(geo["count"])
            for coord,val in zip(("worldMinX","worldMinY","worldMinZ"),
                                 geo["min"]):attrs[coord]=_format(val)
            for coord,val in zip(("worldMaxX","worldMaxY","worldMaxZ"),
                                 geo["max"]):attrs[coord]=_format(val)
            if obj.is_a("IfcWall"):
                a,b=_native_wall_axis(obj)
                attrs.update({
                    "axisStartX":_format(a[0]),"axisStartY":_format(a[1]),
                    "axisEndX":_format(b[0]),"axisEndY":_format(b[1])})
        etree.SubElement(products,Q+"Product",attrib=attrs)
        types[obj.is_a()]=types.get(obj.is_a(),0)+1
    task_id=PINS[original_input_sha256][0]
    expected={"geometry_test_01":{"IfcColumn":4,"IfcBuildingStorey":2},
              "topological_test_05":{"IfcWall":7,"IfcSlab":2,"IfcBuildingStorey":2}}[task_id]
    if any(types.get(klass)!=count for klass,count in expected.items()):
        raise ComplexV039Error("Original pinned source actual native IFC Product inventory changed")
    # The source objects remain native IFC4X3, not typed editable rectangles.
    required_reptype=(
        ("IfcColumn","MappedRepresentation") if task_id=="geometry_test_01"
        else ("IfcWall","Clipping"))
    if any(
        next((rep.RepresentationType for rep in product.Representation.Representations
              if rep.RepresentationIdentifier=="Body"),None)!=required_reptype[1]
        for product in p if product.is_a()==required_reptype[0]
    ):
        raise ComplexV039Error("Original mapped/clipped native physical geometry changed")
    relations=etree.SubElement(native,Q+"Relations")
    rels=_source_relations(f)
    if len(rels)>10000:
        raise ComplexV039Error("Complex original native relationship list too large")
    for klass,rel,src,dst in rels:
        etree.SubElement(relations,Q+"Relation",attrib={
            "ifcGuid":rel,"ifcClass":klass,"relatingGuid":src,
            "relatedGuid":dst,"originalSourceOwned":"true"})
    etree.SubElement(root,Q+"Elements")
    result=etree.tostring(root,encoding="utf8",xml_declaration=True,
                          pretty_print=False)
    if len(result)>300000 or not _schema().validate(root):
        raise ComplexV039Error("New complex native overlay projection does not validate")
    if file_hash(source_m)!=modelsha:
        raise ComplexV039Error("Original native IFC changed during source projection")
    return ComplexV039View(result,modelsha,original_input_sha256,f.schema,task_id)


def _num(node,attr:str,lower:float=-100.,upper:float=100.)->float:
    val=node.get(attr)
    if val is None:
        raise ComplexV039Error("Missing native geometry numeric XML field: "+attr)
    try:
        result=float(val)
    except (ValueError,OverflowError) as exc:
        raise ComplexV039Error("Malformed native geometry XML number") from exc
    if not math.isfinite(result) or not lower<=result<=upper:
        raise ComplexV039Error("Native geometry XML dimensions out of safe bounded range")
    return result


def _parse_plan(source_m:Path,xml:bytes,view:ComplexV039View,model)->dict:
    if not xml or len(xml)>300000 or b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
        raise ComplexV039Error("XML DTD, entity or oversized payload not allowed")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True,
                           remove_comments=False,huge_tree=False)
    try:
        root=etree.fromstring(xml,parser=parser)
    except etree.XMLSyntaxError as exc:
        raise ComplexV039Error("Malformed full declarative native XML source") from exc
    if not _schema().validate(root):
        raise ComplexV039Error("Complete declarative source does not match v0.39 XML XSD")
    if any(isinstance(n,(etree._Comment,etree._ProcessingInstruction))
           for n in root.iter()):
        raise ComplexV039Error("Source injection of XML comments/PIs refused")
    baseline=etree.fromstring(view.xml,parser=parser)
    if (dict(root.attrib)!=dict(baseline.attrib)
        or etree.tostring(root.find(Q+"OriginalNativeSource"),method="c14n")!=
           etree.tostring(baseline.find(Q+"OriginalNativeSource"),method="c14n")):
        raise ComplexV039Error("Immutable native source inventory/mesh/relations changed")
    children=list(root.find(Q+"Elements"))
    if any(x.tail and x.tail.strip() for x in children):
        raise ComplexV039Error("Imperative text payload not allowed in XML Elements")
    srcids={x.GlobalId for x in model.by_type("IfcRoot")}
    if view.task_id=="geometry_test_01":
        if len(children)!=1 or children[0].tag!=Q+"Slab":
            raise ComplexV039Error("P1 geometry only one new declarative IfcSlab supported")
        slab=children[0]
        level=next((e for e in model.by_type("IfcBuildingStorey")
                    if e.GlobalId==slab.get("levelGuid")),None)
        if level is None:
            raise ComplexV039Error("New Slab must reference an original native Storey GUID")
        x,y,z=(_num(slab,k,-10.,30.) for k in ("x","y","z"))
        length=_num(slab,"length",.1,10.)
        depth=_num(slab,"depth",.1,10.)
        t=_num(slab,"thickness",.05,.8)
        if x+length>30. or y+depth>30.:
            raise ComplexV039Error("New slab lies outside bounded original source working area")
        ids=[slab.get("id")]
        plan={"kind":"Slab","level":level,"x":x,"y":y,"z":z,
              "length":length,"depth":depth,"thickness":t}
    else:
        if len(children)!=2 or [x.tag for x in children]!=[
                Q+"Opening",Q+"Door"]:
            raise ComplexV039Error("P1 exterior Door requires exactly Opening then Door")
        op,door=children
        if door.get("id")==op.get("id"):
            raise ComplexV039Error("Duplicate or missing declarative new IDs")
        if door.get("opening")!=op.get("id"):
            raise ComplexV039Error("P1 Door must fill exactly its declared new Opening")
        width=_num(op,"width",.6,2.)
        height=_num(op,"height",1.5,2.4)
        if abs(width-_num(door,"width",.6,2.))>1e-8 or abs(
                height-_num(door,"height",1.5,2.4))>1e-8:
            raise ComplexV039Error("New Door and hosted Opening declared sizes differ")
        x,y=(_num(op,k,-50.,50.) for k in ("centerX","centerY"))
        z=_num(op,"sillZ",-10.,50.)
        host=next((e for e in model.by_type("IfcWall")
                   if e.GlobalId==op.get("hostGuid")),None)
        if host is None:
            raise ComplexV039Error("Native Door cannot attach to non-original source Wall")
        if host.GlobalId not in srcids:
            raise ComplexV039Error("Native Door host is not original source Wall")
        rep=next((r for r in host.Representation.Representations
                  if r.RepresentationIdentifier=="Body"),None)
        if rep is None or rep.RepresentationType!="Clipping" or host.HasOpenings:
            raise ComplexV039Error("Native Door host requires intact original clipped source Wall")
        a,b=_native_wall_axis(host)
        dx,dy=b[0]-a[0],b[1]-a[1]
        run=math.hypot(dx,dy)
        if not run>width+.6:
            raise ComplexV039Error("Source clipped wall shorter than new Door opening")
        tangent=np.asarray((dx/run,dy/run))
        normal=np.asarray((-tangent[1],tangent[0]))
        delta=np.asarray((x-a[0],y-a[1]))
        distance=float(np.dot(delta,tangent))
        lateral=float(np.dot(delta,normal))
        geo=_geom(host)
        face_proj=[float(np.dot(np.asarray(pt[:2]),normal))
                   for pt in geo["vertices"]]
        thick=max(face_proj)-min(face_proj)
        original_center=(max(face_proj)+min(face_proj))/2.
        axis_center=float(np.dot(np.asarray(a),normal))
        if not .14<=thick<=.4 or abs(original_center-axis_center)>.025:
            raise ComplexV039Error("Original clipped Wall native physical thickness or Axis ambiguous")
        if not width/2+.2<=distance<=run-width/2-.2 or abs(lateral)>.008:
            raise ComplexV039Error("Door must sit on original native Wall Axis, away from joins")
        if z<geo["min"][2]-.00001 or z+height>geo["max"][2]-.15:
            raise ComplexV039Error("Door sill/top exceeds physical source clipped Wall height")
        original_container=ifcopenshell.util.element.get_container(host)
        if original_container is None or not original_container.is_a("IfcBuildingStorey"):
            raise ComplexV039Error("Original physical host Wall lacks unique source Storey")
        ids=[op.get("id"),door.get("id")]
        plan={"kind":"Door","host_guid":host.GlobalId,
              "level":original_container,"x":x,"y":y,"z":z,
              "width":width,"height":height,"thickness":thick,
              "angle":math.atan2(float(tangent[1]),float(tangent[0]))}
    if not all(x and x.isascii() for x in ids) or len(set(ids))!=len(ids):
        raise ComplexV039Error("Duplicate or missing declarative new IDs")
    guids={x:ifcopenshell.guid.compress(
        hashlib.md5((view.source_sha256+"|"+x).encode("ascii")).hexdigest())
           for x in ids}
    if len(set(guids.values()))!=len(guids) or any(x in srcids for x in guids.values()):
        raise ComplexV039Error("New declarative GUID conflicts with original source IFC")
    plan["ids"]=ids
    plan["guids"]=guids
    return plan


def _body(model):
    candidates=[r for r in model.by_type("IfcGeometricRepresentationSubContext")
        if r.ContextIdentifier=="Body" and r.TargetView=="MODEL_VIEW"]
    if len(candidates)!=1:
        raise ComplexV039Error("Expected exactly one native source Body MODEL_VIEW context")
    return candidates[0]


def _box_rep(model,body,w,d,h):
    profile=model.createIfcRectangleProfileDef("AREA",None,None,w,d)
    return ifcopenshell.api.geometry.add_profile_representation(
        model,context=body,profile=profile,depth=h)


def _pose(model,product,xyz,angle=0.):
    c,s=math.cos(angle),math.sin(angle)
    matrix=np.eye(4)
    matrix[:3,3]=xyz
    matrix[0,0],matrix[0,1],matrix[1,0],matrix[1,1]=c,-s,s,c
    ifcopenshell.api.geometry.edit_object_placement(
        model,product=product,matrix=matrix,is_si=True)


def compile_complex_v039(source_m:Path,edited_xml:bytes,
                         destination_m:Path,*,original_input_sha256:str):
    source_m,destination_m=Path(source_m),Path(destination_m)
    if (not source_m.is_file() or source_m.is_symlink()
        or destination_m.exists() or destination_m.is_symlink()
        or source_m.resolve()==destination_m.resolve()):
        raise ComplexV039Error("Native source and candidate must be distinct existing/unused paths")
    view=project_complex_v039(source_m,original_input_sha256=original_input_sha256)
    model=ifcopenshell.open(str(source_m))
    plan=_parse_plan(source_m,edited_xml,view,model)
    originally_present={x.GlobalId for x in model.by_type("IfcRoot")}
    old_hist_ids={x.id() for x in model.by_type("IfcOwnerHistory")}
    old_containment={
        x.GlobalId:tuple(y.GlobalId for y in x.RelatedElements)
        for x in model.by_type("IfcRelContainedInSpatialStructure")
    }
    body=_body(model)
    created=[]
    if plan["kind"]=="Slab":
        slab=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcSlab",
            name="P1 research-only full-declarative XML native slab")
        slab.GlobalId=plan["guids"][plan["ids"][0]]
        rep=_box_rep(model,body,plan["length"],plan["depth"],plan["thickness"])
        ifcopenshell.api.geometry.assign_representation(
            model,product=slab,representation=rep)
        _pose(model,slab,(plan["x"]+plan["length"]/2,
                          plan["y"]+plan["depth"]/2,plan["z"]))
        ifcopenshell.api.spatial.assign_container(
            model,products=[slab],relating_structure=plan["level"])
        created.append(slab)
    else:
        opening=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcOpeningElement",
            name="P1 research-only hosted native clipped-Wall opening")
        opening.GlobalId=plan["guids"][plan["ids"][0]]
        rep=_box_rep(model,body,plan["width"],plan["thickness"]+.2,plan["height"])
        ifcopenshell.api.geometry.assign_representation(
            model,product=opening,representation=rep)
        _pose(model,opening,(plan["x"],plan["y"],plan["z"]),plan["angle"])
        ifcopenshell.api.feature.add_feature(
            model,feature=opening,element=model.by_guid(plan["host_guid"]))
        door=ifcopenshell.api.root.create_entity(
            model,ifc_class="IfcDoor",
            name="P1 research-only full-declarative XML hosted Door")
        door.GlobalId=plan["guids"][plan["ids"][1]]
        door.OverallWidth=plan["width"]
        door.OverallHeight=plan["height"]
        rep=_box_rep(model,body,plan["width"],.08,plan["height"])
        ifcopenshell.api.geometry.assign_representation(
            model,product=door,representation=rep)
        _pose(model,door,(plan["x"],plan["y"],plan["z"]),plan["angle"])
        ifcopenshell.api.feature.add_filling(model,opening=opening,element=door)
        ifcopenshell.api.spatial.assign_container(
            model,products=[door],relating_structure=plan["level"])
        created.extend((opening,door))
    if not originally_present.issubset(
        {x.GlobalId for x in model.by_type("IfcRoot")}):
        raise ComplexV039Error("Original native IFC Root object deleted by writer")
    # Existing spatial membership order is source-controlled, not API-set order.
    for guid,before in old_containment.items():
        rel=model.by_guid(guid)
        members={e.GlobalId for e in rel.RelatedElements}
        additions=members-set(before)
        if not set(before)<=members or len(additions)>1 or not additions<=set(
                plan["guids"].values()):
            raise ComplexV039Error("Original native containment membership unexpectedly mutated")
        rel.RelatedElements=tuple(model.by_guid(g)
            for g in (*before,*sorted(additions)))
    # New relations/OwnerHistories from IfcOpenShell API have random IDs or
    # wall-clock fields. Anchor them deterministically in the PUBLIC SOURCE,
    # as with the independently verified v0.8 compiler, for replayable output.
    existing_ids={x.GlobalId for x in model.by_type("IfcRoot")}
    for kind in ("IfcRelContainedInSpatialStructure","IfcRelVoidsElement",
                 "IfcRelFillsElement"):
        newrels=[x for x in model.by_type(kind)
                 if x.GlobalId not in originally_present]
        for index,rel in enumerate(sorted(newrels,key=lambda x:x.id())):
            deterministic=ifcopenshell.guid.compress(hashlib.md5(
                (view.source_sha256+"|relation|"+kind+"|"+str(index)).encode("ascii")
                ).hexdigest())
            if deterministic in existing_ids:
                raise ComplexV039Error("Deterministic original native relation GUID collision")
            existing_ids.add(deterministic)
            rel.GlobalId=deterministic
    old_epochs=[int(x.CreationDate) for x in model.by_type("IfcOwnerHistory")
                if x.id() in old_hist_ids and x.CreationDate is not None]
    new_hist=[x for x in model.by_type("IfcOwnerHistory")
              if x.id() not in old_hist_ids]
    if new_hist and not old_epochs:
        raise ComplexV039Error("No source-anchored epoch for new owner history")
    for entry in new_hist:
        entry.CreationDate=max(old_epochs)
        if entry.LastModifiedDate is not None:
            entry.LastModifiedDate=max(old_epochs)
    if file_hash(source_m)!=view.source_sha256:
        raise ComplexV039Error("Native source changed during bounded declarative write")
    # Staging: write only a new separately named IFC file after validation.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix="p1-complex-compile-") as d:
        stage=Path(d)/"stage.ifc"
        model.write(str(stage))
        reopened=ifcopenshell.open(str(stage))
        if reopened.schema!="IFC4X3" or abs(
                ifcopenshell.util.unit.calculate_unit_scale(reopened)-1.)>1e-12:
            raise ComplexV039Error("Compiled original native IFC schema/units changed")
        for obj in created:
            checked=reopened.by_guid(obj.GlobalId)
            if checked is None or checked.is_a()!=obj.is_a():
                raise ComplexV039Error("Declared new native Product not created")
            _geom(checked)
        if file_hash(source_m)!=view.source_sha256:
            raise ComplexV039Error("Native source changed before compiler commit")
        with destination_m.open("xb") as file:
            file.write(stage.read_bytes())
    return ComplexV039CompileReport(
        status="COMMITTED_SOURCE_SCHEMA_PRESERVED_CREATE_ORIGINAL_IFC4X3_COMPLEX_V039",
        task_id=view.task_id,native_schema="IFC4X3",
        created_classes=tuple(x.is_a() for x in created))
