$ErrorActionPreference = "Stop"

$url = "http://127.0.0.1:4177/"

Start-Process -FilePath $url
Write-Output $url
