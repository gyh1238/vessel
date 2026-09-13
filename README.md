# vessel

Paper campaign workspace for multi-agent COLREGs + communication.

This GitHub copy **does not include checkpoints** (`*.pt`, ~2 GB). Weights stay on the machine that trained freeze `common_freeze_v11`. Start with `campaigns/a2z-2026-09-05_paper_v11/runs/paper/results/v2/DISCUSSION.md`.

```
vessel/
├── HANDOFF.md
├── main/                 latest DT_Vessel code (no nested git)
├── campaigns/
│   └── a2z-2026-09-05_paper_v11/   freeze v11 Python + Fig1–8 tables/figures
├── reference/
│   ├── YHSH_VESSEL/      delivered figure pack / design notes
│   └── manuscripts/      .tex drafts
└── README.md
```

Local-only (gitignored): `archive/`, `repro/`, `ckpts/`, eval logs.

| Need | Open |
|------|------|
| Co-author discussion | `campaigns/.../results/v2/DISCUSSION.md` |
| Claims vs YHSH wording | `.../results/v2/CLAIMS.md` |
| Freeze and per-figure flags | `.../results/v2/IMPLEMENTATION.md` |
| Latest code | `main/` |
| Paper train/eval scripts | `campaigns/a2z-2026-09-05_paper_v11/Python/` |

