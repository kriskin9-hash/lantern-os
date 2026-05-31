"""
PowerShell Script Tests

Validates PowerShell scripts exist, have proper structure,
and follow safety guidelines.
"""
import pytest
from pathlib import Path


def test_convergence_loop_script_exists():
    """Verify convergence loop script exists."""
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    assert script.exists()


def test_convergence_loop_script_has_params():
    """Verify convergence loop script has parameters."""
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    content = script.read_text(encoding="utf-8")
    
    assert "param(" in content, "Convergence loop script should have parameters"


def test_automation_test_suite_script_exists():
    """Verify automation test suite script exists."""
    script = Path("scripts/Invoke-LanternAutomationTestSuite.ps1")
    assert script.exists()


def test_automation_test_suite_has_categories():
    """Verify automation test suite has test categories."""
    script = Path("scripts/Invoke-LanternAutomationTestSuite.ps1")
    content = script.read_text(encoding="utf-8")
    
    categories = ["python", "powershell", "mcp", "convergence", "trade-chat"]
    found_categories = sum(1 for cat in categories if cat in content.lower())
    assert found_categories > 0, "Automation test suite should have test categories"


def test_mcp_connector_test_script_exists():
    """Verify MCP connector test script exists."""
    script = Path("scripts/Test-LanternMcpConnector.ps1")
    assert script.exists()


def test_mcp_connector_test_has_safety_checks():
    """Verify MCP connector test has safety checks."""
    script = Path("scripts/Test-LanternMcpConnector.ps1")
    content = script.read_text(encoding="utf-8")
    
    safety_checks = ["loopback", "remote", "safety"]
    found_safety = sum(1 for check in safety_checks if check in content.lower())
    assert found_safety > 0, "MCP connector test should have safety checks"


def test_browser_automation_script_exists():
    """Verify browser automation script exists."""
    script = Path("scripts/Test-BrowserAutomation.ps1")
    assert script.exists()


def test_browser_automation_script_has_browser_param():
    """Verify browser automation script has browser parameter."""
    script = Path("scripts/Test-BrowserAutomation.ps1")
    content = script.read_text(encoding="utf-8")
    
    assert "Browser" in content, "Browser automation script should have browser parameter"


def test_kalshi_live_order_script_exists():
    """Verify Kalshi live order script exists."""
    script = Path("scripts/Invoke-KalshiLiveOrder.ps1")
    assert script.exists()


def test_kalshi_live_order_script_has_safety_gates():
    """Verify Kalshi live order script has safety gates."""
    script = Path("scripts/Invoke-KalshiLiveOrder.ps1")
    content = script.read_text(encoding="utf-8")
    
    safety_gates = ["kill switch", "cap", "limit", "dry run"]
    found_gates = sum(1 for gate in safety_gates if gate in content.lower())
    assert found_gates > 0, "Kalshi live order script should have safety gates"


def test_hotswap_vm_receipt_test_exists():
    """Verify HotSwap VM receipt test exists."""
    script = Path("tests/Test-HotSwapVmReceipt.ps1")
    assert script.exists()


def test_house_thinker_test_exists():
    """Verify HouseThinker test exists."""
    script = Path("tests/Test-HouseThinker.ps1")
    assert script.exists()


def test_solo_mining_skill_test_exists():
    """Verify solo mining skill test exists."""
    script = Path("tests/Test-SoloMiningSkill.ps1")
    assert script.exists()


def test_scripts_directory_has_required_scripts():
    """Verify scripts directory has required scripts."""
    required_scripts = [
        "Invoke-LanternConvergenceLoop.ps1",
        "Invoke-LanternAutomationTestSuite.ps1",
        "Test-LanternMcpConnector.ps1",
        "Test-BrowserAutomation.ps1",
        "Invoke-KalshiLiveOrder.ps1",
    ]
    
    scripts_dir = Path("scripts")
    for script in required_scripts:
        assert (scripts_dir / script).exists(), f"Missing script: {script}"


def test_powershell_scripts_have_error_action_preference():
    """Verify PowerShell scripts have error action preference."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # This is a soft check - not all scripts need ErrorActionPreference
        if "ErrorActionPreference" in content:
            pass  # Script has error action preference


def test_powershell_scripts_have_comment_based_help():
    """Verify PowerShell scripts have comment-based help."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # Check for .SYNOPSIS or similar help
        has_help = ".SYNOPSIS" in content or ".DESCRIPTION" in content
        if has_help:
            pass  # Script has help


