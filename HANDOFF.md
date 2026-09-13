# HANDOFF — Vessel paper RL campaign (common_freeze_v11)

작성일: 2026-09-12  
범위: Fig1–8 재현 학습·평가 캠페인 인수인계  
원칙: **완료된 학습·체크포인트·결과 파일을 보존**한다. 새 Agent는 재학습보다 평가·분석·그림화를 우선한다.

---

## 0. 워크스페이스 지도 (필수)

```
F:\projects\vessel\
├── HANDOFF.md                 ← 이 문서
├── README.md                  ← 폴더 역할 요약
├── main\                      ← GitHub DT_Vessel origin/main (최신 코드 미러)
├── campaigns\
│   └── a2z-2026-09-05_paper_v11\   ← ★ 논문 캠페인 코드 + 결과 (작업 본체)
├── reference\
│   ├── YHSH_VESSEL\           ← 납품 그림·실험 설계 문서
│   └── manuscripts\           ← .tex 초안
├── archive\                   ← 옛 arm 포크, Unity 런 덤프, Comm_* 
└── repro\                     ← 이동 잔여물(잠금). 사용 금지 → campaigns 사용
```

**캠페인 루트 (이하 `$C`):**  
`F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11`

**결과 레이아웃:** `$C\runs\paper\STRUCTURE.txt`  
**Freeze 노트:** `$C\runs\PAPER_FREEZE.md`  
**Freeze env:** `$C\Python\paper_freeze.env` (hash `c6d7099b9d31`, version `common_freeze_v11`)

