<#
.SYNOPSIS
  Builds a NIGHT FALL target and captures the full output.
.EXAMPLE
  .\Tools\Build.ps1
.EXAMPLE
  .\Tools\Build.ps1 -Target NightFallServer
#>
[CmdletBinding()]
param(
    [string]$Target = 'NightFallEditor',
    [ValidateSet('Development', 'DebugGame', 'Shipping')]
    [string]$Configuration = 'Development',
    [string]$Platform = 'Win64'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EngineRoot = 'C:\UE_5.8'
$BuildBat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$UProject = Join-Path $ProjectRoot 'NightFall.uproject'

if (-not (Test-Path $BuildBat)) { throw "Build.bat not found: $BuildBat" }
if (-not (Test-Path $UProject)) { throw "uproject not found: $UProject" }

$logDir = Join-Path $ProjectRoot 'Saved\BuildLogs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir ("{0}-{1}-{2}.log" -f $Target, $Configuration, (Get-Date -Format 'yyyyMMdd-HHmmss'))

Write-Host "=== Building $Target $Platform $Configuration ===" -ForegroundColor Cyan
Write-Host "Project : $UProject"
Write-Host "Engine  : $EngineRoot"
Write-Host "Log     : $logFile`n"

$buildArgs = @($Target, $Platform, $Configuration, "-Project=$UProject", '-WaitMutex', '-FromMsBuild')
$started = Get-Date

$lines = @()
& $BuildBat @buildArgs 2>&1 | ForEach-Object {
    $text = "$_"
    $lines += $text
    Write-Host $text
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
$elapsed = (Get-Date) - $started

$all = $lines -join "`r`n"
$all | Set-Content -Path $logFile -Encoding UTF8

$errors = @()
foreach ($line in ($all -split "`r?`n")) {
    if ($line -match '(error [A-Z]+\d+|error C\d+|error LNK\d+|Fatal error)') { $errors += $line.Trim() }
}

Write-Host ""
Write-Host ("Elapsed: {0:n1}s   Exit code: {1}" -f $elapsed.TotalSeconds, $exitCode) -ForegroundColor $(if ($exitCode -eq 0) { 'Green' } else { 'Red' })

if ($exitCode -eq 0) {
    Write-Host "BUILD SUCCEEDED" -ForegroundColor Green
} else {
    Write-Host "BUILD FAILED - first errors:" -ForegroundColor Red
    $errors | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    if ($errors.Count -eq 0) { Write-Host "  (no 'error' lines matched; see $logFile)" -ForegroundColor Yellow }
}

exit $exitCode