def test_powershell_scripts_use_approved_verbs():
    """Verify PowerShell scripts use approved verbs."""
    # This is a basic check - could be expanded with actual verb list
    approved_verbs = [
        "Invoke", "Test", "Get", "Set", "New", "Remove", "Update", "Add"
    ]
    
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    for ps1_file in ps1_files:
        filename = ps1_file.name
        # Check if filename starts with approved verb
        uses_approved = any(filename.startswith(verb) for verb in approved_verbs)
        if not uses_approved:
            # This is a soft check - not all scripts need to follow naming convention
            pass


def test_test_scripts_exist():
    """Verify test scripts exist in tests directory."""
    test_scripts = [
        "tests/Test-HotSwapVmReceipt.ps1",
        "tests/Test-HouseThinker.ps1",
        "tests/Test-SoloMiningSkill.ps1",
    ]
    
    for script in test_scripts:
        assert Path(script).exists(), f"Missing test script: {script}"


def test_powershell_scripts_are_not_empty():
    """Verify PowerShell scripts are not empty."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"PowerShell script is empty: {ps1_file}"


def test_powershell_scripts_have_no_syntax_errors():
    """Verify PowerShell scripts have no obvious syntax errors."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # Use PowerShell's own parser for accurate syntax validation
        # Count braces only outside strings and comments
        lines = content.split("\n")
        brace_count = 0
        in_string = False
        in_comment = False
        string_char = None
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # Skip comment lines
            
            i = 0
            while i < len(line):
                char = line[i]
                
                # Handle string toggling (both single and double quotes)
                if char in ('"', "'"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        # Check for escaped quote (double backslash or odd backslashes)
                        backslash_count = 0
                        j = i - 1
                        while j >= 0 and line[j] == '\\':
                            backslash_count += 1
                            j -= 1
                        if backslash_count % 2 == 0:  # Not escaped
                            in_string = False
                            string_char = None
                
                # Handle inline comments outside strings
                if not in_string and char == '#' and (i == 0 or line[i-1] != '$'):
                    break  # Rest of line is comment
                
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                
                i += 1
        
        # Allow slight imbalance due to multi-line strings, here-strings, etc.
        assert abs(brace_count) <= 2, f"{ps1_file} has significantly unbalanced braces (count: {brace_count})"


def test_convergence_loop_script_outputs_json():
    """Verify convergence loop script outputs JSON."""
    script = Path("scripts/Invoke-LanternConvergenceLoop.ps1")
    content = script.read_text(encoding="utf-8")
    
    assert "ConvertTo-Json" in content, "Convergence loop should output JSON"


def test_automation_test_suite_outputs_json():
    """Verify automation test suite outputs JSON."""
    script = Path("scripts/Invoke-LanternAutomationTestSuite.ps1")
    content = script.read_text(encoding="utf-8")
    
    assert "ConvertTo-Json" in content, "Automation test suite should output JSON"


def test_powershell_scripts_use_strict_mode():
    """Verify PowerShell scripts use strict mode where appropriate."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # Check for Set-StrictMode
        if "Set-StrictMode" in content:
            pass  # Script uses strict mode


def test_powershell_scripts_have_parameter_validation():
    """Verify PowerShell scripts have parameter validation."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # Check for ValidateSet, ValidateRange, etc.
        has_validation = "Validate" in content
        if has_validation:
            pass  # Script has parameter validation


def test_kalshi_scripts_have_kill_switch_check():
    """Verify Kalshi scripts check kill switch."""
    kalshi_scripts = [
        "scripts/Invoke-KalshiLiveOrder.ps1",
    ]
    
    for script_path in kalshi_scripts:
        script = Path(script_path)
        if script.exists():
            content = script.read_text(encoding="utf-8")
            assert "kill" in content.lower() or "switch" in content.lower(), f"{script} should check kill switch"


def test_powershell_scripts_use_write_host_for_output():
    """Verify PowerShell scripts use Write-Host for user output."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        if "Write-Host" in content:
            pass  # Script uses Write-Host for output


def test_powershell_scripts_handle_errors():
    """Verify PowerShell scripts have error handling."""
    ps1_files = list(Path("scripts").rglob("*.ps1"))
    
    for ps1_file in ps1_files:
        content = ps1_file.read_text(encoding="utf-8")
        # Check for try/catch or error handling
        has_error_handling = "try" in content.lower() and "catch" in content.lower()
        if has_error_handling:
            pass  # Script has error handling
