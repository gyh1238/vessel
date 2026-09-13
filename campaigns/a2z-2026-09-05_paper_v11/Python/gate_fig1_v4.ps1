# Smart fig1_v4 gate: safety AND Fig1 goal (ON should beat OFF on COLREGs / collisions).
# At each step N with both off_s42 + on_s42 ckpts:
#   short frozen eval both → log metrics
# Kill if:
#   A) safety: either arm oColl>20 OR goal<40
#   B) Fig1 miss (only step>=8M, after comm@6M): two consecutive steps where
#        ON colregsOK < OFF-2pp  AND  ON (vColl+oColl) > OFF (vColl+oColl)
# Warn (no kill) logged when ON behind on only one axis.
$ErrorActionPreference = "Continue"
$Py   = "C:\Users\JYH\miniconda3\envs\vessel_repro\python.exe"
$Root = "F:\projects\vessel\repro\a2z-2026-09-05\Python"
$Out  = "F:\projects\vessel\repro\a2z-2026-09-05\runs\fig1_v4"
$Gate = Join-Path $Out "gate"
New-Item -ItemType Directory -Force -Path $Gate | Out-Null
$pairDone = @{}
$missStreak = 0
$Hist = Join-Path $Gate "pair_history.txt"

function Set-GateEnv {
  $env:PYTHONUNBUFFERED = "1"
  $env:VESSEL_USE_MOE = "1"; $env:VESSEL_MOE_SHARED = "1"; $env:VESSEL_MOE_WIDTH = "1.0"
  $env:VESSEL_MSG_DIM = "6"; $env:VESSEL_POS_GROUND = "1"; $env:VESSEL_USE_ATTENTION = "0"
  $env:VESSEL_THREAT_COEF = "0.8"; $env:VESSEL_ROLE_COMM_COEF = "0.10"
  $env:VESSEL_GOAL_COMM_COEF = "0.05"; $env:VESSEL_INTENT_COEF = "0.05"
  $env:VESSEL_COMM_CONSUMER_COEF = "0.05"; $env:VESSEL_COMM_CONSUMER_COUPLING = "1"
  $env:VESSEL_SIM_COLREGS_COEF = "0.70"; $env:VESSEL_COLREGS_PRIMARY_ALIGN = "1.0"
  $env:VESSEL_RADAR_ACT = "leaky"; $env:VESSEL_USE_COMM = "1"; $env:VESSEL_COMM_RANGE = "420"
}

function Kill-AllV4([string]$Reason) {
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'vessel_gym_train' -and $_.CommandLine -match 'fig1_v4' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
  $Reason | Set-Content -Encoding UTF8 (Join-Path $Out "GATE_FAILED.txt")
  Write-Host "GATE FAIL: $Reason"
}

function Invoke-ShortEval([string]$Ckpt, [string]$Arm, [string]$Logf, [string]$Gpu) {
  Set-GateEnv
  $env:CUDA_VISIBLE_DEVICES = $Gpu
  $p = Start-Process -FilePath $Py -ArgumentList @(
    "-u","eval_ckpt.py","--ckpt",$Ckpt,"--arm",$Arm,
    "--envs","64","--burnin","800","--eval_decisions","1500",
    "--ring","0.7","--max_partners","4","--device","cuda:0"
  ) -WorkingDirectory $Root -RedirectStandardOutput $Logf -RedirectStandardError "$Logf.err" -PassThru -WindowStyle Hidden
  Wait-Process -Id $p.Id -Timeout 700 -EA SilentlyContinue
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -EA SilentlyContinue }
}

function Parse-Eval([string]$Logf) {
  $o = @{ ok=$false; goal=0; vColl=0; oColl=0; colregs=0; cross=0; sit2=0; sit3=0 }
  $g = Select-String -Path $Logf -Pattern 'goal=' -EA SilentlyContinue | Select-Object -Last 1
  if (-not $g) { return $o }
  if ($g.Line -match 'goal=\s*([\d.]+)%\s+vColl=\s*([\d.]+)%\s+oColl=\s*([\d.]+)%.*?colregsOK=\s*([\d.]+)%') {
    $o.goal=[double]$Matches[1]; $o.vColl=[double]$Matches[2]; $o.oColl=[double]$Matches[3]; $o.colregs=[double]$Matches[4]
    $o.ok = $true
  }
  $c = Select-String -Path $Logf -Pattern 'COLREGs crossing' -EA SilentlyContinue | Select-Object -Last 1
  if ($c -and $c.Line -match 'sit3\(GW\)=\s*([\d.]+)%.*?sit2\(SO\)=\s*([\d.]+)%.*?crossingAvg=\s*([\d.]+)%') {
    $o.sit3=[double]$Matches[1]; $o.sit2=[double]$Matches[2]; $o.cross=[double]$Matches[3]
  }
  return $o
}

Set-GateEnv
"smart gate started $(Get-Date -Format o) | safety + Fig1 ON>OFF" | Add-Content $Hist
Write-Host "fig1_v4 SMART gate started $(Get-Date -Format o)"

