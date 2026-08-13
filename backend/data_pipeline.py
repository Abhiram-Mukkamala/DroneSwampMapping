import numpy as np
from schemas.drone_state import DroneState

class PipelineNode:
    def __init__(self, grid_width, grid_height, cell_size):
        self.grid = np.zeros((grid_height, grid_width), dtype=int)
        self.cell_size = cell_size
        self.telemetry_stream = {}

    def process_yolo_detections(self, detections):
        self.grid.fill(0)
        
        for det in detections:
            if det.get("class") == "obstacle":
                x, y, w, h = det["bbox"]
                gx = int(x // self.cell_size)
                gy = int(y // self.cell_size)
                gw = max(1, int(w // self.cell_size))
                gh = max(1, int(h // self.cell_size))
                self.grid[gy:gy+gh, gx:gx+gw] = 1
                
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