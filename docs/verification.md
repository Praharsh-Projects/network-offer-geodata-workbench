# Verification record

Verification date: 2026-07-21

## Local evidence

| Check | Result |
|---|---|
| Ruff format and lint | Passed |
| Strict MyPy | Passed across 26 source/test files |
| Pytest portable suite | 47 passed, 3 environment-specific tests deselected |
| Python branch coverage | 98.64% |
| Nuxt typecheck | Passed |
| Vitest | 5 passed |
| Frontend coverage | 100% statements/lines/functions; 82.53% branches |
| Nuxt production build | Passed; 1.96 MB total, 473 kB gzip |
| Playwright Chromium | 1 workflow passed |
| Live API/UI/WMS exercise | Passed; `SEG-EAST` recommended from 3 candidates |
| Desktop/mobile browser QA | Passed at 1440 x 1000 and 390 x 844 |

## CI evidence

Public pull-request validation passed all independent backend, PostgreSQL, PyQGIS container, and frontend/Node jobs:

- Run: [29818139429](https://github.com/Praharsh-Projects/network-offer-geodata-workbench/actions/runs/29818139429)
- Validated commit: `1afbae334eca1b8cce8e24e48bb3fe350e3fed86`
- Result: 4 of 4 jobs successful, including QGIS 3.40 container and PostgreSQL 16 integration contracts

After merge, the repository CI badge and GitHub Actions history provide the current `main` result without making this record self-referential.

## Evidence boundaries

- QGIS and Docker are unavailable in the local environment, so their authoritative result is CI-only.
- Fixture records are synthetic and contain no customer data.
- PostgreSQL is exercised as JSONB storage; PostGIS is not installed or claimed.
