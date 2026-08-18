# Legacy System — Archived Branch Consolidation

This directory consolidates the unique work from 6 archived development branches into a single reference location. Each subdirectory contains the files that were **changed or added** on that branch relative to `main` at the time of archiving.

> **Note:** The original branch tips are permanently preserved as Git tags under `archive/<branch-name>` for full commit history access.

## Contents

| Folder | Original Branch | Description | Key Commits |
|:---|:---|:---|:---|
| `phase0-uncommitted-wip/` | `phase0-uncommitted-wip` | WIP Protocol Beta/Gamma, terrain, and heightmap files; grid bounds clamping and repulsion vector routing fixes | `e4d3866`, `5c3390e` |
| `rahul-hazard-integration/` | `rahul-hazard-integration` | Telemetry tracking, API compatibility, test coverage fixes; grid bounds clamping | `3703d25`, `5c3390e` |
| `rahul-simulation-engine/` | `rahul-simulation-engine` | WebSocket pipeline mainframe and documentation | `7ef9f2a` |
| `shreyas/` | `shreyas` | Drone 3D model render (`.obj`) and simulation modifications | `fe6daca` |
| `sutar/` | `sutar` | YOLOv8 perception integration, WebSocket bridge, architecture README | `0c95a8d` |
| `sutar-recovered-decision-engine/` | `sutar-recovered-decision-engine` | Hierarchical decision engine, A* path planning, obstacle mapping, telemetry sync | `987717d`, `2f0bba0` |

## Restoring Original Branch History

To inspect the full commit history of any archived branch:

```bash
# View the log
git log archive/<branch-name>

# Create a temporary branch from the archive tag
git checkout -b temp-restore archive/<branch-name>

# Compare against main at the time
git diff main...archive/<branch-name>
```
