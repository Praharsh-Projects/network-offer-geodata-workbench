import pytest
from pydantic import ValidationError

from network_offer.config import Settings
from network_offer.models import EvaluationRequest


def test_evaluation_request_defaults_are_valid() -> None:
    request = EvaluationRequest()
    assert request.maximum_distance_m == 750
    assert request.minimum_demand_sites == 2


@pytest.mark.parametrize(
    "bbox",
    [
        (-3.0, 37.0, -4.0, 38.0),
        (-3.0, 38.0, -2.0, 37.0),
        (-181.0, 37.0, -2.0, 38.0),
        (-3.0, -91.0, -2.0, 38.0),
    ],
)
def test_evaluation_request_rejects_invalid_bbox(
    bbox: tuple[float, float, float, float],
) -> None:
    with pytest.raises(ValidationError):
        EvaluationRequest(bbox=bbox)


def test_settings_parse_cors_origins() -> None:
    settings = Settings(cors_origins="http://localhost:3000, https://review.example ")
    assert settings.parsed_cors_origins == [
        "http://localhost:3000",
        "https://review.example",
    ]
