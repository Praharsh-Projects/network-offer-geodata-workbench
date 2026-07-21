"""Memory and PostgreSQL persistence for evaluation audit records."""

from collections.abc import Sequence
from typing import Protocol
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from network_offer.models import EvaluationRecord, EvaluationRequest, EvaluationResult


class EvaluationRepository(Protocol):
    def save(self, request: EvaluationRequest, result: EvaluationResult) -> str:
        """Persist a completed evaluation and return its identifier."""

    def list_recent(self, limit: int = 20) -> Sequence[EvaluationRecord]:
        """Return recent evaluation records."""


class MemoryEvaluationRepository:
    def __init__(self) -> None:
        self._records: list[EvaluationRecord] = []

    def save(self, request: EvaluationRequest, result: EvaluationResult) -> str:
        evaluation_id = result.evaluation_id or str(uuid4())
        stored_result = result.model_copy(update={"evaluation_id": evaluation_id})
        self._records.append(
            EvaluationRecord(
                evaluation_id=evaluation_id,
                request=request,
                result=stored_result,
            )
        )
        return evaluation_id

    def list_recent(self, limit: int = 20) -> Sequence[EvaluationRecord]:
        return list(reversed(self._records[-limit:]))


class PostgresEvaluationRepository:
    """Small JSONB-backed audit repository for reproducible workflow results."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def ensure_schema(self) -> None:
        with (
            psycopg.connect(self.database_url) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offer_evaluations (
                    evaluation_id UUID PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    request_payload JSONB NOT NULL,
                    result_payload JSONB NOT NULL
                )
                """
            )

    def save(self, request: EvaluationRequest, result: EvaluationResult) -> str:
        evaluation_id = result.evaluation_id or str(uuid4())
        result_payload = result.model_copy(update={"evaluation_id": evaluation_id}).model_dump(
            mode="json"
        )
        with (
            psycopg.connect(self.database_url) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                INSERT INTO offer_evaluations (
                    evaluation_id, request_payload, result_payload
                ) VALUES (%s, %s, %s)
                """,
                (
                    evaluation_id,
                    Jsonb(request.model_dump(mode="json")),
                    Jsonb(result_payload),
                ),
            )
        return evaluation_id

    def list_recent(self, limit: int = 20) -> Sequence[EvaluationRecord]:
        with (
            psycopg.connect(self.database_url) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT evaluation_id::text, request_payload, result_payload
                FROM offer_evaluations
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            EvaluationRecord(
                evaluation_id=row[0],
                request=EvaluationRequest.model_validate(row[1]),
                result=EvaluationResult.model_validate(row[2]),
            )
            for row in rows
        ]
