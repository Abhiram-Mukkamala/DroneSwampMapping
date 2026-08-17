# DroneSwampMapping - AI Terrain Mode (Phase 2 Findings)

## 1. Overview & Objectives

In Phase 2, we formalized the data ingestion layer into two modular, production-grade fetchers and validated them against the identical test bounding box in Lower Manhattan (World Trade Center / Financial District, NYC):
- **Bounding Box**: $(40.7090^\circ\text{N}, -74.0145^\circ\text{W})$ to $(40.7140^\circ\text{N}, -74.0075^\circ\text{W})$
- **Physical Span**: $591.16\text{m}$ (Width) $\times$ $555.25\text{m}$ (Height)

---

## 2. Building Footprints Fetcher (`fetch_buildings.py`)

### Module Status & Features
- **Implementation**: [`geo_terrain/fetch_buildings.py`](file:///c:/Projects/droneswarm/geo_terrain/fetch_buildings.py)
- **Interface**: `fetch_buildings(bbox, cache_dir, force_refresh, timeout) -> dict`
- **Caching Mechanism**: Query bounding boxes are canonicalized and MD5-hashed. Raw responses are stored in `geo_terrain/cache/buildings_<hash>.json`.

### Verification Results
1. **Live Query**: Successfully queried primary Overpass endpoint (`overpass-api.de/api/interpreter`), retrieving 196 building entities in $\sim 1.1\text{s}$. Saved to `cache/buildings_d0c0770aa60e23f9e3d5c1314f9a2035.json`.
2. **Cache Hit**: Second invocation yielded an immediate $0.005\text{s}$ cache hit with verified identity of elements.

### Height Tag Classification & Zero-Height Investigation
Phase 1 revealed a minimum building height of $0.0\text{m}$. Phase 2 conducted a detailed inspection:

| Height Classification | Entity Count | Details / Phase 3 Handling |
| :--- | :--- | :--- |
| **Explicit Height $> 0.0\text{m}$** | 158 | Height ranges from $3.0\text{m}$ to $417.0\text{m}$ (Avg: $45.94\text{m}$). Ready for direct extrusion. |
| **Explicit Height $== 0.0\text{m}$ (FLAGGED)** | 1 | **ID 812927889** (WTC Cortlandt Subway concourse). Marked in OSM as `location=underground`, `layer=-1`, `height=0`. Phase 3 must ignore or render as a subterranean floor plate. |
| **Missing Height, Has `building:levels`** | 6 | Floor counts range from 4 to 28 levels. Phase 3 will apply fallback: $\text{height} = \text{levels} \times 3.5\text{m}$. |
| **Missing Both** | 31 | Minor un-surveyed structures/annexes. Phase 3 will apply default heuristic height ($10.0\text{m} - 15.0\text{m}$). |

---

## 3. Digital Elevation Model Fetcher (`fetch_elevation.py`)

### Module Status & Features
- **Implementation**: [`geo_terrain/fetch_elevation.py`](file:///c:/Projects/droneswarm/geo_terrain/fetch_elevation.py)
- **Interface**: `fetch_elevation(bbox, zoom_level=15, cache_dir, force_refresh) -> dict`
- **Tile Source**: AWS S3 Terrarium Elevation Tiles (`https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`)
- **RGB Decoding Formula**:
  $$\text{Elevation (meters)} = (\text{Red} \times 256 + \text{Green} + \frac{\text{Blue}}{256}) - 32768$$
- **Caching Mechanism**: Two-tiered cache:
  1. Raw tile PNGs stored in `geo_terrain/cache/tiles/{zoom}_{x}_{y}.png`
  2. Cropped, decoded elevation matrices stored in `geo_terrain/cache/elevation/elevation_<hash>.json`

### Grid Resolution & Output Metrics (Zoom Level 15)
- **Tile Coverage**: 2 tiles (`15/9647/12319.png` and `15/9647/12320.png`)
- **Grid Dimensions**: $153\text{ rows (North to South)} \times 163\text{ columns (West to East)}$
- **Total Height Samples**: $24,939\text{ elevation points}$
- **Spatial Resolution**: $\mathbf{3.63\text{ meters per grid cell}}$ (X: $3.63\text{m}$, Y: $3.63\text{m}$)
- **Elevation Values**:
  - Minimum: $-7.92\text{m}$ (Hudson River waterline/edge)
  - Maximum: $+26.44\text{m}$ (Broadway ridge in Financial District)
  - Mean: $+6.56\text{m}$ ($\sigma = 3.34\text{m}$)

---

## 4. Real Sample Outputs

### Sample 1: Digital Elevation Grid ([`geo_terrain/sample_elevation.json`](file:///c:/Projects/droneswarm/geo_terrain/sample_elevation.json))
```json
{
  "source": "AWS S3 Terrarium Elevation Tiles (elevation-tiles-prod)",
  "bounding_box": {
    "south": 40.709,
    "west": -74.0145,
    "north": 40.714,
    "east": -74.0075
  },
  "zoom_level": 15,
  "grid_dimensions": {
    "rows": 153,
    "cols": 163,
    "total_points": 24939
  },
  "resolution_meters": {
    "x_resolution_m": 3.63,
    "y_resolution_m": 3.63,
    "approx_grid_spacing_m": 3.63
  },
  "physical_extent_meters": {
    "width_m": 591.16,
    "height_m": 555.25
  },
  "stats": {
    "min_elevation_m": -7.92,
    "max_elevation_m": 26.44,
    "avg_elevation_m": 6.56,
    "std_elevation_m": 3.34
  },
  "elevation_grid": [
    [ 4.03, 3.94, 3.84, 3.73, 3.62, 3.51, 3.43, 3.37, ... ],
    ...
  ]
}
```

### Sample 2: Building Footprint Entity ([`geo_terrain/sample_output.json`](file:///c:/Projects/droneswarm/geo_terrain/sample_output.json))
```json
{
  "type": "way",
  "id": 75309476,
  "bounds": {
    "minlat": 40.7125769,
    "minlon": -74.0094485,
    "maxlat": 40.7130662,
    "maxlon": -74.008832
  },
  "geometry": [
    { "lat": 40.7127619, "lon": -74.0094485 },
    { "lat": 40.713058,  "lon": -74.009215 },
    { "lat": 40.7130662, "lon": -74.0091523 },
    { "lat": 40.7129673, "lon": -74.0089378 },
    { "lat": 40.7129176, "lon": -74.008832 },
    { "lat": 40.7125769, "lon": -74.0091076 },
    { "lat": 40.712656,  "lon": -74.0092906 },
    { "lat": 40.7127226, "lon": -74.0094406 },
    { "lat": 40.7127619, "lon": -74.0094485 }
  ],
  "tags": {
    "addr:housenumber": "30",
    "addr:street": "Park Place",
    "building": "apartments",
    "building:colour": "#DCD5B9",
    "building:levels": "82",
    "height": "286",
    "name": "Four Seasons Private Residences New York Downtown"
  }
}
```

---

## 5. Summary & Readiness for Phase 3 (Mesh Extrusion)

- Both data fetchers operate reliably with zero API keys and zero cost.
- Local multi-tier caching shields the application from network latency and rate limits.
- The elevation grid ($3.63\text{m}$ cell pitch) and building footprints ($2,555$ polygon vertices) share identical spatial boundaries and are primed for coordinate normalization and 3D mesh extrusion in Phase 3.
