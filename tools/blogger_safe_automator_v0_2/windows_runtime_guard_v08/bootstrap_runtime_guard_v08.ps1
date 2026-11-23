param(
  [string]$Root = 'C:\Blogger-Automator\blogger_safe_automator_v0_3'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Repo = 'adelrib27/blogger-automation1'
$Branch = 'blogger-safe-ui-provisioning-v0-2'
$Workflow = 'blogger_runtime_safe_sync_validation.yml'
$ToolsRel = 'tools/blogger_safe_automator_v0_2'
$Tools = Join-Path $Root 'tools\blogger_safe_automator_v0_2'
$Python = Join-Path $Tools '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Stage = Join-Path $env:TEMP "blogger-runtime-guard-bootstrap-$Stamp"
$Backup = "C:\Blogger-Automator\backups\runtime-guard-bootstrap-$Stamp"

$Files = @(
  'tools/blogger_safe_automator_v0_2/runtime_update_guard_v08.py',
  'tools/blogger_safe_automator_v0_2/local_service_v05.py',
  'tools/blogger_safe_automator_v0_2/local_service_v08.py',
  'tools/blogger_safe_automator_v0_2/windows_autostart_v07/start_blogger_automation_v07.ps1'
)

function Api([string]$Url) {
  $headers = @{
    'User-Agent' = 'blogger-runtime-guard-bootstrap-v08'
    'Accept' = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
  }
  return Invoke-RestMethod -Uri $Url -Headers $headers -TimeoutSec 30
}

function ToLocal([string]$Base, [string]$Rel) {
  return Join-Path $Base ($Rel -replace '/', '\')
}

try {
  Write-Host '=== Blogger Runtime Guard v0.8: bootstrap seguro ==='
  if (-not (Test-Path $Root)) { throw "Raiz operacional nao encontrada: $Root" }
  if (-not (Test-Path $Python)) { throw "Python da venv nao encontrado: $Python" }
  if (-not (Test-Path (Join-Path $Tools 'local_service_v07.py'))) { throw 'Runner v0.7 atual nao encontrado.' }

  $branchInfo = Api "https://api.github.com/repos/$Repo/branches/$Branch"
  $sha = [string]$branchInfo.commit.sha
  if ($sha.Length -ne 40) { throw 'SHA oficial invalido.' }

  $runs = Api "https://api.github.com/repos/$Repo/actions/runs?branch=$Branch&event=push&per_page=20"
  $run = @($runs.workflow_runs | Where-Object {
    [string]$_.head_sha -eq $sha -and [string]$_.name -eq 'Blogger Runtime Safe Sync Validation'
  } | Select-Object -First 1)
  if ($run.Count -ne 1) { throw "CI de runtime nao encontrada para $sha" }
  if ([string]$run[0].status -ne 'completed' -or [string]$run[0].conclusion -ne 'success') {
    throw "CI de runtime nao esta verde para $sha"
  }
  Write-Host "CI verde: sha=$sha run=$($run[0].id)"

  New-Item -ItemType Directory -Force -Path $Stage | Out-Null
  New-Item -ItemType Directory -Force -Path $Backup | Out-Null
  $raw = "https://raw.githubusercontent.com/$Repo/$sha"

  foreach ($rel in $Files) {
    $dst = ToLocal $Stage $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri "$raw/$rel" -OutFile $dst -TimeoutSec 45
    if (-not (Test-Path $dst) -or (Get-Item $dst).Length -eq 0) { throw "Download vazio: $rel" }
  }

  $stageTools = ToLocal $Stage $ToolsRel
  & $Python -m py_compile `
    (Join-Path $stageTools 'runtime_update_guard_v08.py') `
    (Join-Path $stageTools 'local_service_v05.py') `
    (Join-Path $stageTools 'local_service_v08.py')
  if ($LASTEXITCODE -ne 0) { throw 'Validacao Python falhou; nenhuma troca foi feita.' }

  foreach ($rel in $Files) {
    $current = ToLocal $Root $rel
    if (Test-Path $current) {
      $saved = ToLocal $Backup $rel
      New-Item -ItemType Directory -Force -Path (Split-Path $saved -Parent) | Out-Null
      Copy-Item -LiteralPath $current -Destination $saved -Force
    }
  }

  foreach ($rel in $Files) {
    $src = ToLocal $Stage $rel
    $dst = ToLocal $Root $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    $tmp = "$dst.bootstrap.tmp"
    Copy-Item -LiteralPath $src -Destination $tmp -Force
    Move-Item -LiteralPath $tmp -Destination $dst -Force
  }

  $start = Join-Path $Tools 'windows_autostart_v07\start_blogger_automation_v07.ps1'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $start -Root $Root
  if ($LASTEXITCODE -ne 0) { throw 'Inicializador v0.8 falhou.' }

  Write-Host ''
  Write-Host 'BLOGGER_RUNTIME_GUARD_V08_BOOTSTRAP_OK'
  Write-Host "sha=$sha"
  Write-Host "backup=$Backup"
  Write-Host 'runner_expected=0.8'
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  Write-Host "BLOGGER_RUNTIME_GUARD_V08_BOOTSTRAP_FAIL backup=$Backup"
  exit 1
}
finally {
  if (Test-Path $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue }
}
