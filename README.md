# vessel

GitHub `main`은 **paper freeze v11** 입니다. 학습 가중치(`*.pt`)는 올리지 않습니다.

`latest/` 는 최신 DT_Vessel 코드 미러입니다. 논문 숫자·그림의 출처가 아닙니다.

```
vessel/
├── README.md
├── DISCUSSION.md         공저자 토론 (개념도 + Fig1–8)
├── CLAIMS.md             쓸 수 있는 주장
├── IMPLEMENTATION.md     freeze · 그림별 플래그
├── ARCHITECTURE.md       관측·신경망 구조
├── figures/              Fig1–8 png/pdf
├── results/              FIG*.txt, metrics.csv
├── Python/               학습·평가
├── Agent/                Unity 선박
├── runs/paper/           ckpts (로컬) · eval 로그
├── latest/               DT_Vessel 미러
└── reference/            YHSH 납품 그림 · tex
```

| Need | Open |
|------|------|
| 공저자 토론 | [DISCUSSION.md](DISCUSSION.md) |
| 쓸 수 있는 주장 | [CLAIMS.md](CLAIMS.md) |
| freeze · 그림별 플래그 | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| 신경망 구조 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Fig1–8 파일 | [figures/](figures/) |
| 표 | [results/](results/) |
| 학습·평가 | `Python/` |

hub (통신 ON, 공유 MoE, 이웃 4, DIM6, COLREGS on, 통신 @9M): **goal 93.7 · prox 2.4 · C_v2 95.9**

## Figures (PRIMARY v2)

![Fig1 Communication necessity](figures/Fig1_Communication_necessity.png)

![Fig2 MoE architecture](figures/Fig2_MoE_architecture.png)

![Fig3 Multi-neighbour aggregation](figures/Fig3_Multi_neighbour_aggregation.png)

![Fig4 Message dimensionality](figures/Fig4_Message_dimensionality.png)

![Fig5 COLREGs shaping](figures/Fig5_COLREGs_shaping.png)

![Fig6 Communication timing](figures/Fig6_Communication_timing.png)

![Fig7 Heterogeneous fleet](figures/Fig7_Heterogeneous_fleet.png)

![Fig8 Global path](figures/Fig8_Global_path.png)
