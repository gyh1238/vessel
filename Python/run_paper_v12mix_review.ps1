# v12mix review follow-up (coauthor feedback). NEVER FINAL.
# Phase A: re-eval existing ckpts with PRIMARY v2-strict (paper_freeze.env).
# Phase B: train Fig4 DIM2/4 + Fig5 COLREGS late-ramp (coef 0→0.45 @9M).
# Phase C (after train): post-eval new arms; Fig7 re-run separately.
param(
  [int[]]$Gpus = @(0, 1, 2, 3),
  [int]$Steps = 16000000,
  [int]$Envs = 128,
  [switch]$SkipReeval,
  [switch]$SkipTrain
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"

$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$Src = Join-Path $Paper "v12mix"
$Hub = Join-Path $Paper "v12mix_hub"
$Out = Join-Path $Paper "v12mix_review"
$EvalDir = Join-Path $Out "eval"
$LogDir = Join-Path $Out "logs"
$Status = Join-Path $Out "STATUS.txt"
New-Item -ItemType Directory -Force -Path $Out, $EvalDir, $LogDir, $Hub | Out-Null

function Write-Status([string]$msg) {
  $line = "{0}  {1}" -f (Get-Date -Format o), $msg
  Add-Content -Path $Status -Value $line -Encoding UTF8
  Write-Host $line
}
function Set-Freeze([hashtable]$Ov) {
  if ($null -eq $Ov) { Set-PaperFreezeEnv } else { Set-PaperFreezeEnv -Override $Ov }
}
function Find-Resume([string]$tag, [string]$dir) {
  $files = Get-ChildItem (Join-Path $dir "$tag.step*.pt") -EA SilentlyContinue |
    Sort-Object { [double]($_.BaseName -replace '.*step', '' -replace 'M$', '') } -Descending
  if ($files) { return $files[0] }
  $pt = Join-Path $dir "$tag.pt"
  if (Test-Path $pt) { return Get-Item $pt }
  return $null
}
function Test-TrainDone([string]$tag, [string]$dir) {
  $pt = Join-Path $dir "$tag.pt"
  if (-not (Test-Path $pt)) { return $false }
  $csv = Join-Path $dir "$tag.csv"
  if (Test-Path $csv) {
    try {
      $step = [int](((Get-Content $csv -Tail 1) -split ',')[0])
      if ($step -ge ($Steps - 100000)) { return $true }
    } catch {}
  }
  return $false
}
function Test-EvalDone([string]$logf) {
  if (-not (Test-Path $logf)) { return $false }
  return [bool](Select-String -Path $logf -Pattern 'PRIMARY-v2-dominant' -Quiet -EA SilentlyContinue)
}

$ovHub = @{
  VESSEL_TIE_MSG_CTRL_ENC   = "1"
  VESSEL_MOE_SHARED         = "1"
  VESSEL_MOE_SHARE_BACKBONE = "1"
  VESSEL_MOE_THIN_MU        = "0"
  VESSEL_MOE_ROUTE_MIX      = "0.15"
  VESSEL_MOE_RESIDUAL_HEAD  = "0"
  VESSEL_MOE_DELTA_L2       = "0"
  VESSEL_MOE_MSG            = "0"
  VESSEL_MOE_CRITIC         = "0"
}

# Ensure hub ON pts linked.
foreach ($s in 42, 43, 44) {
  $srcPt = Join-Path $Src "qd_MOE_SE_MX_s$s.pt"
  $dstPt = Join-Path $Hub "qd_MOE_SE_MX_s$s.pt"
  if (-not (Test-Path $srcPt)) { throw "missing $srcPt" }
  if (-not (Test-Path $dstPt)) { Copy-Item $srcPt $dstPt }
}

$pending = [System.Collections.Generic.List[object]]::new()

# ---- Phase A: strict re-eval of existing arms ----
if (-not $SkipReeval) {
  $reeval = @(
    @{ Tag = "qd_MOE_SE_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 6 },
    @{ Tag = "q_MOE_SINGLE_MX"; Dir = $Src; Arm = "ON"; Partners = 4; MsgDim = 6 },
    @{ Tag = "qf_SE_OFF_MX"; Dir = $Hub; Arm = "OFF"; Partners = 4; MsgDim = 6 },
    @{ Tag = "qf_SE_NEAR1_MX"; Dir = $Hub; Arm = "ON"; Partners = 1; MsgDim = 6 },
    @{ Tag = "qo_SE_COMM0_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 6 },
    @{ Tag = "q_DIM8_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 8 },
    @{ Tag = "q_DIM10_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 10 },
    @{ Tag = "q_DIM12_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 12 },
    @{ Tag = "q_MOE_THIN_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 6 },
    @{ Tag = "q_MOE_THICK_MX"; Dir = $Hub; Arm = "ON"; Partners = 4; MsgDim = 6 }
  )
  foreach ($spec in $reeval) {
    foreach ($s in 42, 43, 44) {
      $tag = "$($spec.Tag)_s$s"
      $ckpt = Join-Path $spec.Dir "$tag.pt"
      if (-not (Test-Path $ckpt)) {
        Write-Status "SKIP reeval missing $ckpt"
        continue
      }
      $ov = @{}
      foreach ($k in $ovHub.Keys) { $ov[$k] = $ovHub[$k] }
      if ($spec.MsgDim -ne 6) { $ov["VESSEL_MSG_DIM"] = "$($spec.MsgDim)" }
      if ($spec.Tag -eq "q_MOE_THIN_MX") {
        $ov["VESSEL_MOE_SHARED"] = "0"; $ov["VESSEL_MOE_SHARE_BACKBONE"] = "0"
        $ov["VESSEL_MOE_WIDTH"] = "0.44"; $ov["VESSEL_TIE_MSG_CTRL_ENC"] = "0"
      }
      if ($spec.Tag -eq "q_MOE_THICK_MX") {
        $ov["VESSEL_MOE_SHARED"] = "0"; $ov["VESSEL_MOE_SHARE_BACKBONE"] = "0"
        $ov["VESSEL_MOE_WIDTH"] = "1.0"; $ov["VESSEL_TIE_MSG_CTRL_ENC"] = "0"
      }
      if ($spec.Tag -eq "q_MOE_SINGLE_MX") {
        $ov["VESSEL_USE_MOE"] = "0"; $ov["VESSEL_MOE_SHARED"] = "0"
        $ov["VESSEL_MOE_SHARE_BACKBONE"] = "0"; $ov["VESSEL_MOE_ROUTE_MIX"] = "0"
      }
      $pending.Add([pscustomobject]@{
          Kind = "eval"; Pri = 1; Label = "strict_$tag"; Ckpt = $ckpt; Arm = $spec.Arm
          Crossing = 0; Partners = $spec.Partners; MsgDim = $spec.MsgDim
          Override = $ov; Tag = "strict_$tag"
        })
    }
  }
}

# ---- Phase B: train DIM2/4 + Fig5 late ----
if (-not $SkipTrain) {
  foreach ($s in 42, 43, 44) {
    foreach ($d in @(2, 4)) {
      $pending.Add([pscustomobject]@{
          Kind = "train"; Pri = (20 + $d); Tag = "q_DIM${d}_MX_s$s"; Arm = "ON"; Seed = $s
          Override = $ovHub; MsgDim = $d; Partners = 4; Crossing = 0; CommOnAt = 9000000
          ColregsOnAt = 0; Dir = $Hub; Label = "q_DIM${d}_MX_s$s"
        })
    }
    # Fig5 late: coef 0 until 9M, then 0.45 (env still 0.45; train ramps)
    $pending.Add([pscustomobject]@{
        Kind = "train"; Pri = 15; Tag = "qo_SE_COLREGS_LATE_MX_s$s"; Arm = "ON"; Seed = $s
        Override = $ovHub; MsgDim = 6; Partners = 4; Crossing = 0; CommOnAt = 9000000
        ColregsOnAt = 9000000; Dir = $Hub; Label = "qo_SE_COLREGS_LATE_MX_s$s"
      })
  }
}

function Get-JobOverride($job) {
  $ov = @{}
  if ($job.Override) { foreach ($k in $job.Override.Keys) { $ov[$k] = $job.Override[$k] } }
  if ($job.MsgDim -and ($job.MsgDim -ne 6)) { $ov["VESSEL_MSG_DIM"] = "$($job.MsgDim)" }
  return $ov
}

function Enqueue-PostEval($job) {
  $dir = if ($job.Dir) { $job.Dir } else { $Hub }
  $ckpt = Join-Path $dir "$($job.Tag).pt"
  if (-not (Test-Path $ckpt)) { Write-Status "WARN no pt $($job.Tag)"; return }
  $logf = Join-Path $EvalDir "strict_$($job.Tag).log"
  if (Test-EvalDone $logf) { Write-Status "skip post-eval strict_$($job.Tag)"; return }
  $pending.Insert(0, [pscustomobject]@{
      Kind = "eval"; Pri = 2; Label = "strict_$($job.Tag)"; Ckpt = $ckpt; Arm = $job.Arm
      Crossing = $job.Crossing; Partners = $job.Partners; MsgDim = $job.MsgDim
      Override = $job.Override; Tag = "strict_$($job.Tag)"
    })
  Write-Status "queued post-eval strict_$($job.Tag)"
}

$slots = @{}
foreach ($g in $Gpus) { $slots[$g] = $null }

function Start-JobOnGpu($job, [int]$gpu) {
  $env:CUDA_VISIBLE_DEVICES = "$gpu"
  $partners = if ($job.Partners) { [int]$job.Partners } else { 4 }
  if ($job.Kind -eq "eval") {
    $logf = Join-Path $EvalDir "$($job.Label).log"
    if (Test-EvalDone $logf) { Write-Status "skip eval $($job.Label)"; return @{ Skip = $true } }
    Set-Freeze (Get-JobOverride $job)
    $p = Start-Process -FilePath $Py -ArgumentList @(
      "-u", "eval_ckpt.py", "--ckpt", $job.Ckpt, "--arm", $job.Arm,
      "--envs", "64", "--burnin", "800", "--eval_decisions", "3000",
      "--ring", "0.7", "--crossing", "0", "--max_partners", "$partners",
      "--device", "cuda:0"
    ) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError "$logf.err" `
      -PassThru -WindowStyle Hidden
    Write-Status "eval $($job.Label) pid=$($p.Id) gpu=$gpu"
    return @{ P = $p; Job = $job; Gpu = $gpu; Log = $logf }
  }
  $dir = if ($job.Dir) { $job.Dir } else { $Hub }
  if (Test-TrainDone $job.Tag $dir) {
    Write-Status "skip train $($job.Tag)"
    return @{ SkipTrain = $true; Job = $job }
  }
  Set-Freeze (Get-JobOverride $job)
  $save = Join-Path $dir "$($job.Tag).pt"
  $csv = Join-Path $dir "$($job.Tag).csv"
  $logf = Join-Path $LogDir "$($job.Tag).log"
  $colregsOn = if ($null -ne $job.ColregsOnAt) { [int]$job.ColregsOnAt } else { 0 }
  $argList = [System.Collections.Generic.List[string]]::new()
  $argList.AddRange([string[]]@(
      "-u", "vessel_gym_train.py", "--arm", $job.Arm, "--steps", "$Steps",
      "--envs", "$Envs", "--vessels", "16", "--rollout", "32", "--ring", "0.7",
      "--seed", "$($job.Seed)", "--max_partners", "$partners",
      "--comm_on_at", "$($job.CommOnAt)", "--colregs_coef_on_at", "$colregsOn",
      "--ckpt_every", "2", "--crossing", "0", "--save", $save, "--csv", $csv
    ))
  $ckpt = Find-Resume $job.Tag $dir
  if ($ckpt) {
    $m = [regex]::Match($ckpt.Name, 'step([0-9.]+)M')
    $resumeAt = if ($m.Success) { [int]([double]$m.Groups[1].Value * 1e6) } else { 0 }
    if ($resumeAt -gt 0 -and $resumeAt -lt $Steps) {
      $argList.AddRange([string[]]@("--resume", $ckpt.FullName, "--resume_at", "$resumeAt", "--resume_warmup", "1200"))
      Write-Status "RESUME $($job.Tag) from $($ckpt.Name)"
    } else { Write-Status "FRESH train $($job.Tag) gpu=$gpu" }
  } else { Write-Status "FRESH train $($job.Tag) gpu=$gpu" }
  $p = Start-Process -FilePath $Py -ArgumentList $argList -WorkingDirectory $Root `
    -RedirectStandardOutput $logf -RedirectStandardError "$logf.err" -PassThru -WindowStyle Hidden
  return @{ P = $p; Job = $job; Gpu = $gpu; Log = $logf }
}

Write-Status "v12mix_review start gpus=$($Gpus -join ',') n=$($pending.Count) skipReeval=$SkipReeval skipTrain=$SkipTrain"
try {
  while ($pending.Count -gt 0 -or (@($slots.Values | Where-Object { $_ })).Count -gt 0) {
    foreach ($g in $Gpus) {
      if ($null -ne $slots[$g]) { continue }
      if ($pending.Count -eq 0) { continue }
      $best = 0
      for ($i = 1; $i -lt $pending.Count; $i++) {
        if ($pending[$i].Pri -lt $pending[$best].Pri) { $best = $i }
      }
      $job = $pending[$best]
      $pending.RemoveAt($best)
      $slot = Start-JobOnGpu $job $g
      if ($null -eq $slot) { continue }
      if ($slot.Skip) { continue }
      if ($slot.SkipTrain) { Enqueue-PostEval $job; continue }
      $slots[$g] = $slot
    }
    Start-Sleep -Seconds 20
    foreach ($g in @($Gpus)) {
      $slot = $slots[$g]
      if ($null -eq $slot) { continue }
      $slot.P.Refresh()
      if (-not $slot.P.HasExited) { continue }
      try { Wait-Process -Id $slot.P.Id -EA SilentlyContinue } catch {}
      $slot.P.Refresh()
      $job = $slot.Job
      $exit = $slot.P.ExitCode
      $slots[$g] = $null
      if (($job.Kind -eq "eval") -and (Test-EvalDone $slot.Log)) {
        Write-Status "done eval $($job.Label)"; continue
      }
      if ($null -eq $exit) {
        Write-Status "WARN $($job.Kind) $($job.Label) exit=null - requeue"
        $pending.Insert(0, $job); continue
      }
      if ($exit -ne 0) {
        Write-Status "FAIL $($job.Kind) $($job.Label) exit=$exit - continue"; continue
      }
      if ($job.Kind -eq "eval") {
        Write-Status "WARN eval incomplete $($job.Label) - requeue"
        $pending.Insert(0, $job)
      } else {
        Write-Status "done train $($job.Tag)"
        Enqueue-PostEval $job
      }
    }
  }
  Write-Status "v12mix_review complete"
} finally {
  foreach ($g in $Gpus) {
    if ($null -ne $slots[$g]) {
      try { Stop-Process -Id $slots[$g].P.Id -Force -EA SilentlyContinue } catch {}
    }
  }
}
