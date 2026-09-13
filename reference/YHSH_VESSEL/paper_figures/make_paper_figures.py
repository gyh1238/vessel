"""논문용 최종 그림 생성 — fig1_8_reorganization_plan.md 구현.

흩어져 있던 지표별 개별 그래프를, 그림마다 하나의 설계 질문에 답하는 복합 그림으로
다시 묶는다. 출력은 이 폴더에 Fig1~Fig8 의 png/pdf.

    python make_paper_figures.py            # 전부
    python make_paper_figures.py 2 5        # 일부만

── 수치 출처 ────────────────────────────────────────────────────────────────
Fig1·3·4  각 그림 폴더의 description.txt (고정정책 완주 평가값)
Fig2      위 + 파라미터 수는 config/networks 실측
Fig5      계획서가 지정한 제안구조 3시드 재측정값 (qo_SE_COLREGSOFF / qd_MOE_SE)
Fig6      납품 그림 실측 + RUNS.md 요약
Fig7      Fig7_통통배/RawData/EP_by_config.csv 를 직접 재집계 (유일하게 원자료가 있음)

⚠️ 학습곡선(Fig1a·Fig6a)은 원자료 Python/plotting/_data 가 저장소에 없어 다시 그릴 수
   없다. 이미 렌더된 PNG 를 패널로 삽입한다(래스터). _data 를 확보하면 벡터로 교체할 것.
⚠️ 개별 시드 점은 시드별 값이 _data 에만 있어 Fig7 에서만 표시한다. 나머지 그림에는
   가짜 점을 만들지 않는다(계획서 공통 원칙).
"""
import os
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import figstyle as fsx
from figstyle import C
import schematics as sch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # YHSH_VESSEL/
OUT = HERE

SIT4 = ['Head-On', 'Give-Way', 'Overtaking', 'Stand-On']


# ══════════════════════════════════════════════════════════════════════════
# Fig.1 — Communication necessity
# ══════════════════════════════════════════════════════════════════════════
def fig1():
    off = dict(arrival=54.4, coll=2.77, colregs=48.4, fuel=816, head=1930)
    on = dict(arrival=55.6, coll=1.83, colregs=52.3, fuel=802, head=1852)
    sit_off, sit_on = [99, 53, 76, 21], [100, 65, 70, 30]
    lab = ['Comm OFF', 'Comm ON']
    col = [C['base'], C['proposed']]

    # 학습곡선은 넣지 않는다. 막대는 고정정책 완주 평가값이고 곡선은 학습 로그를 다시
    # 계산한 값이라 추정량이 다르다 — 한 그림에 섞으면 같은 수치처럼 읽힌다.
    fig = plt.figure(figsize=(11.0, 6.2))
    gs = GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.34)

    ax = fig.add_subplot(gs[0, 0])
    fsx.bars(ax, lab, [off['coll'], on['coll']], col, '{:.2f}',
             ylabel='Collision rate (%)', title='Collision rate')
    ax.annotate('-34%', xy=(1, on['coll']), xytext=(0, 22), textcoords='offset points',
                ha='center', fontsize=9, color=C['accent'], fontweight='bold')
    fsx.panel_tag(ax, '(a)', dx=-0.14)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [off['arrival'], on['arrival']], col, '{:.1f}',
             ylabel='Arrival rate (%)', title='Arrival rate')
    fsx.panel_tag(ax, '(b)', dx=-0.14)

    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [off['colregs'], on['colregs']], col, '{:.1f}',
             ylabel='Compliance (%)', title='Overall COLREGs compliance')
    fsx.panel_tag(ax, '(c)', dx=-0.14)

    ax = fig.add_subplot(gs[1, :2])
    fsx.grouped_bars(ax, SIT4, [('Comm OFF', sit_off), ('Comm ON', sit_on)], col,
                     ylabel='Compliance (%)', title='COLREGs compliance by encounter type',
                     fmt='{:.0f}')
    ax.set_ylim(0, 132)
    fsx.panel_tag(ax, '(d)', dx=-0.07)

    ax = fig.add_subplot(gs[1, 2])
    fsx.rel_change(ax, ['Fuel', 'Heading\ntravel'], [off['fuel'], off['head']],
                   [on['fuel'], on['head']], title='Efficiency vs Comm OFF')
    fsx.panel_tag(ax, '(e)', dx=-0.14)

    fig.text(0.5, -0.035,
             'All values are fixed-policy full-run evaluations, three seeds per arm.  '
             'Minimum separation and episode length are reported in the text.  '
             'Per-seed values are unavailable, so no seed dots are drawn.\n'
             'Communication mainly improves safety and coordination in interaction-dependent '
             'crossing encounters rather than simply increasing arrival rate.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig1_Communication_necessity')


