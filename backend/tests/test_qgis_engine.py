import pytest

from network_offer.models import EvaluationRequest, FeatureCollection

pytestmark = pytest.mark.qgis


def test_pyqgis_engine_matches_portable_contract(
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    pytest.importorskip("qgis.core")
    from network_offer.geo.qgis_engine import QgisGeometryEngine

    results = QgisGeometryEngine().evaluate(
        network_features,
        demand_features,
        EvaluationRequest(),
        source_crs="EPSG:4326",
        analysis_crs="EPSG:25830",
    )
    assert len(results) == 3
    assert results[0].eligible
    assert {candidate.segment_id for candidate in results} == {
        "SEG-CENTRAL",
        "SEG-NORTH",
        "SEG-EAST",
    }
    assert all(candidate.length_m > 1_000 for candidate in results)


def test_pyqgis_engine_rejects_invalid_crs(
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    pytest.importorskip("qgis.core")
    from network_offer.geo.qgis_engine import QgisGeometryEngine

    with pytest.raises(ValueError, match="invalid source or analysis CRS"):
        QgisGeometryEngine().evaluate(
            network_features,
            demand_features,
            EvaluationRequest(),
            source_crs="EPSG:4326",
            analysis_crs="EPSG:0",
        )
