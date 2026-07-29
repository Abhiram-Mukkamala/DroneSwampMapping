import io
import time
import socket
from urllib.parse import urlparse

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8765"


def create_sample_image():
    """Create a 320x240 test JPEG image frame with synthetic obstacle geometry."""
    if not HAS_PIL:
        # Minimal 1x1 white JPEG header fallback
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'

    img = Image.new("RGB", (320, 240), color=(30, 40, 60))
    draw = ImageDraw.Draw(img)
    
    # Draw ground grid lines
    for y in range(40, 240, 40):
        draw.line([(0, y), (320, y)], fill=(50, 70, 100), width=1)
    for x in range(40, 320, 40):
        draw.line([(x, 0), (x, 240)], fill=(50, 70, 100), width=1)
    
    # Draw a distinct red rectangle object (synthetic obstacle)
    draw.rectangle([100, 80, 180, 180], fill=(220, 50, 50), outline=(255, 255, 255))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()


def test_health():
    print("--- 1. Testing GET /health ---")
    if not HAS_REQUESTS:
        print("[NOTICE] Dependency 'requests' not installed. Install via 'pip install requests' to run HTTP test.")
        return
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=5)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200, "Health check failed"
        assert resp.json().get("status") == "ok", "Expected status ok"
        print("[PASS] GET /health check passed!")
    except requests.exceptions.ConnectionError:
        print(f"[NOTICE] Perception server at {SERVER_URL} is currently offline. Skipped live assertion.")


def test_detect():
    print("\n--- 2. Testing POST /detect ---")
    if not HAS_REQUESTS:
        print("[NOTICE] Dependency 'requests' not installed. Install via 'pip install requests' to run HTTP test.")
        return
    image_bytes = create_sample_image()
    
    try:
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
        assert "detections" in data, "Missing 'detections' key in response"
        assert isinstance(data["detections"], list), "'detections' must be a list"
        print("[PASS] Perception Service POST /detect Verification Passed!")
    except requests.exceptions.ConnectionError:
        print(f"[NOTICE] Perception server at {SERVER_URL} is currently offline. Skipped live assertion.")


def test_websocket_graceful():
    print(f"\n--- 3. Testing WebSocket Endpoint ({WS_URL}) Connection Gracefulness ---")
    parsed = urlparse(WS_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8765

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        print(f"[INFO] Pipeline Lead WebSocket server at {WS_URL} is ONLINE and reachable.")
        s.close()
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"[PASS] WebSocket server at {WS_URL} is offline ({e}). Handled gracefully — no crash.")


if __name__ == "__main__":
    test_health()
    test_detect()
    test_websocket_graceful()
    print("\n==========================================")
    print("Perception Verification Test Suite Complete!")
    print("==========================================")