# ══════════════════════════════════════════════════════════════════════════
# Fig.2 — Shared-perception MoE architecture
# ══════════════════════════════════════════════════════════════════════════
def fig2():
    lab = ['Single\nnetwork', 'Separate\nthin', 'Separate\nfull', 'Shared\n(proposed)']
    col = [C['base'], C['alt1'], C['alt2'], C['proposed']]
    params = [369131, 363004, 1826719, 511543]
    coll = [6.07, 9.50, 6.40, 1.83]
    arrival = [57.2, 33.8, 55.3, 55.6]

    fig = plt.figure(figsize=(11.6, 7.4))
    gs = GridSpec(3, 2, figure=fig, width_ratios=[1.32, 1.0],
                  hspace=0.52, wspace=0.22)

    ax = fig.add_subplot(gs[:, 0])
    sch.architectures(ax)
    ax.set_title('Four architectures compared', pad=4)
    fsx.panel_tag(ax, '(a)', dx=0.0, dy=1.005)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [p / 1e3 for p in params], col, '{:.0f}K',
             ylabel='Parameters (thousands)', title='Parameter count')
    ax.tick_params(axis='x', labelsize=7.6)
    fsx.panel_tag(ax, '(b)')

    ax = fig.add_subplot(gs[1, 1])
    fsx.bars(ax, lab, coll, col, '{:.2f}',
             ylabel='Collision rate (%)', title='Collision rate')
    ax.tick_params(axis='x', labelsize=7.6)
    fsx.panel_tag(ax, '(c)')

    ax = fig.add_subplot(gs[2, 1])
    fsx.bars(ax, lab, arrival, col, '{:.1f}',
             ylabel='Arrival rate (%)', title='Arrival rate')
    ax.tick_params(axis='x', labelsize=7.6)
    fsx.panel_tag(ax, '(d)')

    fig.text(0.5, -0.015,
             'Separate-thin is a single seed (no error bar shown; not used for effect-size claims).  '
             'Single-network arrival includes one run that converged to a\nrushing policy '
             '(12.5% collision); excluding it gives 53.8%.  '
             'Separate-full metrics come from the same completed runs used in Fig.4 (dim 6) and Fig.5.\n'
             'The physical scene is a shared perception problem, whereas COLREGs obligations create '
             'situation-specific decision problems.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig2_MoE_architecture')


# ══════════════════════════════════════════════════════════════════════════
# Fig.3 — Multi-neighbour aggregation
# ══════════════════════════════════════════════════════════════════════════
def fig3():
    lab = ['Nearest-1', 'Nearest-4']
    col = [C['base'], C['proposed']]
    sit_1, sit_4 = [97.2, 56.3, 64.1, 20.4], [99.6, 64.5, 70.2, 30.0]

    fig = plt.figure(figsize=(10.4, 6.3))
    gs = GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.28)

    ax = fig.add_subplot(gs[0, 0])
    sch.aggregation(ax)
    ax.set_title('Message aggregation', pad=4)
    fsx.panel_tag(ax, '(a)', dx=-0.02)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [3.43, 1.83], col, '{:.2f}',
             ylabel='Collision rate (%)', title='Collision rate')
    ax.annotate('-47%', xy=(1, 1.83), xytext=(0, 22), textcoords='offset points',
                ha='center', fontsize=9, color=C['accent'], fontweight='bold')
    fsx.panel_tag(ax, '(b)', dx=-0.12)

    ax = fig.add_subplot(gs[1, 0])
    fsx.grouped_bars(ax, SIT4, [('Nearest-1', sit_1), ('Nearest-4', sit_4)], col,
                     ylabel='Compliance (%)', title='Compliance by encounter type',
                     fmt='{:.1f}')
    ax.set_ylim(0, 128)
    ax.tick_params(axis='x', labelsize=7.8)
    fsx.panel_tag(ax, '(c)')

    ax = fig.add_subplot(gs[1, 1])
    fsx.rel_change(ax, ['Fuel', 'Heading\ntravel'], [836, 1990], [802, 1852],
                   ylabel='Change vs nearest-1 (%)',
                   title='Efficiency vs nearest-1')
    fsx.panel_tag(ax, '(d)', dx=-0.12)

    fig.text(0.5, -0.03,
             'Arrival rate is 55.0% → 55.6% and is reported in the text.  '
             'Overall compliance 45.6% → 52.3%.\nA pairwise communication bottleneck fails when '
             'resolving one encounter changes the geometry of another.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig3_Multi_neighbour_aggregation')


