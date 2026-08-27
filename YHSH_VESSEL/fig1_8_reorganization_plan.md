# Fig.1–Fig.8 재구성 계획

## 0. 전체 원칙

현재 각 실험 폴더에는 동일한 비교를 여러 metric으로 반복한 개별 그래프가 많다. 최종 논문에서는 이를 그대로 6–8 panel에 모두 넣는 대신, **각 Figure가 하나의 설계 질문에 답하도록 재구성**한다.

전체 실험 서사는 다음 순서를 따른다.

1. **Fig.1 — Is communication useful?**
2. **Fig.2 — How should COLREGs-conditioned specialization be structured?**
3. **Fig.3 — How should multiple neighbor messages be combined?**
4. **Fig.4 — How much information should the latent message carry?**
5. **Fig.5 — How should COLREGs knowledge enter the policy objective?**
6. **Fig.6 — When should communication be introduced during learning?**
7. **Fig.7 — Does the policy remain robust when fleet communication capability is heterogeneous?**
8. **Fig.8 — Can the learned local controller be integrated with a route-level planner?**

즉, **Fig.1–6은 알고리즘 설계의 인과적 검증**, **Fig.7–8은 운용 조건에 대한 robustness/integration 검증**으로 역할을 나눈다.

또한 모든 Figure에 collision, arrival, COLREGs, fuel, heading, minimum separation, episode length를 반복해서 넣지 않는다. Figure마다 핵심 질문에 직접 답하는 지표만 남기고, 나머지는 본문 또는 보조표로 이동한다.

---

# Fig.1 — Communication necessity

## 질문

**Does inter-vessel communication improve cooperative navigation beyond local sensing alone?**

이 Figure의 목적은 communication OFF와 ON을 비교하여 통신 자체의 유효성을 검증하는 것이다. Communication timing 문제는 Fig.6에서 분리해서 다룬다.

## 권장 구성: 2×3

### (a) Learning outcome score vs training decisions

- 기존 `0_reward_curve`를 사용.
- Comm OFF / Comm ON 각각 3 seeds의 mean + uncertainty band.
- Fig.6과 역할이 겹치지 않도록 9M communication activation vertical line은 Fig.1에서는 강조하지 않는다.
- 학습곡선용 score는 fixed-policy bar metric과 수치적으로 직접 비교하지 않는다.

### (b) Arrival rate

- OFF: 54.4%
- ON: 55.6%

Arrival은 통신으로 인한 safety gain이 단순히 vessel이 덜 움직여서 생긴 현상이 아님을 보이는 보조 지표다.

### (c) Collision rate

- OFF: 2.77%
- ON: 1.83%

Fig.1의 가장 중요한 quantitative panel.

### (d) Overall COLREGs compliance

- OFF: 48.4%
- ON: 52.3%

### (e) COLREGs compliance by encounter type

- Head-On: 99 → 100%
- Give-Way: 53 → 65%
- Overtaking: 76 → 70%
- Stand-On: 21 → 30%

이 panel은 매우 중요하다. 단순 평균 향상이 아니라, 통신의 가치가 특히 crossing 계열처럼 coordinated intent가 중요한 상황에 집중된다는 점을 보여준다. Overtaking의 역방향 결과도 숨기지 않는다.

### (f) Navigation efficiency

Fuel과 heading travel을 각각 별도 panel로 쓰지 않고, OFF 대비 relative change 또는 normalized bar로 함께 표현한다.

- Fuel: 816 → 802
- Heading travel: 1930° → 1852°

예:

\[
\Delta_{\mathrm{rel}} = \frac{x_{\mathrm{ON}}-x_{\mathrm{OFF}}}{x_{\mathrm{OFF}}}\times100\%.
\]

## 제외/이동

- Minimum separation → 본문 또는 supplementary.
- Episode length → 본문 또는 supplementary.

## Figure가 전달해야 할 한 문장

> Communication mainly improves safety and coordination in interaction-dependent crossing encounters rather than simply increasing arrival rate.

---

# Fig.2 — Shared-perception MoE architecture

## 질문

**Why should perception be shared while COLREGs-conditioned decisions are specialized?**

이 Figure는 논문 전체에서 가장 중요한 algorithm Figure로 취급한다. 단순 performance bar가 아니라 **architecture + parameter cost + navigation performance**를 한 Figure에서 연결한다.

