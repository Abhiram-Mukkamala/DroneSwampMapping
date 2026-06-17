import cv2
import numpy as np

def detect_targets(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return [(300.0, 300.0)]
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    targets = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 50:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                targets.append((float(cx), float(cy)))
                
    if not targets:
        targets.append((300.0, 300.0))
        
    return targets

if __name__ == "__main__":
    IMAGE_PATH = "map_cache/map_18.4575_73.8508_18.png"
    found_targets = detect_targets(IMAGE_PATH)
    print(found_targets)