import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { useDrones } from '../../contexts/DroneContext';
import './SwarmView3D.css';

// Matches the existing status colors used by BottomStats.jsx
const STATUS_COLORS = {
  ACTIVE: '#4ade80',
  STUCK: '#facc15',
  OFFLINE: '#f87171',
  IDLE: '#94a3b8',
};

const getStatusColor = (status) => {
  return STATUS_COLORS[status] || STATUS_COLORS.IDLE;
};

const DroneMesh = ({ drone }) => {
  if (!drone.position) return null;

  const { x = 0, y = 0, z = 0 } = drone.position;
  const heading = Number(drone.heading) || 0;
  const color = getStatusColor(drone.status);

  return (
    <group
      position={[x, y, z]}
      rotation={[0, heading, 0]}
    >
      <mesh
        rotation={[Math.PI / 2, 0, 0]}
        castShadow
      >
        <coneGeometry args={[2, 5, 8]} />

        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.45}
          roughness={0.35}
          metalness={0.6}
        />
      </mesh>

      <mesh castShadow>
        <sphereGeometry args={[0.8, 8, 8]} />

        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.7}
          roughness={0.3}
          metalness={0.5}
        />
      </mesh>
    </group>
  );
};

const Ground = () => {
  return (
    <>
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[250, 0, 250]}
        receiveShadow
      >
        <planeGeometry args={[500, 500]} />

        <meshStandardMaterial
          color="#0d1117"
          roughness={0.9}
          metalness={0.1}
        />
      </mesh>

      <gridHelper
        args={[500, 10, '#1a2332', '#111a27']}
        position={[250, 0.02, 250]}
      />
    </>
  );
};

const Scene = ({ drones }) => {
  return (
    <>
      <color
        attach="background"
        args={['#070b15']}
      />

      <ambientLight intensity={0.8} />

      <hemisphereLight
        args={['#28282b', '#111111', 0.5]}
      />

      <directionalLight
        position={[200, 300, 150]}
        intensity={1.2}
        castShadow
      />

      <directionalLight
        position={[-100, 50, -100]}
        intensity={0.3}
        color="#28282b"
      />

      <Ground />

      {drones.map((drone) => (
        <DroneMesh
          key={drone.id}
          drone={drone}
        />
      ))}
    </>
  );
};

const SwarmView3D = () => {
  const { drones } = useDrones();

  return (
    <div className="swarm-view-3d glass-panel">
      <div className="panel-header">
        <h2>3D SWARM</h2>

        <div className="swarm-3d-header-actions">
          <span className="swarm-3d-count">
            {drones.length} DRONES
          </span>
        </div>
      </div>

      <div className="swarm-3d-content">
        <Canvas
          camera={{
            position: [40, 35, 60],
            fov: 50,
            near: 0.1,
            far: 1000,
          }}
          dpr={[1, 2]}
          shadows
        >
          <Scene drones={drones} />

          <OrbitControls
            target={[0, 0, 0]}
            enablePan
            enableZoom
            enableRotate
          />
        </Canvas>

        {drones.length === 0 && (
          <div className="swarm-3d-empty">
            NO DRONES DEPLOYED
          </div>
        )}
      </div>
    </div>
  );
};

export default SwarmView3D;