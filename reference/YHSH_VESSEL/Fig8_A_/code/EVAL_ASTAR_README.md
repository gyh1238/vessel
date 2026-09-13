# 전역경로(A*) 평가 — `eval_astar_global.py`

구 `Figure/Fig9_Global` 은 `mock_longhaul_estimate.py` 가 만든 **합성 그림**이었음(실측 아님).
이 하네스는 그 실험을 처음으로 실제로 돌리는 것임.

---

## 0. 뭘 하는가

Unity `WaypointPathFinder.cs`(NavMesh A*) → `VesselManager` → `VesselAgent.SetWaypoints` 배선을
`vessel_gym` 배치 심 위에 재현함. 그래야 Fig1~Fig8 과 **같은 정책·같은 지표**로 비교됨.

1. 격자 A* 로 장애물을 피하는 전역경로 산출 → string-pull → 최소간격 병합
   (Unity `CalculatePath` + `SimplifyPath` 미러: 시작점 제외, 목표 항상 포함)
2. waypoint 를 `env.goal` 에 하나씩 꽂음 → 정책은 waypoint 를 목표로 인식
   (`VesselAutoPilot.cs:128` 의 `goalPosition = waypoints[i]` 와 같은 동작)
3. **최종 waypoint 만** 종료 판정 대상. 중간 waypoint 는 종료 안 시킴
4. 지표는 `eval_ckpt.py` 와 같은 정의·같은 출력 형식 (+ `travel`/`plan`/`excess` 추가)

경로 계산은 **(spawn 20 × goal 16) = 320 조합을 초기에 전부 풀어 표로 보관**함.
리스폰마다 A* 를 다시 돌지 않으므로 런타임 비용 0. 초기 계산 16초(Mac CPU).

## 1. 실행

```bash
export VESSEL_MSG_DIM=6 VESSEL_USE_MOE=1 VESSEL_MOE_SHARED=1 VESSEL_MOE_WIDTH=1.0
export VESSEL_USE_COMM=1 VESSEL_RADAR_RANGE=56 VESSEL_THREAT_COEF=0.5
export VESSEL_SIM_COLREGS_COEF=0.45 VESSEL_POS_GROUND=1 VESSEL_USE_ATTENTION=0

python eval_astar_global.py --ckpt ql_SE_START_s42.pt --arm ON --path astar \
    --envs 96 --vessels 16 --max_partners 4 --burnin 1200 --eval_decisions 10000
```

`--path` × `--arm` 2×2 로 돌리면 **전역경로 효과 · 통신 효과 · 둘의 상호작용**이 분리됨.

## 2. 검증 상태

| 항목 | 결과 |
|---|---|
| A* 320 조합 전수 — 팽창영역 관통 | **0건** |
| 〃 — 실충돌반경(r=20) 관통 | **0건** |
| 〃 — 마지막 waypoint = 진짜 목표 | **320/320** |
| 직선이 뚫린 조합 → waypoint 1개(=direct 와 동일) | **172/172** |
| 직선이 막힌 조합 → waypoint ≥2 | **148/148** |
| 경로/직선 비율 | 중앙 1.000 · 최대 1.074 |

`--path direct` 는 `eval_ckpt.py` 와 동일 조건 → **하네스 자체 검증용 대조**로 쓸 것.

발견·수정한 버그 2개 (둘 다 Unity 원본과 대조하며 잡음):
- `SimplifyPath` 의 `Count<=1` 조기반환 누락 → 목표가 중복돼 waypoint 가 2개로 잡히던 것
- string-pull 을 격자 스냅점으로 하고 끝점만 실제 목표로 바꿔치기 → 검사선분과 주행선분 불일치,
  실측 32/320 조합이 팽창영역을 스쳤음. 양 끝을 실제 좌표로 되돌린 뒤 pull 하도록 수정

## 3. 한계 — 결과 해석 전에 반드시 읽을 것

1. **zero-shot 임.** 정책은 waypoint 없이 직행 목표로 학습됐음. A* arm 이 지면
   "A* 가 나쁘다"가 아니라 "이 정책이 waypoint 추종을 못 배웠다"일 수 있음. 주장하려면 재학습 필요.
2. **효과가 희석됨.** 320 조합 중 172개(54%)는 직선이 이미 뚫려 있어 A* 와 direct 가 완전히 동일함.
   전역경로 효과는 나머지 46% 에서만 나타남 → 전체 평균은 절반으로 묽어짐.
   순수 효과를 보려면 막힌 148 조합만 따로 집계해야 함(현재 미구현).
3. **epReward 는 arm 간 비교 금지.** waypoint 전환 때 progress 기준거리를 다시 잡으므로
   보상 스케일이 direct 와 다름. ground-truth(goal%/vColl%/fuel/len)만 쓸 것.
4. **살아남은 체크포인트가 전부 통신 ON 학습분임.** `checkpoints/` 12개 = `ql_SE_*`, `qo_SE_COLREGSOFF_*`,
   `qn_MIXFLEET_*`. 학습-OFF 팔(`base_off`, `qf_SE_OFF`)은 소실됨(`현황과_할일.txt` 1-8).
   → `--arm OFF` 는 *런타임 차단*이지 *학습-OFF* 가 아님. 둘은 다른 주장임.
5. 도착 판정 반경 3.0m 문제(`현황과_할일.txt` 1-1)는 여기서도 그대로임.

---
