param(
    [string]$ProjectRoot = "$env:USERPROFILE\SimplicityStudio\v6_workspace\rail_soc_railtest",
    [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$InstallAppShim,
    [switch]$EnableAutoTx,
    [switch]$EnableAutoRx,
    [switch]$EnableAutoRole,
    [switch]$EnableNetwork,
    [switch]$EnableSecureNetwork,
    [switch]$EnablePersistentEpoch,
    [switch]$EnablePersistentSecurityCounters,
    [switch]$EnablePersistentConfig,
    [switch]$EnablePersistentBootState,
    [switch]$EnablePersistentDeviceRecord,
    [switch]$EnableHardwareWatchdog,
    [uint32]$WatchdogTestHangAfterFeeds = 0,
    [string]$WatchdogHangMarker = "",
    [string]$WatchdogBootMarker = "",
    [ValidateRange(1, 6)]
    [int]$NetworkNodeId = 1,
    [switch]$EnableLc3Benchmark,
    [string]$Lc3Root = "",
    [switch]$EnableGpioMarkers,
    [string]$BuildMarker = "",
    [string]$QueueMarker = "",
    [string]$StartMarker = "",
    [string]$DoneMarker = ""
)

$ErrorActionPreference = "Stop"

function Convert-OpenRefGpioMarker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Marker
    )

    $normalized = $Marker.Trim().ToUpperInvariant()
    if ($normalized -notmatch "^P?([A-Z])(\d{1,2})$") {
        throw "Invalid GPIO marker '$Marker'. Use labels like B0, PB3, or A5."
    }

    $pin = [int]$Matches[2]
    if ($pin -lt 0 -or $pin -gt 15) {
        throw "Invalid GPIO marker '$Marker'. Pin must be in the range 0-15."
    }

    return @{
        Port = $Matches[1]
        Pin = $pin
    }
}

function Add-OpenRefGpioMarkerDefinitions {
    param(
        [string[]]$Definitions,
        [string]$Label,
        [string]$Marker
    )

    if ([string]::IsNullOrWhiteSpace($Marker)) {
        return $Definitions
    }

    $gpio = Convert-OpenRefGpioMarker -Marker $Marker
    $Definitions += "OPENREF_GPIO_$($Label)_PORT=gpioPort$($gpio.Port)"
    $Definitions += "OPENREF_GPIO_$($Label)_PIN=$($gpio.Pin)"
    return $Definitions
}

$projectRootPath = Resolve-Path $ProjectRoot
$repoRootPath = Resolve-Path $RepoRoot
$overlayRoot = Join-Path $projectRootPath "openref"
$overlayCommon = Join-Path $overlayRoot "common"
$overlayFg23 = Join-Path $overlayRoot "fg23"
$cmakeOverlay = Join-Path $projectRootPath "cmake_gcc\rail_soc_railtest_project.cmake"

New-Item -ItemType Directory -Force -Path $overlayCommon | Out-Null
New-Item -ItemType Directory -Force -Path $overlayFg23 | Out-Null

Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_proto0_packet.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_proto0_packet.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_radio.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_network.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_network.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_network_packet.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_network_packet.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_security.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_security.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_boot_counter.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_boot_counter.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_radio_session.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_radio_session.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_startup.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_startup.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_network_packet.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_network_packet.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_transport.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\common\openref_secure_transport.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_config_store.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_config_store.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_packet_pair.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_packet_pair.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_app.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_app.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_network_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_network_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_lc3_benchmark.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_lc3_benchmark.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_security_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_security_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_boot_counter_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_boot_counter_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_network_epoch_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_network_epoch_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_security_counters_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_security_counters_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_config_store_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_config_store_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_boot_policy.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_boot_policy.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_boot_state_store.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_boot_state_store.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_device_lifecycle.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_device_lifecycle.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_device_record_store.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_device_record_store.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_watchdog_gate.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_watchdog_gate.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_watchdog_driver.h") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\system\common\openref_watchdog_driver.c") -Destination $overlayCommon
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_boot_state_store_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_boot_state_store_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_watchdog_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_watchdog_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_reset_cause_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_reset_cause_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_device_record_store_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_device_record_store_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_radio_session_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_radio_session_fg23.c") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_secure_startup_fg23.h") -Destination $overlayFg23
Copy-Item -Force -Path (Join-Path $repoRootPath "firmware\prototype0\fg23\src\openref_secure_startup_fg23.c") -Destination $overlayFg23

