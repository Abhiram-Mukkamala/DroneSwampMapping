import os
import cv2
import numpy as np

def get_map_image(lat, lon, zoom):
    if not os.path.exists("map_cache"):
        os.makedirs("map_cache")
        
    filename = f"map_cache/map_{lat}_{lon}_{zoom}.png"
    
    if os.path.exists(filename):
        return filename
        
    offline_source = "offline_campus.png"
    
    if os.path.exists(offline_source):
        img = cv2.imread(offline_source)
        h, w = img.shape[:2]
        cy, cx = h // 2, w // 2
        
        y1 = max(0, cy - 300)
        y2 = min(h, cy + 300)
        x1 = max(0, cx - 300)
        x2 = min(w, cx + 300)
        
        crop = img[y1:y2, x1:x2]
        
        if crop.shape[:2] != (600, 600):
            crop = cv2.resize(crop, (600, 600))
            
        cv2.imwrite(filename, crop)
        return filename
    else:
        blank_image = np.zeros((600, 600, 3), np.uint8)
        blank_image[:] = (30, 30, 30) 
        cv2.imwrite(filename, blank_image)
        return filename

if __name__ == "__main__":
    DRONE_LAT = 18.4575
    DRONE_LON = 73.8508
    ZOOM = 18
    
    img_path = get_map_image(DRONE_LAT, DRONE_LON, ZOOM)
    print(img_path)