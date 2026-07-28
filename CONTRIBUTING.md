# Contributing to DroneSwampMapping

Thanks for your interest in contributing! This is a browser-based drone
swarm simulator that runs on any device — no install required. It
validates swarm AI (perception, formation control, pathfinding) entirely
in simulation, with an architecture designed to extend to real hardware
if a client has an actual drone fleet.

## Project Status

| Phase | What | Status |
|---|---|---|
| 1 | Core simulation loop + Three.js rendering foundation | ✅ Complete |
| 2 | VectorSwarm (APF) formation engine, ported from Python and numerically verified | ✅ Complete |
| 3 | Simulated per-drone POV + YOLOv8 perception pipeline | 🚧 In progress |
| 4+ | Terrain/hazard mapping, real-hardware outlet | 📋 Planned |

## Architecture at a Glance

The simulator is built around one stable contract — drone state:
```js
{ id, position: {x,y,z}, velocity: {x,y,z}, heading, battery, status }
```
Every module reads and/or writes this shape. This is what lets modules be
worked on independently:

```
web/
├── core/          Physics loop, drone state (the contract everything else uses)
├── render/         Three.js scene, drone meshes, camera controls, per-drone POV capture
├── swarm/          Formation control / pathfinding (VectorSwarm APF engine)
├── perception/      YOLOv8 detection (simulated vision, in progress)
├── data/            Terrain / obstacle / hazard map (planned)
├── ui/              Control panel
└── tests/           Fixture-based verification (see below)
```

**Movement logic lives in `/core` and `/swarm`, never in the render loop.**
Rendering only ever reads state — it doesn't decide behavior.

## Getting Set Up

### Simulator (client-side, no Docker needed)
```bash
cd web
npx serve .
# open http://localhost:3000
```

### Perception service (Python, Docker)
```bash
docker compose up
# health check: curl http://localhost:8000/health
```
You only need this running if you're working on `/perception` or testing
the full vision pipeline — the simulator itself runs fine without it.

## How Verification Works Here

Algorithmic modules (like the swarm engine) are ported from a Python
reference implementation and checked against **fixture snapshots** — a
Python run's output, saved as JSON, that the JS port's output is diffed
against. See `web/tests/` for examples (`test_swarm.html`,
`fixture_snapshot.json`, `fixture_stuck_snapshot.json`).

If you're porting or modifying algorithmic behavior:
- Don't just eyeball that it "looks right" — add or extend a fixture
  comparison
- If your change affects a scenario with randomness (like stuck-detection
  noise), verify behaviorally (does it converge? does it escape a trap?)
  rather than expecting exact float matches
- Note any hardcoded constants you're changing and why — these engines
  tend to have tuned magic numbers that aren't obvious from the code alone

## Module Boundaries — Pick One and Go

Each module has a narrow, defined interface. You can generally work on one
without needing to understand the others:

- **`/core`** — owns drone kinematics only. Doesn't know about swarm logic,
  rendering, or perception.
- **`/render`** — pure consumer of drone state. Never decides drone
  behavior. Also owns the per-drone POV camera capture (`DroneCamera.js`)
  that perception consumes.
- **`/swarm`** — pure function of drone state + obstacles → velocity
  commands. No rendering, no direct DOM/canvas access.
- **`/perception`** — takes an image in, returns detections out. Doesn't
  care whether the image came from the simulator or (eventually) a real
  camera.
- **`/data`** — terrain/obstacle data provider. No physics, no rendering.

If your change needs to touch more than one of these to work, that's a
signal the interface between them might need to change — flag it in your
PR description rather than quietly coupling two modules together.

## Submitting Changes

1. Fork and branch from `main`
2. Keep PRs scoped to one module/concern where possible — easier to review,
   easier to verify
3. If you touched an algorithmic module, include your verification method
   (fixture diff output, or a description of the behavioral check you ran)
4. Open a PR with a clear description of what changed and why

## Reporting Issues

Found a bug or have an idea? Open an issue. If it's a behavioral bug in
one of the algorithmic modules (swarm, perception), include:
- What you expected vs. what happened
- The scenario/inputs that trigger it, if you can isolate them
- Whether it reproduces consistently or seems related to randomness

## Questions?

Open a discussion or issue — happy to help orient new contributors to
whichever module you want to dig into.
