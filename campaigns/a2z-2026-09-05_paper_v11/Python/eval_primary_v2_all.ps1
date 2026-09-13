# PRIMARY v2 + YHSH metrics re-eval for all Fig1-6 FINAL ckpts.
# Does NOT overwrite eval/*.log or FIG*_FORMAL*.txt. Writes eval_v2/ and results/v2/.
# Skips logs that already contain PRIMARY-v2-dominant.
param(
  [int[]]$Gpus = @(0, 1, 2, 3)
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv

$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$CkptDir = Join-Path $Paper "ckpts\final"
$Out = Join-Path $Paper "eval_v2"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

function Add-Job([System.Collections.Generic.List[object]]$list, [string]$Tag, [string]$Arm, [int]$Partners = 4) {
  $list.Add([pscustomobject]@{ Tag = $Tag; Arm = $Arm; Partners = $Partners; Label = $Tag })
}

$jobs = [System.Collections.Generic.List[object]]::new()
foreach ($s in 42, 43, 44) {
  Add-Job $jobs "qd_MOE_SE_s$s" "ON"
  Add-Job $jobs "qf_SE_OFF_s$s" "OFF"
  Add-Job $jobs "q_MOE_SINGLE_s$s" "ON"
  Add-Job $jobs "q_MOE_ISO_s$s" "ON"
  Add-Job $jobs "base_comm_s$s" "ON"
  Add-Job $jobs "qf_SE_NEAR1_s$s" "ON" 1
  foreach ($d in 2, 4, 8, 10, 12) { Add-Job $jobs "q_DIM${d}_s$s" "ON" }
  Add-Job $jobs "qo_SE_COLREGSOFF_s$s" "ON"
  Add-Job $jobs "ql_SE_START_s$s" "ON"
}

# Fig1 aliases already evaluated under short names
$aliasDone = @{
  "qd_MOE_SE_s42" = "ON_s42"; "qd_MOE_SE_s43" = "ON_s43"; "qd_MOE_SE_s44" = "ON_s44"
  "qf_SE_OFF_s42" = "OFF_s42"; "qf_SE_OFF_s43" = "OFF_s43"; "qf_SE_OFF_s44" = "OFF_s44"
  "q_MOE_SINGLE_s42" = "SINGLE_s42"
}

function Test-Complete([string]$logf) {
  if (-not (Test-Path $logf)) { return $false }
  return [bool](Select-String -Path $logf -Pattern 'PRIMARY-v2-dominant' -Quiet -ErrorAction SilentlyContinue)
}

$todo = @()
foreach ($j in $jobs) {
  $logf = Join-Path $Out "$($j.Label).log"
  $alt = $aliasDone[$j.Tag]
  if ($alt) {
    $altf = Join-Path $Out "$alt.log"
    if (Test-Complete $altf) {
      Write-Host "skip $($j.Tag) (have $alt)"
      continue
    }
  }
  if (Test-Complete $logf) {
    Write-Host "skip $($j.Tag)"
    continue
  }
  $ckpt = Join-Path $CkptDir "$($j.Tag).pt"
  if (-not (Test-Path $ckpt)) { throw "missing $ckpt" }
  $todo += $j
}
Write-Host "queued $($todo.Count) evals"

$procs = @()
$i = 0
while ($i -lt $todo.Count) {
  $wave = @()
  for ($g = 0; $g -lt $Gpus.Count -and $i -lt $todo.Count; $g++, $i++) {
    $j = $todo[$i]
    $gpu = $Gpus[$g]
    $ckpt = Join-Path $CkptDir "$($j.Tag).pt"
    $logf = Join-Path $Out "$($j.Label).log"
    $errf = "$logf.err"
    $env:CUDA_VISIBLE_DEVICES = "$gpu"
    $p = Start-Process -FilePath $Py -ArgumentList @(
      "-u", "eval_ckpt.py", "--ckpt", $ckpt, "--arm", $j.Arm,
      "--envs", "64", "--burnin", "800", "--eval_decisions", "3000",
      "--ring", "0.7", "--max_partners", "$($j.Partners)", "--device", "cuda:0"
    ) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError $errf -PassThru -WindowStyle Hidden
    $item = @{ P = $p; Label = $j.Label; Log = $logf; Gpu = $gpu; Partners = $j.Partners }
    $wave += $item
    $procs += $item
    Write-Host "launched $($j.Label) pid=$($p.Id) gpu=$gpu partners=$($j.Partners)"
  }
  foreach ($x in $wave) {
    try { Wait-Process -Id $x.P.Id -ErrorAction Stop } catch {}
    if ($null -ne $x.P.ExitCode -and $x.P.ExitCode -ne 0) {
      throw "eval failed $($x.Label) exit=$($x.P.ExitCode) see $($x.Log).err"
    }
    if (-not (Test-Complete $x.Log)) { throw "eval incomplete $($x.Label)" }
    Write-Host "done $($x.Label) gpu=$($x.Gpu)"
  }
}

Write-Host "all Fig1-6 v2 evals complete ($($todo.Count) launched)"
