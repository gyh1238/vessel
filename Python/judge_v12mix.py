"""Fig2-only judge: SHARED MoE must beat SINGLE on goal+prox.

Same train recipe (sit oversample) on both arms. SINGLE mean goal must stay
>=90 so a collapsed baseline cannot count as a win. Never writes FINAL.
Fig1 is v12p, not this campaign.
"""
from __future__ import annotations
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "runs" / "paper" / "v12mix" / "eval"
GATE = ROOT / "runs" / "paper" / "v12mix" / "GATE.txt"
MAIN = re.compile(
    r"goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%\s+TO=\s*([\d.]+)%"
)
NEPS = re.compile(r"\|\s*(\d+)\s+eps")
CENS = re.compile(r"\[censored\].*?(\d+)")
CDOM = re.compile(r"PRIMARY-v2-dominant\] C=\s*([\d.]+)%")


def parse(p: Path):
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


def arm(prefix: str):
    return [parse(EVAL / f"post_{prefix}_s{s}.log") for s in (42, 43, 44)]


def mu(xs, k):
    return statistics.mean(x[k] for x in xs)


def sd(xs, k):
    v = [x[k] for x in xs]
    return statistics.stdev(v) if len(v) > 1 else 0.0


def fmt(name, xs):
    return (
        f"{name} goal={mu(xs,'goal'):.1f}±{sd(xs,'goal'):.1f} "
        f"prox={mu(xs,'prox'):.2f}±{sd(xs,'prox'):.2f} C={mu(xs,'C'):.1f}"
    )


def main() -> int:
    on = arm("qd_MOE_SE_MX")
    si = arm("q_MOE_SINGLE_MX")
    lines = []
    if any(x is None for x in on + si):
        lines.append("LOSE")
        lines.append(f"missing ON={on} SINGLE={si}")
        GATE.parent.mkdir(parents=True, exist_ok=True)
        GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 1
    g_on, p_on = mu(on, "goal"), mu(on, "prox")
    g_si, p_si = mu(si, "goal"), mu(si, "prox")
    fig2 = (g_on >= g_si) and (p_on <= p_si)
    n2 = sum(1 for a, b in zip(on, si) if a["goal"] >= b["goal"] and a["prox"] <= b["prox"])
    collapsed = g_si < 90.0
    win = fig2 and not collapsed
    lines.append("WIN" if win else "LOSE")
    lines.append(fmt("SHARED_ON", on))
    lines.append(fmt("SINGLE", si))
    lines.append(
        f"Fig2 ON>=SINGLE: {'PASS' if fig2 else 'FAIL'} dGoal={g_on-g_si:+.1f} dProx={p_on-p_si:+.2f} seeds={n2}/3"
    )
    if collapsed:
        lines.append(f"SINGLE collapsed mean goal={g_si:.1f}<90 - not a Fig2 win")
    for s, a, b in zip((42, 43, 44), on, si):
        lines.append(f"s{s} ON {a['goal']:.1f}/{a['prox']:.2f}  SINGLE {b['goal']:.1f}/{b['prox']:.2f}")
    GATE.parent.mkdir(parents=True, exist_ok=True)
    GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if win else 1


if __name__ == "__main__":
    sys.exit(main())
