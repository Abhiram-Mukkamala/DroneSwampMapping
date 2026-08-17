import numpy as np
from schemas.drone_state import DroneState

class PipelineNode:
    def __init__(self, grid_width, grid_height, cell_size):
        self.grid = np.zeros((grid_height, grid_width), dtype=int)
        self.cell_size = cell_size
        self.telemetry_stream = {}

    def process_yolo_detections(self, detections):
        self.grid.fill(0)
        max_h, max_w = self.grid.shape
        
        for det in detections:
            if det.get("class") == "obstacle":
                x, y, w, h = det["bbox"]
                
                # Calculate raw grid indices
                gx = int(x // self.cell_size)
                gy = int(y // self.cell_size)
                gw = max(1, int(w // self.cell_size))
                gh = max(1, int(h // self.cell_size))
                
                # Clamp boundaries to grid dimensions to prevent IndexError
                gy_start = max(0, min(gy, max_h))
                gx_start = max(0, min(gx, max_w))
                gy_end = max(0, min(gy + gh, max_h))
                gx_end = max(0, min(gx + gw, max_w))
                
                self.grid[gy_start:gy_end, gx_start:gx_end] = 1
                
        return self.broadcast_hazard_map()

    def broadcast_hazard_map(self):
        return {
            "grid": self.grid.tolist(),
            "cellSize": self.cell_size
        }

    def process_drone_telemetry(self, payload):
        state = DroneState(**payload)
        self.telemetry_stream[state.id] = state.dict()
        return self.telemetry_stream