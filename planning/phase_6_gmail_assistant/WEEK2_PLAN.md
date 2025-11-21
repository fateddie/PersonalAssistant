# Week 2: Natural Language Commands - Detailed Plan

**Goal**: Enable natural language command parsing and safe Gmail actions with human-in-loop approval

**Timeline**: 10-15 hours

**Outcome**: 90%+ command accuracy, confirmation flow working

---

## Day 1: CommandParser Implementation (4-5 hours)

### 1.1: Define Function Schema
**Time**: 1 hour

Create `assistant/modules/email_assistant/schemas/command_functions.py`:
```python
"""
OpenAI function calling schemas for email commands
"""

COMMAND_FUNCTIONS = [
    {
        "name": "search_emails",
        "description": "Search emails by sender, subject, or keywords. No confirmation needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'from:john@example.com', 'subject:meeting')"
                },
                "sender": {
                    "type": "string",
                    "description": "Filter by sender email or domain"
                },
                "subject_contains": {
                    "type": "string",
                    "description": "Filter by words in subject"
                },
                "date_after": {
                    "type": "string",
                    "description": "Date filter (YYYY-MM-DD)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "archive_emails",
        "description": "Archive emails (remove from inbox). Requires confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of email IDs to archive"
                },
                "sender": {
                    "type": "string",
                    "description": "Archive all emails from this sender"
                }
            }
        }
    },
    {
        "name": "mark_read",
        "description": "Mark emails as read. Requires confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "sender": {
                    "type": "string",
                    "description": "Mark all emails from this sender as read"
                }
            }
        }
    },
    {
        "name": "mark_unread",
        "description": "Mark emails as unread. Requires confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["email_ids"]
        }
    },
    {
        "name": "star_emails",
        "description": "Star emails for later. Requires confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["email_ids"]
        }
    },
    {
        "name": "delete_emails",
        "description": "Move emails to trash. Requires confirmation. Use with caution.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["email_ids"]
        }
    }
]

# Action classification
SAFE_ACTIONS = ["search_emails"]  # No confirmation needed
DESTRUCTIVE_ACTIONS = ["delete_emails"]  # Extra warning
```

---

### 1.2: Implement CommandParser
**Time**: 2-3 hours

Create `assistant/modules/email_assistant/command_parser.py`:
```python
"""
Natural language command parser using OpenAI function calling
"""
import openai
import os
from typing import Dict, Optional, List
from .schemas.command_functions import COMMAND_FUNCTIONS, SAFE_ACTIONS, DESTRUCTIVE_ACTIONS

class CommandParser:
    """Parse natural language commands into structured actions"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def parse_command(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Convert natural language to structured action

        Args:
            user_input: Natural language command (e.g., "archive all from beehiiv")
            context: Optional context (selected emails, current view, etc.)

        Returns: {
            "action": "archive_emails",
            "parameters": {"sender": "beehiiv.com"},
            "confidence": 0.95,
            "needs_confirmation": True,
            "is_destructive": False,
            "user_command": "archive all from beehiiv"
        }
        """
        # Build system message
        system_prompt = """You are an email assistant that understands Gmail commands.
Convert user requests into structured function calls.

Guidelines:
- Be flexible with terminology (e.g., "get rid of" = archive, "trash" = delete)
- Infer intent from context
- Default to safe actions when ambiguous
- Extract sender domains from partial names (e.g., "beehiiv" → "beehiiv.com")
"""

        # Add context if provided
        if context:
            system_prompt += f"\n\nContext: {context}"

        try:
            # Call OpenAI with function calling
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                functions=COMMAND_FUNCTIONS,
                function_call="auto",
                temperature=0.1  # Low temperature for consistency
            )

            message = response["choices"][0]["message"]

            # Check if function was called
            if "function_call" not in message:
                return {
                    "action": None,
                    "error": "Could not understand command",
                    "suggestion": "Try being more specific (e.g., 'archive emails from sender')"
                }

            function_name = message["function_call"]["name"]
            parameters = eval(message["function_call"]["arguments"])  # JSON string → dict

            # Calculate confidence (simple heuristic)
            confidence = 0.9 if len(parameters) > 1 else 0.7

            # Determine if confirmation needed
            needs_confirmation = function_name not in SAFE_ACTIONS
            is_destructive = function_name in DESTRUCTIVE_ACTIONS

            return {
                "action": function_name,
                "parameters": parameters,
                "confidence": confidence,
                "needs_confirmation": needs_confirmation,
                "is_destructive": is_destructive,
                "user_command": user_input
            }

        except Exception as e:
            return {
                "action": None,
                "error": str(e),
                "suggestion": "Please try again or rephrase your command"
            }

    def suggest_corrections(self, user_input: str, failed_action: Dict) -> List[str]:
        """
        If action fails, suggest alternatives

        Example:
        Input: "unsubscribe from beehiiv"
        Failed: No List-Unsubscribe header
        Output: ["Archive all emails from beehiiv", "Block sender beehiiv"]
        """
        # Use OpenAI to generate suggestions
        prompt = f"""
The user tried: "{user_input}"
But the action failed with: {failed_action.get('error', 'Unknown error')}

Suggest 2-3 alternative actions that might help.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )

            suggestions = response["choices"][0]["message"]["content"].strip().split("\n")
            return [s.strip("- ").strip() for s in suggestions if s.strip()]

        except:
            # Fallback suggestions
            return [
                "Try archiving these emails instead",
                "Create a filter to automatically delete future emails",
                "Search for similar emails and batch delete"
            ]
```

