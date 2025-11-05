# AskSharon.ai – Modular Personal Assistant Blueprint

**Internal package name:** `asksharon_ai_blueprint`
**Public brand:** AskSharon.ai

AskSharon.ai is a modular, voice-enabled personal assistant designed for **phase-gated**, **plug-in style** development. It manages email, tasks, routines, and behaviour — with persistent memory and a behavioural-psychology layer (adaptive goal reinforcement, conversational data elicitation, weekly reviews).

## 🎯 Core Characteristics

- ✅ **Automation** - One-command setup, automated testing, self-healing
- 🔔 **Notifications** - Proactive system events with clear communication
- 🛡️ **Error Handling** - Robust, structured, user-friendly error management
- 📝 **Decision Documentation** - Every technical choice logged with rationale

## 📁 Folder Structure

```
asksharon_ai_blueprint/
├── README.md
├── requirements.txt
├── docs/
│   ├── system_design_blueprint.md
│   ├── phase1_implementation_plan.md
│   └── architecture.puml
├── assistant/
│   ├── core/                  # orchestrator, scheduler, context manager
│   ├── modules/               # voice, memory, email, planner, BIL
│   ├── configs/module_registry.yaml
│   └── data/                  # schema.sql, seeds.json, memory.db (after init)
└── planning/
    ├── progress.yaml
    ├── phase_1_mvp/
    ├── phase_2_behaviour/
    ├── phase_3_planner/
    ├── phase_4_fitness/
    └── phase_5_expansion/
```

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/fateddie/asksharon_ai_blueprint.git
cd asksharon_ai_blueprint
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Configure environment
cp assistant/configs/.env.example .env
# Edit .env with your API keys

# 3. Run
uvicorn assistant.core.orchestrator:app --reload
streamlit run assistant/modules/voice/main.py
```

## 📋 Phase-Gated Workflow

1. Work only on the active phase in `/planning/<phase>/`
2. Build per `tasks.md`
3. Verify per `acceptance_tests.md`
4. Update `/planning/progress.yaml` before unlocking next phase

## 🧩 Module System

All modules follow the **register()** contract:

```python
def register(app, publish, subscribe):
    """Register module with orchestrator"""
    app.include_router(router, prefix="/module")
    subscribe("event_name", handle_event)
    publish("module_loaded", {"name": "module"})
```

## 📚 Documentation

- `.cursorrules` - 26 development rules (Python edition)
- `CLAUDE.md` - AI assistant context
- `principles.md` - Development philosophy
- `docs/RULES_DATABASE_PYTHON.md` - Comprehensive patterns
- `docs/AUTOMATION_STANDARDS.md` - Automation guidelines
- `docs/ERROR_HANDLING_GUIDE.md` - Error management
- `docs/NOTIFICATION_SYSTEM.md` - Notification patterns
- `docs/DECISIONS.md` - Technical decision log

## 🔧 Tech Stack

- **Backend:** FastAPI + uvicorn
- **Frontend:** Streamlit (voice-ready)
- **Database:** SQLite + FAISS (semantic)
- **AI:** OpenAI API
- **Testing:** pytest
- **Formatting:** Black + mypy

## 📦 Packaging

```bash
cd ..
zip -r asksharon_ai_blueprint.zip asksharon_ai_blueprint/
```

## 🤝 Contributing

Follow the 26 Rules in `.cursorrules` and document decisions in `docs/DECISIONS.md`.

## 📄 License

Private - For personal use and MVP development.

---

**Built with** phase-gated methodology, event-driven architecture, and behavioral intelligence.
