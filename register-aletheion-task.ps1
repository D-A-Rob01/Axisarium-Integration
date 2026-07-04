param(
  [string]$StartTime = "06:00"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runner = Join-Path $Root "run-daily-aletheion.ps1"
$LogDir = Join-Path $Root "logs"
$InstallLog = Join-Path $LogDir "scheduler-install.log"
$TaskName = "Aletheion Daily Sky"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Start-Transcript -Path $InstallLog -Append | Out-Null
try {
  Write-Host "Aletheion scheduler installer started: $(Get-Date -Format o)"
  Write-Host "Running as: $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
  Write-Host "Root: $Root"

if (!(Test-Path -LiteralPath $Runner)) {
  throw "Runner not found: $Runner"
}

function Register-LimitedFallback {
  param(
    [string]$RunnerPath,
    [string]$DailyTaskName,
    [string]$CatchupTaskName,
    [string]$DailyStartTime
  )

  $PowerShellPath = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
  $TaskRun = "`"$PowerShellPath`" -NoProfile -ExecutionPolicy Bypass -File `"$RunnerPath`""

  & schtasks.exe /Create /TN $DailyTaskName /SC DAILY /ST $DailyStartTime /TR $TaskRun /RL LIMITED /F | Write-Host
  if ($LASTEXITCODE -ne 0) {
    throw "Limited daily task registration failed with exit code $LASTEXITCODE."
  }

  & schtasks.exe /Create /TN $CatchupTaskName /SC ONLOGON /TR $TaskRun /RL LIMITED /F | Write-Host
  if ($LASTEXITCODE -ne 0) {
    throw "Limited logon catch-up task registration failed with exit code $LASTEXITCODE."
  }

  Write-Host "Registered limited fallback tasks:"
  Write-Host "  ${DailyTaskName}: daily at $DailyStartTime"
  Write-Host "  ${CatchupTaskName}: at logon"
  Write-Host "Note: Wake-to-run and retry settings require the elevated ScheduledTasks registration path."
}

try {
  $Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" `
    -WorkingDirectory $Root

  $DailyTrigger = New-ScheduledTaskTrigger -Daily -At $StartTime
  $LogonCatchupTrigger = New-ScheduledTaskTrigger -AtLogOn
  $Triggers = @($DailyTrigger, $LogonCatchupTrigger)

  $Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

  Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Description "Generate Aletheion Daily Sky note into the OneDrive-synced Obsidian vault." `
    -Force | Out-Null

  Write-Host "Registered task: $TaskName"
  Write-Host "Schedule: daily at $StartTime, plus logon catch-up"
  Write-Host "Wake to run: enabled"
  Write-Host "Missed-run catch-up: enabled"
  Write-Host "Runner: $Runner"
} catch {
  Write-Warning "Full ScheduledTasks registration failed: $($_.Exception.Message)"
  Write-Warning "Attempting limited current-user fallback registration with schtasks.exe."
  Register-LimitedFallback `
    -RunnerPath $Runner `
    -DailyTaskName $TaskName `
    -CatchupTaskName "$TaskName Catchup" `
    -DailyStartTime $StartTime
}
} finally {
  Write-Host "Aletheion scheduler installer finished: $(Get-Date -Format o)"
  Stop-Transcript | Out-Null
}
