"""Parallel short eval sweep for fig1_v4 OFF/ON x s42/s43 x steps. Rank Fig1-friendly combos."""
import os, re, sys, time, subprocess
from pathlib import Path

PY = sys.executable
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "runs" / "fig1_v4"
SWEEP = OUT / "combo_sweep"
SWEEP.mkdir(parents=True, exist_ok=True)

ENV = os.environ.copy()
ENV.update({
    "PYTHONUNBUFFERED": "1",
    "VESSEL_USE_MOE": "1", "VESSEL_MOE_SHARED": "1", "VESSEL_MOE_WIDTH": "1.0",
    "VESSEL_MSG_DIM": "6", "VESSEL_POS_GROUND": "1", "VESSEL_USE_ATTENTION": "0",
    "VESSEL_THREAT_COEF": "0.8", "VESSEL_ROLE_COMM_COEF": "0.10",
    "VESSEL_GOAL_COMM_COEF": "0.05", "VESSEL_INTENT_COEF": "0.05",
    "VESSEL_COMM_CONSUMER_COEF": "0.05", "VESSEL_COMM_CONSUMER_COUPLING": "1",
    "VESSEL_SIM_COLREGS_COEF": "0.70", "VESSEL_COLREGS_PRIMARY_ALIGN": "1.0",
    "VESSEL_RADAR_ACT": "leaky", "VESSEL_USE_COMM": "1", "VESSEL_COMM_RANGE": "420",
})

GOAL_RE = re.compile(
    r"goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%.*?colregsOK=\s*([\d.]+)%"
)

def ckpt_path(arm: str, seed: int, step: int) -> Path:
    tag = f"fig1_{arm.lower()}_s{seed}"
    p = OUT / f"{tag}.step{step}M.pt"
    return p if p.exists() else OUT / f"{tag}.pt"

def parse_log(log: Path):
    if not log.exists():
        return None
    text = log.read_text(encoding="utf-8", errors="ignore")
    m = GOAL_RE.search(text)
    if not m:
        return None
    g, v, o, c = map(float, m.groups())
    return {"goal": g, "vColl": v, "oColl": o, "coll": v + o, "C": c}

def run_one(arm, seed, step, gpu):
    ckpt = ckpt_path(arm, seed, step)
    if not ckpt.exists():
        return None
    log = SWEEP / f"fig1_{arm.lower()}_s{seed}_{step}M.log"
    if parse_log(log):
        return parse_log(log)
    env = ENV.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    cmd = [
        PY, "-u", str(ROOT / "eval_ckpt.py"),
        "--ckpt", str(ckpt), "--arm", arm,
        "--envs", "64", "--burnin", "800", "--eval_decisions", "1500",
        "--ring", "0.7", "--max_partners", "4", "--device", "cuda:0",
    ]
    print(f"RUN {arm} s{seed} {step}M GPU{gpu}", flush=True)
    with open(log, "w", encoding="utf-8") as fo, open(str(log) + ".err", "w", encoding="utf-8") as fe:
        p = subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=fo, stderr=fe)
        p.wait(timeout=900)
    return parse_log(log)

