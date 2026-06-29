import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from path_planning import AStarPlanner
from decision_engine import DecisionEngine
from perfect_swarm import VectorSwarm, Obstacle

def grid_to_world(grid_pos, cell_size=5.0):
    return (grid_pos[1] * cell_size + 2.5, grid_pos[0] * cell_size + 2.5, 20.0)

def draw_cylinder(ax, pos, radius, height, color, alpha=0.3):
    z = np.linspace(0, height, 2)
    theta = np.linspace(0, 2*np.pi, 20)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = radius * np.cos(theta_grid) + pos[0]
    y_grid = radius * np.sin(theta_grid) + pos[1]
    ax.plot_surface(x_grid, y_grid, z_grid, color=color, alpha=alpha)

grid_map = np.zeros((20, 20))
planner = AStarPlanner(safety_margin=1)

static_obstacles = [
    Obstacle([30.0, 30.0, 0.0], 8.0, 25.0, 'cylinder'),
    Obstacle([70.0, 70.0, 0.0], 6.0, 15.0, 'box'),
    Obstacle([30.0, 70.0, 0.0], 10.0, 20.0, 'cylinder'),
    Obstacle([70.0, 30.0, 0.0], 8.0, 30.0, 'box')
]

for obs in static_obstacles:
    r_grid = int(obs.radius // 5.0) + 1
    cx, cy = int(obs.pos[1] // 5.0), int(obs.pos[0] // 5.0)
    r_min = max(0, cx - r_grid)
    r_max = min(20, cx + r_grid + 1)
    c_min = max(0, cy - r_grid)
    c_max = min(20, cy + r_grid + 1)
    grid_map[r_min:r_max, c_min:c_max] = 1

n_drones = 12
start_positions = [[np.random.uniform(2.0, 15.0), np.random.uniform(2.0, 15.0), 10.0] for _ in range(n_drones)]
target_positions = [[50.0 + 15.0 * np.cos(2 * np.pi * i / n_drones), 50.0 + 15.0 * np.sin(2 * np.pi * i / n_drones), 20.0] for i in range(n_drones)]
swarm = VectorSwarm(start_positions, target_positions)
brains = {i+1: DecisionEngine(str(i+1), planner) for i in range(n_drones)}

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')
colors = plt.cm.jet(np.linspace(0, 1, n_drones))
scatters = [ax.scatter([], [], [], c=[colors[i]], s=60) for i in range(n_drones)]
lines = [ax.plot([], [], [], c=colors[i], alpha=0.5, linewidth=1.5)[0] for i in range(n_drones)]

for obs in static_obstacles:
    if obs.shape == 'cylinder':
        draw_cylinder(ax, obs.pos, obs.radius, obs.height, 'cyan')
    elif obs.shape == 'box':
        z = np.zeros(1)
        dx = np.ones(1) * (obs.radius * 2)
        dy = np.ones(1) * (obs.radius * 2)
        dz = np.ones(1) * obs.height 
        ax.bar3d(obs.pos[0] - obs.radius, obs.pos[1] - obs.radius, z, dx, dy, dz, color='gray', alpha=0.3)

ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_zlim(0, 30)

def update(frame):
    for i in range(n_drones):
        brain = brains[i+1]
        grid_pos = (int(swarm.pos[i, 1] // 5.0), int(swarm.pos[i, 0] // 5.0))
        goal_pos = (int(target_positions[i][1] // 5.0), int(target_positions[i][0] // 5.0))
        
        state, path, next_grid_waypoint = brain.evaluate(grid_map, grid_pos, goal_pos)
        next_world_waypoint = grid_to_world(next_grid_waypoint)
        swarm.targets[i] = next_world_waypoint

    swarm.update(static_obstacles)
        
    history = np.array(swarm.history)
    for i in range(n_drones):
        scatters[i]._offsets3d = (history[-1:, i, 0], history[-1:, i, 1], history[-1:, i, 2])
        lines[i].set_data(history[:, i, 0], history[:, i, 1])
        lines[i].set_3d_properties(history[:, i, 2])
        
    return scatters + lines

ani = animation.FuncAnimation(fig, update, frames=300, interval=30, blit=False)
plt.show()