---

### 1.3: Unit Tests
**Time**: 1 hour

Create `tests/test_command_parser.py`:
```python
import pytest
from assistant.modules.email_assistant.command_parser import CommandParser

@pytest.fixture
def parser():
    return CommandParser()

def test_parse_archive_command(parser):
    """Test: 'archive all from beehiiv'"""
    result = parser.parse_command("archive all from beehiiv")

    assert result["action"] == "archive_emails"
    assert "beehiiv" in result["parameters"]["sender"].lower()
    assert result["needs_confirmation"] == True
    assert result["confidence"] > 0.7

def test_parse_search_command(parser):
    """Test: 'show me emails from john'"""
    result = parser.parse_command("show me emails from john")

    assert result["action"] == "search_emails"
    assert "john" in result["parameters"]["query"].lower()
    assert result["needs_confirmation"] == False

def test_parse_mark_read(parser):
    """Test: 'mark as read'"""
    # With context (selected email)
    context = {"selected_email_ids": ["abc123"]}
    result = parser.parse_command("mark as read", context=context)

    assert result["action"] == "mark_read"
    assert result["needs_confirmation"] == True

def test_parse_ambiguous_command(parser):
    """Test: 'get rid of these' (ambiguous - archive or delete?)"""
    result = parser.parse_command("get rid of these")

    # Should default to safer action (archive > delete)
    assert result["action"] in ["archive_emails", "delete_emails"]

def test_parse_invalid_command(parser):
    """Test: 'make me a sandwich'"""
    result = parser.parse_command("make me a sandwich")

    assert result["action"] is None
    assert "error" in result
    assert "suggestion" in result
```

**Run tests**:
```bash
pytest tests/test_command_parser.py -v
```

---

## Day 2: Pending Actions & Approval System (3-4 hours)

### 2.1: Create pending_email_actions Table
**Time**: 30 minutes

Add to `assistant_api/app/models.py`:
```python
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class PendingEmailAction(Base):
    __tablename__ = "pending_email_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = Column(String, ForeignKey("emails.email_id"), nullable=True)  # Null if batch action

    # Action details
    action_type = Column(String(50), nullable=False)  # archive, mark_read, delete, etc.
    user_command = Column(Text, nullable=False)
    parsed_parameters = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # pending, approved, rejected, executed
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Results
    error_message = Column(Text, nullable=True)
    affected_count = Column(Integer, default=0)  # How many emails affected

    # Relationship
    email = relationship("Email", backref="pending_actions")
```

Run migration:
```bash
# Create migration
alembic revision --autogenerate -m "Add pending_email_actions table"

# Apply
alembic upgrade head
```

---

### 2.2: Create CRUD Operations
**Time**: 45 minutes