## 권장 구성: 2×2 또는 1 large + 3 small

### (a) Four architecture schematics

네 구조를 동일 visual language로 비교한다.

#### Single network

```text
RadarEncoder → Decision core
```

#### Separate thin MoE

```text
Thin Radar 0 → Decision 0
Thin Radar 1 → Decision 1
...
Thin Radar 4 → Decision 4
```

#### Separate full MoE

```text
Full Radar 0 → Decision 0
Full Radar 1 → Decision 1
...
Full Radar 4 → Decision 4
```

#### Proposed shared-perception MoE

```text
                  → None decision
                  → Head-On decision
Shared Radar ──── → Stand-On decision
                  → Give-Way decision
                  → Overtaking decision
```

실제 구현에서는 MessageActor, ControlActor, Critic 각각에 동일한 expert decomposition이 적용된다는 것을 작은 annotation으로 표시한다.

RadarEncoder block을 decision block보다 시각적으로 크게 그린다. 단일 network parameter 중 radar perception이 약 89%이기 때문에, **왜 perception duplication이 비효율적인지 그림만 봐도 이해되어야 한다.**

### (b) Parameter count

4-arm bar:

- Single: 369,131
- Separate thin: 363,004
- Separate full: 1,826,719
- Proposed shared perception: 511,543

Separate full의 parameter explosion과 proposed의 절충점이 명확히 드러나야 한다.

### (c) Collision rate

4-arm comparison.

현재 확정된 주요 값:

- Single: 6.07%
- Separate thin: 9.50%
- Proposed: 1.83%
- Separate full: 기존 completed run에서 추가

### (d) Arrival rate

4-arm comparison.

현재 주요 값:

- Single: 57.2%
- Separate thin: 33.8%
- Proposed: 55.6%
- Separate full: 기존 completed run에서 추가

Collision만 보여주면 “안 움직여서 안전한 것”이라는 반론이 가능하므로 arrival을 같이 둔다.

## 선택 사항

Parameter–collision Pareto inset을 추가할 수 있다.

x-axis: parameters  
y-axis: collision rate

Proposed가 single보다 안전하고 full separated보다 훨씬 작다는 위치를 한눈에 보여줄 수 있다.

## 주의

- Separate thin은 현재 1 seed이므로 precise effect-size claim에 사용하지 않는다.
- Figure caption에 seed imbalance를 명시한다.
- Full separated arm을 반드시 포함해 4-arm 구조로 완성한다.

## Figure가 전달해야 할 한 문장

> The physical scene is a shared perception problem, whereas COLREGs obligations create situation-specific decision problems; sharing the former while specializing the latter yields a more efficient inductive decomposition.

---

# Fig.3 — Multi-neighbor aggregation

## 질문

**Why should a vessel aggregate several neighbors instead of reacting only to the nearest vessel?**

## 권장 구성: schematic + 3 panels

### (a) Nearest-1 vs nearest-4 communication schematic

Nearest-1:

```text
receiver ← nearest vessel
other valid neighbors discarded
```

Nearest-4:

```text
          m1
           ↘
 m2 → receiver ← m3
           ↗
          m4
```

각 sender의 latent message가 receiver-side relative geometry와 결합되는 것을 표시:

\[
[\sin\phi_{ij},\cos\phi_{ij},d_{ij}/420]\Vert \mathbf m_j
\rightarrow f_{\mathrm{loc}}
\rightarrow \mathbf e_{ij}.
\]

그리고 최종적으로 masked mean:

\[
\bar{\mathbf m}_i = \frac{1}{|\mathcal P_i|}\sum_{j\in\mathcal P_i}\mathbf e_{ij}.
\]

### (b) Collision rate

- Nearest 1: 3.43%
- Nearest 4: 1.83%

Primary panel.

### (c) COLREGs compliance by situation

가능하면 overall이 아니라 상황별 결과를 사용한다.

특히:

- Crossing Stand-On: 약 20.4 → 30.0%
- Crossing Give-Way: 약 56.3 → 64.5%

multi-neighbor communication의 필요성과 직접 연결된다.

### (d) Navigation efficiency

Arrival 차이는 55.0 → 55.6%로 작으므로 별도 panel 가치가 낮다.

