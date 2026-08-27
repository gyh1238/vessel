"""그림 안에 들어가는 개념도 — 계획서가 요구한 schematic panel 들.

전부 matplotlib 도형으로 그린다(외부 이미지 없음).
"""
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Wedge, Rectangle
from figstyle import C

SIT = ['None', 'Head-On', 'Stand-On', 'Give-Way', 'Overtaking']


def _box(ax, x, y, w, h, label, fc, ec='#3a3a3a', fs=7.2, lw=0.8, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.008,rounding_size=0.02',
                                facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))
    ax.text(x + w / 2, y + h / 2, label, ha='center', va='center', fontsize=fs,
            zorder=4, color=tc or C['ink'], linespacing=1.15)


def _arrow(ax, p, q, lw=0.9, color='#5a5a5a', shrink=1.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=7,
                                 linewidth=lw, color=color, zorder=2,
                                 shrinkA=shrink, shrinkB=shrink))


# ── Fig2 (a) 네 구조 ──────────────────────────────────────────────────────
def architectures(ax):
    """레이더 인식부를 결정부보다 크게 그려, 왜 복제가 비싼지 그림만으로 보이게 한다.

    블록 넓이 = 파라미터 비중(인식부 89%)에 맞춘 시각적 비례.
    각 그룹은 [제목줄 · 부제줄]을 도형 위에 따로 두어 겹치지 않게 한다.
    """
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()
    PW, DW = 0.30, 0.175          # 인식부 / 결정부 폭
    x0, xd = 0.10, 0.52           # 열 시작 x
    RH, RS = 0.026, 0.034         # 전문가 행 높이 / 행 간격

    def head(y, t, sub):
        ax.text(0.02, y, t, fontsize=8.6, fontweight='bold', va='center', color=C['ink'])
        ax.text(0.02, y - 0.030, sub, fontsize=6.9, va='center', color=C['mute'])

    def experts(ytop, pw, px, pfc, dfc, plabel, pfs, dtc=None):
        """전문가 5행: 인식부 5벌 + 결정부 5벌."""
        for k in range(5):
            yy = ytop - k * RS
            _box(ax, px, yy - RH / 2, pw, RH, plabel, pfc, fs=pfs)
            _arrow(ax, (px + pw, yy), (xd, yy), lw=0.7)
            _box(ax, xd, yy - RH / 2, DW, RH, SIT[k], dfc, fs=5.6, tc=dtc)

    # 1) 단일망
    head(0.978, 'Single network', '369K  ·  one perception, one decision')
    y = 0.880
    _box(ax, x0, y - 0.028, PW, 0.056, 'RadarEncoder', '#dfe6ec', fs=7.4)
    _arrow(ax, (x0 + PW, y), (xd, y))
    _box(ax, xd, y - 0.028, DW, 0.056, 'Decision', C['base'], fs=7.4, tc='white')

    # 2) 분리·얇게
    head(0.815, 'Separate experts, thin',
         '363K  ·  perception duplicated x5, each narrowed')
    experts(0.755, PW * 0.62, x0 + PW * 0.38, '#e8eef3', C['alt1'], 'Thin RadarEncoder', 5.4)

    # 3) 분리·두껍게
    head(0.560, 'Separate experts, full',
         '1.83M  ·  perception duplicated x5, full width')
    experts(0.500, PW, x0, '#dfe6ec', C['alt2'], 'RadarEncoder', 5.8)

    # 4) 공유 (제안)
    head(0.305, 'Shared perception (proposed)',
         '512K  ·  one perception, five specialised decisions')
    ytop = 0.245
    yc = ytop - 2 * RS                     # 5행의 중앙
    _box(ax, x0, yc - 0.055, PW, 0.110, 'Shared\nRadarEncoder', '#cfe0ee',
         ec=C['proposed'], lw=1.4, fs=7.4)
    for k in range(5):
        yy = ytop - k * RS
        _arrow(ax, (x0 + PW, yc), (xd, yy), lw=0.7, color=C['proposed'])
        _box(ax, xd, yy - RH / 2, DW, RH, SIT[k], C['proposed'], fs=5.6, tc='white')

    ax.text(0.5, 0.012,
            'Radar perception is ~89% of single-network parameters.\n'
            'The same expert decomposition is applied to MessageActor, ControlActor and Critic.',
            ha='center', va='bottom', fontsize=6.9, color=C['mute'], linespacing=1.4)


