"""v11 paper figures in the YHSH layout. Numbers come from eval_v2 (PRIMARY v2).

Proximity (not 'collision'): ship-box overlap episodes / (ended + window-open).
Arrival/goal stays among ended episodes (TO=0 in this protocol).

    python make_paper_figures.py
    python make_paper_figures.py 1 5
"""
from __future__ import annotations
import csv
import os
import sys
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAPER = ROOT / "runs" / "paper"
CSV = ROOT / "results" / "metrics.csv"
OUT = ROOT / "figures"
YHSH_FIG = Path(r"F:\projects\vessel\reference\YHSH_VESSEL\paper_figures")
sys.path.insert(0, str(YHSH_FIG))

import figstyle as fsx
from figstyle import C
import schematics as sch

SIT4 = ["Head-On", "Give-Way", "Overtaking", "Stand-On"]
SIT_KEYS = ("sit1", "sit3", "sit4", "sit2")
W_GOAL, W_PROX, W_TO = 1.5, 6.0, 0.5
PARAMS = {  # YHSH measured counts; architecture unchanged
    "SINGLE": 369131, "THIN": 363004, "THICK": 1826719, "SHARED": 511543,
}


def load_rows():
    rows = []
    with CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out = dict(r)
            for k, v in r.items():
                if k in ("fig", "arm", "tag", "prefix"):
                    continue
                try:
                    out[k] = float(v)
                except (TypeError, ValueError):
                    pass
            out["seed"] = int(float(out["seed"]))
            tag = str(out.get("tag", ""))
            m = __import__("re").match(r"^(.*)_s(42|43|44)$", tag)
            out["prefix"] = m.group(1) if m else out.get("arm", "")
            rows.append(out)
    return rows


def pick(rows, prefix):
    return [r for r in rows if r["prefix"] == prefix]


def ms(rows, key):
    xs = [float(r[key]) for r in rows]
    if not xs:
        return float("nan"), 0.0, []
    if len(xs) == 1:
        return xs[0], 0.0, xs
    return statistics.mean(xs), statistics.stdev(xs), xs


def sits(rows):
    return [ms(rows, k)[0] for k in SIT_KEYS]


def score_row(r):
    return W_GOAL * r["goal"] - W_PROX * r["prox"] - W_TO * r.get("TO", 0.0)


def pct(a, b):
    if b == 0:
        return 0.0
    return (a - b) / b * 100.0


def fig1(rows):
    off, on = pick(rows, "qf_SE_OFF"), pick(rows, "qd_MOE_SE")
    lab = ["Comm OFF", "Comm ON"]
    col = [C["base"], C["proposed"]]
    off_p, on_p = ms(off, "prox"), ms(on, "prox")
    off_g, on_g = ms(off, "goal"), ms(on, "goal")
    off_c, on_c = ms(off, "C_v2"), ms(on, "C_v2")
    dprox = pct(on_p[0], off_p[0])

    fig = plt.figure(figsize=(11.0, 6.2))
    gs = GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.34)

    ax = fig.add_subplot(gs[0, 0])
    fsx.bars(ax, lab, [off_p[0], on_p[0]], col, "{:.2f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    ax.annotate(f"{dprox:+.0f}%", xy=(1, on_p[0]), xytext=(0, 22),
                textcoords="offset points", ha="center", fontsize=9,
                color=C["accent"], fontweight="bold")
    fsx.panel_tag(ax, "(a)", dx=-0.14)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [off_g[0], on_g[0]], col, "{:.1f}",
             ylabel="Arrival rate (%)", title="Arrival rate")
    fsx.panel_tag(ax, "(b)", dx=-0.14)

    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [off_c[0], on_c[0]], col, "{:.1f}",
             ylabel="Compliance (%)", title="Overall COLREGs (PRIMARY v2)")
    fsx.panel_tag(ax, "(c)", dx=-0.14)

    ax = fig.add_subplot(gs[1, :2])
    fsx.grouped_bars(ax, SIT4, [("Comm OFF", sits(off)), ("Comm ON", sits(on))], col,
                     ylabel="Compliance (%)", title="COLREGs by encounter type",
                     fmt="{:.1f}")
    ax.set_ylim(0, 132)
    fsx.panel_tag(ax, "(d)", dx=-0.07)

    ax = fig.add_subplot(gs[1, 2])
    fsx.rel_change(ax, ["Fuel", "Heading\ntravel"],
                   [ms(off, "fuel")[0], ms(off, "headTravel")[0]],
                   [ms(on, "fuel")[0], ms(on, "headTravel")[0]],
                   title="Efficiency vs Comm OFF")
    fsx.panel_tag(ax, "(e)", dx=-0.14)

    fig.text(0.5, -0.035,
             "v11 freeze, 3 seeds. Arrival is among ended episodes. Proximity is ship-box overlap "
             "over ended + still-open voyages (not a crash rate among finished trips).\n"
             f"Typical goal-episode minSep ON {ms(on, 'minSep')[0]:.1f} m / OFF {ms(off, 'minSep')[0]:.1f} m.  "
             "PRIMARY v2 compliance is near ceiling on both arms; communication wins arrival and proximity.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig1_Communication_necessity")


