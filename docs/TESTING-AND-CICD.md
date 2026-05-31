# Lantern OS Testing and CI/CD

**Status:** Active testing infrastructure with browser automation, MCP validation, and CI/CD pipelines

---

## Simple Answer

Lantern OS has a comprehensive testing and CI/CD infrastructure including:
- **Browser E2E testing** with Playwright (Chromium, Firefox, WebKit)
- **Python pytest suite** for policy and data validation
- **PowerShell script tests** for core functionality
- **MCP connector validation** with safety boundaries
- **Convergence loop validation** for repo health
- **GitHub Actions CI/CD** workflows for automated testing

## What It Actually Does

### Browser Testing (Playwright)

Tests web surfaces across multiple browsers:
- Trade chat app (Kalshi integration UI)
- Garage app (payment bridge)
- Static surfaces (shareholder index, desktop, dashboard)

**Run locally:**
```powershell
cd tests
npm install
npx playwright install --with-deps
npx playwright test
```

**Run with PowerShell wrapper:**
```powershell
.\scripts\Test-BrowserAutomation.ps1 -Browser all
```

### Python Test Suite

Validates policies, data models, and integrations:
- Action pooling and CI policy
- Kalshi trading safety
- Baseline model validation
- MCP connector contracts
- Convergence loop validation

**Run:**
```bash
python -m pytest tests -q
```

### PowerShell Script Tests

Tests core PowerShell functionality:
- HotSwap VM receipt generation
- HouseThinker agent
- Solo mining skill

**Run:**
```powershell
.\scripts\Test-HotSwapVmReceipt.ps1
.\scripts\Test-HouseThinker.ps1
.\scripts\Test-SoloMiningSkill.ps1
```

### MCP Connector Validation

Validates MCP safety boundaries and tool discovery:
- Local endpoint verification (127.0.0.1:8787)
- Remote tunnel safety checks
- Tool descriptor validation
- Evidence class verification

**Run:**
```powershell
.\scripts\Test-LanternMcpConnector.ps1
```

**Run enhanced tests:**
```bash
python -m pytest tests/test_mcp_connector_enhanced.py -v
```

### Convergence Loop Validation

Validates repo health and required surfaces:
- Required file existence
- Documentation phrase validation
- ASI skill boundary checks
- Windsurf hooks configuration
- Source repo state inspection

**Run:**
```powershell
.\scripts\Invoke-LanternConvergenceLoop.ps1
```

### Full Automation Test Suite

Runs all tests in sequence:
```powershell
.\scripts\Invoke-LanternAutomationTestSuite.ps1 -TestCategory all
```

Categories: `all`, `python`, `powershell`, `mcp`, `convergence`, `trade-chat`

## CI/CD Workflows

### Static Surface CI (`.github/workflows/static-surface-ci.yml`)

Runs on push/PR to master:
- Repo surface validation
- Manifest anchors
- HTML link integrity
- Python tests
- CI parallel shape guard

### Browser Testing CI (`.github/workflows/browser-testing-ci.yml`)

Runs on push/PR to master:
- Playwright browser E2E tests
- Trade chat unit tests
- Screenshot/video capture on failure

### Orchestration Challenge CI (`.github/workflows/orchestration-challenge-ci.yml`)

Validates orchestration contracts:
- Workflow inventory
- MCP contract guard
- Action pool contract
- Science report contract
- Python tests

### MCP Tunnel Canary (`.github/workflows/mcp-tunnel-canary.yml`)

Manual workflow for testing remote MCP tunnels:
- Validates HTTPS requirement
- Blocks localhost/loopback
- Probes health and tool-discovery endpoints

## Evidence / Source Discipline

- All test results written to `manifests/validation/`
- Browser test reports stored as artifacts
- MCP validation JSON tracks connector state
- Convergence loop JSON tracks repo health
- Automation test suite JSON tracks overall test status

## Proven / Held / Local-only

