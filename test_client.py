import asyncio
import websockets
import json

async def test_yolo_feed():
    uri = "ws://localhost:8765"
    
    print("Attempting to connect to Pipeline Mainframe...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # The exact JSON contract you told the YOLO lead to use
            mock_payload = {
                "type": "yolo_detections",
                "payload": [
                    {"class": "obstacle", "bbox": [120, 45, 30, 30], "confidence": 0.91},
                    {"class": "drone", "bbox": [200, 150, 40, 40], "confidence": 0.88}
                ]
            }
            
            print("Sending mock YOLO detections...")
            await websocket.send(json.dumps(mock_payload))
            
            # Listen for your pipeline's response (The Hazard Map)
            response = await websocket.recv()
            print("\n📥 Received from Pipeline:")
            
            # Pretty-print the JSON response so it's easy to read
            parsed_response = json.loads(response)
            print(json.dumps(parsed_response, indent=2))
            
    except ConnectionRefusedError:
        print("❌ Connection failed. Make sure data_pipeline.py is running.")

if __name__ == "__main__":
    asyncio.run(test_yolo_feed())