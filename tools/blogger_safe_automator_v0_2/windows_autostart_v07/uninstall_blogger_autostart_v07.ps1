$ErrorActionPreference = 'Stop'
$TaskName = 'BloggerAutomationV20'
$StartupDir = [Environment]::GetFolderPath('Startup')
$FallbackCmd = Join-Path $StartupDir 'BloggerAutomationV20.cmd'

try {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }
} catch {}

if (Test-Path $FallbackCmd) { Remove-Item $FallbackCmd -Force }

[ordered]@{
  status = 'BLOGGER_AUTOSTART_UNINSTALLED'
  task_name = $TaskName
  startup_fallback_removed = -not (Test-Path $FallbackCmd)
  token_file_preserved = $true
} | ConvertTo-Json
