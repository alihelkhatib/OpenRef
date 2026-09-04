[CmdletBinding()] param(
  [string]$InstallRoot,
  [string]$ToolchainRoot,
  [Parameter(Mandatory=$true)][string]$TrustAnchorHeader,
  [switch]$Pristine)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
if(!$InstallRoot){$InstallRoot=Join-Path $PSScriptRoot "..\artifacts\local\rt595-sdk"}
if(!$ToolchainRoot){$ToolchainRoot=Join-Path $PSScriptRoot "..\artifacts\local\rt595-toolchain"}
$InstallRoot=[IO.Path]::GetFullPath($InstallRoot);$ToolchainRoot=[IO.Path]::GetFullPath($ToolchainRoot)
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."));$TrustAnchorHeader=[IO.Path]::GetFullPath($TrustAnchorHeader)
$sdk=Join-Path $InstallRoot "workspace\mcuxsdk";$west=Join-Path $InstallRoot ".venv\Scripts\west.exe";$python=Join-Path $InstallRoot ".venv\Scripts\python.exe"
$build=Join-Path $InstallRoot "build\openref_rt595_bootstrap";$source=Join-Path $repo "firmware\audio_processor\targets\mimxrt595_evk\bootstrap_target"
foreach($p in @($sdk,$west,$python,(Join-Path $ToolchainRoot "bin\arm-none-eabi-gcc.exe"),$TrustAnchorHeader)){if(!(Test-Path -LiteralPath $p)){throw "Missing dependency: $p"}}
if((Split-Path -Leaf $TrustAnchorHeader) -ne "openref_trust_anchor_generated.h"){throw "Trust anchor header must be named openref_trust_anchor_generated.h"}
$env:ARMGCC_DIR=$ToolchainRoot;$env:PATH="$(Join-Path $InstallRoot '.venv\Scripts');$(Join-Path $ToolchainRoot 'bin');$env:PATH"
$args=@("build","-b","evkmimxrt595","-d",$build,$source,"--toolchain","armgcc","--config","flash_release","-Dcore_id=cm33","-DPython3_EXECUTABLE=$python","-DOPENREF_TRUST_ANCHOR_HEADER=$TrustAnchorHeader")
if($Pristine){$args+=@("-p","always")}
Push-Location $sdk;try{& $west @args;if($LASTEXITCODE){throw "Bootstrap build failed: $LASTEXITCODE"}}finally{Pop-Location}
$layout=Join-Path $repo "firmware\audio_processor\targets\mimxrt595_evk\openref_rt595_flash_layout.json";$map=Join-Path $build "output.map"
& $python (Join-Path $repo "tools\validate_rt595_flash_layout.py") $layout --map $map
if($LASTEXITCODE){throw "Bootstrap flash layout validation failed: $LASTEXITCODE"}
$elf=Join-Path $build "openref_rt595_bootstrap_cm33.elf";if(!(Test-Path $elf)){throw "Missing ELF: $elf"}
$hash=(Get-FileHash -Algorithm SHA256 $elf).Hash.ToLowerInvariant();Write-Host "Bootstrap ELF: $elf";Write-Host "SHA-256: $hash"
