FROM qgis/qgis:3.40.15-noble AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=offscreen \
    QGIS_PREFIX_PATH=/usr

ENTRYPOINT []

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY backend /app/backend
COPY fixtures /app/fixtures

RUN python3 -m pip install --break-system-packages --no-cache-dir /app/backend

FROM base AS test

RUN python3 -m pip install --break-system-packages --no-cache-dir "/app/backend[dev]"
WORKDIR /app/backend
CMD ["python3", "-m", "pytest", "-m", "qgis"]

FROM base AS runtime

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

ENV NETGEO_ENVIRONMENT=production \
    NETGEO_GEOMETRY_ENGINE=qgis

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

CMD ["python3", "-m", "uvicorn", "network_offer.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