`main\` 과 `$C` 는 **분리**되어 있다. `main`에 pull한 최신 코드를 캠페인 폴더에 맹목적으로 덮어쓰지 말 것.

---

## 1. 연구 목표와 현재 단계

### 1.1 논문에서 검증하려는 주장 (그림축)

출처: `reference\YHSH_VESSEL\README.txt`, `알고리즘과 비교설계.md`, `그림별 정리.md`

| Fig | 비교 축 | 목적 |
|-----|---------|------|
| Fig1 | 통신 ON vs OFF | 통신이 성능(도착/안전)을 올리는가 |
| Fig2 | MoE 구조 4종 (SINGLE / shared hub / THIN / THICK) | 제안 구조(공유 MoE)의 상대 위치 |
| Fig3 | max_partners 4 vs 1 (NEAR1) | 메시지 집계 폭 |
| Fig4 | msg_dim 2…12 (hub=6) | 메시지 차원 |
| Fig5 | COLREGS 보상 항 ON vs OFF | 규정 항의 기여 |
| Fig6 | `comm_on_at` 9M vs 0 (early) | 통신 커리큘럼 시점 |
| Fig7 | 혼합함대(RX-only 비율) | **학습 없음**, hub 정책 고정 평가 |
| Fig8 | A* 전역경로 vs direct | **학습 없음**, hub 정책 고정 평가 |

공통 원칙(캠페인에서 확정):

1. **한 freeze로 Fig1–8** — ablation은 **한 축만** 변경.
2. **Fig1 ON > OFF가 게이트** — 실패 시 freeze를 바꾸고 hub부터 재학습 (v2–v10 실패 후 **v11 PASS**).
3. YHSH 파라미터표를 그대로 복제하는 것이 목표가 아님 — “무엇을 비교할지”의 축만 맞춤.

### 1.2 완료 / 남은 작업

| 상태 | 내용 |
|------|------|
| **완료** | `common_freeze_v11` 하 Fig1–6 **학습 × seeds 42/43/44** + **formal 평가** |
| **완료** | Fig7 mixed-fleet eval (hub ×3 seeds) |
| **완료** | Fig8 A* vs direct eval (**hub s42 only** 2×2) |
| **완료** | `runs/paper` 폴더 정리 (`results/`, `ckpts/final|steps`, `train_meta/`) |
| **완료** | 캠페인을 `campaigns\…`로 분리, `main`을 GitHub 최신으로 pull |
| **미완 / 후속** | 새 formal 수치로 **논문 그림 재생성** (YHSH `plotting` 파이프라인) |
| **미완** | Fig8 **blocked-subset** 별도 리포트 (overall mean은 TO~35%로 희석) |
| **미완** | Fig8 **s43/s44** 동일 프로토콜 (현재 s42만) — **미합의**; 필요 시 평가만 |
| **미완** | colregsOK(C) ~55% vs 목표 감각 ≥80% — freeze 전반 만성, Fig1 PASS로 진행 결정됨 |
| **미확인** | `main` git worktree가 `msgComparision` 경로를 가리키며 `git` 명령 실패하는 경우 있음. 코드 파일은 존재 |

### 1.3 확정 / 제약 / 기각

**확정**

- Freeze: `common_freeze_v11`, hash `c6d7099b9d31`
- Seeds: **42, 43, 44**
- 학습량: **16M** decisions (`--steps 16000000`), 중간 ckpt 2M마다
- Hub formal 기준 성능: ON mean goal **93.7%**
- Collapse gate만 사용 (Fig1 패턴 미스로 kill하지 않음): mid-eval에서 goal&lt;40 또는 oColl&gt;20 → kill (`gate_paper_collapse.ps1`)
- Fig1 PASS 후에야 Fig2–6 진행

**제약**

- Python env: `C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe`
- GPU: 캠페인 당시 4× RTX (물리 `cuda:N`; formal 시 `CUDA_VISIBLE_DEVICES` remapping 사용)
- Formal 집계 시 `goal=` / `oColl=` 필드를 혼동하지 말 것 (gate mid-eval ≠ formal)

**기각 / 하지 말 것**

- Fig1 FAIL 시 그림별로 freeze를 따로 튜닝하지 않음 → **공통 freeze 재설계** (v2…v11)
- v8 전면 retrain 계획 취소됨 (대화상); v9 privileged-reward 수정 후 v10 → v11
- 완료된 FINAL을 “더 좋은 mid-ckpt”로 대체해 cherry-pick하지 않음
- `main` 최신 코드를 캠페인 결과에 맞춰 **재학습으로 덮어쓰기** 금지 (먼저 평가·그림)

---

## 2. 현재 코드와 학습 설정

### 2.1 진입점·핵심 파일 (`$C\Python\`)

| 경로 | 역할 |
|------|------|
| `start_paper_train.ps1` | Fig hub/fig1–6 학습 런처 (freeze + 1축 override) |
| `paper_freeze.env` | 공통 freeze 환경변수 |
| `load_paper_freeze.ps1` / `apply_paper_freeze.py` | freeze 로드·적용·hash |
| `vessel_gym_train.py` | PPO 학습 루프 |
| `vessel_gym.py` | GPU 배치 시뮬 |
| `networks.py` | 정책·MoE·통신 |
| `eval_ckpt.py` | 정책 고정 formal/mid 평가 |
| `eval_mixed.py` | Fig7 혼합함대 |
| `eval_fig7_paper.ps1` / `eval_fig8_paper.ps1` | Fig7/8 캠페인 래퍼 |
| `astar_fig9\eval_astar_global.py` | Fig8 A*/direct (캠페인 내 경로; `eval_fig8`가 호출) |
| `fig8_blocked_pairs.py` | blocked vs clear spawn 집계 |
| `gate_paper_collapse.ps1` | collapse-only gate |

참고 설계 문서(납품): `reference\YHSH_VESSEL\알고리즘과 비교설계.md`

### 2.2 학습에 실제로 쓴 설정 (메타·스크립트에서 확인)

허브 예: `$C\runs\paper\train_meta\qd_MOE_SE_s42.meta.txt`

```
freeze=c6d7099b9d31 version=common_freeze_v11
CLI: steps=16000000 envs=128 ring=0.7 partners=4 comm_on_at=9000000 msg_dim=6
```

| 항목 | 값 | 근거 |
|------|-----|------|
| steps | 16_000_000 | `start_paper_train.ps1` `-Steps`, meta |
| envs | 128 | 동일 |
| vessels | 16 | `start_paper_train.ps1` |
| rollout | 32 | 동일 |
| ring | 0.7 | 동일 |
| seeds | 42,43,44 | 동일 |
| hub `comm_on_at` | 9_000_000 | meta / freeze 커리큘럼 |
| Fig6 `comm_on_at` | 0 | early-comm 축 |
| msg_dim hub | 6 | freeze |
| MoE | USE_MOE=1, SHARED=1, WIDTH=1.0 | `paper_freeze.env` |
| radar act | leaky | freeze |
| threat / goal-comm / consumer | 0.45 / 0.18 / 0.15 | freeze (v11) |
| SIM_COLREGS | 0.45 (Fig5 train만 0) | freeze; Fig5 override |
| progress / arrival / collision | 1.5 / 120 / -450 | freeze |
| ckpt_every | 2 (M) | launcher |

**보상·관측 전체 PPO 하이퍼(γ, lr 등):** 캠페인 당시 `config.py` / train 기본값에 의존.  
YHSH 문서상 일반표는 `알고리즘과 비교설계.md` §3에 있으나, **v11 학습 순간의 config 스냅샷 파일은 별도 미확인** (meta에는 CLI·freeze만 기록).

### 2.3 Formal / Fig7–8 평가 프로토콜 (결과 파일 헤더 기준)

**Fig1–6 formal (표준):**

```
envs=64 burnin=800 eval_decisions=3000 ring=0.7 partners=4
```

(Fig3만 `max_partners=1`)

**Fig7:** `eval_fig7_paper.ps1` — mode=rx, sweep 2..14, envs_per=14, burnin=1200, eval_decisions=4500 (스크립트 기본값; 요약은 `results\FIG7\FIG7_FORMAL.txt`)

**Fig8:** seed=42, envs=96, burnin=1200, eval_decisions=10000 (`FIG8_FORMAL.txt`)

### 2.4 학습 이후 코드 상태 차이

| 트리 | 상태 |
|------|------|
| `$C` (캠페인) | v11 학습·평가에 사용한 **패치된** 트리 + paper 스크립트. Git tip는 대화상 `repro/a2z-2026-09-05` @ `9e9e6e8` + 로컬 미커밋 다수였음. **현재 dirty 여부 미확인**(이동 후 git 메타 깨질 수 있음). |
| `main\` | GitHub `origin/main`으로 **fast-forward** 완료 (대화상 `fd358e8`). config 통합·골든 테스트·run_repro 등 **대규모 리팩터** 포함 → **캠페인 코드와 동일하지 않음**. |

→ 체크포인트 재평가·추가 분석은 **`$C\Python`에서 freeze를 로드한 뒤** 수행할 것.

---

## 3. 완료된 학습과 결과 위치

### 3.1 체크포인트

- **Canonical FINAL:** `$C\runs\paper\ckpts\final\*.pt` — **39개** (확인됨)
- **Root hardlink:** `$C\runs\paper\<tag>.pt` → 동일 FINAL (스크립트 호환)
- **중간 step:** `$C\runs\paper\ckpts\steps\*.step{2..16}M.pt`
- **선택 기준:** 학습 `steps=16M` 종료 시 저장되는 **FINAL `.pt`**. Formal은 FINAL만 사용. Mid `step*M`은 gate/디버그용.
- **Train meta / csv / heartbeat:** `$C\runs\paper\train_meta\`

Tag 맵: `STRUCTURE.txt` 참고.

### 3.2 실험별 완료 상태

| 실험 | 학습 | Formal/Eval | 요약 파일 |
|------|------|-------------|-----------|
| Hub ON (Fig1 ON) | 완료 ×3 | 완료 | `results\HUB_FORMAL_ON.txt`, `FIG1\` |
| Fig1 OFF | 완료 ×3 | 완료 | `FIG1\FIG1_FORMAL_COMPARE.txt`, `FIG1_GATE_VERDICT.txt` = **PASS** |
| Fig2 SINGLE/THIN/THICK | 완료 ×3 each | 완료 | `FIG2\FIG2_FORMAL_{SINGLE,THIN,THICK}.txt` |
| Fig3 NEAR1 | 완료 ×3 | 완료 | `FIG3\FIG3_FORMAL_NEAR1.txt` |
| Fig4 DIM2/4/8/10/12 | 완료 ×3 each | 완료 | `FIG4\FIG4_TREND.txt` + `FIG4_FORMAL_DIM*.txt` |
| Fig5 COLREGSOFF | 완료 ×3 | 완료 | `FIG5\FIG5_FORMAL.txt` |
| Fig6 START | 완료 ×3 | 완료 | `FIG6\FIG6_FORMAL.txt` |
| Fig7 mixed | N/A (eval) | 완료 ×3 hub | `FIG7\FIG7_FORMAL.txt`, `fig7\mixed_fleet_rx.csv` |
| Fig8 A*/direct | N/A (eval) | **s42만** 완료 | `FIG8\FIG8_FORMAL.txt`, `fig8\summary_s42.txt`, `fig8\hub_s42_*.log` |
| Fig8 blocked pairs | N/A | JSON 생성됨 | `fig8\blocked_pairs.json` (blocked 212/320) |
| Collapse gate log | — | 있음 | `gate\collapse_history.txt` |
| Formal raw logs | — | 있음 | `eval\` |

캠페인 타임라인: `results\CAMPAIGN_V11.txt`

### 3.3 코드/설정 대응

모든 paper formal 헤더에 **`common_freeze_v11`** 명시.  
메타 `freeze=c6d7099b9d31`.  
구버전 freeze 아카이브: `$C\runs\archive\paper_freeze_v{2..10}\` (있으면).

### 3.4 재학습 없이 평가하는 명령 (템플릿)

작업 디렉터리: `$C\Python`  
Python: `C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe`

```powershell
cd F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11\Python
. .\load_paper_freeze.ps1
Set-PaperFreezeEnv   # Fig5만: Set-PaperFreezeEnv -Override @{ VESSEL_SIM_COLREGS_COEF = "0" }
$env:CUDA_VISIBLE_DEVICES = "0"
& "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe" -u eval_ckpt.py `
  --ckpt F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11\runs\paper\qd_MOE_SE_s42.pt `
  --arm ON --envs 64 --burnin 800 --eval_decisions 3000 --ring 0.7 --max_partners 4 --device cuda:0
