param(
  [switch]$SkipDataFiles
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SwissRoot = Join-Path $Root "swiss-eph"
$EpheDir = Join-Path $SwissRoot "ephe"
$BinDir = Join-Path $SwissRoot "bin"

New-Item -ItemType Directory -Path $SwissRoot, $EpheDir, $BinDir -Force | Out-Null

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Save-RemoteFile {
  param(
    [Parameter(Mandatory = $true)][string]$Uri,
    [Parameter(Mandatory = $true)][string]$OutFile
  )

  Write-Host "Downloading $Uri"
  Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing
  if (!(Test-Path -LiteralPath $OutFile)) {
    throw "Download failed: $OutFile was not created."
  }
  $item = Get-Item -LiteralPath $OutFile
  if ($item.Length -lt 1KB) {
    throw "Download failed: $OutFile is unexpectedly small."
  }
}

$Swetest = Join-Path $BinDir "swetest64.exe"
Save-RemoteFile `
  -Uri "https://raw.githubusercontent.com/aloistr/swisseph/master/windows/programs/swetest64.exe" `
  -OutFile $Swetest

if (!$SkipDataFiles) {
  $DataFiles = @(
    "sepl_18.se1",
    "semo_18.se1",
    "seas_18.se1"
  )

  foreach ($file in $DataFiles) {
    Save-RemoteFile `
      -Uri "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/$file" `
      -OutFile (Join-Path $EpheDir $file)
  }
}

$TestArgs = @(
  "-edir$EpheDir",
  "-b01.06.2026",
  "-ut12:00:00",
  "-p0123456789Dt",
  "-fPls",
  "-g,",
  "-head",
  "-speed"
)

Write-Host ""
Write-Host "Testing Swiss Ephemeris..."
& $Swetest @TestArgs

Write-Host ""
Write-Host "Swiss Ephemeris setup complete."
Write-Host "swetest: $Swetest"
Write-Host "ephe:    $EpheDir"