대신 nearest-1 대비 normalized efficiency improvement를 사용:

- Fuel: 836 → 802
- Heading travel: 1990° → 1852°

## Figure가 전달해야 할 한 문장

> A pairwise communication bottleneck fails when resolving one encounter changes the geometry of another; several spatially attributed messages allow the policy to act on the local traffic configuration rather than one neighbor at a time.

---

# Fig.4 — Message dimensionality

## 질문

**How much latent channel capacity is required?**

## 권장 구성: 2×2 shared-x line plots

x-axis 공통:

\[
|\mathbf m|\in\{2,4,6,8,10,12\}.
\]

### (a) Arrival rate vs message dimension

### (b) Collision rate vs message dimension

### (c) COLREGs compliance vs message dimension

### (d) Outcome score vs message dimension

현재 데이터:

| Dim | Arrival | Collision | COLREGs | Score |
|---:|---:|---:|---:|---:|
| 2 | 52.2 | 5.87 | 46.8 | 22.1 |
| 4 | 51.9 | 8.20 | 42.5 | 8.7 |
| 6 | 55.3 | 6.40 | 48.7 | 25.5 |
| 8 | 56.4 | 4.00 | 46.1 | 40.7 |
| 10 | 52.5 | 5.70 | 42.9 | 23.7 |
| 12 | 53.3 | 4.87 | 53.3 | 29.9 |

## 표현 원칙

- `d=8 is optimal`이라고 쓰지 않는다.
- 작은 dimension에서 bottleneck이 발생하고, moderate dimension 이후 systematic gain이 없다는 정도로 해석한다.
- 6–8 범위를 moderate-width region으로 옅게 표시하는 것은 가능하다.
- 이 sweep은 **full-width separated MoE**에서 수행되었다는 점을 caption 또는 panel note에 명시한다.
- seed가 없는 condition에 fake error bar를 만들지 않는다.

## Figure가 전달해야 할 한 문장

> Very small messages can become an information bottleneck, whereas increasing latent width beyond a moderate regime does not provide a consistent gain.

---

# Fig.5 — COLREGs shaping

## 질문

**Does the COLREGs term act as a useful coordination prior rather than only as a compliance score?**

## 권장 구성: 1×3 또는 mechanism + 2 performance panels

### (a) Directional noncompliance penalty schematic

대표적인 두 경우만 그린다.

#### Head-On / Give-Way / Overtaking

```text
port turn        starboard turn
   ✗                   ✓
penalized             free
```

#### Stand-On

```text
turn ✗  ←  maintain course ✓  →  turn ✗
```

식도 작게 포함:

\[
R_i^{\mathrm{COLREGs}}
=-\alpha_c(1+\rho_i)\mathbf 1[\rho_i>0.3](\cdots).
\]

이 panel의 목적은 “positive compliance reward”가 아니라 **directional symmetry-breaking penalty**라는 것을 즉시 전달하는 것이다.

### (b) Collision rate

최종적으로 matched proposed 3-seed comparison 사용:

- COLREGs OFF: 약 6.43%
- COLREGs ON: 1.83%

bar + individual seed dots 권장.

### (c) Overall COLREGs compliance

- OFF: 약 31.4%
- ON: 52.3%

bar + individual seed dots.

### 선택적 (d)

Situation-specific compliance가 충분히 깔끔할 경우 추가. 그렇지 않으면 1×3으로 끝내는 편이 낫다.

## 데이터 교체

기존 1-seed OFF / 3-seed ON full-separated figure를 사용하지 않는다.

최종 재생성 대상:

- OFF: `qo_SE_COLREGSOFF_s42/s43/s44`
- ON: `qd_MOE_SE_s42/s43/s44`

## Figure가 전달해야 할 한 문장

> The COLREGs term acts as a domain prior that breaks symmetric but mutually incompatible avoidance choices, improving both rule compliance and collision safety.

---

# Fig.6 — Communication introduction timing

## 질문

**Should communication be learned from the beginning or introduced after a local navigation policy has formed?**

## 권장 구성: 2×2

### (a) Learning curves

두 조건:

- Communication from 0M
- Communication from 9M

x=9M에 vertical dashed line을 명확하게 표시한다.

이 vertical line은 Fig.6에서만 핵심 annotation으로 사용한다.

### (b) Collision rate

