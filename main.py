from map_engine import get_map_image
from vision_engine import detect_targets
from geo_engine import pixel_to_gps

if __name__ == "__main__":
    MY_API_KEY = "YOUR_API_KEY_HERE"
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18
    IMG_WIDTH = 600
    IMG_HEIGHT = 600

    image_path = get_map_image(DRONE_LAT, DRONE_LON, ZOOM, MY_API_KEY)

    if image_path:
        targets = detect_targets(image_path)
        
        for i, (target_x, target_y) in enumerate(targets):
            t_lat, t_lon = pixel_to_gps(
                DRONE_LAT, DRONE_LON, ZOOM, IMG_WIDTH, IMG_HEIGHT, target_x, target_y
            )
            print(f"{t_lat}, {t_lon}")