while ($true) {
  if (Test-Path (Join-Path $Out "GATE_FAILED.txt")) { break }
  $nTrain = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'vessel_gym_train' -and $_.CommandLine -match 'fig1_v4' }).Count
  $nFinal = @(Get-ChildItem (Join-Path $Out "fig1_*.pt") -EA SilentlyContinue |
    Where-Object { $_.Name -notmatch 'step' }).Count
  if ($nTrain -eq 0 -and $nFinal -ge 4) {
    "ALL_DONE $(Get-Date -Format o)" | Set-Content (Join-Path $Out "GATE_OK.txt")
    Write-Host "all finals — smart gate exit OK"
    break
  }

  # steps that have BOTH off and on s42 ckpts
  $offSteps = @{}
  Get-ChildItem (Join-Path $Out "fig1_off_s42.step*.pt") -EA SilentlyContinue | ForEach-Object {
    $m = [regex]::Match($_.Name, 'step([0-9.]+)M'); if ($m.Success) { $offSteps[[int][double]$m.Groups[1].Value] = $_.FullName }
  }
  $onSteps = @{}
  Get-ChildItem (Join-Path $Out "fig1_on_s42.step*.pt") -EA SilentlyContinue | ForEach-Object {
    $m = [regex]::Match($_.Name, 'step([0-9.]+)M'); if ($m.Success) { $onSteps[[int][double]$m.Groups[1].Value] = $_.FullName }
  }
  # also finals as 16 if named .pt without step — skip; use step files only
  # newest first — catch Fig1 miss early while train still runs
  $steps = ($offSteps.Keys | Where-Object { $onSteps.ContainsKey($_) -and $_ -ge 2 } | Sort-Object -Descending)

  foreach ($step in $steps) {
    if ($pairDone.ContainsKey($step)) { continue }
    $offCk = Get-Item $offSteps[$step]
    $onCk  = Get-Item $onSteps[$step]
    if (((Get-Date)-$offCk.LastWriteTime).TotalSeconds -lt 20) { continue }
    if (((Get-Date)-$onCk.LastWriteTime).TotalSeconds -lt 20) { continue }

    $pairDone[$step] = $true
    $offLog = Join-Path $Gate "pair_off42_${step}M.log"
    $onLog  = Join-Path $Gate "pair_on42_${step}M.log"
    Write-Host "$(Get-Date -Format HH:mm:ss) PAIR eval step${step}M OFF+ON ..."

    # parallel on free-ish GPUs 0 and 1 (train may use them — short eval OK)
    Set-GateEnv
    $env:CUDA_VISIBLE_DEVICES = "0"
    $p0 = Start-Process -FilePath $Py -ArgumentList @("-u","eval_ckpt.py","--ckpt",$offCk.FullName,"--arm","OFF","--envs","64","--burnin","800","--eval_decisions","1500","--ring","0.7","--max_partners","4","--device","cuda:0") -WorkingDirectory $Root -RedirectStandardOutput $offLog -RedirectStandardError "$offLog.err" -PassThru -WindowStyle Hidden
    $env:CUDA_VISIBLE_DEVICES = "1"
    $p1 = Start-Process -FilePath $Py -ArgumentList @("-u","eval_ckpt.py","--ckpt",$onCk.FullName,"--arm","ON","--envs","64","--burnin","800","--eval_decisions","1500","--ring","0.7","--max_partners","4","--device","cuda:0") -WorkingDirectory $Root -RedirectStandardOutput $onLog -RedirectStandardError "$onLog.err" -PassThru -WindowStyle Hidden
    Wait-Process -Id $p0.Id -Timeout 700 -EA SilentlyContinue
    Wait-Process -Id $p1.Id -Timeout 700 -EA SilentlyContinue
    if (-not $p0.HasExited) { Stop-Process -Id $p0.Id -Force -EA SilentlyContinue }
    if (-not $p1.HasExited) { Stop-Process -Id $p1.Id -Force -EA SilentlyContinue }

    $off = Parse-Eval $offLog
    $on  = Parse-Eval $onLog
    if (-not $off.ok -or -not $on.ok) {
      Kill-AllV4 "step${step}M pair parse fail off=$($off.ok) on=$($on.ok)"
      break
    }

    $offColl = $off.vColl + $off.oColl
    $onColl  = $on.vColl + $on.oColl
    $dC = [math]::Round($on.colregs - $off.colregs, 1)
    $dX = [math]::Round($on.cross - $off.cross, 1)
    $dColl = [math]::Round($onColl - $offColl, 1)
    $line = "step${step}M OFF goal=$($off.goal) vColl=$($off.vColl) oColl=$($off.oColl) C=$($off.colregs) X=$($off.cross) | ON goal=$($on.goal) vColl=$($on.vColl) oColl=$($on.oColl) C=$($on.colregs) X=$($on.cross) | dC=$dC dX=$dX dColl=$dColl"
    Write-Host $line
    $line | Add-Content $Hist

    # A) safety
    if ($off.oColl -gt 20 -or $off.goal -lt 40 -or $on.oColl -gt 20 -or $on.goal -lt 40) {
      Kill-AllV4 "SAFETY $line"
      break
    }

    # B) Fig1 goal after comm curriculum (comm@6M → judge from 8M)
    if ($step -ge 8) {
      $colregsMiss = ($on.colregs -lt ($off.colregs - 2.0))
      $collMiss    = ($onColl -gt $offColl)
      if ($colregsMiss -and $collMiss) {
        $missStreak++
        $w = "WARN Fig1-miss streak=$missStreak at ${step}M (ON worse C and coll)"
        Write-Host $w
        $w | Add-Content $Hist
        if ($missStreak -ge 2) {
          Kill-AllV4 "FIG1_GOAL $line (2 consecutive misses)"
          break
        }
      } else {
        if ($missStreak -gt 0) { "streak reset at ${step}M" | Add-Content $Hist }
        $missStreak = 0
      }
      # single-axis note
      if ($colregsMiss -and -not $collMiss) { "NOTE ${step}M ON behind COLREGs only dC=$dC" | Add-Content $Hist }
      if ($collMiss -and -not $colregsMiss) { "NOTE ${step}M ON behind collision only dColl=$dColl" | Add-Content $Hist }
      if (-not $colregsMiss -and -not $collMiss) { "OK ${step}M ON on-track (C and/or coll)" | Add-Content $Hist }
    }
  }
  Start-Sleep -Seconds 45
}
