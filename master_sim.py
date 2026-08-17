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
    Physical Rigid-Body Drone operating in high open airspace with 26-direction 
    spherical raycast obstacle avoidance.
    """
    def __init__(self, drone_id: int, start_pos: list[float], offset_angle: float, orbit_radius: float = 5.0):
        self.drone_id = drone_id
        self.offset_angle = offset_angle
        self.orbit_radius = orbit_radius
        self.ray_dirs = self._generate_26_spherical_rays()

        # Rigid body physical setup
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
        # Current true physical state from engine
        pos_tuple, _ = p.getBasePositionAndOrientation(self.drone_id)
        current_pos = np.array(pos_tuple, dtype=np.float64)

        lin_vel, _ = p.getBaseVelocity(self.drone_id)
        current_vel = np.array(lin_vel, dtype=np.float64)

        # 1. Target Orbit Formation Slot
        angle = self.offset_angle + sim_time * 0.35
        desired_slot = np.array([
            target_pos[0] + self.orbit_radius * math.cos(angle),
            target_pos[1] + self.orbit_radius * math.sin(angle),
            target_pos[2] + 0.5 * math.sin(sim_time + self.offset_angle),
        ])

        target_diff = desired_slot - current_pos
        dist_to_target = np.linalg.norm(target_diff)
        attract_dir = target_diff / (dist_to_target + 1e-5)
        f_attract = attract_dir * min(dist_to_target * 8.0, 20.0)

        # 2. 26-Ray 3D Obstacle Avoidance
        sensor_dist = 8.0
        ray_starts = [current_pos.tolist()] * len(self.ray_dirs)
        ray_ends = [(current_pos + r * sensor_dist).tolist() for r in self.ray_dirs]

        ray_results = p.rayTestBatch(ray_starts, ray_ends)
        f_obstacle = np.zeros(3, dtype=np.float64)

        for i, result in enumerate(ray_results):
            hit_uid = result[0]
            hit_fraction = result[2]
            hit_normal = np.array(result[4], dtype=np.float64)

            if hit_uid >= 0 and hit_uid != self.drone_id:
                hit_dist = hit_fraction * sensor_dist
                if 0.01 < hit_dist < sensor_dist:
                    repulsion_mag = 70.0 * ((1.0 / hit_dist) - (1.0 / sensor_dist)) ** 2
                    repulse_dir = hit_normal if np.linalg.norm(hit_normal) > 0.1 else -self.ray_dirs[i]
                    repulse_dir = repulse_dir / (np.linalg.norm(repulse_dir) + 1e-5)
                    f_obstacle += repulse_dir * repulsion_mag

        # 3. Swarm Anti-Collision Force
        f_swarm = np.zeros(3, dtype=np.float64)
        for other_pos in all_follower_positions:
            diff = current_pos - other_pos
            d = np.linalg.norm(diff)
            if 0.01 < d < 2.8:
                f_swarm += (diff / d) * (2.8 - d) * 16.0

        # 4. Integrate Forces and apply velocity
        kd = 2.8
        total_force = f_attract + f_obstacle + f_swarm - kd * current_vel
        new_vel = current_vel + total_force * dt

        max_speed = 8.0
        speed = np.linalg.norm(new_vel)
        if speed > max_speed:
            new_vel = (new_vel / speed) * max_speed

        p.resetBaseVelocity(self.drone_id, linearVelocity=new_vel.tolist(), angularVelocity=[0, 0, 0])

    def get_position(self) -> np.ndarray:
        pos_tuple, _ = p.getBasePositionAndOrientation(self.drone_id)
        return np.array(pos_tuple, dtype=np.float64)

    def get_heading_angle(self) -> float:
        lin_vel, _ = p.getBaseVelocity(self.drone_id)
        if math.hypot(lin_vel[0], lin_vel[1]) > 0.1:
            return math.atan2(lin_vel[1], lin_vel[0])
        return self.offset_angle


import math
import pybullet as p

def create_drone(
    position: list[float], 
    color: list[float], 
    radius: float = 1.0,         
    obj_path: str = "drone.obj", 
    scale: float = 0.7,      #Size    
    mass: float = 0.8,
    mesh_rotation_euler: list[float] = [math.radians(90), 0, 0] # Model axis fix
) -> int:
    """
    Spawns a scaled-up drone with a baked-in visual mesh orientation offset
    so flight controls and yaw turning don't flip the model standing up.
    """
    # 1. Convert Euler angles to quaternion for the visual frame offset
    mesh_orient = p.getQuaternionFromEuler(mesh_rotation_euler)

    # 2. Visual mesh (Rotated permanently relative to the physics body)
    vis_id = p.createVisualShape(
        shapeType=p.GEOM_MESH,
        fileName=obj_path,
        meshScale=[scale, scale, scale],
        rgbaColor=color,
        visualFrameOrientation=mesh_orient 
    )
    
    # 3. Bounding sphere collision shape
    col_id = p.createCollisionShape(
        shapeType=p.GEOM_SPHERE,
        radius=radius
    )
    
    # 4. Create the physical body
    return p.createMultiBody(
        baseMass=mass,
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=position
    )


def main():
    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

    p.loadURDF("plane.urdf")

    # Generate 3D City Layout
    city_layout.build_city()

    # HIGH SKY SPAWN (Z = 35.0m) to clear all building rooftops
    HIGH_ALTITUDE = 35.0

    # 1. Spawn Red Pilot Drone in high open sky
    red_pos = np.array([0.0, 0.0, HIGH_ALTITUDE], dtype=np.float64)
    red_yaw = 0.0
    red_drone_id = create_drone(red_pos.tolist(), color=[0.9, 0.1, 0.1, 1.0], radius=0.5, mass=0.0)

    # 2. Spawn Blue Swarm Drones orbiting at high altitude
    num_followers = 6
    followers = []
    orbit_radius = 5.0

    for k in range(num_followers):
        angle = (2.0 * math.pi / num_followers) * k
        start_p = [
            red_pos[0] + orbit_radius * math.cos(angle),
            red_pos[1] + orbit_radius * math.sin(angle),
            HIGH_ALTITUDE
        ]
        b_id = create_drone(start_p, color=[0.1, 0.4, 0.9, 1.0], radius=0.4, mass=0.8)
        followers.append(FollowerDrone(b_id, start_p, angle, orbit_radius=orbit_radius))

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
                # e[0] == 1 indicates a MOUSE_MOVE_EVENT
                if e[0] == 1:
                    curr_x = e[1]
                    if last_mouse_x is not None:
                        dx = curr_x - last_mouse_x
                        # Mouse drag/move turns yaw heading
                        red_yaw -= dx * 0.003
                    last_mouse_x = curr_x

            # 2. Pilot Keyboard Controls for Red Drone
            keys = p.getKeyboardEvents()
            move_speed = 0.3

            KEY_W, KEY_S = ord('w'), ord('s')
            KEY_A, KEY_D = ord('a'), ord('d')
            KEY_SPACE = ord(' ')
            KEY_LSHIFT = getattr(p, 'B3G_SHIFT', 65306)

            # Forward / Backward along current Yaw vector
            if KEY_W in keys and keys[KEY_W] & p.KEY_IS_DOWN:
                red_pos[0] += move_speed * math.cos(red_yaw)
                red_pos[1] += move_speed * math.sin(red_yaw)
            if KEY_S in keys and keys[KEY_S] & p.KEY_IS_DOWN:
                red_pos[0] -= move_speed * math.cos(red_yaw)
                red_pos[1] -= move_speed * math.sin(red_yaw)

            # Strafe Left / Right perpendicular to Yaw vector
            if KEY_A in keys and keys[KEY_A] & p.KEY_IS_DOWN:
                red_pos[0] -= move_speed * math.sin(red_yaw)
                red_pos[1] += move_speed * math.cos(red_yaw)
            if KEY_D in keys and keys[KEY_D] & p.KEY_IS_DOWN:
                red_pos[0] += move_speed * math.sin(red_yaw)
                red_pos[1] -= move_speed * math.cos(red_yaw)

            # Ascend / Descend
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

            # 4. Pathfinding Step for Swarm
            all_follower_positions = [f.get_position() for f in followers]
            for follower in followers:
                follower.update_pathfinding(red_pos, sim_time, dt, all_follower_positions)

            # 5. Onboard Camera Feed rendering from Lead Blue Drone
            if tick_count % 3 == 0:
                lead_blue = followers[0]
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