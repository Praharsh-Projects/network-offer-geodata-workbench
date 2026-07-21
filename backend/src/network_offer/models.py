"""Typed API and domain contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

FeatureCollection = dict[str, Any]


class EvaluationRequest(BaseModel):
    """Parameters for evaluating synthetic network corridors."""

    model_config = ConfigDict(extra="forbid")

    bbox: tuple[float, float, float, float] = (-3.66, 37.14, -3.52, 37.23)
    maximum_distance_m: float = Field(default=750, ge=25, le=5_000)
    minimum_demand_sites: int = Field(default=2, ge=1, le=100)

    @field_validator("bbox")
    @classmethod
    def validate_bbox(
        cls, value: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        min_x, min_y, max_x, max_y = value
        if min_x >= max_x or min_y >= max_y:
            raise ValueError("bbox must use min_x, min_y, max_x, max_y ordering")
        if not (-180 <= min_x <= 180 and -180 <= max_x <= 180):
            raise ValueError("bbox longitude must be between -180 and 180")
        if not (-90 <= min_y <= 90 and -90 <= max_y <= 90):
            raise ValueError("bbox latitude must be between -90 and 90")
        return value


class SegmentEvaluation(BaseModel):
    segment_id: str
    name: str
    length_m: float = Field(ge=0)
    demand_sites: int = Field(ge=0)
    coverage_percent: float = Field(ge=0, le=100)
    available_capacity_gbps: int = Field(ge=0)
    eligible: bool


class EvaluationResult(BaseModel):
    evaluation_id: str
    engine: str
    source_crs: str
    analysis_crs: str
    recommended_segment_id: str | None
    wms_preview_url: str
    candidates: list[SegmentEvaluation]


class EvaluationRecord(BaseModel):
    evaluation_id: str
    request: EvaluationRequest
    result: EvaluationResult


class HealthResponse(BaseModel):
    status: str
    service: str
    geometry_engine: str
