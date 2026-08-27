"""Fig9 대체 후보 — 연료·항해시간 comm OFF/ON 대조 (실측).

구 Fig9_Global(longhaul_4/5)은 mock_longhaul_estimate.py가 만든 **합성 그림**이었음.
이 스크립트는 그걸 실측 데이터로 대체하는 후보를 만듦.

입력: Figures/_data/metrics_v2.txt (eval_ckpt.py 출력 원문, 손으로 옮긴 숫자 없음)
지표: eval_ckpt.py 의 goal 에피소드 기준
  - fuel = Σ (speed_norm² + 0.5·|rudder|²)   (보상 연료항과 같은 형태)
  - len  = 도착까지 decision 수
환경: vessel_gym 600×600m 아레나, 16척, ring 0.7. **장거리(Taiwan↔Busan) 아님.**

주의(정직성):
  - goal 에피소드만 집계 → 도착률이 다른 팔끼리 비교하면 selection bias. 도착률을 같이 표기함.
  - 오차막대 = 시드간 표준편차(n=3). 에피소드간 산포 아님.
  - 시드별 승패를 그림 위에 직접 노출(페어 선으로) — 평균만 보고 판단하지 않게.
"""
import os
import re
import sys

import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paper_style  # noqa: E402

SRC = os.path.join(HERE, '_data', 'metrics_v2.txt')
OUT_DIR = os.path.join(HERE, '_fig9_candidate')

C_OFF = '#C0504D'   # 통신 없음
C_ON = '#4472C4'    # 통신 있음

# 시드 페어가 맞는 OFF/ON 대조만. 이름→설정 매핑은 Figures/RUNS.md 기준.
PAIRS = [
    ('Baseline', ['OFF_s42', 'OFF_s43', 'OFF_s44'],
                 ['COMM_s42', 'COMM_s43', 'COMM_s44']),
    ('SE',       ['SE_OFF_s42', 'SE_OFF_s43', 'SE_OFF_s44'],
                 ['SE_NEAR1_s42', 'SE_NEAR1_s43', 'SE_NEAR1_s44']),
    ('SE (v20)', ['V20_SE_OFF_s42', 'V20_SE_OFF_s43', 'V20_SE_OFF_s44'],
                 ['V20_MOE_SE_s42', 'V20_MOE_SE_s43', 'V20_MOE_SE_s44']),
    ('VA',       ['VA_OFF_s42', 'VA_OFF_s43', 'VA_OFF_s44'],
                 ['VA_COMM_s42', 'VA_COMM_s43', 'VA_COMM_s44']),
]

# 시드가 3개 미만이라 그림에서 뺀 것들 — 콘솔에만 찍음(제약: n=1 단독 주장 금지)
PAIRS_THIN = [
    ('FAR',   ['FAR_OFF_s42', 'FAR_OFF_s43'], ['FAR_COMM_s42', 'FAR_COMM_s43']),
    ('FOG28', ['FOG28_OFF_s42'],              ['FOG28_COMM_s42']),
]


def load(path=SRC):
    """metrics_v2.txt 원문 → {name: dict}. 파싱 실패 줄은 건너뜀."""
    rows = {}
    with open(path, encoding='utf-8') as fh:
        for ln in fh:
            m = re.match(r'\[([^\]]+)\]\s+(\S+)\s+\|\s+arm=(\w+)', ln)
            if not m:
                continue
            g = re.search(r'goal=\s*([\d.]+)%', ln)
            f = re.search(r'fuel=\s*([\d.]+)', ln)
            l = re.search(r'len=\s*(\d+)', ln)
            v = re.search(r'vColl=\s*([\d.]+)%', ln)
            if not (g and f and l and v):
                continue
            rows[m.group(1)] = dict(ckpt=m.group(2), arm=m.group(3),
                                    goal=float(g.group(1)), vcoll=float(v.group(1)),
                                    fuel=float(f.group(1)), length=float(l.group(1)))
    return rows


def pick(rows, names, key):
    miss = [n for n in names if n not in rows]
    if miss:
        raise KeyError(f'metrics_v2.txt 에 없는 실행: {miss}')
    return np.array([rows[n][key] for n in names], dtype=float)


