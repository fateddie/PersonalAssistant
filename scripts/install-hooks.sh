#!/bin/bash
# Install git hooks for AskSharon.ai
# Run this once after cloning the repo

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Installing git hooks..."

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook - runs automated checks before commit
# Installed by: ./scripts/install-hooks.sh

# Run the pre-commit check script
./scripts/pre-commit-check.sh
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "✓ pre-commit hook installed"

# Create commit-msg hook for conventional commits
cat > "$HOOKS_DIR/commit-msg" << 'EOF'
#!/bin/bash
# Commit message hook - validates commit message format
# Installed by: ./scripts/install-hooks.sh

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Check for conventional commit format
# Pattern: type(scope): description OR type: description
if ! echo "$COMMIT_MSG" | grep -qE "^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+"; then
    echo ""
    echo "ERROR: Commit message does not follow conventional commits format."
    echo ""
    echo "Format: type(scope): description"
    echo "  OR:   type: description"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
    echo ""
    echo "Examples:"
    echo "  feat: Add user login"
    echo "  fix(api): Resolve rate limiting bug"
    echo "  docs: Update README"
    echo "  refactor(voice): Split large module"
    echo ""
    exit 1
fi

echo "✓ Commit message format OK"
EOF

chmod +x "$HOOKS_DIR/commit-msg"
echo "✓ commit-msg hook installed"

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "Hooks will automatically run on:"
echo "  • pre-commit: black, mypy, file size checks, unit tests"
echo "  • commit-msg: conventional commit format validation"
echo ""
echo "To skip hooks (emergency only): git commit --no-verify"
