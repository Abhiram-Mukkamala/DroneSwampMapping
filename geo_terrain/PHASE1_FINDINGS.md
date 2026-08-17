# DroneSwampMapping - AI Terrain Mode (Phase 1 Findings)

## 1. Executive Summary & Feasibility Comparison

For Phase 1 of the **AI Terrain Mode**, we evaluated two primary candidate sources for retrieving real-world building footprint geometry and height data for arbitrary small bounding boxes (e.g., $500\text{m} \times 500\text{m}$ to $1\text{km} \times 1\text{km}$):

| Criteria | **Microsoft Global ML Building Footprints** | **OpenStreetMap via Overpass API** (Selected) |
| :--- | :--- | :--- |
| **Query Mechanism** | Static bulk archives (GeoParquet / Delta / CSV gzip) partitioned by Bing Map Level 9 Quadkeys (~78km $\times$ 78km tiles) or full country archives. | Dynamic REST API with Overpass QL spatial queries (`(south, west, north, east)` bounding box). |
| **Arbitrary Small Area Query** | **High friction**. No lightweight REST endpoint. Requires querying Microsoft Planetary Computer STAC catalog + DuckDB/GeoPandas with spatial partitioning & HTTP range requests, or downloading full country files (>100MB to multiple GBs). | **Native & Instant**. Direct HTTP POST/GET request filtered directly on the bounding box; returns in < 1 second. |
| **Output Format** | GeoParquet / GeoJSON | OSM JSON (with `out geom;`) or GeoJSON |
| **Height / Altitude Metadata** | Estimated ML height in meters (often `-1` or missing in many regions; no level counts). | High density of explicit `height`, `building:levels`, `min_height`, and `roof:shape` tags in urban areas. |
| **Semantic Tags** | Geometry & ML confidence score only. | Rich tags: building names, street addresses, colors (`building:colour`), materials, and roof shapes. |
| **Authentication & Cost** | Free public dataset / Planetary Computer. | 100% Free, no API key or token required. |
| **Recommendation** | Unsuitable for real-time, on-demand small bbox queries without heavy backend infrastructure. | **Selected**: Best suited for lightweight, fast, on-demand terrain and city generation. |

---

## 2. Real Sample Output (from `sample_output.json`)

