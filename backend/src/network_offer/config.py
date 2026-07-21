"""Runtime configuration for the API and geodata adapters."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings with safe local fixture defaults."""

    model_config = SettingsConfigDict(
        env_prefix="NETGEO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    geometry_engine: Literal["auto", "shapely", "qgis"] = "auto"
    wfs_base_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000/fixtures/wfs")
    wms_base_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000/fixtures/wms")
    network_layer: str = Field(default="planning:network_segments", min_length=3)
    demand_layer: str = Field(default="planning:demand_sites", min_length=3)
    wms_layer: str = Field(default="planning:network_segments", min_length=3)
    source_crs: str = "EPSG:4326"
    analysis_crs: str = "EPSG:25830"
    database_url: str | None = None
    request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
