import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class Obstacle:
    def __init__(self, pos, radius):
        self.pos = np.array(pos, dtype=float)
        self.radius = float(radius)

class Drone:
    def __init__(self, drone_id, start_pos, target_pos):
        self.id = drone_id
        self.pos = np.array(start_pos, dtype=float)
        self.target = np.array(target_pos, dtype=float)
        self.velocity = np.zeros(3)
        self.history = [self.pos.copy()]

    def get_attraction(self, k_att=0.1):
        direction = self.target - self.pos
        distance = np.linalg.norm(direction)
        if distance > 0:
            return k_att * direction
        return np.zeros(3)

    def get_repulsion(self, other_drones, obstacles, k_rep=400.0, safe_dist=8.0, obs_margin=6.0):
        rep_force = np.zeros(3)
        
        for other in other_drones:
            if self.id != other.id:
                diff = self.pos - other.pos
                dist = np.linalg.norm(diff)
                if 0 < dist < safe_dist:
                    rep_force += k_rep * (1.0/dist - 1.0/safe_dist) * (1.0/(dist**2)) * (diff/dist)
                    
        for obs in obstacles:
            diff_2d = self.pos[:2] - obs.pos[:2]
            dist_center = np.linalg.norm(diff_2d)
            dist_surface = max(0.1, dist_center - obs.radius)
            
            if dist_surface < obs_margin:
                force_2d = (k_rep * 80) * (1.0/dist_surface - 1.0/obs_margin) * (1.0/(dist_surface**2)) * (diff_2d/dist_center)
                rep_force[0] += force_2d[0]
                rep_force[1] += force_2d[1]
                
        return rep_force

    def update_position(self, other_drones, obstacles, step_size=0.18):
        f_att = self.get_attraction()
        f_rep = self.get_repulsion(other_drones, obstacles)
        
        total_force = f_att + f_rep
        self.velocity = (self.velocity * 0.8) + (total_force * 0.2)
        
        speed = np.linalg.norm(self.velocity)
        dist_to_target = np.linalg.norm(self.target - self.pos)
        
        if speed < 0.2 and dist_to_target > 5.0:
            self.velocity += np.random.uniform(-2.5, 2.5, 3)
            self.velocity[2] = 0 
            
        speed = np.linalg.norm(self.velocity)
        if speed > 3.0:
            self.velocity = (self.velocity / speed) * 3.0
            
        self.pos += self.velocity * step_size
        self.history.append(self.pos.copy())

swarm = [
    Drone(1, [5, 5, 10], [70, 95, 20]),
    Drone(2, [15, 5, 10], [80, 95, 20]),
    Drone(3, [5, 15, 10], [90, 95, 20]),
    Drone(4, [15, 15, 10], [70, 85, 20]),
    Drone(5, [0, 10, 10], [80, 85, 20]),
    Drone(6, [10, 0, 10], [90, 85, 20])
]

np.random.seed()
obstacles = []
attempts = 0

while len(obstacles) < 5 and attempts < 200:
    attempts += 1
    r = np.random.uniform(5, 10)
    px = np.random.uniform(20, 80)
    py = np.random.uniform(20, 80)
    
    overlap = False
    for obs in obstacles:
        if np.linalg.norm(np.array([px, py]) - np.array([obs.pos[0], obs.pos[1]])) < (r + obs.radius + 2.0):
            overlap = True
            break
            
    for t_pos in [d.target for d in swarm]:
        if np.linalg.norm(np.array([px, py]) - np.array([t_pos[0], t_pos[1]])) < (r + 10.0):
            overlap = True
            break
            
    if not overlap:
        obstacles.append(Obstacle([px, py, 0], r))

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(left=0.05, right=0.75)

for obs in obstacles:
    z = np.zeros(1)
    dx = np.ones(1) * (obs.radius * 2)
    dy = np.ones(1) * (obs.radius * 2)
    dz = np.ones(1) * 30 
    ax.bar3d(obs.pos[0] - obs.radius, obs.pos[1] - obs.radius, z, dx, dy, dz, color='gray', alpha=0.3)

colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan']
scatters = [ax.scatter([], [], [], c=colors[i], s=100) for i in range(6)]
lines = [ax.plot([], [], [], c=colors[i], alpha=0.8, linewidth=2)[0] for i in range(6)]
target_scatters = ax.scatter([d.target[0] for d in swarm], [d.target[1] for d in swarm], [d.target[2] for d in swarm], c='black', marker='x', s=100)

ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_zlim(0, 30)

hud = fig.text(0.78, 0.5, '', fontsize=10, verticalalignment='center', family='monospace')

def update(frame):
    hud_text = f"--- KINEMATIC MESH ---\nFrame: {frame}\n\n"
    for drone in swarm:
        drone.update_position(swarm, obstacles)
        
    for i, drone in enumerate(swarm):
        history = np.array(drone.history)
        scatters[i]._offsets3d = (history[-1:, 0], history[-1:, 1], history[-1:, 2])
        lines[i].set_data(history[:, 0], history[:, 1])
        lines[i].set_3d_properties(history[:, 2])
        
    min_obs_dist = float('inf')
    for drone in swarm:
        for obs in obstacles:
            dist_surface = np.linalg.norm(drone.pos[:2] - obs.pos[:2]) - obs.radius
            if dist_surface < min_obs_dist:
                min_obs_dist = dist_surface

    hud_text += f"Min Surface Gap: {min_obs_dist:.1f}m\n"
    if min_obs_dist < 2.0:
        hud_text += "\nWARNING: PROXIMITY"
        
    hud.set_text(hud_text)
    return scatters + lines + [hud]

ani = animation.FuncAnimation(fig, update, frames=180, interval=30, blit=False)
plt.show()