from conftest import StaticFeatureSource
from network_offer.geo.shapely_engine import ShapelyGeometryEngine
from network_offer.models import EvaluationRequest
from network_offer.persistence.repository import MemoryEvaluationRepository
from network_offer.services.planning import PlanningService


def service(source: StaticFeatureSource) -> PlanningService:
    return PlanningService(
        geometry_engine=ShapelyGeometryEngine(),
        feature_source=source,
        repository=MemoryEvaluationRepository(),
        network_layer="planning:network_segments",
        demand_layer="planning:demand_sites",
        wms_base_url="https://geo.example/wms",
        wms_layer="planning:network_segments",
        source_crs="EPSG:4326",
        analysis_crs="EPSG:25830",
    )


async def test_planning_service_orchestrates_both_wfs_layers(
    static_source: StaticFeatureSource,
) -> None:
    planner = service(static_source)
    result = await planner.evaluate(EvaluationRequest())
    assert result.engine == "shapely"
    assert result.recommended_segment_id is not None
    assert result.wms_preview_url.startswith("https://geo.example/wms?")
    assert [call["type_name"] for call in static_source.calls] == [
        "planning:network_segments",
        "planning:demand_sites",
    ]
    history = planner.history()
    assert history[0].evaluation_id == result.evaluation_id
    assert history[0].request.maximum_distance_m == 750


async def test_planning_service_can_return_no_recommendation(
    static_source: StaticFeatureSource,
) -> None:
    result = await service(static_source).evaluate(
        EvaluationRequest(maximum_distance_m=25, minimum_demand_sites=6)
    )
    assert result.recommended_segment_id is None
