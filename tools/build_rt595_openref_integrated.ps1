[CmdletBinding()] param([string]$InstallRoot,[string]$ToolchainRoot,[Parameter(Mandatory=$true)][ValidateRange(1,6)][int]$LocalSourceId,[Parameter(Mandatory=$true)][ValidateSet('A','B')][string]$CurrentSlot,[Parameter(Mandatory=$true)][ValidateRange(1,4294967295)][uint32]$ImageVersion,[string]$TrustAnchorHeader,[switch]$Pristine)
$ErrorActionPreference="Stop"; Set-StrictMode -Version Latest
if(!$InstallRoot){$InstallRoot=Join-Path $PSScriptRoot "..\artifacts\local\rt595-sdk"}
if(!$ToolchainRoot){$ToolchainRoot=Join-Path $PSScriptRoot "..\artifacts\local\rt595-toolchain"}
$InstallRoot=[IO.Path]::GetFullPath($InstallRoot);$ToolchainRoot=[IO.Path]::GetFullPath($ToolchainRoot);$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sdk=Join-Path $InstallRoot "workspace\mcuxsdk";$west=Join-Path $InstallRoot ".venv\Scripts\west.exe";$python=Join-Path $InstallRoot ".venv\Scripts\python.exe";$build=Join-Path $InstallRoot "build\openref_rt595_integrated";$source=Join-Path $repo "firmware\audio_processor\targets\mimxrt595_evk\integrated_target"
foreach($p in @($sdk,$west,$python,(Join-Path $ToolchainRoot "bin\arm-none-eabi-gcc.exe"))){if(!(Test-Path -LiteralPath $p)){throw "Missing dependency: $p"}}
$env:ARMGCC_DIR=$ToolchainRoot;$env:PATH="$(Join-Path $InstallRoot '.venv\Scripts');$(Join-Path $ToolchainRoot 'bin');$env:PATH"
$slotNumber=if($CurrentSlot -eq 'A'){0}else{1}
$a=@("build","-b","evkmimxrt595","-d",$build,$source,"--toolchain","armgcc","--config","flash_release","-Dcore_id=cm33","-DPython3_EXECUTABLE=$python","-DOPENREF_LOCAL_SOURCE_ID=$LocalSourceId","-DOPENREF_CURRENT_SLOT=$slotNumber","-DOPENREF_IMAGE_VERSION=$ImageVersion");if($Pristine){$a+=@("-p","always")}
if($TrustAnchorHeader){$TrustAnchorHeader=[IO.Path]::GetFullPath($TrustAnchorHeader);if(!(Test-Path -LiteralPath $TrustAnchorHeader)){throw "Missing trust anchor header: $TrustAnchorHeader"};$a+="-DOPENREF_TRUST_ANCHOR_HEADER=$TrustAnchorHeader"}
Push-Location $sdk;try{& $west @a;if($LASTEXITCODE){throw "Integrated build failed: $LASTEXITCODE"}}finally{Pop-Location}
$layout=Join-Path $repo "firmware\audio_processor\targets\mimxrt595_evk\openref_rt595_flash_layout.json";$map=Join-Path $build "output.map";$validator=Join-Path $repo "tools\validate_rt595_flash_layout.py"
$linkedPartition=if($CurrentSlot -eq 'A'){'slot_a_image'}else{'slot_b_image'}
& $python $validator $layout --map $map --linked-partition $linkedPartition;if($LASTEXITCODE){throw "RT595 flash layout validation failed: $LASTEXITCODE"}
$elf=Join-Path $build "openref_rt595_integrated_cm33.elf";if(!(Test-Path $elf)){throw "Missing ELF: $elf"};$hash=(Get-FileHash -Algorithm SHA256 $elf).Hash.ToLowerInvariant();Write-Host "Integrated ELF: $elf";Write-Host "SHA-256: $hash";Write-Host "Local source ID: $LocalSourceId";Write-Host "Current slot: $CurrentSlot";Write-Host "Image version: $ImageVersion"
