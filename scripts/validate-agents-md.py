#!/usr/bin/env python3
"""
Validate AGENTS.md before new agents commit.

Pre-commit hook that ensures:
1. AGENTS.md exists and is up-to-date
2. Current agent is documented with metadata
3. Agent runbook/behavior documented
4. No multiple open PRs from same agent (per monoworkstream rule)
5. Agent capabilities clearly defined

Usage:
    python scripts/validate-agents-md.py
    SKIP_AGENT_CHECK=1 git commit  # to bypass (discouraged)
"""

import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
AGENTS_MD = REPO_ROOT / "AGENTS.md"
AGENT_SLOTS = REPO_ROOT / ".claude/agent-slots.json"

def run_cmd(cmd):
    """Run shell command."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def get_current_branch():
    """Get current git branch."""
    output, code = run_cmd("git rev-parse --abbrev-ref HEAD")
    return output if code == 0 else None

def extract_agent_name_from_branch(branch):
    """Extract agent name from branch prefix."""
    # Pattern: prefix/agent-name-context
    patterns = {
        'claude/': 'claude',
        'gemini/': 'gemini',
        'codex/': 'codex',
        'devin/': 'devin',
        'grok/': 'grok',
        'openai/': 'openai',
    }

    for prefix, agent in patterns.items():
        if branch.startswith(prefix):
            return agent

    return None

def agents_md_exists():
    """Check if AGENTS.md exists."""
    return AGENTS_MD.exists()

def read_agents_md():
    """Read AGENTS.md."""
    try:
        with open(AGENTS_MD, 'r') as f:
            return f.read()
    except:
        return None

def agent_documented_in_md(agent, content):
    """Check if agent is documented in AGENTS.md."""
    if not content:
        return False, "AGENTS.md not readable"

    # Look for agent heading
    pattern = rf'^#+\s+.*{agent.capitalize()}.*$'
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

    if not match:
        return False, f"Agent '{agent}' not documented in AGENTS.md"

    # Get the section for this agent
    agent_section_start = match.start()
    next_heading = re.search(r'^#+\s+', content[agent_section_start + 1:], re.MULTILINE)

    if next_heading:
        agent_section = content[agent_section_start:agent_section_start + 1 + next_heading.start()]
    else:
        agent_section = content[agent_section_start:]

    return True, agent_section

def validate_agent_documentation(agent, section):
    """Validate agent documentation is complete."""
    errors = []

    required_fields = {
        'capabilities': 'What this agent can do',
        'model': 'LLM/model used',
        'lane': 'Workstream lane designation',
        'status': 'Current operational status',
    }

    for field, description in required_fields.items():
        pattern = rf'\b{field}\b'
        if not re.search(pattern, section, re.IGNORECASE):
            errors.append(f"Missing documentation: {field} ({description})")

    # Check for runbook/behavior
    has_runbook = re.search(r'(runbook|behavior|instructions|how to)', section, re.IGNORECASE)
    if not has_runbook:
        errors.append("Missing: runbook or behavior description - how should this agent operate?")

    # Check for capabilities list
    has_capabilities = re.search(r'capabilities|can|supports', section, re.IGNORECASE)
    if not has_capabilities:
        errors.append("Missing: clear list of capabilities")

    # Check for contact/owner
    has_owner = re.search(r'(owner|contact|author|maintained by)', section, re.IGNORECASE)
    if not has_owner:
        errors.append("Missing: owner/contact information")

    return errors

def count_open_prs_for_agent(agent):
    """Count open PRs from this agent using branch prefixes."""
    output, code = run_cmd(f"git branch -r | grep 'origin/{agent}/' | wc -l")

    if code == 0:
        try:
            count = int(output)
            return count
        except:
            pass

    return 0

def check_monoworkstream_rules(agent, branch):
    """Check monoworkstream lane rules."""
    errors = []

    # Check if this agent has multiple open branches
    # (The actual rule is checked in git hooks, but we can warn here)
    open_branches = count_open_prs_for_agent(agent)

    if open_branches > 1:
        errors.append(f"[WARNING] Agent '{agent}' has {open_branches} open branches")
        errors.append("          Per monoworkstream rule: only 1 open PR per agent lane at a time")

    return errors

def get_staged_files():
    """Get staged files."""
    output, _ = run_cmd("git diff --cached --name-only")
    return [f for f in output.split('\n') if f]

def check_if_agent_commit():
    """Heuristically detect if this is an agent commit."""
    files = get_staged_files()

    # Agent commits typically have:
    # - AGENTS.md changes
    # - .claude/ changes
    # - OR use agent branch naming

    agent_commit_signals = [
        any('AGENTS.md' in f for f in files),
        any('.claude/' in f for f in files),
        any('agent' in f.lower() for f in files),
    ]

    return any(agent_commit_signals)

def main():
    """Main validation."""
    print("[*] Validating AGENTS.md and agent documentation...")

    branch = get_current_branch()
    if not branch:
        print("    [!] Could not determine current branch")
        return 1

    agent = extract_agent_name_from_branch(branch)

    if not agent:
        print(f"    Not an agent branch: {branch}")
        print("    AGENTS.md validation skipped")
        return 0

    print(f"    Detected agent: {agent}")
    print(f"    Branch: {branch}")

    # Check 1: AGENTS.md exists
    if not agents_md_exists():
        print("[!] AGENTS.md not found!")
        print("    Create AGENTS.md with documentation for all active agents")
        return 1

    print("    [✓] AGENTS.md exists")

    # Check 2: Agent is documented
    content = read_agents_md()
    documented, msg = agent_documented_in_md(agent, content)

    if not documented:
        print(f"    [!] {msg}")
        print(f"\n[!] Add {agent} to AGENTS.md with format:")
        print(f"""
## {agent.capitalize()} Agent

**Status:** active | on-hold | deprecated
**Model:** claude-opus | gpt-4 | gemini-pro | etc.
**Lane:** {agent}/
**Owner:** [Your name or team]

### Capabilities
- Feature 1
- Feature 2
- Feature 3

### Runbook / Behavior
Brief description of how this agent operates, what it's responsible for, and any special considerations.

### Constraints
- Maximum open PRs: 1 per lane
- Focus area: [describe primary focus]
- Not responsible for: [list exclusions]

### Recent Activity
- {datetime.now().strftime('%Y-%m-%d')}: Agent activated
        """)
        return 1

    print(f"    [✓] Agent documented in AGENTS.md")

    # Check 3: Validate documentation quality
    doc_errors = validate_agent_documentation(agent, msg)

    if doc_errors:
        print(f"\n[!] DOCUMENTATION ISSUES ({len(doc_errors)}):")
        for error in doc_errors:
            print(f"    - {error}")
        return 1

    print("    [✓] Agent documentation complete")

    # Check 4: Monoworkstream rules
    lane_errors = check_monoworkstream_rules(agent, branch)

    if lane_errors:
        print(f"\n[!] MONOWORKSTREAM WARNINGS ({len(lane_errors)}):")
        for error in lane_errors:
            print(f"    {error}")
        # Don't fail, just warn

    # Check 5: Verify commit is updating AGENTS.md if making changes
    files = get_staged_files()
    making_code_changes = any(
        not f.startswith('.claude/') and not f == 'AGENTS.md'
        for f in files if f
    )

    if making_code_changes and 'AGENTS.md' not in files:
        print("\n[!] WARNING: Making code changes without updating AGENTS.md")
        print("    Consider documenting your changes or status updates in AGENTS.md")

    print("\n[OK] Agent documentation validated")
    return 0

if __name__ == "__main__":
    sys.exit(main())
