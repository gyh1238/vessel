# 구현 · Freeze · 그림별 설정 — common_freeze_v11

작성: 2026-09-13  
저장소 루트 `$C`: `F:\projects\vessel` (이 폴더가 freeze v11 본문)  
논리 주장: [CLAIMS.md](CLAIMS.md)

`latest\` (DT_Vessel 미러)과 `$C`는 **다른 코드**다. 재평가·재학습·그림은 전부 `$C\Python`에서 freeze를 로드한 뒤 한다.

---

## 1. 디렉터리

```
$C\                              GitHub 루트 = freeze v11
├── DISCUSSION.md / CLAIMS.md / IMPLEMENTATION.md
├── figures\                     Fig1–8 png/pdf
├── results\                     FIG*.txt, metrics.csv
├── Python\                      학습·평가·그림 스크립트
│   ├── paper_freeze.env         공통 freeze (해시 대상 전체 파일)
│   ├── load_paper_freeze.ps1    freeze 로드 + SHA
│   ├── start_paper_train.ps1    Fig1–6 학습 (축 하나 override)
│   ├── eval_ckpt.py             Fig1–6 고정정책 평가 (PRIMARY v2)
│   ├── aggregate_eval_v2.py     eval_v2 로그 → results/
│   └── make_paper_figures.py    figures/ png/pdf
├── Agent\ Management\ Navigation\
├── latest\                      DT_Vessel 미러 (논문 출처 아님)
└── runs\paper\
    ├── ckpts\final\             FINAL 39개 *.pt (지우지 말 것)
    ├── ckpts\steps\             중간 step*M
    ├── train_meta\              *.meta.txt (freeze 해시·CLI)
    ├── eval\                    옛 formal 로그 (덮지 말 것)
    ├── eval_v2\                 PRIMARY v2 재평가 로그
    ├── fig7\ mixed_fleet_rx.csv
    ├── fig8\ hub_s42_*.log
    └── results\FIG1…FIG8\       학습 직후 FORMAL (보존)
