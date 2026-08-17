"""
Module: geo_terrain.fetch_elevation
DroneSwampMapping - AI Terrain Mode (Phase 2)

Fetches and decodes real-world digital elevation models (DEM) from AWS Terrarium
elevation tiles (hosted on S3) for an arbitrary geographic bounding box.
"""

import hashlib
import io
import json
import math
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

# AWS Terrarium tile URL template (S3 Open Data, public, zero auth)
TERRARIUM_URL_TEMPLATE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

# Default test bounding box: Lower Manhattan (Financial District / World Trade Center, NYC)
# (south, west, north, east)
DEFAULT_BBOX: Tuple[float, float, float, float] = (
    40.7090,  # South latitude
    -74.0145, # West longitude
    40.7140,  # North latitude
    -74.0075  # East longitude
)

DEFAULT_ZOOM = 15  # ~3.5m to ~4.8m resolution per pixel at mid-latitudes


def _get_bbox_hash(bbox: Tuple[float, float, float, float], zoom: int) -> str:
    """Generates a stable MD5 hash string for a bounding box + zoom level."""
    canon = f"{bbox[0]:.6f}_{bbox[1]:.6f}_{bbox[2]:.6f}_{bbox[3]:.6f}_z{zoom}"
    return hashlib.md5(canon.encode("utf-8")).hexdigest()


def latlon_to_global_pixel(lat: float, lon: float, zoom: int) -> Tuple[float, float]:
    """
    Converts latitude and longitude (WGS84 degrees) into global continuous
    pixel coordinates in Web Mercator (EPSG:3857) space at a given zoom level.
    """
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_px = (lon + 180.0) / 360.0 * n * 256.0
    # In Web Mercator image coordinates, Y=0 is North and increases Southward
    y_px = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256.0
    return x_px, y_px


def global_pixel_to_latlon(x_px: float, y_px: float, zoom: int) -> Tuple[float, float]:
    """Converts global pixel coordinates back into latitude and longitude."""
    n = 2.0 ** zoom
    lon = (x_px / (n * 256.0)) * 360.0 - 180.0
    y_val = 1.0 - (y_px / (n * 256.0)) * 2.0
    lat_rad = math.atan(math.sinh(math.pi * y_val))
    lat = math.degrees(lat_rad)
    return lat, lon


def decode_terrarium_tile(image_data: bytes) -> np.ndarray:
    """
    Decodes an AWS Terrarium RGB PNG into elevation values in meters.
    Formula: elevation = (R * 256 + G + B / 256) - 32768
    """
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    elevation = (r * 256.0 + g + b / 256.0) - 32768.0
    return elevation


