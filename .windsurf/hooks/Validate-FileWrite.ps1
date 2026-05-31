param(
    [Parameter(ValueFromPipeline)]
    [string]$InputJson
)

$ErrorActionPreference = "Stop"

# Read JSON input from stdin
if (-not $InputJson) {
    $InputJson = [Console]::In.ReadToEnd()
}

$data = $InputJson | ConvertFrom-Json

# Initialize validation result
$result = @{
    valid = $true
    blocked = $false
    reasons = @()
} | ConvertTo-Json -Depth 10

# Check file path for dangerous locations
$filePath = if ($data.PSObject.Properties.Name -contains 'path') { $data.path } else { "" }

$dangerousPaths = @(
    'C:\Windows\System32',
    'C:\Windows\SysWOW64',
    '/boot',
    '/etc/fstab',
    '/etc/grub',
    'bcdedit',
    'bootloader'
)

foreach ($path in $dangerousPaths) {
    if ($filePath -like "*$path*") {
        $result = @{
            valid = $false
            blocked = $true
            reasons = @("Dangerous file path detected: $path")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 2  # Block the action
    }
}

# Check for system-critical file extensions
$dangerousExtensions = @('.sys', '.dll', '.exe', '.bat', '.cmd', '.ps1', '.sh', '.bin', '.img', '.iso')

$extension = [System.IO.Path]::GetExtension($filePath)
if ($dangerousExtensions -contains $extension) {
    # Allow writes within scripts/ and .windsurf/ directories
    $allowedDirs = @('scripts', '.windsurf', 'tests')
    $isAllowed = $false
    
    foreach ($dir in $allowedDirs) {
        if ($filePath -like "*$dir*") {
            $isAllowed = $true
            break
        }
    }
    
    if (-not $isAllowed) {
        $result = @{
            valid = $false
            blocked = $true
            reasons = @("System-critical file extension in non-allowed directory: $extension")
        } | ConvertTo-Json -Depth 10
        Write-Output $result
        exit 2  # Block the action
    }
}

Write-Output $result
exit 0