# ══════════════════════════════════════════════════════════════════════════
# Fig.4 — Message dimensionality
# ══════════════════════════════════════════════════════════════════════════
def fig4():
    d = [2, 4, 6, 8, 10, 12]
    arrival = [52.2, 51.9, 55.3, 56.4, 52.5, 53.3]
    coll = [5.87, 8.20, 6.40, 4.00, 5.70, 4.87]
    colregs = [46.8, 42.5, 48.7, 46.1, 42.9, 53.3]
    score = [22.1, 8.7, 25.5, 40.7, 23.7, 29.9]

    panels = [('(a)', arrival, 'Arrival rate (%)', 'Arrival rate', False),
              ('(b)', coll, 'Collision rate (%)', 'Collision rate', True),
              ('(c)', colregs, 'Compliance (%)', 'COLREGs compliance', False),
              ('(d)', score, 'Outcome score', 'Outcome score', False)]

    fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.0), sharex=True)
    for ax, (tag, y, ylab, title, lower_better) in zip(axes.ravel(), panels):
        ax.axvspan(6, 8, color=C['proposed'], alpha=0.07, lw=0, zorder=0)
        ax.plot(d, y, marker='o', ms=5, lw=1.5, color=C['proposed'],
                mfc='white', mec=C['proposed'], mew=1.4, zorder=3)
        for xi, yi in zip(d, y):
            ax.annotate(f'{yi:g}', (xi, yi), textcoords='offset points',
                        xytext=(0, 7), ha='center', fontsize=7.6, color=C['ink'])
        ax.set_ylabel(ylab)
        ax.set_title(title)
        lo, hi = min(y), max(y)
        ax.set_ylim(lo - (hi - lo) * 0.30, hi + (hi - lo) * 0.35)
        ax.set_xticks(d)
        fsx.panel_tag(ax, tag)
        if lower_better:
            ax.annotate('lower is better', (0.98, 0.94), xycoords='axes fraction',
                        ha='right', fontsize=7.2, color=C['mute'])
    for ax in axes[1]:
        ax.set_xlabel(r'Message dimension  $|\mathbf{m}|$')
    axes[0, 0].annotate('moderate-width\nregion', (7, axes[0, 0].get_ylim()[0]),
                        textcoords='offset points', xytext=(0, 8), ha='center',
                        fontsize=7.0, color=C['proposed'])

    fig.text(0.5, -0.02,
             'This sweep was run on the full-width separated MoE, not on the proposed shared '
             'architecture.  Per-seed values are unavailable, so no error bars are drawn.\n'
             'Very small messages become an information bottleneck, whereas increasing latent '
             'width beyond a moderate regime gives no consistent gain.',
             ha='center', fontsize=8.0, color=C['mute'])
    fig.tight_layout()
    fsx.save(fig, OUT, 'Fig4_Message_dimensionality')