# ── Fig3 (a) 이웃 집계 ────────────────────────────────────────────────────
def aggregation(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()

    def fleet(cx, cy, keep, label):
        ang = np.deg2rad([90, 162, 234, 306, 18])
        r = 0.145
        ax.plot([cx], [cy], marker='s', ms=9, color=C['proposed'], zorder=5)
        ax.text(cx, cy - 0.052, 'receiver', ha='center', fontsize=6.6, color=C['ink'])
        for j, a in enumerate(ang[:4]):
            px, py = cx + r * np.cos(a), cy + r * np.sin(a)
            used = j < keep
            ax.plot([px], [py], marker='o', ms=6,
                    color=C['proposed'] if used else '#d8dde2',
                    mec='#3a3a3a' if used else '#c2c8ce', mew=0.6, zorder=5)
            if used:
                _arrow(ax, (px, py), (cx, cy), lw=1.0, color=C['proposed'], shrink=7)
            else:
                ax.plot([px, cx], [py, cy], ls=':', lw=0.7, color='#c2c8ce', zorder=1)
            ax.text(px, py + 0.045, f'$m_{j+1}$', ha='center', fontsize=6.6,
                    color=C['ink'] if used else '#b6bcc2')
        ax.text(cx, cy + 0.245, label, ha='center', fontsize=8.2, fontweight='bold')

    fleet(0.25, 0.56, 1, 'Nearest-1')
    fleet(0.75, 0.56, 4, 'Nearest-4  (used)')
    ax.text(0.25, 0.245, 'other neighbours discarded', ha='center', fontsize=6.8,
            color=C['mute'])
    ax.text(0.75, 0.245, 'all four messages combined', ha='center', fontsize=6.8,
            color=C['mute'])
    ax.text(0.5, 0.115,
            r'$[\sin\phi_{ij},\ \cos\phi_{ij},\ d_{ij}/420]\ \Vert\ \mathbf{m}_j'
            r'\ \rightarrow\ f_{\mathrm{loc}}\ \rightarrow\ \mathbf{e}_{ij}$',
            ha='center', fontsize=8.4, color=C['ink'])
    ax.text(0.5, 0.035,
            r'$\bar{\mathbf{m}}_i=\frac{1}{|\mathcal{P}_i|}'
            r'\sum_{j\in\mathcal{P}_i}\mathbf{e}_{ij}$   (masked mean)',
            ha='center', fontsize=8.4, color=C['ink'])


# ── Fig5 (a) 방향성 벌점 ──────────────────────────────────────────────────
def colregs_penalty(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()

    def hull(cx, cy, s=1.0):
        ax.plot([cx], [cy], marker='^', ms=11 * s, color=C['ink'], zorder=5)

    # 좌: Head-On / Give-Way / Overtaking — 좌현 선회가 벌점
    cx, cy = 0.27, 0.60
    ax.text(cx, 0.90, 'Head-On · Give-Way · Overtaking', ha='center',
            fontsize=8.0, fontweight='bold')
    hull(cx, cy)
    ax.add_patch(Wedge((cx, cy), 0.145, 95, 175, facecolor='#e6c3c3',
                       edgecolor='none', alpha=0.85, zorder=2))
    ax.add_patch(Wedge((cx, cy), 0.145, 5, 85, facecolor='#c3ddc9',
                       edgecolor='none', alpha=0.85, zorder=2))
    ax.text(cx - 0.115, cy + 0.10, 'port turn\npenalised', ha='center', fontsize=7.0,
            color='#8d3b3b')
    ax.text(cx + 0.115, cy + 0.10, 'starboard turn\nfree', ha='center', fontsize=7.0,
            color='#2f6b41')
    ax.text(cx - 0.10, cy + 0.185, '✗', ha='center', fontsize=12,
            color='#8d3b3b', fontfamily='DejaVu Sans')
    ax.text(cx + 0.10, cy + 0.185, '✓', ha='center', fontsize=12,
            color='#2f6b41', fontfamily='DejaVu Sans')

    # 우: Stand-On — 어느 쪽이든 선회가 벌점, 침로 유지가 정답
    cx = 0.73
    ax.text(cx, 0.90, 'Stand-On', ha='center', fontsize=8.0, fontweight='bold')
    hull(cx, cy)
    ax.add_patch(Wedge((cx, cy), 0.145, 95, 175, facecolor='#e6c3c3',
                       edgecolor='none', alpha=0.85, zorder=2))
    ax.add_patch(Wedge((cx, cy), 0.145, 5, 85, facecolor='#e6c3c3',
                       edgecolor='none', alpha=0.85, zorder=2))
    _arrow(ax, (cx, cy + 0.03), (cx, cy + 0.185), lw=1.4, color='#2f6b41')
    ax.text(cx - 0.115, cy + 0.10, 'turn ✗', ha='center', fontsize=7.4,
            color='#8d3b3b', fontfamily='DejaVu Sans')
    ax.text(cx + 0.115, cy + 0.10, 'turn ✗', ha='center', fontsize=7.4,
            color='#8d3b3b', fontfamily='DejaVu Sans')
    ax.text(cx + 0.035, cy + 0.20, 'maintain ✓', ha='left', fontsize=7.4,
            color='#2f6b41', fontfamily='DejaVu Sans')

    ax.text(0.5, 0.20,
            r'$R^{\mathrm{COLREGs}}_i=-\alpha_c\,(1+\rho_i)\,'
            r'\mathbf{1}[\rho_i>0.3]\ (\cdots)$',
            ha='center', fontsize=9.0, color=C['ink'])
    ax.text(0.5, 0.085,
            'A directional penalty on non-compliant turning — not a positive compliance bonus.\n'
            r'Weighted by collision risk $\rho_i$ and applied only above a risk gate.',
            ha='center', fontsize=7.0, color=C['mute'])


# ── Fig7 (a) 혼합 함대 ────────────────────────────────────────────────────
def fleet_composition(ax, n_rx=6, n=16):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()
    ax.set_aspect('equal', adjustable='box')
    ax.text(0.5, 0.95, f'Spawn ring — {n} vessels, {n_rx} receive-only',
            ha='center', fontsize=8.2, fontweight='bold')
    cx, cy, r = 0.5, 0.48, 0.30
    th = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 2
    ax.add_patch(Circle((cx, cy), r, fill=False, ec='#d3d8dd', lw=0.8, ls='--', zorder=1))
    # 통신 불가 선박을 링 위에 고르게 분산(한쪽에 몰리면 그 구역만 공백이 됨)
    idx_rx = set(np.round(np.linspace(0, n, n_rx, endpoint=False)).astype(int) % n)
    for i, a in enumerate(th):
        px, py = cx + r * np.cos(a), cy + r * np.sin(a)
        if i in idx_rx:
            ax.plot([px], [py], marker='v', ms=7, color='#d9d9d9', mec='#8d3b3b',
                    mew=1.1, zorder=5)
        else:
            ax.plot([px], [py], marker='o', ms=6.5, color=C['proposed'],
                    mec='#3a3a3a', mew=0.6, zorder=5)
            for k in range(3):
                aa = a + (k + 1) * 0.055
                ax.plot([cx + (r + 0.012 + k * 0.012) * np.cos(aa)],
                        [cy + (r + 0.012 + k * 0.012) * np.sin(aa)],
                        marker='.', ms=1.6, color=C['proposed'], zorder=4)
    ax.plot([], [], marker='o', ls='none', ms=6.5, color=C['proposed'],
            mec='#3a3a3a', mew=0.6, label='Tx + Rx  (broadcasts)')
    ax.plot([], [], marker='v', ls='none', ms=7, color='#d9d9d9', mec='#8d3b3b',
            mew=1.1, label='Rx-only  (listens, never broadcasts)')
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.04), ncol=1,
              handletextpad=0.5, fontsize=7.6)
