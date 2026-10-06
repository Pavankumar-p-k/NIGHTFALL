<#
.SYNOPSIS
  Validates the NIGHT FALL toolchain, engine registration and project integrity.
.EXAMPLE
  .\Tools\Validate-Environment.ps1
.EXAMPLE
  .\Tools\Validate-Environment.ps1 -EditorSmokeTest
#>
[CmdletBinding()]
param(
    [switch]$EditorSmokeTest,
    [int]$SmokeTestTimeoutSec = 300
)

$ErrorActionPreference = 'Continue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EngineRoot = 'C:\UE_5.8'
$BuildBat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$EditorExe = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
$EditorCmdExe = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$UProject = Join-Path $ProjectRoot 'NightFall.uproject'
$LogFile = Join-Path $PSScriptRoot 'validation-latest.txt'

$script:Results = @()
function Add-Result {
    param([string]$Id, [string]$Title, [bool]$Pass, [string]$Detail)
    $script:Results += [pscustomobject]@{ Id = $Id; Title = $Title; Pass = $Pass; Detail = $Detail }
    $mark = if ($Pass) { 'PASS' } else { 'FAIL' }
    Write-Host ("[{0}] {1} - {2}" -f $mark, $Title, $Detail)
}
function Add-Optional {
    param([string]$Id, [string]$Title, [bool]$Pass, [string]$Detail)
    $script:Results += [pscustomobject]@{ Id = $Id; Title = $Title; Pass = $Pass; Detail = $Detail }
    $mark = if ($Pass) { 'PASS' } else { 'SKIP' }
    Write-Host ("[{0}] {1} - {2}" -f $mark, $Title, $Detail)
}

Write-Host "=== NIGHT FALL environment validation ===" -ForegroundColor Cyan
Write-Host ("Project : {0}" -f $ProjectRoot)
Write-Host ("Engine  : {0}`n" -f $EngineRoot)

# --- Engine ---
Add-Result 'E1' 'Engine root exists' (Test-Path $EngineRoot) $EngineRoot
Add-Result 'E2' 'Build.bat present' (Test-Path $BuildBat) $BuildBat
Add-Result 'E3' 'UnrealEditor.exe present' (Test-Path $EditorExe) $EditorExe
Add-Result 'E4' 'UnrealEditor-Cmd.exe present' (Test-Path $EditorCmdExe) $EditorCmdExe
Add-Result 'E5' 'Engine is registered in HKCU Builds key' `
    ((Get-ItemProperty -Path 'HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds' -Name '5.8' -ErrorAction SilentlyContinue).'5.8' -eq $EngineRoot) `
    'HKCU:\SOFTWARE\Epic Games\Unreal Engine\Builds\5.8'

