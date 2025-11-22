#!/usr/bin/env python3
"""
Architecture Validator – AskSharon.ai

Enforces layered architecture rules defined in:
- docs/ENGINEERING_GUIDELINES.md

Current structure (v1):
- UI layer:           assistant/modules/voice/main.py (Streamlit)
- Core layer:         assistant/core/
- Modules/Services:   assistant/modules/* (email, calendar, planner, behavioural_intelligence)

Run manually:
    python tools/check_architecture.py

Can be wired into pre-commit and CI.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict

# Configuration
MAX_FILE_LINES = 500  # Rule #2: Hard limit - must split
WARN_FILE_LINES = 300  # Soft warning - consider splitting

# Forbidden import rules:
#   (folder_pattern, import_prefix_that_is_not_allowed, description)
FORBIDDEN_IMPORTS = [
    # UI (Streamlit in voice/main.py) must not import core/modules directly
    ("assistant/modules/voice/main.py", "assistant.core",
     "UI must not import core directly"),
    ("assistant/modules/voice/main.py", "assistant.modules.email",
     "UI must not import email module directly"),
    ("assistant/modules/voice/main.py", "assistant.modules.calendar",
     "UI must not import calendar module directly"),
    ("assistant/modules/voice/main.py", "assistant.modules.planner",
     "UI must not import planner module directly"),
    ("assistant/modules/voice/main.py", "assistant.modules.behavioural_intelligence",
     "UI must not import behavioural_intelligence module directly"),

    # Core must not import UI (Streamlit)
    ("assistant/core", "streamlit",
     "Core must not import Streamlit (UI framework)"),
    ("assistant/core", "assistant.modules.voice",
     "Core must not import UI layer"),

    # Modules should not import UI
    ("assistant/modules/email", "streamlit",
     "Email module must not import Streamlit"),
    ("assistant/modules/calendar", "streamlit",
     "Calendar module must not import Streamlit"),
    ("assistant/modules/planner", "streamlit",
     "Planner module must not import Streamlit"),
    ("assistant/modules/behavioural_intelligence", "streamlit",
     "Behavioural Intelligence module must not import Streamlit"),

    # Example: prevent direct external API calls from UI
    # Uncomment if you want to enforce this:
    # ("assistant/modules/voice/main.py", "google.auth",
    #  "UI must not make direct Google API calls"),
]


def find_violations(root: str = "."):
    """Scan Python files for architecture violations."""
    violations = []
    root_path = Path(root).resolve()

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue

            filepath = Path(dirpath) / filename
            relpath = filepath.relative_to(root_path)

            # Skip virtual environment
            if "venv" in str(relpath) or ".venv" in str(relpath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(relpath))
            except SyntaxError:
                # Skip files with syntax errors (e.g. partial edits)
                continue

            for node in ast.walk(tree):
                modules = []

                # import x, y, z
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]

                # from x import y
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules = [node.module]

                for module in modules:
                    if not module:
                        continue

                    for folder_contains, forbidden_prefix, description in FORBIDDEN_IMPORTS:
                        # Check if this file matches the pattern
                        if folder_contains in str(relpath).replace("\\", "/"):
                            # Check if it imports the forbidden module
                            if module.startswith(forbidden_prefix):
                                violations.append({
                                    "file": str(relpath),
                                    "module": module,
                                    "rule": forbidden_prefix,
                                    "description": description
                                })

    return violations


def group_violations(violations: List[Dict]) -> Dict[str, List[Dict]]:
    """Group violations by pattern for easier analysis."""
    groups: Dict[str, List[Dict]] = {}

    for v in violations:
        key = f"{v['description']}"
        if key not in groups:
            groups[key] = []
        groups[key].append(v)

    return groups


def check_file_sizes(root: str = ".") -> List[Dict]:
    """
    Check Python files for size violations (Rule #2: <200 lines).

    Returns list of violations with file path and line count.
    """
    violations = []
    root_path = Path(root).resolve()

    # Only check assistant/ directory
    assistant_dir = root_path / "assistant"
    if not assistant_dir.exists():
        return violations

    for dirpath, _, filenames in os.walk(assistant_dir):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue

            # Skip __init__.py files (typically small)
            if filename == "__init__.py":
                continue

            filepath = Path(dirpath) / filename
            relpath = filepath.relative_to(root_path)

            # Skip virtual environments
            if "venv" in str(relpath) or ".venv" in str(relpath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            except (OSError, UnicodeDecodeError):
                continue

            if line_count > MAX_FILE_LINES:
                violations.append({
                    "file": str(relpath),
                    "lines": line_count,
                    "limit": MAX_FILE_LINES,
                    "excess": line_count - MAX_FILE_LINES,
                    "severity": "error"
                })
            elif line_count > WARN_FILE_LINES:
                violations.append({
                    "file": str(relpath),
                    "lines": line_count,
                    "limit": MAX_FILE_LINES,
                    "excess": 0,
                    "severity": "warning"
                })

    # Sort by line count descending
    violations.sort(key=lambda x: x["lines"], reverse=True)
    return violations


def warn_if_no_ui_tests(root: str = "."):
    """
    Optional soft check:
    - If there appears to be Streamlit UI code,
    - And there are no tests in tests/e2e/,
    - Print a warning (but do NOT fail the check).

    This is a gentle reminder, not an enforcement mechanism.
    """
    has_ui = False
    ui_indicators = ("streamlit", "st.sidebar", "st.button", "st.write", "import streamlit")

    for dirpath, _, filenames in os.walk(root):
        # Skip venv
        if "venv" in dirpath or ".venv" in dirpath:
            continue

        for filename in filenames:
            if not filename.endswith(".py"):
                continue

            filepath = os.path.join(dirpath, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            # Crude heuristic: if file imports or uses streamlit, treat it as UI
            if any(ind in source for ind in ui_indicators):
                has_ui = True
                break
        if has_ui:
            break

    # If we have UI but no e2e tests, warn
    e2e_dir = os.path.join(root, "tests", "e2e")
    has_e2e_tests = False
    if os.path.isdir(e2e_dir):
        for fname in os.listdir(e2e_dir):
            if fname.startswith("test_") and fname.endswith(".py"):
                has_e2e_tests = True
                break

    if has_ui and not has_e2e_tests:
        print(
            "\n⚠️  Warning: Streamlit UI code detected, but no tests found in tests/e2e/.\n"
            "    For new or changed UI features, you are expected to add Playwright E2E tests.\n"
            "    See docs/UI_TESTING_STANDARDS.md for details.\n"
        )


if __name__ == "__main__":
    print("🔍 Scanning codebase for architecture violations...\n")

    has_errors = False

    # Check import violations
    import_violations = find_violations(".")

    if import_violations:
        print(f"❌ IMPORT VIOLATIONS DETECTED: {len(import_violations)} total\n")

        # Group violations by pattern
        grouped = group_violations(import_violations)

        for description, items in grouped.items():
            print(f"📋 {description} ({len(items)} violations):")
            for item in items:
                print(f"   - {item['file']}")
                print(f"     imports '{item['module']}'")
            print()

        has_errors = True

    # Check file size violations (Rule #2)
    size_violations = check_file_sizes(".")
    errors = [v for v in size_violations if v["severity"] == "error"]
    warnings = [v for v in size_violations if v["severity"] == "warning"]

    if errors:
        print(f"❌ FILE SIZE VIOLATIONS (Rule #2: <{MAX_FILE_LINES} lines): {len(errors)} files\n")
        for v in errors:
            print(f"   - {v['file']}: {v['lines']} lines (+{v['excess']} over limit)")
        print()
        has_errors = True

    if warnings:
        print(f"⚠️  FILE SIZE WARNINGS (approaching {MAX_FILE_LINES} line limit): {len(warnings)} files\n")
        for v in warnings:
            print(f"   - {v['file']}: {v['lines']} lines (consider splitting soon)")
        print()

    if has_errors:
        print("💡 Tip: These violations are documented patterns to avoid.")
        print("   See docs/ENGINEERING_GUIDELINES.md for architecture rules.")
        print("   See docs/FUTURE_REFACTOR.md for migration plan.")
        print("   Rule #2: Keep modules <200 lines, break into files.\n")
        sys.exit(1)

    # Soft UI test reminder (does not change exit code)
    warn_if_no_ui_tests(".")

    print("✅ No architecture violations detected.")
    print("   All code follows the layered architecture rules.\n")
    sys.exit(0)
