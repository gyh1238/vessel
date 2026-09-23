"""Summarize v12mix hub ablations for Fig1/3/4/5/6. Never writes FINAL.

Hub ON = qd_MOE_SE_MX (Fig2 WIN). Arms trained in runs/paper/v12mix_hub.
"""
from __future__ import annotations
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "runs" / "paper" / "v12mix_hub" / "eval"
GATE = ROOT / "runs" / "paper" / "v12mix_hub" / "GATE.txt"
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
    if any(x is None for x in xs):
        return f"{name} INCOMPLETE"
    return (
        f"{name} goal={mu(xs,'goal'):.1f}±{sd(xs,'goal'):.1f} "
        f"prox={mu(xs,'prox'):.2f}±{sd(xs,'prox'):.2f} C={mu(xs,'C'):.1f}"
    )


def block(title, a, b, rule, higher_goal=True):
    lines = [title, fmt("A", a), fmt("B", b)]
    if any(x is None for x in a + b):
        lines.append("INCOMPLETE")
        return lines, False
    ga, pa = mu(a, "goal"), mu(a, "prox")
    gb, pb = mu(b, "goal"), mu(b, "prox")
    ok = (ga >= gb and pa <= pb) if higher_goal else (ga > gb and pa < pb)
    # Fig1 style: A should beat B with strict goal> and prox<
    if rule == "fig1":
        ok = (ga > gb) and (pa < pb)
        n = sum(1 for x, y in zip(a, b) if x["goal"] > y["goal"] and x["prox"] < y["prox"])
        lines.append(f"Fig1 ON>OFF: {'PASS' if ok else 'FAIL'} dGoal={ga-gb:+.1f} dProx={pa-pb:+.2f} seeds={n}/3")
    elif rule == "ablate":
        # hub (a) vs ablation (b): report delta, pass if hub goal>= and prox<=
        ok = (ga >= gb) and (pa <= pb)
        n = sum(1 for x, y in zip(a, b) if x["goal"] >= y["goal"] and x["prox"] <= y["prox"])
        lines.append(f"hub>=ablate: {'PASS' if ok else 'FAIL'} dGoal={ga-gb:+.1f} dProx={pa-pb:+.2f} seeds={n}/3")
    else:
        lines.append(f"dGoal={ga-gb:+.1f} dProx={pa-pb:+.2f}")
        ok = True
    return lines, ok


def main() -> int:
    on = arm("qd_MOE_SE_MX")
    off = arm("qf_SE_OFF_MX")
    near = arm("qf_SE_NEAR1_MX")
    col = arm("qo_SE_COLREGSOFF_MX")
    c0 = arm("qo_SE_COMM0_MX")
    d8 = arm("q_DIM8_MX")
    d10 = arm("q_DIM10_MX")
    d12 = arm("q_DIM12_MX")
    lines = []
    all_ok = True

    b, ok = block("== Fig1 ON vs OFF ==", on, off, "fig1")
    lines.extend(b); lines.append(""); all_ok = all_ok and ok and not any(x is None for x in on + off)

    b, ok = block("== Fig3 hub(K=4) vs NEAR1 ==", on, near, "ablate")
    lines.extend(b); lines.append("")

    lines.append("== Fig4 DIM6 hub vs DIM8/10/12 ==")
    lines.append(fmt("DIM6", on))
    for name, xs in (("DIM8", d8), ("DIM10", d10), ("DIM12", d12)):
        lines.append(fmt(name, xs))
    lines.append("")

    lines.append("== Fig5 hub vs COLREGS-off ==")
    lines.append(fmt("COLREGS_ON", on))
    lines.append(fmt("COLREGS_OFF", col))
    if not any(x is None for x in on + col):
        lines.append(
            f"C lift: hub={mu(on,'C'):.1f} vs OFF={mu(col,'C'):.1f} "
            f"({'PASS' if mu(on, 'C') > mu(col, 'C') + 5 else 'WEAK'})"
        )
    lines.append("")

    b, ok = block("== Fig6 hub@9M vs COMM@0 ==", on, c0, "ablate")
    lines.extend(b)

    GATE.parent.mkdir(parents=True, exist_ok=True)
    GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
