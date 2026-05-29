# Git Automation System Setup Guide

## Overview

Automated system for git operations, polling, and HFF convergence for Lantern OS development.

## Components Created

1. **Git Auto-Deploy** (`Invoke-GitAutoDeploy.ps1`)
   - Automated git pull/push operations
   - Stash/pull/unstash workflow
   - Deployment trigger on changes
   - Polling interval configuration

2. **Auto-Poll Scheduler** (`Invoke-AutoPoll.ps1`)
   - Multi-repository change detection
   - Configurable polling intervals
   - Action triggering on changes
   - State persistence

3. **HFF Convergence** (`Invoke-HFFConvergence.ps1`)
   - Human Flourishing Frameworks integration
   - Artifact promotion automation
   - Convergence report generation
   - Dirty state handling

4. **Automation Orchestrator** (`Invoke-AutomationOrchestrator.ps1`)
   - Master coordination script
   - Component priority management
   - Health monitoring
   - Result tracking and notifications

5. **Setup Script** (`Start-GitAutomation.ps1`)
   - One-command initialization
   - Dependency verification
   - Directory structure creation

## Quick Start

### Initial Setup (One-time)

```powershell
.\scripts\Start-GitAutomation.ps1
```

This will:
- Create required directories
- Verify all scripts
- Check configuration files
- Run one-time validation

### Run Single Cycle

```powershell
.\scripts\Invoke-AutomationOrchestrator.ps1 -RunOnce
```

### Run Continuous Automation

```powershell
.\scripts\Invoke-AutomationOrchestrator.ps1
```

### Test with Dry Run

```powershell
.\scripts\Invoke-AutomationOrchestrator.ps1 -RunOnce -DryRun
```

## Configuration

### Orchestrator Config
Location: `data/automation/orchestrator-config.json`

```json
{
  "components": [
    {
      "name": "git-auto-deploy",
      "script": "D:\\tmp\\lantern-os\\scripts\\Invoke-GitAutoDeploy.ps1",
      "enabled": true,
      "priority": 1,
      "intervalMinutes": 5
    }
  ]
}
```

### Poll Config
Location: `data/automation/poll-config.json`

```json
{
  "sources": [
    {
      "name": "lantern-os-repo",
      "path": "D:\\tmp\\lantern-os",
      "intervalMinutes": 5,
      "enabled": true
    }
  ],
  "actions": [
    {
      "name": "convergence-loop",
      "script": "D:\\tmp\\lantern-os\\scripts\\Invoke-LanternConvergenceLoop.ps1",
      "triggerOnChanges": true
    }
  ]
}
```

## Component Details

### Git Auto-Deploy
- **Purpose**: Handle git sync and deployment
- **Interval**: Every 5 minutes (configurable)
- **Triggers**: Changes detected in monitored repos
- **Safety**: Uses stash to preserve local changes

### Auto-Poll Scheduler
- **Purpose**: Monitor multiple repositories for changes
- **Monitored Repos**: 
  - Lantern OS (D:\tmp\lantern-os)
  - HFF Scan (C:\tmp\human-flourishing-frameworks-scan)
  - Orchestrator (C:\Users\alexp\Documents\gm-agent-orchestrator)
- **Triggers**: Actions based on change detection

### HFF Convergence
- **Purpose**: Sync with Human Flourishing Frameworks
- **Actions**:
  - Detect changes in HFF repo
  - Promote artifacts to Lantern OS
  - Generate convergence reports
  - Trigger convergence loops
- **Safety**: Dry-run mode available for testing

### Automation Orchestrator
- **Purpose**: Master coordinator for all automation
- **Features**:
  - Priority-based component execution
  - Health monitoring (network, disk, git status)
  - Result tracking and persistence
  - Error handling and recovery
- **Health Checks**: Every 30 minutes

## Usage Scenarios

### Continuous Development Setup
```powershell
# Start continuous automation in background
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File D:\tmp\lantern-os\scripts\Invoke-AutomationOrchestrator.ps1" -WindowStyle Hidden
```

### Manual Sync Before Push
```powershell
# Run single cycle to sync all repos
.\scripts\Invoke-AutomationOrchestrator.ps1 -RunOnce
```

### Test Configuration Changes
```powershell
# Test without executing actual scripts
.\scripts\Invoke-AutomationOrchestrator.ps1 -RunOnce -DryRun
```

### HFF Convergence Check
```powershell
# Check HFF repo for changes and sync if needed
.\scripts\Invoke-HFFConvergence.ps1 -DryRun
```

## Monitoring

### Log Files
- Orchestrator log: `data/automation/orchestrator.log`
- Health status: `data/automation/health-status.json`
- Results: `data/automation/orchestrator-results.json`
- Poll results: `data/automation/poll-results.json`

### Health Check Indicators
- Git working directory cleanliness
- Network connectivity to GitHub
- Disk space availability
- Component success/failure status

### Troubleshooting

#### Component Disabled
- Check configuration file for `enabled: true`
- Verify script paths are correct
- Check component dependencies

#### Git Sync Failures
- Check network connectivity
- Verify repository access permissions
- Review git authentication

#### HFF Convergence Issues
- Verify HFF repo path exists
- Check git remote configuration
- Review convergence report for details

## Advanced Configuration

### Custom Poll Intervals
Edit `data/automation/poll-config.json`:
```json
{
  "sources": [
    {
      "intervalMinutes": 15  // Slower polling
    }
  ]
}
```

### Disable Specific Components
Edit `data/automation/orchestrator-config.json`:
```json
{
  "components": [
    {
      "enabled": false  // Disable this component
    }
  ]
}
```

### Add Custom Components
1. Create your PowerShell script
2. Add to orchestrator config:
```json
{
  "components": [
    {
      "name": "custom-component",
      "script": "path\\to\\your\\script.ps1",
      "enabled": true,
      "priority": 5
    }
  ]
}
```

## Security Considerations

- Scripts do not auto-push by default (configurable)
- Requires manual approval for destructive operations
- Dry-run mode available for testing
- Git stash preserves local changes
- No automated credential handling

## Integration with Existing Workflow

### Before Committing
```powershell
.\scripts\Invoke-AutomationOrchestrator.ps1 -RunOnce
git add .
git commit -m "changes after automation sync"
```

### Before Deployment
```powershell
.\scripts\Invoke-GitAutoDeploy.ps1 -Continuous
# Monitor logs to ensure deployment readiness
```

### Regular Development
- Let orchestrator run in background
- Check logs periodically
- Review convergence reports
- Handle any manual actions needed

## Maintenance

### Weekly Tasks
- Review orchestrator logs
- Check health status trends
- Update configurations as needed
- Archive old result files

### Monthly Tasks
- Review and optimize intervals
- Check disk space usage
- Update script versions
- Review component priorities

## Troubleshooting Commands

```powershell
# Check current status
Get-Content data\automation\orchestrator-results.json | ConvertFrom-Json

# View recent logs
Get-Content data\automation\orchestrator.log -Tail 20

# Test individual component
.\scripts\Invoke-GitAutoDeploy.ps1 -RepoPath "D:\tmp\lantern-os" -RunOnce

# Check git status
git status --porcelain

# View convergence reports
Get-ChildItem manifests\hff-convergence-report-*.md | Select-Object -Last 1 | Get-Content
```

## Support

For issues with:
- **Script execution**: Check log files for error details
- **Git operations**: Verify git configuration and credentials
- **HFF convergence**: Check HFF repo accessibility and permissions
- **Configuration**: Validate JSON syntax and file paths