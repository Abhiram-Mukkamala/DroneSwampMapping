import math
from typing import Tuple


class GeoTranslationEngine:
    """
    Translates local 2D pixel coordinates on a cached satellite map view
    back into real-world GPS Latitude and Longitude coordinates.
    """
    def __init__(self, center_lat: float, center_lon: float, zoom: int,
                 img_width: int = 600, img_height: int = 600) -> None:

        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom = zoom
        self.img_width = img_width
        self.img_height = img_height

    def pixel_to_gps(self, target_x: float,
                     target_y: float) -> Tuple[float, float]:

        """
        Calculates the real-world Latitude and Longitude for
        a target coordinate (target_x, target_y).
        """
        try:
            r_earth = 6378137.0
            # Meters per pixel calculation based on Web Mercator projection
            lat_rad = math.radians(self.center_lat)
            meters_per_pixel = (2 * math.pi * r_earth * math.cos(lat_rad)) / (self.img_width * (2 ** self.zoom))

            # Pixel displacement from center
            # (positive dx = east, positive dy = north)
            dx_pixels = target_x - (self.img_width / 2.0)
            dy_pixels = (self.img_height / 2.0) - target_y

            dx_meters = dx_pixels * meters_per_pixel
            dy_meters = dy_pixels * meters_per_pixel

            # Convert displacements to degrees
            d_lat = (dy_meters / r_earth) * (180.0 / math.pi)
            d_lon = (dx_meters / (r_earth * math.cos(lat_rad))) * (180.0 / math.pi)

            target_lat = self.center_lat + d_lat
            target_lon = self.center_lon + d_lon

            return target_lat, target_lon
        except ZeroDivisionError as zde:
            print(f"[GeoTranslationEngine] Zero division error in calculation: {zde}")
            return self.center_lat, self.center_lon
        except Exception as e:
            print(f"[GeoTranslationEngine] Exception in coordinate translation: {e}")
            return self.center_lat, self.center_lon


def pixel_to_gps(center_lat: float, center_lon: float, zoom: int, img_width: int, img_height: int, target_x: float, target_y: float) -> Tuple[float, float]:
    """
    Deprecated: Deprecated function for backward compatibility.
    """
    engine = GeoTranslationEngine(center_lat, center_lon, zoom, img_width, img_height)
    return engine.pixel_to_gps(target_x, target_y)


if __name__ == "__main__":
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18
    IMG_WIDTH = 600
    IMG_HEIGHT = 600
    TARGET_X = 400
    TARGET_Y = 200

    engine = GeoTranslationEngine(DRONE_LAT, DRONE_LON, ZOOM, IMG_WIDTH, IMG_HEIGHT)
    target_lat, target_lon = engine.pixel_to_gps(TARGET_X, TARGET_Y)
    print(f"Target GPS: {target_lat}, {target_lon}")