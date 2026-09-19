"""Parse eval_v2/*.log into YHSH-style metric tables. Does not overwrite FIG*_FORMAL*.txt."""
from __future__ import annotations
import csv, re, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "runs" / "paper"
LOGD = PAPER / "eval_v2"
OUTD = ROOT / "results"

MAIN = re.compile(
    r"goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%\s+TO=\s*([\d.]+)%"
    r".*?fuel=\s*([\d.]+)\s+headTravel=\s*([\d.]+)deg\s+minSep=\s*([\d.]+)m\s+len=\s*([\d.]+)"
    r".*?colregsOK=\s*([\d.]+)%"
    r".*?sit1=\s*([\d.]+)%\(n=(\d+)\)\s+sit2=\s*([\d.]+)%\(n=(\d+)\)"
    r"\s+sit3=\s*([\d.]+)%\(n=(\d+)\)\s+sit4=\s*([\d.]+)%\(n=(\d+)\)"
)
V11 = re.compile(r"\[COLREGs PRIMARY-v11\].*?C=\s*([\d.]+)%")
CENS = re.compile(r"\[censored\].*?(\d+)")
NEPS = re.compile(r"\|\s*(\d+)\s+eps")
ALLMIN = re.compile(r"allMinSep=\s*([\d.]+)m")
ALIAS = {
    "ON_s42": "qd_MOE_SE_s42", "ON_s43": "qd_MOE_SE_s43", "ON_s44": "qd_MOE_SE_s44",
    "OFF_s42": "qf_SE_OFF_s42", "OFF_s43": "qf_SE_OFF_s43", "OFF_s44": "qf_SE_OFF_s44",
    "SINGLE_s42": "q_MOE_SINGLE_s42",
}

# condition -> (figure, arm_name)
COND = {
    "qd_MOE_SE": ("hub", "shared_ON"),
    "qf_SE_OFF": ("fig1", "OFF"),
    "q_MOE_SINGLE": ("fig2", "SINGLE"),
    "q_MOE_ISO": ("fig2", "THIN"),
    "base_comm": ("fig2", "THICK"),
    "qf_SE_NEAR1": ("fig3", "NEAR1"),
    "q_DIM2": ("fig4", "DIM2"),
    "q_DIM4": ("fig4", "DIM4"),
    "q_DIM8": ("fig4", "DIM8"),
    "q_DIM10": ("fig4", "DIM10"),
    "q_DIM12": ("fig4", "DIM12"),
    "qo_SE_COLREGSOFF": ("fig5", "COLREGSOFF"),
    "ql_SE_START": ("fig6", "EARLY"),
}

KEYS = ["goal", "vColl", "oColl", "prox", "n_fin", "n_open", "TO", "C_v2", "C_v11",
        "sit1", "sit2", "sit3", "sit4", "fuel", "headTravel", "minSep", "allMinSep", "len"]


def tag_of(stem: str) -> str:
    return ALIAS.get(stem, stem)


def cond_of(tag: str):
    seed = tag.rsplit("_s", 1)[-1]
    prefix = tag[: -(len(seed) + 2)] if tag.endswith(tuple(f"_s{s}" for s in (42, 43, 44))) else tag
    # q_DIM10_s42 -> prefix q_DIM10
    m = re.match(r"^(.*)_s(42|43|44)$", tag)
    if not m:
        return None
    prefix, seed = m.group(1), m.group(2)
    if prefix not in COND:
        return None
    fig, arm = COND[prefix]
    return fig, arm, int(seed), prefix


# Residual+L2 proposed hub (v12r1) and matched arms overwrite v11 freeze logs of the same tag.
OVERLAY = (
    (PAPER / "v12r1" / "eval", {
        "post_qd_MOE_SE_RL2": "qd_MOE_SE",
    }),
    (PAPER / "v12r1_hub" / "eval", {
        "post_qf_SE_OFF_RL2": "qf_SE_OFF",
        "post_q_DIM8_RL2": "q_DIM8",
        "post_q_DIM10_RL2": "q_DIM10",
        "post_q_DIM12_RL2": "q_DIM12",
    }),
    (PAPER / "v12" / "eval", {
        "post_q_MOE_SINGLE_B": "q_MOE_SINGLE",
    }),
    (PAPER / "v12r0" / "eval", {
        "post_qd_MOE_SE_R0": "ql_SE_START",
    }),
)