Add to `assistant_api/app/crud.py`:
```python
from .models import PendingEmailAction
import json

def create_pending_action(
    db: Session,
    action_type: str,
    user_command: str,
    parameters: Dict,
    confidence: float,
    email_ids: List[str] = None
) -> PendingEmailAction:
    """Create pending action awaiting approval"""
    action = PendingEmailAction(
        action_type=action_type,
        user_command=user_command,
        parsed_parameters=json.dumps(parameters),
        confidence=confidence,
        affected_count=len(email_ids) if email_ids else 0
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

def get_pending_actions(
    db: Session,
    status: str = "pending",
    limit: int = 50
) -> List[PendingEmailAction]:
    """Get pending actions"""
    query = db.query(PendingEmailAction)

    if status:
        query = query.filter(PendingEmailAction.status == status)

    return query.order_by(PendingEmailAction.created_at.desc()).limit(limit).all()

def approve_action(db: Session, action_id: str) -> PendingEmailAction:
    """Approve pending action (ready for execution)"""
    action = db.query(PendingEmailAction).filter(PendingEmailAction.id == action_id).first()
    if not action:
        return None

    action.status = "approved"
    action.approved_at = datetime.utcnow()
    db.commit()
    return action

def reject_action(db: Session, action_id: str, reason: str = None):
    """Reject pending action"""
    action = db.query(PendingEmailAction).filter(PendingEmailAction.id == action_id).first()
    if not action:
        return None

    action.status = "rejected"
    if reason:
        action.error_message = reason
    db.commit()
    return action

def mark_action_executed(
    db: Session,
    action_id: str,
    success: bool,
    error_message: str = None,
    affected_count: int = 0
):
    """Mark action as executed"""
    action = db.query(PendingEmailAction).filter(PendingEmailAction.id == action_id).first()
    if not action:
        return None

    action.status = "executed" if success else "failed"
    action.executed_at = datetime.utcnow()
    action.affected_count = affected_count
    if error_message:
        action.error_message = error_message
    db.commit()
    return action
```

---

### 2.3: Create API Endpoints
**Time**: 1 hour

Create `assistant_api/app/routers/email_actions.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from ..db import get_db
from .. import crud, schemas
from assistant.modules.email_assistant.command_parser import CommandParser
from assistant.modules.email_assistant.gmail_client import GmailClient

router = APIRouter(prefix="/email", tags=["email_actions"])

parser = CommandParser()
gmail_client = GmailClient()

@router.post("/parse-command")
def parse_email_command(
    command: str,
    context: Dict = None,
    db: Session = Depends(get_db)
):
    """
    Parse natural language command

    Returns: {
        "action": "archive_emails",
        "parameters": {...},
        "confidence": 0.95,
        "needs_confirmation": true
    }
    """
    result = parser.parse_command(command, context)

    # If action needs confirmation, create pending action
    if result.get("needs_confirmation"):
        pending = crud.create_pending_action(
            db=db,
            action_type=result["action"],
            user_command=command,
            parameters=result["parameters"],
            confidence=result["confidence"]
        )
        result["pending_action_id"] = pending.id

    return result

@router.get("/pending-actions")
def list_pending_actions(
    status: str = "pending",
    db: Session = Depends(get_db)
):
    """Get actions awaiting approval"""
    actions = crud.get_pending_actions(db, status=status)
    return {"actions": actions, "total": len(actions)}

@router.post("/approve-action/{action_id}")
def approve_and_execute_action(
    action_id: str,
    db: Session = Depends(get_db)
):
    """
    Approve and execute pending action

    Steps:
    1. Mark action as approved
    2. Execute via GmailClient
    3. Mark as executed
    4. Return results
    """
    # Approve
    action = crud.approve_action(db, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Execute
    try:
        parameters = json.loads(action.parsed_parameters)

        if action.action_type == "archive_emails":
            if "email_ids" in parameters:
                for email_id in parameters["email_ids"]:
                    gmail_client.archive(email_id)
                affected_count = len(parameters["email_ids"])
            elif "sender" in parameters:
                # Find all emails from sender and archive
                emails = gmail_client.list_emails(query=f"from:{parameters['sender']}", max_results=100)
                for email in emails:
                    gmail_client.archive(email["id"])
                affected_count = len(emails)

        elif action.action_type == "mark_read":
            for email_id in parameters.get("email_ids", []):
                gmail_client.mark_read(email_id)
            affected_count = len(parameters.get("email_ids", []))

        # ... handle other action types

        # Mark as executed
        crud.mark_action_executed(db, action_id, success=True, affected_count=affected_count)

        return {
            "success": True,
            "message": f"Action executed successfully",
            "affected_count": affected_count
        }

    except Exception as e:
        # Mark as failed
        crud.mark_action_executed(db, action_id, success=False, error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reject-action/{action_id}")
def reject_action(action_id: str, reason: str = None, db: Session = Depends(get_db)):
    """Reject pending action"""
    action = crud.reject_action(db, action_id, reason)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    return {"success": True, "message": "Action rejected"}
```

Add to `assistant_api/app/main.py`:
```python
from .routers import email_actions

app.include_router(email_actions.router)
```

---

### 2.4: Test API Endpoints
**Time**: 30 minutes

