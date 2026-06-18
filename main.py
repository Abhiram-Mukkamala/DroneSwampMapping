import sys
from typing import List, Tuple
from map_engine import SyntheticMapEngine
from vision_engine import YOLOVisionEngine
from geo_engine import GeoTranslationEngine

def run_simulation(lat: float, lon: float, zoom: int, img_size: int = 600) -> None:
    """
    Orchestrates the drone tracking simulation loop completely in memory.
    """
    try:
        # 1. Instantiate Wadhwani's SyntheticMapEngine (RAM-only viewport generation)
        map_engine = SyntheticMapEngine(offline_source="offline_campus.png")
        
        # 2. Grab a 600x600 viewport frame in memory
        frame = map_engine.get_viewport(lat, lon, zoom)
        
        # 3. Instantiate YOLOVisionEngine with the optimized ONNX model
        vision_engine = YOLOVisionEngine(model_path="best.onnx")
        
        # 4. Extract target pixel coordinates relative to the 600x600 canvas space
        targets: List[Tuple[float, float]] = vision_engine.detect_targets(frame)
        
        if not targets:
            print("[Tracker] No targets detected in viewport.")
            return

        # 5. Instantiate GeoTranslationEngine and convert coordinate indices to GPS coordinates
        geo_engine = GeoTranslationEngine(
            center_lat=lat,
            center_lon=lon,
            zoom=zoom,
            img_width=img_size,
            img_height=img_size
        )
        
        for i, (target_x, target_y) in enumerate(targets):
            t_lat, t_lon = geo_engine.pixel_to_gps(target_x, target_y)
            # Print final real-world Latitude and Longitude tracking strings
            print(f"[Tracker] Target {i+1} detected at Latitude: {t_lat:.8f}, Longitude: {t_lon:.8f}")

    except Exception as e:
        print(f"[Simulation Coordinator] Error during simulation execution: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Drone simulation configuration
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18
    IMG_SIZE = 600

    print("--- Starting Drone Tracking Simulation Pipeline ---")
    run_simulation(DRONE_LAT, DRONE_LON, ZOOM, IMG_SIZE)
    print("--- Simulation Pipeline Execution Finished ---")