# Launch Phase-2 contrast arms after hub is running (or when GPUs free).
# Does not kill hub. Uses remaining GPU slots round-robin.
param(
  [ValidateSet("fig1", "fig2", "fig3", "fig5", "fig6", "fig4", "all")]
  [string]$Phase = "all",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$hubOk = Test-Path (Join-Path (Split-Path $Root -Parent) "runs\paper\qd_MOE_SE_s42.pt")
# Allow starting contrasts in parallel with hub; hub finals not required for OFF/NEAR1/etc.

$order = switch ($Phase) {
  "all" { @("fig1", "fig3", "fig6", "fig5", "fig2", "fig4") }
  default { @($Phase) }
}

foreach ($fig in $order) {
  Write-Host "=== Phase launch Fig=$fig ==="
  $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            (Join-Path $Root "start_paper_train.ps1"), "-Fig", $fig)
  if ($DryRun) { $args += "-DryRun" }
  if ($fig -eq "fig2") {
    # shared = hub; launch non-hub arms separately to avoid GPU stampede
    foreach ($arm in @("single", "thin", "thick")) {
      & powershell @args -Arm $arm
    }
  } else {
    & powershell @args
  }
}
Write-Host "Phase2 queue issued. Monitor runs/logs/paper_*.log"