# --- Project files ---
$requiredFiles = @(
    'NightFall.uproject',
    '.gitignore', '.gitattributes',
    'README.md',
    'Docs\DEVELOPMENT.md', 'Docs\ARCHITECTURE.md', 'Docs\BUILD.md',
    'Docs\ROADMAP.md', 'Docs\TESTING.md', 'Docs\DEVELOPMENT_RULES.md',
    'Config\DefaultEngine.ini', 'Config\DefaultGame.ini', 'Config\DefaultInput.ini', 'Config\DefaultEditor.ini',
    'Source\NightFall.Target.cs', 'Source\NightFallEditor.Target.cs', 'Source\NightFallServer.Target.cs',
    'Source\NightFall\NightFall.Build.cs', 'Source\NightFall\NightFall.cpp', 'Source\NightFall\NightFall.h',
    'Tools\Build.ps1'
)
$missing = @()
foreach ($f in $requiredFiles) {
    if (-not (Test-Path (Join-Path $ProjectRoot $f))) { $missing += $f }
}
Add-Result 'P1' 'Project files present' ($missing.Count -eq 0) `
    $(if ($missing.Count -eq 0) { "$($requiredFiles.Count)/$($requiredFiles.Count) files" } else { "missing: $($missing -join ', ')" })

# --- .uproject parses and points at 5.8 ---
$uprojectOk = $false; $uprojectDetail = 'parse failed'
try {
    $json = Get-Content $UProject -Raw | ConvertFrom-Json
    $modOk = ($json.Modules | Where-Object { $_.Name -eq 'NightFall' }) -ne $null
    $pluginOk = ($json.Plugins | Where-Object { $_.Name -eq 'EnhancedInput' }) -ne $null
    $uprojectOk = ($json.EngineAssociation -eq '5.8') -and $modOk -and $pluginOk
    $uprojectDetail = "EngineAssociation='$($json.EngineAssociation)', module=$modOk, EnhancedInput=$pluginOk"
} catch { $uprojectDetail = $_.Exception.Message }
Add-Result 'P2' '.uproject is valid JSON with NightFall module' $uprojectOk $uprojectDetail

# --- Toolchain ---
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = $null
if (Test-Path $vswhere) { $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null }
Add-Result 'T1' 'Visual Studio with C++ toolset' ($null -ne $vsPath -and $vsPath -ne '') $(if ($vsPath) { $vsPath } else { 'not found (install VS with NativeDesktop workload)' })

$cl = $null
$msvcRoot = 'C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC'
if (Test-Path $msvcRoot) {
    $vers = Get-ChildItem $msvcRoot -Directory | Sort-Object Name -Descending
    foreach ($v in $vers) {
        $candidate = Join-Path $v.FullName 'bin\Hostx64\x64\cl.exe'
        if (Test-Path $candidate) { $cl = $candidate; break }
    }
}
Add-Result 'T2' 'MSVC compiler (cl.exe)' ($null -ne $cl) $(if ($cl) { $cl } else { 'not found under ' + $msvcRoot })

$sdk = $null
$sdkRoot = 'C:\Program Files (x86)\Windows Kits\10\Include'
if (Test-Path $sdkRoot) {
    $sdk = (Get-ChildItem $sdkRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1).Name
}
Add-Result 'T3' 'Windows 10/11 SDK' ($null -ne $sdk) $(if ($sdk) { "10.0.$sdk installed" } else { 'not found' })

$gitOk = $false; $gitVer = ''
try { $gitVer = (& git --version 2>$null); $gitOk = $LASTEXITCODE -eq 0 } catch {}
Add-Result 'T4' 'Git available' $gitOk $gitVer

$lfsOk = $false; $lfsVer = ''
try { $lfsVer = (& git lfs version 2>$null); $lfsOk = $LASTEXITCODE -eq 0 } catch {}
Add-Result 'T5' 'Git LFS available' $lfsOk $lfsVer

$disk = Get-PSDrive -Name 'C'
$freeGB = [math]::Round($disk.Free / 1GB, 1)
Add-Result 'T6' 'C: free space for builds (>= 20 GB)' ($freeGB -ge 20) "$freeGB GB free"

$isGitRepo = Test-Path (Join-Path $ProjectRoot '.git')
Add-Result 'P3' 'Git repository initialised' $isGitRepo 'git init -b main (run if FAIL)'

# --- Optional: editor smoke test ---
if ($EditorSmokeTest) {
    Write-Host "`nRunning headless editor smoke test (timeout ${SmokeTestTimeoutSec}s)..." -ForegroundColor Cyan
    $logPath = Join-Path $ProjectRoot 'Saved\Logs\NightFall.log'
    if (Test-Path $logPath) { Remove-Item $logPath -Force -ErrorAction SilentlyContinue }

    $argStr = "`"$UProject`" -nullrhi -unattended -nop4 -nosplash -stdout -TestExit=`"Engine Initialization) Total time`""
    $smokeOut = Join-Path $env:TEMP 'nf_smoke_out.txt'
    $smokeErr = Join-Path $env:TEMP 'nf_smoke_err.txt'
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $EditorCmdExe
    $psi.Arguments = $argStr
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $finished = $proc.WaitForExit($SmokeTestTimeoutSec * 1000)
    $exitCode = $null
    if ($finished) {
        $proc.WaitForExit()
        $exitCode = $proc.ExitCode
        try { $outTask.Result | Set-Content -Path $smokeOut -Encoding UTF8 } catch {}
        try { $errTask.Result | Set-Content -Path $smokeErr -Encoding UTF8 } catch {}
    } else {
        try { $proc.Kill() } catch {}
        Write-Host "        editor did not exit within ${SmokeTestTimeoutSec}s - killed" -ForegroundColor Yellow
    }
    $sw.Stop()

    $logOk = Test-Path $logPath
    $initOk = $false
    $exitMarker = $false
    $logFatal = $false
    $fatalLines = @()
    if ($logOk) {
        $initOk = (Select-String -Path $logPath -Pattern 'Engine Initialization\) Total time' -Quiet -ErrorAction SilentlyContinue)
        $exitMarker = (Select-String -Path $logPath -Pattern 'TestExit|LogExit: Application exit|LogExit: Engine is shut down' -Quiet -ErrorAction SilentlyContinue)
        $fatal = Select-String -Path $logPath -Pattern 'Fatal error|Assertion failed|LogInit: Error|LogWindows: Error' -ErrorAction SilentlyContinue
        if ($fatal) { $logFatal = $true; $fatalLines = @($fatal | Select-Object -First 5 | ForEach-Object { $_.Line }) }
    }
    $pass = $finished -and $logOk -and $initOk -and $exitMarker -and ($exitCode -eq 0) -and -not $logFatal
    $detail = "finished=$finished exit=$exitCode init=$initOk exitMarker=$exitMarker fatal=$logFatal elapsed=$([math]::Round($sw.Elapsed.TotalSeconds,1))s"
    Add-Result 'S1' 'Headless editor smoke test' $pass $detail
    foreach ($fl in $fatalLines) { Write-Host "        $fl" -ForegroundColor Yellow }
}

# --- Summary ---
$passCount = @($script:Results | Where-Object { $_.Pass }).Count
$total = $script:Results.Count
$failed = @($script:Results | Where-Object { -not $_.Pass })

$lines = @()
$lines += "=== NIGHT FALL validation $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
foreach ($r in $script:Results) { $lines += ("{0,-4} {1,-45} {2}" -f $(if ($r.Pass) { 'PASS' } else { 'FAIL' }), $r.Title, $r.Detail) }
$lines += ""
$lines += "RESULT: $passCount/$total passed"
$lines | Set-Content -Path $LogFile -Encoding UTF8

Write-Host ""
if ($failed.Count -eq 0) {
    Write-Host ("ALL CHECKS PASSED ($passCount/$total). Log: $LogFile") -ForegroundColor Green
    exit 0
} else {
    Write-Host ("$($failed.Count) CHECK(S) FAILED ($passCount/$total). Log: $LogFile") -ForegroundColor Red
    foreach ($f in $failed) { Write-Host ("  - {0}: {1}" -f $f.Title, $f.Detail) -ForegroundColor Red }
    exit 1
}