```bash
# Test parse command
curl -X POST "http://localhost:8002/email/parse-command" \
  -H "Content-Type: application/json" \
  -d '{"command": "archive all from beehiiv"}'

# Expected response:
{
  "action": "archive_emails",
  "parameters": {"sender": "beehiiv.com"},
  "confidence": 0.95,
  "needs_confirmation": true,
  "pending_action_id": "abc-123"
}

# Test list pending
curl "http://localhost:8002/email/pending-actions"

# Test approve
curl -X POST "http://localhost:8002/email/approve-action/abc-123"
```

---

## Day 3: Approval UI in Streamlit (3-4 hours)

### 3.1: Create ApprovalUI Component
**Time**: 2 hours

Create `assistant/modules/voice/components/approval_ui.py`:
```python
"""
Streamlit component for action approval
"""
import streamlit as st
from typing import Dict, List

def render_approval_card(pending_action: Dict, api_client) -> str:
    """
    Render approval card for pending action

    Returns: "approved", "rejected", or "pending"
    """
    with st.container():
        # Header
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### 🔔 Action Requires Approval")
            st.markdown(f"**Command:** \"{pending_action['user_command']}\"")

        with col2:
            # Confidence badge
            confidence = pending_action.get('confidence', 0)
            color = "green" if confidence > 0.9 else "orange" if confidence > 0.7 else "red"
            st.markdown(f"<span style='background:{color};color:white;padding:0.25rem 0.5rem;border-radius:0.25rem'>{confidence:.0%} confident</span>", unsafe_allow_html=True)

        st.divider()

        # Action details
        st.markdown(f"**Action:** {pending_action['action_type']}")
        st.json(pending_action['parsed_parameters'])

        # Preview affected emails (if applicable)
        if 'email_ids' in pending_action['parsed_parameters']:
            email_ids = pending_action['parsed_parameters']['email_ids']
            st.caption(f"Will affect {len(email_ids)} email(s)")

            with st.expander("Preview affected emails"):
                for email_id in email_ids[:10]:  # Show first 10
                    try:
                        email = api_client.get_item(email_id)
                        st.markdown(f"- **{email['subject']}** from {email['sender']}")
                    except:
                        st.markdown(f"- {email_id}")

                if len(email_ids) > 10:
                    st.caption(f"... and {len(email_ids) - 10} more")

        elif 'sender' in pending_action['parsed_parameters']:
            sender = pending_action['parsed_parameters']['sender']
            st.caption(f"Will affect all emails from: **{sender}**")

            # Search for preview
            with st.expander("Preview affected emails"):
                with st.spinner("Searching..."):
                    try:
                        result = api_client.list_items(search=sender, limit=10)
                        for email in result['items']:
                            st.markdown(f"- **{email['title']}** ({email['date']})")

                        if result['total'] > 10:
                            st.caption(f"... and {result['total'] - 10} more")
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Warning for destructive actions
        if pending_action.get('is_destructive'):
            st.warning("⚠️ This action is destructive and cannot be undone easily!")

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Approve", key=f"approve_{pending_action['id']}", type="primary"):
                return "approved"

        with col2:
            if st.button("❌ Reject", key=f"reject_{pending_action['id']}"):
                return "rejected"

        with col3:
            if st.button("✏️ Edit", key=f"edit_{pending_action['id']}"):
                # TODO: Show edit form
                st.info("Edit functionality coming soon")

    return "pending"


def render_pending_actions_sidebar(api_client):
    """Render pending actions in sidebar"""
    try:
        result = api_client.list_pending_actions()
        pending = [a for a in result['actions'] if a['status'] == 'pending']

        if pending:
            st.sidebar.markdown(f"### 🔔 Pending Actions ({len(pending)})")

            for action in pending:
                with st.sidebar.expander(f"{action['action_type']}", expanded=True):
                    st.caption(action['user_command'])

                    col1, col2 = st.sidebar.columns(2)
                    with col1:
                        if st.button("✅", key=f"sidebar_approve_{action['id']}"):
                            # Trigger main approval flow
                            st.session_state[f"show_approval_{action['id']}"] = True
                            st.rerun()

                    with col2:
                        if st.button("❌", key=f"sidebar_reject_{action['id']}"):
                            api_client.reject_action(action['id'])
                            st.success("Action rejected")
                            st.rerun()

    except Exception as e:
        st.sidebar.error(f"Error loading pending actions: {e}")
```

---

### 3.2: Integrate with Main UI
**Time**: 1 hour

