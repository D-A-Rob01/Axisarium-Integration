param(
  [switch]$Force,
  [string]$Date,
  [switch]$DryRun,
  [string]$PythonPath
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
  $PSNativeCommandUseErrorActionPreference = $false
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectPython = Join-Path $Root ".venv\Scripts\python.exe"
$FallbackPython = "C:\Users\david\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Python = if (-not [string]::IsNullOrWhiteSpace($PythonPath)) {
  $PythonPath
} elseif (Test-Path -LiteralPath $ProjectPython -PathType Leaf) {
  $ProjectPython
} else {
  $FallbackPython
}
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) {
  throw "Python runtime not found: $Python"
}
$ConfigPath = Join-Path $Root "config\aletheion.config.json"
$GuardedRunner = Join-Path $Root "tools\run_aletheion_guarded.py"
$SourceGate = Join-Path $Root "tools\validate_topologos_source.py"
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
if (!(Test-Path -LiteralPath $SourceGate)) {
  "Topologos source gate not found: $SourceGate" | Tee-Object -FilePath $LogFile -Append
  exit 1
}

$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
if (-not [string]::IsNullOrWhiteSpace($Date)) {
  $Day = $Date
} else {
  try {
    $UtcNow = [DateTimeOffset]::UtcNow
    $Eastern = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($UtcNow, "Eastern Standard Time")
    $Day = $Eastern.ToString("yyyy-MM-dd")
  } catch {
    "Unable to resolve America/New_York date: $($_.Exception.Message)" | Tee-Object -FilePath $LogFile -Append
    exit 1
  }
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
$DryRunDirectory = $null
$SourcePath = $OutputPath
if ($DryRun) {
  $DryRunDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("aletheion-dry-run-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $DryRunDirectory | Out-Null
  $SourcePath = Join-Path $DryRunDirectory "Daily Sky - $Day.md"
  $Arguments += @("--dry-run", "--stage-dir", $DryRunDirectory)
  "Dry-run staging only: $SourcePath" | Tee-Object -FilePath $LogFile -Append
}

"& $Python $($Arguments -join ' ')" | Tee-Object -FilePath $LogFile -Append

$PriorErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$Output = & $Python @Arguments 2>&1
$ExitCode = $LASTEXITCODE
$ErrorActionPreference = $PriorErrorActionPreference

$Output | Tee-Object -FilePath $LogFile -Append

if ($ExitCode -eq 0) {
  $GateArguments = @($SourceGate, "--requested-date", $Day, "--source", $SourcePath)
  "& $Python $($GateArguments -join ' ')" | Tee-Object -FilePath $LogFile -Append
  $PriorErrorActionPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $GateOutput = & $Python @GateArguments 2>&1
  $GateExitCode = $LASTEXITCODE
  $ErrorActionPreference = $PriorErrorActionPreference
  $GateOutput | Tee-Object -FilePath $LogFile -Append
  if ($GateExitCode -ne 0) {
    "Topologos source gate rejected the guarded producer output." | Tee-Object -FilePath $LogFile -Append
    $ExitCode = $GateExitCode
  }
}

if ($DryRunDirectory) {
  $ResolvedTempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
  $ResolvedDryRun = [System.IO.Path]::GetFullPath($DryRunDirectory)
  if ($ResolvedDryRun.StartsWith($ResolvedTempRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
      (Split-Path -Leaf $ResolvedDryRun).StartsWith("aletheion-dry-run-")) {
    Remove-Item -LiteralPath $ResolvedDryRun -Recurse -Force
    "Dry-run staging removed; production note, ledgers, and captures were not written." | Tee-Object -FilePath $LogFile -Append
  } else {
    "Refusing to remove unexpected dry-run staging path: $ResolvedDryRun" | Tee-Object -FilePath $LogFile -Append
    $ExitCode = 1
  }
}

"Aletheion guarded daily run finished: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile -Append
"Exit code: $ExitCode" | Tee-Object -FilePath $LogFile -Append

exit $ExitCode
