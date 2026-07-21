"""Self-contained WFS/WMS fixtures for local and browser verification."""

import json
from pathlib import Path
from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from network_offer.ogc.wfs import capabilities_document

router = APIRouter(prefix="/fixtures", tags=["local OGC fixtures"])


def _fixture_directory() -> Path:
    candidates = [
        Path.cwd() / "fixtures",
        Path(__file__).resolve().parents[4] / "fixtures",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise RuntimeError("fixture directory was not found")


def _load_collection(filename: str) -> dict[str, object]:
    fixture_path = _fixture_directory() / filename
    return cast(dict[str, object], json.loads(fixture_path.read_text(encoding="utf-8")))


@router.get("/wfs")
def wfs_fixture(request: Request) -> Response:
    query = {key.lower(): value for key, value in request.query_params.items()}
    operation = query.get("request", "GetCapabilities").lower()
    if operation == "getcapabilities":
        return Response(
            capabilities_document(["planning:network_segments", "planning:demand_sites"]),
            media_type="application/xml",
        )
    if operation != "getfeature":
        raise HTTPException(status_code=400, detail="unsupported WFS operation")

    type_name = query.get("typenames", "")
    filenames = {
        "planning:network_segments": "network_segments.geojson",
        "planning:demand_sites": "demand_sites.geojson",
    }
    filename = filenames.get(type_name)
    if filename is None:
        raise HTTPException(status_code=404, detail="unknown fixture feature type")
    return JSONResponse(_load_collection(filename), media_type="application/geo+json")


@router.get("/wms")
def wms_fixture(request: Request) -> Response:
    query = {key.lower(): value for key, value in request.query_params.items()}
    operation = query.get("request", "GetCapabilities").lower()
    if operation == "getcapabilities":
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<WMS_Capabilities version="1.3.0">'
            "<Capability><Layer><Name>planning:network_segments</Name></Layer></Capability>"
            "</WMS_Capabilities>"
        )
        return Response(xml, media_type="application/xml")
    if operation != "getmap":
        raise HTTPException(status_code=400, detail="unsupported WMS operation")

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" '
        'viewBox="0 0 960 540">'
        '<rect width="960" height="540" fill="#e8f0ee"/>'
        '<path d="M100 410 C260 300 420 340 590 190 S820 120 880 80" '
        'fill="none" stroke="#0f766e" stroke-width="16"/>'
        '<path d="M80 120 C260 180 390 130 520 250 S760 390 900 330" '
        'fill="none" stroke="#2563eb" stroke-width="12"/>'
        '<g fill="#f97316" stroke="#ffffff" stroke-width="5">'
        '<circle cx="240" cy="310" r="13"/>'
        '<circle cx="470" cy="245" r="13"/>'
        '<circle cx="720" cy="145" r="13"/>'
        "</g>"
        '<text x="38" y="52" font-family="Arial, sans-serif" font-size="26" '
        'fill="#16324f">Synthetic WMS planning preview</text>'
        "</svg>"
    )
    return Response(svg, media_type="image/svg+xml")