- From start: 6.53%
- Delayed: 1.83%

### (c) Arrival rate + seed variability

- From start: 61.3%, seed spread 약 ±14.5 percentage points
- Delayed: 55.6%, seed spread 약 ±1.4 percentage points

단순 mean bar만 쓰면 from-start가 더 좋아 보이므로 **individual seed dots + error bar**를 반드시 포함한다.

### (d) COLREGs compliance

- From start: 46.4%
- Delayed: 52.3%

individual seed dots 권장.

## Figure 해석 원칙

Delayed communication이 모든 metric을 향상시켰다고 주장하지 않는다. Arrival mean은 from-start가 더 높다. 핵심은:

- much lower collision
- higher COLREGs compliance
- far lower seed-to-seed variability

따라서 **safety and optimization stability**의 결과로 해석한다.

## Figure가 전달해야 할 한 문장

> Establishing a stable local control policy before coupling agents through learned communication produces a safer and substantially less seed-sensitive solution.

---

# Fig.7 — Heterogeneous communication fleet

## 질문

**How gracefully does the learned cooperative policy degrade when some vessels cannot transmit?**

## 권장 구성: schematic + 3 degradation curves

x-axis:

\[
N_{\mathrm{Rx-only}}=0,2,4,6,8,10,12,14.
\]

현재 sweep이 2부터 시작하더라도 x=0에는 normal full-communication proposed baseline을 추가하는 것을 권장한다.

secondary x-axis 또는 top label:

```text
Tx-capable vessels
16 14 12 10 8 6 4 2
```

### (a) Fleet composition schematic

16 vessels 중:

- Tx + Rx capable
- Rx-only

를 서로 다른 marker로 표시.

여기서 Rx-only vessel은 메시지를 받을 수 있으나 자신의 메시지는 broadcast하지 않는다는 점을 명시한다.

### (b) Collision rate vs Rx-only vessels

### (c) COLREGs compliance vs Rx-only vessels

### (d) Minimum separation vs Rx-only vessels

이 robustness 실험에서는 fuel/heading보다 minimum separation이 질문에 더 직접적이다.

Fuel/heading은 supplementary 또는 본문으로 이동.

## 현재 blocker

Delivered figure와 raw data 재집계가 일치하지 않는다.

- Delivered-like result: COLREGs 약 51.4–52.3%, collision 약 1.08–2.60%
- Current raw reaggregation: 다른 수치 및 seed count

따라서 provenance 해결 전에는 final figure를 재생성하거나 정량 claim을 확정하지 않는다.

## Figure가 전달해야 할 한 문장

> The deployment question is graceful degradation under heterogeneous communication capability, not whether every vessel must be fully transmitting for the policy to remain safe.

---

# Fig.8 — Global A* + local cooperative policy

## 질문

**Can the learned local cooperative controller operate under an external route-level planner?**

Fig.8은 앞선 ablation figures와 다르게 **system integration figure**로 구성한다.

## 권장 구성: 2×2

### (a) Real-coastline global A* route

현재 Korea–Taiwan route map 활용.

Caption에 명확히:

- coastline occupancy map
- Natural Earth 기반
- AIS traffic digital twin이 아님

### (b) Controlled simulator route example

하나의 obstructed spawn-goal pair를 선택하여 동시에 표시:

- direct straight line
- A* waypoint path
- obstacles
- inflated obstacle boundary
- final goal

이 panel이 real-world map과 quantitative simulator test를 연결한다.

### (c) Collision rate

4 conditions:

1. Direct / Comm OFF
2. Direct / Comm ON
3. A* / Comm OFF
4. A* / Comm ON

각 condition에서 가능하면 두 집합을 같이 표시:

- all 320 spawn-goal pairs
- blocked 148 pairs

### (d) Arrival rate

동일한 4-condition × all/blocked 구성.

작은 annotation:

```text
172 / 320 : direct line already clear
148 / 320 : route altered by A*
```

## 재평가 조건

기존 A* 결과는 final claim에 사용하지 않는다.

최종 rerun 조건:

- proposed checkpoint 사용 (`qd_MOE_SE`, 우선 seed 42부터 검증 후 42–44)
- `ring=0.7`
- direct vs A*
- communication OFF vs ON
- all 320 pairs와 blocked 148 pairs를 분리 보고

