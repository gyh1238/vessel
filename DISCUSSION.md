# 공저자 토론용 — 이 논문이 하는 일

2026-09-24, **v12mix** hub + PRIMARY v2-strict 재평가 (FINAL 아님).

숫자·문장 엄밀본: [CLAIMS.md](CLAIMS.md)  
코드·학습 설정: [IMPLEMENTATION.md](IMPLEMENTATION.md)  
그림 파일: [figures/](figures/)  
게이트: `runs/paper/v12mix/GATE.txt`, `runs/paper/v12mix_hub/GATE.txt`, `results/GATE_v12mix_strict.txt`

이 문서는 **그림과 쉬운 말**로 토론하기 위한 것이다. 회의에서 이 파일만 띄워도 된다.

---

## 0. 30초 요약

혼잡한 해역에서 배들이 **레이더만으로는 안 보이는 먼 배**와 짧은 메시지를 주고받으며, COLREGS(항법 규칙) 역할에 맞춰 피하고 목적지에 간다.

묻는 것:

1. 그 메시지가 실제로 도움이 되나? → **예** (Fig1)
2. 상황별 조타를 어디서 나누나? → **눈은 공유, 손만 상황 라우팅** (Fig2). 잔차 Δμ 아님.
3. 규정 점수를 언제 올리나? → **항해 뒤에 올려도 되고, 처음부터 켜도 붕괴는 없다** (Fig5)

제안 허브(v12mix): 공유 MoE + 학습 soft route-mix=0.15(평가는 hard) + Message/Critic 단일 + 타이 인코더.  
Fig1–7은 **같은 레시피** 위에서 축 하나만 바꾼다.  
채점: **PRIMARY v2-strict** (구 v2 천장 ~98%를 소폭 조임 → hub C≈96%).

---

## 1. 배가 사는 세계

16척 · 600×600 m · 레이더 56 m ≪ 통신 420 m · ring 0.7.

```mermaid
flowchart LR
  subgraph 한 척이 매 순간
    R["레이더 56 m"]
    C["통신 420 m"]
    G["목적지"]
    S["속력·타각·역할"]
  end
  R --> π["정책"]
  C --> π
  G --> π
  S --> π
  π --> A["타각 + 추력"]
```

역할(COLREGS)은 기하로 판정한다. 신경망이 고르지 않는다.

---

## 2. 제안 구조 (한 눈)

- **눈(레이더 인코더·백본)은 공유**한다.
- **조타 헤드만** 상황(없음/정면/유지/양보/추월)으로 라우팅한다.
- 학습 때 soft mix=0.15로 희소 헤드에 그라디언트를 흘린다. 평가는 hard.
- Message / Critic는 단일망. **잔차 Δμ가 아니다.**

---

## 3. 숫자를 이렇게 읽자

| 이름 | 쉬운 말 | hub |
|------|---------|-----|
| **도착** | 끝난 항해 중 목적지 도달 | **95.7±0.9%** |
| **근접** | 박스 겹침 / (종료+창끝 미완) | **1.5±0.6%** |
| **C_v2** | PRIMARY v2-strict 준수 | **~96%** |

조건 선택은 **도착·근접**. C는 Fig5에서만 크게 말한다.

---

## 4. 일곱 그림

### Fig1 통신을 켜야 하나?

![Fig1](figures/Fig1_Communication_necessity.png)

| | 도착 | 근접 | C_v2 |
|--|------|------|------|
| OFF | 92.7 | 2.5 | 95.5 |
| ON | **95.7** | **1.5** | 96.2 |

통신: 도착 +3pp, 근접 −1pp (시드 2/3). **C로 통신 이득을 말하지 않는다.**

### Fig2 전문화를 어디서 하나?

![Fig2](figures/Fig2_MoE_architecture.png)

| | 도착 | 근접 |
|--|------|------|
| **SHARED** | **95.7** | **1.5** |
| SINGLE | 95.6 | 1.7 |
| THICK | 92.3 | 2.5 |
| THIN | 87.4 | 4.5 |

SHARED ≥ SINGLE (goal+prox, 시드 2/3). SHARED ≫ THIN/THICK (인식 분리 실패 = C2). Unique params: SHARED≈SINGLE.

### Fig3 이웃을 몇 척 듣나?

![Fig3](figures/Fig3_Multi_neighbour_aggregation.png)

K=4가 K=1보다 낫다 (95.7/1.5 vs 94.6/1.9).

### Fig4 메시지는 몇 차원?

![Fig4](figures/Fig4_Message_dimensionality.png)

DIM2/4 ≪ DIM6. DIM≥6에서 평탄·소폭 악화 → **6이 충분.**  
패널 (c): unique params ~215–223K — **차원↑ = 용량↑가 아님.**

### Fig5 규정 계수를 언제 올리나?

![Fig5](figures/Fig5_COLREGs_shaping.png)

| | 도착 | 근접 | C |
|--|------|------|---|
| late (0→0.45 @9M) | **96.4** | **1.3** | 90.9 |
| early (처음부터 0.45) | 95.7 | 1.5 | **96.2** |

항해가 선 뒤에 올려도 도착·근접은 동등 이상. C는 early가 높다. 전면 OFF 패널은 폐기.

### Fig6 통신을 언제 켜나?

![Fig6](figures/Fig6_Communication_timing.png)

@9M이 @0보다 낫다 (95.7/1.5 vs 93.1/2.5). 처음부터 켜도 시드 붕괴는 없다.

### Fig7 일부만 송신하면? (재학습 없음)

![Fig7](figures/Fig7_Heterogeneous_fleet.png)

같은 mute-TX 스윕, **ON 학습 vs OFF 학습** 정책.  
ON ~95% 평탄, OFF ~93% 평탄 — 송신 희소해도 붕괴 없고, Fig1 ON/OFF 레벨이 유지됨.  
(같은 ON에서 radar vs rx는 이 hub에서 안 갈려 폐기.)

---

## 5. 한눈에

```mermaid
flowchart TB
  Q1["메시지가 필요한가"] --> A1["예. 도착↑ 근접↓"]
  Q2["상황별 눈을 복제?"] --> A2["하지 마라 THIN/THICK 패배"]
  Q3["눈 공유 + 손만 라우팅"] --> A3["SINGLE 이상, 제안으로 유지"]
  Q4["규정 계수를 언제"] --> A4["late도 OK. early가 C↑"]
  Q5["통신 투입 시점"] --> A5["늦게 켜는 편이 낫다"]
  Q6["송신만 막으면"] --> A6["급락 없음. OFF와 다름"]
```

---

## 6. 버리지 말 것

- 잔차 Δμ를 MoE라고 쓰지 않는다.
- YHSH 57%/1.83% 서사 금지.
- FINAL ckpt를 덮어쓰지 않는다.
- Fig1을 C로 증명하지 않는다.
- Fig4를 “용량 폭증”으로 설명하지 않는다.
- 환경 리깅으로 Fig1/Fig2를 맞추지 않는다 (학습 재균형만 허용했고, Fig2는 soft mix로 이김).

회의 전에 `figures/Fig1_….png` … `Fig7_….png`와 [CLAIMS.md](CLAIMS.md)를 같이 띄우면 된다.
