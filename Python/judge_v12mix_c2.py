"""Fig2 C2: SHARED vs SINGLE vs THIN vs THICK on v12mix recipe. Never FINAL."""
from __future__ import annotations
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_HUB = ROOT / "runs" / "paper" / "v12mix_hub" / "eval"
EVAL_MIX = ROOT / "runs" / "paper" / "v12mix" / "eval"
GATE = ROOT / "runs" / "paper" / "v12mix_hub" / "GATE_C2.txt"
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


def arm(prefix: str, folder: Path):
    return [parse(folder / f"post_{prefix}_s{s}.log") for s in (42, 43, 44)]


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


def main() -> int:
    shared = arm("qd_MOE_SE_MX", EVAL_MIX)
    if any(x is None for x in shared):
        shared = arm("qd_MOE_SE_MX", EVAL_HUB)
    single = arm("q_MOE_SINGLE_MX", EVAL_MIX)
    thin = arm("q_MOE_THIN_MX", EVAL_HUB)
    thick = arm("q_MOE_THICK_MX", EVAL_HUB)
    lines = [
        fmt("SHARED", shared),
        fmt("SINGLE", single),
        fmt("THIN", thin),
        fmt("THICK", thick),
    ]
    if not any(x is None for x in shared + thin + thick):
        # C2: SHARED should beat THIN and THICK on goal+prox
        ok_thin = mu(shared, "goal") >= mu(thin, "goal") and mu(shared, "prox") <= mu(thin, "prox")
        ok_thick = mu(shared, "goal") >= mu(thick, "goal") and mu(shared, "prox") <= mu(thick, "prox")
        lines.append(
            f"C2 SHARED>=THIN: {'PASS' if ok_thin else 'FAIL'} "
            f"dGoal={mu(shared,'goal')-mu(thin,'goal'):+.1f} "
            f"dProx={mu(shared,'prox')-mu(thin,'prox'):+.2f}"
        )
        lines.append(
            f"C2 SHARED>=THICK: {'PASS' if ok_thick else 'FAIL'} "
            f"dGoal={mu(shared,'goal')-mu(thick,'goal'):+.1f} "
            f"dProx={mu(shared,'prox')-mu(thick,'prox'):+.2f}"
        )
        win = ok_thin and ok_thick
        lines.insert(0, "WIN" if win else "LOSE")
    else:
        lines.insert(0, "INCOMPLETE")
        win = False
    GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if win else 1


if __name__ == "__main__":
    sys.exit(main())
