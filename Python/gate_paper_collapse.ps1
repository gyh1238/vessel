# Collapse-only gate for paper runs (anti-cherry-pick).
# Kill paper trainers if mid frozen eval shows goal<40 OR oColl>20.
# Does NOT kill for Fig1 ON/OFF pattern misses.
param(
  [string]$OutName = "paper",
  [double]$MinGoal = 40.0,
  [double]$MaxOColl = 20.0,
  [int]$PollSec = 120
)

$ErrorActionPreference = "Continue"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv

$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Out  = Join-Path (Split-Path $Root -Parent) "runs\$OutName"
$Gate = Join-Path $Out "gate"
New-Item -ItemType Directory -Force -Path $Gate | Out-Null
$Hist = Join-Path $Gate "collapse_history.txt"
$done = @{}
# Resume: skip ckpts already successfully gated (SKIP_EARLY / goal= / FAIL), not NO_PARSE.
# Match any *.step*M.pt token (qd_*, qf_*, q_MOE_*, base_comm_*, …).
if (Test-Path $Hist) {
  Get-Content $Hist -EA SilentlyContinue | ForEach-Object {
    if ($_ -match 'NO_PARSE') { return }
    if ($_ -match '([\w.-]+\.step[\d.]+M\.pt)') { $done[$Matches[1]] = $true }
  }
  Write-Host "gate resume: seeded $($done.Count) done keys from history"
}

function Kill-Paper([string]$Reason) {
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object {
      $_.CommandLine -and
      $_.CommandLine -match 'vessel_gym_train' -and
      $_.CommandLine -match 'runs[\\/]+paper'
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
  $Reason | Set-Content -Encoding UTF8 (Join-Path $Out "GATE_FAILED.txt")
  "$(Get-Date -Format o) FAIL $Reason" | Add-Content $Hist
  Write-Host "GATE FAIL: $Reason"
}

function Invoke-ShortEval([string]$Ckpt, [string]$Arm, [string]$Logf, [string]$Gpu) {
  Set-PaperFreezeEnv
  # msg dim / moe from ckpt meta if needed — freeze default; dim runs set via sidecar
  $meta = "$Ckpt" -replace '\.pt$', '.meta.txt' -replace '\.step[\d.]+M', ''
  if (Test-Path $meta) {
    $line = Select-String -Path $meta -Pattern 'VESSEL_MSG_DIM=(\d+)' -EA SilentlyContinue
    if ($line -and $line.Line -match 'VESSEL_MSG_DIM=(\d+)') { $env:VESSEL_MSG_DIM = $Matches[1] }
    if (Select-String -Path $meta -Pattern 'VESSEL_USE_MOE=0' -Quiet) { $env:VESSEL_USE_MOE = "0" }
    if (Select-String -Path $meta -Pattern 'VESSEL_MOE_SHARED=0' -Quiet) { $env:VESSEL_MOE_SHARED = "0" }
    if (Select-String -Path $meta -Pattern 'VESSEL_MOE_WIDTH=0\.44' -Quiet) { $env:VESSEL_MOE_WIDTH = "0.44" }
    if (Select-String -Path $meta -Pattern 'VESSEL_SIM_COLREGS_COEF=0' -Quiet) { $env:VESSEL_SIM_COLREGS_COEF = "0" }
  }
  $env:CUDA_VISIBLE_DEVICES = $Gpu
  $p = Start-Process -FilePath $Py -ArgumentList @(
    "-u", "eval_ckpt.py", "--ckpt", $Ckpt, "--arm", $Arm,
    "--envs", "64", "--burnin", "800", "--eval_decisions", "1500",
    "--ring", "0.7", "--max_partners", "4", "--device", "cuda:0"
  ) -WorkingDirectory $Root -RedirectStandardOutput $Logf -RedirectStandardError "$Logf.err" -PassThru -WindowStyle Hidden
  Wait-Process -Id $p.Id -Timeout 700 -EA SilentlyContinue
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -EA SilentlyContinue }
}

"collapse gate started $(Get-Date -Format o) minGoal=$MinGoal maxOColl=$MaxOColl" | Add-Content $Hist
Write-Host "paper collapse gate started"

while ($true) {
  if (Test-Path (Join-Path $Out "GATE_FAILED.txt")) { break }
  $nTrain = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object {
      $_.CommandLine -and
      $_.CommandLine -match 'vessel_gym_train' -and
      $_.CommandLine -match 'runs[\\/]+paper'
    }).Count

  $ckpts = Get-ChildItem (Join-Path $Out "*.step*.pt") -EA SilentlyContinue
  foreach ($c in $ckpts) {
    $key = $c.Name
    if ($done.ContainsKey($key)) { continue }
    $stepM = 0.0
    if ($c.Name -match 'step([0-9.]+)M') { $stepM = [double]$Matches[1] }
    # Early training is noisy; only enforce collapse after 6M (pre-comm curriculum).
    if ($stepM -gt 0 -and $stepM -lt 6.0) {
      $done[$key] = $true
      "$(Get-Date -Format o) SKIP_EARLY $key" | Add-Content $Hist
      continue
    }
    # Arm: Fig1 OFF tags are *_SE_OFF_*; do NOT treat COLREGSOFF as arm OFF.
    $arm = if ($c.Name -match 'SE_OFF') { "OFF" } else { "ON" }
    $logf = Join-Path $Gate ($c.BaseName + ".eval.log")
    Write-Host "eval $key"
    Invoke-ShortEval $c.FullName $arm $logf "0"
    $g = Select-String -Path $logf -Pattern 'goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%' -EA SilentlyContinue |
      Select-Object -Last 1
    if (-not $g) {
      "$(Get-Date -Format o) NO_PARSE $key (eval incomplete?)" | Add-Content $Hist
      continue
    }
    if ($g.Line -notmatch 'goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%') { continue }
    $goal = [double]$Matches[1]; $oColl = [double]$Matches[3]
    $line = "$(Get-Date -Format o) $key goal=$goal oColl=$oColl"
    $line | Add-Content $Hist
    Write-Host $line
    $done[$key] = $true
    if ($goal -lt $MinGoal -or $oColl -gt $MaxOColl) {
      Kill-Paper "collapse $key goal=$goal oColl=$oColl"
      break
    }
  }

  # Stay alive across phase gaps (trainers briefly 0 between arms).
  # Exit only on explicit GATE_STOP.txt (or GATE_FAILED from collapse).
  if (Test-Path (Join-Path $Out "GATE_STOP.txt")) {
    "GATE_STOP $(Get-Date -Format o)" | Set-Content (Join-Path $Out "GATE_OK.txt")
    Write-Host "GATE_STOP requested — gate exit OK"
    break
  }
  $pending = @($ckpts | Where-Object {
    $_.Name -match 'step([0-9.]+)M' -and [double]$Matches[1] -ge 6.0 -and -not $done.ContainsKey($_.Name)
  }).Count
  if ($nTrain -eq 0 -and $pending -eq 0) {
    Write-Host "idle (no trainers, no pending mid-ckpts) — waiting for next arm or GATE_STOP"
  }
  Start-Sleep $PollSec
}
