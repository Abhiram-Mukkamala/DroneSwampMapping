## Resolve the duplicate vision-engine pipeline, decide fate of root-level scripts

### Context

Two unrelated things both called "vision engine" exist:
- `backend/vision_engine.py`'s `DroneVisionEngine` (RGB/depth/segmentation for the PyBullet camera — genuinely wired into `master_sim_server.py`, working).
- A completely separate `YOLOVisionEngine` referenced in root-level `main.py`, `run_local_test.py`, `run_on_map_cache.py` — all of which import `best.onnx`, a model file that has **never existed** in the repo on any branch. These will crash on import.

### Scope

1. **Determine:** is `YOLOVisionEngine`/`main.py`'s pipeline meant to be a distinct standalone target-detection tool (separate from the Dockerized YOLOv8 FastAPI server the browser sim uses), or is it dead/superseded code from an earlier design? You wrote the original PyBullet showcase — you're the right person to make this call.
2. **If it's meant to live:** either supply `best.onnx` (train/export one, or document exactly what's needed to obtain it) or repoint it at the stock `yolov8n.pt` already in the repo, matching what the browser pipeline uses.
3. **If it's dead:** remove `main.py`, `run_local_test.py`, `run_on_map_cache.py`, and `YOLOVisionEngine` from `vision_engine.py` (root-level copy — **do not touch** `backend/vision_engine.py`'s `DroneVisionEngine`, that's unrelated and working). Update the README tech-debt section accordingly.
4. **Either way:** document the decision in a short comment/README note so this doesn't get rediscovered as a mystery a third time.

### Branch

`shreyas-vision-cleanup`, based on current `phase0-foundation` tip.

### Acceptance Criteria

- No remaining import of a nonexistent file anywhere in the repo.
- A clear, documented answer for what `YOLOVisionEngine` is for (or a clean removal).

### Workflow

- Push to `shreyas-vision-cleanup`.
- Open a PR into `phase0-foundation` — do **not** merge it yourself.
