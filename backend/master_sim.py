"""
master_sim.py
-------------
Controls updated to FPS-style drone navigation:
  - W / S          : Fly Forward / Backward
  - A / D          : Strafe Left / Right
  - Mouse Movement : Yaw Turning (Look Left / Right)
  - Space / LShift : Ascend / Descend Into City Streets
"""

import time
import math
import numpy as np

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    raise ImportError("PyBullet required. Run 'pip install pybullet'.")

import city_layout
from vision_engine import DroneVisionEngine


class FollowerDrone:
    """
    Physical Rigid-Body Drone operating in high open airspace.
    """
    def __init__(self, drone_id: int, start_pos: list[float], offset_angle: float, orbit_radius: float = 5.0):
        self.drone_id = drone_id
        self.offset_angle = offset_angle
        self.orbit_radius = orbit_radius
        self.last_dist_to_target = 0.0
        self.ray_dirs = self._generate_26_spherical_rays()

        # NOTE: Rigid body collision shapes are kept for PyBullet raycasting/AABB queries,
        # but dynamics settings (mass, friction, damping) no longer drive motion directly.
        # Motion is authoritatively computed by VectorSwarm and applied kinematically
        # via resetBasePositionAndOrientation and resetBaseVelocity each tick.
        p.changeDynamics(
            self.drone_id, -1,
            mass=0.8,              # Dynamic rigid body
            restitution=0.0,       # Prevents springy bouncing
            lateralFriction=1.0,   # High sliding friction
            linearDamping=0.6,
            angularDamping=0.9
        )

    def _generate_26_spherical_rays(self) -> list[np.ndarray]:
        """Generates 26 uniform 3D directional vectors covering a full sphere."""
        dirs = []
        for x in [-1, 0, 1]:
            for y in [-1, 0, 1]:
                for z in [-1, 0, 1]:
                    if x == 0 and y == 0 and z == 0:
                        continue
                    vec = np.array([x, y, z], dtype=np.float64)
                    dirs.append(vec / np.linalg.norm(vec))
        return dirs

    def update_pathfinding(self, target_pos: np.ndarray, sim_time: float, dt: float, all_follower_positions: list[np.ndarray]):
        """
        Legacy inline pathfinding stub. Swarm physics is now authoritatively
        stepped via SwarmController / VectorSwarm.
        """
        pass

    def get_position(self) -> np.ndarray:
        pos_tuple, _ = p.getBasePositionAndOrientation(self.drone_id)
        return np.array(pos_tuple, dtype=np.float64)

    def get_heading_angle(self) -> float:
        lin_vel, _ = p.getBaseVelocity(self.drone_id)
        if math.hypot(lin_vel[0], lin_vel[1]) > 0.1:
            return math.atan2(lin_vel[1], lin_vel[0])
        return self.offset_angle


def create_drone(position: list[float], color: list[float], radius: float = 0.45, mass: float = 0.8) -> int:
    col_id = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)
    vis_id = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=color)
    return p.createMultiBody(
        baseMass=mass,
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=position
    )


