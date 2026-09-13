# When hub finals exist: formal frozen eval for Fig1 ON (+ optional OFF if trained).
# Usage: .\eval_hub_formal.ps1
param(
  [int[]]$Seeds = @(42, 43, 44),
  [switch]$IncludeOff,
  [int]$Gpu = 3
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Paper = Join-Path (Split-Path $Root -Parent) "runs\paper"

foreach ($s in $Seeds) {
  $on = Join-Path $Paper "qd_MOE_SE_s$s.pt"
  if (-not (Test-Path $on)) { Write-Host "skip missing $on"; continue }
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "eval_paper_ckpt.ps1") `
    -Ckpt $on -Arm ON -Gpu $Gpu
  if ($IncludeOff) {
    $off = Join-Path $Paper "qf_SE_OFF_s$s.pt"
    if (Test-Path $off) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "eval_paper_ckpt.ps1") `
        -Ckpt $off -Arm OFF -Gpu $Gpu
    }
  }
}
Write-Host "Formal evals under $Paper\eval\"
