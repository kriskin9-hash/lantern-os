# Start two independent Lantern Garage servers on Windows

Write-Host "🌙 Starting dual Lantern Garage servers..." -ForegroundColor Cyan
Write-Host ""

# Kill any existing servers on these ports
Write-Host "Cleaning up old processes..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Get-NetTCPConnection -LocalPort 4177 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'} | ForEach-Object {taskkill /PID $_.OwningProcess /F 2>$null}
Get-NetTCPConnection -LocalPort 4178 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'} | ForEach-Object {taskkill /PID $_.OwningProcess /F 2>$null}

Start-Sleep -Seconds 2

# Start main branch server (port 4177)
Write-Host "📍 Starting MAIN branch server on port 4177..." -ForegroundColor Green
$mainProcess = Start-Process powershell -ArgumentList @"
`$env:PORT=4177; cd 'C:\Users\alexp\OneDrive\Documents\GitHub\lantern-os\apps\lantern-garage'; npm start
"@ -PassThru

# Start dev/master branch server (port 4178)
Write-Host "📍 Starting DEV branch server on port 4178..." -ForegroundColor Green
$devProcess = Start-Process powershell -ArgumentList @"
`$env:PORT=4178; cd 'C:\Users\alexp\OneDrive\Documents\GitHub\lantern-os\apps\lantern-garage'; npm start
"@ -PassThru

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ Both servers starting in background..." -ForegroundColor Green
Write-Host "   🌙 Main (port 4177): http://127.0.0.1:4177" -ForegroundColor Cyan
Write-Host "   🌙 Dev  (port 4178): http://127.0.0.1:4178" -ForegroundColor Cyan
Write-Host ""
Write-Host "PIDs: Main=$($mainProcess.Id), Dev=$($devProcess.Id)" -ForegroundColor White
Write-Host ""
Write-Host "To stop servers: taskkill /PID $($mainProcess.Id) /F && taskkill /PID $($devProcess.Id) /F" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to exit this script (servers will continue running)" -ForegroundColor Yellow

# Wait for processes
$mainProcess.WaitForExit()
$devProcess.WaitForExit()
