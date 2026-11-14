"""v0.18 research: shared read-only original IFC facts, not a BIM authoring API.

An isolated pre-model process uses ONLY the public original IFC to make a
canonical, schema-versioned fact packet. Two separate read sessions (D/I)
serve *identical* data from the identical frozen bytes, with equal call caps
and SHA-256 receipts. Does not expose original IFC file paths, evaluator
targets, model outputs or a native IFC object to either read session.

IMPORTANT: this limited fact packet and its equality do NOT sandbox a Python
LLM tool and do NOT establish complete native IFC informational equivalence.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit

PACKET_SCHEMA = "bibimbap.original_ifc_common_read.v018"
DEFAULT_CALL_CAP = 25
_MAX_PRODUCTS = 10_000
_GLOBAL_ID = re.compile(r"^[0-9A-Za-z_$]{22}$")
_HEX_HASH = re.compile(r"^[a-f0-9]{64}$")


class CommonReadBlocked(ValueError):
    """An unsupported or non-reproducible source/query must fail closed."""


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def canonical_json(data: object) -> bytes:
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf8")


def _float(value: float) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise CommonReadBlocked("Non-finite source world coordinate")
    v = round(x, 8)
    return 0.0 if v == 0 else v


def _bbox(product, settings):
    if not getattr(product, "Representation", None):
        return {"status": "NO_SHAPE_REPRESENTATION", "bbox_world_m": None}
    try:
        shape = ifcopenshell.geom.create_shape(settings, product)
        coords = shape.geometry.verts
        if len(coords) < 3 or len(coords) % 3 != 0:
            return {"status": "MESH_EMPTY", "bbox_world_m": None}
        if any(not math.isfinite(float(x)) for x in coords):
            return {"status": "MESH_NONFINITE", "bbox_world_m": None}
        return {
            "status": "PHYSICAL_WORLD_BBOX_METRES",
            "bbox_world_m": [
                [_float(min(coords[axis::3])), _float(max(coords[axis::3]))]
                for axis in range(3)
            ],
        }
    except Exception:
        # Cannot invent geometry or silently claim completeness. Exception
        # text may include local paths and is never returned to either arm.
        return {"status": "MESH_UNAVAILABLE", "bbox_world_m": None}


def _world_placement(product, model, scale):
    obj = product.ObjectPlacement
    if obj is None:
        return {"status": "NO_OBJECT_PLACEMENT", "origin_world_m": None,
                "basis_world": None}
    if not obj.is_a("IfcLocalPlacement"):
        return {"status": "UNSUPPORTED_PLACEMENT", "origin_world_m": None,
                "basis_world": None}
    try:
        matrix = ifcopenshell.util.placement.get_local_placement(obj)
        origin = [_float(matrix[i][3] * scale) for i in range(3)]
        basis = [
            [_float(matrix[i][j]) for j in range(3)] for i in range(3)
        ]
        return {
            "status": "WORLD_PLACEMENT_AVAILABLE",
            "origin_world_m": origin,
            "basis_world": basis,
        }
    except Exception:
        return {"status": "WORLD_PLACEMENT_UNAVAILABLE", "origin_world_m": None,
                "basis_world": None}


def _referenced_products(item):
    if item is None:
        return set()
    if isinstance(item, ifcopenshell.entity_instance):
        if item.is_a("IfcProduct") and getattr(item, "GlobalId", None):
            return {item.GlobalId}
        # Do not recurse through entire IFC graphs here: relationship
        # argument references directly identify product-side membership.
        return set()
    if isinstance(item, (tuple, list)):
        found = set()
        for sub in item:
            found.update(_referenced_products(sub))
        return found
    return set()


def build_public_source_packet(source: Path, public_question_sha256: str) -> bytes:
    """Read original IFC once, return deterministic bytes; never write IFC."""
    if not source.is_file() or source.is_symlink():
        raise CommonReadBlocked("Expected an existing public source IFC")
    if not _HEX_HASH.fullmatch(public_question_sha256):
        raise CommonReadBlocked("Public question must be supplied by SHA-256")
    original_sha = _sha(source.read_bytes())
    original = ifcopenshell.open(str(source))
    if original.schema not in ("IFC2X3", "IFC4", "IFC4X3"):
        raise CommonReadBlocked("Original IFC source schema unsupported")
    scale = float(ifcopenshell.util.unit.calculate_unit_scale(original))
    if not math.isfinite(scale) or scale <= 0:
        raise CommonReadBlocked("Invalid original IFC source length unit")
    products = list(original.by_type("IfcProduct"))
    if len(products) > _MAX_PRODUCTS:
        raise CommonReadBlocked("Original product count exceeds audited packet budget")
    product_by_guid = {}
    source_types = Counter()
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    geometry_status = Counter()
    placement_status = Counter()

    for product in products:
        guid = getattr(product, "GlobalId", None)
        if not isinstance(guid, str) or not _GLOBAL_ID.fullmatch(guid):
            raise CommonReadBlocked("Original IfcProduct lacks valid public source GlobalId")
        if guid in product_by_guid:
            raise CommonReadBlocked("Duplicate original public source GlobalId")
        category = product.is_a()
        geo = _bbox(product, settings)
        placement = _world_placement(product, original, scale)
        source_types[category] += 1
        geometry_status[geo["status"]] += 1
        placement_status[placement["status"]] += 1
        try:
            container = ifcopenshell.util.element.get_container(product)
            container_guid = (container.GlobalId if container is not None
                              and getattr(container, "GlobalId", None) else None)
        except Exception:
            container_guid = None

        native_representation = []
        shape = getattr(product, "Representation", None)
        if shape is not None:
            for rep in shape.Representations or ():
                native_representation.append({
                    "representation_identifier": rep.RepresentationIdentifier,
                    "representation_type": rep.RepresentationType,
                    "item_count": len(rep.Items or ()),
                })
        product_by_guid[guid] = {
            "global_id": guid,
            "ifc_class": category,
            "name": product.Name,
            "description": getattr(product, "Description", None),
            "spatial_container_guid": container_guid,
            "placement": placement,
            "geometry": geo,
            "representations": native_representation,
        }

    source_relations = []
    product_link_map = {g: [] for g in product_by_guid}
    for relation in original.by_type("IfcRelationship"):
        guid = getattr(relation, "GlobalId", None)
        if not isinstance(guid, str) or not _GLOBAL_ID.fullmatch(guid):
            raise CommonReadBlocked("Original IfcRelationship lacks valid GlobalId")
        # Direct product references only, label their attribute roles to
        # preserve relation direction, without fabricating indirect links.
        roles = {}
        for idx in range(len(relation)):
            attr = relation.attribute_name(idx)
            refs = sorted(_referenced_products(relation[idx]))
            if refs:
                roles[attr] = refs
        if not roles:
            # Keep relation inventory even when it references no IfcProduct;
            # it may have other IFC objects/properties not included here.
            roles = {}
        record = {
            "global_id": guid,
            "ifc_class": relation.is_a(),
            "product_roles": roles,
            "non_product_link_details_exhaustive": False,
        }
        source_relations.append(record)
        for ref in sorted({x for values in roles.values() for x in values}):
            if ref in product_link_map:
                product_link_map[ref].append(guid)

    for guid in product_by_guid:
        product_by_guid[guid]["relationship_guids"] = sorted(
            set(product_link_map[guid])
        )

    packet = {
        "schema": PACKET_SCHEMA,
        "public_source": {
            "original_ifc_sha256": original_sha,
            "public_question_sha256": public_question_sha256,
            "ifc_schema": original.schema,
            "native_length_unit_to_metres": _float(scale),
        },
        "manifest": {
            "all_native_source_IfcProduct_count": len(products),
            "serialized_native_IfcProduct_count": len(product_by_guid),
            "source_native_relationship_count": len(source_relations),
            "ifc_product_class_counts": dict(sorted(source_types.items())),
            "geometry_status_counts": dict(sorted(geometry_status.items())),
            "placement_status_counts": dict(sorted(placement_status.items())),
            "source_product_guids_all_present": True,
            "full_native_IFC_semantic_information_equivalent": False,
            "ifc_non_product_entities_and_attributes_exhaustive": False,
            "ifc_property_sets_exhaustive": False,
            "geometry_raw_mesh_and_topology_exhaustive": False,
            "native_IFC_file_writer_or_mutator_access_in_packet": False,
        },
        "products": [product_by_guid[g] for g in sorted(product_by_guid)],
        "relationships": sorted(
            source_relations, key=lambda r: (r["global_id"], r["ifc_class"])
        ),
    }
    if packet["manifest"]["serialized_native_IfcProduct_count"] != len(products):
        raise CommonReadBlocked("Incomplete original native IfcProduct inventory")
    if _sha(source.read_bytes()) != original_sha:
        raise CommonReadBlocked("Original public IFC changed during snapshot")
    return canonical_json(packet)


def bind_public_question_to_frozen_source_packet(
    source_packet_bytes: bytes, public_question_sha256: str
) -> bytes:
    """Rebind task identity without re-reading/repairing original native IFC.

    All other original native-source facts are copied unchanged from the
    previously source-derived, content-hashed canonical original packet.
    The caller must separately verify public question and source IFC hashes.
    """
    if not _HEX_HASH.fullmatch(public_question_sha256):
        raise CommonReadBlocked("Original PUBLIC question SHA-256 required")
    if not isinstance(source_packet_bytes, bytes):
        raise CommonReadBlocked("Only canonical immutable source bytes accepted")
    parsed = json.loads(source_packet_bytes)
    if canonical_json(parsed) != source_packet_bytes or parsed.get("schema") != PACKET_SCHEMA:
        raise CommonReadBlocked("Source-derived packet is not canonical or authentic")
    if not _HEX_HASH.fullmatch(parsed.get("public_source", {}).get("original_ifc_sha256", "")):
        raise CommonReadBlocked("Source-derived original IFC digest missing")
    parsed["public_source"]["public_question_sha256"] = public_question_sha256
    return canonical_json(parsed)

class CommonReadSession:
    """Separate D/I observer, frozen bytes only; NO native IFC file handle."""

    def __init__(self, packet_bytes: bytes, arm: str, *, expected_packet_sha256: str, max_calls: int = DEFAULT_CALL_CAP):
        if arm not in ("D", "I"):
            raise CommonReadBlocked("Read observer arm must be D or I")
        if not isinstance(packet_bytes, bytes):
            raise CommonReadBlocked("Read-only fact packet must be immutable bytes")
        if (not isinstance(expected_packet_sha256, str)
            or not _HEX_HASH.fullmatch(expected_packet_sha256)
            or _sha(packet_bytes) != expected_packet_sha256):
            raise CommonReadBlocked("Source-attested read packet SHA-256 mismatch")
        if not isinstance(max_calls, int) or not (1 <= max_calls <= 25):
            raise CommonReadBlocked("Read-tool call limit must be within 1..25")
        decoded = json.loads(packet_bytes)
        if canonical_json(decoded) != packet_bytes:
            raise CommonReadBlocked("Noncanonical or tampered public source fact packet")
        if decoded.get("schema") != PACKET_SCHEMA:
            raise CommonReadBlocked("Unsupported fact packet schema")
        if (decoded.get("manifest", {}).get("all_native_source_IfcProduct_count")
            != len(decoded.get("products", []))):
            raise CommonReadBlocked("Incomplete native source product inventory in packet")
        ids = [p.get("global_id") for p in decoded["products"]]
        if len(set(ids)) != len(ids):
            raise CommonReadBlocked("Duplicate packet product identity")
        self._data = decoded
        self.arm = arm
        self.packet_sha256 = _sha(packet_bytes)
        self.max_calls = max_calls
        self._calls = []

    @property
    def calls_used(self) -> int:
        return len(self._calls)

    def request(self, operation: str, *, global_id: str | None = None,
                ifc_class: str | None = None) -> bytes:
        if len(self._calls) >= self.max_calls:
            raise CommonReadBlocked("Original public task common-read call cap exhausted")
        if operation not in (
            "source_summary", "list_all_products", "list_by_class",
            "get_product", "related_relations",
        ):
            raise CommonReadBlocked("Unknown or mutating common-read operation")
        if operation in ("get_product", "related_relations"):
            if not isinstance(global_id, str) or not _GLOBAL_ID.fullmatch(global_id):
                raise CommonReadBlocked("Exact original public IfcProduct GlobalId required")
            if ifc_class is not None:
                raise CommonReadBlocked("Unexpected class selector")
        elif operation == "list_by_class":
            if (not isinstance(ifc_class, str)
                or not re.fullmatch(r"Ifc[A-Za-z0-9_]{1,80}", ifc_class)
                or global_id is not None):
                raise CommonReadBlocked("Exact IFC product class selector required")
        elif global_id is not None or ifc_class is not None:
            raise CommonReadBlocked("Unused selector prohibited for this operation")

        data = self._data
        if operation == "source_summary":
            response = {
                "schema": PACKET_SCHEMA,
                "public_source": data["public_source"],
                "manifest": data["manifest"],
            }
        elif operation == "list_all_products":
            response = {
                "products": [
                    {"global_id": x["global_id"], "ifc_class": x["ifc_class"],
                     "name": x["name"]}
                    for x in data["products"]
                ],
            }
        elif operation == "list_by_class":
            response = {
                "products": [
                    {"global_id": x["global_id"], "ifc_class": x["ifc_class"],
                     "name": x["name"]}
                    for x in data["products"] if x["ifc_class"] == ifc_class
                ],
            }
        else:
            items = [p for p in data["products"] if p["global_id"] == global_id]
            if len(items) != 1:
                raise CommonReadBlocked("Original public IfcProduct identity not in source")
            product = items[0]
            if operation == "get_product":
                response = {"product": product}
            else:
                refs = set(product["relationship_guids"])
                response = {"global_id": global_id, "relationships": [
                    r for r in data["relationships"] if r["global_id"] in refs
                ]}
        request_bytes = canonical_json({
            "op": operation, "global_id": global_id, "ifc_class": ifc_class
        })
        response_bytes = canonical_json(response)
        self._calls.append({
            "ordinal": len(self._calls) + 1,
            "request_sha256": _sha(request_bytes),
            "response_sha256": _sha(response_bytes),
        })
        return response_bytes

    def receipt(self) -> dict:
        return {
            "arm": self.arm,
            "packet_sha256": self.packet_sha256,
            "max_calls": self.max_calls,
            "calls_used": len(self._calls),
            "observation_hash_transcript": [dict(x) for x in self._calls],
            "real_LLM_or_provider_trial": False,
            "original_source_native_IFC_access": False,
        }


def compare_equal_observations(d: CommonReadSession, i: CommonReadSession,
                               queries: tuple[dict, ...]) -> dict:
    if d.arm != "D" or i.arm != "I" or d.packet_sha256 != i.packet_sha256:
        raise CommonReadBlocked("Two observers must have exact same original source packet")
    if d.max_calls != i.max_calls:
        raise CommonReadBlocked("Different observation cap")
    if len(queries) > min(d.max_calls - d.calls_used, i.max_calls - i.calls_used):
        raise CommonReadBlocked("The paired task exceeds either read budget")
    for query in queries:
        left = d.request(**query)
        right = i.request(**query)
        if left != right:
            raise CommonReadBlocked("D/I actual observation bytes mismatch")
    receipt_d, receipt_i = d.receipt(), i.receipt()
    if (receipt_d["observation_hash_transcript"]
        != receipt_i["observation_hash_transcript"]):
        raise CommonReadBlocked("D/I observation receipts disagree")
    return {
        "packet_sha256": d.packet_sha256,
        "D_and_I_exact_common_read_response_bytes_identical": True,
        "D_and_I_read_tool_call_caps_identical": True,
        "call_count": len(queries),
        "transcript_sha256": _sha(canonical_json(
            receipt_d["observation_hash_transcript"]
        )),
    }


def strict_llm_trial_launch_gate(*, common_facts_identical: bool,
                                 native_python_original_ifc_mount: bool,
                                 python_unrestricted_filesystem_or_exec: bool,
                                 independent_os_sandbox_attestation: bool,
                                 matched_write_capability_verified: bool,
                                 explicit_paid_budget_approved: bool) -> dict:
    """Prohibit causal experiment launch unless independent controls exist.

    A boolean attestation is a *reported* fact, not an OS security
    enforcement mechanism. This module never launches model or Python code.
    """
    blockers = []
    if not common_facts_identical:
        blockers.append("COMMON_OBSERVATION_RESPONSES_NOT_IDENTICAL")
    if native_python_original_ifc_mount:
        blockers.append("PYTHON_NATIVE_ORIGINAL_IFC_SIDE_CHANNEL_PRESENT")
    if python_unrestricted_filesystem_or_exec:
        blockers.append("UNRESTRICTED_PYTHON_CODE_OR_FILESYSTEM_SIDE_CHANNEL_PRESENT")
    if not independent_os_sandbox_attestation:
        blockers.append("NO_VERIFIED_EXTERNAL_OS_SANDBOX_ATTESTATION")
    if not matched_write_capability_verified:
        blockers.append("NATIVE_WRITE_CAPABILITY_NOT_MATCHED")
    if not explicit_paid_budget_approved:
        blockers.append("NO_EXPLICIT_PAID_LLM_BUDGET_APPROVAL")
    return {
        "status": "BLOCKED" if blockers else "REQUIRES_INDEPENDENT_HOST_ENFORCEMENT",
        "causal_real_LLM_launch_permitted_by_this_module": False,
        "blockers": blockers,
        "note": "This code never runs LLMs or untrusted Python. External sandbox, "
                "model runner and independent security proof are required; "
                "a caller-supplied attestation boolean is NOT proof of confinement.",
    }