def main():
    jobs = []
    for seed in (42, 43):
        for step in (16, 14, 12, 10, 8, 6, 4, 2):
            for arm in ("OFF", "ON"):
                if ckpt_path(arm, seed, step).exists():
                    jobs.append((arm, seed, step))

    # skip already parsed
    pending = [(a, s, st) for a, s, st in jobs if parse_log(SWEEP / f"fig1_{a.lower()}_s{s}_{st}M.log") is None]
    print(f"pending={len(pending)} / total={len(jobs)}", flush=True)

    i = 0
    while i < len(pending):
        batch = pending[i:i + 4]
        procs = []
        for g, (arm, seed, step) in enumerate(batch):
            ckpt = ckpt_path(arm, seed, step)
            log = SWEEP / f"fig1_{arm.lower()}_s{seed}_{step}M.log"
            env = ENV.copy()
            env["CUDA_VISIBLE_DEVICES"] = str(g)
            cmd = [
                PY, "-u", str(ROOT / "eval_ckpt.py"),
                "--ckpt", str(ckpt), "--arm", arm,
                "--envs", "64", "--burnin", "800", "--eval_decisions", "1500",
                "--ring", "0.7", "--max_partners", "4", "--device", "cuda:0",
            ]
            print(f"launch {arm} s{seed} {step}M GPU{g}", flush=True)
            fo = open(log, "w", encoding="utf-8")
            fe = open(str(log) + ".err", "w", encoding="utf-8")
            p = subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=fo, stderr=fe)
            procs.append((p, fo, fe, arm, seed, step))
        for p, fo, fe, arm, seed, step in procs:
            try:
                p.wait(timeout=900)
            except subprocess.TimeoutExpired:
                p.kill()
            fo.close(); fe.close()
            r = parse_log(SWEEP / f"fig1_{arm.lower()}_s{seed}_{step}M.log")
            print(f"done {arm} s{seed} {step}M -> {r}", flush=True)
        i += 4

    # rank matched-step pairs per seed and mean
    rows = []
    for seed in (42, 43):
        for step in (2, 4, 6, 8, 10, 12, 14, 16):
            off = parse_log(SWEEP / f"fig1_off_s{seed}_{step}M.log")
            on = parse_log(SWEEP / f"fig1_on_s{seed}_{step}M.log")
            if not off or not on:
                continue
            dG = on["goal"] - off["goal"]
            dColl = on["coll"] - off["coll"]
            dC = on["C"] - off["C"]
            # target: dG>0, dColl<0, dC in [-3, +1]
            ok = (dG > 0) and (dColl < 0) and (-3.0 <= dC <= 1.0)
            # score: prefer big goal gain + big coll drop; colregs near 0 from below
            score = dG + (-dColl) + max(0.0, 3.0 + dC)  # reward dC closer to 0 from negative
            if dC > 1:
                score -= 2 * (dC - 1)
            rows.append({
                "seed": seed, "step": step, "ok": ok, "score": score,
                "dG": dG, "dColl": dColl, "dC": dC,
                "off": off, "on": on,
            })

    rows.sort(key=lambda r: (not r["ok"], -r["score"]))
    out_txt = SWEEP / "ranking.txt"
    lines = []
    lines.append("TARGET: ON goal↑, coll↓, colregsOK similar or slightly↓ (dC in [-3,+1])\n")
    for r in rows:
        mark = "PASS" if r["ok"] else "fail"
        lines.append(
            f"{mark} s{r['seed']} step{r['step']}M score={r['score']:.1f} "
            f"dG={r['dG']:+.1f} dColl={r['dColl']:+.1f} dC={r['dC']:+.1f} | "
            f"OFF g={r['off']['goal']:.1f} coll={r['off']['coll']:.1f} C={r['off']['C']:.1f} / "
            f"ON g={r['on']['goal']:.1f} coll={r['on']['coll']:.1f} C={r['on']['C']:.1f}"
        )
    # also mean over seeds at same step
    lines.append("\n=== mean s42+s43 by step ===")
    by_step = {}
    for r in rows:
        by_step.setdefault(r["step"], []).append(r)
    mean_rows = []
    for step, rs in by_step.items():
        if len(rs) < 2:
            continue
        dG = sum(x["dG"] for x in rs) / len(rs)
        dColl = sum(x["dColl"] for x in rs) / len(rs)
        dC = sum(x["dC"] for x in rs) / len(rs)
        ok = (dG > 0) and (dColl < 0) and (-3.0 <= dC <= 1.0)
        score = dG + (-dColl) + max(0.0, 3.0 + dC)
        mean_rows.append((ok, score, step, dG, dColl, dC, rs))
    mean_rows.sort(key=lambda t: (not t[0], -t[1]))
    for ok, score, step, dG, dColl, dC, rs in mean_rows:
        mark = "PASS" if ok else "fail"
        lines.append(
            f"{mark} MEAN step{step}M score={score:.1f} dG={dG:+.1f} dColl={dColl:+.1f} dC={dC:+.1f} (n={len(rs)})"
        )

    text = "\n".join(lines) + "\n"
    out_txt.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out_txt}", flush=True)

if __name__ == "__main__":
    main()
