from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from network_offer.models import FeatureCollection


@pytest.fixture
def fixture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def network_features(fixture_root: Path) -> FeatureCollection:
    return cast(
        FeatureCollection,
        json.loads((fixture_root / "network_segments.geojson").read_text(encoding="utf-8")),
    )


@pytest.fixture
def demand_features(fixture_root: Path) -> FeatureCollection:
    return cast(
        FeatureCollection,
        json.loads((fixture_root / "demand_sites.geojson").read_text(encoding="utf-8")),
    )


class StaticFeatureSource:
    def __init__(
        self, network_features: FeatureCollection, demand_features: FeatureCollection
    ) -> None:
        self.network_features = network_features
        self.demand_features = demand_features
        self.calls: list[dict[str, Any]] = []

    async def get_features(
        self,
        *,
        type_name: str,
        bbox: tuple[float, float, float, float],
        srs_name: str,
    ) -> FeatureCollection:
        self.calls.append({"type_name": type_name, "bbox": bbox, "srs_name": srs_name})
        if type_name.endswith("network_segments"):
            return self.network_features
        if type_name.endswith("demand_sites"):
            return self.demand_features
        raise AssertionError(f"unexpected type name {type_name}")


@pytest.fixture
def static_source(
    network_features: FeatureCollection, demand_features: FeatureCollection
) -> StaticFeatureSource:
    return StaticFeatureSource(network_features, demand_features)
