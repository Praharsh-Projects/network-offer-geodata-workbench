import pytest

from network_offer.geo.protocol import GeodataValidationError
from network_offer.geo.shapely_engine import ShapelyGeometryEngine
from network_offer.models import EvaluationRequest, FeatureCollection


def test_shapely_engine_ranks_synthetic_corridors(
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    results = ShapelyGeometryEngine().evaluate(
        network_features,
        demand_features,
        EvaluationRequest(),
        source_crs="EPSG:4326",
        analysis_crs="EPSG:25830",
    )
    assert len(results) == 3
    assert results[0].eligible is True
    assert results[0].demand_sites >= 2
    assert {candidate.segment_id for candidate in results} == {
        "SEG-CENTRAL",
        "SEG-NORTH",
        "SEG-EAST",
    }
    assert all(candidate.length_m > 1_000 for candidate in results)
    assert all(0 <= candidate.coverage_percent <= 100 for candidate in results)


def test_shapely_engine_respects_minimum_sites(
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    results = ShapelyGeometryEngine().evaluate(
        network_features,
        demand_features,
        EvaluationRequest(maximum_distance_m=25, minimum_demand_sites=6),
        source_crs="EPSG:4326",
        analysis_crs="EPSG:25830",
    )
    assert not any(candidate.eligible for candidate in results)


def test_shapely_engine_validates_collection_contract(
    demand_features: FeatureCollection,
) -> None:
    with pytest.raises(GeodataValidationError, match="FeatureCollection"):
        ShapelyGeometryEngine().evaluate(
            {"type": "Feature", "features": []},
            demand_features,
            EvaluationRequest(),
            source_crs="EPSG:4326",
            analysis_crs="EPSG:25830",
        )


@pytest.mark.parametrize(
    "collection, message",
    [
        ({"type": "FeatureCollection", "features": []}, "at least one"),
        (
            {"type": "FeatureCollection", "features": [{"type": "broken"}]},
            "GeoJSON Feature",
        ),
    ],
)
def test_shapely_engine_rejects_bad_features(
    collection: FeatureCollection,
    message: str,
    demand_features: FeatureCollection,
) -> None:
    with pytest.raises(GeodataValidationError, match=message):
        ShapelyGeometryEngine().evaluate(
            collection,
            demand_features,
            EvaluationRequest(),
            source_crs="EPSG:4326",
            analysis_crs="EPSG:25830",
        )


@pytest.mark.parametrize(
    "mutation, message",
    [
        ({"geometry": {"type": "Point", "coordinates": [-3.6, 37.1]}}, "geometry must"),
        ({"properties": None}, "properties must"),
        ({"id": None, "properties": {"name": "Missing ID"}}, "segment_id"),
        (
            {
                "properties": {
                    "segment_id": "SEG-X",
                    "name": 17,
                    "available_capacity_gbps": -1,
                }
            },
            "invalid name or capacity",
        ),
    ],
)
def test_shapely_engine_rejects_invalid_network_contract(
    mutation: dict[str, object],
    message: str,
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    first = dict(network_features["features"][0])
    first.update(mutation)
    broken = {**network_features, "features": [first]}
    with pytest.raises(GeodataValidationError, match=message):
        ShapelyGeometryEngine().evaluate(
            broken,
            demand_features,
            EvaluationRequest(),
            source_crs="EPSG:4326",
            analysis_crs="EPSG:25830",
        )
