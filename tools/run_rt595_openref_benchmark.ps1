[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Port,
    [string]$InstallRoot,
    [string]$OutputDirectory,
    [ValidateSet("linkserver", "jlink")]
    [string]$Runner = "linkserver",
    [int]$Baud = 115200,
    [int]$CaptureSeconds = 1860,
    [switch]$SkipFlash
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($CaptureSeconds -lt 1830) {
    throw "CaptureSeconds must be at least 1830 (1810 s workload plus startup/flash margin)."
}
if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $PSScriptRoot "..\artifacts\local\rt595-sdk"
}
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$build = Join-Path $InstallRoot "build\openref_rt595_benchmark"
$sdk = Join-Path $InstallRoot "workspace\mcuxsdk"
$python = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$west = Join-Path $InstallRoot ".venv\Scripts\west.exe"
$elf = Join-Path $build "openref_rt595_benchmark_cm33.elf"
$map = Join-Path $build "output.map"
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputDirectory = Join-Path $repoRoot "artifacts\local\rt595-benchmark-$stamp"
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)

foreach ($required in @($python, $west, $sdk, $elf)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing prerequisite: $required. Build the paced image first."
    }
}
if (-not $SkipFlash) {
    $flasher = if ($Runner -eq "linkserver") { "LinkServer.exe" } else { "JLink.exe" }
    if (-not (Get-Command $flasher -ErrorAction SilentlyContinue)) {
        throw "$flasher is not on PATH. Install the selected debug probe software or use -SkipFlash after flashing separately."
    }
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$rawLog = Join-Path $OutputDirectory "uart.log"
$resultJson = Join-Path $OutputDirectory "result.json"
$captureStdout = Join-Path $OutputDirectory "capture.stdout.log"
$captureStderr = Join-Path $OutputDirectory "capture.stderr.log"
$captureArgs = @(
    (Join-Path $repoRoot "tools\capture_serial.py"),
    "--port", $Port, "--baud", $Baud,
    "--output", $rawLog, "--duration-seconds", $CaptureSeconds,
    "--reset-input-buffer"
)
$capture = Start-Process -FilePath $python -ArgumentList $captureArgs -PassThru `
    -WindowStyle Hidden -RedirectStandardOutput $captureStdout `
    -RedirectStandardError $captureStderr
Start-Sleep -Seconds 2
if ($capture.HasExited) {
    throw "UART capture exited before flashing; inspect $captureStderr"
}

try {
    if (-not $SkipFlash) {
        Push-Location $sdk
        try {
            & $west flash -d $build -r $Runner
            if ($LASTEXITCODE -ne 0) { throw "west flash failed: $LASTEXITCODE" }
        }
        finally { Pop-Location }
    } else {
        Write-Host "Capture active. Reset the already-flashed board now."
    }

    Write-Host "Capturing $Port at $Baud baud for $CaptureSeconds seconds (workload alone is 1810 seconds)."
    $capture.WaitForExit()
    if ($capture.ExitCode -ne 0) {
        throw "UART capture failed with exit code $($capture.ExitCode); inspect $captureStderr"
    }
}
catch {
    if (-not $capture.HasExited) { $capture.Kill($true) }
    throw
}

& $python (Join-Path $repoRoot "tools\extract_audio_benchmark_result.py") $rawLog $resultJson
if ($LASTEXITCODE -ne 0) { throw "No unique benchmark result was captured." }
& $python (Join-Path $repoRoot "tools\validate_audio_benchmark_result.py") $resultJson
if ($LASTEXITCODE -ne 0) { throw "Captured result failed promotion validation." }

Copy-Item -LiteralPath $elf -Destination $OutputDirectory
if (Test-Path -LiteralPath $map) { Copy-Item -LiteralPath $map -Destination $OutputDirectory }
$hashed = Get-ChildItem -LiteralPath $OutputDirectory -File |
    Where-Object { $_.Name -ne "sha256.txt" } |
    Sort-Object Name |
    ForEach-Object { "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant(), $_.Name }
Set-Content -LiteralPath (Join-Path $OutputDirectory "sha256.txt") -Value $hashed -Encoding ascii
Write-Host "PASS: preserved validated RT595 evidence in $OutputDirectory"