Below is an exact raw element returned by the prototype fetch script (`geo_terrain/prototype_fetch.py`) querying a $550\text{m} \times 600\text{m}$ bounding box in Lower Manhattan (Financial District / World Trade Center area, NYC):

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
  "nodes": [
    889261888,
    13829922092,
    889261824,
    12085869782,
    889261540,
    889261958,
    12085869784,
    13829922091,
    889261888
  ],
  "geometry": [
    {
      "lat": 40.7127619,
      "lon": -74.0094485
    },
    {
      "lat": 40.713058,
      "lon": -74.009215
    },
    {
      "lat": 40.7130662,
      "lon": -74.0091523
    },
    {
      "lat": 40.7129673,
      "lon": -74.0089378
    },
    {
      "lat": 40.7129176,
      "lon": -74.008832
    },
    {
      "lat": 40.7125769,
      "lon": -74.0091076
    },
    {
      "lat": 40.712656,
      "lon": -74.0092906
    },
    {
      "lat": 40.7127226,
      "lon": -74.0094406
    },
    {
      "lat": 40.7127619,
      "lon": -74.0094485
    }
  ],
  "tags": {
    "addr:city": "New York",
    "addr:housenumber": "30",
    "addr:state": "NY",
    "addr:street": "Park Place",
    "architect": "Robert A.M. Stern Architects",
    "building": "apartments",
    "building:colour": "#DCD5B9",
    "building:levels": "82",
    "building:part": "yes",
    "height": "286",
    "name": "Four Seasons Private Residences New York Downtown",
    "operator": "Silverstein Properties",
    "roof:colour": "#d3d1d0",
    "start_date": "2015",
    "website": "https://www.thirtyparkplace.com/",
    "wikidata": "Q224126"
  }
}
```

### Key Properties in the Output
- **`geometry`**: Array of `{lat, lon}` vertices forming the closed footprint polygon (first and last coordinate match).
- **`tags.height`**: Explicit building height in meters (e.g. `286` for 286 meters).
- **`tags.building:levels`**: Floor count (e.g. `82`), usable as a height fallback (`levels * 3.5m`) if `height` is absent.
- **`tags.building:colour` / `tags.roof:colour`**: Hex or named color codes directly usable in 3D rendering.

---

## 3. Elevation & Heightmap API Options (Research Summary)

To fuse ground terrain elevation with building footprints, we researched four candidate elevation APIs:

### Candidate A: Open-Elevation API (`api.open-elevation.com`)
- **Model**: Point lookup REST API (SRTM data source).
- **Bounding Box Query**: No native bounding box endpoint; requires generating an $(N \times M)$ grid of lat/lon coordinates and querying via POST `/api/v1/lookup` with up to 100 points per batch.
- **Rate Limits & Auth**: No authentication required. Public endpoint can experience occasional downtime or throttling; however, the server is open source (GPLv2) and can be run locally via Docker.

### Candidate B: AWS Terrarium Elevation Tiles (`elevation-tiles-prod`)
- **Model**: Global raster elevation tiles hosted on Amazon S3 (`https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`).
- **Data Encoding**: Elevation encoded into standard RGB PNG pixels:
  $$\text{Elevation (meters)} = (\text{Red} \times 256 + \text{Green} + \frac{\text{Blue}}{256}) - 32768$$
- **Feasibility**: **High**. Zero auth, instant HTTP tile fetching, directly ingestible by WebGL / Three.js heightmap textures and Python raster tools.

### Candidate C: USGS 3DEP / OpenTopography API
- **Model**: High-resolution LiDAR / DEM data for the United States (1m to 10m resolution).
- **Bounding Box Query**: OpenTopography provides a REST API that extracts a subset GeoTIFF mosaic for an exact bounding box (`/api/bulk?demtype=USGS30m&south=...&north=...`).
- **Rate Limits & Auth**: Requires a free API key; limited daily quota for anonymous accounts.

### Candidate D: Open-Meteo Elevation API (`api.open-meteo.com/v1/elevation`)
- **Model**: Point lookup API based on 90m Copernicus GLO-90 DEM.
- **Feasibility**: High reliability, batch queries up to 100 points per call, no authentication required.

---

## 4. Rate Limits, Authentication & Cost Concerns

1. **Overpass API**:
   - **Cost**: $0.00 (Public infrastructure maintained by OpenStreetMap contributors).
   - **Authentication**: None required.
   - **Limits**: Public endpoints (`overpass-api.de`, `overpass.kumi.systems`) enforce concurrency limits (max 2 concurrent queries per IP) and execution slot limits.
   - **Mitigations for Prototype/Production**:
     - Keep bounding boxes reasonable ($\le 2\text{km} \times 2\text{km}$).
     - Use fallback endpoints (configured in `prototype_fetch.py`).
     - Cache fetched bounding boxes locally (`.json` or `.geojson`) to avoid repeated network calls.

---

## 5. What Phase 2 (Mesh Extrusion Pipeline) Will Need to Consume

Phase 2 will convert the raw JSON output into extruded 3D meshes for DroneSwampMapping. The processing pipeline will require:

1. **Geographic to Local Metric Projection**:
   - Convert `(lat, lon)` GPS coordinates into local Cartesian coordinates $(x, z)$ in meters relative to the bounding box center or origin:
     $$x = (\text{lon} - \text{lon}_0) \times \left(\frac{\pi}{180} \times R \times \cos(\text{lat}_0)\right)$$
     $$z = -(\text{lat} - \text{lat}_0) \times \left(\frac{\pi}{180} \times R\right)$$
     *(where $R \approx 6,378,137\text{m}$)*

2. **Height Parsing & Fallback Logic**:
   - **Priority 1**: `float(tags['height'])` (clean strings like `"39m"` $\to 39.0$).
   - **Priority 2**: `float(tags['building:levels']) * 3.5` meters.
   - **Priority 3**: Fallback default height (e.g., $12.0\text{m}$) with slight stochastic variation for visual realism.

3. **Polygon Triangulation & Extrusion**:
   - Transform the 2D polygon vertex loop into a Three.js `ShapeGeometry` or extruded prism (`ExtrudeGeometry`).
   - Ground plane alignment: Place the base of each building mesh at the local ground terrain height from the elevation model.
