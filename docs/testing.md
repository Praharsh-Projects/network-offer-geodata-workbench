# Testing strategy

## Local, portable checks

`make test-backend` runs Ruff formatting/linting, strict MyPy, and Pytest with branch coverage. The tests cover request and response models, OGC request/response failures, geometry validation, deterministic planning, API error mapping, fixture routes, and both repository implementations through unit doubles.

`make test-frontend` runs Nuxt type checking and Vitest coverage for typed API calls, view transformations, successful UI rendering, and recoverable failures. `make test-e2e` runs Chromium through the form workflow and verifies the Node/Nitro runtime route.

## Environment-specific CI gates

| Gate | Runtime | Contract exercised |
|---|---|---|
| PyQGIS container | `qgis/qgis:3.40.15-noble` | `QgsGeometry`, CRS validation, `QgsCoordinateTransform`, metric output |
| PostgreSQL integration | PostgreSQL 16 | schema creation, JSONB save, ordered history round trip |
| Frontend container | Node 22 Alpine | frozen pnpm install, Nuxt production build, non-root Nitro runtime image |
| Security audits | `pip-audit`, `pnpm audit` | known dependency vulnerability scan |

## Browser QA

The live Nuxt client was tested against the live FastAPI fixture service at desktop (1440 x 1000) and mobile (390 x 844) viewports. Both runs returned `SEG-EAST`, stayed within page width, and produced no application console errors. The WMS preview link rendered the synthetic planning image.

## Deliberate separation

Local test results do not stand in for unavailable runtimes. PyQGIS, PostgreSQL, and Docker are reported only from their dedicated CI jobs; the portable Shapely suite is reported separately.
