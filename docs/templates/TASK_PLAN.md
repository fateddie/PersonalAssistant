# Task Plan: [Title]

> Copy this template for each substantial task. Save as `planning/tasks/TASK_<name>.md` or discuss inline.

## 1. Overview

**Task:** [Brief description of what needs to be done]

**Type:** [ ] Feature | [ ] Bug Fix | [ ] Refactor | [ ] Documentation | [ ] Test

**Complexity:** [ ] Small (<1hr) | [ ] Medium (1-4hr) | [ ] Large (>4hr)

**Related Phase:** [e.g., Phase 6: Gmail Assistant]

---

## 2. Context

### Files to Modify
| File | Changes |
|------|---------|
| `path/to/file.py` | Description of changes |
| `path/to/file2.py` | Description of changes |

### Dependencies
- [ ] Requires: [other feature/module]
- [ ] External: [API, service, etc.]

### Related Docs
- [Link to relevant documentation]

---

## 3. Implementation Plan

### Step 1: [Name]
- [ ] Sub-task 1
- [ ] Sub-task 2

### Step 2: [Name]
- [ ] Sub-task 1
- [ ] Sub-task 2

### Step 3: Testing
- [ ] Unit tests for new functionality
- [ ] E2E tests (if UI changes)
- [ ] Manual verification

---

## 4. Edge Cases & Risks

| Scenario | Handling |
|----------|----------|
| What if X fails? | Graceful degradation / error message |
| What if Y is empty? | Default value / validation |

---

## 5. Pre-Commit Checklist (from .cursorrules)

### Automated (run `./scripts/pre-commit-check.sh`)
- [ ] `black` formatting passes
- [ ] `mypy` type checking passes
- [ ] File sizes under 200 lines
- [ ] Unit tests pass

### Manual Verification
- [ ] Error handling implemented
- [ ] Docstrings complete
- [ ] Decision logged in DECISIONS.md (if substantial)
- [ ] E2E tests for UI changes

---

## 6. Decision Record

> If this task involves architectural decisions, document them here or in DECISIONS.md

**Decision:** [What was decided]

**Rationale:** [Why this approach]

**Alternatives Considered:**
1. [Alternative 1] - rejected because...
2. [Alternative 2] - rejected because...

---

## 7. Completion

- [ ] Code implemented
- [ ] Tests passing
- [ ] Pre-commit checks passing
- [ ] Changes committed with conventional commit message
- [ ] PR created (if applicable)

**Commit Hash:** [e.g., abc1234]

**Time Spent:** [e.g., 2 hours]

---

*Template Version: 1.0 | See [docs/INDEX.md](../INDEX.md) for documentation index*
