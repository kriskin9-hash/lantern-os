param(
    [string]$OutputPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "data\mining-lab\hardware-inventory-latest.csv"),
    [decimal]$PowerUsdPerKwh = 0.16,
    [switch]$IncludeManualAsicTemplate
)

$ErrorActionPreference = "Stop"

function Convert-BytesToGb {
    param([Nullable[uint64]]$Bytes)
    if (-not $Bytes) { return 0 }
    return [math]::Round(([double]$Bytes / 1GB), 2)
}

$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$cpus = @(Get-CimInstance Win32_Processor)
$gpus = @(Get-CimInstance Win32_VideoController)
$ram = @(Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum)
$ramGb = [math]::Round(($ram.Sum / 1GB), 2)

$nvidiaRows = @{}
try {
    $nvidia = @(nvidia-smi --query-gpu=name,power.draw,power.limit,temperature.gpu,memory.total,driver_version --format=csv,noheader,nounits 2>$null)
    foreach ($line in $nvidia) {
        $parts = @($line -split "," | ForEach-Object { $_.Trim() })
        if ($parts.Count -ge 6) {
            $nvidiaRows[$parts[0]] = [pscustomobject]@{
                power = $parts[1]
                limit = $parts[2]
                temp = $parts[3]
                mem = $parts[4]
                driver = $parts[5]
            }
        }
    }
}
catch {
    # nvidia-smi is optional. Keep inventory read-only and continue.
}

$rows = @()
foreach ($cpu in $cpus) {
    $rows += [pscustomobject]@{
        host_name = $computer.Name
        os = "$($os.Caption) $($os.Version)"
        cpu_name = $cpu.Name
        cpu_cores = $cpu.NumberOfCores
        cpu_threads = $cpu.NumberOfLogicalProcessors
        ram_gb = $ramGb
        gpu_name = ""
        gpu_vram_gb = ""
        gpu_driver = ""
        nvidia_smi_power_draw_w = ""
        asic_model = ""
        asic_algorithm = ""
        asic_hashrate = ""
        asic_power_w = ""
        power_usd_per_kwh = $PowerUsdPerKwh
        heat_noise_limit = "operator-review"
        run_24x7 = "no"
        wallet_ready = "no"
        off_ramp_ready = "no"
        notes = "CPU inventory row; benchmark before mining decision"
    }
}

foreach ($gpu in $gpus) {
    $vram = Convert-BytesToGb $gpu.AdapterRAM
    $match = $null
    foreach ($key in $nvidiaRows.Keys) {
        if ($gpu.Name -like "*$key*" -or $key -like "*$($gpu.Name)*") {
            $match = $nvidiaRows[$key]
            break
        }
    }
    $rows += [pscustomobject]@{
        host_name = $computer.Name
        os = "$($os.Caption) $($os.Version)"
        cpu_name = ""
        cpu_cores = ""
        cpu_threads = ""
        ram_gb = $ramGb
        gpu_name = $gpu.Name
        gpu_vram_gb = $vram
        gpu_driver = if ($match) { $match.driver } else { $gpu.DriverVersion }
        nvidia_smi_power_draw_w = if ($match) { $match.power } else { "" }
        asic_model = ""
        asic_algorithm = ""
        asic_hashrate = ""
        asic_power_w = ""
        power_usd_per_kwh = $PowerUsdPerKwh
        heat_noise_limit = "operator-review"
        run_24x7 = "no"
        wallet_ready = "no"
        off_ramp_ready = "no"
        notes = "GPU inventory row; measure wall power and thermals before mining decision"
    }
}

if ($IncludeManualAsicTemplate) {
    $rows += [pscustomobject]@{
        host_name = $computer.Name
        os = "$($os.Caption) $($os.Version)"
        cpu_name = ""
        cpu_cores = ""
        cpu_threads = ""
        ram_gb = $ramGb
        gpu_name = ""
        gpu_vram_gb = ""
        gpu_driver = ""
        nvidia_smi_power_draw_w = ""
        asic_model = "manual-entry"
        asic_algorithm = "Scrypt|SHA-256|kHeavyHash|other"
        asic_hashrate = "0"
        asic_power_w = "0"
        power_usd_per_kwh = $PowerUsdPerKwh
        heat_noise_limit = "garage-only"
        run_24x7 = "no"
        wallet_ready = "no"
        off_ramp_ready = "no"
        notes = "Manual ASIC row; fill from nameplate, vendor UI, and wall meter"
    }
}

if ($rows.Count -eq 0) {
    throw "No hardware inventory rows were produced."
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
$rows | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
Write-Output $OutputPath
