"""WFS 2.0 request construction, capabilities parsing, and GeoJSON retrieval."""

from collections.abc import Iterable
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from defusedxml import ElementTree

from network_offer.models import FeatureCollection


class WfsProtocolError(ValueError):
    """Raised for invalid WFS configuration or responses."""


def validate_service_url(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "backend"}:
        return
    raise WfsProtocolError("WFS/WMS endpoint must use HTTPS or an approved local hostname")


def build_get_feature_url(
    base_url: str,
    *,
    type_name: str,
    bbox: tuple[float, float, float, float],
    srs_name: str,
    count: int = 1_000,
) -> str:
    validate_service_url(base_url)
    if not type_name or count < 1 or count > 10_000:
        raise WfsProtocolError("invalid WFS type name or feature count")
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "srsName": srs_name,
        "bbox": ",".join(str(value) for value in bbox) + f",{srs_name}",
        "count": str(count),
        "outputFormat": "application/json",
    }
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode(params)}"


def parse_capabilities(xml_payload: str) -> list[str]:
    try:
        root = ElementTree.fromstring(xml_payload)
    except ElementTree.ParseError as exc:
        raise WfsProtocolError("invalid WFS capabilities XML") from exc

    names: list[str] = []
    for element in root.iter():
        if element.tag.endswith("}Name") and element.text and ":" in element.text:
            names.append(element.text.strip())
    return sorted(set(names))


def validate_feature_collection(payload: Any) -> FeatureCollection:
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise WfsProtocolError("WFS response is not a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        raise WfsProtocolError("WFS FeatureCollection is missing a feature list")
    return payload


class WfsClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        validate_service_url(base_url)
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def get_features(
        self,
        *,
        type_name: str,
        bbox: tuple[float, float, float, float],
        srs_name: str,
    ) -> FeatureCollection:
        url = build_get_feature_url(
            self.base_url, type_name=type_name, bbox=bbox, srs_name=srs_name
        )
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds, transport=self.transport
        ) as client:
            response = await client.get(url, headers={"Accept": "application/geo+json"})
            response.raise_for_status()
            return validate_feature_collection(response.json())


def capabilities_document(feature_types: Iterable[str]) -> str:
    entries = "".join(
        f"<wfs:FeatureType><wfs:Name>{name}</wfs:Name></wfs:FeatureType>" for name in feature_types
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" version="2.0.0">'
        f"<wfs:FeatureTypeList>{entries}</wfs:FeatureTypeList>"
        "</wfs:WFS_Capabilities>"
    )
