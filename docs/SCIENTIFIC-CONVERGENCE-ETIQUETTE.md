# Scientific Convergence Etiquette

**Purpose:** Establish communication standards for Lantern OS convergence work  
**Status:** Active standard  
**Effective:** 2026-05-30

---

## Core Principles

1. **Precision** - Use exact terminology and avoid ambiguity
2. **Objectivity** - Present facts without emotional language
3. **Clarity** - State assumptions and reasoning explicitly
4. **Evidence** - Support claims with data or citations
5. **Brevity** - Convey information efficiently without unnecessary elaboration
6. **Professionalism** - Maintain formal, scientific tone in all communications

---

## Communication Standards

### Written Communication

**Prohibited:**
- Emojis and emoticons
- Slang or colloquialisms
- Exclamation points
- Hyperbolic language (e.g., "amazing", "incredible")
- Personal opinions without qualification
- Vague or ambiguous statements

**Required:**
- Complete sentences with proper grammar
- Specific, measurable terms
- Explicit assumptions and constraints
- Citations for external references
- Clear action items with owners and deadlines
- Quantitative metrics where applicable

### Agent-to-Agent Communication

**Format:**
```
[Context] - [Action Required] - [Supporting Evidence]
```

**Example:**
```
Convergence loop detected 3 actionable issues in lantern-os repository. 
Execute scripts/Invoke-LanternConvergenceLoop.ps1 to validate. 
Evidence: manifests/open-issues.md lines 1-50.
```

### Agent-to-Human Communication

**Format:**
1. State current status objectively
2. Present findings with evidence
3. Propose next actions with rationale
4. Request approval or input as needed

**Example:**
```
Status: Convergence loop validation complete
Findings: 0 actionable issues, 1 held issue (LANTERN-OS-BOOT-001)
Next Action: Review held issues and select promotion candidate
Rationale: No blocking issues prevent advancement
```

---

## Documentation Standards

### File Headers

```markdown
# [Document Title]

**Purpose:** [Clear statement of document purpose]  
**Status:** [draft|active|deprecated]  
**Effective:** [YYYY-MM-DD]  
**Owner:** [Responsible party]
```

### Code Comments

**Prohibited:**
- Emojis in comments
- Humorous or casual remarks
- Unclear abbreviations

**Required:**
- Clear explanation of complex logic
- Assumptions and constraints
- Input/output specifications
- Error conditions and handling

### Issue Tracking

**Format:**
```
[ID]: [Title]
- Status: [open|in_progress|resolved|held]
- Severity: [critical|high|medium|low]
- Evidence: [supporting data or references]
- Next Action: [specific next step]
```

---

## Meeting Standards

### Stand-up Format

1. Completed work (objective facts)
2. Current blockers (with evidence)
3. Next actions (specific and time-bound)

### Decision Records

**Format:**
```
Decision: [Clear statement]
Context: [Background information]
Alternatives Considered: [List with pros/cons]
Rationale: [Reasoning for decision]
Implications: [Consequences and dependencies]
```

---

## Code Review Standards

### Review Comments

**Prohibited:**
- Emojis in review comments
- Vague feedback (e.g., "this looks weird")
- Personal attacks or criticism

**Required:**
- Specific line references
- Clear explanation of issue
- Suggested improvement with rationale
- Reference to relevant standards or patterns

### Approval Criteria

- Code follows established patterns
- Tests included and passing
- Documentation updated
- Security implications considered
- Performance impact assessed

---

## Error Reporting

### Format

```
Error: [Specific error message]
Context: [What was being attempted]
Evidence: [Error logs, stack traces, screenshots]
Impact: [What systems or users are affected]
Mitigation: [Immediate workaround if available]
Next Action: [Specific steps to resolve]
```

---

## Convergence Loop Standards

### Issue Reporting

**Format:**
```
Issue ID: [LANTERN-XXX-###]
Title: [Concise description]
Severity: [critical|high|medium|low]
Evidence: [Supporting data]
Fix: [Proposed solution]
Status: [open|in_progress|resolved|held]
```

### Status Updates

**Format:**
```
Convergence Status: [number] actionable issues, [number] held issues
Leading Issues: [list of top priority issues]
Next Action: [specific next step]
Evidence: [supporting data]
```

---

## Terminology Standards

### Preferred Terms

- Use "validate" instead of "check"
- Use "execute" instead of "run"
- Use "terminate" instead of "kill"
- Use "address" instead of "fix"
- Use "implement" instead of "build"

### Avoided Terms

- "awesome", "cool", "great" (use specific descriptors)
- "just", "simply" (be precise)
- "obviously", "clearly" (provide evidence)
- "should", "would" (use "must", "will" for requirements)

---

## Quality Metrics

### Communication Quality Indicators

- Ambiguity rate: < 5%
- Evidence support rate: > 90%
- Action item clarity: 100%
- Terminology consistency: 100%

### Documentation Quality Indicators

- Completeness: All sections present
- Accuracy: Technical details verified
- Currency: Last updated within 30 days
- Clarity: Peer review approved

---

## Enforcement

### Violation Categories

1. **Minor** - Single emoji or informal term in non-critical document
2. **Major** - Systematic use of informal language in critical documentation
3. **Critical** - Ambiguous communication causing operational issues

### Correction Process

1. Identify violation with specific reference
2. Provide corrected version
3. Update relevant standards if needed
4. Monitor for recurrence

---

## References

- IEEE Style Guide
- ACM Documentation Standards
- Scientific Writing Guidelines
- Technical Communication Best Practices

---

## Version History

- v1.0 (2026-05-30): Initial standard established
