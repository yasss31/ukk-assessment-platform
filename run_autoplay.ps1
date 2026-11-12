param(
    [switch]$status,
    [switch]$run_now,
    [switch]$enable,
    [switch]$disable,
    [int]$interval = 180,
    [switch]$loop,
    [string]$creds
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $scriptDir "backend\venv\Scripts\python.exe"
$pyScript = Join-Path $scriptDir "run_autoplay.py"

if (-not (Test-Path $pythonPath)) {
    $parentPython = Join-Path $scriptDir "..\ukk-assessment-platform\backend\venv\Scripts\python.exe"
    if (Test-Path $parentPython) {
        $pythonPath = $parentPython
        $pyScript = Join-Path $scriptDir "..\ukk-assessment-platform\run_autoplay.py"
    } else {
        $pythonPath = "python"
    }
}

$pyArgs = @()
if ($status) { $pyArgs += "--status" }
if ($run_now) { $pyArgs += "--run-now" }
if ($enable) { $pyArgs += "--enable" }
if ($disable) { $pyArgs += "--disable" }
if ($interval -ne 180 -or $enable) { $pyArgs += @("--interval", "$interval") }
if ($loop) { $pyArgs += "--loop" }
if ($creds) { $pyArgs += @("--creds", "$creds") }

& $pythonPath $pyScript @pyArgs
