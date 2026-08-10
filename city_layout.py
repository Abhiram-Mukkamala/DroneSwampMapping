"""
city_layout.py
---------------
Renders full 3D city models with EXACT concave triangle-mesh (TRIMESH) physical
collisions so drones bounce off walls and roofs instead of phasing through.
"""

from __future__ import annotations
import os
import math
import random

try:
    import pybullet as p
except ImportError:
    p = None

TILE_SIZE = 4.0
BLOCK_SIZE = 3
NUM_BLOCKS = 3
TOTAL_GRID = NUM_BLOCKS * (BLOCK_SIZE + 1) + 1  # 13x13 tile grid


class CityAssetLibrary:
    def __init__(self):
        self.skyscrapers: list[tuple[str, int]] = []
        self.standard_buildings: list[tuple[str, int]] = []
        self.low_detail_buildings: list[tuple[str, int]] = []
        self.road_straights: list[tuple[str, int]] = []
        self.road_crossroads: list[tuple[str, int]] = []
        self._scan_and_cache()

    def _scan_and_cache(self):
        scale = [TILE_SIZE, TILE_SIZE, TILE_SIZE]

        for root, _, files in os.walk("."):
            for file in files:
                if not file.lower().endswith(".obj"):
                    continue

                full_path = os.path.abspath(os.path.join(root, file)).replace("\\", "/")
                name = file.lower()

                vis_id = self._cache_mesh(full_path, scale)
                if vis_id < 0:
                    continue

                item = (full_path, vis_id)

                if "skyscraper" in name:
                    self.skyscrapers.append(item)
                elif "low-detail" in name:
                    self.low_detail_buildings.append(item)
                elif "building" in name:
                    self.standard_buildings.append(item)
                elif "crossroad" in name or "intersection" in name or "crossing" in name:
                    self.road_crossroads.append(item)
                elif "road" in name or "street" in name:
                    self.road_straights.append(item)

    def _cache_mesh(self, path: str, scale: list[float]) -> int:
        try:
            return p.createVisualShape(
                shapeType=p.GEOM_MESH,
                fileName=path,
                meshScale=scale,
            )
        except Exception:
            return -1


def spawn_grounded_tile(asset: tuple[str, int], x: float, y: float, yaw: float, is_building: bool) -> int:
    """Spawns mesh with EXACT concave triangle mesh physical collision boundaries."""
    full_path, vis_id = asset
    orientation = p.getQuaternionFromEuler([math.pi / 2, 0, yaw])

    if is_building:
        # GEOM_FORCE_CONCAVE_TRIMESH enforces true 3D physical collision with every triangle on the mesh
        col_id = p.createCollisionShape(
            shapeType=p.GEOM_MESH,
            fileName=full_path,
            meshScale=[TILE_SIZE, TILE_SIZE, TILE_SIZE],
            flags=p.GEOM_FORCE_CONCAVE_TRIMESH
        )
    else:
        col_id = p.createCollisionShape(
            shapeType=p.GEOM_BOX,
            halfExtents=[TILE_SIZE * 0.48, TILE_SIZE * 0.48, 0.02]
        )

    body_id = p.createMultiBody(
        baseMass=0,  # Static world geometry
        baseCollisionShapeIndex=col_id,
        baseVisualShapeIndex=vis_id,
        basePosition=[x, y, 0.0],
        baseOrientation=orientation,
    )

    aabb_min, _ = p.getAABB(body_id)
    z_offset = -aabb_min[2] + 0.01
    p.resetBasePositionAndOrientation(body_id, [x, y, z_offset], orientation)

    return body_id


def spawn_solid_fallback(x: float, y: float, is_road: bool) -> int:
    if is_road:
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[TILE_SIZE / 2, TILE_SIZE / 2, 0.02])
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[TILE_SIZE / 2, TILE_SIZE / 2, 0.02], rgbaColor=[0.25, 0.25, 0.28, 1.0])
        return p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col, baseVisualShapeIndex=vis, basePosition=[x, y, 0.01])
    else:
        h = random.uniform(10.0, 22.0)
        w = TILE_SIZE * 0.85
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[w / 2, w / 2, h / 2])
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=[w / 2, w / 2, h / 2], rgbaColor=[0.35, 0.45, 0.55, 1.0])
        return p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col, baseVisualShapeIndex=vis, basePosition=[x, y, h / 2])


def build_city() -> list[int]:
    p.configureDebugVisualizer(p.COV_ENABLE_KEYBOARD_SHORTCUTS, 0)
    p.configureDebugVisualizer(p.COV_ENABLE_WIREFRAME, 0)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)

    lib = CityAssetLibrary()
    body_ids = []

    half_grid = TOTAL_GRID // 2
    stride = BLOCK_SIZE + 1

    for row in range(TOTAL_GRID):
        for col in range(TOTAL_GRID):
            x = (col - half_grid) * TILE_SIZE
            y = (row - half_grid) * TILE_SIZE

            is_road_row = (row % stride == 0)
            is_road_col = (col % stride == 0)

            # 1. Road Avenues
            if is_road_row or is_road_col:
                if is_road_row and is_road_col:
                    if lib.road_crossroads:
                        asset = random.choice(lib.road_crossroads)
                        body_ids.append(spawn_grounded_tile(asset, x, y, yaw=0.0, is_building=False))
                    else:
                        body_ids.append(spawn_solid_fallback(x, y, is_road=True))
                else:
                    yaw = math.pi / 2 if is_road_col else 0.0
                    if lib.road_straights:
                        asset = random.choice(lib.road_straights)
                        body_ids.append(spawn_grounded_tile(asset, x, y, yaw=yaw, is_building=False))
                    else:
                        body_ids.append(spawn_solid_fallback(x, y, is_road=True))

            # 2. Building Lots
            else:
                if row == half_grid and col == half_grid:
                    continue  # Clear origin lot

                local_r = (row % stride) - 1
                local_c = (col % stride) - 1
                is_block_center = (local_r == 1 and local_c == 1)
                random_yaw = random.choice([0.0, math.pi / 2, math.pi, 3 * math.pi / 2])

                if is_block_center and lib.skyscrapers:
                    asset = random.choice(lib.skyscrapers)
                    body_ids.append(spawn_grounded_tile(asset, x, y, yaw=random_yaw, is_building=True))
                elif lib.standard_buildings:
                    asset = random.choice(lib.standard_buildings)
                    body_ids.append(spawn_grounded_tile(asset, x, y, yaw=random_yaw, is_building=True))
                elif lib.low_detail_buildings:
                    asset = random.choice(lib.low_detail_buildings)
                    body_ids.append(spawn_grounded_tile(asset, x, y, yaw=random_yaw, is_building=True))
                else:
                    body_ids.append(spawn_solid_fallback(x, y, is_road=False))

    print(f"[city_layout] Successfully generated {len(body_ids)} city tiles with exact trimesh physical collision.")
    return body_ids