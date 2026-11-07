"""Native IFC-only geometry comparison for independent BIM-Edit-like scoring.

The area-weighted point sampling is deterministic, but this is NOT official
BIM-Edit evaluation code. We measure real IFC mesh world coordinates in SI
meters using the same pinned IfcOpenShell kernel for GT and prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import ifcopenshell
import ifcopenshell.geom
import numpy as np


class UnsupportedGeometry(ValueError):
    pass


@dataclass(frozen=True)
class GeometrySettings:
    metric_version:str="independent-ifc-surface-cd-v0.1"
    sample_count:int=384
    random_seed:int=2607
    alpha:float=5.0
    absolute_m_tolerance:float=1e-6

    def __post_init__(self):
        if self.metric_version!="independent-ifc-surface-cd-v0.1":
            raise UnsupportedGeometry("Unknown metric/tolerance version")
        if not (64<=self.sample_count<=4096) or not (0<=self.random_seed<=2**31):
            raise UnsupportedGeometry("Unrecognized deterministic geometry sampling policy")
        if not math.isfinite(self.alpha) or self.alpha<=0:
            raise UnsupportedGeometry("Invalid alpha")
        if not math.isfinite(self.absolute_m_tolerance) or self.absolute_m_tolerance<=0:
            raise UnsupportedGeometry("Invalid world-coordinate tolerance")


def triangle_mesh(product:ifcopenshell.entity_instance)->tuple[np.ndarray,np.ndarray]:
    if not getattr(product,"Representation",None):
        raise UnsupportedGeometry("No native IFC geometric representation")
    try:
        settings=ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS,True)
        shape=ifcopenshell.geom.create_shape(settings,product)
        vertices=np.asarray(shape.geometry.verts,dtype=np.float64).reshape((-1,3))
        triangles=np.asarray(shape.geometry.faces,dtype=np.int64).reshape((-1,3))
    except Exception as exc:
        raise UnsupportedGeometry("IFC kernel failed to triangulate product geometry") from exc
    if len(vertices)<3 or len(triangles)<1 or not np.isfinite(vertices).all():
        raise UnsupportedGeometry("Degenerate/nonfinite native IFC product mesh")
    if triangles.max()>=len(vertices) or triangles.min()<0:
        raise UnsupportedGeometry("Invalid generated native mesh indices")
    return vertices,triangles


def surface_sample(product:ifcopenshell.entity_instance,
                   config:GeometrySettings)->np.ndarray:
    vertices,triangles=triangle_mesh(product)
    corners=vertices[triangles]
    left=corners[:,1]-corners[:,0]
    right=corners[:,2]-corners[:,0]
    areas=0.5*np.linalg.norm(np.cross(left,right),axis=1)
    total=float(np.sum(areas))
    if not math.isfinite(total) or total<=0:
        raise UnsupportedGeometry("No nonzero surface to sample")
    rng=np.random.default_rng(config.random_seed)
    selection=rng.choice(len(triangles),size=config.sample_count,
                         replace=True,p=areas/total)
    sampled=corners[selection]
    a=np.sqrt(rng.random(config.sample_count))
    b=rng.random(config.sample_count)
    points=((1-a)[:,None]*sampled[:,0]+
            (a*(1-b))[:,None]*sampled[:,1]+
            (a*b)[:,None]*sampled[:,2])
    if not np.isfinite(points).all():
        raise UnsupportedGeometry("Nonfinite IFC sample coordinates")
    return points


def nearest_median_bidirectional(a:np.ndarray,b:np.ndarray)->float:
    if a.ndim!=2 or b.ndim!=2 or a.shape[1]!=3 or b.shape[1]!=3 or not len(a) or not len(b):
        raise UnsupportedGeometry("Invalid surface point arrays")
    # Bounded 4K×4K matrix; chunking avoids massive temporary allocations.
    def nearest(source,target):
        result=[]
        for start in range(0,len(source),256):
            chunk=source[start:start+256]
            d2=np.sum((chunk[:,None,:]-target[None,:,:])**2,axis=2)
            result.append(np.sqrt(np.min(d2,axis=1)))
        return np.concatenate(result)
    distances=np.concatenate([nearest(a,b),nearest(b,a)])
    return float(np.median(distances))


def compare_surface_geometry(reference:ifcopenshell.entity_instance,
                             prediction:ifcopenshell.entity_instance,
                             config:GeometrySettings=GeometrySettings())->dict:
    a=surface_sample(reference,config)
    b=surface_sample(prediction,config)
    union=np.vstack((a,b))
    diagonal=float(np.linalg.norm(union.max(axis=0)-union.min(axis=0)))
    median=nearest_median_bidirectional(a,b)
    if diagonal<=config.absolute_m_tolerance:
        raise UnsupportedGeometry("Degenerate normalized sampling diagonal")
    reference_vertices,_=triangle_mesh(reference)
    predicted_vertices,_=triangle_mesh(prediction)
    corners_a=np.array((reference_vertices.min(axis=0),reference_vertices.max(axis=0)))
    corners_b=np.array((predicted_vertices.min(axis=0),predicted_vertices.max(axis=0)))
    aabb_dist=float(np.max(np.abs(corners_a-corners_b)))
    # An AABB check is an extra conservative cutoff for near-identical
    # parallel but physically different geometry. It is not the paper's score.
    normalized=float(median/diagonal)
    score=float(math.exp(-config.alpha*normalized))
    if aabb_dist<=config.absolute_m_tolerance and median<=config.absolute_m_tolerance:
        score=1.0
    return {
        "score":score,
        "median_bidirectional_surface_distance_m":median,
        "joint_sampled_bbox_diagonal_m":diagonal,
        "maximum_aabb_coordinate_difference_m":aabb_dist,
        "sample_points_per_target":config.sample_count,
        "geometry_metric":config.metric_version,
        "sampling_seed":config.random_seed,
        "world_unit":"m",
        "sampling_kernel":"IfcOpenShell native triangulation",
    }


def geometry_bbox_center(product:ifcopenshell.entity_instance)->np.ndarray:
    v,_=triangle_mesh(product)
    return (v.min(axis=0)+v.max(axis=0))/2