```

Python 학습/평가: `C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe`  
그림만: `qxapp` env (matplotlib). freeze env에 matplotlib를 넣지 않았다.

---

## 2. 공통 freeze (`paper_freeze.env`)

**버전** `common_freeze_v11`  
**해시** `c6d7099b9d31` — 파일 **전체** SHA. 한 줄만 고쳐도 해시가 바뀌므로 **이 파일을 편집하지 않는다.** 그림별 차이는 런처 override / CLI로만 준다.

v10은 Fig1 dGoal −0.9pp로 FAIL. v11은 threat 0.45·9M 커리큘럼을 유지하고 goal-comm 0.18, consumer 0.15로 메시지에 목표를 실어 쓰게 했다. Fig1 mean dGoal **+3.3pp PASS**.

| 그룹 | 변수 | hub 값 | 하는 일 |
|------|------|--------|---------|
| 구조 | `VESSEL_USE_MOE` | 1 | COLREGS 상황으로 hard-route |
| | `VESSEL_MOE_SHARED` | 1 | 전문가 RadarEncoder를 1벌로 묶음 |
| | `VESSEL_MOE_WIDTH` | 1.0 | 코어 내부 폭 (인터페이스 6D/2D는 불변) |
| 센서·통신 | `VESSEL_MSG_DIM` | 6 | 메시지 차원 |
| | `VESSEL_RADAR_RANGE` | 56 | m |
| | `VESSEL_COMM_RANGE` | 420 | m. 레이더보다 커야 통신이 필요해짐 |
| | `VESSEL_POS_GROUND` | 1 | 상대방위·거리 ⊕ 메시지 → 평균 |
| | `VESSEL_USE_ATTENTION` | 0 | |
| | `VESSEL_USE_COMM` | 1 | |
| | `VESSEL_RADAR_ACT` | leaky | |
| 보조손실 | `VESSEL_THREAT_COEF` | 0.45 | 생산측 위협 복원 (MessageActor만) |
| | `VESSEL_GOAL_COMM_COEF` | 0.18 | 생산측 목표 복원 |
| | `VESSEL_COMM_CONSUMER_COEF` | 0.15 | 수신 Control이 이웃 목표를 쓰게 |
| | `VESSEL_COMM_CONSUMER_COUPLING` | 1 | 복원을 fc3에 연결 |
| | intent / role / recon / primary_align | 0 | 끔 |
| 보상 | `VESSEL_PROGRESS_COEF` | 1.5 | 거리 감소 |
| | `VESSEL_ARRIVAL_REWARD` | 120 | 도착. 올리면 돌진 EV↑ |
| | `VESSEL_COLLISION_PENALTY` | −450 | 겹침 종료. soft라 0%가 최적 아님 |
| | `VESSEL_PROX_COEF` / `PROXRAMP` | −2.0 | 접근 벌점 |
| | `VESSEL_SIM_COLREGS_COEF` | 0.45 | 방향성 비준수 벌점 |

학습 CLI (런처 기본, 메타에 기록):

```
steps=16_000_000  envs=128  vessels=16  rollout=32  ring=0.7
seeds=42,43,44    ckpt_every=2M
hub: comm_on_at=9_000_000  max_partners=4  msg_dim=6  --arm ON
```

PPO는 `config.py` 기본: γ=0.99, λ=0.95, LR 3e-4, clip 0.2. 공유 정책, sender→receiver 재실행으로 메시지 생성까지 역전파.

게이트: `gate_paper_collapse.ps1`만. mid-eval goal<40 또는 oColl>20이면 kill. Fig1 패턴 미스로 죽이지 않음.

---

## 3. 코드가 하는 일

### 3.1 시뮬 `vessel_gym.py`

- 배치 `[E, N]` 선박. N=16. 원형 스폰 ring=0.7.
- obs 369D: 레이더 360 + 목표 2 + 자기 4 + 위치 2 + 상황 1.
- 상황 0–4: 없음 / 정면 / 교차유지 / 교차양보 / 추월. MoE 라우팅과 one-hot에 사용. 기하로 판정, 학습하지 않음.
- 종료: 목표 반경 / 선박 OBB-OBB 겹침(vColl) / 장애물·벽(oColl) / timeout.
- 선체: `SHIP_HALF_LEN≈7.09 m`, `SHIP_HALF_BEAM≈0.96 m`. vColl은 박스 교차이지 “근처”가 아니다. 논문 표기만 근접(분모 포함)으로 바꾼다.
- `--arm OFF`: 메시지 입력을 0. 가중치는 그대로.

### 3.2 네트워크 `networks.py`

세 망이 **각각** RadarEncoder를 가진다. Control과 Message는 인코더를 공유하지 않는다 (`_share_radar_encoder`는 MoE 전문가 **안**에서만).

```
Radar 3×360 → Conv1d×3 (원형 패딩) → Linear → RADAR_FEAT_DIM=30
```

30D는 옛 C# 30섹터 min-pool의 잔재. freeze는 `VESSEL_RADAR_ACT=leaky`만 바꾸고 차원은 그대로다.

| 망 | 입력 | 출력 |
|----|------|------|
| MessageActor | 레이더 + 자기 | 메시지 6D, tanh |
| ControlActor | 레이더 + 자기 + 집계 메시지 | 타각·추력 |
| Critic | 동일 관측 | 가치 |

MoE (`USE_MOE=1`): 상황 인덱스로 전문가 5명 hard-route.  
`MOE_SHARED=1`: 다섯 전문가의 `radar_encoder`를 `experts[0]` 텐서로 통일. state_dict는 5벌 동일 사본으로 저장해 로드 호환.

집계 기본: 거리순 최대 4명, `[sinφ, cosφ, d/420] ⊕ m` → 로컬 인코더 → masked mean (`POS_GROUND=1`).

### 3.3 학습 `vessel_gym_train.py`

`start_paper_train.ps1`가 freeze를 깔고 축 override를 env에 넣은 뒤 이 파일을 띄운다. 중간 ckpt `*.step{2..16}M.pt`, 종료 시 FINAL. Formal은 **FINAL만**. mid를 cherry-pick하지 않는다.

### 3.4 평가 `eval_ckpt.py`

Fig1–6 주지표. 기본 `VESSEL_EVAL_PRIMARY_MODE=v2`.

**프로토콜 (formal = v2 재평가와 동일)**

```
envs=64  burnin=800  eval_decisions=3000  ring=0.7  max_partners=4
```

Fig3만 `max_partners=1`. 창 끝 미완은 집계에서 빼고 `[censored]`로 개수를 남긴다. 첫 종료는 phase 때문에 제외.

PRIMARY v2-strict (요지; env `VESSEL_EVAL_PRIMARY_*` / `VESSEL_EVAL_SO_NULL_Q`):

- 양보(sit 1/3/4): 우현 오프셋≥**15°** **또는** 우현 Δψ≥**15°** **또는** 감속≥**20%**.
- 유지(sit 2): 같은 길이 무조우 창 |Δψ|의 **P60** 이하 **또는** 최근접 < 28.4 m.
- 주지표 = 모든 쌍. 로그에 v2 / v2-dominant / v11 / legacy-step을 같이 찍는다.
- 조건 선택은 계속 **goal/prox**. C는 진단·Fig5용.

`aggregate_eval_v2.py`가 `eval_v2/*.log`를 읽어

- `goal` = 종료분 도착률
- `prox` = vColl건수 / (종료 + censored 미완) × 100
- `C_v2` = 본문 colregsOK (mode=v2이면 PRIMARY)

`FIG*_FORMAL*.txt`와 `eval/*.log`는 덮지 않는다.

Fig7 `eval_mixed.py`는 step-legacy C를 찍지만 **그림에서는 쓰지 않는다** (prox/goal/minSep). Fig8도 step-legacy.

---

## 4. 그림별 구현 (학습 한 축 + 평가)

허브 태그 `qd_MOE_SE_s{42,43,44}` = freeze 그대로, `--arm ON`, partners=4, comm@9M, dim=6.

### Fig1 통신

| 팔 | 태그 | freeze 대비 | 학습 | 평가 |
|----|------|-------------|------|------|
| ON | `qd_MOE_SE_*` | 없음 (hub) | 16M, comm@9M | `--arm ON` |
| OFF | `qf_SE_OFF_*` | 없음 | `--arm OFF`, `comm_on_at=0` | `--arm OFF` |

런처: `start_paper_train.ps1 -Fig hub` 와 `-Fig fig1`.  
차이 = 메시지 채널의 존재뿐. 구조·보상·차원은 같다.

### Fig2 MoE 구조

| 팔 | 태그 | override | 파라미터(YHSH 실측) |
|----|------|----------|---------------------|
| SINGLE | `q_MOE_SINGLE_*` | `USE_MOE=0 SHARED=0` | ~369k |
| THIN | `q_MOE_ISO_*` | `SHARED=0 WIDTH=0.44` | ~363k |
| THICK | `base_comm_*` | `SHARED=0 WIDTH=1.0` | ~1.83M |
| SHARED | hub | freeze | ~512k |

런처: `-Fig fig2 -Arm single|thin|thick`. shared는 `-Fig hub`.  
THIN은 단일망과 파라미터를 맞춰 **전문화 vs 용량**을 분리한다.

### Fig3 집계 폭

| 팔 | 태그 | 차이 |
|----|------|------|
| partners=4 | hub | `max_partners=4` |
| partners=1 | `qf_SE_NEAR1_*` | 학습·평가 모두 `--max_partners 1` |

가중치는 hub와 같다. 평가 때 hub에 `--max_partners 1`만 주면 **1척으로 학습한 정책**이 아니다.

### Fig4 메시지 차원

| 팔 | 태그 | override |
|----|------|----------|
| DIM6 | hub | 6 |
| DIM2/4/8/10/12 | `q_DIM{d}_MX_*` | `VESSEL_MSG_DIM=d` (학습·네트워크 shape) |

**공유 MoE에서** 스윕한다. unique 파라미터는 |m|에 거의 안 변한다(~215–223K).

### Fig5 규정 계수 투입 시점

| 팔 | 태그 | override |
|----|------|----------|
| early | hub | `SIM_COLREGS_COEF=0.45` from step 0 |
| late | `qo_SE_COLREGS_LATE_MX_*` | `--colregs_coef_on_at 9000000` (0→0.45 @9M) |

구조·통신은 hub와 같다. **전면 OFF(coef=0 학습)는 본문 축이 아님** (C만 붕괴).

### Fig6 통신 시점

| 팔 | 태그 | `comm_on_at` |
|----|------|----------------|
| 9M | hub | 9_000_000 |
| 0 | `qo_SE_COMM0_MX_*` | 0 |

총 16M은 같다. 메시지가 흐르기 시작하는 스텝만 다르다.

### Fig7 혼합함대 (학습 없음)

- 스크립트: `eval_fig7_v12mix.ps1` → `eval_mixed.py`
- 정책: hub ×3 시드
- n_rx ∈ {0,2,…,16}. 그 척은 **송신 불가, 수신은 가능** (mode=rx)
- 산출: `runs/paper/v12mix_hub/fig7/mixed_fleet_rx.csv` (+ tracked copy `runs/paper/fig7/`)
- 그림 패널: prox / goal / minSep. step-legacy C는 쓰지 않음.

### Fig8 전역경로 (학습 없음)

- 스크립트: `eval_fig8_paper.ps1` → `astar_fig9/eval_astar_global.py`
- 정책: hub **s42만**. ON/OFF × direct/A*
- `envs=96 burnin=1200 eval_decisions=10000`
- A*는 occupancy 해안선. 정책은 직진 목표로만 학습(웨이포인트 재학습 없음)
- 전체 평균 timeout ~35%. 막힌 쌍 분리: `fig8_blocked_pairs.py` (리포트 미완)

---

## 5. 지표 정의 (v2 표·그림)

| 이름 | 정의 | 쓰는 곳 |
|------|------|---------|
| 도착 goal | 종료 에피소드 중 목표 도달 % | Fig1–6, 그림 막대 |
| 근접 prox | vColl 건수 / (종료 + 창끝 미완) × 100 | Fig1–6 막대. “충돌률”이라고 쓰지 않음 |
| vColl | 종료분만의 선박 박스 겹침 % | CSV에 보존. 표의 주지표 아님 |
| C_v2 | PRIMARY v2 전 쌍 | Fig1–6. Fig5에서만 조건 선택 |
| C_v11 | 옛 주지표 (유지 \|offset\|≤25°) | 병기 |
| sit1–4 | 정면 / 유지 / 양보 / 추월 준수 (v2) | Fig1·3 그룹막대 순서는 Head-On, Give-Way, Overtake, Stand-On |
| fuel, headTravel, minSep, len | **도착 에피소드** 평균 | 효율 패널. minSep은 도착한 배의 항해 중 최소간격 |
| Fig7 prox | CSV `coll` (그 평가의 에피소드 분모) | 그림 (b). Fig1 prox와 직접 비교 금지 |
| Fig8 prox | 로그 vColl. 분모에 TO 포함 | timeout 있는 프로토콜 |

그림 생성: `Python/make_paper_figures.py`  
스타일·개념도는 `reference/YHSH_VESSEL/paper_figures/{figstyle,schematics}.py`를 import.  
출력: `$C/figures/Fig{1–8}_*.png|pdf`  
막대 오차막대는 넣지 않는다. Fig7만 시드 점.

---

## 6. 다시 돌리는 명령

Freeze 로드는 학습 런처가 한다. 평가 스크립트는 `load_paper_freeze.ps1`를 dot-source.

```powershell
# 학습 (예시). FINAL을 덮지 않게 출력을 다른 폴더로 빼는 것이 안전.
cd $C\Python
.\start_paper_train.ps1 -Fig hub -FromScratch   # 합의된 재학습만

# Fig1–6 PRIMARY v2 재평가 → eval_v2/ (있으면 skip)
.\eval_primary_v2_all.ps1

# 표
C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe -u aggregate_eval_v2.py

# 그림
C:\Users\JYH\miniconda3\envs\qxapp\python.exe -u make_paper_figures.py
```

하지 말 것

- `paper_freeze.env` 직접 수정 (해시 파괴)
- `ckpts/final`, `results/FIG*/FIG*_FORMAL*`, `eval/*.log` 삭제·덮어쓰기
- 그림마다 freeze를 따로 튜닝
- mid-ckpt를 FINAL 대신 논문 숫자로 사용
- `main\` 코드를 `$C`에 덮어 쓰고 재평가

---

## 7. 태그 → 그림 빠른 표

| 태그 prefix | 그림 | 한 축 |
|-------------|------|--------|
| `qd_MOE_SE` | hub (1 ON, 2 SHARED, 3×4, 4 DIM6, 5 on, 6@9M) | 없음 |
| `qf_SE_OFF` | 1 | 통신 없음 |
| `q_MOE_SINGLE` | 2 | MoE 끔 |
| `q_MOE_ISO` | 2 | 분리·얇게 |
| `base_comm` | 2 | 분리·두껍게 |
| `qf_SE_NEAR1` | 3 | partners=1 |
| `q_DIM{2,4,8,10,12}` | 4 | msg_dim |
| `qo_SE_COLREGSOFF` | 5 | COLREGS 계수 0 |
| `ql_SE_START` | 6 | comm_on_at=0 |

39 FINAL = 13 조건 × 3 시드. Fig7·8은 이 허브 정책을 평가만 한다.
