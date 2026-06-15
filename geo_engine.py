import math

def pixel_to_gps(center_lat, center_lon, zoom, img_width, img_height, target_x, target_y):
    meters_per_pixel = (156543.03392 * math.cos(center_lat * math.pi / 180.0)) / (2 ** zoom)
    
    dx_pixels = target_x - (img_width / 2.0)
    dy_pixels = (img_height / 2.0) - target_y
    
    dx_meters = dx_pixels * meters_per_pixel
    dy_meters = dy_pixels * meters_per_pixel
    
    r_earth = 6378137.0
    d_lat = (dy_meters / r_earth) * (180.0 / math.pi)
    d_lon = (dx_meters / (r_earth * math.cos(center_lat * math.pi / 180.0))) * (180.0 / math.pi)
    
    target_lat = center_lat + d_lat
    target_lon = center_lon + d_lon
    
    return target_lat, target_lon

if __name__ == "__main__":
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18
    IMG_WIDTH = 600
    IMG_HEIGHT = 600
    TARGET_X = 400
    TARGET_Y = 200
    
    target_lat, target_lon = pixel_to_gps(
        DRONE_LAT, DRONE_LON, ZOOM, IMG_WIDTH, IMG_HEIGHT, TARGET_X, TARGET_Y
    )
    print(f"{target_lat}, {target_lon}")