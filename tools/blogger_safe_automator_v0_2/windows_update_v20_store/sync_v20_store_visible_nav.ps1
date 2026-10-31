param(
  [string]$Root = 'C:\Blogger-Automator\blogger_safe_automator_v0_3'
)

$ErrorActionPreference = 'Stop'
$Commit = '5b5f4da03ad890af5bdecc8eb0597e36b3753b7d'
$RepoRaw = "https://raw.githubusercontent.com/adelrib27/blogger-automation1/$Commit"
$ToolsRel = 'tools/blogger_safe_automator_v0_2'
$Tools = Join-Path $Root $ToolsRel
$Python = Join-Path $Tools '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Stage = Join-Path $env:TEMP "blogger-v20-store-sync-$Stamp"
$Backup = "C:\Blogger-Automator\backups\v20-store-sync-$Stamp"

$Files = @(
  'tools/blogger_safe_automator_v0_2/extend_modelo_v20_store.py',
  'tools/blogger_safe_automator_v0_2/extend_modelo_v20_store_visible_nav.py',
  'tools/blogger_safe_automator_v0_2/install_modelo_v20_adoption.py',
  'tools/blogger_safe_automator_v0_2/validate_modelo_v20_store.py',
  'tools/blogger_safe_automator_v0_2/render_modelo_v20_pages.py',
  'tools/blogger_safe_automator_v0_2/provision_new_blog_v20.py',
  'templates/blogger_modelo_v20/model_manifest.json',
  'templates/blogger_modelo_v20/pages.json',
  'themes/blogger_modelo_v20/pages.json'
)

function To-Local([string]$base, [string]$rel) {
  return Join-Path $base ($rel -replace '/', '\')
}

try {
  Write-Host '=== V20 LOJA: sincronizacao segura ==='
  if (-not (Test-Path $Root)) { throw "Raiz operacional nao encontrada: $Root" }
  if (-not (Test-Path $Python)) { throw "Python da venv nao encontrado: $Python" }
  if (-not (Test-Path (Join-Path $Tools 'local_service_v07.py'))) { throw 'Runner v0.7 nao encontrado na raiz esperada.' }

  New-Item -ItemType Directory -Force -Path $Stage | Out-Null
  New-Item -ItemType Directory -Force -Path $Backup | Out-Null

  foreach ($rel in $Files) {
    $dst = To-Local $Stage $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    $url = "$RepoRaw/$rel"
    Write-Host "Baixando $rel"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $dst -TimeoutSec 45
    if (-not (Test-Path $dst) -or (Get-Item $dst).Length -eq 0) { throw "Download vazio: $rel" }
  }

  $stageTools = To-Local $Stage $ToolsRel
  Write-Host 'Compilando modulos Python baixados...'
  & $Python -m py_compile `
    (Join-Path $stageTools 'extend_modelo_v20_store.py') `
    (Join-Path $stageTools 'extend_modelo_v20_store_visible_nav.py') `
    (Join-Path $stageTools 'install_modelo_v20_adoption.py') `
    (Join-Path $stageTools 'validate_modelo_v20_store.py') `
    (Join-Path $stageTools 'render_modelo_v20_pages.py') `
    (Join-Path $stageTools 'provision_new_blog_v20.py')
  if ($LASTEXITCODE -ne 0) { throw 'py_compile falhou; nenhuma troca local foi feita.' }

  Write-Host 'Validando contrato V20/LOJA no staging...'
  & $Python (Join-Path $stageTools 'validate_modelo_v20_store.py')
  if ($LASTEXITCODE -ne 0) { throw 'Validador V20/LOJA falhou; nenhuma troca local foi feita.' }

  foreach ($rel in $Files) {
    $current = To-Local $Root $rel
    $saved = To-Local $Backup $rel
    if (Test-Path $current) {
      New-Item -ItemType Directory -Force -Path (Split-Path $saved -Parent) | Out-Null
      Copy-Item -LiteralPath $current -Destination $saved -Force
    }
  }

  foreach ($rel in $Files) {
    $src = To-Local $Stage $rel
    $dst = To-Local $Root $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    $tmp = "$dst.syncing.tmp"
    Copy-Item -LiteralPath $src -Destination $tmp -Force
    Move-Item -LiteralPath $tmp -Destination $dst -Force
  }

  Write-Host 'Revalidando copia operacional instalada...'
  & $Python (Join-Path $Tools 'validate_modelo_v20_store.py')
  if ($LASTEXITCODE -ne 0) { throw "Validacao pos-sync falhou. Backup preservado em $Backup" }

  $visible = Join-Path $Tools 'extend_modelo_v20_store_visible_nav.py'
  $install = Join-Path $Tools 'install_modelo_v20_adoption.py'
  if (-not (Select-String -Quiet -Path $visible -Pattern 'BLOGGER_MODELO_V20_STORE_VISIBLE_NAV' -SimpleMatch)) { throw 'Marker do menu visivel ausente apos sync.' }
  if (-not (Select-String -Quiet -Path $install -Pattern 'store_visible_nav_marker' -SimpleMatch)) { throw 'Instalador local ainda nao confirma menu visivel.' }

  Write-Host ''
  Write-Host 'SYNC_V20_STORE_VISIBLE_NAV_OK'
  Write-Host "commit=$Commit"
  Write-Host "root=$Root"
  Write-Host "backup=$Backup"
  Write-Host 'runner_restart_required=false'
  exit 0
}
catch {
  Write-Error $_.Exception.Message
  Write-Host "SYNC_V20_STORE_VISIBLE_NAV_FAIL backup=$Backup stage=$Stage"
  exit 1
}
finally {
  if (Test-Path $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force -ErrorAction SilentlyContinue }
}
