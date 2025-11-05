# Universal Project Setup Template

**Version:** 1.0
**Date:** 2025-10-17
**Purpose:** Reusable template for setting up development tools, libraries, and best practices across all projects

---

## 🎯 Quick Start Checklist

- [ ] Set up virtual environment (Python venv or Node nvm)
- [ ] Configure centralized environment variables (`.env`)
- [ ] Set up code formatting (Prettier + language-specific tools)
- [ ] Configure linting (ESLint/Ruff/Pylint)
- [ ] Create `.editorconfig` for consistent style
- [ ] Set up pre-commit hooks
- [ ] Configure CI/CD pipeline (GitHub Actions)
- [ ] Set up CodeRabbit AI code reviews
- [ ] Set up testing framework
- [ ] Add browser automation (Playwright + MCP)
- [ ] Configure backend (if applicable - Supabase)
- [ ] Add documentation standards
- [ ] Set up monitoring/logging

---

## 🐍 Virtual Environment Setup

### Python Projects (venv)

**Why:** Isolate project dependencies, avoid conflicts between projects, ensure reproducible environments.

#### Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation (should show venv path)
which python

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

#### .gitignore
```
venv/
.venv/
env/
ENV/
```

#### requirements.txt Best Practices
```bash
# Generate from current environment
pip freeze > requirements.txt

# Better: Use pip-tools for dependency management
pip install pip-tools
pip-compile requirements.in  # Creates requirements.txt with pinned versions
pip-sync requirements.txt     # Install exact versions

# requirements.in (high-level dependencies)
fastapi>=0.104.0
pydantic>=2.0.0
redis>=5.0.0
```

### JavaScript/TypeScript Projects (nvm)

**Why:** Manage multiple Node.js versions per project, ensure team uses same Node version.

#### Setup
```bash
# Install nvm (macOS/Linux)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install nvm (Windows - use nvm-windows)
# Download from: https://github.com/coreybutler/nvm-windows

# Install specific Node version
nvm install 20

# Use specific version
nvm use 20

# Set default version
nvm alias default 20

# Create .nvmrc (team uses same version)
echo "20" > .nvmrc

# Team members run:
nvm use  # Reads from .nvmrc
```

#### .gitignore
```
node_modules/
.npm/
```

### Docker (Advanced - Cross-platform isolation)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    volumes:
      - .:/app
    env_file:
      - .env
