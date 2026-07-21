from urllib.parse import parse_qs, urlparse

import pytest

from network_offer.ogc.wfs import WfsProtocolError
from network_offer.ogc.wms import build_get_map_url


def test_wms_130_reorders_epsg_4326_axes() -> None:
    url = build_get_map_url(
        "https://geo.example/wms",
        layer="planning:network_segments",
        bbox=(-3.66, 37.14, -3.52, 37.23),
    )
    query = parse_qs(urlparse(url).query)
    assert query["version"] == ["1.3.0"]
    assert query["crs"] == ["EPSG:4326"]
    assert query["bbox"] == ["37.14,-3.66,37.23,-3.52"]
    assert query["format"] == ["image/svg+xml"]


def test_wms_preserves_xy_axes_for_projected_crs() -> None:
    url = build_get_map_url(
        "https://geo.example/wms?tenant=lab",
        layer="planning:network_segments",
        bbox=(440000, 4110000, 450000, 4120000),
        crs="EPSG:25830",
        width=640,
        height=480,
    )
    assert "tenant=lab&service=WMS" in url
    assert parse_qs(urlparse(url).query)["bbox"] == ["440000,4110000,450000,4120000"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"layer": "", "bbox": (-3.0, 37.0, -2.0, 38.0)},
        {"layer": "roads", "bbox": (-2.0, 37.0, -3.0, 38.0)},
        {"layer": "roads", "bbox": (-3.0, 37.0, -2.0, 38.0), "width": 32},
    ],
)
def test_wms_rejects_invalid_parameters(kwargs: dict[str, object]) -> None:
    with pytest.raises(WfsProtocolError):
        build_get_map_url("https://geo.example/wms", **kwargs)  # type: ignore[arg-type]