$cmake = @"
# OpenRef local overlay. Generated by tools/install_openref_fg23_overlay.ps1.
# This file is included by cmake_gcc/CMakeLists.txt when present.

target_sources(rail_soc_railtest PRIVATE
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_proto0_packet.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_network.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_network_packet.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_security.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_boot_counter.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_radio_session.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_secure_startup.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_secure_network_packet.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_secure_transport.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_config_store.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_boot_policy.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_boot_state_store.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_device_lifecycle.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_device_record_store.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_watchdog_gate.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common/openref_watchdog_driver.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_packet_pair.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_app.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_network_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_lc3_benchmark.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_security_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_boot_counter_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_network_epoch_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_security_counters_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_config_store_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_boot_state_store_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_watchdog_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_reset_cause_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_device_record_store_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_radio_session_fg23.c
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23/openref_secure_startup_fg23.c
)

target_include_directories(rail_soc_railtest PRIVATE
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23
)

target_include_directories(slc PRIVATE
    `${CMAKE_CURRENT_LIST_DIR}/../openref/common
    `${CMAKE_CURRENT_LIST_DIR}/../openref/fg23
)
"@

if ($EnableAutoTx) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_AUTOTX=1)
"@
}

if ($EnableAutoRx) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_AUTORX=1)
"@
}

if ($EnableAutoRole) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_AUTOROLE=1)
"@
}

if ($EnableNetwork) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_NETWORK=1 OPENREF_APP_NETWORK_NODE_ID=$NetworkNodeId)
"@
}

if ($EnableSecureNetwork) {
    if (-not $EnableNetwork) {
        throw "-EnableSecureNetwork requires -EnableNetwork."
    }
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE
    OPENREF_APP_NETWORK_SECURITY=1
    OPENREF_APP_SECURITY=1
    OPENREF_APP_SECURITY_NVM3=1
)
"@
}

if ($EnablePersistentEpoch) {
    if (-not $EnableNetwork) {
        throw "-EnablePersistentEpoch requires -EnableNetwork."
    }
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_NETWORK_EPOCH_NVM3=1)
"@
}

if ($EnablePersistentSecurityCounters) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_SECURITY_COUNTERS_NVM3=1)
"@
}

if ($EnablePersistentConfig) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_CONFIG_NVM3=1)
"@
}

if ($EnablePersistentBootState) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_BOOT_STATE_NVM3=1)
"@
}

if ($EnablePersistentDeviceRecord) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_DEVICE_RECORD_NVM3=1)
"@
}

if ($EnableHardwareWatchdog) {
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE
    OPENREF_APP_WATCHDOG_FG23=1
    OPENREF_APP_RESET_CAUSE_FG23=1
)
"@
}

if ($WatchdogTestHangAfterFeeds -ne 0) {
    if (-not $EnableHardwareWatchdog) {
        throw "-WatchdogTestHangAfterFeeds requires -EnableHardwareWatchdog."
    }
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE OPENREF_APP_WATCHDOG_TEST_HANG_AFTER_FEEDS=$WatchdogTestHangAfterFeeds)
"@
}

if (-not [string]::IsNullOrWhiteSpace($WatchdogHangMarker) -or
    -not [string]::IsNullOrWhiteSpace($WatchdogBootMarker)) {
    if (-not $EnableHardwareWatchdog) {
        throw "Watchdog markers require -EnableHardwareWatchdog."
    }
    $watchdogMarkerDefinitions = @()
    $watchdogMarkerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $watchdogMarkerDefinitions -Label "WATCHDOG_HANG" -Marker $WatchdogHangMarker
    $watchdogMarkerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $watchdogMarkerDefinitions -Label "WATCHDOG_BOOT" -Marker $WatchdogBootMarker
    $watchdogMarkerDefinitionText = $watchdogMarkerDefinitions -join " "
    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE $watchdogMarkerDefinitionText)
"@
}

