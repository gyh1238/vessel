# Formal frozen eval under paper freeze. Writes runs/paper/eval/<tag>.log
param(
  [Parameter(Mandatory = $true)][string]$Ckpt,
  [ValidateSet("OFF", "ON")][string]$Arm = "ON",
  [int]$Envs = 96,
  [int]$Burnin = 1200,
  [int]$EvalDecisions = 6000,
  [int]$MaxPartners = 4,
  [int]$Gpu = 0,
  [hashtable]$Override = @{}
)

$ErrorActionPreference = "Continue"
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv -Override $Override

$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = $PSScriptRoot
$Out  = Join-Path (Split-Path $Root -Parent) "runs\paper\eval"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$base = [IO.Path]::GetFileNameWithoutExtension($Ckpt)
$logf = Join-Path $Out "$base`_$Arm.log"
$errf = "$logf.err"

$env:CUDA_VISIBLE_DEVICES = "$Gpu"
$p = Start-Process -FilePath $Py -ArgumentList @(
  "-u", "eval_ckpt.py", "--ckpt", $Ckpt, "--arm", $Arm,
  "--envs", "$Envs", "--burnin", "$Burnin", "--eval_decisions", "$EvalDecisions",
  "--ring", "0.7", "--max_partners", "$MaxPartners", "--device", "cuda:0"
) -WorkingDirectory $Root -RedirectStandardOutput $logf -RedirectStandardError $errf -PassThru -NoNewWindow
Wait-Process -Id $p.Id
Write-Host "wrote $logf exit=$($p.ExitCode)"
if ($p.ExitCode -ne 0) { throw "eval_ckpt failed exit=$($p.ExitCode) for $Ckpt" }
