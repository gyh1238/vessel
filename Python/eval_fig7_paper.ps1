# Fig7: mute TX (rx-only) sweep on frozen hub policies. No retrain.
param(
  [int[]]$Seeds = @(42, 43, 44),
  [string]$Mode = "rx",
  [int]$Gpu = 0,
  [int]$EnvsPer = 14,
  [int]$Burnin = 1200,
  [int]$EvalDecisions = 4500
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv

$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$Out = Join-Path $Paper "fig7"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$csv = Join-Path $Out "mixed_fleet_rx.csv"
$ep = Join-Path $Out "mixed_fleet_rx_episodes.csv"

foreach ($s in $Seeds) {
  $ckpt = Join-Path $Paper "qd_MOE_SE_s$s.pt"
  if (-not (Test-Path $ckpt)) {
    Write-Host "MISSING hub $ckpt — train -Fig hub first"
    continue
  }
  Write-Host "Fig7 seed=$s mode=$Mode"
  $env:CUDA_VISIBLE_DEVICES = "$Gpu"
  & $Py -u eval_mixed.py --ckpt $ckpt --mode $Mode --tag "s$s" `
    --sweep "2,4,6,8,10,12,14" --envs_per $EnvsPer `
    --burnin $Burnin --eval_decisions $EvalDecisions `
    --ring 0.7 --max_partners 4 `
    --csv $csv --ep_csv $ep
}

Write-Host "Fig7 CSV: $csv"
Write-Host "Verify RawData vs plot with same weighted aggregation before paper use."