```

Fig3: `--max_partners 1`  
Fig7: `.\eval_fig7_paper.ps1`  
Fig8: `.\eval_fig8_paper.ps1 -Seed 42` (내부에서 `PYTHONPATH` 필요 — 캠페인 스크립트에 반영됨)

**학습 재실행 금지**가 기본. 필요 시에만 `start_paper_train.ps1` (아래 §5).

### 3.5 학습 완료 vs 평가 완료

- **학습 완료:** FINAL 39개 존재로 확인.
- **평가 완료:** Fig1–7 및 Fig8(s42) formal 요약 txt 존재로 확인.
- **미확인:** 모든 `eval\*.log`가 요약 txt와 1:1로 잔존하는지 전수 대조는 하지 않음. 요약 txt를 1차 근거로 사용.

---

## 4. 결과 해석과 미해결 사항

### 4.1 확인된 수치 (요약 파일)

**Fig1 (게이트) — PASS**  
ON 93.7% vs OFF 90.4%, mean Δ **+3.3pp** (시드 +3.5/+3.4/+3.2). oColl 낮음. C(colregsOK) ~50–55%.

**Fig2** mean goal: SINGLE **95.6** > hub **93.7** > THIN **91.5** > THICK **88.7**

**Fig3** NEAR1 mean **92.0** (−1.7pp vs hub)

**Fig4** hub dim6 최고; soft U, DIM10 최저(90.6), DIM12 회복(92.5) — `FIG4_TREND.txt`

**Fig5** COLREGS-off mean **95.4** (+1.7pp vs hub)

**Fig6** early-comm mean **91.7** (−2.0pp vs hub) → delayed hub가 소폭 우세

**Fig7** RX-only 비율 2–14에서 mean goal 대략 87–92%, 급격한 붕괴 없음 (`FIG7_FORMAL.txt`)

**Fig8 (s42 overall)** direct ≳ astar (~1.6–2.9pp); goal ~54–58%, **TO ~34–36%**. blocked pairs **212/320 (66.25%)**.

### 4.2 주장과의 관계

| 주장 | 상태 |
|------|------|
| 통신 ON이 OFF보다 나음 (Fig1) | **지지** (v11 formal) |
| 공유 MoE hub가 의미 있는 중간/상단 구조 | **부분 지지** (SINGLE이 더 높음; THICK 최하) |
| msg_dim 6이 합리적 | **지지** (트렌드상 hub 최고) |
| delayed comm가 early보다 나음 | **약한 지지** (−2.0pp) |
| COLREGS 항이 goal을 희생한다 | **방향 일치** (끄면 goal↑) — 규정 준수 trade-off는 C 지표로 추가 서술 필요 |
| 혼합함대에서 RX 증가 시 붕괴 | **이 캠페인 수치만으로는 비지지** (완만한 변동) |
| A*가 direct보다 나음 | **overall mean으로는 비지지**; blocked-subset은 **미완 검증** |

### 4.3 해결 / 잔여 / 반복 금지

**해결**

- Fig1 ON≈OFF 문제: freeze를 v11까지 올려 **PASS**
- 캠페인 산출물 경로 혼선: `runs/paper` 정리 + `campaigns/` 분리

**잔여**

- C~55% 만성 (aspirational 80% 미달) — PASS 판단으로 진행했으나 논문 서술 필요
- Fig8 overall vs blocked 해석
- YHSH 납품 그림과 **수치 파이프라인 재연결** (새 formal → plotting)
- `repro\a2z-…` 잠긴 잔여 폴더 삭제 (사용자 로컬)

**반복 금지**

- Fig1 실패 시 그림별 핵 튜닝
- Gate mid-eval(1500 dec 등) 숫자를 formal(3000)과 혼용
- FINAL 무시하고 step ckpt로 논문 숫자 채우기
- `main` 리팩터 코드를 검증 없이 캠페인 ckpt에 얹어 재학습

**사실 vs 추정**

- **사실:** 위 formal 표 수치, freeze hash, FINAL 39개.
- **추정(대화):** v10 실패 원인이 “메시지 under-use” → v11에서 goal-comm/consumer 강화. 인과는 A/B freeze 비교로만 간접 지지.
- **추정:** Fig8 낮은 goal은 프로토콜(envs/dec/TO)과 clear-pair 희석 — blocked 재집계로 확인 예정.

---

## 5. 다음 작업 (우선순위)

### P0 — 결과 보존·경로 고정 (추가 학습 없음)

- 입력: `$C\runs\paper\**`
- 내용: 새 Agent는 `$C`만 캠페인 루트로 사용. `main`과 섞지 않음.
- 산출: (유지)

### P1 — 논문 그림/표 초안을 **v11 formal 숫자**에 맞추기 (재학습 없음)

- 입력: `results\FIG*\*.txt`, YHSH `paper_figures` / `Python/plotting` 가이드 (`reference\YHSH_VESSEL\README.txt`)
- 내용: formal 요약을 표·그림 데이터 소스로 정리. YHSH `_data` 부재 시 **새 CSV/집계를 `$C`에서 생성**.
- 산출: 그림용 데이터 테이블, (가능하면) 재생성 스크립트 실행 로그
- **재학습 불필요**

### P2 — Fig8 blocked-subset 리포트 (재학습 없음)

- 입력: `fig8\blocked_pairs.json`, `fig8\hub_s42_*.log`, hub FINAL
- 내용: clear vs blocked에서 goal/TO 재집계; 필요 시 eval 하네스에 subset 플래그
- 산출: `FIG8_BLOCKED_SUBSET.txt` (또는 동등)
- **재학습 불필요**; 추가 eval만

### P3 — (선택) Fig8 s43/s44 동일 2×2 eval

- 근거: 시드 평균이 논문 Fig1–6 관례. **합의된 필수는 아님**.
- 재학습 불필요

### P4 — (최후) freeze/코드 변경이 필요할 때만 재학습

- 근거 예시: formal 재현 불가, ckpt 손상, 논문 필수 축 누락이 확인될 때
- 절차: `start_paper_train.ps1` + freeze hash 기록 + Fig1 게이트 재검증

---

## 6. 새 Agent용 시작 프롬프트 (복사용)

```
당신은 Vessel 논문 RL 후속 Agent다. 워크스페이스는 F:\projects\vessel 이다.

