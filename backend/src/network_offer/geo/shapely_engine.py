"""Portable geometry engine used for local development and contract tests."""

from functools import partial
from typing import Any

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

from network_offer.geo.validation import segment_properties, validated_features
from network_offer.models import EvaluationRequest, FeatureCollection, SegmentEvaluation


class ShapelyGeometryEngine:
    """Evaluate the same contract as PyQGIS without requiring a desktop GIS runtime."""

    name = "shapely"

    def evaluate(
        self,
        network_features: FeatureCollection,
        demand_features: FeatureCollection,
        request: EvaluationRequest,
        *,
        source_crs: str,
        analysis_crs: str,
    ) -> list[SegmentEvaluation]:
        segments = validated_features(
            network_features, allowed_geometry_types={"LineString", "MultiLineString"}
        )
        sites = validated_features(demand_features, allowed_geometry_types={"Point"})

        transformer = Transformer.from_crs(source_crs, analysis_crs, always_xy=True)
        project = partial(transformer.transform)
        projected_sites = [transform(project, shape(site["geometry"])) for site in sites]
        total_sites = len(projected_sites)

        evaluations: list[SegmentEvaluation] = []
        for feature in segments:
            segment_id, name, capacity = segment_properties(feature)
            corridor = transform(project, shape(feature["geometry"]))
            demand_count = sum(
                corridor.distance(site) <= request.maximum_distance_m for site in projected_sites
            )
            evaluations.append(
                _evaluation(
                    segment_id=segment_id,
                    name=name,
                    capacity=capacity,
                    length_m=float(corridor.length),
                    demand_count=demand_count,
                    total_sites=total_sites,
                    minimum_sites=request.minimum_demand_sites,
                )
            )

        return sorted(evaluations, key=_rank_key)


def _evaluation(
    *,
    segment_id: str,
    name: str,
    capacity: int,
    length_m: float,
    demand_count: int,
    total_sites: int,
    minimum_sites: int,
) -> SegmentEvaluation:
    return SegmentEvaluation(
        segment_id=segment_id,
        name=name,
        length_m=round(length_m, 2),
        demand_sites=demand_count,
        coverage_percent=round((demand_count / total_sites) * 100, 2),
        available_capacity_gbps=capacity,
        eligible=demand_count >= minimum_sites and capacity > 0,
    )


def _rank_key(candidate: SegmentEvaluation) -> tuple[Any, ...]:
    return (
        not candidate.eligible,
        -candidate.demand_sites,
        -candidate.available_capacity_gbps,
        candidate.length_m,
        candidate.segment_id,
    )
