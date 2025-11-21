# Phase 6: Technical Architecture

## System Overview
```
┌─────────────────┐
│   Streamlit UI  │  Natural language input
└────────┬────────┘
         │
         v
┌─────────────────┐
│ CommandParser   │  OpenAI function calling
│ (AI layer)      │  Intent → Structured action
└────────┬────────┘
         │
         v
┌─────────────────┐
│ ApprovalUI      │  Human-in-loop
│ (safety layer)  │  Confirm/reject actions
└────────┬────────┘
         │
         v
┌─────────────────┐
│ GmailClient     │  Gmail API wrapper
│ (execution)     │  Perform actions
└────────┬────────┘
         │
         v
┌─────────────────┐
│ PatternLearner  │  Track + suggest
│ (intelligence)  │  User behavior patterns
└─────────────────┘
```

## Database Schema Changes

### New: emails_minimal table (replaces emails)
```sql
CREATE TABLE emails_minimal (
    email_id TEXT PRIMARY KEY,
    thread_id TEXT,
    message_id TEXT UNIQUE,  -- RFC822 Message-ID
    gmail_url TEXT NOT NULL,

    -- Metadata only
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    summary TEXT,  -- AI-generated (200 chars max)

    -- No body_text, body_html (90% storage savings)

    -- Classifications
    priority TEXT,  -- 'high', 'med', 'low'
    category TEXT,  -- 'newsletter', 'receipt', 'personal', etc.
    has_attachment BOOLEAN DEFAULT FALSE,

    -- Timestamps
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,

    INDEX idx_sender (sender),
    INDEX idx_date (date),
    INDEX idx_category (category)
);
```

### New: email_patterns table
```sql
CREATE TABLE email_patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,  -- 'sender', 'subject_keyword', 'time_of_day'
    pattern_value TEXT NOT NULL,

    -- Learning data
    suggested_action TEXT,  -- 'archive', 'unsubscribe', 'priority'
    confidence FLOAT DEFAULT 0.0,
    times_seen INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,

    -- Auto-action threshold
    auto_apply BOOLEAN DEFAULT FALSE,  -- True if confidence > 0.95 and confirmed > 10

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    UNIQUE(pattern_type, pattern_value)
);
```

### New: pending_email_actions table
```sql
CREATE TABLE pending_email_actions (
    id TEXT PRIMARY KEY,
    email_id TEXT NOT NULL,
    action_type TEXT NOT NULL,  -- 'unsubscribe', 'reply', 'archive', etc.

    -- Context
    user_command TEXT NOT NULL,  -- Original natural language input
    parsed_parameters JSON,      -- Structured action data
    confidence FLOAT,

    -- Status
    status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'executed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    executed_at TIMESTAMP,

    -- Results
    error_message TEXT,

    FOREIGN KEY (email_id) REFERENCES emails_minimal(email_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
);
```

## Component Specifications

### 1. GmailClient (assistant/modules/email_assistant/gmail_client.py)
```python
class GmailClient:
    """Gmail API wrapper with OAuth, rate limiting, error handling"""

    def __init__(self):
        self.service = self._authenticate()
        self.rate_limiter = RateLimiter(max_calls=100, period=60)

    # Core operations
    def fetch_email_body(self, message_id: str) -> Dict
    def list_emails(self, query: str, max_results: int) -> List[Dict]
    def send_email(self, to: str, subject: str, body: str) -> str
    def reply_to_email(self, message_id: str, reply_body: str) -> str

    # Actions
    def archive(self, message_id: str) -> bool
    def mark_read(self, message_id: str) -> bool
    def mark_unread(self, message_id: str) -> bool
    def star(self, message_id: str) -> bool
    def delete(self, message_id: str) -> bool
    def move_to_trash(self, message_id: str) -> bool

    # Advanced
    def unsubscribe(self, message_id: str) -> bool  # Uses List-Unsubscribe header
    def batch_modify(self, message_ids: List[str], labels_to_add: List, labels_to_remove: List) -> bool
```

