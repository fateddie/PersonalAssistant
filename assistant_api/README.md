# Assistant API

Clean, unified REST API for managing appointments, meetings, tasks, and goals.

## Architecture

**Single Data Model**: All items stored in unified `assistant_items` table with:
- `type` enum: appointment | meeting | task | goal
- `status` enum: upcoming | in_progress | done | overdue
- `source` enum: manual | gmail | calendar

**Clean Separation**:
- FastAPI backend (this directory)
- Streamlit frontend (uses API client)
- Background sync services (Gmail/Calendar)

## Quick Start

### 1. Migrate Data

```bash
python scripts/migrate_to_unified_api.py
```

Migrates existing data from legacy tables → unified schema. Safe (preserves old DB).

### 2. Start API

```bash
uvicorn assistant_api.app.main:app --host 0.0.0.0 --port 8002 --reload
```

API runs on http://localhost:8002

### 3. Test API

```bash
python scripts/test_api.py
```

Runs comprehensive integration tests.

## API Endpoints

### Items

- `GET /items` - List with filters
  - Query params: `type`, `status`, `source`, `date_from`, `date_to`, `search`, `limit`, `offset`
  - Returns: `{"items": [...], "total": int}`

- `GET /items/{id}` - Get single item

- `POST /items` - Create item
  - Body: `AssistantItemCreate` schema

- `PATCH /items/{id}` - Update item (partial)
  - Body: `AssistantItemUpdate` schema

- `DELETE /items/{id}` - Delete item

### Stats

- `GET /stats/summary` - Dashboard statistics
  - Returns: counts by type, status, and today's items

### Health

- `GET /health` - API health check

## Using from Streamlit

```python
from assistant.modules.voice.api_client import AssistantAPIClient

client = AssistantAPIClient("http://localhost:8002")

# List today's tasks
from datetime import date
result = client.list_items(
    type=["task"],
    date_from=date.today(),
    status="upcoming"
)

# Create new item
item = client.create_item({
    "type": "task",
    "title": "Complete project",
    "date": "2025-11-20",
    "status": "upcoming",
    "priority": "high"
})

# Update item
client.update_item(item['id'], {"status": "done"})

# Delete item
client.delete_item(item['id'])
```

## Database

**Location**: `assistant_api.db` (SQLite)

**Schema**: See `app/models.py` for full schema

**Migration**: Old DB preserved at `assistant/data/memory.db`

## Next Steps

1. ✅ Unified API complete
2. ✅ Data migration working
3. ✅ API client ready
4. 🔄 Refactor Streamlit UI to use API
5. 🔄 Add background Gmail/Calendar sync services
6. 🔄 Add authentication/authorization
7. 🔄 Deploy to production

## Structure

```
assistant_api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings
│   ├── db.py            # Database connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   └── routers/
│       ├── items.py     # Item endpoints
│       └── stats.py     # Stats endpoints
└── README.md            # This file
```

## Notes

- API uses port 8002 (8000 taken by old orchestrator)
- CORS enabled for Streamlit integration
- Participants stored as comma-separated in DB, converted to/from lists in API
- Times stored as TIME in DB, converted to "HH:MM" strings in API
- UUID primary keys for all items
- Automatic timestamps (created_at, updated_at)
