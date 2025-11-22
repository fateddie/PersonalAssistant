# AI Development Workflow

This workflow applies to ALL non-trivial code changes made by AI (Claude, ChatGPT, Cursor, etc.).

---

## 1. Files to Read First

Before planning or implementing any feature, the AI MUST read and respect:

1. `docs/principles.md`
2. `docs/ENGINEERING_GUIDELINES.md`
3. `.cursorrules` (27 Rules for AskSharon development)

**Why this matters**: These files contain the project's architectural decisions, constraints, and quality standards. Ignoring them leads to code that breaks existing patterns and creates technical debt.

---

## 2. Workflow: Plan → Implement → Self-review

### Step 0 – Pre-Edit Checklist (BEFORE touching any file)

Before editing ANY Python file, run these checks:

```bash
# 1. Check file size (Rule #2: <200 lines)
wc -l <file_to_edit>

# 2. If file is >150 lines, STOP and plan split first
# 3. Run architecture checker to see current violations
python tools/check_architecture.py
```

**If file is already >200 lines:**
- DO NOT add more code to it
- Split the file first, THEN make your changes
- See `.cursorrules` Rule #2 for splitting guidance

**If your edit would push file >200 lines:**
- Split the file first
- Make your changes to the appropriate new file

This prevents file bloat BEFORE it happens.

---

### Step A – Plan

- **Do NOT write code yet.**
- Identify:
  - Which layers are involved (`ui`, `assistant/core`, `assistant/modules/*`).
  - Which files will be created or modified.
  - How control will flow between those files.
  - What tests are needed.

The plan should be short and explicit.

**Example Plan Format**:
```
Feature: Add email priority detection

Layers involved:
- assistant/modules/email/ (add priority detection logic)
- assistant/core/context_manager.py (store priority in context)

Files to modify:
- assistant/modules/email/main.py (add detect_priority endpoint)
- assistant/core/context_manager.py (add priority field)

Control flow:
1. Email module receives email
2. Analyze urgency keywords
3. Store priority in context
4. Return priority to caller

Tests:
- tests/unit/test_email_priority.py (unit tests for detection logic)
- tests/integration/test_email_integration.py (E2E test)
```

### Step B – Implement

- Implement EXACTLY according to the plan.
- Only touch the files you listed, unless a change is obviously necessary.
- Respect the dependency rules from `docs/ENGINEERING_GUIDELINES.md`:
  - UI must not import `assistant.core` or `assistant.modules`.
  - Core must not import UI.
  - Modules should not import UI.
- Add minimal comments where architecture decisions might not be obvious.
- Follow the 27 Rules from `.cursorrules`:
  - Error handling with `error_handler.handle()`
  - Notifications with `notifier.notify()`
  - Type hints everywhere
  - Run `pytest`, `black`, `mypy` before claiming complete

### Step C – Self-review

After implementation, act as a senior engineer and:

- Compare the changes against `docs/ENGINEERING_GUIDELINES.md`.
- Run `tools/check_architecture.py` to verify no layer violations.
- List:
  - Any violations or potential violations.
  - Any tight coupling between layers.
  - Any duplicated models or logic.
  - Any missing error handling or notifications.
  - Any missing tests.
- For each issue, either:
  - Fix it immediately, or
  - Explain why it is acceptable as a temporary exception.

**The Self-review MUST be written out in text, not just implied.**

**Example Self-Review**:
```
Self-Review: Email Priority Detection

✅ Architecture compliance:
- No UI imports assistant.core or assistant.modules
- Core doesn't import UI
- Follows layered structure

✅ Error handling:
- Added try/except with error_handler.handle()
- Graceful degradation if OpenAI API fails

✅ Notifications:
- Added success/failure notifications

⚠️ Potential issues:
- Priority detection uses hardcoded keywords (future: use ML model)
- Documented in FUTURE_REFACTOR.md

✅ Tests:
- Unit tests: 5 test cases covering edge cases
- Integration test: E2E flow verified

✅ Code quality:
- pytest passes (12/12 tests)
- black formatting applied
- mypy type checks pass
```

---

## 3. When This Workflow Applies

Use this workflow for:
- ✅ New features or modules
- ✅ Refactoring existing code
- ✅ Bug fixes that touch multiple files
- ✅ Changes to core architecture or data models

You may skip this workflow for:
- ❌ Trivial changes (typo fixes, comment updates)
- ❌ Single-line bug fixes
- ❌ Documentation-only changes

When in doubt, use the workflow. It takes 5 extra minutes and prevents hours of debugging later.

---

## 4. Enforcement

### Automated Checks

| Check | Tool | What it catches |
|-------|------|-----------------|
| Layer violations | `python tools/check_architecture.py` | UI importing core, cross-layer imports |
| File size (Rule #2) | `python tools/check_architecture.py` | Files >200 lines |
| File size (quick) | `./scripts/check_file_sizes.sh` | Files >200 lines |
| Formatting | `black assistant/` | Code style |
| Type hints | `mypy assistant/` | Missing types |
| Tests | `pytest` | Regressions |

### When to Run

- **Before every edit**: `wc -l <file>` (check size)
- **After every edit**: `python tools/check_architecture.py`
- **Before commit**: All checks above

### Pre-commit Hook (optional)

```bash
# .git/hooks/pre-commit
#!/bin/bash
python tools/check_architecture.py || exit 1
./scripts/check_file_sizes.sh --strict || exit 1
```

But the AI's self-review is the first line of defense. **Use it.**

---

## 5. Why This Matters

**Without this workflow:**
- AI dumps code that breaks existing patterns
- Layer boundaries get violated
- Technical debt accumulates
- Bugs hide in untested code

**With this workflow:**
- Changes are intentional and planned
- Architecture stays clean
- Code is testable and tested
- Self-review catches issues before they merge

---

**Claude / AI agents**: Treat this workflow as non-negotiable for substantial changes. If you skip steps, explicitly state why and get user approval first.

---

**Version**: 1.0
**Last Updated**: 2025-11-21
**Maintained By**: Engineering Team
