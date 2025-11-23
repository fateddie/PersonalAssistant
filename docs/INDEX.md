# AskSharon.ai Documentation Index

> **Book-style navigation for all project documentation**

---

## Table of Contents

### 📚 Quick Start
| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview and introduction |
| [Setup Guide](setup/SETUP_GUIDE.md) | Installation and configuration |
| [Developer Onboarding](DEVELOPER_ONBOARDING.md) | New developer guide |
| [Tutorial](TUTORIAL.md) | Step-by-step usage tutorial |

---

### 🎯 AI & Development Guidelines

> **Essential reading before making changes**

| Document | Description | Location |
|----------|-------------|----------|
| [Principles](../principles.md) | Core coaching principles (10 rules) | Root |
| [Claude Context](../claude.md) | AI session context and rules | Root |
| [27 Rules](../.cursorrules) | Development rules checklist | Root |
| [Engineering Guidelines](ENGINEERING_GUIDELINES.md) | Layered architecture rules | docs/ |
| [Rules Database](RULES_DATABASE.md) | 23 fundamental rules (Next.js focus) | docs/ |
| [AI Workflow](AI_WORKFLOW.md) | Plan → Implement → Self-review | docs/ |

---

### 🏗️ Architecture & Design

| Document | Description |
|----------|-------------|
| [System Design Blueprint](system_design_blueprint.md) | Full system architecture |
| [Architecture](ARCHITECTURE.md) | Component overview |
| [Future Refactor](FUTURE_REFACTOR.md) | Planned architectural changes |
| [Memory Architecture](../planning/phase_3.5_discipline/memory_architecture.md) | Memory system design |

---

### ✅ Testing Standards

| Document | Description |
|----------|-------------|
| [Testing Standards](TESTING_STANDARDS.md) | Unit test guidelines |
| [UI Testing Standards](UI_TESTING_STANDARDS.md) | Playwright E2E requirements |
| [E2E Tests README](../tests/e2e/README.md) | E2E test documentation |
| [Test Results](TEST_RESULTS.md) | Latest test outputs |

---

### 📅 Phase Planning

#### Active Phases
| Phase | Goal | Tasks | Acceptance |
|-------|------|-------|------------|
| [Phase 6: Gmail Assistant](../planning/phase_6_gmail_assistant/goal.md) | [Tasks](../planning/phase_6_gmail_assistant/tasks.md) | [Tests](../planning/phase_6_gmail_assistant/acceptance_tests.md) |
| [Phase 3.5: Discipline](../planning/phase_3.5_discipline/goal.md) | [Tasks](../planning/phase_3.5_discipline/tasks.md) | [Tests](../planning/phase_3.5_discipline/acceptance_tests.md) |

#### Completed Phases
| Phase | Goal | Status |
|-------|------|--------|
| [Phase 1: MVP](../planning/phase_1_mvp/goal.md) | Basic assistant | ✅ Complete |
| [Phase 2: Behaviour](../planning/phase_2_behaviour/goal.md) | BIL system | ✅ Complete |
| [Phase 3: Planner](../planning/phase_3_planner/goal.md) | Planning features | ✅ Complete |

#### Future Phases
| Phase | Goal |
|-------|------|
| [Phase 4: Fitness](../planning/phase_4_fitness/goal.md) | Health tracking |
| [Phase 5: Expansion](../planning/phase_5_expansion/goal.md) | Feature expansion |

---

### 🔧 Integration Guides

| Document | Description |
|----------|-------------|
| [Gmail Setup](GMAIL_SETUP.md) | Gmail API configuration |
| [Calendar Setup](CALENDAR_SETUP.md) | Google Calendar integration |
| [Calendar Integration Complete](CALENDAR_INTEGRATION_COMPLETE.md) | Calendar feature summary |
| [Memory Integration](MEMORY_INTEGRATION.md) | Memory system setup |
| [Memory Quickstart](MEMORY_QUICKSTART.md) | Quick memory guide |

---

### 📊 Progress & Decisions

| Document | Description |
|----------|-------------|
| [Decisions](DECISIONS.md) | Architecture Decision Records (ADRs) |
| [Progress](PROGRESS.md) | Overall project progress |
| [Progress Reports](PROGRESS_REPORTS.md) | Detailed progress updates |
| [Roadmap](ROADMAP.md) | Future development roadmap |
| [Project Status](PROJECT_STATUS.md) | Current status summary |

---

### 📁 Other Resources

| Document | Description |
|----------|-------------|
| [Implementation Guide](IMPLEMENTATION_GUIDE.md) | Implementation patterns |
| [Implementation Log](IMPLEMENTATION_LOG.md) | Change history |
| [Implementation Control Plan](IMPLEMENTATION_CONTROL_PLAN.md) | Control processes |
| [Voice Commands Guide](VOICE_COMMANDS_GUIDE.md) | Voice interface docs |
| [Deployment Guide](DEPLOYMENT_GUIDE.md) | Deployment instructions |
| [Scripts README](../scripts/README.md) | Script documentation |
| [Assistant API README](../assistant_api/README.md) | API documentation |
| [Prompt Templates](prompt_templates.md) | AI prompt templates |

---

## Document Hierarchy

```
Root (Session Start Files)
├── README.md              # Project intro
├── claude.md              # AI context (CLAUDE.md convention)
├── principles.md          # Core principles
└── .cursorrules           # 27 development rules

docs/
├── INDEX.md               # ← You are here
├── setup/                 # Setup guides
├── Architecture/          # System design
├── Testing/               # Test standards
├── Integrations/          # API setup guides
└── Progress/              # Tracking docs

planning/
├── phase_1_mvp/           # MVP planning
├── phase_2_behaviour/     # BIL planning
├── phase_3_planner/       # Planner planning
├── phase_3.5_discipline/  # Discipline system
├── phase_4_fitness/       # Fitness features
├── phase_5_expansion/     # Expansion planning
└── phase_6_gmail_assistant/ # Gmail features
```

---

## Quick Reference

### Before Making Changes
1. Read [principles.md](../principles.md)
2. Read [.cursorrules](../.cursorrules)
3. Check [ENGINEERING_GUIDELINES.md](ENGINEERING_GUIDELINES.md)

### Before Committing
Run the pre-commit checklist:
```bash
./scripts/pre-commit-check.sh
```

Or manually:
- [ ] `black assistant/` - Format code
- [ ] `mypy assistant/` - Type check
- [ ] `pytest tests/unit/` - Run tests
- [ ] `./scripts/check_file_sizes.sh` - Check line limits
- [ ] Update [DECISIONS.md](DECISIONS.md) if substantial

---

**Last Updated:** 2025-11-23
