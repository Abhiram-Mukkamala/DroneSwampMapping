from ultralytics import YOLO

def detect_targets(image_path):
    model = YOLO('yolov8n.pt')
    results = model(image_path, conf=0.1)
    
    targets = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            targets.append((center_x, center_y))
            
    if not targets:
        targets.append((300.0, 300.0))
            
    return targets

if __name__ == "__main__":
    IMAGE_PATH = "map_cache/map_18.4575_73.8508_18.png"
    found_targets = detect_targets(IMAGE_PATH)
    print(found_targets)