def fetch_tile(
    zoom: int,
    x: int,
    y: int,
    tile_cache_dir: str,
    timeout: int = 15
) -> np.ndarray:
    """
    Fetches a single Terrarium tile from AWS S3 (or local cache) and returns
    the 256x256 decoded elevation array.
    """
    os.makedirs(tile_cache_dir, exist_ok=True)
    cache_tile_path = os.path.join(tile_cache_dir, f"{zoom}_{x}_{y}.png")

    if os.path.exists(cache_tile_path):
        with open(cache_tile_path, "rb") as f:
            raw_bytes = f.read()
    else:
        url = TERRARIUM_URL_TEMPLATE.format(z=zoom, x=x, y=y)
        req = urllib.request.Request(url, headers={"User-Agent": "DroneSwampMapping-Elevation/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
        with open(cache_tile_path, "wb") as f:
            f.write(raw_bytes)

    return decode_terrarium_tile(raw_bytes)


def fetch_elevation(
    bbox: Tuple[float, float, float, float] = DEFAULT_BBOX,
    zoom_level: int = DEFAULT_ZOOM,
    cache_dir: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Fetches and reconstructs a 2D elevation grid covering the specified bounding box
    using AWS Terrarium elevation tiles.

    Args:
        bbox: (south, west, north, east) in decimal degrees.
        zoom_level: Slippy map zoom level (e.g. 14 or 15).
        cache_dir: Cache root directory. Defaults to geo_terrain/cache/.
        force_refresh: If True, ignores cached grid and re-queries tiles.

    Returns:
        Dict with metadata and 2D list of elevation floats (rows North->South, cols West->East).
    """
    south, west, north, east = bbox
    if south >= north or west >= east:
        raise ValueError(f"Invalid bounding box: south < north and west < east required. Got: {bbox}")

    if cache_dir is None:
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

    elev_cache_dir = os.path.join(cache_dir, "elevation")
    tile_cache_dir = os.path.join(cache_dir, "tiles")
    os.makedirs(elev_cache_dir, exist_ok=True)
    os.makedirs(tile_cache_dir, exist_ok=True)

    bbox_hash = _get_bbox_hash(bbox, zoom_level)
    cached_result_path = os.path.join(elev_cache_dir, f"elevation_{bbox_hash}.json")

    if not force_refresh and os.path.exists(cached_result_path):
        try:
            with open(cached_result_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            print(f"[CACHE HIT] Loaded elevation grid from {cached_result_path}")
            return cached_data
        except Exception as e:
            print(f"[CACHE WARN] Failed to read elevation cache: {e}. Recomputing.")

    print(f"[CACHE MISS] Fetching elevation tiles at zoom {zoom_level} for bbox {bbox}...")

    # Calculate global pixel coordinates
    min_x_px, max_y_px = latlon_to_global_pixel(south, west, zoom_level)
    max_x_px, min_y_px = latlon_to_global_pixel(north, east, zoom_level)

    tile_min_x = int(min_x_px // 256)
    tile_max_x = int(max_x_px // 256)
    tile_min_y = int(min_y_px // 256)
    tile_max_y = int(max_y_px // 256)

    num_tiles_x = tile_max_x - tile_min_x + 1
    num_tiles_y = tile_max_y - tile_min_y + 1
    print(f"[*] Required tile grid: {num_tiles_x}x{num_tiles_y} ({num_tiles_x * num_tiles_y} tiles)")

    # Build composite mosaic array
    mosaic = np.zeros((num_tiles_y * 256, num_tiles_x * 256), dtype=np.float64)

    for ty_idx, ty in enumerate(range(tile_min_y, tile_max_y + 1)):
        for tx_idx, tx in enumerate(range(tile_min_x, tile_max_x + 1)):
            tile_elev = fetch_tile(zoom_level, tx, ty, tile_cache_dir)
            mosaic[
                ty_idx * 256 : (ty_idx + 1) * 256,
                tx_idx * 256 : (tx_idx + 1) * 256
            ] = tile_elev

    # Crop mosaic to exact bounding box pixel bounds
    start_x = int(round(min_x_px - tile_min_x * 256))
    start_y = int(round(min_y_px - tile_min_y * 256))
    end_x = int(round(max_x_px - tile_min_x * 256))
    end_y = int(round(max_y_px - tile_min_y * 256))

    # Ensure valid slice boundaries
    start_x = max(0, start_x)
    start_y = max(0, start_y)
    end_x = min(mosaic.shape[1], max(start_x + 1, end_x))
    end_y = min(mosaic.shape[0], max(start_y + 1, end_y))

    grid = mosaic[start_y:end_y, start_x:end_x]
    rows, cols = grid.shape

    # Calculate geographic span and resolution in meters
    lat_center = (south + north) / 2.0
    meters_per_deg_lat = 111132.954 - 559.822 * math.cos(2 * math.radians(lat_center))
    meters_per_deg_lon = 111412.84 * math.cos(math.radians(lat_center))
    
    width_meters = (east - west) * meters_per_deg_lon
    height_meters = (north - south) * meters_per_deg_lat
    
    res_x_m = width_meters / cols
    res_y_m = height_meters / rows

    stats = {
        "min_elevation_m": round(float(np.min(grid)), 2),
        "max_elevation_m": round(float(np.max(grid)), 2),
        "avg_elevation_m": round(float(np.mean(grid)), 2),
        "std_elevation_m": round(float(np.std(grid)), 2),
    }

    # Convert 2D numpy array to standard Python list of rounded floats
    grid_list = [[round(float(val), 2) for val in row] for row in grid]

    result: Dict[str, Any] = {
        "source": "AWS S3 Terrarium Elevation Tiles (elevation-tiles-prod)",
        "bounding_box": {
            "south": south,
            "west": west,
            "north": north,
            "east": east
        },
        "zoom_level": zoom_level,
        "grid_dimensions": {
            "rows": rows,
            "cols": cols,
            "total_points": rows * cols
        },
        "resolution_meters": {
            "x_resolution_m": round(res_x_m, 2),
            "y_resolution_m": round(res_y_m, 2),
            "approx_grid_spacing_m": round((res_x_m + res_y_m) / 2.0, 2)
        },
        "physical_extent_meters": {
            "width_m": round(width_meters, 2),
            "height_m": round(height_meters, 2)
        },
        "stats": stats,
        "elevation_grid": grid_list
    }

    # Save to cache
    with open(cached_result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[+] Saved elevation result to cache: {cached_result_path}")

    return result


def main():
    print("=" * 65)
    print(" DroneSwampMapping - Elevation Fetcher (Phase 2)")
    print("=" * 65)
    south, west, north, east = DEFAULT_BBOX
    print(f"Target Bounding Box: ({south:.4f}, {west:.4f}) to ({north:.4f}, {east:.4f})")
    print(f"Zoom Level: {DEFAULT_ZOOM}\n")

    # 1. Fetch elevation grid
    result = fetch_elevation(DEFAULT_BBOX, zoom_level=DEFAULT_ZOOM)

    # 2. Save real output to geo_terrain/sample_elevation.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_out_path = os.path.join(script_dir, "sample_elevation.json")
    with open(sample_out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    file_size_kb = os.path.getsize(sample_out_path) / 1024
    print(f"\n[+] Saved sample output to {sample_out_path} ({file_size_kb:.1f} KB)")

    # 3. Test second invocation for cache hit verification
    print("\nTesting cache hit on second invocation...")
    cached_result = fetch_elevation(DEFAULT_BBOX, zoom_level=DEFAULT_ZOOM)
    assert cached_result["grid_dimensions"] == result["grid_dimensions"]
    print("[+] Elevation cache hit verified successfully!")

    # 4. Display stats
    dims = result["grid_dimensions"]
    res = result["resolution_meters"]
    ext = result["physical_extent_meters"]
    stats = result["stats"]

    print("\n--- Elevation Grid Summary ---")
    print(f"  Grid Dimensions:       {dims['rows']} rows (N->S) x {dims['cols']} cols (W->E)")
    print(f"  Total Data Points:     {dims['total_points']}")
    print(f"  Physical Extent:       {ext['width_m']}m width x {ext['height_m']}m height")
    print(f"  Pixel Grid Spacing:    ~{res['approx_grid_spacing_m']} meters/pixel")
    print(f"  Elevation Min/Max:     {stats['min_elevation_m']}m / {stats['max_elevation_m']}m (Avg: {stats['avg_elevation_m']}m)")
    print("=" * 65)


if __name__ == "__main__":
    main()
