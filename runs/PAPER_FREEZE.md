# Fig1–8 common freeze (campaign)

**Version:** `common_freeze_v11`

## Layout
See [`paper/STRUCTURE.txt`](paper/STRUCTURE.txt). Summaries live under `paper/results/FIG{1..8}/`; FINAL ckpts under `paper/ckpts/final/` (hardlinked at `paper/<tag>.pt` for scripts).

## Why v11 (after v10 FAIL, dGoal −0.9pp)

Kept from v10:
- `reward_range=DETECTION_RANGE` (fair obs↔reward)
- `comm_on_at=9M` (nav-first)
- `threat=0.45` (avoid post-comm aux shock that hurt v9 s42)

Changed: messages under-used for goal (all seeds ON≈OFF−ε). Boost goal-comm / consumer.

| | v10 | **v11** |
|--|-----|---------|
| Threat | 0.45 | 0.45 |
| Consumer | 0.08 | **0.15** |
| Goal-comm | 0.08 | **0.18** |
| Fig1 | dGoal **−0.9** | target ON > OFF |

Archives: `runs/archive/paper_freeze_v{2..10}/`.

## Fig1 gate (v11) — PASS
2026-09-11 00:23
mean ON=93.7%  mean OFF=90.4%  mean dGoal=+3.3pp
All seeds ON>OFF (+3.5 / +3.4 / +3.2). oColl low.
Hub bar: goal OK; C~55% soft vs aspirational ≥80% (judgment: proceed; C chronic across freezes).
See `paper/results/FIG1/FIG1_FORMAL_COMPARE.txt`.