# ══════════════════════════════════════════════════════════════════════════
# Fig.5 — COLREGs shaping
# ══════════════════════════════════════════════════════════════════════════
def fig5():
    lab = ['COLREGs term\nOFF', 'COLREGs term\nON']
    col = [C['base'], C['proposed']]

    fig = plt.figure(figsize=(11.0, 3.9))
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1.45, 1.0, 1.0], wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    sch.colregs_penalty(ax)
    ax.set_title('Directional non-compliance penalty', pad=4)
    fsx.panel_tag(ax, '(a)', dx=-0.02)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [6.43, 1.83], col, '{:.2f}',
             ylabel='Collision rate (%)', title='Collision rate')
    ax.tick_params(axis='x', labelsize=8.2)
    fsx.panel_tag(ax, '(b)')

    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [31.4, 52.3], col, '{:.1f}',
             ylabel='Compliance (%)', title='Overall COLREGs compliance')
    ax.tick_params(axis='x', labelsize=8.2)
    fsx.panel_tag(ax, '(c)')

    fig.text(0.5, -0.10,
             'Matched proposed-architecture comparison, three seeds per arm '
             '(OFF: qo_SE_COLREGSOFF_s42/43/44,  ON: qd_MOE_SE_s42/43/44).  '
             'Per-seed dots require the source logs.\n'
             'The COLREGs term acts as a domain prior that breaks symmetric but mutually '
             'incompatible avoidance choices, improving both rule compliance and collision safety.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig5_COLREGs_shaping')


# ══════════════════════════════════════════════════════════════════════════
# Fig.6 — Communication introduction timing
# ══════════════════════════════════════════════════════════════════════════
def fig6():
    lab = ['From start\n(0M)', 'Delayed\n(9M)']
    col = [C['base'], C['proposed']]

    # 학습곡선 없음 — Fig1 과 같은 이유(추정량이 다름). 통신 투입 시점 자체는 x축 라벨과
    # 캡션이 전달하고, 그림은 결과 비교만 한다.
    fig = plt.figure(figsize=(10.6, 3.9))
    gs = GridSpec(1, 3, figure=fig, wspace=0.36)

    ax = fig.add_subplot(gs[0, 0])
    fsx.bars(ax, lab, [6.53, 1.83], col, '{:.2f}',
             ylabel='Collision rate (%)', title='Collision rate')
    ax.tick_params(axis='x', labelsize=8.4)
    fsx.panel_tag(ax, '(a)', dx=-0.16)

    ax = fig.add_subplot(gs[0, 1])
    fsx.bars(ax, lab, [46.4, 52.3], col, '{:.1f}',
             ylabel='Compliance (%)', title='Overall COLREGs compliance')
    ax.tick_params(axis='x', labelsize=8.4)
    fsx.panel_tag(ax, '(b)', dx=-0.16)

    ax = fig.add_subplot(gs[0, 2])
    fsx.bars(ax, lab, [61.3, 55.6], col, '{:.1f}', err=[14.5, 1.4],
             ylabel='Arrival rate (%)',
             title='Arrival rate — mean ± seed spread')
    ax.tick_params(axis='x', labelsize=8.4)
    ax.annotate('±14.5', xy=(0, 61.3 + 14.5), xytext=(15, 0),
                textcoords='offset points', fontsize=8.0, color='#8d3b3b', va='center')
    ax.annotate('±1.4', xy=(1, 55.6 + 1.4), xytext=(15, 0),
                textcoords='offset points', fontsize=8.0, color=C['accent'], va='center')
    fsx.panel_tag(ax, '(c)', dx=-0.16)

    fig.text(0.5, -0.11,
             'Both arms train for the full 16M decisions; the only difference is when messages '
             'start flowing.  Delayed wins collision and compliance on all three seeds.\n'
             'Arrival mean favours from-start, but its seed spread is ten times larger — one seed '
             'converged to a rushing policy (timeout 15.6%, collisions x3.7).\n'
             'Establishing a stable local control policy before coupling agents through learned '
             'communication produces a safer, far less seed-sensitive solution.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig6_Communication_timing')


# ══════════════════════════════════════════════════════════════════════════
# Fig.7 — Heterogeneous communication fleet   (원자료에서 직접 재집계)
# ══════════════════════════════════════════════════════════════════════════
WEIGHT = {'goal': 'eps', 'coll': 'eps', 'to': 'eps', 'minsep': 'eps',
          'colregs': 'colregs_n', 'fuel': 'goal_eps', 'head': 'goal_eps',
          'length': 'goal_eps'}


