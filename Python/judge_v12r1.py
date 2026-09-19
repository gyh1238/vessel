"""Judge residual+L2 SHARED_RL2 (3 seeds) vs existing v12 SINGLE_B. Mean win: goal>= and prox<=."""
from __future__ import annotations
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / "runs" / "paper" / "v12" / "eval"
V12R = ROOT / "runs" / "paper" / "v12r1" / "eval"
GATE = ROOT / "runs" / "paper" / "v12r1" / "GATE.txt"
MAIN = re.compile(
    r"goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%\s+TO=\s*([\d.]+)%"
)
NEPS = re.compile(r"\|\s*(\d+)\s+eps")
CENS = re.compile(r"\[censored\].*?(\d+)")
CDOM = re.compile(r"PRIMARY-v2-dominant\] C=\s*([\d.]+)%")


def parse(p: Path) -> dict | None:
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    if "PRIMARY-v2-dominant" not in text:
        return None
    last = None
    for line in text.splitlines():
        m = MAIN.search(line)
        if m and "arm=" in line:
            last = m
    if last is None:
        return None
    n_fin = float(NEPS.search(text).group(1)) if NEPS.search(text) else float("nan")
    n_open = float(CENS.search(text).group(1)) if CENS.search(text) else 0.0
    denom = n_fin + n_open
    vcoll = float(last.group(2))
    prox = (vcoll / 100.0 * n_fin) / denom * 100.0 if denom else vcoll
    c = CDOM.search(text)
    return {"goal": float(last.group(1)), "prox": prox, "C": float(c.group(1)) if c else float("nan")}


def arm(dir_: Path, prefix: str):
    out = []
    for s in (42, 43, 44):
        d = parse(dir_ / f"post_{prefix}_s{s}.log")
        out.append(d)
    return out


def main() -> int:
    sh = arm(V12R, "qd_MOE_SE_RL2")
    si = arm(V12, "q_MOE_SINGLE_B")
    lines = []
    if any(x is None for x in sh + si):
        lines.append("LOSE")
        lines.append(f"missing shared={sh} single={si}")
        GATE.parent.mkdir(parents=True, exist_ok=True)
        GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 1
    def mu(xs, k):
        return statistics.mean(x[k] for x in xs)
    def sd(xs, k):
        v = [x[k] for x in xs]
        return statistics.stdev(v) if len(v) > 1 else 0.0
    g_sh, p_sh = mu(sh, "goal"), mu(sh, "prox")
    g_si, p_si = mu(si, "goal"), mu(si, "prox")
    n_win = sum(1 for a, b in zip(sh, si) if a["goal"] >= b["goal"] and a["prox"] <= b["prox"])
    win = (g_sh >= g_si) and (p_sh <= p_si)
    lines.append("WIN" if win else "LOSE")
    lines.append(
        f"SHARED_RL2 goal={g_sh:.1f}±{sd(sh,'goal'):.1f} prox={p_sh:.2f}±{sd(sh,'prox'):.2f} "
        f"C={mu(sh,'C'):.1f}"
    )
    lines.append(
        f"SINGLE_B goal={g_si:.1f}±{sd(si,'goal'):.1f} prox={p_si:.2f}±{sd(si,'prox'):.2f} "
        f"C={mu(si,'C'):.1f}"
    )
    for s, a, b in zip((42, 43, 44), sh, si):
        lines.append(
            f"s{s} RL2 {a['goal']:.1f}/{a['prox']:.2f} vs SINGLE {b['goal']:.1f}/{b['prox']:.2f}"
        )
    lines.append(f"seeds_win={n_win}/3  dGoal={g_sh-g_si:+.1f} dProx={p_sh-p_si:+.2f}")
    GATE.parent.mkdir(parents=True, exist_ok=True)
    GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if win else 1


if __name__ == "__main__":
    sys.exit(main())
