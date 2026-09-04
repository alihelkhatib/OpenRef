[CmdletBinding()]
param(
    [string]$InstallRoot,
    [string]$ToolchainRoot,
    [switch]$SkipSdkUpdate,
    [switch]$BuildSmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$sdkRevision = "v26.06.00-LTS"
$sdkCommit = "b01ab9032249f0d10cf6791ee4d7de45dfb19166"
$board = "evkmimxrt595"
$toolchainVersion = "14.3.rel1"
$toolchainArchive = "arm-gnu-toolchain-14.3.rel1-mingw-w64-x86_64-arm-none-eabi.zip"
$toolchainSha256 = "864c0c8815857d68a1bbba2e5e2782255bb922845c71c97636004a3d74f60986"
$toolchainUrl = "https://armkeil.blob.core.windows.net/developer/Files/downloads/gnu/14.3.rel1/binrel/$toolchainArchive"

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $PSScriptRoot "..\artifacts\local\rt595-sdk"
}
if ([string]::IsNullOrWhiteSpace($ToolchainRoot)) {
    $ToolchainRoot = Join-Path $PSScriptRoot "..\artifacts\local\rt595-toolchain"
}
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$ToolchainRoot = [IO.Path]::GetFullPath($ToolchainRoot)
$workspace = Join-Path $InstallRoot "workspace"
$sdkRoot = Join-Path $workspace "mcuxsdk"
$venv = Join-Path $InstallRoot ".venv"
$python = Join-Path $venv "Scripts\python.exe"
$west = Join-Path $venv "Scripts\west.exe"
$archive = Join-Path $ToolchainRoot $toolchainArchive
$gcc = Join-Path $ToolchainRoot "bin\arm-none-eabi-gcc.exe"

New-Item -ItemType Directory -Force -Path $InstallRoot, $ToolchainRoot | Out-Null

if (-not (Test-Path -LiteralPath $python)) {
    & python -m venv $venv
}
& $python -m pip install --disable-pip-version-check "west==1.5.0" "cmake==3.31.6" `
    "ninja==1.13.0" "jsonschema==4.25.1"
if ($LASTEXITCODE -ne 0) {
    throw "Pinned RT595 Python tool installation failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $gcc)) {
    if (-not (Test-Path -LiteralPath $archive)) {
        Invoke-WebRequest -UseBasicParsing $toolchainUrl -OutFile $archive
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    if ($actualHash -ne $toolchainSha256) {
        throw "Arm GNU archive SHA-256 mismatch: expected $toolchainSha256, got $actualHash"
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $ToolchainRoot -Force
}

$actualGccVersion = (& $gcc -dumpfullversion).Trim()
if ($actualGccVersion -ne "14.3.1") {
    throw "Unexpected Arm GCC version: $actualGccVersion"
}

if (-not (Test-Path -LiteralPath (Join-Path $workspace ".west"))) {
    & $west init -m "https://github.com/nxp-mcuxpresso/mcuxsdk-manifests.git" --mr $sdkRevision $workspace
}
$manifestCommit = (& git -C (Join-Path $workspace "manifests") rev-parse HEAD).Trim()
if ($manifestCommit -ne $sdkCommit) {
    throw "Unexpected MCUXpresso manifest commit: expected $sdkCommit, got $manifestCommit"
}

if (-not $SkipSdkUpdate) {
    Push-Location $workspace
    try {
        & $west update_board --set board $board
    }
    finally {
        Pop-Location
    }
}

$env:ARMGCC_DIR = $ToolchainRoot
$env:PATH = "$(Join-Path $venv 'Scripts');$(Join-Path $ToolchainRoot 'bin');$env:PATH"

if ($BuildSmokeTest) {
    Push-Location $sdkRoot
    try {
        & $west build -p always examples/demo_apps/hello_world `
            --toolchain armgcc --config debug -b $board `
            -Dcore_id=cm33 -DPython3_EXECUTABLE=$python
    }
    finally {
        Pop-Location
    }
}

Write-Host "MCUXpresso SDK: $sdkRevision ($sdkCommit)"
Write-Host "Workspace:       $workspace"
Write-Host "Arm GCC:         $toolchainVersion / GCC $actualGccVersion"
Write-Host "ARMGCC_DIR:      $ToolchainRoot"
Write-Host "Activate tools:  $venv\Scripts\Activate.ps1"
