"""Provider-neutral geometry processing contract."""

from typing import Protocol

from network_offer.models import EvaluationRequest, FeatureCollection, SegmentEvaluation


class GeodataValidationError(ValueError):
    """Raised when a feature collection violates the workflow contract."""


class GeometryEngine(Protocol):
    name: str

    def evaluate(
        self,
        network_features: FeatureCollection,
        demand_features: FeatureCollection,
        request: EvaluationRequest,
        *,
        source_crs: str,
        analysis_crs: str,
    ) -> list[SegmentEvaluation]:
        """Return ranked segment evaluations for one planning request."""