def _load_mixed():
    path = os.path.join(ROOT, 'Fig7_통통배', 'RawData', 'EP_by_config.csv')
    if not os.path.exists(path):
        return None
    by = {}
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d = {k: float(v) for k, v in r.items()
                 if k not in ('tag', 'mode', 'nocomm', 'group')}
            d['goal_eps'] = d['eps'] * d['goal'] / 100.0
            by.setdefault((int(r['nocomm']), r['tag']), {})[r['group']] = d
    return by


def _fleet(groups, col):
    """한 시드의 두 무리를 표본 수 가중으로 합쳐 함대 전체 값 하나로."""
    w = WEIGHT.get(col, 'eps')
    num = sum(g[col] * g[w] for g in groups.values() if g.get(w, 0) > 0)
    den = sum(g[w] for g in groups.values() if g.get(w, 0) > 0)
    return num / den if den > 0 else float('nan')


def fig7():
    by = _load_mixed()
    if by is None:
        print('  Fig7 건너뜀 — RawData/EP_by_config.csv 없음')
        return
    ks = sorted({k for k, _ in by})
    seeds = sorted({t for _, t in by})

    def series(col):
        mean, sd, dots = [], [], []
        for k in ks:
            vals = [_fleet(by[(k, t)], col) for t in seeds if (k, t) in by]
            mean.append(float(np.mean(vals)))
            sd.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
            dots.append(vals)
        return np.array(mean), np.array(sd), dots

    fig = plt.figure(figsize=(10.4, 7.2))
    gs = GridSpec(2, 2, figure=fig, hspace=0.62, wspace=0.30)

    ax = fig.add_subplot(gs[0, 0])
    sch.fleet_composition(ax)
    ax.set_title('Fleet composition', pad=4)
    fsx.panel_tag(ax, '(a)', dx=-0.02)

    spec = [('(b)', 'coll', 'Collision rate (%)', 'Collision rate', gs[0, 1]),
            ('(c)', 'colregs', 'Compliance (%)', 'COLREGs compliance', gs[1, 0]),
            ('(d)', 'minsep', 'Minimum separation (m)', 'Minimum separation', gs[1, 1])]
    for tag, col, ylab, title, cell in spec:
        ax = fig.add_subplot(cell)
        m, s, dots = series(col)
        lo = np.maximum(m - s, 0) if col in ('coll', 'colregs') else m - s
        ax.fill_between(ks, lo, m + s, color=C['proposed'], alpha=0.13, lw=0, zorder=1)
        ax.plot(ks, m, marker='o', ms=4.5, lw=1.5, color=C['proposed'],
                mfc='white', mec=C['proposed'], mew=1.3, zorder=3)
        for k, ds in zip(ks, dots):
            ax.plot([k] * len(ds), ds, marker='.', ls='none', ms=3.4,
                    color=C['mute'], alpha=0.75, zorder=2)
        ax.set_xticks(ks)
        ax.set_xlabel('Rx-only vessels (of 16)')
        ax.set_ylabel(ylab)
        ax.set_title(title, pad=30)
        fsx.panel_tag(ax, tag, dy=1.20)
        sec = ax.secondary_xaxis('top')
        sec.set_xticks(ks)
        sec.set_xticklabels([str(16 - k) for k in ks], fontsize=7.6)
        sec.set_xlabel('Tx-capable vessels', fontsize=8.0, labelpad=2)

    fig.text(0.5, -0.035,
             f'Recomputed directly from Fig7 RawData ({len(seeds)} seeds: {", ".join(seeds)}), '
             'sample-size weighted across the communicating and non-communicating groups.\n'
             'CAUTION: these values do not match the previously delivered Fig7 (compliance 51.4–52.3%, '
             'collision 1.08–2.60%). Provenance must be resolved before quantitative claims.\n'
             'Grey dots are individual seeds; the band is ±1 s.d. across seeds.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig7_Heterogeneous_fleet')


# ══════════════════════════════════════════════════════════════════════════
# Fig.8 — Global A* + local cooperative policy   (재평가 대기)
# ══════════════════════════════════════════════════════════════════════════
SRC_FIG8 = 'Fig8_지도&DT(예정).pdf.png'
# 원본 3309x2062 에서 세 번째 칸('placeholder' 블록)이 차지하는 픽셀 상자 (실측).
PLACEHOLDER_BOX = (1650, 1128, 3300, 1995)


