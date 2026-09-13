# DEPRECATED for paper figures. Use start_paper_train.ps1 + paper_freeze.env instead.
# This fig1_v4 recipe mixes COLREGS/aux/curriculum knobs and is NOT a single-axis ablation.
# Kept only for archival re-runs of contaminated v4 experiments.
param(
  [int]$Steps = 16000000,
  [int]$Envs = 128,
  [double]$CkptEvery = 2,
  [switch]$FromScratch,
  [string]$OutName = "fig1_v4",
  [int]$CommOnAt = 6000000,
  [double]$Ring = 0.7
)

$ErrorActionPreference = "Stop"
$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = "F:\projects\vessel\repro\a2z-2026-09-05\Python"
$Out  = "F:\projects\vessel\repro\a2z-2026-09-05\runs\$OutName"
$Log  = "F:\projects\vessel\repro\a2z-2026-09-05\runs\logs"
New-Item -ItemType Directory -Force -Path $Out, $Log | Out-Null

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'vessel_gym_train' } |
  ForEach-Object { Write-Host "kill $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
Start-Sleep -Seconds 2

$env:PYTHONUNBUFFERED = "1"
$env:VESSEL_USE_MOE = "1"
$env:VESSEL_MOE_SHARED = "1"
$env:VESSEL_MOE_WIDTH = "1.0"
$env:VESSEL_MSG_DIM = "6"
$env:VESSEL_POS_GROUND = "1"
$env:VESSEL_USE_ATTENTION = "0"
$env:VESSEL_RADAR_ACT = "leaky"
$env:VESSEL_USE_COMM = "1"

# === same as v2 (do NOT touch denser ring — v3 lesson) ===
$env:VESSEL_COMM_RANGE = "420"
$env:VESSEL_PROGRESS_COEF = "1.5"
$env:VESSEL_ARRIVAL_REWARD = "120"
$env:VESSEL_COLLISION_PENALTY = "-450"
$env:VESSEL_PROX_COEF = "-2.0"
$env:VESSEL_PROXRAMP_COEF = "-2.0"

# === DIFFERENT from v2 (COLREGs + message channel) ===
$env:VESSEL_SIM_COLREGS_COEF = "0.70"              # v2: 0.45
$env:VESSEL_COLREGS_PRIMARY_ALIGN = "1.0"          # v2: 0
$env:VESSEL_THREAT_COEF = "0.8"                    # v2: 0.5
$env:VESSEL_ROLE_COMM_COEF = "0.10"                # v2: 0
$env:VESSEL_GOAL_COMM_COEF = "0.05"                # v2: 0
$env:VESSEL_INTENT_COEF = "0.05"                   # v2: 0
$env:VESSEL_COMM_CONSUMER_COEF = "0.05"            # v2: 0
$env:VESSEL_COMM_CONSUMER_COUPLING = "1"           # v2: 0
$env:VESSEL_STATE_RECON_COEF = "0"

$runs = @(
  @{Tag="fig1_off_s42"; Arm="OFF"; Seed=42; Gpu=0; Comm=0},
  @{Tag="fig1_on_s42";  Arm="ON";  Seed=42; Gpu=1; Comm=$CommOnAt},
  @{Tag="fig1_off_s43"; Arm="OFF"; Seed=43; Gpu=2; Comm=0},
  @{Tag="fig1_on_s43";  Arm="ON";  Seed=43; Gpu=3; Comm=$CommOnAt}
)

function Find-LatestCkpt([string]$tag) {
  $files = Get-ChildItem (Join-Path $Out "$tag.step*.pt") -EA SilentlyContinue |
    Sort-Object { [double]($_.BaseName -replace '.*step','' -replace 'M$','') } -Descending
  if ($files) { return $files[0] }
  $final = Join-Path $Out "$tag.pt"
  if (Test-Path $final) { return Get-Item $final }
  return $null
}

foreach ($r in $runs) {
  $env:CUDA_VISIBLE_DEVICES = "$($r.Gpu)"
  $save = Join-Path $Out "$($r.Tag).pt"
  $csv  = Join-Path $Out "$($r.Tag).csv"
  $logf = Join-Path $Log "$OutName`_$($r.Tag).log"
  $argList = [System.Collections.Generic.List[string]]::new()
  $argList.AddRange([string[]]@(
    "-u", "vessel_gym_train.py",
    "--arm", $r.Arm,
    "--steps", "$Steps",
    "--envs", "$Envs",
    "--vessels", "16",
    "--rollout", "32",
    "--ring", "$Ring",
    "--seed", "$($r.Seed)",
    "--max_partners", "4",
    "--comm_on_at", "$($r.Comm)",
    "--ckpt_every", "$CkptEvery",
    "--save", $save,
    "--csv", $csv
  ))

  $ckpt = $null
  if (-not $FromScratch) { $ckpt = Find-LatestCkpt $r.Tag }
  if ($ckpt) {
    $m = [regex]::Match($ckpt.Name, 'step([0-9.]+)M')
    $at = if ($m.Success) { [int]([double]$m.Groups[1].Value * 1e6) } else { 0 }
    if ($at -ge $Steps) { Write-Host "skip $($r.Tag) done"; continue }
    $argList.AddRange([string[]]@("--resume", $ckpt.FullName, "--resume_at", "$at", "--resume_warmup", "1200"))
    Write-Host "RESUME $($r.Tag) from $($ckpt.Name) at $at GPU$($r.Gpu)"
  } else {
    Write-Host "FRESH  $($r.Tag) GPU$($r.Gpu)"
  }

  @"
tag=$($r.Tag) arm=$($r.Arm) seed=$($r.Seed) gpu=$($r.Gpu)
recipe=fig1_v4  !=v2  !=v3
KEEP: ring=$Ring comm=420 progress=1.5 arrival=120 coll=-450 prox=-2
DIFF: colregs=0.70 primary_align=1 threat=0.8 role/goal/intent/consumer+coupling
comm_on_at=$($r.Comm) steps=$Steps
gate: every 2M frozen eval — kill if oColl>20% or goal<40%
started=$(Get-Date -Format o)
"@ | Set-Content -Encoding UTF8 (Join-Path $Out "$($r.Tag).meta.txt")

  Start-Process -FilePath $Py -ArgumentList $argList -WorkingDirectory $Root `
    -RedirectStandardOutput $logf -RedirectStandardError "$logf.err" -WindowStyle Hidden
  Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "Out: $Out"
Write-Host "v4 = v2 safety + COLREGs/msg DIFF + mid-eval kill gate"
