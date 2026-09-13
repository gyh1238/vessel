# Load paper_freeze.env into process environment. Dot-source from other scripts:
#   . "$PSScriptRoot\load_paper_freeze.ps1"
#   Set-PaperFreezeEnv
# Optional hashtable overrides after load: Set-PaperFreezeEnv -Override @{ VESSEL_MSG_DIM = "8" }
function Set-PaperFreezeEnv {
  param([hashtable]$Override = @{})
  $envFile = Join-Path $PSScriptRoot "paper_freeze.env"
  if (-not (Test-Path $envFile)) { throw "missing paper_freeze.env at $envFile" }
  # Clear prior VESSEL_* so contaminated shells cannot leak (e.g. old fig1_v4).
  @((Get-ChildItem Env:).Name | Where-Object { $_ -like 'VESSEL_*' }) | ForEach-Object {
    Remove-Item "Env:$_" -ErrorAction SilentlyContinue
  }
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $i = $line.IndexOf("=")
    if ($i -lt 1) { return }
    $k = $line.Substring(0, $i).Trim()
    $v = $line.Substring($i + 1).Trim()
    Set-Item -Path "Env:$k" -Value $v
  }
  foreach ($k in $Override.Keys) {
    Set-Item -Path "Env:$k" -Value "$($Override[$k])"
  }
  # Sanity: required knobs must exist after load
  foreach ($req in @(
      'VESSEL_PROGRESS_COEF', 'VESSEL_ARRIVAL_REWARD', 'VESSEL_COLLISION_PENALTY',
      'VESSEL_SIM_COLREGS_COEF', 'VESSEL_THREAT_COEF', 'VESSEL_MOE_SHARED'
    )) {
    if (-not (Get-Item "Env:$req" -EA SilentlyContinue)) {
      throw "paper freeze missing $req after load"
    }
  }
}

function Get-PaperFreezeHash {
  $envFile = Join-Path $PSScriptRoot "paper_freeze.env"
  $h = Get-FileHash $envFile -Algorithm SHA256
  return $h.Hash.Substring(0, 12).ToLower()
}