### 2. CommandParser (assistant/modules/email_assistant/command_parser.py)
```python
class CommandParser:
    """Natural language → structured action using OpenAI function calling"""

    FUNCTIONS = [
        {
            "name": "unsubscribe",
            "description": "Unsubscribe from mailing list",
            "parameters": {
                "type": "object",
                "properties": {
                    "sender": {"type": "string"},
                    "email_id": {"type": "string"}
                }
            }
        },
        # ... other actions
    ]

    def parse_command(self, user_input: str, context: Dict = None) -> Dict:
        """
        Convert natural language to structured action

        Input: "unsubscribe from beehiiv newsletters"
        Output: {
            "action": "unsubscribe",
            "parameters": {"sender": "beehiiv.com"},
            "confidence": 0.95,
            "needs_confirmation": True,
            "suggested_filters": ["from:mail.beehiiv.com"]
        }
        """
        pass

    def suggest_corrections(self, user_input: str, failed_action: Dict) -> List[str]:
        """If action fails, suggest alternatives"""
        pass
```

### 3. PatternLearner (assistant/modules/email_assistant/pattern_learner.py)
```python
class PatternLearner:
    """Learn from user behavior, suggest actions"""

    def record_action(self, email: Dict, action: str, confirmed: bool):
        """Track user confirmation/rejection of suggested actions"""
        pattern = self._extract_pattern(email)
        self._update_confidence(pattern, action, confirmed)

    def suggest_action(self, email: Dict) -> Optional[Dict]:
        """
        Based on patterns, suggest action

        Returns: {
            "action": "archive",
            "reason": "You always archive emails from this sender",
            "confidence": 0.87,
            "times_confirmed": 12
        }
        """
        pass

    def get_auto_actions(self) -> List[Dict]:
        """Get patterns with confidence > 0.95 for auto-execution"""
        pass
```

### 4. ApprovalUI (assistant/modules/voice/components/approval_ui.py)
```python
def render_approval_card(pending_action: Dict) -> bool:
    """
    Streamlit component for action approval

    Shows:
    - Natural language command
    - Parsed action details
    - Affected emails (with previews)
    - Confidence score
    - Pattern match (if learning)

    Returns: True if approved, False if rejected
    """
    with st.container():
        st.markdown(f"**Command:** {pending_action['user_command']}")
        st.caption(f"Confidence: {pending_action['confidence']:.0%}")

        # Preview affected emails
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Approve"):
                return True
        with col2:
            if st.button("❌ Reject"):
                return False
        with col3:
            if st.button("✏️ Edit"):
                # Show edit form
                pass
```

## Event Bus Integration

### Published Events
```python
# When email action is executed
publish("email.action.executed", {
    "action_type": "unsubscribe",
    "email_id": "abc123",
    "sender": "newsletter@example.com",
    "timestamp": datetime.now()
})

# When pattern is learned
publish("email.pattern.learned", {
    "pattern_type": "sender",
    "pattern_value": "beehiiv.com",
    "suggested_action": "archive",
    "confidence": 0.92
})
```

### Subscribed Events
```python
# Listen for calendar events to detect travel emails
subscribe("calendar.event.created", handle_travel_email_detection)

# Listen for task completion to archive related emails
subscribe("task.completed", handle_task_email_archival)
```

## API Endpoints (Extend existing FastAPI)

### New routes in assistant_api/app/routers/email_actions.py
```python
@router.post("/email/parse-command")
def parse_email_command(command: str, context: Optional[Dict] = None):
    """Parse natural language command"""
    pass

@router.get("/email/pending-actions")
def list_pending_actions(status: str = "pending"):
    """Get actions awaiting approval"""
    pass

@router.post("/email/approve-action/{action_id}")
def approve_action(action_id: str):
    """Approve and execute pending action"""
    pass

@router.post("/email/reject-action/{action_id}")
def reject_action(action_id: str):
    """Reject pending action"""
    pass

@router.get("/email/patterns")
def get_learned_patterns():
    """Get all learned patterns"""
    pass

@router.get("/email/fetch/{message_id}")
def fetch_email_body(message_id: str):
    """On-demand email body fetch from Gmail"""
    pass
```

