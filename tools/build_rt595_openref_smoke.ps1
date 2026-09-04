[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$ToolchainRoot,
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
$workspace = Join-Path $InstallRoot "workspace"
$sdk = Join-Path $workspace "mcuxsdk"
$west = Join-Path $InstallRoot ".venv\Scripts\west.exe"
$python = Join-Path $InstallRoot ".venv\Scripts\python.exe"
$source = Join-Path $repoRoot "firmware\audio_processor\targets\mimxrt595_evk\smoke"
$build = Join-Path $InstallRoot "build\openref_rt595_smoke"

foreach ($required in @($west, $sdk, (Join-Path $ToolchainRoot "bin\arm-none-eabi-gcc.exe"))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing RT595 build dependency: $required. Run tools/setup_rt595_sdk.ps1 first."
    }
}

$env:ARMGCC_DIR = $ToolchainRoot
$env:PATH = "$(Join-Path $InstallRoot '.venv\Scripts');$(Join-Path $ToolchainRoot 'bin');$env:PATH"
$arguments = @(
    "build", "-b", "evkmimxrt595", "-d", $build, $source,
    "--toolchain", "armgcc", "--config", "flash_debug",
    "-Dcore_id=cm33", "-DPython3_EXECUTABLE=$python"
)
if ($Pristine) {
    $arguments += @("-p", "always")
}

Push-Location $sdk
try {
    & $west @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "RT595 OpenRef smoke build failed with exit code $LASTEXITCODE"
    }
    $elf = Join-Path $build "openref_rt595_smoke_cm33.elf"
    if (-not (Test-Path -LiteralPath $elf)) {
        throw "RT595 OpenRef smoke build did not produce $elf"
    }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $elf).Hash.ToLowerInvariant()
    Write-Host "OpenRef RT595 smoke ELF: $elf"
    Write-Host "SHA-256: $hash"
}
finally {
    Pop-Location
}
