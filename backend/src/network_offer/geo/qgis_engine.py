"""PyQGIS implementation of the network corridor evaluation contract."""

import json
import os
from typing import Any

from network_offer.geo.shapely_engine import _evaluation, _rank_key
from network_offer.geo.validation import segment_properties, validated_features
from network_offer.models import EvaluationRequest, FeatureCollection, SegmentEvaluation


class QgisGeometryEngine:
    """Use QgsGeometry and QgsCoordinateTransform for production-style processing."""

    name = "pyqgis"
    _owned_application: Any | None = None

    def __init__(self) -> None:
        self._ensure_runtime()

    @classmethod
    def _ensure_runtime(cls) -> None:
        from qgis.core import QgsApplication

        if QgsApplication.instance() is not None:
            return
        prefix = os.getenv("QGIS_PREFIX_PATH", "/usr")
        QgsApplication.setPrefixPath(prefix, True)
        application = QgsApplication([], False)
        application.initQgis()
        cls._owned_application = application

    def evaluate(
        self,
        network_features: FeatureCollection,
        demand_features: FeatureCollection,
        request: EvaluationRequest,
        *,
        source_crs: str,
        analysis_crs: str,
    ) -> list[SegmentEvaluation]:
        from qgis.core import (
            QgsCoordinateReferenceSystem,
            QgsCoordinateTransform,
            QgsGeometry,
            QgsProject,
        )

        segments = validated_features(
            network_features, allowed_geometry_types={"LineString", "MultiLineString"}
        )
        sites = validated_features(demand_features, allowed_geometry_types={"Point"})

        source = QgsCoordinateReferenceSystem(source_crs)
        target = QgsCoordinateReferenceSystem(analysis_crs)
        if not source.isValid() or not target.isValid():
            raise ValueError("invalid source or analysis CRS")
        coordinate_transform = QgsCoordinateTransform(source, target, QgsProject.instance())

        projected_sites = [
            self._project_geometry(site["geometry"], coordinate_transform, QgsGeometry)
            for site in sites
        ]
        total_sites = len(projected_sites)

        evaluations: list[SegmentEvaluation] = []
        for feature in segments:
            segment_id, name, capacity = segment_properties(feature)
            corridor = self._project_geometry(
                feature["geometry"], coordinate_transform, QgsGeometry
            )
            demand_count = sum(
                corridor.distance(site) <= request.maximum_distance_m for site in projected_sites
            )
            evaluations.append(
                _evaluation(
                    segment_id=segment_id,
                    name=name,
                    capacity=capacity,
                    length_m=float(corridor.length()),
                    demand_count=demand_count,
                    total_sites=total_sites,
                    minimum_sites=request.minimum_demand_sites,
                )
            )
        return sorted(evaluations, key=_rank_key)

    @staticmethod
    def _project_geometry(
        geometry: dict[str, Any], coordinate_transform: Any, geometry_class: Any
    ) -> Any:
        projected = geometry_class.fromJson(json.dumps(geometry).encode("utf-8"))
        if projected.isNull() or projected.isEmpty():
            raise ValueError("PyQGIS could not parse GeoJSON geometry")
        result = projected.transform(coordinate_transform)
        if result != 0:
            raise ValueError(f"PyQGIS coordinate transform failed with code {result}")
        return projected