def main():
    from swarm_controller import SwarmController
    import obstacle_map

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    p.loadURDF("plane.urdf")

    # Generate 3D City Layout and extract obstacle bounding boxes
    city_body_ids = city_layout.build_city()
    obstacle_boxes = obstacle_map.build_obstacle_aabbs(city_body_ids)

    # Initialize SwarmController with obstacle AABBs
    controller = SwarmController(obstacle_boxes)

    # HIGH SKY SPAWN (Z = 35.0m) to clear all building rooftops
    HIGH_ALTITUDE = 35.0

    # 1. Spawn Red Pilot Drone in high open sky
    red_pos = np.array([0.0, 0.0, HIGH_ALTITUDE], dtype=np.float64)
    red_yaw = 0.0
    red_drone_id = create_drone(red_pos.tolist(), color=[0.9, 0.1, 0.1, 1.0], radius=0.5, mass=0.0)

    # 2. Spawn Blue Swarm Drones orbiting at high altitude
    num_followers = 6
    orbit_radius = 5.0

    for k in range(num_followers):
        angle = (2.0 * math.pi / num_followers) * k
        start_p = [
            red_pos[0] + orbit_radius * math.cos(angle),
            red_pos[1] + orbit_radius * math.sin(angle),
            HIGH_ALTITUDE
        ]
        b_id = create_drone(start_p, color=[0.1, 0.4, 0.9, 1.0], radius=0.4, mass=0.8)
        follower = FollowerDrone(b_id, start_p, angle, orbit_radius=orbit_radius)
        controller.add_follower(follower, start_p)

    # Onboard Vision Camera for Lead Blue Drone
    blue_vision_engine = DroneVisionEngine(img_width=320, img_height=240, fov=75.0)

    sim_time = 0.0
    dt = 1.0 / 60.0
    tick_count = 0
    last_mouse_x = None

    print("\n--- FPS FLIGHT CONTROLS ---")
    print("  W / S          : Fly Forward / Backward")
    print("  A / D          : Strafe Left / Right")
    print("  Mouse Move     : Change Yaw Heading")
    print("  Space / LShift : Ascend / Descend Into City Streets\n")

    try:
        while True:
            sim_time += dt
            tick_count += 1

            # 1. Mouse Tracking for Yaw Turning
            mouse_events = p.getMouseEvents()
            for e in mouse_events:
                if e[0] == 1:
                    curr_x = e[1]
                    if last_mouse_x is not None:
                        dx = curr_x - last_mouse_x
                        red_yaw -= dx * 0.003
                    last_mouse_x = curr_x

            # 2. Pilot Keyboard Controls for Red Drone
            keys = p.getKeyboardEvents()
            move_speed = 0.3

            KEY_W, KEY_S = ord('w'), ord('s')
            KEY_A, KEY_D = ord('a'), ord('d')
            KEY_SPACE = ord(' ')
            KEY_LSHIFT = getattr(p, 'B3G_SHIFT', 65306)

            if KEY_W in keys and keys[KEY_W] & p.KEY_IS_DOWN:
                red_pos[0] += move_speed * math.cos(red_yaw)
                red_pos[1] += move_speed * math.sin(red_yaw)
            if KEY_S in keys and keys[KEY_S] & p.KEY_IS_DOWN:
                red_pos[0] -= move_speed * math.cos(red_yaw)
                red_pos[1] -= move_speed * math.sin(red_yaw)

            if KEY_A in keys and keys[KEY_A] & p.KEY_IS_DOWN:
                red_pos[0] -= move_speed * math.sin(red_yaw)
                red_pos[1] += move_speed * math.cos(red_yaw)
            if KEY_D in keys and keys[KEY_D] & p.KEY_IS_DOWN:
                red_pos[0] += move_speed * math.sin(red_yaw)
                red_pos[1] -= move_speed * math.cos(red_yaw)

            if KEY_SPACE in keys and keys[KEY_SPACE] & p.KEY_IS_DOWN:
                red_pos[2] += move_speed * 0.5
            if KEY_LSHIFT in keys and keys[KEY_LSHIFT] & p.KEY_IS_DOWN:
                red_pos[2] = max(1.5, red_pos[2] - move_speed * 0.5)

            red_quat = p.getQuaternionFromEuler([0, 0, red_yaw])
            p.resetBasePositionAndOrientation(red_drone_id, red_pos.tolist(), red_quat)

            # 3. Main Viewport Camera following Red Drone heading
            p.resetDebugVisualizerCamera(
                cameraDistance=14.0,
                cameraYaw=math.degrees(red_yaw) - 90.0,
                cameraPitch=-25.0,
                cameraTargetPosition=red_pos.tolist(),
            )

            # 4. Pathfinding Step for Swarm via SwarmController & VectorSwarm
            controller.step(red_pos, sim_time, dt)

            # 5. Onboard Camera Feed rendering from Lead Blue Drone
            if tick_count % 3 == 0 and len(controller.followers) > 0:
                lead_blue = controller.followers[0]
                blue_vision_engine.update_camera_view(
                    drone_pos=lead_blue.get_position(),
                    heading_angle=lead_blue.get_heading_angle()
                )

            p.stepSimulation()
            time.sleep(dt)

    except KeyboardInterrupt:
        print("Simulation terminated.")
    finally:
        p.disconnect()


if __name__ == "__main__":
    main()