def fig8():
    """기존 `Fig8_지도&DT(예정)` 을 되살린 구성.

    그 그림은 (a) 실해안선 A* 경로 → 확대 콜아웃 → (b) 회랑 항적 으로 실제 해역과
    시뮬레이터를 잇는다. 계획서가 integration figure 에 요구한 (a)(b) 를 이미 만족하고,
    특히 (a) 의 빨간 콜아웃이 두 패널을 물리적으로 연결한다 — 잘라 내면 그 연결이
    끊기므로 원본을 통째로 쓰고 세 번째 칸만 교체한다.

    항적 데이터(corridor_traj)가 저장소에 없어 (b) 는 다시 그릴 수 없다.
    정량 패널은 재평가 뒤 (c) 자리에 넣으면 된다.
    """
    src = os.path.join(ROOT, 'Fig8_A_', SRC_FIG8)
    if not os.path.exists(src):
        print(f'  Fig8 건너뜀 — {SRC_FIG8} 없음')
        return
    from PIL import Image, ImageDraw
    im = Image.open(src).convert('RGB')
    W, H = im.size
    ImageDraw.Draw(im).rectangle(PLACEHOLDER_BOX, fill=(0, 0, 0))   # 자리표시자 지움

    fig = plt.figure(figsize=(11.6, 7.8), facecolor='white')
    ax = fig.add_axes([0.0, 0.10, 1.0, 0.90])
    ax.imshow(im)
    ax.set_axis_off()

    # 지운 자리에 (c) 예정 패널을 같은 위치로 올린다 (검은 배경에 맞춘 색).
    x0, y0, x1, y1 = PLACEHOLDER_BOX
    pad = 40
    axC = ax.inset_axes([(x0 + pad) / W, 1 - (y1 - pad) / H,
                         (x1 - x0 - 2 * pad) / W, (y1 - y0 - 2 * pad) / H])
    axC.set_facecolor('none')
    axC.set_xticks([]); axC.set_yticks([]); axC.grid(False)
    for sp in axC.spines.values():
        sp.set_visible(True); sp.set_linestyle((0, (5, 5)))
        sp.set_color('#7d8a97'); sp.set_linewidth(1.1)
    axC.text(0.5, 0.74, '(c)  Collision and arrival rate', ha='center', va='center',
             transform=axC.transAxes, fontsize=11, color='#e8edf2')
    axC.text(0.5, 0.50, 'Direct vs A*  x  Comm OFF / ON\nall 320 pairs   ·   blocked 148 pairs',
             ha='center', va='center', transform=axC.transAxes, fontsize=9.2,
             color='#aab6c2', linespacing=1.7)
    axC.text(0.5, 0.24, 'pending re-evaluation', ha='center', va='center',
             transform=axC.transAxes, fontsize=10, color='#e0a3a3', fontweight='bold')

    fig.text(0.5, 0.005,
             'Panels (a) and (b) are the existing Fig8 composition; the callout in (a) marks the '
             'corridor whose tracks are shown in (b).  (a) is a coastline occupancy map built from\n'
             'Natural Earth polygons, not an AIS traffic digital twin.  Panel (c) awaits the rerun '
             'specified in the reorganization plan: proposed checkpoint (qd_MOE_SE), ring = 0.7, '
             'direct vs A*,\ncommunication OFF vs ON, reporting all 320 spawn-goal pairs and the 148 '
             'blocked pairs separately (172 / 320 already have a clear direct line).  '
             'The corridor tracks in (b)\ncome from checkpoint ql_SE_START_s42, not the proposed '
             'qd_MOE_SE.  This is zero-shot waypoint integration: the policy was trained on direct '
             'goals, not retrained for waypoints.',
             ha='center', fontsize=8.0, color=C['mute'])
    fsx.save(fig, OUT, 'Fig8_Astar_integration')


# ══════════════════════════════════════════════════════════════════════════
FIGS = {1: fig1, 2: fig2, 3: fig3, 4: fig4, 5: fig5, 6: fig6, 7: fig7, 8: fig8}


def main():
    fsx.apply()
    want = [int(a) for a in sys.argv[1:]] or sorted(FIGS)
    print(f'출력 → {OUT}')
    for n in want:
        print(f'Fig{n}')
        FIGS[n]()


if __name__ == '__main__':
    main()
