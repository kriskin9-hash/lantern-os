# Find corrupted JSON files with UTF-16 BOM or invalid encoding
Get-ChildItem -Path $PSScriptRoot\.. -Recurse -Filter "*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    $bytes = [System.IO.File]::ReadAllBytes($_.FullName) | Select-Object -First 2
    $issue = $null
    
    if ($bytes[0] -eq 0xff -and $bytes[1] -eq 0xfe) {
        $issue = "UTF-16 LE BOM"
    } elseif ($bytes[0] -eq 0xfe -and $bytes[1] -eq 0xff) {
        $issue = "UTF-16 BE BOM"
    } elseif ($bytes[0] -eq 0xef -and $bytes[1] -eq 0xbb) {
        $issue = "UTF-8 BOM (OK)"
    } elseif ($bytes[0] -eq 0xff) {
        $issue = "Corrupted/0xff byte"
    }
    
    if ($issue -and ($issue -ne "UTF-8 BOM (OK)")) {
        [PSCustomObject]@{
            File = $_.FullName
            Issue = $issue
            FirstBytes = "0x{0:X2} 0x{1:X2}" -f $bytes[0], $bytes[1]
        }
    }
} | Format-Table -AutoSize
