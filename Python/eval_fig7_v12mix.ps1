# Fig7: mute-TX (rx-only) sweep on v12mix hub. No retrain. Never FINAL.
param(
  [int[]]$Seeds = @(42, 43, 44),
  [string]$Mode = "rx",
  [int]$Gpu = 0,
  [int]$EnvsPer = 7,
  [int]$Burnin = 800,
  [int]$EvalDecisions = 3000,
  [string]$Sweep = "0,2,4,6,8,10,12,14,16"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv -Override @{
  VESSEL_TIE_MSG_CTRL_ENC   = "1"
  VESSEL_MOE_SHARED         = "1"
  VESSEL_MOE_SHARE_BACKBONE = "1"
  VESSEL_MOE_ROUTE_MIX      = "0.15"
  VESSEL_MOE_RESIDUAL_HEAD  = "0"
  VESSEL_MOE_MSG            = "0"
  VESSEL_MOE_CRITIC         = "0"
  VESSEL_EVAL_APPLY_SNAPSHOT = "1"
}

$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$Hub = Join-Path $Paper "v12mix_hub"
$Out = Join-Path $Hub "fig7"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$csv = Join-Path $Out "mixed_fleet_rx.csv"
$ep = Join-Path $Out "mixed_fleet_rx_episodes.csv"
$Status = Join-Path $Hub "STATUS.txt"

function Write-Status([string]$msg) {
  $line = "{0}  {1}" -f (Get-Date -Format o), $msg
  Add-Content -Path $Status -Value $line -Encoding UTF8
  Write-Host $line
}

Write-Status "Fig7 v12mix hub start mode=$Mode sweep=$Sweep"
foreach ($s in $Seeds) {
  $ckpt = Join-Path $Hub "qd_MOE_SE_MX_s$s.pt"
  if (-not (Test-Path $ckpt)) { throw "missing $ckpt" }
  Write-Status "Fig7 seed=$s"
  $env:CUDA_VISIBLE_DEVICES = "$Gpu"
  & $Py -u eval_mixed.py --ckpt $ckpt --mode $Mode --tag "s$s" `
    --sweep $Sweep --envs_per $EnvsPer `
    --burnin $Burnin --eval_decisions $EvalDecisions `
    --ring 0.7 --max_partners 4 `
    --csv $csv --ep_csv $ep
  if ($LASTEXITCODE -ne 0) { throw "Fig7 seed $s exit=$LASTEXITCODE" }
}
Write-Status "Fig7 CSV $csv"
Write-Status "Fig7 v12mix hub complete"
