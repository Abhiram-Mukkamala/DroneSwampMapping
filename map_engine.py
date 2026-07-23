import os
import cv2
import numpy as np
from typing import Optional


class SyntheticMapEngine:
    """
    In-memory simulation map engine that extracts a 600x600 viewport
    without local disk file-write interactions.
    """
    def __init__(self, offline_source: str = "offline_campus.png") -> None:
        self.offline_source = offline_source
        self.image: Optional[np.ndarray] = None

        if os.path.exists(self.offline_source):
            try:
                self.image = cv2.imread(self.offline_source)
            except Exception as e:
                print(f"[MapEngine] Exception loading offline source: {e}")

    def get_viewport(self, lat: float, lon: float, zoom: int) -> np.ndarray:
        """
        Extracts a 600x600 viewport image at the specified coordinates.
        Operates fully in RAM.
        """
        if self.image is not None:
            try:
                h, w = self.image.shape[:2]
                cy, cx = h // 2, w // 2

                y1 = max(0, cy - 300)
                y2 = min(h, cy + 300)
                x1 = max(0, cx - 300)
                x2 = min(w, cx + 300)

                crop = self.image[y1:y2, x1:x2]
                if crop.shape[:2] != (600, 600):
                    crop = cv2.resize(crop, (600, 600))
                return crop
            except Exception as e:
                print(f"[MapEngine] Error processing offline source image: {e}")

        # Check if we have a pre-existing cache file (read-only access)
        cached_path = f"map_cache/map_{lat}_{lon}_{zoom}.png"
        if os.path.exists(cached_path):
            try:
                cached_img = cv2.imread(cached_path)
                if cached_img is not None:
                    if cached_img.shape[:2] != (600, 600):
                        cached_img = cv2.resize(cached_img, (600, 600))
                    return cached_img
            except Exception as e:
                print(f"[MapEngine] Exception loading cached image: {e}")

        # Pure in-memory fallback canvas
        blank_image = np.zeros((600, 600, 3), dtype=np.uint8)
        blank_image[:] = (30, 30, 30)
        return blank_image


def get_map_image(lat: float, lon: float, zoom: int) -> str:
    """
    Deprecated: Deprecated function for backward compatibility.
    Saves viewport to disk cache and returns the filename.
    """
    engine = SyntheticMapEngine()
    viewport = engine.get_viewport(lat, lon, zoom)

    if not os.path.exists("map_cache"):
        os.makedirs("map_cache")

    filename = f"map_cache/map_{lat}_{lon}_{zoom}.png"
    try:
        cv2.imwrite(filename, viewport)
    except Exception as e:
        print(f"[MapEngine] Failed to write cache image to disk: {e}")
    return filename


if __name__ == "__main__":
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18

    engine = SyntheticMapEngine()
    viewport = engine.get_viewport(DRONE_LAT, DRONE_LON, ZOOM)
    print(f"Viewport shape: {viewport.shape}")