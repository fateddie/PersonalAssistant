# Engineering Guidelines – AskSharon

These guidelines define how code in this repo should be structured.

They **extend** the project-level principles defined in:

- `docs/principles.md`

If there is any conflict between this file and `docs/principles.md`,
**`docs/principles.md` takes precedence.**

---

## 1. Current Architecture Overview

AskSharon is currently organised as:

```text
assistant/
  core/           # core logic, shared behaviour
  modules/        # feature/integration modules
    voice/
    email/
    calendar/
    planner/
    behavioural_intelligence/
```

Plus separate UI code (e.g. Streamlit / frontend entrypoints).

For now we treat:
- `assistant/core/` as the **Core layer**
- `assistant/modules/*` as the **Modules / Services layer**
- Any UI files (Streamlit, web frontend) as the **UI layer**

A future refactor may migrate this to a standard structure:

```text
app/
  api/
  core/
  services/
  db/
ui/
```

That refactor is tracked separately in `docs/FUTURE_REFACTOR.md`.

---

## 2. Layered Architecture Rules (AskSharon v1)

### 2.1 Layers

Conceptual layers in this repo:

- **UI layer**
  - Any Streamlit / web frontend files (e.g. under `ui/` or top-level app entry).
  - Responsible only for display & user interaction.

- **Core layer**
  - `assistant/core/`
  - Business rules, workflows, shared domain logic.

- **Modules / Services layer**
  - `assistant/modules/` and its subpackages (email, calendar, planner, voice, behavioural_intelligence).
  - Integrations, concrete features, external API wrappers.

Later we may introduce explicit `api/` and `db/` layers; for now this guideline covers what exists.

### 2.2 Allowed dependencies

- **UI layer MAY**:
  - Call backend services via clearly defined functions or HTTP APIs.
  - Import thin client wrappers if we define them later.

- **Core layer MAY**:
  - Import and use `assistant/modules/*` where needed.

- **Modules / Services layer MAY**:
  - Import shared utilities from `assistant/core` only if they are generic and reusable,
    not business-logic that belongs in core.

### 2.3 Forbidden dependencies (conceptual)

- **UI MUST NOT**:
  - Import `assistant.core` directly for heavy business logic.
  - Import `assistant.modules` directly for low-level integrations.
  - Talk to DB or external APIs directly.

- **Core MUST NOT**:
  - Import any UI code (no knowledge of Streamlit / web frameworks).

- **Modules SHOULD NOT**:
  - Import UI code.
  - Embed UI concerns (rendering, formatting for display, etc.).

These rules are partially enforced automatically by `tools/check_architecture.py`.

---

## 3. Separation of Concerns

- **UI code**:
  - Handles layout, forms, navigation, and interaction.
  - Delegates decisions and data operations to core/modules via clear functions/APIs.
  - Does not contain complex business logic.

- **Core code** (`assistant/core`):
  - Implements business rules, workflows and decision logic.
  - Converts inputs from UI/services into decisions and output structures.
  - Avoids direct knowledge of UI frameworks or external HTTP clients where possible.

- **Modules** (`assistant/modules`):
  - Encapsulate feature-specific behaviour (email, calendar, planner, voice, behavioural intelligence).
  - Wrap external APIs, SDKs, and third-party integrations behind clean interfaces.
  - Should not depend on UI.

---

## 4. Data Models & Single Source of Truth

- Each important domain concept (e.g. task, appointment, goal, email context) should have
  a clear, canonical representation (e.g. a dataclass, Pydantic model, or similar).

- Avoid multiple slightly-different versions of the same concept scattered around the code.

- External systems remain the source of truth for their own data, e.g.:
  - Gmail / Calendar own raw email and calendar data.
  - AskSharon owns internal status, notes, metadata (e.g. task state, priority, behavioural tags).

Whenever possible, centralise shared models in `assistant/core` (or a dedicated models module)
rather than duplicating structures inside each module.

---

## 5. Pure vs Impure Functions

- Prefer **pure functions** in `assistant/core` for core decision-making:
  - Same input → same output.
  - No external I/O (no network calls, no DB, no direct Gmail/Calendar calls).

- Impure operations (network, file system, database, environment) should be encapsulated in:
  - `assistant/modules/*` (or dedicated integration wrappers),
  - or clearly-marked boundary functions.

This makes it easier to:
- Test important logic,
- Reuse logic across UI, agents, and future APIs,
- Evolve modules without breaking core behaviour.

---

## 6. Error Handling & Logging

- Avoid bare `except:` blocks. Always catch specific exception types.
- Do not silently swallow errors that affect system behaviour.
- Prefer:
  - Logging meaningful errors at module boundaries,
  - Returning structured error information up to the caller.

If/when a central logging util is introduced, modules should use that consistently.

---

## 7. Testing Expectations

- Any non-trivial logic in `assistant/core` SHOULD have unit tests under `tests/unit/`.
- Modules that wrap external APIs should have:
  - At least basic integration tests (possibly with mocks),
  - Or smoke tests that verify end-to-end behaviour in a safe environment.

We are not enforcing a strict testing percentage, but core logic should be testable
and tested where it matters.

---

## 8. Architecture Checker

This repo includes `tools/check_architecture.py`, which enforces a subset of these rules by:
- Scanning imports in `.py` files.
- Blocking obvious violations of layering (e.g. UI importing `assistant.core` or `assistant.modules`).

All code changes are expected to pass this checker.

If a change legitimately needs to break a rule, it MUST be documented in code comments
and ideally in an issue or `docs/FUTURE_REFACTOR.md`, and the rules updated consciously,
not accidentally.

---

## 9. AI / Claude Usage Rules

Claude and any AI agents MUST:

1. Read this file and `docs/principles.md` before major changes.
2. Use the **Plan → Implement → Self-review** workflow for any substantial feature (see `docs/AI_WORKFLOW.md`).
3. In the Self-review, explicitly state:
   - Any violations of these guidelines.
   - Any tight coupling between layers.
   - Any duplicated models or logic.

---

**Version**: 1.0
**Last Updated**: 2025-11-21
**Maintained By**: Engineering Team