Update `assistant/modules/voice/main.py`:
```python
from components.approval_ui import render_approval_card, render_pending_actions_sidebar

# Add to sidebar
with st.sidebar:
    # ... existing sidebar code
    st.divider()
    render_pending_actions_sidebar(client)

# Add new tab for command input
tabs = st.tabs([" 📅 Today", "📆 Upcoming", "✅ All Items", "🤖 Commands", "➕ Add New"])

# ... existing tabs

# Commands tab
with tabs[3]:
    st.header("Email Commands")

    st.markdown("""
    Try natural language commands like:
    - "archive all emails from beehiiv"
    - "mark emails from john as read"
    - "show me emails about project X"
    - "star important emails from yesterday"
    """)

    # Command input
    command = st.text_input("Enter command:", placeholder="archive all from...")

    if st.button("Execute") and command:
        with st.spinner("Parsing command..."):
            try:
                result = client.parse_email_command(command)

                if result.get("action") is None:
                    st.error(f"❌ {result.get('error', 'Could not understand command')}")
                    if result.get("suggestion"):
                        st.info(f"💡 {result['suggestion']}")

                elif result.get("needs_confirmation"):
                    st.success("✅ Command understood!")

                    # Show approval card
                    action_id = result["pending_action_id"]
                    pending_action = client.get_pending_action(action_id)

                    decision = render_approval_card(pending_action, client)

                    if decision == "approved":
                        with st.spinner("Executing..."):
                            exec_result = client.approve_and_execute_action(action_id)
                            st.success(f"✅ {exec_result['message']}")
                            st.balloons()
                            st.rerun()

                    elif decision == "rejected":
                        client.reject_action(action_id)
                        st.warning("Action cancelled")

                else:
                    # Safe action, execute immediately
                    st.success("✅ Executing safe action...")
                    # TODO: Execute safe action

            except Exception as e:
                st.error(f"Error: {e}")
```

---

### 3.3: Update API Client
**Time**: 30 minutes

Add to `assistant/core/api_client.py`:
```python
def parse_email_command(self, command: str, context: Dict = None) -> Dict:
    """Parse natural language command"""
    response = requests.post(
        f"{self.base_url}/email/parse-command",
        params={"command": command},
        json=context or {}
    )
    response.raise_for_status()
    return response.json()

def list_pending_actions(self, status: str = "pending") -> Dict:
    """List pending actions"""
    response = requests.get(
        f"{self.base_url}/email/pending-actions",
        params={"status": status}
    )
    response.raise_for_status()
    return response.json()

def get_pending_action(self, action_id: str) -> Dict:
    """Get single pending action"""
    response = requests.get(f"{self.base_url}/email/pending-actions/{action_id}")
    response.raise_for_status()
    return response.json()

def approve_and_execute_action(self, action_id: str) -> Dict:
    """Approve and execute action"""
    response = requests.post(f"{self.base_url}/email/approve-action/{action_id}")
    response.raise_for_status()
    return response.json()

def reject_action(self, action_id: str, reason: str = None) -> Dict:
    """Reject action"""
    response = requests.post(
        f"{self.base_url}/email/reject-action/{action_id}",
        params={"reason": reason} if reason else {}
    )
    response.raise_for_status()
    return response.json()
```

---

## Day 4: Testing & Polish (2-3 hours)

### 4.1: End-to-End Testing
**Time**: 1 hour

Test all command types:
```python
# Test commands
test_commands = [
    "archive all from beehiiv",
    "mark emails from john as read",
    "show me emails about meeting",
    "star important emails",
    "delete emails older than 30 days",
]

for cmd in test_commands:
    print(f"\nTesting: {cmd}")
    result = client.parse_email_command(cmd)
    print(f"  Action: {result['action']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Needs confirmation: {result['needs_confirmation']}")
```

---

### 4.2: Acceptance Tests
**Time**: 1 hour

Run tests from `acceptance_tests.md` Week 2:
- [ ] Test 2.1: Command Parsing Accuracy (45/50 = 90%)
- [ ] Test 2.2: Confirmation Flow
- [ ] Test 2.3: Undo Functionality
- [ ] Test 2.4: Batch Actions

---

### 4.3: Polish & Documentation
**Time**: 1 hour

- [ ] Add loading spinners
- [ ] Add success/error notifications
- [ ] Write user guide for commands
- [ ] Document common commands

---

## Deliverables

1. ✅ CommandParser with OpenAI function calling
2. ✅ pending_email_actions table and CRUD
3. ✅ API endpoints for parse/approve/reject
4. ✅ Approval UI component in Streamlit
5. ✅ Commands tab in UI
6. ✅ 90%+ command accuracy
7. ✅ Confirmation flow working
8. ✅ All tests pass