def parse_log(p: Path, force_tag: str | None = None) -> dict | None:
    text = p.read_text(encoding="utf-8", errors="replace")
    if "PRIMARY-v2-dominant" not in text:
        return None
    tag = force_tag if force_tag else tag_of(p.stem)
    meta = cond_of(tag)
    if not meta:
        return None
    fig, arm, seed, prefix = meta
    # last MAIN-like line (the policy summary)
    last = None
    for line in text.splitlines():
        m = MAIN.search(line)
        if m and "arm=" in line:
            last = m
    if last is None:
        return None
    g = last.groups()
    v11 = V11.search(text)
    n_fin = float(NEPS.search(text).group(1)) if NEPS.search(text) else float("nan")
    n_open = float(CENS.search(text).group(1)) if CENS.search(text) else 0.0
    denom = (n_fin + n_open) if (n_fin == n_fin and (n_fin + n_open) > 0) else float("nan")
    vcoll = float(g[1])
    row = {
        "tag": tag, "fig": fig, "arm": arm, "seed": seed, "prefix": prefix,
        "goal": float(g[0]), "vColl": vcoll, "oColl": float(g[2]), "TO": float(g[3]),
        "n_fin": n_fin, "n_open": n_open,
        "fuel": float(g[4]), "headTravel": float(g[5]), "minSep": float(g[6]), "len": float(g[7]),
        "C_v2": float(g[8]),
        "sit1": float(g[9]), "sit2": float(g[11]), "sit3": float(g[13]), "sit4": float(g[15]),
        "C_v11": float(v11.group(1)) if v11 else float("nan"),
        "allMinSep": float(ALLMIN.search(text).group(1)) if ALLMIN.search(text) else float("nan"),
    }
    # 근접: 선박 박스 겹침으로 끊긴 항해 / (종료 + 창끝 미완). 종료만 모으면 ~6-10%로 부풀어 보임.
    row["prox"] = (vcoll / 100.0 * n_fin) / denom * 100.0 if denom == denom else vcoll
    return row


def mean_std(xs):
    if not xs:
        return float("nan"), float("nan")
    if len(xs) == 1:
        return xs[0], 0.0
    return statistics.mean(xs), statistics.stdev(xs)


def fmt_ms(mu, sd, nd=1):
    return f"{mu:.{nd}f}±{sd:.{nd}f}"


