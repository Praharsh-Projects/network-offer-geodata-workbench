import httpx
import pytest
from fastapi import FastAPI

from conftest import StaticFeatureSource
from network_offer.api.main import _geometry_engine, _repository, create_app
from network_offer.config import Settings
from network_offer.geo.shapely_engine import ShapelyGeometryEngine
from network_offer.models import FeatureCollection
from network_offer.ogc.wfs import WfsProtocolError
from network_offer.persistence.repository import MemoryEvaluationRepository


def app_for(source: StaticFeatureSource) -> FastAPI:
    return create_app(
        settings=Settings(geometry_engine="shapely"),
        geometry_engine=ShapelyGeometryEngine(),
        feature_source=source,
        repository=MemoryEvaluationRepository(),
    )


async def test_health_and_evaluation_api(
    static_source: StaticFeatureSource,
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(static_source)),
        base_url="http://test",
    ) as client:
        health = await client.get("/health")
        assert health.json() == {
            "status": "ok",
            "service": "network-offer-geodata-workbench",
            "geometry_engine": "shapely",
        }
        assert (await client.get("/ready")).json() == health.json()
        assert (await client.get("/")).json()["docs"] == "/docs"
        response = await client.post(
            "/api/v1/offers/evaluate",
            json={"maximum_distance_m": 750, "minimum_demand_sites": 2},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["recommended_segment_id"]
        assert len(payload["candidates"]) == 3
        history = await client.get("/api/v1/offers/history?limit=1")
        assert history.status_code == 200
        assert history.json()[0]["evaluation_id"] == payload["evaluation_id"]


async def test_api_rejects_invalid_request(static_source: StaticFeatureSource) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(static_source)),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/offers/evaluate",
            json={"maximum_distance_m": 0},
        )
    assert response.status_code == 422


async def test_fixture_wfs_and_wms_routes(
    static_source: StaticFeatureSource,
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(static_source)),
        base_url="http://test",
    ) as client:
        capabilities = await client.get("/fixtures/wfs?request=GetCapabilities")
        assert capabilities.status_code == 200
        assert "planning:network_segments" in capabilities.text
        features = await client.get(
            "/fixtures/wfs?request=GetFeature&typeNames=planning:network_segments"
        )
        assert features.status_code == 200
        assert len(features.json()["features"]) == 3
        map_response = await client.get("/fixtures/wms?request=GetMap")
        assert map_response.status_code == 200
        assert map_response.headers["content-type"].startswith("image/svg+xml")
        wms_capabilities = await client.get("/fixtures/wms?request=GetCapabilities")
        assert "planning:network_segments" in wms_capabilities.text
        assert (await client.get("/fixtures/wfs?request=DescribeFeatureType")).status_code == 400
        assert (await client.get("/fixtures/wms?request=GetFeatureInfo")).status_code == 400
        unknown = await client.get("/fixtures/wfs?request=GetFeature&typeNames=planning:unknown")
        assert unknown.status_code == 404


async def test_api_returns_geodata_validation_error(
    network_features: FeatureCollection,
    demand_features: FeatureCollection,
) -> None:
    broken = {"type": "FeatureCollection", "features": []}
    source = StaticFeatureSource(broken, demand_features)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(source)),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/offers/evaluate", json={})
    assert response.status_code == 422
    assert "at least one feature" in response.json()["detail"]


class FailingFeatureSource:
    async def get_features(
        self,
        *,
        type_name: str,
        bbox: tuple[float, float, float, float],
        srs_name: str,
    ) -> FeatureCollection:
        raise WfsProtocolError(f"failed to load {type_name} in {srs_name} for {bbox}")


async def test_api_maps_wfs_errors_to_bad_gateway() -> None:
    app = create_app(
        settings=Settings(geometry_engine="shapely"),
        geometry_engine=ShapelyGeometryEngine(),
        feature_source=FailingFeatureSource(),
        repository=MemoryEvaluationRepository(),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/offers/evaluate", json={})
    assert response.status_code == 502
    assert "failed to load" in response.json()["detail"]


def test_runtime_factories_use_portable_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _geometry_engine(Settings(geometry_engine="shapely")).name == "shapely"
    assert isinstance(_repository(Settings(database_url=None)), MemoryEvaluationRepository)

    class FakePostgresRepository(MemoryEvaluationRepository):
        initialized = False

        def __init__(self, database_url: str) -> None:
            super().__init__()
            assert database_url.startswith("postgresql://")

        def ensure_schema(self) -> None:
            self.initialized = True

    monkeypatch.setattr(
        "network_offer.api.main.PostgresEvaluationRepository", FakePostgresRepository
    )
    repository = _repository(
        Settings(database_url="postgresql://postgres:postgres@localhost:5432/netgeo")
    )
    assert isinstance(repository, FakePostgresRepository)
    assert repository.initialized
