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
    def __init__(self, img_width: int = 640, img_height: int = 480, fov: float = 60.0):
        self.width = img_width
        self.height = img_height
        self.fov = fov
        self.proj_matrix = p.computeProjectionMatrixFOV(
            fov=self.fov, aspect=img_width / img_height, nearVal=0.1, farVal=1000.0
        )

    def update_camera_view(self, drone_pos=None, heading_angle: float = 0.0):
        """Generates the camera feed matching the exact PyBullet simulator main view."""
        view_matrix = None
        proj_matrix = self.proj_matrix

        # First try to grab the exact camera matrix from the live PyBullet GUI window
        try:
            cam_info = p.getDebugVisualizerCamera()
            if cam_info is not None and len(cam_info) >= 4:
                view_matrix = cam_info[2]
                proj_matrix = cam_info[3]
        except Exception:
            pass

        # Fallback to computing view matrix following the red drone
        if view_matrix is None and drone_pos is not None:
            view_matrix = p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=drone_pos,
                distance=14.0,
                yaw=math.degrees(heading_angle) - 90.0,
                pitch=-25.0,
                roll=0,
                upAxisIndex=2
            )

        try:
            return p.getCameraImage(
                width=self.width,
                height=self.height,
                viewMatrix=view_matrix,
                projectionMatrix=proj_matrix,
                renderer=p.ER_BULLET_HARDWARE_OPENGL,
            )
        except Exception:
            return p.getCameraImage(
                width=self.width,
                height=self.height,
                viewMatrix=view_matrix,
                projectionMatrix=proj_matrix,
                renderer=p.ER_TINY_RENDERER,
            )