def fig2(rows):
    arms = [
        ("SINGLE", "q_MOE_SINGLE", C["base"]),
        ("THIN", "q_MOE_ISO", C["alt1"]),
        ("THICK", "base_comm", C["alt2"]),
        ("SHARED", "qd_MOE_SE", C["proposed"]),
    ]
    lab = ["Single\nnetwork", "Separate\nthin", "Separate\nfull", "Shared\n(proposed)"]
    col = [a[2] for a in arms]
    params = [PARAMS[a[0]] / 1e3 for a in arms]
    prox = [ms(pick(rows, a[1]), "prox") for a in arms]
    goal = [ms(pick(rows, a[1]), "goal") for a in arms]

    fig = plt.figure(figsize=(11.6, 7.4))
    gs = GridSpec(3, 2, figure=fig, width_ratios=[1.32, 1.0], hspace=0.52, wspace=0.22)

    ax = fig.add_subplot(gs[:, 0])
    sch.architectures(ax)
    ax.set_title("Four architectures compared", pad=4)
    fsx.panel_tag(ax, "(a)", dx=0.0, dy=1.005)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, params, col, "{:.0f}K",
             ylabel="Parameters (thousands)", title="Parameter count")
    ax.tick_params(axis="x", labelsize=7.6)
    fsx.panel_tag(ax, "(b)")

    ax = fig.add_subplot(gs[1, 1])
    fsx.bars(ax, lab, [p[0] for p in prox], col, "{:.2f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    ax.tick_params(axis="x", labelsize=7.6)
    fsx.panel_tag(ax, "(c)")

    ax = fig.add_subplot(gs[2, 1])
    fsx.bars(ax, lab, [g[0] for g in goal], col, "{:.1f}",
             ylabel="Arrival rate (%)", title="Arrival rate")
    ax.tick_params(axis="x", labelsize=7.6)
    fsx.panel_tag(ax, "(d)")

    fig.text(0.5, -0.015,
             "v11 3 seeds per arm. Single-network (no MoE) is best on arrival and proximity; "
             "separate-full is worst. Shared hub sits in between.\n"
             "This does not reproduce the YHSH story that shared MoE uniquely minimises crashes. "
             "Capacity vs specialisation still favours not duplicating the radar encoder (thin/full).",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig2_MoE_architecture")


def fig3(rows):
    n1, n4 = pick(rows, "qf_SE_NEAR1"), pick(rows, "qd_MOE_SE")
    lab = ["Nearest-1", "Nearest-4"]
    col = [C["base"], C["proposed"]]
    p1, p4 = ms(n1, "prox"), ms(n4, "prox")

    fig = plt.figure(figsize=(10.4, 6.3))
    gs = GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.28)

    ax = fig.add_subplot(gs[0, 0])
    sch.aggregation(ax)
    ax.set_title("Message aggregation", pad=4)
    fsx.panel_tag(ax, "(a)", dx=-0.02)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [p1[0], p4[0]], col, "{:.2f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    ax.annotate(f"{pct(p4[0], p1[0]):+.0f}%", xy=(1, p4[0]), xytext=(0, 22),
                textcoords="offset points", ha="center", fontsize=9,
                color=C["accent"], fontweight="bold")
    fsx.panel_tag(ax, "(b)", dx=-0.12)

    ax = fig.add_subplot(gs[1, 0])
    fsx.grouped_bars(ax, SIT4, [("Nearest-1", sits(n1)), ("Nearest-4", sits(n4))], col,
                     ylabel="Compliance (%)", title="Compliance by encounter type",
                     fmt="{:.1f}")
    ax.set_ylim(0, 128)
    ax.tick_params(axis="x", labelsize=7.8)
    fsx.panel_tag(ax, "(c)")

    ax = fig.add_subplot(gs[1, 1])
    fsx.rel_change(ax, ["Fuel", "Heading\ntravel"],
                   [ms(n1, "fuel")[0], ms(n1, "headTravel")[0]],
                   [ms(n4, "fuel")[0], ms(n4, "headTravel")[0]],
                   ylabel="Change vs nearest-1 (%)", title="Efficiency vs nearest-1")
    fsx.panel_tag(ax, "(d)", dx=-0.12)

    g1, g4 = ms(n1, "goal")[0], ms(n4, "goal")[0]
    c1, c4 = ms(n1, "C_v2")[0], ms(n4, "C_v2")[0]
    fig.text(0.5, -0.03,
             f"Arrival {g1:.1f}% -> {g4:.1f}%. PRIMARY v2 compliance {c1:.1f}% -> {c4:.1f}%.\n"
             "Four neighbours beat one on arrival and proximity; situation-wise compliance is already high on both.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig3_Multi_neighbour_aggregation")


