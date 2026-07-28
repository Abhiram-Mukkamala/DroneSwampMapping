import io
import time
import requests
from PIL import Image, ImageDraw

SERVER_URL = "http://localhost:8000"

def create_sample_image():
    """Create a 320x240 test JPEG image with geometric shapes / mock objects."""
    img = Image.new("RGB", (320, 240), color=(30, 40, 60))
    draw = ImageDraw.Draw(img)
    # Draw ground grid lines
    for y in range(40, 240, 40):
        draw.line([(0, y), (320, y)], fill=(50, 70, 100), width=1)
    for x in range(40, 320, 40):
        draw.line([(x, 0), (x, 240)], fill=(50, 70, 100), width=1)
    
    # Draw a distinct red rectangle object
    draw.rectangle([100, 80, 180, 180], fill=(220, 50, 50), outline=(255, 255, 255))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

def test_health():
    print("--- 1. Testing GET /health ---")
    resp = requests.get(f"{SERVER_URL}/health", timeout=5)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.json()}")
    assert resp.status_code == 200, "Health check failed"

def test_detect():
    print("\n--- 2. Testing POST /detect ---")
    image_bytes = create_sample_image()
    
    start_time = time.perf_counter()
    files = {'file': ('test_frame.jpg', image_bytes, 'image/jpeg')}
    resp = requests.post(f"{SERVER_URL}/detect", files=files, timeout=10)
    total_roundtrip_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    print(f"Status Code: {resp.status_code}")
    print(f"Total HTTP Roundtrip Time: {total_roundtrip_ms} ms")
    
    data = resp.json()
    print("Response Payload:")
    print(data)
    
    assert resp.status_code == 200, "Detect endpoint failed"
    assert "detections" in data, "Missing detections key"
    print("\n[PASS] Perception Service Endpoint Verification Passed!")

if __name__ == "__main__":
    try:
        test_health()
        test_detect()
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
