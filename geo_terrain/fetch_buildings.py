"""
Module: geo_terrain.fetch_buildings
DroneSwampMapping - AI Terrain Mode (Phase 2)

Fetches building footprints and metadata from OpenStreetMap via the Overpass API
with local file-based caching and fallback endpoint handling.
"""

import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# Overpass API endpoints (tested in Phase 1)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Default test bounding box: Lower Manhattan (Financial District / World Trade Center, NYC)
# (south, west, north, east)
DEFAULT_BBOX: Tuple[float, float, float, float] = (
    40.7090,  # South latitude
    -74.0145, # West longitude
    40.7140,  # North latitude
    -74.0075  # East longitude
)


def _get_bbox_hash(bbox: Tuple[float, float, float, float]) -> str:
    """Generates a stable MD5 hash string for a bounding box tuple."""
    canon = f"{bbox[0]:.6f}_{bbox[1]:.6f}_{bbox[2]:.6f}_{bbox[3]:.6f}"
    return hashlib.md5(canon.encode("utf-8")).hexdigest()


def build_overpass_query(bbox: Tuple[float, float, float, float], timeout: int = 30) -> str:
    """
    Constructs an Overpass QL query to fetch all building ways and relations
    with full geometry coordinates within the specified bounding box.
    """
    south, west, north, east = bbox
    return f"""[out:json][timeout:{timeout}];
(
  way["building"]({south},{west},{north},{east});
  relation["building"]({south},{west},{north},{east});
);
out body geom;
"""