def fig4(rows):
    order = [(2, "q_DIM2"), (4, "q_DIM4"), (6, "qd_MOE_SE"),
             (8, "q_DIM8"), (10, "q_DIM10"), (12, "q_DIM12")]
    d = [x[0] for x in order]
    goal = [ms(pick(rows, p), "goal")[0] for _, p in order]
    prox = [ms(pick(rows, p), "prox")[0] for _, p in order]
    cre = [ms(pick(rows, p), "C_v2")[0] for _, p in order]
    sco = [score_row(r) for _, p in order for r in [ {**{"goal": ms(pick(rows, p), "goal")[0],
                                                         "prox": ms(pick(rows, p), "prox")[0],
                                                         "TO": 0.0}} ]]

    panels = [("(a)", goal, "Arrival rate (%)", "Arrival rate", False),
              ("(b)", prox, "Proximity rate (%)", "Proximity rate", True),
              ("(c)", cre, "Compliance (%)", "COLREGs PRIMARY v2", False),
              ("(d)", sco, "Outcome score", "Outcome score (1.5 goal - 6 prox)", False)]

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.0), sharex=True)
    for ax, (tag, y, ylab, title, lower_better) in zip(axes.ravel(), panels):
        ax.axvspan(6, 8, color=C["proposed"], alpha=0.07, lw=0, zorder=0)
        ax.plot(d, y, marker="o", ms=5, lw=1.5, color=C["proposed"],
                mfc="white", mec=C["proposed"], mew=1.4, zorder=3)
        for xi, yi in zip(d, y):
            ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points",
                        xytext=(0, 7), ha="center", fontsize=7.6, color=C["ink"])
        ax.set_ylabel(ylab)
        ax.set_title(title)
        lo, hi = min(y), max(y)
        span = max(hi - lo, 0.2)
        ax.set_ylim(lo - span * 0.30, hi + span * 0.35)
        ax.set_xticks(d)
        fsx.panel_tag(ax, tag)
        if lower_better:
            ax.annotate("lower is better", (0.98, 0.94), xycoords="axes fraction",
                        ha="right", fontsize=7.2, color=C["mute"])
    for ax in axes[1]:
        ax.set_xlabel(r"Message dimension  $|\mathbf{m}|$")
    fig.text(0.5, -0.02,
             "v11 sweep is on the shared hub (DIM6 = qd_MOE_SE), 3 seeds averaged. "
             "DIM6 is best on arrival and proximity; wider channels do not help.\n"
             "PRIMARY v2 compliance is flat (~96%) across widths and is not a selection criterion.",
             ha="center", fontsize=8.0, color=C["mute"])
    fig.tight_layout()
    fsx.save(fig, str(OUT), "Fig4_Message_dimensionality")


def fig5(rows):
    off, on = pick(rows, "qo_SE_COLREGSOFF"), pick(rows, "qd_MOE_SE")
    lab = ["COLREGs term\nOFF", "COLREGs term\nON"]
    col = [C["base"], C["proposed"]]
    fig = plt.figure(figsize=(11.0, 3.9))
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1.45, 1.0, 1.0], wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    sch.colregs_penalty(ax)
    ax.set_title("Directional non-compliance penalty", pad=4)
    fsx.panel_tag(ax, "(a)", dx=-0.02)

    p_off, p_on = ms(off, "prox"), ms(on, "prox")
    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [p_off[0], p_on[0]], col, "{:.2f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    ax.tick_params(axis="x", labelsize=8.2)
    fsx.panel_tag(ax, "(b)")

    c_off, c_on = ms(off, "C_v2"), ms(on, "C_v2")
    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [c_off[0], c_on[0]], col, "{:.1f}",
             ylabel="Compliance (%)", title="Overall COLREGs (PRIMARY v2)")
    ax.tick_params(axis="x", labelsize=8.2)
    fsx.panel_tag(ax, "(c)")

    fig.text(0.5, -0.10,
             "3 seeds. The COLREGs term raises PRIMARY v2 compliance (sit2/sit3 especially) "
             "and is the only ablation that moves C off the ceiling.\n"
             "Proximity is not improved by the term (OFF can look safer while violating stand-on/give-way). "
             "Pick training by C here, not by proximity.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig5_COLREGs_shaping")


