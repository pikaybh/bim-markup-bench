"""Grader-private IFC product semantic signatures and collateral audit.

No agent source, BIM compiler, task prompt, model response or authoring APIs
are imported. This module only consumes already existing IFC entities.
"""
from __future__ import annotations

import math

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement

from src.evaluation.geometry_metrics import triangle_mesh,UnsupportedGeometry

SCORABLE_PRODUCT_CLASSES=(
    "IfcWall","IfcSlab","IfcSpace","IfcDoor","IfcWindow",
    "IfcColumn","IfcOpeningElement",
)
PROPERTY_EXCLUDES={"id","Tag","LongName","Description"}


def product_by_guid(model:ifcopenshell.file)->dict[str,ifcopenshell.entity_instance]:
    result={}
    for cls in SCORABLE_PRODUCT_CLASSES:
        for product in model.by_type(cls):
            if product.GlobalId in result:
                raise ValueError("Duplicate native IFC product GUID")
            result[product.GlobalId]=product
    return result


def _property_values(element)->dict[str,object]:
    result={}
    for key in ("Name","ObjectType","PredefinedType"):
        value=getattr(element,key,None)
        if value is not None:
            result[key]=str(value)
    try:
        property_sets=ifcopenshell.util.element.get_psets(element,should_inherit=False)
    except (AttributeError,TypeError,RuntimeError):
        property_sets={}
    for pset,payload in property_sets.items():
        if not isinstance(payload,dict):
            continue
        for name,value in payload.items():
            if name in PROPERTY_EXCLUDES or value is None:
                continue
            if isinstance(value,(bool,int,float,str)):
                result[str(pset)+"/"+str(name)]=value
            else:
                result[str(pset)+"/"+str(name)]=str(value)
    try:
        material=ifcopenshell.util.element.get_material(element,should_inherit=False)
    except (AttributeError,TypeError,RuntimeError):
        material=None
    if material is not None:
        result["MaterialType"]=material.is_a()
        if getattr(material,"Name",None) is not None:
            result["MaterialName"]=str(material.Name)
    return result


def _equal_property(a:object,b:object)->bool:
    if isinstance(a,bool) or isinstance(b,bool):
        return a is b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        left=float(a);right=float(b)
        return math.isfinite(left) and math.isfinite(right) and (
            math.isclose(left,right,rel_tol=0.05,abs_tol=1e-6)
        )
    return type(a)==type(b) and a==b


def compare_target_semantics(reference,prediction)->dict:
    if prediction is None:
        return {
            "score":0.0,"class_match":False,
            "properties_fraction":0.0,"matched_property_count":0,
            "reference_property_count":len(_property_values(reference)),
        }
    class_match=reference.is_a()==prediction.is_a()
    properties=_property_values(reference)
    candidate=_property_values(prediction)
    equal=sum(1 for name,value in properties.items()
              if name in candidate and _equal_property(value,candidate[name]))
    fraction=(equal/len(properties)) if properties else 1.0
    return {
        "score":float(0.5*(float(class_match)+fraction)),
        "class_match":bool(class_match),
        "properties_fraction":float(fraction),
        "matched_property_count":equal,
        "reference_property_count":len(properties),
    }


def product_fingerprint(product)->tuple:
    """Deterministic IFC-native typed semantic/placement/mesh signature."""
    properties=tuple(sorted((key,str(value))
                            for key,value in _property_values(product).items()))
    placement=getattr(product,"ObjectPlacement",None)
    try:
        frame=ifcopenshell.util.placement.get_local_placement(placement)
        frame_sig=tuple(float(round(x,6)) for x in frame.ravel())
    except Exception:
        frame_sig=None
    try:
        vertices,triangles=triangle_mesh(product)
        shape_sig=(tuple(float(round(x,6)) for x in vertices.min(axis=0)),
                   tuple(float(round(x,6)) for x in vertices.max(axis=0)),
                   len(triangles))
    except UnsupportedGeometry:
        shape_sig=None
    return (product.is_a(),properties,frame_sig,shape_sig)


def collateral_change_audit(source,reference,prediction,
                            reference_target_guid:str|None=None,
                            prediction_target_guid:str|None=None)->dict:
    """Unexpected non-target product changes get an explicit fail penalty.

    Determine what GT intentionally changes versus original; do not compare
    unrelated products only by global count. Names, properties/materials,
    placement, and mesh bounds are checked under the same IFC kernel.
    """
    baseline=product_by_guid(source)
    expected=product_by_guid(reference)
    actual=product_by_guid(prediction)
    all_guids=set(baseline)|set(expected)|set(actual)
    unexpected=[]
    for guid in sorted(all_guids):
        if guid in (reference_target_guid,prediction_target_guid):
            continue
        lhs=baseline.get(guid);rhs=expected.get(guid);got=actual.get(guid)
        baseline_fp=product_fingerprint(lhs) if lhs else None
        expected_fp=product_fingerprint(rhs) if rhs else None
        actual_fp=product_fingerprint(got) if got else None
        if baseline_fp==expected_fp and baseline_fp!=actual_fp:
            unexpected.append(guid)
        if baseline_fp!=expected_fp and expected_fp!=actual_fp:
            unexpected.append(guid)
    unexpected=sorted(set(unexpected))
    return {
        "collateral_changed_count":len(unexpected),
        "collateral_clean":not bool(unexpected),
        # Do not leak GT-only GlobalIds through score responses.
        "checked_product_guid_count":len(all_guids),
    }
