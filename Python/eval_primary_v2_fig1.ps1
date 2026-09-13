# PRIMARY v2 re-eval of existing FINAL ckpts. Does NOT overwrite eval/*.log or FIG*_FORMAL*.txt.
# Fig1 protocol: envs=64 burnin=800 eval_decisions=3000 ring=0.7 partners=4
# Waves of |Gpus| so two evals never share a GPU.
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
$Res = Join-Path $Paper "results\FIG1"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
New-Item -ItemType Directory -Force -Path $Res | Out-Null

$jobs = @(
  @{ Tag = "qd_MOE_SE_s42"; Arm = "ON";  Label = "ON_s42" }
  @{ Tag = "qd_MOE_SE_s43"; Arm = "ON";  Label = "ON_s43" }
  @{ Tag = "qd_MOE_SE_s44"; Arm = "ON";  Label = "ON_s44" }
  @{ Tag = "qf_SE_OFF_s42"; Arm = "OFF"; Label = "OFF_s42" }
  @{ Tag = "qf_SE_OFF_s43"; Arm = "OFF"; Label = "OFF_s43" }
  @{ Tag = "qf_SE_OFF_s44"; Arm = "OFF"; Label = "OFF_s44" }
  @{ Tag = "q_MOE_SINGLE_s42"; Arm = "ON"; Label = "SINGLE_s42" }
)

$procs = @()
$i = 0
while ($i -lt $jobs.Count) {
  $wave = @()
  for ($g = 0; $g -lt $Gpus.Count -and $i -lt $jobs.Count; $g++, $i++) {
    $j = $jobs[$i]
    $ckpt = Join-Path $CkptDir "$($j.Tag).pt"
    if (-not (Test-Path $ckpt)) { throw "missing $ckpt" }
    $gpu = $Gpus[$g]
    $logf = Join-Path $Out "$($j.Label).log"
    $errf = "$logf.err"
    $env:CUDA_VISIBLE_DEVICES = "$gpu"
    $p = Start-Process -FilePath $Py -ArgumentList @(
      "-u", "eval_ckpt.py", "--ckpt", $ckpt, "--arm", $j.Arm,
      "--envs", "64", "--burnin", "800", "--eval_decisions", "3000",
      "--ring", "0.7", "--max_partners", "4", "--device", "cuda:0"
    ) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError $errf -PassThru -WindowStyle Hidden
    $item = @{ P = $p; Label = $j.Label; Log = $logf; Gpu = $gpu }
    $wave += $item
    $procs += $item
    Write-Host "launched $($j.Label) pid=$($p.Id) gpu=$gpu"
  }
  foreach ($x in $wave) {
    try { Wait-Process -Id $x.P.Id -ErrorAction Stop } catch { }
    if ($null -ne $x.P.ExitCode -and $x.P.ExitCode -ne 0) {
      throw "eval failed $($x.Label) exit=$($x.P.ExitCode)  see $($x.Log).err"
    }
    if (-not (Select-String -Path $x.Log -Pattern 'PRIMARY-v2-dominant' -Quiet)) {
      throw "eval failed $($x.Label) incomplete $($x.Log)"
    }
    Write-Host "done $($x.Label) exit=$($x.P.ExitCode) gpu=$($x.Gpu)"
  }
}

$sum = Join-Path $Res "FIG1_PRIMARY_V2.txt"
$lines = @(
  "=== PRIMARY v2 re-eval (existing FINAL, no retrain) $(Get-Date -Format 'yyyy-MM-dd HH:mm') ===",
  "protocol: envs=64 burnin=800 eval_decisions=3000 ring=0.7 partners=4",
  "mode=v2 all-pairs (dominant and v11 lines also in each log)",
  "ckpts: $CkptDir",
  "logs: $Out",
  "doc: runs/paper/results/COLREGS_EVAL.md",
  ""
)
foreach ($x in $procs) {
  $g = Select-String -Path $x.Log -Pattern 'goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%.*?colregsOK=\s*([\d.]+)%' |
    Select-Object -Last 1
  $p2 = Select-String -Path $x.Log -Pattern '\[COLREGs PRIMARY-v2\]' | Select-Object -Last 1
  $p2d = Select-String -Path $x.Log -Pattern '\[COLREGs PRIMARY-v2-dominant\]' | Select-Object -Last 1
  $p11 = Select-String -Path $x.Log -Pattern '\[COLREGs PRIMARY-v11\]' | Select-Object -Last 1
  $cross = Select-String -Path $x.Log -Pattern '\[COLREGs crossing\]' | Select-Object -Last 1
  $lines += "--- $($x.Label) ---"
  if ($g) { $lines += $g.Line.Trim() }
  if ($p2) { $lines += $p2.Line.Trim() }
  if ($p2d) { $lines += $p2d.Line.Trim() }
  if ($p11) { $lines += $p11.Line.Trim() }
  if ($cross) { $lines += $cross.Line.Trim() }
  $lines += ""
}
$lines | Set-Content -Encoding utf8 $sum
Write-Host "wrote $sum"
