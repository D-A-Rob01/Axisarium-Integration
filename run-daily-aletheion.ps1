param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Users\david\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$ConfigPath = Join-Path $Root "config\aletheion.config.json"
$GuardedRunner = Join-Path $Root "tools\run_aletheion_guarded.py"
$LogDir = Join-Path $Root "logs"
$Stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$LogFile = Join-Path $LogDir "aletheion-$Stamp.log"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Set-Location $Root

"Aletheion guarded daily run started: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile

if (!(Test-Path -LiteralPath $ConfigPath)) {
  "Config not found: $ConfigPath" | Tee-Object -FilePath $LogFile -Append
  exit 1
}
if (!(Test-Path -LiteralPath $GuardedRunner)) {
  "Guarded runner not found: $GuardedRunner" | Tee-Object -FilePath $LogFile -Append
  exit 1
}

$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$TimeZoneId = "Eastern Standard Time"
try {
  $UtcNow = [DateTimeOffset]::UtcNow
  $Eastern = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($UtcNow, $TimeZoneId)
  $Day = $Eastern.ToString("yyyy-MM-dd")
} catch {
  "Unable to resolve America/New_York date: $($_.Exception.Message)" | Tee-Object -FilePath $LogFile -Append
  exit 1
}

$Vault = [string]$Config.obsidian_vault_path
$DailyFolder = [string]$Config.daily_note_folder
if ([string]::IsNullOrWhiteSpace($DailyFolder)) {
  $DailyFolder = "02 Daily Sky"
}
$OutputPath = Join-Path (Join-Path $Vault $DailyFolder) "Daily Sky - $Day.md"

"Resolved production date: $Day (America/New_York)" | Tee-Object -FilePath $LogFile -Append
"Target note: $OutputPath" | Tee-Object -FilePath $LogFile -Append

$Arguments = @($GuardedRunner, "--date", $Day)
if ($Force) {
  $Arguments += "--force"
}

"& $Python $($Arguments -join ' ')" | Tee-Object -FilePath $LogFile -Append

$PriorErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$Output = & $Python @Arguments 2>&1
$ExitCode = $LASTEXITCODE
$ErrorActionPreference = $PriorErrorActionPreference

$Output | Tee-Object -FilePath $LogFile -Append

"Aletheion guarded daily run finished: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile -Append
"Exit code: $ExitCode" | Tee-Object -FilePath $LogFile -Append

exit $ExitCode
