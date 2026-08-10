"""
vision_engine.py
----------------
Renders synthetic camera feeds (RGB, Depth, Segmentation) 
mounted on a Blue Swarm Drone looking forward.
"""

import math
import numpy as np

try:
    import pybullet as p
except ImportError:
    p = None


class DroneVisionEngine:
    def __init__(self, img_width: int = 320, img_height: int = 240, fov: float = 75.0):
        self.width = img_width
        self.height = img_height
        self.fov = fov
        self.proj_matrix = p.computeProjectionMatrixFOV(
            fov=self.fov, aspect=img_width / img_height, nearVal=0.1, farVal=100.0
        )

    def update_camera_view(self, drone_pos: np.ndarray, heading_angle: float):
        """Attaches synthetic camera lens to the front of a specified drone."""
        dx, dy, dz = drone_pos[0], drone_pos[1], drone_pos[2]

        # Offset camera slightly forward (0.4m) from sphere center to avoid mesh clipping
        cam_pos = [
            dx + 0.4 * math.cos(heading_angle),
            dy + 0.4 * math.sin(heading_angle),
            dz + 0.1,
        ]
        target_pos = [
            dx + 10.0 * math.cos(heading_angle),
            dy + 10.0 * math.sin(heading_angle),
            dz,
        ]

        view_matrix = p.computeViewMatrix(
            cameraEyePosition=cam_pos,
            cameraTargetPosition=target_pos,
            cameraUpVector=[0, 0, 1]
        )

        return p.getCameraImage(
            width=self.width,
            height=self.height,
            viewMatrix=view_matrix,
            projectionMatrix=self.proj_matrix,
            renderer=p.ER_TINY_RENDERER,
        )