반드시 먼저 읽고 따르라:
1) F:\projects\vessel\HANDOFF.md
2) F:\projects\vessel\README.md
3) F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11\runs\paper\STRUCTURE.txt
4) F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11\runs\PAPER_FREEZE.md
5) 필요 시 results/FIG*/FIG*_FORMAL*.txt

캠페인 코드·결과 루트는
  F:\projects\vessel\campaigns\a2z-2026-09-05_paper_v11
이다. main\ 은 GitHub 최신 미러일 뿐이며 캠페인과 섞지 마라.

제약:
- 완료된 학습 FINAL 체크포인트·formal 결과·runs/paper 산출물을 삭제·덮어쓰기·재학습으로 대체하지 마라.
- 기본은 추가 평가·분석·그림화(HANDOFF §5 P1–P2)부터 진행한다.
- 재학습은 HANDOFF에 적힌 근거가 있을 때만, 사용자 확인 후 진행한다.
- 확인되지 않은 사실은 미확인으로 두고 추측으로 확정하지 마라.

첫 응답에서: (a) HANDOFF 기준 현재 단계 한 줄, (b) 다음에 할 P1/P2 작업 계획을 짧게 제시한 뒤 사용자 확인을 받아라.
```

---

## 부록 — 빠른 경로 치트시트

| 보고 싶은 것 | 경로 |
|--------------|------|
| Fig1 PASS | `$C\runs\paper\results\FIG1\FIG1_FORMAL_COMPARE.txt` |
| Hub | `$C\runs\paper\results\HUB_FORMAL_ON.txt` |
| 전 Fig 트렌드 | `$C\runs\paper\results\FIG4\FIG4_TREND.txt` 등 |
| FINAL ckpt | `$C\runs\paper\ckpts\final\` 또는 `$C\runs\paper\<tag>.pt` |
| Freeze env | `$C\Python\paper_freeze.env` |
| 캠페인 로그 | `$C\runs\logs\campaign_v11\` (있으면) |
| YHSH 설계 | `F:\projects\vessel\reference\YHSH_VESSEL\` |