if ($EnableLc3Benchmark) {
    if ([string]::IsNullOrWhiteSpace($Lc3Root)) {
        throw "-EnableLc3Benchmark requires -Lc3Root pointing to google/liblc3."
    }
    $lc3RootPath = Resolve-Path $Lc3Root
    $lc3Overlay = Join-Path $overlayRoot "lc3"
    New-Item -ItemType Directory -Force -Path (Join-Path $lc3Overlay "include") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $lc3Overlay "src") | Out-Null
    Copy-Item -Force -Path (Join-Path $lc3RootPath "include\*.h") -Destination (Join-Path $lc3Overlay "include")
    Copy-Item -Force -Path (Join-Path $lc3RootPath "src\*.h") -Destination (Join-Path $lc3Overlay "src")
    Copy-Item -Force -Path (Join-Path $lc3RootPath "src\*.c") -Destination (Join-Path $lc3Overlay "src")
    Copy-Item -Force -Path (Join-Path $lc3RootPath "LICENSE") -Destination $lc3Overlay

    $cmake += @"

file(GLOB OPENREF_LC3_SOURCES CONFIGURE_DEPENDS
    `${CMAKE_CURRENT_LIST_DIR}/../openref/lc3/src/*.c
)
target_sources(rail_soc_railtest PRIVATE `${OPENREF_LC3_SOURCES})
target_include_directories(rail_soc_railtest PRIVATE
    `${CMAKE_CURRENT_LIST_DIR}/../openref/lc3/include
    `${CMAKE_CURRENT_LIST_DIR}/../openref/lc3/src
)
target_compile_definitions(rail_soc_railtest PRIVATE
    OPENREF_APP_LC3_BENCHMARK=1 LC3_PLUS=0 LC3_PLUS_HR=0
)
target_compile_definitions(slc PRIVATE SL_STACK_SIZE=8192)
target_compile_options(rail_soc_railtest PRIVATE -ffast-math)
target_link_libraries(rail_soc_railtest PRIVATE m)
"@
}

$gpioMarkersRequested = $EnableGpioMarkers -or
    -not [string]::IsNullOrWhiteSpace($BuildMarker) -or
    -not [string]::IsNullOrWhiteSpace($QueueMarker) -or
    -not [string]::IsNullOrWhiteSpace($StartMarker) -or
    -not [string]::IsNullOrWhiteSpace($DoneMarker)

if ($gpioMarkersRequested) {
    if (-not $EnableAutoRole) {
        throw "GPIO markers require -EnableAutoRole because marker hooks are compiled only for the AutoRole runtime."
    }
    if ([string]::IsNullOrWhiteSpace($BuildMarker) -and
        [string]::IsNullOrWhiteSpace($QueueMarker) -and
        [string]::IsNullOrWhiteSpace($StartMarker) -and
        [string]::IsNullOrWhiteSpace($DoneMarker)) {
        throw "GPIO markers were requested, but no marker pins were supplied. Add at least one of -BuildMarker, -QueueMarker, -StartMarker, or -DoneMarker."
    }

    $markerDefinitions = @("OPENREF_APP_GPIO_MARKERS=1")
    $markerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $markerDefinitions -Label "BUILD" -Marker $BuildMarker
    $markerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $markerDefinitions -Label "QUEUE" -Marker $QueueMarker
    $markerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $markerDefinitions -Label "START" -Marker $StartMarker
    $markerDefinitions = Add-OpenRefGpioMarkerDefinitions -Definitions $markerDefinitions -Label "DONE" -Marker $DoneMarker
    $markerDefinitionText = $markerDefinitions -join " "

    $cmake += @"

target_compile_definitions(rail_soc_railtest PRIVATE $markerDefinitionText)
"@
}

Set-Content -Path $cmakeOverlay -Value $cmake -Encoding ASCII

if ($InstallAppShim) {
    $appFile = Join-Path $projectRootPath "app.c"
    $backupDir = Join-Path $projectRootPath ".openref-backup"
    $backupFile = Join-Path $backupDir "app.c"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    if (-not (Test-Path $backupFile)) {
        Copy-Item -Force -Path $appFile -Destination $backupFile
    }

    $appShim = @"
#include "app.h"
#include "openref_app.h"

void app_init(void)
{
  openref_app_init();
}

void app_process_action(void)
{
  openref_app_process_action();
}
"@

    Set-Content -Path $appFile -Value $appShim -Encoding ASCII
    Write-Host "Installed OpenRef app shim:"
    Write-Host "  $appFile"
    Write-Host "  Backup: $backupFile"
}

Write-Host "Installed OpenRef overlay:"
Write-Host "  $overlayRoot"
Write-Host "  $cmakeOverlay"