## 해석 원칙

현재 policy는 direct-goal training이고 waypoint following으로 retrain하지 않았다. 따라서 Fig.8은 **zero-shot waypoint integration**이다.

A*가 local policy보다 항상 성능을 높인다고 주장할 필요는 없다. 기본 contribution은:

> The learned local cooperative controller can be placed below an external route-level planner without changing its policy architecture.

A*가 obstructed subset에서 추가 성능 향상을 보이면 이를 secondary result로 제시한다.

---

# 전체 Figure narrative

최종 논문에서는 Figure가 다음과 같은 논리적 sequence를 형성하도록 한다.

```text
Fig.1  Communication is useful
   ↓
Fig.2  Specialization should occur in decision, not duplicated perception
   ↓
Fig.3  Several spatially grounded neighbor messages are needed
   ↓
Fig.4  The latent channel need not be large
   ↓
Fig.5  COLREGs provides a directional coordination prior
   ↓
Fig.6  Communication should be introduced after local control stabilizes
   ↓
Fig.7  The learned system degrades gracefully with heterogeneous transmit capability
   ↓
Fig.8  The local controller can be integrated with a global route planner
```

이 구조를 따르면 Fig.1–6이 Proposed Algorithm의 각 design choice를 순서대로 검증하고, Fig.7–8은 deployment/extension 가능성을 보여준다.

---

# Figure 제작 우선순위

실제 재제작 순서는 다음을 권장한다.

1. **Fig.2 — MoE architecture**  
   논문 전체 visual language와 central design principle을 결정.

2. **Fig.5 — COLREGs shaping**  
   기존 figure의 seed imbalance를 제거하고 algorithm mechanism과 result를 연결.

3. **Fig.1 — Communication necessity**  
   전체 communication claim의 기준 figure.

4. **Fig.3 — Multi-neighbor aggregation**  
   position-grounded aggregation의 필요성을 직접 보여줌.

5. **Fig.6 — Communication timing**  
   2-stage learning rationale를 실험적으로 정리.

6. **Fig.4 — Message dimension**  
   기존 data를 line figure로 재배치하면 비교적 쉽게 완료 가능.

7. **Fig.7 — Mixed fleet**  
   raw-data provenance 해결 후 제작.

8. **Fig.8 — A* integration**  
   ring=0.7 + proposed checkpoint rerun 후 최종 제작.

---

# Figure 공통 시각화 원칙

- Seed가 존재하는 실험은 **mean bar/line만 그리지 말고 individual seed dots 또는 uncertainty band를 같이 표시**한다.
- One-seed arm은 caption에 명시하고 fake uncertainty를 만들지 않는다.
- 성능 비교에서 arrival와 collision을 함께 보아 `safe because inactive` 해석을 방지한다.
- Fuel이라는 명칭은 실제 물리 연료소모 모델이 아니라 control-effort proxy라면 final manuscript/axis에서 `fuel/control effort` 또는 더 정확한 표현으로 정리한다.
- Training curve와 fixed-policy bar는 서로 다른 estimator이므로 같은 수치처럼 비교하지 않는다.
- 각 Figure caption 첫 문장은 **무엇을 비교하는지**, 마지막 문장은 **무엇을 결론낼 수 있는지** 명확히 쓴다.
- 동일 실험에서 subplot별 condition ordering, marker, hatch, legend 순서를 통일한다.
- 가능한 경우 raw magnitude보다 논문 질문에 더 적합한 relative change를 사용하되, 핵심 safety metric(collision, compliance)은 실제 값을 유지한다.

---

# 아직 해결해야 하는 데이터 항목

- [ ] Fig.2: full separated 1.83M arm을 최종 4-arm figure에 포함.
- [ ] Fig.2: thin arm 추가 seeds 가능 여부 판단 또는 one-seed disclosure 유지.
- [ ] Fig.5: proposed 3-seed OFF/ON 데이터로 final figure 재생성.
- [ ] Fig.7: delivered figure와 raw-data seed/provenance mismatch 해결.
- [ ] Fig.8: `ring=0.7`, proposed checkpoint로 direct/A* 재평가.
- [ ] Fig.8: all 320 / obstructed 148 pair를 분리 분석.
- [ ] Fig.8: zero-shot waypoint integration임을 caption과 본문에 명시.
