from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from network_offer.ogc.wfs import (
    WfsClient,
    WfsProtocolError,
    build_get_feature_url,
    capabilities_document,
    parse_capabilities,
    validate_feature_collection,
    validate_service_url,
)


def test_get_feature_url_uses_wfs_2_contract() -> None:
    url = build_get_feature_url(
        "https://geo.example/wfs",
        type_name="planning:network_segments",
        bbox=(-3.7, 37.1, -3.5, 37.3),
        srs_name="EPSG:4326",
        count=250,
    )
    query = parse_qs(urlparse(url).query)
    assert query == {
        "service": ["WFS"],
        "version": ["2.0.0"],
        "request": ["GetFeature"],
        "typeNames": ["planning:network_segments"],
        "srsName": ["EPSG:4326"],
        "bbox": ["-3.7,37.1,-3.5,37.3,EPSG:4326"],
        "count": ["250"],
        "outputFormat": ["application/json"],
    }


def test_get_feature_url_preserves_existing_query() -> None:
    url = build_get_feature_url(
        "https://geo.example/wfs?tenant=lab",
        type_name="planning:demand_sites",
        bbox=(-3.7, 37.1, -3.5, 37.3),
        srs_name="EPSG:4326",
    )
    assert "tenant=lab&service=WFS" in url


@pytest.mark.parametrize("type_name, count", [("", 10), ("roads", 0), ("roads", 10_001)])
def test_get_feature_url_rejects_invalid_query(type_name: str, count: int) -> None:
    with pytest.raises(WfsProtocolError):
        build_get_feature_url(
            "https://geo.example/wfs",
            type_name=type_name,
            bbox=(-3.7, 37.1, -3.5, 37.3),
            srs_name="EPSG:4326",
            count=count,
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://untrusted.example/wfs",
        "file:///tmp/features.geojson",
        "ftp://geo.example/features",
    ],
)
def test_service_url_rejects_insecure_external_endpoints(url: str) -> None:
    with pytest.raises(WfsProtocolError):
        validate_service_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://geo.example/wfs",
        "http://localhost:8000/fixtures/wfs",
        "http://127.0.0.1:8000/fixtures/wfs",
        "http://backend:8000/fixtures/wfs",
    ],
)
def test_service_url_accepts_https_and_local_runtime_hosts(url: str) -> None:
    validate_service_url(url)


def test_capabilities_round_trip() -> None:
    xml = capabilities_document(["planning:demand_sites", "planning:network_segments"])
    assert parse_capabilities(xml) == [
        "planning:demand_sites",
        "planning:network_segments",
    ]


def test_capabilities_reject_invalid_xml() -> None:
    with pytest.raises(WfsProtocolError, match="capabilities XML"):
        parse_capabilities("<broken>")


def test_feature_collection_validation() -> None:
    payload = {"type": "FeatureCollection", "features": []}
    assert validate_feature_collection(payload) is payload
    with pytest.raises(WfsProtocolError):
        validate_feature_collection({"type": "Feature"})
    with pytest.raises(WfsProtocolError, match="feature list"):
        validate_feature_collection({"type": "FeatureCollection", "features": None})


@pytest.mark.asyncio
async def test_wfs_client_fetches_geojson() -> None:
    observed: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(200, json={"type": "FeatureCollection", "features": []})

    client = WfsClient(
        "https://geo.example/wfs",
        transport=httpx.MockTransport(handler),
    )
    result = await client.get_features(
        type_name="planning:network_segments",
        bbox=(-3.7, 37.1, -3.5, 37.3),
        srs_name="EPSG:4326",
    )
    assert result["features"] == []
    assert observed[0].headers["accept"] == "application/geo+json"


@pytest.mark.asyncio
async def test_wfs_client_propagates_http_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(503))
    client = WfsClient("https://geo.example/wfs", transport=transport)
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_features(
            type_name="planning:network_segments",
            bbox=(-3.7, 37.1, -3.5, 37.3),
            srs_name="EPSG:4326",
        )
