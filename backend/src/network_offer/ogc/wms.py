"""WMS 1.3.0 preview request builder with explicit axis-order handling."""

from urllib.parse import urlencode

from network_offer.ogc.wfs import WfsProtocolError, validate_service_url


def build_get_map_url(
    base_url: str,
    *,
    layer: str,
    bbox: tuple[float, float, float, float],
    crs: str = "EPSG:4326",
    width: int = 960,
    height: int = 540,
) -> str:
    validate_service_url(base_url)
    if not layer or not 64 <= width <= 4_096 or not 64 <= height <= 4_096:
        raise WfsProtocolError("invalid WMS layer or image dimensions")

    min_x, min_y, max_x, max_y = bbox
    if min_x >= max_x or min_y >= max_y:
        raise WfsProtocolError("invalid WMS bounding box")

    # WMS 1.3.0 uses latitude/longitude axis order for EPSG:4326.
    protocol_bbox = (min_y, min_x, max_y, max_x) if crs == "EPSG:4326" else bbox
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": layer,
        "styles": "",
        "crs": crs,
        "bbox": ",".join(str(value) for value in protocol_bbox),
        "width": str(width),
        "height": str(height),
        "format": "image/svg+xml",
        "transparent": "true",
    }
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode(params)}"
