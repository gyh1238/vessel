# Fig2 C2 arms on v12mix hub: THIN (width 0.44, no share) + THICK (width 1.0, no share).
# Same train mix=0.15. Compare to existing SHARED MX + SINGLE MX. Never FINAL.
param(
  [int[]]$Gpus = @(0, 1, 2, 3),
  [int]$Steps = 16000000,
  [int]$Envs = 128
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"

$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$V12r = Join-Path $Paper "v12mix_hub"
if ($V12r -like '*ckpts*final*') { throw "refusing FINAL" }
$EvalDir = Join-Path $V12r "eval"
$LogDir = Join-Path $V12r "logs"
$Status = Join-Path $V12r "STATUS.txt"
New-Item -ItemType Directory -Force -Path $V12r, $EvalDir, $LogDir | Out-Null

function Write-Status([string]$msg) {
  $line = "{0}  {1}" -f (Get-Date -Format o), $msg
  Write-Host $line
  for ($i = 0; $i -lt 5; $i++) {
    try {
      Add-Content -Path $Status -Value $line -Encoding UTF8 -ErrorAction Stop
      break
    } catch {
      Start-Sleep -Milliseconds 200
    }
  }
}
function Set-Freeze([hashtable]$Ov) {
  if ($null -eq $Ov) { Set-PaperFreezeEnv } else { Set-PaperFreezeEnv -Override $Ov }
}
function Find-Resume([string]$tag) {
  $files = Get-ChildItem (Join-Path $V12r "$tag.step*.pt") -EA SilentlyContinue |
    Sort-Object { [double]($_.BaseName -replace '.*step', '' -replace 'M$', '') } -Descending
  if ($files) { return $files[0] }
  $pt = Join-Path $V12r "$tag.pt"
  if (Test-Path $pt) { return Get-Item $pt }
  return $null
}
function Test-TrainDone([string]$tag) {
  $pt = Join-Path $V12r "$tag.pt"
  if (-not (Test-Path $pt)) { return $false }
  $csv = Join-Path $V12r "$tag.csv"
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

$ovThin = @{
  VESSEL_TIE_MSG_CTRL_ENC   = "0"
  VESSEL_USE_MOE            = "1"
  VESSEL_MOE_SHARED         = "0"
  VESSEL_MOE_SHARE_BACKBONE = "0"
  VESSEL_MOE_WIDTH          = "0.44"
  VESSEL_MOE_ROUTE_MIX      = "0.15"
  VESSEL_MOE_RESIDUAL_HEAD  = "0"
  VESSEL_MOE_MSG            = "0"
  VESSEL_MOE_CRITIC         = "0"
}
$ovThick = @{
  VESSEL_TIE_MSG_CTRL_ENC   = "0"
  VESSEL_USE_MOE            = "1"
  VESSEL_MOE_SHARED         = "0"
  VESSEL_MOE_SHARE_BACKBONE = "0"
  VESSEL_MOE_WIDTH          = "1.0"
  VESSEL_MOE_ROUTE_MIX      = "0.15"
  VESSEL_MOE_RESIDUAL_HEAD  = "0"
  VESSEL_MOE_MSG            = "0"
  VESSEL_MOE_CRITIC         = "0"
}

$pending = [System.Collections.Generic.List[object]]::new()
foreach ($s in 42, 43, 44) {
  $pending.Add([pscustomobject]@{
      Kind = "train"; Pri = 10; Tag = "q_MOE_THIN_MX_s$s"; Arm = "ON"; Seed = $s
      Override = $ovThin; Label = "q_MOE_THIN_MX_s$s"
    })
  $pending.Add([pscustomobject]@{
      Kind = "train"; Pri = 11; Tag = "q_MOE_THICK_MX_s$s"; Arm = "ON"; Seed = $s
      Override = $ovThick; Label = "q_MOE_THICK_MX_s$s"
    })
}

function Enqueue-PostEval($job) {
  $ckpt = Join-Path $V12r "$($job.Tag).pt"
  if (-not (Test-Path $ckpt)) { Write-Status "WARN no pt $($job.Tag)"; return }
  $logf = Join-Path $EvalDir "post_$($job.Tag).log"
  if (Test-EvalDone $logf) { Write-Status "skip post-eval post_$($job.Tag)"; return }
  $pending.Insert(0, [pscustomobject]@{
      Kind = "eval"; Pri = 5; Label = "post_$($job.Tag)"; Ckpt = $ckpt; Arm = $job.Arm
      Override = $job.Override; Tag = "post_$($job.Tag)"
    })
  Write-Status "queued post-eval post_$($job.Tag)"
}

$slots = @{}
foreach ($g in $Gpus) { $slots[$g] = $null }

function Start-JobOnGpu($job, [int]$gpu) {
  $env:CUDA_VISIBLE_DEVICES = "$gpu"
  if ($job.Kind -eq "eval") {
    $logf = Join-Path $EvalDir "$($job.Label).log"
    if (Test-EvalDone $logf) { Write-Status "skip eval $($job.Label)"; return @{ Skip = $true } }
    Set-Freeze $job.Override
    $p = Start-Process -FilePath $Py -ArgumentList @(
      "-u", "eval_ckpt.py", "--ckpt", $job.Ckpt, "--arm", $job.Arm,
      "--envs", "64", "--burnin", "800", "--eval_decisions", "3000",
      "--ring", "0.7", "--crossing", "0", "--max_partners", "4", "--device", "cuda:0"
    ) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError "$logf.err" `
      -PassThru -WindowStyle Hidden
    Write-Status "eval $($job.Label) pid=$($p.Id) gpu=$gpu"
    return @{ P = $p; Job = $job; Gpu = $gpu; Log = $logf }
  }
  if (Test-TrainDone $job.Tag) {
    Write-Status "skip train $($job.Tag)"
    return @{ SkipTrain = $true; Job = $job }
  }
  Set-Freeze $job.Override
  $save = Join-Path $V12r "$($job.Tag).pt"
  $csv = Join-Path $V12r "$($job.Tag).csv"
  $logf = Join-Path $LogDir "$($job.Tag).log"
  $argList = [System.Collections.Generic.List[string]]::new()
  $argList.AddRange([string[]]@(
      "-u", "vessel_gym_train.py", "--arm", $job.Arm, "--steps", "$Steps",
      "--envs", "$Envs", "--vessels", "16", "--rollout", "32", "--ring", "0.7",
      "--seed", "$($job.Seed)", "--max_partners", "4", "--comm_on_at", "9000000",
      "--ckpt_every", "2", "--crossing", "0", "--save", $save, "--csv", $csv
    ))
  $ckpt = Find-Resume $job.Tag
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

Write-Status "v12mix THIN/THICK Fig2 C2 gpus=$($Gpus -join ',')"
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
        Write-Status "done train $($job.Label)"
        Enqueue-PostEval $job
      }
    }
  }
  Write-Status "judging Fig2 THIN/THICK"
  & $Py -u (Join-Path $Root "judge_v12mix_c2.py")
  Write-Status "v12mix C2 campaign complete"
} catch {
  Write-Status "ABORT $_"
  throw
}
