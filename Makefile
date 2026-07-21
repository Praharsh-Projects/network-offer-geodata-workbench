PYTHON := backend/.venv/bin/python
PIP := backend/.venv/bin/pip
RUFF := backend/.venv/bin/ruff

.PHONY: setup dev-backend dev-frontend test test-backend test-frontend test-e2e audit build compose-up compose-down

setup:
	python3.12 -m venv backend/.venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"
	cd frontend && pnpm install --frozen-lockfile

dev-backend:
	NETGEO_GEOMETRY_ENGINE=shapely $(PYTHON) -m uvicorn network_offer.api.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	cd frontend && pnpm dev --host 127.0.0.1 --port 3000

test: test-backend test-frontend

test-backend:
	$(RUFF) format --check backend
	$(RUFF) check backend
	cd backend && .venv/bin/mypy src tests
	cd backend && .venv/bin/pytest -m "not qgis and not postgres" --cov=network_offer --cov-branch --cov-report=term-missing --cov-fail-under=90

test-frontend:
	cd frontend && pnpm typecheck
	cd frontend && pnpm test:coverage

test-e2e:
	cd frontend && pnpm test:e2e

audit:
	$(PIP) freeze --exclude-editable > backend/.audit-requirements.txt
	$(PYTHON) -m pip_audit --strict --requirement backend/.audit-requirements.txt --progress-spinner off
	cd frontend && pnpm audit --audit-level high

build:
	cd frontend && pnpm build

compose-up:
	docker compose up --build

compose-down:
	docker compose down
