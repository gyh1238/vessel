# Fig7: mute-TX (rx-only) sweep on v12mix hub. No retrain. Never FINAL.
#
# Protocol note (2026-09-24): batched multi-k in one VesselBatchEnv with small
# envs_per inverted the arrival curve and broke the Fig1 ON anchor (n_rx=0).
# Each k is now an isolated run with EnvsPer=64 (same budget as eval_ckpt Fig1).
param(
  [int[]]$Seeds = @(42, 43, 44),
  [string]$Mode = "rx",
  [int[]]$Gpus = @(0, 1, 2),
  [int]$EnvsPer = 64,
  [int]$Burnin = 800,
  [int]$EvalDecisions = 3000,
  [string]$Sweep = "0,2,4,6,8,10,12,14,16"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"

$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$Hub = Join-Path $Paper "v12mix_hub"
$Out = Join-Path $Hub "fig7"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$tag = if ($Mode -eq "radar") { "radar" } else { "rx" }
$csv = Join-Path $Out "mixed_fleet_$tag.csv"
$ep = Join-Path $Out "mixed_fleet_${tag}_episodes.csv"
$Status = Join-Path $Hub "STATUS.txt"
$Ks = @($Sweep.Split(',') | ForEach-Object { [int]$_.Trim() } | Where-Object { $_ -ge 0 })

function Write-Status([string]$msg) {
  $line = "{0}  {1}" -f (Get-Date -Format o), $msg
  Add-Content -Path $Status -Value $line -Encoding UTF8
  Write-Host $line
}
function Set-Fig7Freeze {
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
}

Write-Status "Fig7 v12mix hub start mode=$Mode sweep=$Sweep envs_per=$EnvsPer gpus=$($Gpus -join ',') isolated-k=1"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path $csv) {
  Copy-Item $csv (Join-Path $Out "mixed_fleet_${tag}.prev_$ts.csv")
  Remove-Item $csv -EA SilentlyContinue
}
Remove-Item $ep -EA SilentlyContinue

# Per-seed CSVs to avoid concurrent append races.
$seedJobs = @()
$gi = 0
foreach ($s in $Seeds) {
  $ckpt = Join-Path $Hub "qd_MOE_SE_MX_s$s.pt"
  if (-not (Test-Path $ckpt)) { throw "missing $ckpt" }
  $gpu = $Gpus[$gi % $Gpus.Count]; $gi++
  $seedCsv = Join-Path $Out "mixed_fleet_${tag}_s$s.csv"
  $seedEp = Join-Path $Out "mixed_fleet_${tag}_s${s}_episodes.csv"
  $log = Join-Path $Out "rerun_iso_${tag}_s$s.log"
  Remove-Item $seedCsv, $seedEp, $log -EA SilentlyContinue
  $script = Join-Path $Out "_iso_seed_${tag}_s$s.ps1"
  $kList = ($Ks -join ',')
  @"
`$ErrorActionPreference = 'Stop'
`$env:CUDA_VISIBLE_DEVICES = '$gpu'
cd '$Root'
. '.\load_paper_freeze.ps1'
Set-PaperFreezeEnv -Override @{
  VESSEL_TIE_MSG_CTRL_ENC='1'; VESSEL_MOE_SHARED='1'; VESSEL_MOE_SHARE_BACKBONE='1'
  VESSEL_MOE_ROUTE_MIX='0.15'; VESSEL_MOE_RESIDUAL_HEAD='0'; VESSEL_MOE_MSG='0'; VESSEL_MOE_CRITIC='0'
  VESSEL_EVAL_APPLY_SNAPSHOT='1'
}
foreach (`$k in @($kList)) {
  Write-Host ("Fig7 $Mode s$s k=`$k gpu=$gpu")
  & '$Py' -u eval_mixed.py --ckpt '$ckpt' --mode '$Mode' --tag 's$s' --sweep ("{0}" -f `$k) --envs_per $EnvsPer --burnin $Burnin --eval_decisions $EvalDecisions --ring 0.7 --max_partners 4 --csv '$seedCsv' --ep_csv '$seedEp'
  if (`$LASTEXITCODE -ne 0) { throw "Fig7 $Mode s$s k=`$k exit=`$LASTEXITCODE" }
}
"@ | Set-Content $script -Encoding UTF8
  Write-Status "launch mode=$Mode seed=$s gpu=$gpu"
  $seedJobs += Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $script
  ) -PassThru -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError "$log.err"
}

while ($seedJobs | Where-Object { -not $_.HasExited }) { Start-Sleep -Seconds 30 }
foreach ($j in $seedJobs) {
  if (-not $j.HasExited) { throw "Fig7 seed worker pid=$($j.Id) still running" }
  if ($null -ne $j.ExitCode -and $j.ExitCode -ne 0) {
    throw "Fig7 seed worker pid=$($j.Id) exit=$($j.ExitCode)"
  }
}

# Merge
$header = $null
foreach ($s in $Seeds) {
  $seedCsv = Join-Path $Out "mixed_fleet_${tag}_s$s.csv"
  if (-not (Test-Path $seedCsv)) { throw "missing $seedCsv" }
  $lines = Get-Content $seedCsv
  if ($null -eq $header) { $header = $lines[0]; Set-Content $csv $header }
  $lines | Select-Object -Skip 1 | Add-Content $csv
  $seedEp = Join-Path $Out "mixed_fleet_${tag}_s${s}_episodes.csv"
  if (Test-Path $seedEp) {
    $el = Get-Content $seedEp
    if (-not (Test-Path $ep)) { Set-Content $ep $el[0] }
    $el | Select-Object -Skip 1 | Add-Content $ep
  }
}
# Tracked paper copy: keep rx name for figure loader; radar stays under hub/fig7 only.
if ($tag -eq "rx") {
  Copy-Item $csv (Join-Path $Paper "fig7\mixed_fleet_rx.csv") -Force
}
Write-Status "Fig7 CSV $csv"
Write-Status "Fig7 v12mix hub complete mode=$Mode"
