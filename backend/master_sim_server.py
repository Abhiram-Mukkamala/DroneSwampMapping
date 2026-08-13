import asyncio
import websockets
import json
import math
import numpy as np
import time
import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    raise ImportError("PyBullet required. Run 'pip install pybullet'.")

from master_sim import FollowerDrone, create_drone
import city_layout
import obstacle_map
from schemas.drone_state import DroneState
from swarm_controller import SwarmController

# Global state
simulation_running = False
swarm_controller = SwarmController()
red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)
red_yaw = 0.0
red_drone_id = None
tick_count = 0
clients = set()
latest_jpeg_frame = None
last_frame_time = 0.0
frame_lock = threading.Lock()

# Stuck detection: track per-drone low-velocity tick counts
# NOTE: This concept mirrors (conceptually, not numerically) the stuck-detection logic in
# perfect_swarm.py / VectorSwarm.js. In those engines, a drone is flagged stuck when
# speed < threshold AND dist_to_target > threshold. Here, constants use PyBullet's real-world
# metric scale (metres & m/s) rather than unscaled tuning steps, and incorporate a tick-based
# debounce (_STUCK_TICK_THRESHOLD) to prevent single-frame velocity noise from flipping status.
_stuck_tick_counts: dict[int, int] = {}
_STUCK_VELOCITY_THRESHOLD = 0.15   # m/s — below this counts as "low velocity / not moving"
_STUCK_DISTANCE_THRESHOLD = 1.5    # metres — distance to target slot must exceed this.
                                   # Followers hovering near their target slot in PyBullet metric
                                   # scale stay within ~0.5m-1.0m, so >1.5m indicates trapped by an obstacle.
_STUCK_TICK_THRESHOLD = 60         # ~1 second at 60Hz before marking STUCK

from vision_engine import DroneVisionEngine
vision_engine = DroneVisionEngine(img_width=640, img_height=480, fov=90.0)


# ── Simple threaded MJPEG HTTP server (no aiohttp, no chunked encoding) ──

class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            try:
                while True:
                    with frame_lock:
                        frame = latest_jpeg_frame
                    if frame is not None:
                        self.wfile.write(b'--frame\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n')
                        self.wfile.write(f'Content-Length: {len(frame)}\r\n'.encode())
                        self.wfile.write(b'\r\n')
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                    time.sleep(1/24.0)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress noisy HTTP logs


def start_mjpeg_server():
    server = HTTPServer(('0.0.0.0', 5000), MJPEGHandler)
    print("Video stream running on http://localhost:5000/video_feed")
    server.serve_forever()


# ── WebSocket handler ──

async def handler(websocket):
    global simulation_running, red_pos, red_yaw, red_drone_id, swarm_controller
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "START_SIMULATION":
                simulation_running = True
            elif msg_type == "PAUSE_SIMULATION" or msg_type == "EMERGENCY_STOP":
                simulation_running = False
            elif msg_type == "ADD_DRONES":
                count = payload.get("count", 1)
                for _ in range(count):
                    angle = np.random.uniform(0, 2 * math.pi)
                    orbit_radius = 5.0
                    start_p = [
                        red_pos[0] + orbit_radius * math.cos(angle),
                        red_pos[1] + orbit_radius * math.sin(angle),
                        35.0
                    ]
                    b_id = create_drone(start_p, color=[0.1, 0.4, 0.9, 1.0], radius=0.4, mass=0.8)
                    f = FollowerDrone(b_id, start_p, angle, orbit_radius=orbit_radius)
                    swarm_controller.add_follower(f, start_p)
            elif msg_type == "REMOVE_DRONE":
                drone_index = payload.get("droneId")
                if drone_index is not None and 0 <= drone_index < len(swarm_controller.followers):
                    removed = swarm_controller.remove_follower(drone_index)
                    p.removeBody(removed.drone_id)
                    print(f"Removed drone at sim index {drone_index}, {len(swarm_controller.followers)} remaining")
            elif msg_type == "SET_FORMATION":
                mode = payload.get("mode", "orbit")
                params = {k: v for k, v in payload.items() if k != "mode"}
                try:
                    swarm_controller.set_formation(mode, **params)
                    print(f"Formation set to {mode!r} with params {params}")
                except ValueError as e:
                    print(f"SET_FORMATION error: {e}")
            elif msg_type == "RESET_SIMULATION":
                removed_list = swarm_controller.clear()
                for f in removed_list:
                    p.removeBody(f.drone_id)
                print("Simulation reset: all follower drones removed")
    finally:
        clients.remove(websocket)


# ── Main simulation loop ──

