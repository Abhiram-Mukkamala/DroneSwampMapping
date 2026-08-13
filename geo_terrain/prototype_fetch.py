"""
Standalone Prototype Fetch Script for DroneSwampMapping - AI Terrain Mode (Phase 1)
Fetches real-world building footprint data with geometries and height tags
from OpenStreetMap via the Overpass API for an arbitrary bounding box.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple

# Primary and fallback Overpass API endpoints (no authentication required)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Default test bounding box: Lower Manhattan (Financial District / World Trade Center, NYC)
# Approximately 500m x 550m area with high density of skyscraper footprints & height data
# Format: (south_lat, west_lon, north_lat, east_lon)
DEFAULT_BBOX: Tuple[float, float, float, float] = (
    40.7090,  # South latitude
    -74.0145, # West longitude
    40.7140,  # North latitude
    -74.0075  # East longitude
)


def build_overpass_query(bbox: Tuple[float, float, float, float], timeout: int = 30) -> str:
    """
    Constructs an Overpass QL query to fetch all building ways and relations
    with full geometry coordinates within the specified bounding box.
    """
    south, west, north, east = bbox
    query = f"""[out:json][timeout:{timeout}];
(
  way["building"]({south},{west},{north},{east});
  relation["building"]({south},{west},{north},{east});
);
out body geom;
"""
    return query


def fetch_building_footprints(
    bbox: Tuple[float, float, float, float] = DEFAULT_BBOX,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Sends the Overpass query to the public Overpass API and returns the parsed JSON response.
    Tries fallback endpoints if the primary endpoint fails or is rate-limited.
    """
    query = build_overpass_query(bbox, timeout=timeout)
    encoded_data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    headers = {
        "User-Agent": "DroneSwampMapping-TerrainPrototype/1.0 (Research Prototype)",
        "Accept": "application/json",
    }

    last_exception = None
    for endpoint in OVERPASS_ENDPOINTS:
        print(f"[*] Querying Overpass API endpoint: {endpoint}...")
        req = urllib.request.Request(endpoint, data=encoded_data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout + 10) as response:
                if response.status == 200:
                    raw_text = response.read().decode("utf-8")
                    data = json.loads(raw_text)
                    print(f"[+] Successfully received response from {endpoint}")
                    return data
                else:
                    print(f"[-] HTTP {response.status} from {endpoint}")
        except Exception as e:
            print(f"[-] Failed with endpoint {endpoint}: {e}")
            last_exception = e

    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_exception}")


def analyze_footprints(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the raw Overpass elements to compute statistics on geometries,
    height tags, and building levels for Phase 2 mesh extrusion planning.
    """
    elements: List[Dict[str, Any]] = data.get("elements", [])
    total_buildings = len(elements)
    with_height = 0
    with_levels = 0
    with_name = 0
    total_nodes = 0
    heights: List[float] = []

    for el in elements:
        tags = el.get("tags", {})
        geom = el.get("geometry", [])
        total_nodes += len(geom)

        if "name" in tags:
            with_name += 1

        if "height" in tags:
            with_height += 1
            try:
                # Parse numeric height value, stripping units like 'm' or 'ft' if present
                h_str = tags["height"].lower().replace("m", "").replace("meters", "").strip()
                if "ft" in h_str or "'" in h_str:
                    h_val = float(h_str.replace("ft", "").replace("'", "").strip()) * 0.3048
                else:
                    h_val = float(h_str)
                heights.append(h_val)
            except ValueError:
                pass

        if "building:levels" in tags:
            with_levels += 1

    stats = {
        "total_elements": total_buildings,
        "buildings_with_explicit_height": with_height,
        "buildings_with_level_count": with_levels,
        "buildings_with_name": with_name,
        "total_polygon_vertices": total_nodes,
        "min_height_m": min(heights) if heights else None,
        "max_height_m": max(heights) if heights else None,
        "avg_height_m": round(sum(heights) / len(heights), 2) if heights else None,
    }
    return stats


def main():
    south, west, north, east = DEFAULT_BBOX
    print("=" * 60)
    print(" DroneSwampMapping - AI Terrain Mode (Phase 1 Prototype)")
    print("=" * 60)
    print(f"Target Bounding Box:")
    print(f"  South-West: ({south:.4f}, {west:.4f})")
    print(f"  North-East: ({north:.4f}, {east:.4f})")
    print(f"  Area: ~550m x 600m (Lower Manhattan / Financial District, NYC)\n")

    # Fetch footprints
    data = fetch_building_footprints(DEFAULT_BBOX)

    # Determine output file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "sample_output.json")

    # Save raw output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"\n[+] Raw response saved to: {output_path} ({file_size_kb:.1f} KB)")

    # Run analysis
    stats = analyze_footprints(data)
    print("\n--- Summary Statistics ---")
    print(f"  Total building entities:           {stats['total_elements']}")
    print(f"  Buildings with explicit height:    {stats['buildings_with_explicit_height']}")
    print(f"  Buildings with 'building:levels':  {stats['buildings_with_level_count']}")
    print(f"  Buildings with mapped names:       {stats['buildings_with_name']}")
    print(f"  Total polygon vertices:            {stats['total_polygon_vertices']}")
    if stats['max_height_m'] is not None:
        print(f"  Height range:                      {stats['min_height_m']}m - {stats['max_height_m']}m (Avg: {stats['avg_height_m']}m)")
    print("=" * 60)


if __name__ == "__main__":
    main()
