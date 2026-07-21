"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from network_offer.api.fixtures import router as fixture_router
from network_offer.config import Settings, get_settings
from network_offer.geo.protocol import GeodataValidationError, GeometryEngine
from network_offer.geo.shapely_engine import ShapelyGeometryEngine
from network_offer.models import (
    EvaluationRecord,
    EvaluationRequest,
    EvaluationResult,
    HealthResponse,
)
from network_offer.ogc.wfs import WfsClient, WfsProtocolError
from network_offer.persistence.repository import (
    EvaluationRepository,
    MemoryEvaluationRepository,
    PostgresEvaluationRepository,
)
from network_offer.services.planning import PlanningService, WfsFeatureSource


def _geometry_engine(settings: Settings) -> GeometryEngine:
    if settings.geometry_engine == "shapely":
        return ShapelyGeometryEngine()
    if settings.geometry_engine == "qgis":
        from network_offer.geo.qgis_engine import QgisGeometryEngine

        return QgisGeometryEngine()
    try:
        from network_offer.geo.qgis_engine import QgisGeometryEngine

        return QgisGeometryEngine()
    except (ImportError, ModuleNotFoundError):
        return ShapelyGeometryEngine()


def _repository(settings: Settings) -> EvaluationRepository:
    if settings.database_url:
        repository = PostgresEvaluationRepository(settings.database_url)
        repository.ensure_schema()
        return repository
    return MemoryEvaluationRepository()


def create_app(
    *,
    settings: Settings | None = None,
    geometry_engine: GeometryEngine | None = None,
    feature_source: WfsFeatureSource | None = None,
    repository: EvaluationRepository | None = None,
) -> FastAPI:
    active_settings = settings or get_settings()
    engine = geometry_engine or _geometry_engine(active_settings)
    source = feature_source or WfsClient(
        str(active_settings.wfs_base_url),
        timeout_seconds=active_settings.request_timeout_seconds,
    )
    active_repository = repository or _repository(active_settings)
    service = PlanningService(
        geometry_engine=engine,
        feature_source=source,
        repository=active_repository,
        network_layer=active_settings.network_layer,
        demand_layer=active_settings.demand_layer,
        wms_base_url=str(active_settings.wms_base_url),
        wms_layer=active_settings.wms_layer,
        source_crs=active_settings.source_crs,
        analysis_crs=active_settings.analysis_crs,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title="Network Offer Geodata Workbench",
        version="0.1.0",
        description=(
            "Synthetic network planning workflow using WFS, WMS, and pluggable geometry engines."
        ),
        lifespan=lifespan,
    )
    app.state.planning_service = service
    app.state.geometry_engine_name = engine.name
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.parsed_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(fixture_router)

    @app.exception_handler(GeodataValidationError)
    async def geodata_error(_request: Request, exc: GeodataValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(WfsProtocolError)
    async def ogc_error(_request: Request, exc: WfsProtocolError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="network-offer-geodata-workbench",
            geometry_engine=engine.name,
        )

    @app.get("/ready", response_model=HealthResponse, tags=["operations"])
    async def ready() -> HealthResponse:
        return await health()

    @app.post(
        "/api/v1/offers/evaluate",
        response_model=EvaluationResult,
        tags=["network offers"],
    )
    async def evaluate(payload: EvaluationRequest) -> EvaluationResult:
        return await service.evaluate(payload)

    @app.get(
        "/api/v1/offers/history",
        response_model=list[EvaluationRecord],
        tags=["network offers"],
    )
    async def history(limit: int = Query(default=20, ge=1, le=100)) -> list[EvaluationRecord]:
        return service.history(limit)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": "network-offer-geodata-workbench", "docs": "/docs"}

    return app


app = create_app()