async def simulation_loop():
    global simulation_running, red_pos, red_yaw, red_drone_id, swarm_controller
    global tick_count, latest_jpeg_frame, last_frame_time

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.loadURDF("plane.urdf")

    city_body_ids = city_layout.build_city()
    obstacle_boxes = obstacle_map.build_obstacle_aabbs(city_body_ids)
    swarm_controller.set_obstacle_boxes(obstacle_boxes)

    red_drone_id = create_drone(red_pos.tolist(), color=[0.9, 0.1, 0.1, 1.0], radius=0.5, mass=0.0)

    sim_time = 0.0
    dt = 1.0 / 60.0
    last_mouse_x = None

    while True:
        if simulation_running:
            sim_time += dt
            tick_count += 1

            mouse_events = p.getMouseEvents()
            for e in mouse_events:
                if e[0] == 1:
                    curr_x = e[1]
                    if last_mouse_x is not None:
                        red_yaw -= (curr_x - last_mouse_x) * 0.003
                    last_mouse_x = curr_x

            keys = p.getKeyboardEvents()
            move_speed = 0.3
            KEY_W, KEY_S, KEY_A, KEY_D = ord('w'), ord('s'), ord('a'), ord('d')
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

            p.resetBasePositionAndOrientation(red_drone_id, red_pos.tolist(), p.getQuaternionFromEuler([0, 0, red_yaw]))
            p.resetDebugVisualizerCamera(14.0, math.degrees(red_yaw) - 90.0, -25.0, red_pos.tolist())

            swarm_controller.step(red_pos, sim_time, dt)

            p.stepSimulation()

        # Broadcast telemetry (always, even when paused)
        if clients:
            states = []
            followers_list = swarm_controller.followers
            for i, f in enumerate(followers_list):
                pos = f.get_position()
                heading_rad = f.get_heading_angle()
                lin_vel, _ = p.getBaseVelocity(f.drone_id)

                # Derive status from actual drone state
                speed = math.hypot(lin_vel[0], lin_vel[1], lin_vel[2])
                dist_to_target = getattr(f, 'last_dist_to_target', 0.0)

                if not simulation_running:
                    status = "IDLE"
                    _stuck_tick_counts[i] = 0
                elif speed < _STUCK_VELOCITY_THRESHOLD and dist_to_target > _STUCK_DISTANCE_THRESHOLD:
                    _stuck_tick_counts[i] = _stuck_tick_counts.get(i, 0) + 1
                    status = "STUCK" if _stuck_tick_counts[i] >= _STUCK_TICK_THRESHOLD else "ACTIVE"
                else:
                    _stuck_tick_counts[i] = 0
                    status = "ACTIVE"

                drone_state = DroneState.from_pybullet(
                    drone_index=i,
                    position=(pos[0], pos[1], pos[2]),
                    linear_velocity=(lin_vel[0], lin_vel[1], lin_vel[2]),
                    heading_rad=heading_rad,
                    battery=1.0,
                    status=status,
                )
                states.append(drone_state.to_dict())

            payload = {
                "type": "TELEMETRY_UPDATE",
                "payload": {
                    "droneStates": states,
                    "fps": 60,
                    "droneCount": len(followers_list)
                }
            }
            msg = json.dumps(payload)
            websockets.broadcast(clients, msg)

        # Render camera frame at ~24 FPS (independent of sim state)
        current_time = time.time()
        if current_time - last_frame_time > 0.041:
            last_frame_time = current_time
            followers_list = swarm_controller.followers
            cam_pos = followers_list[0].get_position() if followers_list else red_pos.tolist()
            cam_yaw = followers_list[0].get_heading_angle() if followers_list else red_yaw

            try:
                w, h, rgba, dep, seg = vision_engine.update_camera_view(
                    drone_pos=cam_pos,
                    heading_angle=cam_yaw
                )
                rgba_arr = np.array(rgba, dtype=np.uint8)
                if rgba_arr.ndim == 1:
                    rgba_arr = rgba_arr.reshape((h, w, 4))
                rgb_arr = rgba_arr[:, :, :3]
                bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                success, encoded_image = cv2.imencode('.jpg', bgr_arr, encode_param)
                if success:
                    with frame_lock:
                        latest_jpeg_frame = encoded_image.tobytes()
            except Exception as e:
                print(f"Frame capture error: {e}")

        await asyncio.sleep(dt)


async def main():
    print("Starting WebSocket Server on ws://localhost:8765")

    # Start MJPEG HTTP server in a background thread
    mjpeg_thread = threading.Thread(target=start_mjpeg_server, daemon=True)
    mjpeg_thread.start()

    async with websockets.serve(handler, "localhost", 8765):
        await simulation_loop()


if __name__ == "__main__":
    asyncio.run(main())
