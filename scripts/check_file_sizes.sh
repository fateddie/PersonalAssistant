#!/bin/bash
#
# File Size Checker – AskSharon.ai
# =================================
# Enforces Rule #2: Keep Modules Small (<200 lines)
#
# Usage:
#   ./scripts/check_file_sizes.sh          # Check and report
#   ./scripts/check_file_sizes.sh --strict # Fail on any violation
#
# Can be wired into pre-commit hooks and CI.

set -e

MAX_LINES=500
WARN_LINES=300
STRICT_MODE=false

# Parse arguments
if [ "$1" == "--strict" ]; then
    STRICT_MODE=true
fi

echo "🔍 Checking file sizes in assistant/ (Rule #2: <${MAX_LINES} lines)..."
echo ""

VIOLATIONS=0
WARNINGS=0

# Find all Python files, excluding __init__.py and venv
while IFS= read -r file; do
    # Skip __init__.py files
    if [[ "$file" == *"__init__.py" ]]; then
        continue
    fi

    # Count lines
    lines=$(wc -l < "$file" | tr -d ' ')

    if [ "$lines" -gt "$MAX_LINES" ]; then
        excess=$((lines - MAX_LINES))
        echo "❌ $file: $lines lines (+$excess over limit)"
        VIOLATIONS=$((VIOLATIONS + 1))
    elif [ "$lines" -gt "$WARN_LINES" ]; then
        echo "⚠️  $file: $lines lines (approaching limit)"
        WARNINGS=$((WARNINGS + 1))
    fi
done < <(find assistant -name "*.py" -type f 2>/dev/null | grep -v venv | grep -v __pycache__)

echo ""

if [ "$VIOLATIONS" -gt 0 ]; then
    echo "❌ Found $VIOLATIONS file(s) exceeding $MAX_LINES lines"
    if [ "$WARNINGS" -gt 0 ]; then
        echo "⚠️  Found $WARNINGS file(s) approaching the limit"
    fi
    echo ""
    echo "💡 Tip: Split large files into smaller, focused modules."
    echo "   See docs/ENGINEERING_GUIDELINES.md for guidance."

    if [ "$STRICT_MODE" = true ]; then
        exit 1
    fi
elif [ "$WARNINGS" -gt 0 ]; then
    echo "⚠️  Found $WARNINGS file(s) approaching the $MAX_LINES line limit"
    echo "   Consider splitting these files before they grow further."
    exit 0
else
    echo "✅ All files under $MAX_LINES lines"
    exit 0
fi
