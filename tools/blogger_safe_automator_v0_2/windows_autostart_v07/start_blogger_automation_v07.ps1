param(
  [string]$Root = 'C:\Blogger-Automator\blogger_safe_automator_v0_3'
)

$ErrorActionPreference = 'Stop'
$Tools = Join-Path $Root 'tools\blogger_safe_automator_v0_2'
$Python = Join-Path $Tools '.venv\Scripts\python.exe'
$Runner = Join-Path $Tools 'local_service_v08.py'
$Profile = 'C:\Blogger-Automator\chrome-debug-profile'
$SecretFile = 'C:\Blogger-Automator\secrets\blogger_runner_token.dpapi'
$LogDir = 'C:\Blogger-Automator\logs\autostart'
$LogFile = Join-Path $LogDir 'blogger_automation_v08.log'
$ExpectedVersion = '0.8'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
function Log([string]$m) { Add-Content -Path $LogFile -Value ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }

function Unprotect-Token {
  if ($env:BLOGGER_RUNNER_TOKEN -and $env:BLOGGER_RUNNER_TOKEN.Length -ge 32) { return $env:BLOGGER_RUNNER_TOKEN }
  if (-not (Test-Path $SecretFile)) { throw "Token DPAPI não encontrado: $SecretFile" }
  $enc = Get-Content -Raw -Path $SecretFile
  $sec = ConvertTo-SecureString $enc
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

function Probe-Cdp {
  try {
    $r = Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2
    return [bool]$r.Browser
  } catch { return $false }
}

function Find-Chrome {
  $candidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
  )
  foreach ($p in $candidates) { if ($p -and (Test-Path $p)) { return $p } }
  throw 'Google Chrome oficial não encontrado.'
}

function Probe-Runner([string]$token) {
  try {
    $h = @{ Authorization = 'Bearer ' + $token }
    return Invoke-RestMethod 'http://127.0.0.1:8765/v1/health' -Headers $h -TimeoutSec 2
  } catch { return $null }
}

function Stop-OldSafeRunner {
  try {
    $listeners = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction Stop
  } catch { return }
  foreach ($l in $listeners) {
    $p = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $l.OwningProcess) -ErrorAction SilentlyContinue
    if (-not $p) { continue }
    $cmd = [string]$p.CommandLine
    if ($cmd -like "*$Tools*" -and $cmd -match 'local_service_v0[3-8]\.py') {
      Log "Encerrando runner antigo controlado PID=$($p.ProcessId)"
      Stop-Process -Id $p.ProcessId -Force
      Start-Sleep -Milliseconds 700
    } else {
      throw "Porta 8765 ocupada por processo não reconhecido; abortando por segurança."
    }
  }
}

try {
  Log '=== bootstrap iniciado ==='
  if (-not (Test-Path $Python)) { throw "Python da venv não encontrado: $Python" }
  if (-not (Test-Path $Runner)) { throw "Runner v0.8 não encontrado: $Runner" }
  $token = Unprotect-Token
  if (-not $token -or $token.Length -lt 32) { throw 'BLOGGER_RUNNER_TOKEN inválido.' }
  $env:BLOGGER_RUNNER_TOKEN = $token

  if (-not (Probe-Cdp)) {
    $chrome = Find-Chrome
    Log "Iniciando Chrome CDP: $chrome"
    Start-Process -FilePath $chrome -ArgumentList @('--remote-debugging-port=9222','--remote-debugging-address=127.0.0.1',("--user-data-dir=$Profile"),'https://www.blogger.com/')
    $ok = $false
    for ($i=0; $i -lt 30; $i++) { Start-Sleep -Seconds 1; if (Probe-Cdp) { $ok = $true; break } }
    if (-not $ok) { throw 'Chrome CDP não ficou disponível em 30s.' }
  }
  Log 'Chrome CDP OK.'

  $health = Probe-Runner $token
  if ($health -and [string]$health.version -eq $ExpectedVersion) {
    Log "Runner v$ExpectedVersion já estava ativo."
  } else {
    if ($health) { Log "Runner ativo em versão diferente: $($health.version)." }
    Stop-OldSafeRunner
    Log "Iniciando runner v$ExpectedVersion."
    Start-Process -FilePath $Python -ArgumentList @($Runner) -WorkingDirectory $Tools -WindowStyle Hidden
    $ready = $false
    for ($i=0; $i -lt 30; $i++) {
      Start-Sleep -Seconds 1
      $health = Probe-Runner $token
      if ($health -and [string]$health.version -eq $ExpectedVersion) { $ready = $true; break }
    }
    if (-not $ready) { throw "Runner v$ExpectedVersion não respondeu em 30s." }
  }

  Log "BOOTSTRAP_OK runner=$($health.version) cdp=9222 runtime_guard=v20"
  exit 0
} catch {
  Log ("BOOTSTRAP_FAIL " + $_.Exception.Message)
  exit 1
}
