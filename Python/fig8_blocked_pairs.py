"""Report A* blocked vs clear spawn/goal pairs (Fig8 dilution note).

Does not run policy eval — only rebuilds the path table like eval_astar_global.
Writes runs/paper/fig8/blocked_pairs.json
"""
from __future__ import annotations
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from apply_paper_freeze import apply_paper_freeze
apply_paper_freeze()

import torch
import vessel_gym as vg

# load sibling module without package init
_spec = importlib.util.spec_from_file_location(
    "eval_astar_global", ROOT / "astar_fig9" / "eval_astar_global.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
build_path_table = _mod.build_path_table


def main():
    out = ROOT.parent / "runs" / "paper" / "fig8"
    out.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    env = vg.VesselBatchEnv(
        num_envs=1, n_vessels=16, device=device, seed=0,
        ring_scale=0.7, crossing=0, risk_range=420.0,
        farfield_coef=0.5, perpair_coef=-0.15, perpair_exp=3.0,
    )
    wp, wn = build_path_table(
        env, "astar", cell=5.0, inflate=vg.SHIP_HALF_LEN,
        wall_margin=vg.SHIP_HALF_LEN, min_wpt_dist=1.5, verbose=True)
    S, G = wn.shape
    blocked, clear = [], []
    sp = (env.spawn_pts * env.ring_scale).tolist()
    gp = (env.goal_pts * env.ring_scale).tolist()
    for si in range(S):
        for gi in range(G):
            n = int(wn[si, gi].item())
            item = {"spawn": si, "goal": gi, "n_wpt": n,
                    "straight": math.dist(sp[si], gp[gi])}
            (blocked if n > 1 else clear).append(item)
    payload = {
        "n_total": S * G,
        "n_blocked": len(blocked),
        "n_clear": len(clear),
        "blocked_frac": len(blocked) / max(S * G, 1),
        "note": "Report Fig8 metrics on blocked subset separately; overall mean dilutes clear pairs.",
        "blocked": blocked,
        "clear": clear,
    }
    path = out / "blocked_pairs.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"blocked={len(blocked)} clear={len(clear)} total={S * G} -> {path}")


if __name__ == "__main__":
    main()
