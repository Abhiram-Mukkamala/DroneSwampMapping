import numpy as np

class Obstacle:
    def __init__(self, pos, radius, height=30.0, shape='box'):
        self.pos = np.array(pos, dtype=float)
        self.radius = float(radius)
        self.height = float(height)
        self.shape = shape

class VectorSwarm:
    def __init__(self, starts, targets):
        self.pos = np.array(starts, dtype=float)
        self.targets = np.array(targets, dtype=float)
        self.vel = np.zeros_like(self.pos)
        self.n = len(starts)
        self.history = [self.pos.copy()]
        self.ids = np.arange(1, self.n + 1)

    def update(self, obstacles, step_size=0.18):
        dirs = self.targets - self.pos
        dists = np.linalg.norm(dirs, axis=1, keepdims=True)
        f_att = np.where(dists > 0, 0.15 * dirs, 0)

        f_rep = np.zeros_like(self.pos)
        
        for i in range(self.n):
            diffs = self.pos[i] - self.pos
            d = np.linalg.norm(diffs, axis=1, keepdims=True)
            mask = (d > 0) & (d < 5.0)
            safe_d = np.where(d == 0, 1.0, d)
            f_rep[i] += np.sum(np.where(mask, 150.0 * (1/safe_d - 1/5.0) * (1/safe_d**2) * (diffs/safe_d), 0), axis=0)

        for obs in obstacles:
            diffs_2d = self.pos[:, :2] - obs.pos[:2]
            d_center = np.linalg.norm(diffs_2d, axis=1, keepdims=True)
            d_surf = np.maximum(0.1, d_center - obs.radius)
            mask = d_surf < 5.0
            force_2d = np.where(mask, 800.0 * (1/d_surf - 1/5.0) * (1/d_surf**2) * (diffs_2d/d_center), 0)
            f_rep[:, 0] += force_2d[:, 0]
            f_rep[:, 1] += force_2d[:, 1]

        total_f = f_att + f_rep
        self.vel = (self.vel * 0.85) + (total_f * 0.15)
        
        speeds = np.linalg.norm(self.vel, axis=1, keepdims=True)
        stuck = (speeds < 0.1) & (dists > 3.0)
        noise = np.random.uniform(-1.0, 1.0, self.vel.shape)
        noise[:, 2] = 0
        self.vel = np.where(stuck, self.vel + noise, self.vel)
        
        speeds = np.linalg.norm(self.vel, axis=1, keepdims=True)
        safe_speeds = np.where(speeds == 0, 1.0, speeds)
        self.vel = np.where(speeds > 3.5, (self.vel / safe_speeds) * 3.5, self.vel)
        
        self.pos += self.vel * step_size
        self.history.append(self.pos.copy())