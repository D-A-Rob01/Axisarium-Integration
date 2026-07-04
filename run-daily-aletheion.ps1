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
$LogDir = Join-Path $Root "logs"
$Stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$LogFile = Join-Path $LogDir "aletheion-$Stamp.log"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Set-Location $Root

"Aletheion daily run started: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile

if (!(Test-Path -LiteralPath $ConfigPath)) {
  "Config not found: $ConfigPath" | Tee-Object -FilePath $LogFile -Append
  exit 1
}

$Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$Day = Get-Date -Format "yyyy-MM-dd"
$Vault = [string]$Config.obsidian_vault_path
$DailyFolder = [string]$Config.daily_note_folder
if ([string]::IsNullOrWhiteSpace($DailyFolder)) {
  $DailyFolder = "02 Daily Sky"
}
$OutputPath = Join-Path (Join-Path $Vault $DailyFolder) "Daily Sky - $Day.md"

"Target note: $OutputPath" | Tee-Object -FilePath $LogFile -Append

if (!$Force -and (Test-Path -LiteralPath $OutputPath)) {
  $Existing = Get-Item -LiteralPath $OutputPath
  if ($Existing.Length -gt 0) {
    "Today's note already exists; skipping. Use -Force to regenerate." | Tee-Object -FilePath $LogFile -Append
    "Aletheion daily run finished: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile -Append
    "Exit code: 0" | Tee-Object -FilePath $LogFile -Append
    exit 0
  }
}

"& $Python .\aletheion.py daily --vault" | Tee-Object -FilePath $LogFile -Append

$PriorErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$Output = & $Python ".\aletheion.py" daily --vault 2>&1
$ExitCode = $LASTEXITCODE
$ErrorActionPreference = $PriorErrorActionPreference

$Output | Tee-Object -FilePath $LogFile -Append

"Aletheion daily run finished: $(Get-Date -Format o)" | Tee-Object -FilePath $LogFile -Append
"Exit code: $ExitCode" | Tee-Object -FilePath $LogFile -Append

exit $ExitCode
