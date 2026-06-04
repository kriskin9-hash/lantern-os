# Agent Responsibility Matrix

## Core Principle
Each feature flows through multiple agents. No single agent does design→dev→test→QA.

---

## Claude - Architecture & Design
**Primary:** Owns the "what should we build" decisions
- Feature design & specification
- Architecture review & approval
- Code review for correctness
- Cross-repo coordination
- Risk assessment

**Handoff:** Passes spec to Codex with "approved for implementation"

---

## Codex - Implementation
**Primary:** Owns "build it according to spec"
- Write code from Claude's spec
- Follow established patterns
- Implementation tests (unit level)
- Code formatting & style

**Validation Gate:** Must pass Claude's code review
**Handoff:** Passes to Gemini with "ready for QA"

---

## Gemini - Quality Assurance
**Primary:** Owns "does it actually work?"
- Integration testing
- Edge case testing
- Performance testing
- User acceptance criteria
- Regression detection

**Validation Gate:** Must pass all test criteria
**Handoff:** Passes to GPT with "validated" or back to Codex with "fixes needed"

---

## GPT - Documentation & Continuous Improvement
**Primary:** Owns "is it usable and optimized?"
- User documentation
- API documentation
- Performance optimization
- Refactoring suggestions
- Release notes

**Special:** Can suggest improvements back to any agent
**Always On:** Processes documentation, utilities, improvements continuously

---

## Workflow Example

```
Feature: Add task retry button

1. Claude designs: "Retry button in dashboard, moves task from failed to queue"
   └─> Creates spec, reviews architecture
   
2. Codex implements: Writes React button, API endpoint
   └─> Runs unit tests, follows patterns
   
3. Claude reviews: Code matches spec? Quality OK?
   └─> Approves or requests changes
   
4. Gemini tests: Button works? Edge cases? Performance?
   └─> Integration tests, user flows
   
5. GPT documents: Update UI docs, release notes, suggests optimizations
   └─> May suggest refactoring back to Codex
```

---

## Coverage & Cross-Checks

| Stage | Owner | Checked By | Cross-Check |
|-------|-------|-----------|------------|
| Design | Claude | - | Codex flags if unrealistic |
| Code | Codex | Claude | Matches spec? Quality? |
| Tests | Gemini | - | Codex can request re-test |
| Docs | GPT | Claude | Accuracy of documentation |

---

## Task Routing Rules

- **Design/Architecture** → Claude
- **Implementation** → Codex (if spec exists), else back to Claude
- **Testing/QA** → Gemini (only after code review passes)
- **Documentation/Optimization** → GPT (anytime)
- **Bug Found During Testing** → Back to Codex (with Gemini's report)
- **Design Flaw Found** → Back to Claude (with implementer's feedback)

---

## Queue Discipline

Features move through agents in sequence, not parallel. Each handoff is explicit:
- ✅ Approved by previous agent
- 📋 Clear acceptance criteria
- 🔄 Path to reopen if issues found

This ensures quality through peer review, not speed.