## Storage Optimization Flow

### Before (Current)
```
Email received → Store full body_text + body_html (avg 12KB per email)
User opens UI → Display from local DB
```

### After (Optimized)
```
Email received → Store metadata only (avg 0.6KB per email)
                 + AI summary (200 chars)
                 + gmail_url link

User opens UI → Display summary + "View full email" button
User clicks → Fetch from Gmail API on-demand
             Cache for 15 minutes
```

**Savings**: 95% storage reduction (12KB → 0.6KB per email)

## Cost Optimization Strategy

### Batch Processing
```python
# Before: 1 AI call per email
for email in emails:
    classify(email)  # $0.002 per call
# Cost: 100 emails × $0.002 = $0.20

# After: 1 AI call for 20 emails
batch = emails[:20]
classify_batch(batch)  # $0.02 per call
# Cost: 100 emails / 20 × $0.02 = $0.10 (50% savings)
```

### Smart Caching
```python
# Check cache before AI processing
if sender in known_patterns and confidence > 0.95:
    return cached_classification  # $0.00
else:
    classification = ai_classify(email)  # $0.002
    cache_result(sender, classification)
```

### Lazy Processing
```python
# Don't process unless user interacts
if email.days_since_received > 7 and not email.accessed:
    skip_processing()  # User likely won't read it
```

**Expected Monthly Cost**:
- Before: 3000 emails × $0.002 = $6.00
- After: 250 AI calls × $0.002 = $0.50 (92% reduction)

## Safety Measures

### 1. Confirmation System
- All destructive actions (delete, unsubscribe) require explicit approval
- Show preview of affected emails
- Allow undo within 30 seconds

### 2. Undo Buffer
```python
class ActionUndoBuffer:
    """30-second window to undo actions"""

    def __init__(self):
        self.buffer = []  # [(action, timestamp, undo_data)]

    def undo_last_action(self):
        """Reverse most recent action"""
        pass
```

### 3. Audit Trail
All actions logged with:
- Timestamp
- User command
- Parsed action
- Affected emails
- Result (success/failure)
- User who approved

### 4. Rate Limiting
- Max 100 Gmail API calls per minute
- Max 10 AI command parses per minute
- Exponential backoff on errors

## Testing Strategy

### Unit Tests
```python
def test_command_parser_unsubscribe():
    parser = CommandParser()
    result = parser.parse_command("unsubscribe from beehiiv")
    assert result["action"] == "unsubscribe"
    assert "beehiiv" in result["parameters"]["sender"]
    assert result["confidence"] > 0.8

def test_pattern_learner_confidence():
    learner = PatternLearner()
    # Record 10 confirmed actions
    for _ in range(10):
        learner.record_action(email_from_sender_x, "archive", confirmed=True)

    suggestion = learner.suggest_action(email_from_sender_x)
    assert suggestion["action"] == "archive"
    assert suggestion["confidence"] > 0.9
```

### Integration Tests
```python
def test_end_to_end_unsubscribe():
    # 1. User enters command
    command = "unsubscribe from all beehiiv newsletters"

    # 2. Command is parsed
    action = parse_command(command)

    # 3. User approves
    approve_action(action["id"])

    # 4. Action is executed
    result = execute_action(action["id"])
    assert result["status"] == "success"

    # 5. Verify Gmail state
    emails = gmail_client.list_emails("from:beehiiv.com", max_results=10)
    assert all(email["unsubscribed"] for email in emails)
```

### Acceptance Tests
See acceptance_tests.md for full list per week
