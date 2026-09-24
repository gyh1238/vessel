# Paper Fig1–6 trainer: freeze + one-axis override only.
# Examples:
#   .\start_paper_train.ps1 -Fig hub -FromScratch
#   .\start_paper_train.ps1 -Fig fig1
#   .\start_paper_train.ps1 -Fig fig2 -Arm thin
#   .\start_paper_train.ps1 -Fig fig4 -DryRun
param(
  [ValidateSet("hub", "fig1", "fig2", "fig3", "fig4", "fig5", "fig6")]
  [string]$Fig = "hub",
  [string]$Arm = "",
  [int]$Steps = 16000000,
  [int]$Envs = 128,
  [double]$CkptEvery = 2,
  [double]$Ring = 0.7,
  # v4/v6/v8: solo nav before channel @9M. Fig6 axis = 0 vs this.
  # v7@8M helped s42 but collapsed s44 ON — reverted.
  [int]$CommOnAt = 9000000,
  [int[]]$Seeds = @(),
  # Prefer -SeedList / -GpuList when calling via powershell.exe -File (commas bind badly otherwise).
  [string]$SeedList = "42,43,44",
  [string]$GpuList = "0,1,2,3",
  [int[]]$Gpus = @(),
  [switch]$FromScratch,
  [switch]$DryRun,
  [switch]$KillExisting
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"

if ($Seeds -and $Seeds.Count -gt 0) {
  # keep explicit -Seeds 42 -Seeds 43 ... if provided as repeated binds
} else {
  $Seeds = @($SeedList.Split(',') | ForEach-Object { [int]($_.Trim()) })
}
if (-not $Seeds -or $Seeds.Count -eq 0) { throw "no Seeds configured" }

if ($Gpus -and $Gpus.Count -gt 0) {
  # keep explicit -Gpus 0 -Gpus 1 ... if provided as repeated binds
} else {
  $Gpus = @($GpuList.Split(',') | ForEach-Object { [int]($_.Trim()) })
}
if (-not $Gpus -or $Gpus.Count -eq 0) { throw "no GPUs configured" }

$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Runs = Join-Path (Split-Path $Root -Parent) "runs"
$Out  = Join-Path $Runs "paper"
$Log  = Join-Path $Runs "logs"
New-Item -ItemType Directory -Force -Path $Out, $Log | Out-Null

$FreezeHash = Get-PaperFreezeHash
Write-Host "paper_freeze hash=$FreezeHash fig=$Fig arm=$Arm"

if ($KillExisting) {
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'vessel_gym_train' -and $_.CommandLine -match '\\runs\\paper\\' } |
    ForEach-Object { Write-Host "kill $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
  Start-Sleep 2
}

# Spec: Tag, Arm, Seed, EnvOverride hashtable, CommOnAt, MaxPartners, MsgDim
function New-Spec([string]$Tag, [string]$ArmName, [int]$Seed, [hashtable]$Ov, [int]$Comm, [int]$Partners = 4, [int]$MsgDim = 6) {
  return [pscustomobject]@{
    Tag = $Tag; Arm = $ArmName; Seed = $Seed
    Override = $Ov; Comm = $Comm; Partners = $Partners; MsgDim = $MsgDim
  }
}

$specs = [System.Collections.Generic.List[object]]::new()
$empty = @{}

function Add-Seeds([string]$Prefix, [string]$ArmName, [hashtable]$Ov, [int]$Comm, [int]$Partners = 4, [int]$MsgDim = 6) {
  foreach ($s in $Seeds) {
    $specs.Add((New-Spec "${Prefix}_s$s" $ArmName $s $Ov $Comm $Partners $MsgDim))
  }
}

switch ($Fig) {
  "hub" {
    Add-Seeds "qd_MOE_SE" "ON" $empty $CommOnAt
  }
  "fig1" {
    # ON = hub (do not retrain here)
    Add-Seeds "qf_SE_OFF" "OFF" $empty 0
  }
  "fig2" {
    $want = if ($Arm) { $Arm.ToLower() } else { "all" }
    if ($want -in @("all", "single")) {
      Add-Seeds "q_MOE_SINGLE" "ON" @{ VESSEL_USE_MOE = "0"; VESSEL_MOE_SHARED = "0" } $CommOnAt
    }
    if ($want -in @("all", "thin")) {
      Add-Seeds "q_MOE_ISO" "ON" @{ VESSEL_MOE_WIDTH = "0.44"; VESSEL_MOE_SHARED = "0" } $CommOnAt
    }
    if ($want -in @("all", "thick")) {
      Add-Seeds "base_comm" "ON" @{ VESSEL_MOE_SHARED = "0"; VESSEL_MOE_WIDTH = "1.0" } $CommOnAt
    }
    if ($want -eq "shared") {
      Write-Host "shared = hub (qd_MOE_SE). Use -Fig hub."
    }
  }
  "fig3" {
    Add-Seeds "qf_SE_NEAR1" "ON" $empty $CommOnAt 1
  }
  "fig4" {
    $dims = if ($Arm -match '^\d+$') { @([int]$Arm) } else { @(2, 4, 8, 10, 12) }
    foreach ($d in $dims) {
      Add-Seeds "q_DIM$d" "ON" @{ VESSEL_MSG_DIM = "$d" } $CommOnAt 4 $d
    }
  }
  "fig5" {
    # 계수 스윕. 0 = 항 없음(기존 태그). 0.45 = hub(재학습하지 않음).
    $coef = if ($Arm -match '^[0-9.]+$') { [double]$Arm } else { $null }
    if ($null -eq $coef) {
      Add-Seeds "qo_SE_COLREGSOFF" "ON" @{ VESSEL_SIM_COLREGS_COEF = "0" } $CommOnAt
    } elseif ([math]::Abs($coef - 0.0) -lt 1e-9) {
      Add-Seeds "qo_SE_COLREGSOFF" "ON" @{ VESSEL_SIM_COLREGS_COEF = "0" } $CommOnAt
    } elseif ([math]::Abs($coef - 0.45) -lt 1e-9) {
      Write-Host "coef 0.45 = hub (qd_MOE_SE). Use -Fig hub."
    } else {
      $tag = ("qo_SE_C{0}" -f ($coef.ToString("0.00", [System.Globalization.CultureInfo]::InvariantCulture) -replace '\.', 'p'))
      Add-Seeds $tag "ON" @{ VESSEL_SIM_COLREGS_COEF = "$coef" } $CommOnAt
    }
  }
  "fig6" {
    Add-Seeds "ql_SE_START" "ON" $empty 0
  }
}

if ($Arm -and $Fig -notin @("fig2", "fig4", "fig5")) {
  $specs = [System.Collections.Generic.List[object]]@($specs | Where-Object { $_.Tag -match [regex]::Escape($Arm) })
}

if ($specs.Count -eq 0) { throw "no runs selected for Fig=$Fig Arm=$Arm" }

function Find-LatestCkpt([string]$tag) {
  $files = Get-ChildItem (Join-Path $Out "$tag.step*.pt") -EA SilentlyContinue |
    Sort-Object { [double]($_.BaseName -replace '.*step', '' -replace 'M$', '') } -Descending
  if ($files) { return $files[0] }
  $final = Join-Path $Out "$tag.pt"
  if (Test-Path $final) { return Get-Item $final }
  return $null
}

$gi = 0
foreach ($r in $specs) {
  $gpu = $Gpus[$gi % $Gpus.Count]
  $gi++
  $ov = @{}
  foreach ($k in $r.Override.Keys) { $ov[$k] = $r.Override[$k] }
  if ($r.MsgDim -ne 6) { $ov["VESSEL_MSG_DIM"] = "$($r.MsgDim)" }

  Set-PaperFreezeEnv -Override $ov
  $save = Join-Path $Out "$($r.Tag).pt"
  $csv  = Join-Path $Out "$($r.Tag).csv"
  $logf = Join-Path $Log "paper_$($r.Tag).log"
  $meta = Join-Path $Out "$($r.Tag).meta.txt"

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
    "--max_partners", "$($r.Partners)",
    "--comm_on_at", "$($r.Comm)",
    "--ckpt_every", "$CkptEvery",
    "--save", $save,
    "--csv", $csv
  ))

  $ckpt = $null
  if (-not $FromScratch) { $ckpt = Find-LatestCkpt $r.Tag }
  $resumeAt = 0
  if ($ckpt) {
    $m = [regex]::Match($ckpt.Name, 'step([0-9.]+)M')
    $resumeAt = if ($m.Success) { [int]([double]$m.Groups[1].Value * 1e6) } else { 0 }
    if ($resumeAt -ge $Steps) {
      Write-Host "skip $($r.Tag) done"
      continue
    }
    $argList.AddRange([string[]]@("--resume", $ckpt.FullName, "--resume_at", "$resumeAt", "--resume_warmup", "1200"))
    Write-Host "RESUME $($r.Tag) from $($ckpt.Name) at $resumeAt GPU$gpu"
  } else {
    Write-Host "FRESH  $($r.Tag) GPU$gpu partners=$($r.Partners) comm_on_at=$($r.Comm)"
  }

  $ovText = ($ov.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join " "
  @"
tag=$($r.Tag) arm=$($r.Arm) seed=$($r.Seed) gpu=$gpu
freeze=$FreezeHash version=common_freeze_v11
fig=$Fig
CLI: steps=$Steps envs=$Envs ring=$Ring partners=$($r.Partners) comm_on_at=$($r.Comm) msg_dim=$($r.MsgDim)
override: $ovText
principle: shared WORKING baseline across Fig1-8; one axis only; not YHSH coef clone
gate: collapse-only (see gate_paper_collapse.ps1)
started=$(Get-Date -Format o)
"@ | Set-Content -Encoding UTF8 $meta

  if ($DryRun) {
    Write-Host "DRY CUDA_VISIBLE_DEVICES=$gpu $($argList -join ' ')"
    continue
  }

  $env:CUDA_VISIBLE_DEVICES = "$gpu"
  Start-Process -FilePath $Py -ArgumentList $argList -WorkingDirectory $Root `
    -RedirectStandardOutput $logf -RedirectStandardError "$logf.err" -WindowStyle Hidden
  Start-Sleep 2
}

Write-Host ""
Write-Host "Out: $Out"
Write-Host "Launched/skipped $($specs.Count) specs for Fig=$Fig"
