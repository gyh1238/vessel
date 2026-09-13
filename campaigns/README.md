# campaigns/ — isolated paper experiments

This tree is **separate from** `main/` (GitHub DT_Vessel).
Pulling/updating `main/` does **not** touch anything here.

## Snapshot

`a2z-2026-09-05_paper_v11/`

- Former path: `repro/a2z-2026-09-05/`
- Branch tip at freeze: `repro/a2z-2026-09-05` @ `9e9e6e8` (+ local paper patches)
- Contains:
  - modified sim code (`vessel_gym.py`, `vessel_gym_train.py`, …)
  - paper freeze scripts (`paper_freeze.env`, `start_paper_train.ps1`, …)
  - full Fig1–8 v11 results (`runs/paper/`)

Open results: `a2z-2026-09-05_paper_v11/runs/paper/STRUCTURE.txt`

## Do not

- `git pull` inside this snapshot expecting to “sync with main”
- Train/eval against the old `repro/a2z-2026-09-05` path if it still exists (locked leftover)

## Canonical code (latest GitHub)

Use `F:\projects\vessel\main\` after `git pull --ff-only origin main`.
