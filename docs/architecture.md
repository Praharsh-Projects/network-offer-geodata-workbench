# Architecture

## Design goal

The workbench demonstrates a narrow but complete network-offer workflow: retrieve candidate corridors and demand points through WFS, transform them into a projected CRS, calculate evidence, rank eligible candidates, persist the decision record, and return a WMS review link to an operator.

## Components

| Component | Responsibility | Replaceable boundary |
|---|---|---|
| Nuxt 3 client | Typed criteria form, recommendation view, evidence table | Calls one versioned JSON endpoint |
| Nitro Node server | Serves the production client and exposes `/api/runtime` | Independent of geometry processing |
| FastAPI service | Request validation, concurrent feature retrieval, orchestration, health/OpenAPI | Depends on protocols, not concrete engines |
| WFS client | Safe request construction, GeoJSON response validation, capabilities parsing | Base URL and layer names are configuration |
| Geometry engine | Projection, distance/length analysis, candidate ranking | `GeometryEngine` protocol selects PyQGIS or Shapely |
| WMS builder | Standards-aware map request URL | Provider-neutral base URL/layer configuration |
| Evaluation repository | Audit record storage/history | In-memory development or PostgreSQL JSONB |

## Processing sequence

1. The operator submits a bounding box, maximum site distance, and minimum demand count.
2. FastAPI validates the request and concurrently requests corridor and site feature collections.
3. The active engine validates geometries and projects `EPSG:4326` data into `EPSG:25830` before metric calculations.
4. Each corridor receives length, nearby-demand count, coverage, capacity, and eligibility evidence.
5. A deterministic ordering selects the first eligible candidate and preserves all candidates for review.
6. The request and complete response are stored as JSONB when PostgreSQL is configured.
7. The API returns the evidence and a WMS 1.3.0 preview URL; the client renders both.

## Engine strategy

`NETGEO_GEOMETRY_ENGINE=auto` prefers PyQGIS when available and otherwise uses Shapely. Containers force `qgis`; local development defaults can force `shapely`. Both implement the same protocol and tests exercise the portable path, while CI runs a dedicated PyQGIS contract test against QGIS 3.40 LTR.

## Modernization boundary

The provider-neutral adapters and typed API are designed as reusable replacement components, but this project does not claim migration of any T-Systems front-end assistant, plugin, or internal workflow. Authentication, event orchestration, and organization-specific stages would be separate integrations.