**Proven:**
- Python pytest suite (24+ tests)
- Trade chat unit tests (14 tests)
- MCP connector validation
- Convergence loop validation

**Held:**
- Browser tests require local server setup for full coverage
- MCP tool enumeration held until local MCP server running
- Remote tunnel validation held until operator approval

**Local-only:**
- Playwright browser automation
- PowerShell script tests
- Local MCP endpoint testing

## Next Safe Action

1. Install browser testing dependencies:
```powershell
cd tests
npm install
npx playwright install --with-deps
```

2. Run full automation test suite:
```powershell
.\scripts\Invoke-LanternAutomationTestSuite.ps1 -TestCategory all
```

3. Run browser tests locally:
```powershell
.\scripts\Test-BrowserAutomation.ps1 -Browser chromium
```

4. Review test results in `manifests/validation/`

## Validation Path

```bash
# Run all Python tests
python -m pytest tests -q

# Run MCP connector tests
python -m pytest tests/test_mcp_connector_enhanced.py -v

# Run trade chat unit tests
cd apps/lantern-trade-chat
pytest tests -v

# Run browser tests
cd ../..
.\scripts\Test-BrowserAutomation.ps1 -Browser all

# Run full automation suite
.\scripts\Invoke-LanternAutomationTestSuite.ps1 -TestCategory all
```

## Appendices

### Test Coverage

- **Python tests:** 50+ test files covering:
  - Repository structure (20+ tests)
  - Skill validation (15+ tests)
  - Data validation (20+ tests)
  - Security and boundaries (20+ tests)
  - Documentation validation (25+ tests)
  - CI/CD workflow validation (25+ tests)
  - PowerShell scripts (20+ tests)
  - MCP connector (14 tests)
  - Integration tests (20+ tests)
  - Policy and data models (24+ existing tests)
- **PowerShell tests:** 3 core script tests + 20+ validation tests
- **Browser tests:** 5 Playwright test suites (trade chat, garage, static surfaces, desktop, dashboard)
- **MCP tests:** 14 enhanced validation tests
- **Convergence loop:** 20+ validation checks

### CI/CD Pipeline Status

- Static surface CI: ✅ Active
- Browser testing CI: ✅ Active
- Orchestration challenge CI: ✅ Active
- MCP tunnel canary: ✅ Active (manual)

### Test Result Locations

- `manifests/validation/AUTOMATION-TEST-LATEST.json` - Full automation suite results
- `manifests/validation/MCP-CONNECTOR-LATEST.json` - MCP connector validation
- `manifests/validation/CONVERGENCE-FLEET-LATEST.json` - Convergence fleet validation
- `tests/playwright-report/` - Playwright HTML report
- `tests/test-results/` - Playwright screenshots/videos (on failure)

### New Test Files Added

**Repository Structure Tests:**
- `tests/test_repository_structure.py` - Validates repo structure, required files, directories

**Skill Validation Tests:**
- `tests/test_skill_validation.py` - Validates skill structure, boundaries, documentation

**Data Validation Tests:**
- `tests/test_data_validation.py` - Validates JSON/JSONL files, data integrity

**Security and Boundary Tests:**
- `tests/test_security_boundaries.py` - Validates security boundaries, safety gates

**Documentation Validation Tests:**
- `tests/test_documentation_validation.py` - Validates documentation structure, completeness

**CI/CD Workflow Validation Tests:**
- `tests/test_cicd_validation.py` - Validates GitHub Actions workflows, CI/CD config

**PowerShell Script Tests:**
- `tests/test_powershell_scripts.py` - Validates PowerShell scripts, structure, safety

**Integration Tests:**
- `tests/test_integration.py` - Validates component integration, cross-component workflows

**Browser E2E Tests:**
- `tests/e2e/desktop-surfaces.spec.ts` - Desktop surface browser tests
- `tests/e2e/dashboard.spec.ts` - Dashboard browser tests