def fig6(rows):
    early, delay = pick(rows, "ql_SE_START"), pick(rows, "qd_MOE_SE")
    lab = ["From start\n(0M)", "Delayed\n(9M)"]
    col = [C["base"], C["proposed"]]
    fig = plt.figure(figsize=(10.6, 3.9))
    gs = GridSpec(1, 3, figure=fig, wspace=0.36)

    p0, p9 = ms(early, "prox"), ms(delay, "prox")
    ax = fig.add_subplot(gs[0, 0])
    fsx.bars(ax, lab, [p0[0], p9[0]], col, "{:.2f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    ax.tick_params(axis="x", labelsize=8.4)
    fsx.panel_tag(ax, "(a)", dx=-0.16)

    c0, c9 = ms(early, "C_v2"), ms(delay, "C_v2")
    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [c0[0], c9[0]], col, "{:.1f}",
             ylabel="Compliance (%)", title="Overall COLREGs (PRIMARY v2)")
    ax.tick_params(axis="x", labelsize=8.4)
    fsx.panel_tag(ax, "(b)", dx=-0.16)

    g0, g9 = ms(early, "goal"), ms(delay, "goal")
    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [g0[0], g9[0]], col, "{:.1f}",
             ylabel="Arrival rate (%)", title="Arrival rate")
    ax.tick_params(axis="x", labelsize=8.4)
    fsx.panel_tag(ax, "(c)", dx=-0.16)

    fig.text(0.5, -0.11,
             "Both arms train 16M decisions; only the message-on time differs. "
             "Delayed (9M, hub) wins arrival and proximity; PRIMARY v2 C is tied.\n"
             "v11 does not reproduce a from-start rushing collapse on arrival.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig6_Communication_timing")


def _load_mixed():
    path = PAPER / "fig7" / "mixed_fleet_rx.csv"
    if not path.exists():
        return None
    by = {}
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = {k: float(v) for k, v in r.items()
                 if k not in ("tag", "mode", "nocomm", "group")}
            d["goal_eps"] = d["eps"] * d["goal"] / 100.0
            by.setdefault((int(float(r["nocomm"])), r["tag"]), {})[r["group"]] = d
    return by


def fig7(_rows):
    WEIGHT = {"goal": "eps", "coll": "eps", "to": "eps", "minsep": "eps",
              "colregs": "colregs_n", "fuel": "goal_eps", "head": "goal_eps",
              "length": "goal_eps"}
    by = _load_mixed()
    if by is None:
        print("  Fig7 skipped - mixed_fleet_rx.csv missing")
        return
    ks = sorted({k for k, _ in by})
    seeds = sorted({t for _, t in by})

    def fleet(groups, col):
        w = WEIGHT.get(col, "eps")
        num = sum(g[col] * g[w] for g in groups.values() if g.get(w, 0) > 0)
        den = sum(g[w] for g in groups.values() if g.get(w, 0) > 0)
        return num / den if den > 0 else float("nan")

    def series(col):
        mean, sd, dots = [], [], []
        for k in ks:
            vals = [fleet(by[(k, t)], col) for t in seeds if (k, t) in by]
            mean.append(float(np.mean(vals)))
            sd.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
            dots.append(vals)
        return np.array(mean), np.array(sd), dots

    fig = plt.figure(figsize=(10.4, 7.2))
    gs = GridSpec(2, 2, figure=fig, hspace=0.62, wspace=0.30)
    ax = fig.add_subplot(gs[0, 0])
    sch.fleet_composition(ax)
    ax.set_title("Fleet composition", pad=4)
    fsx.panel_tag(ax, "(a)", dx=-0.02)

    spec = [("(b)", "coll", "Proximity rate (%)", "Proximity rate", gs[0, 1]),
            ("(c)", "colregs", "Compliance (%)", "COLREGs (step-legacy)", gs[1, 0]),
            ("(d)", "minsep", "Minimum separation (m)", "Minimum separation", gs[1, 1])]
    for tag, col, ylab, title, cell in spec:
        ax = fig.add_subplot(cell)
        m, s, dots = series(col)
        ax.plot(ks, m, marker="o", ms=4.5, lw=1.5, color=C["proposed"],
                mfc="white", mec=C["proposed"], mew=1.3, zorder=3)
        for k, ds in zip(ks, dots):
            ax.plot([k] * len(ds), ds, marker=".", ls="none", ms=3.4,
                    color=C["mute"], alpha=0.75, zorder=2)
        ax.set_xticks(ks)
        ax.set_xlabel("Rx-only vessels (of 16)")
        ax.set_ylabel(ylab)
        ax.set_title(title, pad=30)
        fsx.panel_tag(ax, tag, dy=1.20)
        sec = ax.secondary_xaxis("top")
        sec.set_xticks(ks)
        sec.set_xticklabels([str(16 - k) for k in ks], fontsize=7.6)
        sec.set_xlabel("Tx-capable vessels", fontsize=8.0, labelpad=2)

    fig.text(0.5, -0.035,
             f"v11 mixed-fleet CSV, {len(seeds)} seeds, sample-weighted fleet. "
             "Panel (b) is the CSV proximity/overlap rate (not PRIMARY v2). "
             "Panel (c) is still step-legacy C.\n"
             "Grey dots are individual seeds.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig7_Heterogeneous_fleet")


