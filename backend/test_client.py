import asyncio
import websockets
import json

async def run_test():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        mock_payload = {
            "type": "yolo_detections",
            "payload": [{"class": "obstacle", "bbox": [10.0, 10.0, 20.0, 20.0], "confidence": 0.99}]
        }
        print("📡 Beaming YOLO Payload to Mainframe...")
        await websocket.send(json.dumps(mock_payload))
        response = await websocket.recv()
        print(f"✅ Mainframe replied with Hazard Map (Truncated): {response[:100]}...")

if __name__ == "__main__":
    asyncio.run(run_test())