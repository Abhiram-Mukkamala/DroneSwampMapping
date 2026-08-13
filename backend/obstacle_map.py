import numpy as np

class ObstacleMap:
    def __init__(self):
        self.static_aabbs = []
        self.dynamic_grid = None
        self.cell_size = 1.0
        self.moat_repulsion = 150.0

    def update_dynamic_grid(self, grid, cell_size):
        self.dynamic_grid = np.array(grid)
        self.cell_size = cell_size

    def calculate_repulsion(self, drone_pos):
        force = np.zeros(3)
        if self.dynamic_grid is not None:
            gx = int(drone_pos[0] // self.cell_size)
            gy = int(drone_pos[1] // self.cell_size)
            
            if 0 <= gy < self.dynamic_grid.shape[0] and 0 <= gx < self.dynamic_grid.shape[1]:
                if self.dynamic_grid[gy, gx] == 1:
                    force[0] -= self.moat_repulsion
                    force[1] -= self.moat_repulsion
                    
                return force