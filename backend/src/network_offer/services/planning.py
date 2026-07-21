"""Orchestrate OGC feature retrieval, geometry processing, and persistence."""

import asyncio
from typing import Protocol
from uuid import uuid4

from network_offer.geo.protocol import GeometryEngine
from network_offer.models import (
    EvaluationRecord,
    EvaluationRequest,
    EvaluationResult,
    FeatureCollection,
)
from network_offer.ogc.wms import build_get_map_url
from network_offer.persistence.repository import EvaluationRepository


class WfsFeatureSource(Protocol):
    async def get_features(
        self,
        *,
        type_name: str,
        bbox: tuple[float, float, float, float],
        srs_name: str,
    ) -> FeatureCollection:
        """Fetch one feature collection through a WFS-compatible boundary."""


class PlanningService:
    def __init__(
        self,
        *,
        geometry_engine: GeometryEngine,
        feature_source: WfsFeatureSource,
        repository: EvaluationRepository,
        network_layer: str,
        demand_layer: str,
        wms_base_url: str,
        wms_layer: str,
        source_crs: str,
        analysis_crs: str,
    ) -> None:
        self.geometry_engine = geometry_engine
        self.feature_source = feature_source
        self.repository = repository
        self.network_layer = network_layer
        self.demand_layer = demand_layer
        self.wms_base_url = wms_base_url
        self.wms_layer = wms_layer
        self.source_crs = source_crs
        self.analysis_crs = analysis_crs

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        network_features, demand_features = await asyncio.gather(
            self.feature_source.get_features(
                type_name=self.network_layer,
                bbox=request.bbox,
                srs_name=self.source_crs,
            ),
            self.feature_source.get_features(
                type_name=self.demand_layer,
                bbox=request.bbox,
                srs_name=self.source_crs,
            ),
        )
        candidates = self.geometry_engine.evaluate(
            network_features,
            demand_features,
            request,
            source_crs=self.source_crs,
            analysis_crs=self.analysis_crs,
        )
        recommended = next(
            (candidate.segment_id for candidate in candidates if candidate.eligible), None
        )
        evaluation_id = str(uuid4())
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            engine=self.geometry_engine.name,
            source_crs=self.source_crs,
            analysis_crs=self.analysis_crs,
            recommended_segment_id=recommended,
            wms_preview_url=build_get_map_url(
                self.wms_base_url,
                layer=self.wms_layer,
                bbox=request.bbox,
                crs=self.source_crs,
            ),
            candidates=candidates,
        )
        stored_id = self.repository.save(request, result)
        return result.model_copy(update={"evaluation_id": stored_id})

    def history(self, limit: int = 20) -> list[EvaluationRecord]:
        return list(self.repository.list_recent(limit))