def fig8(_rows):
    import re
    fig8_re = re.compile(
        r"arm=(\w+)\s+path=(\w+).*?goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%\s+TO=\s*([\d.]+)%"
        r".*?fuel=\s*([\d.]+)\s+headTravel=\s*([\d.]+)deg\s+minSep=\s*([\d.]+)m\s+len=\s*([\d.]+)"
    )
    recs = {}
    for p in sorted((PAPER / "fig8").glob("hub_s42_*.log")):
        t = p.read_text(encoding="utf-8", errors="replace")
        m = fig8_re.search(t)
        if not m:
            continue
        arm, path, goal, vc, oc, to, fuel, head, ms_, ln = m.groups()
        recs[(arm, path)] = dict(goal=float(goal), prox=float(vc), to=float(to),
                                 fuel=float(fuel), head=float(head), minsep=float(ms_),
                                 length=float(ln))
    order = [("OFF", "direct"), ("OFF", "astar"), ("ON", "direct"), ("ON", "astar")]
    lab = ["OFF\ndirect", "OFF\nA*", "ON\ndirect", "ON\nA*"]
    col = [C["base"], C["base"], C["proposed"], C["proposed"]]
    if len(recs) < 4:
        print("  Fig8 skipped - missing hub_s42 logs")
        return

    fig = plt.figure(figsize=(11.0, 6.4))
    gs = GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)

    def vals(key):
        return [recs[k][key] for k in order]

    ax = fig.add_subplot(gs[0, 0])
    fsx.bars(ax, lab, vals("prox"), col, "{:.1f}",
             ylabel="Proximity rate (%)", title="Proximity rate")
    fsx.panel_tag(ax, "(a)", dx=-0.14)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, vals("goal"), col, "{:.1f}",
             ylabel="Arrival rate (%)", title="Arrival rate")
    fsx.panel_tag(ax, "(b)", dx=-0.14)

    ax = fig.add_subplot(gs[1, 0])
    fsx.bars(ax, lab, vals("to"), col, "{:.1f}",
             ylabel="Timeout (%)", title="Timeout")
    fsx.panel_tag(ax, "(c)", dx=-0.14)

    ax = fig.add_subplot(gs[1, 1])
    fsx.bars(ax, lab, vals("minsep"), col, "{:.1f}",
             ylabel="Min separation (m)", title="Minimum separation")
    fsx.panel_tag(ax, "(d)", dx=-0.14)

    fig.text(0.5, -0.04,
             "Hub qd_MOE_SE s42 only. Fig8 eval includes timeout (~35%), so arrival is not the "
             "Fig1-6 90%+ protocol. Proximity here is vColl among all ended outcomes including TO.\n"
             "A* raises fuel/heading/length vs direct and does not raise arrival. "
             "PRIMARY v2 C was not ported to this eval.",
             ha="center", fontsize=8.0, color=C["mute"])
    fsx.save(fig, str(OUT), "Fig8_Global_path")


FIGS = {1: fig1, 2: fig2, 3: fig3, 4: fig4, 5: fig5, 6: fig6, 7: fig7, 8: fig8}


def main():
    fsx.apply()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    want = [int(a) for a in sys.argv[1:]] or list(FIGS)
    for n in want:
        print(f"Fig{n} ...")
        FIGS[n](rows)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
