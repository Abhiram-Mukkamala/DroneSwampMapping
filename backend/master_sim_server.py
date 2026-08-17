import asyncio
import websockets
import json
from data_pipeline import PipelineNode
from obstacle_map import ObstacleMap

pipeline = PipelineNode(grid_width=100, grid_height=100, cell_size=5)
obs_map = ObstacleMap()

async def master_router(websocket):
    async for message in websocket:
        packet = json.loads(message)
        
        if packet.get("type") == "yolo_detections":
            hazard_map = pipeline.process_yolo_detections(packet["payload"])
            obs_map.update_dynamic_grid(hazard_map["grid"], hazard_map["cellSize"])
            obs_map.calculate_repulsion([12.0, 12.0, 0.0])
            await websocket.send(json.dumps({"type": "hazard_map", "payload": hazard_map}))
            
        elif packet.get("type") == "telemetry":
            global_state = pipeline.process_drone_telemetry(packet["payload"])
            await websocket.send(json.dumps({"type": "global_telemetry", "payload": global_state}))

async def main():
    async with websockets.serve(master_router, "localhost", 8765):
        print("🚀 Master Simulation Mainframe LIVE on ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())