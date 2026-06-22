import math
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

class MockTelemetryNetwork:
    """
    A lightweight, in-memory telemetry synchronization layer that simulates
    real-time communication and state-sharing among team drones.
    """
    def __init__(self) -> None:
        self.network_state: Dict[str, Dict[str, Any]] = {}

    def broadcast(self, drone_id: str, telemetry: Dict[str, Any]) -> None:
        """
        Broadcasts a drone's telemetry profile and detected hazard coordinates to the fleet.
        """
        self.network_state[drone_id] = telemetry

    def get_network_state(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves the global network state of all teammate drones.
        """
        return self.network_state


class DecisionEngine:
    """
    Hierarchical state machine evaluator designed for low-latency edge computing.
    Decides when to trigger A* path replanning and applies Reynolds separation forces.
    """
    def __init__(
        self,
        drone_id: str,
        planner: Any,
        vicinity_radius: float = 4.0,
        repulsion_weight: float = 1.0
    ) -> None:
        """
        Initializes the Decision Engine.

        Args:
            drone_id: Unique identifier for the drone.
            planner: An instance of AStarPlanner.
            vicinity_radius: Proximity threshold (in grid cells) to check for teammates.
            repulsion_weight: Multiplier scaling the strength of the teammate separation force.
        """
        self.drone_id = drone_id
        self.planner = planner
        self.vicinity_radius = vicinity_radius
        self.repulsion_weight = repulsion_weight
        self.current_path: List[Tuple[int, int]] = []
        self.telemetry_network: Dict[str, Dict[str, Any]] = {}

    def update_network_state(self, network_state: Dict[str, Dict[str, Any]]) -> None:
        """
        Updates the local knowledge of teammate positions and paths from telemetry.
        """
        self.telemetry_network = network_state

    def evaluate(
        self,
        grid_map: np.ndarray,
        drone_grid_pos: Tuple[int, int],
        goal_grid_pos: Tuple[int, int],
        detected_hazards_px: List[Tuple[float, float]]
    ) -> Tuple[str, List[Tuple[int, int]], Tuple[float, float]]:
        """
        Executes the hierarchical decision rules:
        1. Check if the current path vector is blocked by a newly detected obstacle.
           -> YES: Re-trigger A* path planning.
        2. Check if teammate drones are nearby in the vicinity.
           -> YES: Compute Reynolds separation/repulsion forces to adjust steering.
        3. Otherwise: Safely follow the active waypoint.

        Args:
            grid_map: The 2D NumPy occupancy grid.
            drone_grid_pos: Drone's current location (row, col).
            goal_grid_pos: Goal location (row, col).
            detected_hazards_px: List of (x, y) pixels of hazards from the vision module.

        Returns:
            A tuple of (decision_state, active_path, steering_vector) where
            steering_vector is a normalized (dy, dx) steering vector.
        """
        decision_state = "FOLLOW_PATH"
        
        # --- Rule 1: Collision & Path Check ---
        path_blocked = False
        
        if not self.current_path:
            path_blocked = True
        else:
            # Check if drone has wandered off path, or if start of path doesn't align
            # If the drone's position is not in the first few steps, we may need to align/replan.
            # In a simulation, we usually align the path start to drone_grid_pos.
            if drone_grid_pos not in self.current_path:
                path_blocked = True
            else:
                # Find current position index in path
                curr_idx = self.current_path.index(drone_grid_pos)
                # Check for obstacles from current position onwards
                for cell in self.current_path[curr_idx:]:
                    r, c = cell
                    if grid_map[r, c] == 1:
                        path_blocked = True
                        break

        if path_blocked:
            decision_state = "REPLAN"
            try:
                # Heavy calculation executed only upon path obstruction
                new_path = self.planner.plan(grid_map, drone_grid_pos, goal_grid_pos)
                if new_path:
                    self.current_path = new_path
                else:
                    # Path planning failed to find path, keep path empty
                    self.current_path = []
                    decision_state = "NO_PATH_FOUND"
            except Exception as e:
                print(f"[DecisionEngine] Exception during defensive A* planning: {e}")
                self.current_path = []
                decision_state = "NO_PATH_FOUND"

        if not self.current_path:
            return decision_state, [], (0.0, 0.0)

        # Get next waypoint along the path
        curr_idx = 0
        if drone_grid_pos in self.current_path:
            curr_idx = self.current_path.index(drone_grid_pos)
            
        next_idx = min(curr_idx + 1, len(self.current_path) - 1)
        next_waypoint = self.current_path[next_idx]
        
        # Nominal direction to the next waypoint
        dy = float(next_waypoint[0] - drone_grid_pos[0])
        dx = float(next_waypoint[1] - drone_grid_pos[1])
        dist = math.hypot(dy, dx)
        
        nominal_vector = (0.0, 0.0)
        if dist > 0.0:
            nominal_vector = (dy / dist, dx / dist)
        else:
            # If already at the target waypoint, try to look ahead further if possible
            if next_idx + 1 < len(self.current_path):
                next_waypoint = self.current_path[next_idx + 1]
                dy = float(next_waypoint[0] - drone_grid_pos[0])
                dx = float(next_waypoint[1] - drone_grid_pos[1])
                dist = math.hypot(dy, dx)
                if dist > 0.0:
                    nominal_vector = (dy / dist, dx / dist)

        # --- Rule 2: Teammate Vicinity Check (Reynolds Separation) ---
        repulsion_dy = 0.0
        repulsion_dx = 0.0
        teammate_in_vicinity = False

        for peer_id, peer_telemetry in self.telemetry_network.items():
            if peer_id == self.drone_id:
                continue
                
            peer_pos = peer_telemetry.get("grid_position")
            if peer_pos is None:
                continue
                
            # Compute grid-space distance to teammate
            d_peer = math.hypot(drone_grid_pos[0] - peer_pos[0], drone_grid_pos[1] - peer_pos[1])
            
            if d_peer <= self.vicinity_radius:
                teammate_in_vicinity = True
                if d_peer > 0.0:
                    # Separation force: repel inversely proportional to squared distance
                    force = 1.0 / (d_peer ** 2)
                    repulsion_dy += (drone_grid_pos[0] - peer_pos[0]) / d_peer * force
                    repulsion_dx += (drone_grid_pos[1] - peer_pos[1]) / d_peer * force

        # --- Apply Swarm Rules to adjust steering vector ---
        if teammate_in_vicinity:
            if decision_state != "REPLAN":
                decision_state = "AVOID_TEAMMATE"
                
            # Combine nominal and separation steering forces
            steer_dy = nominal_vector[0] + self.repulsion_weight * repulsion_dy
            steer_dx = nominal_vector[1] + self.repulsion_weight * repulsion_dx
            
            steer_dist = math.hypot(steer_dy, steer_dx)
            if steer_dist > 0.0:
                steering_vector = (steer_dy / steer_dist, steer_dx / steer_dist)
            else:
                steering_vector = nominal_vector
        else:
            steering_vector = nominal_vector

        return decision_state, self.current_path, steering_vector
