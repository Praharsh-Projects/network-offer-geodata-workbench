"""GeoJSON contract validation shared by geometry engines."""

from typing import Any

from network_offer.geo.protocol import GeodataValidationError
from network_offer.models import FeatureCollection


def validated_features(
    collection: FeatureCollection,
    *,
    allowed_geometry_types: set[str],
) -> list[dict[str, Any]]:
    if collection.get("type") != "FeatureCollection":
        raise GeodataValidationError("expected a GeoJSON FeatureCollection")

    features = collection.get("features")
    if not isinstance(features, list) or not features:
        raise GeodataValidationError("feature collection must contain at least one feature")

    validated: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise GeodataValidationError("every item must be a GeoJSON Feature")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") not in allowed_geometry_types:
            expected = ", ".join(sorted(allowed_geometry_types))
            raise GeodataValidationError(f"geometry must be one of: {expected}")
        if not isinstance(feature.get("properties"), dict):
            raise GeodataValidationError("feature properties must be an object")
        validated.append(feature)
    return validated


def segment_properties(feature: dict[str, Any]) -> tuple[str, str, int]:
    properties = feature["properties"]
    segment_id = properties.get("segment_id") or feature.get("id")
    if not isinstance(segment_id, str) or not segment_id.strip():
        raise GeodataValidationError("network feature requires a segment_id")
    name = properties.get("name", segment_id)
    capacity = properties.get("available_capacity_gbps", 0)
    if not isinstance(name, str) or not isinstance(capacity, int) or capacity < 0:
        raise GeodataValidationError("network feature has invalid name or capacity")
    return segment_id, name, capacity
