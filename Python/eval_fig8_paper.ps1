# Fig8: direct vs astar on hub policy (not ql_SE_START). 2x2 arm x path.
# Also writes blocked-subset note from path table if present in logs.
param(
  [int]$Seed = 42,
  [int]$Gpu = 0,
  [int]$Envs = 96,
  [int]$Burnin = 1200,
  [int]$EvalDecisions = 10000
)

$ErrorActionPreference = "Continue"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv

$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$env:PYTHONPATH = $Root
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"
$Out = Join-Path $Paper "fig8"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$ckpt = Join-Path $Paper "qd_MOE_SE_s$Seed.pt"
if (-not (Test-Path $ckpt)) { throw "MISSING hub $ckpt — train -Fig hub first" }

$jobs = @(
  @{ Arm = "ON";  Path = "direct" },
  @{ Arm = "ON";  Path = "astar" },
  @{ Arm = "OFF"; Path = "direct" },
  @{ Arm = "OFF"; Path = "astar" }
)

foreach ($j in $jobs) {
  $tag = "hub_s${Seed}_$($j.Arm)_$($j.Path)"
  $logf = Join-Path $Out "$tag.log"
  $errf = "$logf.err"
  Write-Host "Fig8 $tag"
  $env:CUDA_VISIBLE_DEVICES = "$Gpu"
  $p = Start-Process -FilePath $Py -ArgumentList @(
    "-u", (Join-Path $Root "astar_fig9\eval_astar_global.py"),
    "--ckpt", $ckpt, "--arm", $j.Arm, "--path", $j.Path,
    "--envs", "$Envs", "--vessels", "16", "--max_partners", "4",
    "--burnin", "$Burnin", "--eval_decisions", "$EvalDecisions",
    "--ring", "0.7"
  ) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError $errf -PassThru -NoNewWindow
  Wait-Process -Id $p.Id
  Start-Sleep -Milliseconds 500
  $code = $p.ExitCode
  if ($null -eq $code) {
    $proc = Get-Process -Id $p.Id -EA SilentlyContinue
    if ($proc) { Wait-Process -Id $p.Id -EA SilentlyContinue; $code = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -EA SilentlyContinue) }
    $code = 0  # Start-Process often leaves ExitCode null after Wait-Process on success
  }
  $hasGoal = Select-String -Path $logf -Pattern 'goal=\s*[\d.]+%' -EA SilentlyContinue
  if (($code -ne 0) -and -not $hasGoal) {
    Write-Host "Fig8 $tag FAILED exit=$code"
    throw "Fig8 $tag failed"
  }
  if (-not $hasGoal) { Write-Host "Fig8 $tag WARN: exit=$code but no goal line yet" }
  else { Write-Host "Fig8 $tag OK" }
}

# Summarize: prefer blocked (excess/plan) lines if logged
$sum = Join-Path $Out "summary_s$Seed.txt"
@"
Fig8 paper eval seed=$Seed ckpt=$ckpt
Policy = hub qd_MOE_SE (NOT ql_SE_START).
Blocked-subset: re-read logs for combinations where A* path has >1 waypoint
(or excess>1). Overall mean dilutes ~54% straight-line cases — report blocked separately.
Logs: $Out
Generated=$(Get-Date -Format o)
"@ | Set-Content -Encoding UTF8 $sum

# Extract goal/coll/C from each log
Get-ChildItem "$Out\hub_s${Seed}_*.log" | ForEach-Object {
  $g = Select-String -Path $_.FullName -Pattern 'goal=\s*([\d.]+)%.*?oColl=\s*([\d.]+)%.*?colregsOK=\s*([\d.]+)%' |
    Select-Object -Last 1
  if ($g) { "$($_.Name): $($g.Line.Substring(0, [Math]::Min(160, $g.Line.Length)))" | Add-Content $sum }
}
Write-Host "wrote $sum"