def write_fig(path: Path, title: str, rows_by_arm: dict, hub_mu: dict | None, extra_note: str = ""):
    lines = [title, extra_note, ""] if extra_note else [title, ""]
    lines.append(
        f"{'arm':<16} {'goal':>10} {'prox':>10} {'C_v2':>10} "
        f"{'sit1':>10} {'sit2':>10} {'sit3':>10} {'sit4':>10} "
        f"{'fuel':>10} {'head':>10} {'minSep':>10} {'len':>10}  n"
    )
    for arm, rows in rows_by_arm.items():
        n = len(rows)
        cells = []
        for k in ("goal", "prox", "C_v2", "sit1", "sit2", "sit3", "sit4",
                  "fuel", "headTravel", "minSep", "len"):
            mu, sd = mean_std([r[k] for r in rows])
            cells.append(fmt_ms(mu, sd, 1))
        lines.append(f"{arm:<16} " + " ".join(f"{c:>10}" for c in cells) + f"  {n}")
        if hub_mu and "hub" not in arm.lower():
            rels = []
            for k, lab in (("prox", "prox"), ("fuel", "fuel"), ("headTravel", "head")):
                mu, _ = mean_std([r[k] for r in rows])
                if hub_mu.get(k):
                    rels.append(f"d{lab}={(mu/hub_mu[k]-1)*100:+.1f}% vs hub")
            if rels:
                lines.append("               " + "  ".join(rels))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def overlay_logs():
    extra = []
    for folder, amap in OVERLAY:
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*.log")):
            stem = p.stem
            for src, dst in amap.items():
                m = re.match(rf"^{re.escape(src)}_s(42|43|44)$", stem)
                if m:
                    extra.append((p, f"{dst}_s{m.group(1)}"))
                    break
    return extra


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    logs = sorted(LOGD.glob("*.log"))
    # prefer canonical tag names over aliases if both exist
    parsed = []
    for p in logs:
        r = parse_log(p)
        if r:
            parsed.append(r)
    for p, tag in overlay_logs():
        r = parse_log(p, force_tag=tag)
        if r:
            parsed.append(r)
    by_tag = {}
    for r in parsed:
        # canonical tag wins over alias duplicates
        prev = by_tag.get(r["tag"])
        if prev is None or not prev.get("_alias"):
            r["_alias"] = r["tag"] not in {p.stem for p in logs} and False
            by_tag[r["tag"]] = r
    # if both ON_s42 and qd_MOE_SE_s42, the second overwrites with same tag
    for r in parsed:
        by_tag[r["tag"]] = r
    rows = list(by_tag.values())
    rows.sort(key=lambda r: (r["fig"], r["arm"], r["seed"]))

    csv_path = OUTD / "metrics.csv"
    fields = ["fig", "arm", "seed", "tag", "prefix"] + KEYS
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    hub = [r for r in rows if r["prefix"] == "qd_MOE_SE"]
    hub_mu = {k: statistics.mean([r[k] for r in hub]) for k in KEYS} if hub else {}

    def pick(*pairs):
        out = {}
        for name, pred in pairs:
            out[name] = [r for r in rows if pred(r)]
        return out

    write_fig(OUTD / "FIG1.txt",
              "Fig1 PRIMARY v2 + YHSH metrics (goal among ended; prox among ended+open)",
              pick(("ON (hub)", lambda r: r["prefix"] == "qd_MOE_SE"),
                   ("OFF", lambda r: r["prefix"] == "qf_SE_OFF")),
              hub_mu, "goal=ended eps; prox=v-box overlap / (ended+open). Not labelled collision.")

    write_fig(OUTD / "FIG2.txt", "Fig2 MoE structures PRIMARY v2 + YHSH metrics",
              pick(("SINGLE", lambda r: r["prefix"] == "q_MOE_SINGLE"),
                   ("SHARED (hub)", lambda r: r["prefix"] == "qd_MOE_SE"),
                   ("THIN", lambda r: r["prefix"] == "q_MOE_ISO"),
                   ("THICK", lambda r: r["prefix"] == "base_comm")),
              hub_mu)

    write_fig(OUTD / "FIG3.txt", "Fig3 max_partners PRIMARY v2 + YHSH metrics",
              pick(("partners=4 (hub)", lambda r: r["prefix"] == "qd_MOE_SE"),
                   ("partners=1", lambda r: r["prefix"] == "qf_SE_NEAR1")),
              hub_mu)

    fig4 = {}
    for d in (2, 4, 6, 8, 10, 12):
        name = "DIM6 (hub)" if d == 6 else f"DIM{d}"
        pref = "qd_MOE_SE" if d == 6 else f"q_DIM{d}"
        fig4[name] = [r for r in rows if r["prefix"] == pref]
    write_fig(OUTD / "FIG4.txt", "Fig4 msg_dim PRIMARY v2 + YHSH metrics", fig4, hub_mu)

    write_fig(OUTD / "FIG5.txt", "Fig5 COLREGS term PRIMARY v2 + YHSH metrics",
              pick(("COLREGS on (hub)", lambda r: r["prefix"] == "qd_MOE_SE"),
                   ("COLREGS off", lambda r: r["prefix"] == "qo_SE_COLREGSOFF")),
              hub_mu)

    write_fig(OUTD / "FIG6.txt", "Fig6 comm timing PRIMARY v2 + YHSH metrics",
              pick(("comm @9M (hub)", lambda r: r["prefix"] == "qd_MOE_SE"),
                   ("comm @0 (early)", lambda r: r["prefix"] == "ql_SE_START")),
              hub_mu)

    # Fig7 from existing mixed_fleet_rx.csv (C = step-legacy, not PRIMARY v2).
    # YHSH Fig7: sample-weighted fleet of comm + nocomm groups per (n_rx, seed).
    fig7_csv = PAPER / "fig7" / "mixed_fleet_rx.csv"
    W7 = {"goal": "eps", "coll": "eps", "to": "eps", "minsep": "eps",
          "colregs": "colregs_n", "fuel": "goal_eps", "head": "goal_eps",
          "length": "goal_eps", "sit1": "colregs_n", "sit2": "colregs_n",
          "sit3": "colregs_n", "sit4": "colregs_n"}
    if fig7_csv.exists():
        by7 = {}
        with fig7_csv.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = {k: float(v) for k, v in r.items()
                     if k not in ("tag", "mode", "nocomm", "group")}
                d["goal_eps"] = d["eps"] * d["goal"] / 100.0
                by7.setdefault((int(float(r["nocomm"])), r["tag"]), {})[r["group"]] = d

        def fleet7(groups, col):
            w = W7.get(col, "eps")
            num = sum(g[col] * g[w] for g in groups.values() if g.get(w, 0) > 0)
            den = sum(g[w] for g in groups.values() if g.get(w, 0) > 0)
            return num / den if den > 0 else float("nan")

        ks = sorted({k for k, _ in by7})
        lines = [
            "Fig7 mixed-fleet (existing CSV, YHSH sample-weighted fleet)",
            "C/sit* are STEP-legacy (rudder gate), NOT PRIMARY v2. prox is CSV coll (already all-episode).",
            "",
            f"{'n_rx':>6} {'goal':>10} {'prox':>10} {'C_step':>10} "
            f"{'sit1':>10} {'sit2':>10} {'sit3':>10} {'sit4':>10} "
            f"{'fuel':>10} {'head':>10} {'minSep':>10} {'len':>10}  n",
        ]
        cols = ("goal", "coll", "colregs", "sit1", "sit2", "sit3", "sit4",
                "fuel", "head", "minsep", "length")
        for nrx in ks:
            seeds = sorted({t for k, t in by7 if k == nrx})
            recs = [{c: fleet7(by7[(nrx, t)], c) for c in cols} for t in seeds]
            cells = []
            for c in cols:
                mu, sd = mean_std([x[c] for x in recs])
                cells.append(fmt_ms(mu, sd, 1))
            lines.append(f"{nrx:6d} " + " ".join(f"{c:>10}" for c in cells) + f"  {len(recs)}")
        (OUTD / "FIG7.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Fig8 from existing fig8/*.log (C = step-legacy)
    fig8_re = re.compile(
        r"arm=(\w+)\s+path=(\w+).*?goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%\s+TO=\s*([\d.]+)%"
        r".*?fuel=\s*([\d.]+)\s+headTravel=\s*([\d.]+)deg\s+minSep=\s*([\d.]+)m\s+len=\s*([\d.]+)"
        r".*?colregsOK=\s*([\d.]+)%"
        r".*?sit2=\s*([\d.]+)%"
    )
    f8_lines = [
        "Fig8 A* vs direct hub s42 (existing logs, no retrain)",
        "C/sit2 are STEP-legacy, NOT PRIMARY v2. prox = vColl (Fig8 denom already includes TO).",
        "",
        f"{'arm':<6} {'path':<8} {'goal':>7} {'prox':>7} {'TO':>7} {'C_step':>7} {'sit2':>7} {'fuel':>8} {'head':>8} {'minSep':>8} {'len':>7}",
    ]
    for p in sorted((PAPER / "fig8").glob("hub_s42_*.log")):
        t = p.read_text(encoding="utf-8", errors="replace")
        m = fig8_re.search(t)
        if not m:
            continue
        arm, path, goal, vc, oc, to, fuel, head, ms, ln, c, sit2 = m.groups()
        prox = float(vc)
        f8_lines.append(
            f"{arm:<6} {path:<8} {float(goal):7.1f} {prox:7.1f} {float(to):7.1f} "
            f"{float(c):7.1f} {float(sit2):7.1f} {float(fuel):8.1f} {float(head):8.0f} "
            f"{float(ms):8.1f} {float(ln):7.0f}"
        )
    (OUTD / "FIG8.txt").write_text("\n".join(f8_lines) + "\n", encoding="utf-8")

    n_expect = 3 * (2 + 3 + 1 + 5 + 1 + 1)  # fig1 2arms + fig2 3extra + fig3 1 + fig4 5 + fig5 1 + fig6 1 = 13 cond * 3
    summary = [
        f"v2 YHSH aggregate  logs={len(rows)} (expect ~39)",
        f"csv: {csv_path}",
        f"hub goal={hub_mu.get('goal', float('nan')):.1f} prox={hub_mu.get('prox', float('nan')):.1f} "
        f"C_v2={hub_mu.get('C_v2', float('nan')):.1f} fuel={hub_mu.get('fuel', float('nan')):.1f}",
        "Fig7/Fig8: see FIG7/FIG8 notes - mixed/astar still use their own C unless re-eval ported.",
    ]
    (OUTD / "README.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    missing = []
    for prefix in COND:
        have = {r["seed"] for r in rows if r["prefix"] == prefix}
        for s in (42, 43, 44):
            if s not in have:
                missing.append(f"{prefix}_s{s}")
    if missing:
        print("MISSING", len(missing), missing[:20], ("..." if len(missing) > 20 else ""))
    else:
        print("all Fig1-6 conditions present")


if __name__ == "__main__":
    main()
