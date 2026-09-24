# After v12mix_review finishes: aggregate, figures, Fig7 CSV copy, GATE notes.
# Poll STATUS for "v12mix_review complete".
param([int]$PollSec = 120)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Status = Join-Path $Root "runs\paper\v12mix_review\STATUS.txt"
$Py = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$PyFig = "C:\Users\JYH\miniconda3\envs\blt\python.exe"

Write-Host "Waiting for v12mix_review complete..."
while ($true) {
  if ((Test-Path $Status) -and (Select-String -Path $Status -Pattern 'v12mix_review complete' -Quiet)) {
    break
  }
  Start-Sleep -Seconds $PollSec
  if (Test-Path $Status) {
    Get-Content $Status -Tail 3 | ForEach-Object { Write-Host $_ }
  }
}

Write-Host "Review done. Aggregating + figures + Fig7."
. "$PSScriptRoot\load_paper_freeze.ps1"
Set-PaperFreezeEnv -Override @{
  VESSEL_TIE_MSG_CTRL_ENC   = "1"
  VESSEL_MOE_SHARED         = "1"
  VESSEL_MOE_SHARE_BACKBONE = "1"
  VESSEL_MOE_ROUTE_MIX      = "0.15"
  VESSEL_MOE_RESIDUAL_HEAD  = "0"
  VESSEL_MOE_MSG            = "0"
  VESSEL_MOE_CRITIC         = "0"
  VESSEL_EVAL_APPLY_SNAPSHOT = "1"
}

# Fig7 re-run (goal/prox/minSep figure; no step-legacy C panel)
& "$PSScriptRoot\eval_fig7_v12mix.ps1" -Gpu 0
if ($LASTEXITCODE -ne 0) { Write-Host "WARN Fig7 exit=$LASTEXITCODE" }

Copy-Item (Join-Path $Root "runs\paper\v12mix_hub\fig7\mixed_fleet_rx.csv") `
  (Join-Path $Root "runs\paper\fig7\mixed_fleet_rx.csv") -Force

Set-Location $PSScriptRoot
& $Py -u aggregate_eval_v2.py
& $PyFig -u make_paper_figures.py 1 2 3 4 5 6 7

# Snapshot hub C for GATE note
$gate = Join-Path $Root "results\GATE_v12mix_strict.txt"
& $Py -c @"
from pathlib import Path
import re, statistics
EVAL = Path(r'$Root') / 'runs' / 'paper' / 'v12mix_review' / 'eval'
CDOM = re.compile(r'PRIMARY-v2-dominant\] C=\s*([\d.]+)%')
MAIN = re.compile(r'goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%')
lines = ['PRIMARY v2-strict re-eval (OFF_DEG=15 SPD=0.20 SO_NULL_Q=60)', '']
for pref in ['strict_qd_MOE_SE_MX','strict_q_MOE_SINGLE_MX','strict_qf_SE_OFF_MX',
             'strict_qo_SE_COLREGS_LATE_MX','strict_q_DIM2_MX','strict_q_DIM4_MX']:
    xs=[]
    for s in (42,43,44):
        p = EVAL / f'{pref}_s{s}.log'
        if not p.exists():
            continue
        t = p.read_text(encoding='utf-8', errors='replace')
        c = CDOM.search(t); m = None
        for line in t.splitlines():
            mm = MAIN.search(line)
            if mm and 'arm=' in line: m = mm
        if c and m:
            xs.append((float(m.group(1)), float(m.group(2)), float(c.group(1))))
    if xs:
        g=statistics.mean(x[0] for x in xs); c=statistics.mean(x[2] for x in xs)
        lines.append(f'{pref}: n={len(xs)} goal={g:.1f} C_dom={c:.1f}')
Path(r'$gate').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('\n'.join(lines))
"@

Write-Host "finish_review_figures done"

