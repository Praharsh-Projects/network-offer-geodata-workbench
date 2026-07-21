# OGC contracts

## WFS 2.0.0

`network_offer.ogc.wfs` builds `GetFeature` requests with:

- `typeNames`, `srsName`, bounded `count`, and GeoJSON output parameters;
- an explicit bounding box including its CRS;
- HTTPS enforcement for remote hosts and a small allowlist for local/container fixtures;
- response validation requiring a GeoJSON `FeatureCollection` and feature array;
- XML capabilities parsing with `defusedxml`.

The included fixture exposes only `GetCapabilities` and `GetFeature` for `planning:network_segments` and `planning:demand_sites`. It is a deterministic test provider, not a general WFS server.

## WMS 1.3.0

`network_offer.ogc.wms` validates image dimensions and bounding boxes before building `GetMap` URLs. WMS 1.3.0 uses latitude/longitude axis order for `EPSG:4326`, so the input `(min_x, min_y, max_x, max_y)` becomes `(min_y, min_x, max_y, max_x)` in the protocol request.

The fixture returns a synthetic SVG preview. Browser QA verifies that the generated link renders, while unit tests assert the exact query contract and reject invalid parameters.

## Geometry validation

- Corridors must be `LineString` or `MultiLineString` features.
- Demand locations must be `Point` features.
- Empty collections, invalid coordinates, missing identifiers, and invalid capacities fail explicitly.
- Metric calculations occur only after projection from `EPSG:4326` to `EPSG:25830`.
