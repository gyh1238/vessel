"""논문 그림 공통 스타일 — fig1_8_reorganization_plan.md 의 '공통 시각화 원칙' 구현.

원칙
  * 조건 색·순서·마커를 전 그림에서 통일한다.
  * 시드가 있는 조건은 개별 점을 함께 찍는다. 시드가 하나면 점 하나만 찍고
    가짜 오차막대를 만들지 않는다.
  * 얇은 선, 볼드 절제, top/right spine 제거 (기존 paper_style.py 계승).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


# ── 조건 색 — 전 그림 공통 ────────────────────────────────────────────────
# 회색 = 기준선/비교대상, 짙은 청색 = 논문 제안 설정, 나머지는 보조 조건.
C = {
    'base':     '#9aa6b2',   # 통신 OFF · nearest-1 · 규정항 없음 · 처음부터
    'proposed': '#2e6f9e',   # 제안 설정 (공유 MoE + 통신 ON + 4척 + 9M)
    'alt1':     '#d59b5c',   # 분리·얇게
    'alt2':     '#a4626c',   # 분리·두껍게
    'accent':   '#3f7f5f',   # 강조선 (기준선 표시 등)
    'ink':      '#2b2b2b',
    'mute':     '#8a8a8a',
}

BAR_KW = dict(edgecolor='#3a3a3a', linewidth=0.7, zorder=3)
DOT_KW = dict(marker='o', linestyle='none', ms=3.6, mfc='white',
              mec='#3a3a3a', mew=0.8, zorder=5)


def apply():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'font.size': 9.5,
        'axes.titlesize': 10.0, 'axes.titleweight': 'normal',
        'axes.labelsize': 9.5, 'axes.labelweight': 'normal',
        'legend.fontsize': 8.8, 'legend.frameon': False,
        'axes.grid': True, 'grid.alpha': 0.15, 'grid.linewidth': 0.5,
        'axes.axisbelow': True, 'axes.linewidth': 0.8,
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.direction': 'out', 'ytick.direction': 'out',
        'xtick.major.width': 0.8, 'ytick.major.width': 0.8,
        'xtick.labelsize': 9.0, 'ytick.labelsize': 9.0,
        'figure.dpi': 110, 'savefig.dpi': 300,
        'pdf.fonttype': 42, 'ps.fonttype': 42,
    })


def panel_tag(ax, tag, dx=-0.06, dy=1.06):
    """(a) (b) … 패널 라벨. 좌상단 축 바깥."""
    ax.text(dx, dy, tag, transform=ax.transAxes, fontsize=10.5,
            fontweight='bold', va='bottom', ha='left', color=C['ink'])


def bars(ax, labels, values, colors, fmt='{:.2f}', err=None, dots=None,
         ylabel=None, title=None, pad_top=0.22, width=0.62, annotate=True):
    """막대 + 값 라벨 (+ 오차막대 · 개별 시드 점).

    err  : 시드 표준편차. None 이면 오차막대 없음(시드 1개 조건 포함).
    dots : 조건별 개별 시드 값 리스트. 값을 아는 조건만 채운다.
    """
    x = np.arange(len(labels))
    ax.bar(x, values, width=width, color=colors, **BAR_KW)
    if err is not None:
        e = [0 if v is None else v for v in err]
        mask = [v is not None for v in err]
        ax.errorbar(x[mask], np.asarray(values)[mask], yerr=np.asarray(e)[mask],
                    fmt='none', ecolor='#3a3a3a', elinewidth=0.9, capsize=3, zorder=4)
    if dots is not None:
        for xi, ds in zip(x, dots):
            if ds:
                ax.plot([xi] * len(ds), ds, **DOT_KW)
    top = max(v + (e_ or 0) for v, e_ in zip(values, (err or [0] * len(values))))
    if annotate:
        for xi, v in zip(x, values):
            ax.annotate(fmt.format(v), (xi, v), textcoords='offset points',
                        xytext=(0, 3.5), ha='center', fontsize=8.8, color=C['ink'])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, top * (1 + pad_top))
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return x


def grouped_bars(ax, group_labels, series, colors, ylabel=None, title=None,
                 fmt='{:.0f}', width=0.36, pad_top=0.22, annotate=True):
    """조건 2개를 상황별로 나란히. series = [(name, values), ...]"""
    x = np.arange(len(group_labels))
    n = len(series)
    off = (np.arange(n) - (n - 1) / 2) * width
    top = 0
    for k, (name, vals) in enumerate(series):
        ax.bar(x + off[k], vals, width=width, color=colors[k], label=name, **BAR_KW)
        top = max(top, max(vals))
        if annotate:
            for xi, v in zip(x + off[k], vals):
                ax.annotate(fmt.format(v), (xi, v), textcoords='offset points',
                            xytext=(0, 3), ha='center', fontsize=8.0, color=C['ink'])
    ax.set_xticks(x)
    ax.set_xticklabels(group_labels)
    ax.set_ylim(0, top * (1 + pad_top))
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.legend(loc='upper left', ncol=n, handlelength=1.2, columnspacing=1.0)


def rel_change(ax, labels, base_vals, new_vals, ylabel='Change vs baseline (%)',
               title=None, colors=None):
    """기준 대비 상대 변화(%). 개선이 음수인 지표(연료·조타)에 씀."""
    d = [(n - b) / b * 100.0 for b, n in zip(base_vals, new_vals)]
    x = np.arange(len(labels))
    cols = colors or [C['proposed']] * len(labels)
    ax.bar(x, d, width=0.5, color=cols, **BAR_KW)
    ax.axhline(0, color='#3a3a3a', lw=0.9, zorder=4)
    for xi, v, b, n in zip(x, d, base_vals, new_vals):
        va, dy = ('top', -4) if v < 0 else ('bottom', 4)
        ax.annotate(f'{v:+.1f}%', (xi, v), textcoords='offset points',
                    xytext=(0, dy), ha='center', va=va, fontsize=8.8, color=C['ink'])
        ax.annotate(f'{b:g} → {n:g}', (xi, 0), textcoords='offset points',
                    xytext=(0, 6 if v < 0 else -14), ha='center', fontsize=7.6,
                    color=C['mute'])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    lo, hi = min(d + [0]), max(d + [0])
    span = max(abs(lo), abs(hi))
    ax.set_ylim(lo - span * 0.45, hi + span * 0.45)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)


def embed_png(ax, path, note=None):
    """기존 렌더 그림을 패널로 삽입.

    학습곡선은 원자료(_data)가 저장소에 없어 다시 그릴 수 없으므로, 이미 만들어진
    PNG 를 그대로 넣는다. 벡터가 아니라 래스터로 들어간다는 점을 문서에 남길 것.
    """
    import os
    if not os.path.exists(path):
        ax.text(0.5, 0.5, 'learning curve\n(source PNG not found)', ha='center',
                va='center', transform=ax.transAxes, fontsize=9, color=C['mute'])
        ax.set_axis_off()
        return False
    ax.imshow(plt.imread(path))
    ax.set_axis_off()
    if note:
        ax.text(0.5, -0.02, note, transform=ax.transAxes, ha='center', va='top',
                fontsize=7.6, color=C['mute'])
    return True


def save(fig, outdir, name):
    import os
    os.makedirs(outdir, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(outdir, f'{name}.{ext}'), bbox_inches='tight')
    plt.close(fig)
    print(f'  {name}.png / .pdf')
