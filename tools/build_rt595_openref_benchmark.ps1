[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$ToolchainRoot,
    [string]$BoardRevision = "unknown",
    [string]$CurrentMeasurement = "not_measured",
    [string]$IdleCurrentMa = "null",
    [string]$OneTalkerCurrentMa = "null",
    [string]$SixTalkerCurrentMa = "null",
    [switch]$Pristine
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $PSScriptRoot "..\artifacts\local\rt595-sdk"
}
if ([string]::IsNullOrWhiteSpace($ToolchainRoot)) {
    $ToolchainRoot = Join-Path $PSScriptRoot "..\artifacts\local\rt595-toolchain"
}
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$ToolchainRoot = [IO.Path]::GetFullPath($ToolchainRoot)
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sdk = Join-Path $InstallRoot "workspace\mcuxsdk"
$west = Join-Path $InstallRoot ".venv\Scripts\west.exe"
$python = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$source = Join-Path $repoRoot "firmware\audio_processor\targets\mimxrt595_evk\benchmark_target"
$build = Join-Path $InstallRoot "build\openref_rt595_benchmark"
$commit = (git -C $repoRoot rev-parse --verify HEAD).Trim()
$dirty = git -C $repoRoot status --porcelain --untracked-files=normal
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect repository state" }
if ($dirty) { $commit = "$commit-dirty" }
$BoardRevision = $BoardRevision -replace '\s+', '_'
$CurrentMeasurement = $CurrentMeasurement -replace '\s+', '_'
foreach ($provenance in @($BoardRevision, $CurrentMeasurement)) {
    if ($provenance -notmatch '^[A-Za-z0-9_.-]+$') {
        throw "Provenance values may contain letters, numbers, dot, dash, underscore, or spaces: $provenance"
    }
}

foreach ($required in @($west, $sdk, (Join-Path $ToolchainRoot "bin\arm-none-eabi-gcc.exe"))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing RT595 build dependency: $required. Run tools/setup_rt595_sdk.ps1 first."
    }
}
foreach ($value in @($IdleCurrentMa, $OneTalkerCurrentMa, $SixTalkerCurrentMa)) {
    if ($value -ne "null" -and $value -notmatch '^\d+(\.\d+)?$') {
        throw "Current values must be positive JSON numbers or null: $value"
    }
    if ($value -ne "null" -and [double]$value -le 0.0) {
        throw "Current values must be greater than zero: $value"
    }
}

$env:ARMGCC_DIR = $ToolchainRoot
$env:PATH = "$(Join-Path $InstallRoot '.venv\Scripts');$(Join-Path $ToolchainRoot 'bin');$env:PATH"
$arguments = @(
    "build", "-b", "evkmimxrt595", "-d", $build, $source,
    "--toolchain", "armgcc", "--config", "flash_release", "-Dcore_id=cm33",
    "-DPython3_EXECUTABLE=$python", "-DOPENREF_FIRMWARE_COMMIT=$commit",
    "-DOPENREF_BOARD_REVISION=$BoardRevision",
    "-DOPENREF_CURRENT_MEASUREMENT=$CurrentMeasurement",
    "-DOPENREF_IDLE_CURRENT_MA=$IdleCurrentMa",
    "-DOPENREF_ONE_TALKER_CURRENT_MA=$OneTalkerCurrentMa",
    "-DOPENREF_SIX_TALKER_CURRENT_MA=$SixTalkerCurrentMa"
)
if ($Pristine) { $arguments += @("-p", "always") }

Push-Location $sdk
try {
    & $west @arguments
    if ($LASTEXITCODE -ne 0) { throw "RT595 benchmark build failed: $LASTEXITCODE" }
    $elf = Join-Path $build "openref_rt595_benchmark_cm33.elf"
    if (-not (Test-Path -LiteralPath $elf)) { throw "Missing benchmark ELF: $elf" }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $elf).Hash.ToLowerInvariant()
    Write-Host "OpenRef RT595 paced benchmark ELF: $elf"
    Write-Host "SHA-256: $hash"
    Write-Host "BUILD-ONLY: flashing and UART capture are required for timing evidence."
}
finally { Pop-Location }
