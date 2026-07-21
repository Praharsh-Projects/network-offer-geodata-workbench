# Deployment and operations

## Configuration

The API reads `NETGEO_` environment variables. Important settings are:

- `GEOMETRY_ENGINE`: `auto`, `shapely`, or `qgis`;
- `WFS_BASE_URL`, `WMS_BASE_URL`, and layer names;
- `SOURCE_CRS` and `ANALYSIS_CRS`;
- `DATABASE_URL` for PostgreSQL audit records;
- `CORS_ORIGINS` and request timeout.

The client reads `NUXT_PUBLIC_API_BASE`. See `.env.example` for safe local defaults.

## Container topology

`compose.yaml` starts PostgreSQL 16, a QGIS 3.40 LTR API image, and a Node 22/Nuxt runtime. Health conditions order startup. The API and client run as non-root users in their final images; PostgreSQL data uses a named volume.

## Operational endpoints

- `/health`: process health and selected geometry engine;
- `/ready`: readiness contract for orchestrators;
- `/docs`: OpenAPI reference;
- `/api/v1/offers/history`: recent persisted evaluation records.

## Production boundaries

Before a real deployment, add organization-managed identity, encrypted secrets, externally hosted OGC providers, structured telemetry, backup/retention policy, rate controls, high-volume performance tests, and deployment-specific network policies. The bundled credentials and fixtures are local-only.
