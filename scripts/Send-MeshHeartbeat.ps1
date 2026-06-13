<#
.SYNOPSIS
  Report this machine into the Lantern OS mesh hub.

.DESCRIPTION
  Posts a heartbeat to the hub's /api/mesh/heartbeat endpoint. Run it manually,
  or schedule it (Task Scheduler, every few minutes) so the fleet view shows
  your machine as online while you're contributing.

  Your member id must already exist in config/mesh-members.json — joining the
  mesh is a PR that adds you there.

.EXAMPLE
  powershell -File scripts/Send-MeshHeartbeat.ps1 -Member courtney

.EXAMPLE
  powershell -File scripts/Send-MeshHeartbeat.ps1 -Member mookman11 -Hub https://your-railway-app.up.railway.app -Note "running refactor agents"
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$Member,

  # Hub base URL. Local hub by default; use the Railway URL to report into the shared cloud hub.
  [string]$Hub = "http://127.0.0.1:4177",

  # What this machine is running, e.g. "claude-code","ollama"
  [string[]]$Agents = @(),

  # Provider keys this node contributes locally, e.g. "anthropic","gemini"
  [string[]]$Providers = @(),

  [string]$Note = ""
)

$payload = @{
  member    = $Member
  machine   = $env:COMPUTERNAME
  agents    = $Agents
  providers = $Providers
  note      = $Note
} | ConvertTo-Json

try {
  $resp = Invoke-RestMethod -Method Post -Uri "$Hub/api/mesh/heartbeat" -ContentType "application/json" -Body $payload -TimeoutSec 10
  if ($resp.ok) {
    Write-Host "Heartbeat accepted for '$Member' from $env:COMPUTERNAME" -ForegroundColor Green
    Write-Host ("Mesh: {0}/{1} members online" -f $resp.mesh.onlineCount, $resp.mesh.memberCount)
  } else {
    Write-Host "Heartbeat rejected: $($resp.error)" -ForegroundColor Yellow
  }
} catch {
  Write-Host "Could not reach hub at $Hub — $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
