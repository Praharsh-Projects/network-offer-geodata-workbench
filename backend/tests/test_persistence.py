from __future__ import annotations

import os
from typing import Any

import pytest

from network_offer.models import EvaluationRequest, EvaluationResult
from network_offer.persistence.repository import (
    MemoryEvaluationRepository,
    PostgresEvaluationRepository,
)


def empty_result(evaluation_id: str = "result-id") -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=evaluation_id,
        engine="shapely",
        source_crs="EPSG:4326",
        analysis_crs="EPSG:25830",
        recommended_segment_id=None,
        wms_preview_url="https://geo.example/wms?request=GetMap",
        candidates=[],
    )


def test_memory_repository_returns_newest_first() -> None:
    repository = MemoryEvaluationRepository()
    repository.save(EvaluationRequest(), empty_result("first"))
    repository.save(EvaluationRequest(), empty_result("second"))
    assert [record.evaluation_id for record in repository.list_recent()] == ["second", "first"]
    assert [record.evaluation_id for record in repository.list_recent(1)] == ["second"]


def test_postgres_repository_executes_schema_save_and_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[tuple[str, object | None]] = []
    request = EvaluationRequest()
    result = empty_result("database-id")

    class FakeCursor:
        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def execute(self, query: str, params: object | None = None) -> None:
            executed.append((query, params))

        def fetchall(self) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
            return [
                (
                    "database-id",
                    request.model_dump(mode="json"),
                    result.model_dump(mode="json"),
                )
            ]

    class FakeConnection:
        def __enter__(self) -> FakeConnection:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def cursor(self) -> FakeCursor:
            return FakeCursor()

    monkeypatch.setattr(
        "network_offer.persistence.repository.psycopg.connect",
        lambda _database_url: FakeConnection(),
    )
    repository = PostgresEvaluationRepository("postgresql://example")
    repository.ensure_schema()
    assert repository.save(request, result) == "database-id"
    records = repository.list_recent(5)
    assert records[0].evaluation_id == "database-id"
    assert len(executed) == 3


@pytest.mark.postgres
def test_postgres_repository_round_trip() -> None:
    database_url = os.getenv("NETGEO_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("NETGEO_TEST_DATABASE_URL is not configured")
    repository = PostgresEvaluationRepository(database_url)
    repository.ensure_schema()
    evaluation_id = repository.save(EvaluationRequest(), empty_result("postgres-round-trip"))
    records = repository.list_recent(10)
    match = next(record for record in records if record.evaluation_id == evaluation_id)
    assert match.result.engine == "shapely"
    assert match.request.minimum_demand_sites == 2
