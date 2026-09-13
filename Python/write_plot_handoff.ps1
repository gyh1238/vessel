# Bridge paper eval CSVs into YHSH plot inputs (paths only — run after evals).
# Does not regenerate plots; documents the handoff.
$ErrorActionPreference = "Stop"
$Paper = "F:\projects\vessel\repro\a2z-2026-09-05\runs\paper"
$Note = Join-Path $Paper "PLOT_HANDOFF.txt"
@"
Paper freeze plot handoff
=========================
1. Train under runs/paper/ with start_paper_train.ps1
2. Formal bars: eval_paper_ckpt.ps1 / eval_hub_formal.ps1 → runs/paper/eval/*.log
3. Fig7: eval_fig7_paper.ps1 → runs/paper/fig7/mixed_fleet_rx.csv
   Re-aggregate with same weighted scheme as YHSH make_mixed_fleet.py before plotting.
4. Fig8: eval_fig8_paper.ps1 → runs/paper/fig8/*.log
   Blocked pairs: fig8/blocked_pairs.json (n_blocked / n_clear) — report blocked subset separately.
5. Curves: each run's *.csv under runs/paper/ → feed YHSH regenerate_all / make_ablation_rewards
   with paper freeze tags (qd_MOE_SE, qf_SE_OFF, ...).

YHSH plot code: YHSH_VESSEL/Fig*/code/build_final.py and paper_figures/make_paper_figures.py
Do not mix archive/fig1_v* CSVs into paper figures.
"@ | Set-Content -Encoding UTF8 $Note
Write-Host "wrote $Note"
