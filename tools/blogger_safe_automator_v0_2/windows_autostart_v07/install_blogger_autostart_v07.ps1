param(
  [string]$Root = 'C:\Blogger-Automator\blogger_safe_automator_v0_3',
  [string]$Token = $env:BLOGGER_RUNNER_TOKEN
)

$ErrorActionPreference = 'Stop'
$TaskName = 'BloggerAutomationV20'
$Tools = Join-Path $Root 'tools\blogger_safe_automator_v0_2'
$Launcher = Join-Path $Tools 'windows_autostart_v07\start_blogger_automation_v07.ps1'
$SecretDir = 'C:\Blogger-Automator\secrets'
$SecretFile = Join-Path $SecretDir 'blogger_runner_token.dpapi'
$StartupDir = [Environment]::GetFolderPath('Startup')
$FallbackCmd = Join-Path $StartupDir 'BloggerAutomationV20.cmd'

if (-not (Test-Path $Launcher)) { throw "Launcher não encontrado: $Launcher" }
if (-not $Token -or $Token.Length -lt 32) { throw 'Forneça BLOGGER_RUNNER_TOKEN com pelo menos 32 caracteres.' }

New-Item -ItemType Directory -Force -Path $SecretDir | Out-Null
$secure = ConvertTo-SecureString $Token -AsPlainText -Force
$secure | ConvertFrom-SecureString | Set-Content -Encoding ASCII -Path $SecretFile

$ps = (Get-Command powershell.exe).Source
$args = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Launcher`""
$installedBy = $null

try {
  $action = New-ScheduledTaskAction -Execute $ps -Argument $args
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
  if (Test-Path $FallbackCmd) { Remove-Item $FallbackCmd -Force }
  $installedBy = 'scheduled_task'
  Start-ScheduledTask -TaskName $TaskName
} catch {
  $cmd = "@echo off`r`nstart `"`" /min powershell.exe $args`r`n"
  Set-Content -Path $FallbackCmd -Value $cmd -Encoding ASCII
  $installedBy = 'startup_folder_fallback'
  Start-Process -FilePath $ps -ArgumentList $args -WindowStyle Hidden
}

Start-Sleep -Seconds 3
$result = [ordered]@{
  status = 'BLOGGER_AUTOSTART_INSTALLED'
  installed_by = $installedBy
  task_name = $TaskName
  launcher = $Launcher
  token_storage = $SecretFile
  token_storage_mode = 'Windows DPAPI current user'
  startup_fallback = $FallbackCmd
}
$result | ConvertTo-Json