```

---

## 🔐 Centralized Environment Variables

### Why Centralized Config?

**Problem:** API keys scattered across multiple files
```python
# Bad: Direct os.getenv() everywhere
import os
api_key = os.getenv("OPENAI_API_KEY")  # Repeated 20x across codebase
```

**Solution:** Single config manager
```python
# Good: Central config
from config.env_manager import get_config
config = get_config()
api_key = config.openai_api_key  # Type-safe, validated, one place
```

**Benefits:**
- ✅ One place to manage all variables
- ✅ Automatic validation (fail fast with helpful errors)
- ✅ Type safety (int/bool conversion)
- ✅ Default values for optional configs
- ✅ Easy to mock for testing

### Implementation

#### 1. Create `config/env_manager.py`

```python
"""
Centralized environment variable management.
Loads from .env file and provides type-safe access.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env from project root or config/
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env"

load_dotenv(env_path)


@dataclass
class Config:
    """
    Centralized configuration with type safety and validation.

    Usage:
        from config.env_manager import get_config
        config = get_config()
        api_key = config.openai_api_key
    """

    # Project Settings
    project_name: str
    environment: str
    debug: bool

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None

    # Database
    database_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    # Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # External APIs
    github_token: Optional[str] = None
    slack_webhook_url: Optional[str] = None

    # Feature Flags
    enable_caching: bool = True
    enable_logging: bool = True

    def validate(self) -> list[str]:
        """
        Validate required configuration.
        Returns list of missing/invalid settings.
        """
        errors = []

        # Check required fields
        if not self.project_name:
            errors.append("PROJECT_NAME is required")

        if self.environment not in ["development", "staging", "production"]:
            errors.append(f"ENVIRONMENT must be dev/staging/prod, got: {self.environment}")

        # Warn about missing optional keys
        if not self.openai_api_key:
            errors.append("Warning: OPENAI_API_KEY not set (OpenAI features disabled)")

        return errors


def get_config() -> Config:
    """
    Load and return validated configuration.

    Raises:
        ValueError: If required configuration is missing

    Returns:
        Config instance with all settings
    """
    config = Config(
        # Required
        project_name=os.getenv("PROJECT_NAME", "MyProject"),
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=os.getenv("DEBUG", "true").lower() == "true",

        # API Keys
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),

        # Database
        database_url=os.getenv("DATABASE_URL"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        redis_password=os.getenv("REDIS_PASSWORD"),

        # Supabase
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),

        # External APIs
        github_token=os.getenv("GITHUB_TOKEN"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),

        # Feature Flags
        enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
        enable_logging=os.getenv("ENABLE_LOGGING", "true").lower() == "true",
    )

    # Validate and warn
    errors = config.validate()
    if any("required" in e.lower() for e in errors):
        raise ValueError(f"Configuration errors:\n" + "\n".join(errors))

    # Print warnings
    for warning in errors:
        if "Warning" in warning:
            print(f"⚠️  {warning}")

    return config


# Singleton instance
_config: Optional[Config] = None

def get_config_cached() -> Config:
    """Get cached config (faster for repeated calls)"""
    global _config
    if _config is None:
        _config = get_config()
    return _config
```

#### 2. Create `config/.env.example`

```bash
# ==============================================
# Central Environment Variables
# ==============================================
# SETUP: Copy to .env and fill in your values
# Command: cp config/.env.example config/.env

# -----------------------------------------------------
# Project Settings (REQUIRED)
# -----------------------------------------------------
PROJECT_NAME=MyProject
ENVIRONMENT=development  # development, staging, production
DEBUG=true

# -----------------------------------------------------
# API Keys (OPTIONAL - features disabled if missing)
# -----------------------------------------------------
# OpenAI (GPT models)
OPENAI_API_KEY=sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Perplexity (Research)
PERPLEXITY_API_KEY=pplx-...

# -----------------------------------------------------
# Database
# -----------------------------------------------------
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# Redis (Caching & Memory)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# -----------------------------------------------------
# Supabase (Backend)
# -----------------------------------------------------
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# -----------------------------------------------------
# External APIs
# -----------------------------------------------------
GITHUB_TOKEN=ghp_...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# -----------------------------------------------------
# Feature Flags
# -----------------------------------------------------
ENABLE_CACHING=true
ENABLE_LOGGING=true

# =====================================================
# SECURITY NOTES:
# - Never commit .env file with real keys!
# - Add .env to .gitignore
# - Use environment-specific files (.env.production)
# - Rotate keys regularly
# =====================================================
```

#### 3. Usage in Your Code

```python
# agents/strategy_agent/strategy_agent.py
from config.env_manager import get_config

class StrategyAgent:
    def __init__(self):
        config = get_config()

        # Type-safe access
        if config.openai_api_key:
            self.client = OpenAI(api_key=config.openai_api_key)
        else:
            raise ValueError("OpenAI API key required for StrategyAgent")

        self.debug = config.debug

# scripts/run_pipeline.py
from config.env_manager import get_config

config = get_config()
print(f"Running {config.project_name} in {config.environment} mode")

# Tests
from config.env_manager import Config

def test_agent():
    # Mock config for testing
    test_config = Config(
        project_name="test",
        environment="development",
        debug=True,
        openai_api_key="test-key"
    )
    # Pass to agent...
```

#### 4. Create `scripts/validate_environment.py`

```python
"""
Validate environment configuration before running.
"""

from config.env_manager import get_config

def main():
    print("🔍 Validating environment configuration...\n")

    try:
        config = get_config()

        print("✅ Configuration loaded successfully!")
        print(f"\nProject: {config.project_name}")
        print(f"Environment: {config.environment}")
        print(f"Debug: {config.debug}")

        # Check API keys
        print("\n📋 API Keys Status:")
        print(f"  OpenAI: {'✅ Set' if config.openai_api_key else '❌ Missing'}")
        print(f"  Anthropic: {'✅ Set' if config.anthropic_api_key else '❌ Missing'}")
        print(f"  Perplexity: {'✅ Set' if config.perplexity_api_key else '❌ Missing'}")

        # Check database
        print("\n🗄️  Database Status:")
        print(f"  Redis: {config.redis_host}:{config.redis_port}")
        print(f"  Supabase: {'✅ Configured' if config.supabase_url else '❌ Not configured'}")

        print("\n✅ Environment validation complete!")

    except ValueError as e:
        print(f"❌ Configuration error:\n{e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
```

### Environment-Specific Configs

```bash
# Different configs per environment
.env.development
.env.staging
.env.production

# Load specific environment
# In env_manager.py
env_name = os.getenv("ENVIRONMENT", "development")
env_path = Path(__file__).parent / f".env.{env_name}"
load_dotenv(env_path)
```

### Docker Compose Integration

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - config/.env
    environment:
      - ENVIRONMENT=production
```

---

## 📦 Core Development Tools

### 1. Code Formatting

#### JavaScript/TypeScript Projects
```bash
# Install Prettier
npm install --save-dev prettier

# Create .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}

# Create .prettierignore
node_modules/
dist/
build/
*.min.js
coverage/
```

#### Python Projects
```bash
# Install Black (opinionated formatter)
pip install black

# Install Ruff (fast linter + formatter)
pip install ruff

# Create pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

# Format command
black .
ruff format .
```

### 2. EditorConfig (Universal)

Create `.editorconfig`:
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

### 3. Linting

#### JavaScript/TypeScript
```bash
# Install ESLint
npm install --save-dev eslint @eslint/js

# Create eslint.config.js (flat config)
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    rules: {
      'no-console': 'warn',
      'no-unused-vars': 'error',
    },
  },
];
```

#### Python
```bash
# Using Ruff (recommended - fastest)
pip install ruff

# Create .ruff.toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "I", "N", "W", "C90", "B", "UP"]
ignore = ["E501"]

# Or use Pylint
pip install pylint
pylint src/
```

---

## 🔧 Git Workflow

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
      - id: mixed-line-ending

  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # JavaScript/TypeScript
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier

# Install hooks
pre-commit install
```

### Commit Message Convention

Use Conventional Commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Example:**
```
feat(auth): add OAuth2 Google login

Implemented Google OAuth2 authentication flow using Supabase Auth.
Users can now sign in with their Google accounts.

Closes #123
```

### Branch Strategy

```
main          - Production-ready code
develop       - Integration branch
feature/*     - New features (feature/user-auth)
fix/*         - Bug fixes (fix/login-error)
hotfix/*      - Production hotfixes
release/*     - Release preparation
```

---

## 🤖 CI/CD - GitHub Actions

Create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Python project
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest ruff black

      - name: Lint with Ruff
        run: ruff check .

      - name: Format check with Black
        run: black --check .

      - name: Run tests
        run: pytest tests/ -v

      # JavaScript/TypeScript project
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run type-check

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

  coderabbit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: CodeRabbit Review
        uses: coderabbitai/coderabbit-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 🧠 AI Code Reviews - CodeRabbit

### Setup

1. **Free IDE Integration** (VS Code/Cursor/Windsurf)
   ```bash
   # Install CodeRabbit extension
   # Search "CodeRabbit" in VS Code extensions
   # Get real-time code reviews as you type
   ```

2. **GitHub Integration** (Paid - $12-30/month)
   ```bash
   # Go to https://www.coderabbit.ai
   # Connect your GitHub account
   # Select repositories
   # CodeRabbit will review all PRs automatically
   ```

3. **CLI Tool** (Terminal reviews)
   ```bash
   # Install CLI
   npm install -g @coderabbit/cli

   # Review current changes
   coderabbit review

   # Review specific files
   coderabbit review src/main.py
   ```

### Features
- Line-by-line code reviews
- Security vulnerability detection
- Best practice suggestions
- Auto-generated PR summaries
- Learning from your coding style
- One-click fixes

---

## 🌐 Browser Automation - Playwright + MCP

### Setup

```bash
# Install Playwright
npm install -D @playwright/test
npx playwright install

# Install MCP (Model Context Protocol) server
npm install -g @executeautomation/mcp-playwright
```

### Configuration

Create `playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } },
  ],
});
```

### MCP Integration (for Claude Code)

Add to Claude Code config:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@executeautomation/mcp-playwright"]
    }
  }
}
```

### Example Test

```typescript
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Welcome');
});
```

---

## 🗄️ Backend - Supabase

### Features
- **PostgreSQL Database** - Full Postgres with auto-generated APIs
- **Authentication** - Email, OAuth (Google, GitHub, etc.), magic links
- **Storage** - File/image storage with CDN
- **Realtime** - WebSocket subscriptions for live updates
- **Edge Functions** - Serverless Deno functions
- **Row Level Security** - Database-level authorization

### Setup

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Initialize project
supabase init

# Start local development
supabase start

# Install client library
npm install @supabase/supabase-js  # JavaScript
pip install supabase               # Python
```

### Configuration

Create `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Client Setup (JavaScript)

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Authentication
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123',
});

// Database query
const { data: users } = await supabase
  .from('users')
  .select('*')
  .eq('active', true);

// Realtime subscription
const channel = supabase
  .channel('public:messages')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'messages' },
    (payload) => console.log('New message:', payload)
  )
  .subscribe();

// Storage
await supabase.storage
  .from('avatars')
  .upload('user-123.png', file);
```

### Client Setup (Python)

```python
from supabase import create_client, Client
import os

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Authentication
user = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password123"
})

# Database query
response = supabase.table("users").select("*").eq("active", True).execute()
users = response.data

# Storage
with open("avatar.png", "rb") as f:
    supabase.storage.from_("avatars").upload("user-123.png", f)
```

---

## 🧪 Testing

### Python - Pytest

```bash
# Install
pip install pytest pytest-cov pytest-asyncio

# Create pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term

# Create tests/conftest.py (fixtures)
import pytest

@pytest.fixture
def sample_data():
    return {"id": 1, "name": "Test"}

# Create tests/test_example.py
def test_example(sample_data):
    assert sample_data["id"] == 1
    assert sample_data["name"] == "Test"

# Run tests
pytest
pytest --cov=src --cov-report=html
```

### JavaScript/TypeScript - Vitest

```bash
# Install
npm install -D vitest @vitest/ui

# Create vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
});

# Create tests/example.test.ts
import { describe, it, expect } from 'vitest';

describe('Example', () => {
  it('should pass', () => {
    expect(1 + 1).toBe(2);
  });
});

# Run tests
npm test
npm run test:coverage
```

---

## 📊 Monitoring & Logging

### Python - Structured Logging

```python
import logging
import json
from datetime import datetime

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Setup logger
logger = logging.getLogger(__name__)
handler = logging.FileHandler("app.log")
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User logged in", extra={"user_id": 123})
logger.error("Failed to process", extra={"error": "Connection timeout"})
```

### Environment Variables

Create `.env.example`:
```env
# Application
APP_ENV=development
APP_PORT=3000
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
DATABASE_POOL_SIZE=20

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key

# APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...

# External Services
REDIS_URL=redis://localhost:6379
SENTRY_DSN=https://...
```

### Load Environment Variables

Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
```

JavaScript:
```typescript
import 'dotenv/config';

const apiKey = process.env.OPENAI_API_KEY;
```

---

## 📝 Documentation Standards

### README.md Structure

```markdown
# Project Name

Brief description (1-2 sentences)

## Features

- Feature 1
- Feature 2

## Quick Start

\`\`\`bash
npm install
npm run dev
\`\`\`

## Documentation

- [Setup Guide](docs/setup.md)
- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)

## Testing

\`\`\`bash
npm test
\`\`\`

## License

MIT
```

### Code Documentation

Python (Docstrings):
```python
def calculate_score(data: dict) -> float:
    """
    Calculate weighted score from input data.

    Args:
        data: Dictionary containing 'reach', 'impact', 'confidence', 'effort'

    Returns:
        Weighted score between 0-100

    Raises:
        ValueError: If required keys are missing

    Example:
        >>> calculate_score({'reach': 8, 'impact': 7, 'confidence': 0.9, 'effort': 3})
        75.5
    """
    pass
```

TypeScript (JSDoc):
```typescript
/**
 * Calculate weighted score from input data
 *
 * @param data - Object containing reach, impact, confidence, effort
 * @returns Weighted score between 0-100
 * @throws {Error} If required keys are missing
 *
 * @example
 * ```ts
 * calculateScore({ reach: 8, impact: 7, confidence: 0.9, effort: 3 })
 * // Returns: 75.5
 * ```
 */
function calculateScore(data: ScoreInput): number {
  // ...
}
```

---

## 🚀 Deployment

### GitHub Secrets (for CI/CD)

Add to repository settings → Secrets:
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
OPENAI_API_KEY
SENTRY_DSN
```

### Docker (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
```

---

## 📋 Project Checklist

Use this checklist when starting a new project:

### Initial Setup
- [ ] Initialize git repository
- [ ] Create `.gitignore` (use gitignore.io)
- [ ] Set up virtual environment (Python) or node_modules (JS)
- [ ] Create `README.md`
- [ ] Create `.env.example`
- [ ] Add license (MIT, Apache, etc.)

### Code Quality
- [ ] Install and configure Prettier/Black
- [ ] Install and configure linters (ESLint/Ruff)
- [ ] Create `.editorconfig`
- [ ] Set up pre-commit hooks
- [ ] Configure CodeRabbit

### Testing
- [ ] Install testing framework (Pytest/Vitest)
- [ ] Write sample tests
- [ ] Set up test coverage reporting
- [ ] Add Playwright for E2E tests (if web app)

### CI/CD
- [ ] Create GitHub Actions workflow
- [ ] Add build and test jobs
- [ ] Set up automated deployments
- [ ] Configure branch protection rules

### Backend (if applicable)
- [ ] Set up Supabase project
- [ ] Configure authentication
- [ ] Design database schema
- [ ] Set up Row Level Security policies
- [ ] Create API endpoints or Edge Functions

### Documentation
- [ ] Write setup instructions
- [ ] Document API endpoints
- [ ] Add architecture diagrams
- [ ] Write contribution guidelines

### Monitoring
- [ ] Set up structured logging
- [ ] Add error tracking (Sentry)
- [ ] Configure performance monitoring
- [ ] Set up alerts

---

## 🔗 Useful Resources

### Tools
- [Prettier Playground](https://prettier.io/playground/)
- [ESLint Config Generator](https://eslint.org/docs/latest/use/configure/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [CodeRabbit](https://www.coderabbit.ai/)
- [Playwright Documentation](https://playwright.dev/)
- [Supabase Documentation](https://supabase.com/docs)

### Guides
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

---

**Last Updated:** 2025-10-17
**Maintained By:** Development Team
**License:** Use freely for all projects
