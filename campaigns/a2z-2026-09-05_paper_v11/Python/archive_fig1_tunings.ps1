# Archive contaminated fig1_v* tunings away from paper path.
$ErrorActionPreference = "Stop"
$Runs = "F:\projects\vessel\repro\a2z-2026-09-05\runs"
$Arch = Join-Path $Runs "archive"
New-Item -ItemType Directory -Force -Path $Arch | Out-Null

@"
These folders are NOT paper Fig1–8.
They used mixed knobs (COLREGS>0.45, aux losses, non-9M curriculum, altered rewards).
Do not cite for ablation claims. Paper path: runs/paper/ + paper_freeze.env
Archived=$(Get-Date -Format o)
"@ | Set-Content -Encoding UTF8 (Join-Path $Arch "README.txt")

foreach ($name in @("fig1", "fig1_v2", "fig1_v3", "fig1_v4")) {
  $src = Join-Path $Runs $name
  $dst = Join-Path $Arch $name
  if ((Test-Path $src) -and -not (Test-Path $dst)) {
    Move-Item $src $dst
    Write-Host "moved $name -> archive/"
  } elseif (Test-Path $dst) {
    Write-Host "already archived: $name"
  } else {
    Write-Host "missing: $name"
  }
}