def panel(ax, rows, pairs, key, ylabel, title):
    """팔별 OFF/ON 막대 + 시드 페어 선. 반환: 콘솔용 요약 리스트."""
    lines = []
    xs = np.arange(len(pairs), dtype=float)
    w = 0.32
    for i, (label, off_n, on_n) in enumerate(pairs):
        o = pick(rows, off_n, key)
        n = pick(rows, on_n, key)
        ax.bar(xs[i] - w / 2, o.mean(), w, yerr=o.std(ddof=1), capsize=3,
               color=C_OFF, alpha=0.85, edgecolor='none',
               error_kw=dict(lw=0.9, ecolor='0.25'),
               label='Comm OFF' if i == 0 else None, zorder=2)
        ax.bar(xs[i] + w / 2, n.mean(), w, yerr=n.std(ddof=1), capsize=3,
               color=C_ON, alpha=0.85, edgecolor='none',
               error_kw=dict(lw=0.9, ecolor='0.25'),
               label='Comm ON' if i == 0 else None, zorder=2)
        # 시드 페어 — 평균 뒤에 가려지는 승패를 그대로 노출
        for a, b in zip(o, n):
            ax.plot([xs[i] - w / 2, xs[i] + w / 2], [a, b],
                    color='0.25', lw=0.7, alpha=0.75, zorder=4,
                    marker='o', ms=2.6, mfc='white', mec='0.25', mew=0.7)
        wins = int((n < o).sum())
        d_pct = 100.0 * (n.mean() - o.mean()) / o.mean()
        # 0-기준 막대라 5% 차이는 눈에 안 보임 → 축을 자르는 대신 값을 직접 씀
        top = max(o.mean() + o.std(ddof=1), n.mean() + n.std(ddof=1), o.max(), n.max())
        ax.text(xs[i], top * 1.055, f'{d_pct:+.1f}%', ha='center', va='bottom',
                fontsize=9.5, color=(C_ON if d_pct < 0 else C_OFF))
        lines.append((label, o.mean(), o.std(ddof=1), n.mean(), n.std(ddof=1),
                      wins, len(o)))
    ax.set_xticks(xs)
    ax.set_xticklabels([f'{lab}\n{w_}/{n_}' for (lab, *_), (w_, n_)
                        in zip(pairs, [(r[5], r[6]) for r in lines])])
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc='left', pad=8)
    ax.margins(x=0.12)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
    return lines


def main():
    paper_style.apply()
    rows = load()
    os.makedirs(OUT_DIR, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.1))
    lf = panel(axes[0], rows, PAIRS, 'fuel',
               r'Fuel  $\Sigma(v^2 + 0.5\delta^2)$',
               '(a) Fuel consumption')
    ll = panel(axes[1], rows, PAIRS, 'length',
               'Decisions to goal',
               '(b) Time to goal')
    axes[0].legend(loc='upper left', ncol=2, bbox_to_anchor=(0.0, 1.02))
    fig.suptitle('Goal-reached episodes, 16 vessels, 600 x 600 m arena '
                 '(not a long-haul voyage)', fontsize=10, y=1.04, color='0.25')
    fig.text(0.5, -0.04,
             'Percentages: change of Comm ON relative to Comm OFF.   '
             'Below each arm: seeds where Comm ON wins.\n'
             'Error bars: across-seed SD (n=3).   Thin grey lines: seed-paired runs.   '
             'Bars start at zero - the effect really is this small.',
             ha='center', fontsize=8.2, color='0.35')
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT_DIR, f'fig9_candidate.{ext}'),
                    bbox_inches='tight')
    plt.close(fig)

    # ── 콘솔 표: 그림에 넣은 것 + 시드 부족해 뺀 것 전부 ──
    print(f'입력: {SRC}')
    print(f'출력: {OUT_DIR}/fig9_candidate.png|pdf\n')
    for key, title, block in (('fuel', '연료 Σ(v²+0.5δ²)', lf),
                              ('length', '도착까지 decision', ll)):
        print(f'== {title} (도착 에피소드) ==')
        print(f"{'팔':10s} {'OFF':>16s} {'ON':>16s} {'Δ':>9s} {'Δ%':>7s} {'ON승':>6s}")
        for lab, om, os_, nm, ns, wins, ntot in block:
            d = nm - om
            print(f'{lab:10s} {om:8.1f}±{os_:6.1f} {nm:8.1f}±{ns:6.1f} '
                  f'{d:+9.1f} {100*d/om:+6.1f}% {wins:3d}/{ntot}')
        print()

    print('== 도착률(%) — 위 지표가 "도착한 배"만 세므로 같이 봐야 함 ==')
    print(f"{'팔':10s} {'OFF':>14s} {'ON':>14s} {'Δpp':>7s}")
    for lab, off_n, on_n in PAIRS:
        o = pick(rows, off_n, 'goal'); n = pick(rows, on_n, 'goal')
        print(f'{lab:10s} {o.mean():7.1f}±{o.std(ddof=1):5.1f} '
              f'{n.mean():7.1f}±{n.std(ddof=1):5.1f} {n.mean()-o.mean():+7.1f}')
    print()

    print('== 시드 부족(<3)이라 그림에서 뺀 대조 — 단독 주장 금지 ==')
    for lab, off_n, on_n in PAIRS_THIN:
        for key, nm in (('fuel', '연료'), ('length', '시간'), ('goal', '도착률')):
            o = pick(rows, off_n, key); n = pick(rows, on_n, key)
            print(f'  {lab:6s} n={len(o)} {nm:4s}: OFF {o.mean():7.1f}  '
                  f'ON {n.mean():7.1f}  ({int((n<o).sum())}/{len(o)} ON 우세)')
        print()


if __name__ == '__main__':
    main()
