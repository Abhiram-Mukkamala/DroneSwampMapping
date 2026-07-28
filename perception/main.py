import io
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from ultralytics import YOLO

app = FastAPI(title="DroneSwarm Perception API", version="1.0.0")

# Enable CORS for browser access from http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load stock YOLOv8n ONCE at startup
print("Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")
print("YOLOv8n model loaded successfully.")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "perception",
        "model": "yolov8n.pt",
        "timestamp": time.time()
    }

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    """
    Accepts a 320x240 JPEG/PNG image frame (via multipart/form-data with field name 'file'),
    runs YOLOv8 object detection, and returns bounding box detections.
    
    Response contract:
    [
      {
        "class": "person",
        "bbox": [x_min, y_min, width, height],
        "confidence": 0.87
      }
    ]
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded must be an image")

    start_time = time.perf_counter()
    image_bytes = await file.read()

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

    # Run inference on PIL Image
    results = model(image, verbose=False)

    detections = []
    if len(results) > 0:
        result = results[0]
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                # xywh format: [center_x, center_y, width, height]
                # convert to [x_min, y_min, width, height]
                xyxy = box.xyxy[0].cpu().numpy().tolist() # [x1, y1, x2, y2]
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = model.names.get(cls_id, f"class_{cls_id}")

                x1, y1, x2, y2 = xyxy
                w = x2 - x1
                h = y2 - y1

                detections.append({
                    "class": cls_name,
                    "bbox": [round(x1, 2), round(y1, 2), round(w, 2), round(h, 2)],
                    "confidence": round(conf, 4)
                })

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "detections": detections,
        "inference_time_ms": elapsed_ms,
        "image_size": [image.width, image.height]
    }
