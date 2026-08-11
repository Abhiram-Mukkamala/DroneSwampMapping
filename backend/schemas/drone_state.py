"""
drone_state.py — Canonical Drone State Schema (Python)

This is the single source of truth for the shape of a drone's telemetry
state on the backend side.  The matching JavaScript definition lives at
shared/schemas/droneState.js.  Both MUST stay in sync — any field
added/removed/renamed here must be mirrored there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Literal


# ---------------------------------------------------------------------------
# Valid status values — must match DRONE_STATUS in droneState.js
# ---------------------------------------------------------------------------
VALID_STATUSES = frozenset({"ACTIVE", "IDLE", "STUCK", "OFFLINE"})

DroneStatusType = Literal["ACTIVE", "IDLE", "STUCK", "OFFLINE"]


# ---------------------------------------------------------------------------
# Vec3 — reusable 3-component vector
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class Vec3:
    """A 3-component float vector (position or velocity)."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}


# ---------------------------------------------------------------------------
# DroneState — canonical telemetry record
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class DroneState:
    """
    Canonical shape for a single drone's telemetry state.

    Fields
    ------
    id : str
        Unique drone identifier (stringified sim index).
    position : Vec3
        World-space position in metres.
    velocity : Vec3
        Linear velocity in m/s (x, y, z components).
    heading : float
        Yaw heading in degrees [0, 360).
    battery : float
        Charge level, 0.0 (dead) to 1.0 (full).
    status : DroneStatusType
        One of "ACTIVE", "IDLE", "STUCK", "OFFLINE".
    """

    id: str = "0"
    position: Vec3 = None  # type: ignore[assignment]
    velocity: Vec3 = None  # type: ignore[assignment]
    heading: float = 0.0
    battery: float = 1.0
    status: DroneStatusType = "IDLE"

    def __post_init__(self):
        if self.position is None:
            self.position = Vec3()
        if self.velocity is None:
            self.velocity = Vec3()

    # -- Serialisation -------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a plain dict matching the canonical JSON schema."""
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "heading": self.heading,
            "battery": self.battery,
            "status": self.status,
        }

    # -- Factory helpers -----------------------------------------------------

    @classmethod
    def from_pybullet(
        cls,
        *,
        drone_index: int,
        position: tuple[float, float, float],
        linear_velocity: tuple[float, float, float],
        heading_rad: float,
        battery: float = 1.0,
        status: DroneStatusType = "ACTIVE",
    ) -> "DroneState":
        """
        Construct a DroneState from raw PyBullet query results.

        Parameters
        ----------
        drone_index : int
            The sim-engine array index; will be stringified to ``id``.
        position : (x, y, z)
            From ``p.getBasePositionAndOrientation()``.
        linear_velocity : (vx, vy, vz)
            From ``p.getBaseVelocity()`` (first element of the tuple).
        heading_rad : float
            Yaw in **radians** — will be converted to degrees.
        battery : float
            0.0–1.0.
        status : str
            One of the canonical status strings.
        """
        return cls(
            id=str(drone_index),
            position=Vec3(x=position[0], y=position[1], z=position[2]),
            velocity=Vec3(
                x=linear_velocity[0],
                y=linear_velocity[1],
                z=linear_velocity[2],
            ),
            heading=math.degrees(heading_rad) % 360.0,
            battery=max(0.0, min(1.0, battery)),
            status=status if status in VALID_STATUSES else "ACTIVE",
        )