def fetch_buildings(
    bbox: Tuple[float, float, float, float] = DEFAULT_BBOX,
    cache_dir: Optional[str] = None,
    force_refresh: bool = False,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Fetches building footprints for a given bounding box from OpenStreetMap via Overpass API.
    
    Args:
        bbox: (south, west, north, east) coordinates in degrees.
        cache_dir: Directory to store cached JSON responses. Defaults to geo_terrain/cache/.
        force_refresh: If True, bypasses cache and queries live API.
        timeout: Query timeout in seconds.

    Returns:
        Dict containing raw Overpass JSON response with building elements and geometries.
    """
    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    
    os.makedirs(cache_dir, exist_ok=True)
    bbox_hash = _get_bbox_hash(bbox)
    cache_file = os.path.join(cache_dir, f"buildings_{bbox_hash}.json")

    # Check local cache
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[CACHE HIT] Loaded {len(data.get('elements', []))} buildings from {cache_file}")
            return data
        except Exception as e:
            print(f"[CACHE WARN] Failed to read cache file {cache_file}: {e}. Falling back to live API.")

    # Cache miss or forced refresh: Query live Overpass API
    print(f"[CACHE MISS] Fetching building data for bbox {bbox} from Overpass API...")
    query = build_overpass_query(bbox, timeout=timeout)
    encoded_data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    headers = {
        "User-Agent": "DroneSwampMapping-Terrain/2.0 (Academic/Research)",
        "Accept": "application/json",
    }

    last_exception = None
    for endpoint in OVERPASS_ENDPOINTS:
        print(f"[*] Trying endpoint: {endpoint}...")
        req = urllib.request.Request(endpoint, data=encoded_data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout + 10) as response:
                if response.status == 200:
                    raw_text = response.read().decode("utf-8")
                    data = json.loads(raw_text)
                    print(f"[+] Successfully received data ({len(data.get('elements', []))} elements).")
                    
                    # Write to cache
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"[+] Saved response to cache: {cache_file}")
                    return data
        except Exception as e:
            print(f"[-] Endpoint {endpoint} failed: {e}")
            last_exception = e

    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_exception}")


def parse_numeric_height(val: str) -> Optional[float]:
    """Helper to parse height strings (e.g., '39', '39m', '120 ft') into meters."""
    if not val:
        return None
    cleaned = val.lower().replace("m", "").replace("meters", "").strip()
    try:
        if "ft" in cleaned or "'" in cleaned:
            return float(cleaned.replace("ft", "").replace("'", "").strip()) * 0.3048
        return float(cleaned)
    except ValueError:
        return None


def inspect_building_heights(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans and classifies building entities by height tag availability.
    
    --------------------------------------------------------------------------
    NOTE ON HEIGHT FALLBACK LOGIC (For Phase 3 Mesh Extrusion):
    --------------------------------------------------------------------------
    In raw OSM data, height tags fall into four distinct categories:
      1. Valid positive height (> 0.0m): Explicitly surveyed building height in meters.
      2. Zero or non-positive height (== 0.0m): Certain ground structures, building
         footprint outlines at grade level, platforms, or un-extruded building:parts
         report height="0" or "0.0".
      3. Missing height but valid building:levels (> 0): Floor count available.
         Phase 3 will apply fallback: height = levels * 3.5m (approx. 3.5m/floor).
      4. Missing both height and building:levels: Unsurveyed structures.
         Phase 3 will apply fallback: default heuristic height (e.g. 10.0m - 15.0m).
    --------------------------------------------------------------------------
    """
    elements = data.get("elements", [])
    valid_positive_heights = []
    zero_height_entities = []
    has_levels_no_height = []
    missing_both = []

    for el in elements:
        tags = el.get("tags", {})
        el_id = el.get("id")
        el_type = el.get("type")
        raw_h = tags.get("height")
        raw_lvl = tags.get("building:levels")

        parsed_h = parse_numeric_height(raw_h) if raw_h is not None else None

        if parsed_h is not None and parsed_h > 0:
            valid_positive_heights.append((el_id, parsed_h, tags.get("name", "Unnamed")))
        elif parsed_h is not None and parsed_h <= 0.0:
            # FLAG: Entity explicitly has height == 0 or negative
            zero_height_entities.append({
                "id": el_id,
                "type": el_type,
                "raw_height": raw_h,
                "name": tags.get("name", "Unnamed"),
                "tags": tags
            })
        elif raw_lvl is not None:
            has_levels_no_height.append((el_id, raw_lvl, tags.get("name", "Unnamed")))
        else:
            missing_both.append(el_id)

    return {
        "total_elements": len(elements),
        "count_valid_positive_height": len(valid_positive_heights),
        "count_zero_or_negative_height": len(zero_height_entities),
        "count_levels_only": len(has_levels_no_height),
        "count_missing_both": len(missing_both),
        "zero_height_entities_sample": zero_height_entities[:5],
        "height_stats": {
            "min_m": min([h for _, h, _ in valid_positive_heights]) if valid_positive_heights else None,
            "max_m": max([h for _, h, _ in valid_positive_heights]) if valid_positive_heights else None,
            "avg_m": round(sum([h for _, h, _ in valid_positive_heights]) / len(valid_positive_heights), 2) if valid_positive_heights else None
        }
    }


def main():
    print("=" * 65)
    print(" DroneSwampMapping - Building Fetcher (Phase 2)")
    print("=" * 65)
    
    # 1. First call (test live fetch / cache write)
    data = fetch_buildings(DEFAULT_BBOX)
    
    # 2. Second call (test cache hit)
    print("\nTesting cache hit on second invocation...")
    cached_data = fetch_buildings(DEFAULT_BBOX)
    assert len(data.get("elements", [])) == len(cached_data.get("elements", []))
    print("[+] Cache validation successful!")

    # 3. Analyze height classification & flag height == 0
    inspection = inspect_building_heights(data)
    print("\n--- Height Classification & Zero-Height Analysis ---")
    print(f"  Total elements fetched:              {inspection['total_elements']}")
    print(f"  Explicit height > 0:                 {inspection['count_valid_positive_height']}")
    print(f"  Explicit height == 0 (FLAGGED):      {inspection['count_zero_or_negative_height']}")
    print(f"  Missing height, has levels:          {inspection['count_levels_only']}")
    print(f"  Missing both (needs heuristic):      {inspection['count_missing_both']}")
    if inspection['height_stats']['max_m']:
        print(f"  Positive height range:               {inspection['height_stats']['min_m']}m - {inspection['height_stats']['max_m']}m (Avg: {inspection['height_stats']['avg_m']}m)")
    
    if inspection["zero_height_entities_sample"]:
        print("\n  Sample zero-height entities flagged:")
        for ent in inspection["zero_height_entities_sample"]:
            print(f"    - ID {ent['id']} ({ent['type']}): raw height='{ent['raw_height']}', tags={list(ent['tags'].keys())}")

    print("=" * 65)


if __name__ == "__main__":
    main()
