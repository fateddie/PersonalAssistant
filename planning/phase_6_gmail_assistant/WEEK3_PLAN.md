# Week 3: Advanced Actions & Pattern Learning - Detailed Plan

**Goal**: Implement advanced Gmail actions (unsubscribe, reply, send) + pattern learning for intelligent suggestions

**Timeline**: 12-18 hours

**Outcome**: All Gmail functions working, system learns from user behavior, past item filtering implemented

---

## Day 1-2: Advanced Gmail Actions (5-7 hours)

### 1.1: Unsubscribe Implementation
**Time**: 2 hours

Add to `assistant/modules/email_assistant/gmail_client.py`:
```python
def unsubscribe(self, message_id: str) -> Dict:
    """
    Unsubscribe from mailing list using List-Unsubscribe header

    Returns: {
        "success": bool,
        "method": "link" | "email" | "none",
        "message": str
    }
    """
    self.rate_limiter.wait_if_needed()

    try:
        # Fetch email to get headers
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Check for List-Unsubscribe header
        unsubscribe_header = headers.get('List-Unsubscribe')

        if not unsubscribe_header:
            return {
                "success": False,
                "method": "none",
                "message": "No unsubscribe option available for this email"
            }

        # Parse header (can be URL or mailto)
        # Format: "<http://example.com/unsub>, <mailto:unsub@example.com>"
        import re

        # Try URL first (preferred)
        url_match = re.search(r'<(https?://[^>]+)>', unsubscribe_header)
        if url_match:
            unsub_url = url_match.group(1)

            # Open unsubscribe URL
            import webbrowser
            webbrowser.open(unsub_url)

            return {
                "success": True,
                "method": "link",
                "message": f"Opened unsubscribe link: {unsub_url}",
                "url": unsub_url
            }

        # Try mailto
        mailto_match = re.search(r'<mailto:([^>]+)>', unsubscribe_header)
        if mailto_match:
            mailto_addr = mailto_match.group(1)

            # Send unsubscribe email
            self.send_email(
                to=mailto_addr,
                subject="Unsubscribe",
                body="Please unsubscribe me from this mailing list."
            )

            return {
                "success": True,
                "method": "email",
                "message": f"Sent unsubscribe request to {mailto_addr}"
            }

        return {
            "success": False,
            "method": "none",
            "message": "Could not parse unsubscribe header"
        }

    except HttpError as e:
        return {
            "success": False,
            "method": "none",
            "message": f"Error: {e}"
        }


def get_unsubscribe_info(self, message_id: str) -> Optional[str]:
    """Get unsubscribe information without executing"""
    # Same logic as unsubscribe() but just returns info
    pass
```

Add function schema to `command_functions.py`:
```python
{
    "name": "unsubscribe_from_list",
    "description": "Unsubscribe from mailing list. Requires confirmation.",
    "parameters": {
        "type": "object",
        "properties": {
            "email_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Email IDs to unsubscribe from"
            },
            "sender": {
                "type": "string",
                "description": "Unsubscribe from all emails from this sender"
            }
        }
    }
}
```

**Test**:
```bash
pytest tests/test_gmail_unsubscribe.py -v
```

---

### 1.2: Reply Implementation
**Time**: 2-3 hours

Add to `gmail_client.py`:
```python
def reply_to_email(
    self,
    message_id: str,
    reply_body: str,
    include_original: bool = True
) -> Dict:
    """
    Reply to email

    Args:
        message_id: ID of email to reply to
        reply_body: Reply message
        include_original: Include original message in reply

    Returns: {
        "success": bool,
        "message_id": str (new message ID),
        "thread_id": str
    }
    """
    self.rate_limiter.wait_if_needed()

    try:
        # Get original message
        original = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in original['payload']['headers']}

        # Extract details
        to = headers.get('From')  # Reply to sender
        subject = headers.get('Subject', '')
        thread_id = original['threadId']

        # Add "Re:" if not already there
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"

        # Build reply message
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(reply_body)
        message['to'] = to
        message['subject'] = subject
        message['In-Reply-To'] = headers.get('Message-ID')
        message['References'] = headers.get('Message-ID')

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send reply
        result = self.service.users().messages().send(
            userId='me',
            body={
                'raw': raw,
                'threadId': thread_id
            }
        ).execute()

        return {
            "success": True,
            "message_id": result['id'],
            "thread_id": result['threadId'],
            "message": f"Reply sent successfully"
        }

    except HttpError as e:
        return {
            "success": False,
            "message": f"Error sending reply: {e}"
        }


def draft_reply(
    self,
    message_id: str,
    intent: str
) -> str:
    """
    Use AI to draft reply based on intent

    Args:
        message_id: Email to reply to
        intent: User's intent (e.g., "say I'll attend", "politely decline")

    Returns: Drafted reply text
    """
    # Fetch original email
    email = self.fetch_email_body(message_id)

    # Use OpenAI to draft reply
    import openai

    prompt = f"""
Original email:
From: {email['from']}
Subject: {email['subject']}
Body: {email['body_text'][:500]}

Draft a reply with this intent: {intent}

Keep it professional, concise, and friendly.
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )

    return response["choices"][0]["message"]["content"].strip()
```

Add function schema:
```python
{
    "name": "reply_to_email",
    "description": "Reply to an email. AI will draft reply based on your intent. Requires confirmation.",
    "parameters": {
        "type": "object",
        "properties": {
            "email_id": {
                "type": "string",
                "description": "Email to reply to"
            },
            "intent": {
                "type": "string",
                "description": "What you want to say (e.g., 'confirm meeting', 'decline invitation')"
            },
            "draft_only": {
                "type": "boolean",
                "description": "If true, just draft reply without sending"
            }
        },
        "required": ["email_id", "intent"]
    }
}
```

**Test**:
```python
def test_reply_to_email(gmail_client):
    # Get first email
    emails = gmail_client.list_emails(max_results=1)
    email_id = emails[0]['id']

    # Draft reply
    draft = gmail_client.draft_reply(email_id, "say thanks")
    assert len(draft) > 10
    assert "thank" in draft.lower()

    # Send reply (only in test environment)
    # result = gmail_client.reply_to_email(email_id, draft)
    # assert result["success"] == True
```

---

### 1.3: Send New Email Implementation
**Time**: 1 hour

Add to `gmail_client.py`:
```python
def send_email(
    self,
    to: str,
    subject: str,
    body: str,
    cc: List[str] = None,
    bcc: List[str] = None
) -> Dict:
    """Send new email"""
    self.rate_limiter.wait_if_needed()

    try:
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        result = self.service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        return {
            "success": True,
            "message_id": result['id'],
            "message": "Email sent successfully"
        }

    except HttpError as e:
        return {
            "success": False,
            "message": f"Error: {e}"
        }
```

---

### 1.4: Batch Operations
**Time**: 1-2 hours

Add to `gmail_client.py`:
```python
def batch_modify(
    self,
    message_ids: List[str],
    add_labels: List[str] = None,
    remove_labels: List[str] = None
) -> Dict:
    """
    Batch modify multiple emails

    Args:
        message_ids: List of email IDs (max 1000)
        add_labels: Label IDs to add (e.g., ['STARRED'])
        remove_labels: Label IDs to remove (e.g., ['INBOX'])

    Returns: {
        "success": int (count),
        "failed": int (count),
        "errors": List[str]
    }
    """
    self.rate_limiter.wait_if_needed()

    if len(message_ids) > 1000:
        return {
            "success": 0,
            "failed": len(message_ids),
            "errors": ["Batch size exceeds 1000"]
        }

    try:
        body = {
            'ids': message_ids
        }
        if add_labels:
            body['addLabelIds'] = add_labels
        if remove_labels:
            body['removeLabelIds'] = remove_labels

        self.service.users().messages().batchModify(
            userId='me',
            body=body
        ).execute()

        return {
            "success": len(message_ids),
            "failed": 0,
            "errors": []
        }

    except HttpError as e:
        return {
            "success": 0,
            "failed": len(message_ids),
            "errors": [str(e)]
        }


def archive_all_from_sender(self, sender: str, max_emails: int = 100) -> Dict:
    """Archive all emails from sender (wrapper for batch operation)"""
    # List emails
    emails = self.list_emails(query=f"from:{sender}", max_results=max_emails)
    email_ids = [e['id'] for e in emails]

    if not email_ids:
        return {"success": 0, "message": "No emails found"}

    # Batch archive
    result = self.batch_modify(email_ids, remove_labels=['INBOX'])
    result['sender'] = sender
    return result
```

---

## Day 3: Pattern Learning System (4-5 hours)

### 3.1: Create email_patterns Table
**Time**: 30 minutes

Add to `assistant_api/app/models.py`:
```python
class EmailPattern(Base):
    __tablename__ = "email_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_type = Column(String(50), nullable=False)  # sender, subject_keyword, time_of_day
    pattern_value = Column(String(255), nullable=False)

    # Learning data
    suggested_action = Column(String(50), nullable=False)  # archive, unsubscribe, mark_read
    confidence = Column(Float, default=0.0)
    times_seen = Column(Integer, default=0)
    times_confirmed = Column(Integer, default=0)
    times_rejected = Column(Integer, default=0)

    # Auto-action
    auto_apply = Column(Boolean, default=False)  # True if confidence > 0.95 and confirmed > 10

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('pattern_type', 'pattern_value', name='uix_pattern'),
    )
```

Run migration:
```bash
alembic revision --autogenerate -m "Add email_patterns table"
alembic upgrade head
```

---

### 3.2: Implement PatternLearner
**Time**: 3-4 hours

Create `assistant/modules/email_assistant/pattern_learner.py`:
```python
"""
Pattern learning for intelligent email suggestions
"""
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from assistant_api.app.models import EmailPattern
from datetime import datetime

class PatternLearner:
    """Learn from user behavior, suggest actions"""

    def __init__(self, db: Session):
        self.db = db

    def _extract_pattern(self, email: Dict) -> Dict:
        """
        Extract pattern from email

        Returns: {
            "type": "sender",
            "value": "beehiiv.com"
        }
        """
        # For now, use sender domain as primary pattern
        sender = email.get('sender', '')

        # Extract domain
        if '@' in sender:
            domain = sender.split('@')[1].split('>')[0]  # Handle "Name <email@domain.com>"
        else:
            domain = sender

        return {
            "type": "sender",
            "value": domain
        }

    def record_action(
        self,
        email: Dict,
        action: str,
        confirmed: bool
    ):
        """
        Track user confirmation/rejection of suggested actions

        Args:
            email: Email dict with sender, subject, etc.
            action: Action taken (archive, mark_read, etc.)
            confirmed: True if user approved, False if rejected
        """
        pattern = self._extract_pattern(email)

        # Find or create pattern
        existing = self.db.query(EmailPattern).filter(
            EmailPattern.pattern_type == pattern["type"],
            EmailPattern.pattern_value == pattern["value"],
            EmailPattern.suggested_action == action
        ).first()

        if existing:
            # Update existing pattern
            existing.times_seen += 1
            if confirmed:
                existing.times_confirmed += 1
            else:
                existing.times_rejected += 1

            # Recalculate confidence
            existing.confidence = existing.times_confirmed / existing.times_seen

            # Enable auto-apply if high confidence
            if existing.confidence >= 0.95 and existing.times_confirmed >= 10:
                existing.auto_apply = True

            existing.updated_at = datetime.utcnow()

        else:
            # Create new pattern
            new_pattern = EmailPattern(
                pattern_type=pattern["type"],
                pattern_value=pattern["value"],
                suggested_action=action,
                times_seen=1,
                times_confirmed=1 if confirmed else 0,
                times_rejected=0 if confirmed else 1,
                confidence=1.0 if confirmed else 0.0
            )
            self.db.add(new_pattern)

        self.db.commit()

    def suggest_action(self, email: Dict) -> Optional[Dict]:
        """
        Based on patterns, suggest action

        Returns: {
            "action": "archive",
            "reason": "You always archive emails from this sender",
            "confidence": 0.87,
            "times_confirmed": 12,
            "auto_apply": False
        } or None if no pattern
        """
        pattern = self._extract_pattern(email)

        # Find best matching pattern
        patterns = self.db.query(EmailPattern).filter(
            EmailPattern.pattern_type == pattern["type"],
            EmailPattern.pattern_value == pattern["value"]
        ).order_by(EmailPattern.confidence.desc()).all()

        if not patterns:
            return None

        # Return highest confidence pattern
        best = patterns[0]

        if best.confidence < 0.5:
            return None  # Not confident enough

        return {
            "action": best.suggested_action,
            "reason": self._generate_reason(best),
            "confidence": best.confidence,
            "times_confirmed": best.times_confirmed,
            "auto_apply": best.auto_apply
        }

    def _generate_reason(self, pattern: EmailPattern) -> str:
        """Generate human-readable reason"""
        if pattern.times_confirmed >= 10:
            return f"You always {pattern.suggested_action} emails from {pattern.pattern_value}"
        elif pattern.times_confirmed >= 5:
            return f"You usually {pattern.suggested_action} emails from {pattern.pattern_value}"
        else:
            return f"You've {pattern.suggested_action}d emails from {pattern.pattern_value} before"

    def get_auto_actions(self) -> List[EmailPattern]:
        """Get patterns with auto_apply enabled"""
        return self.db.query(EmailPattern).filter(
            EmailPattern.auto_apply == True
        ).all()

    def get_all_patterns(self, min_confidence: float = 0.5) -> List[EmailPattern]:
        """Get all learned patterns"""
        return self.db.query(EmailPattern).filter(
            EmailPattern.confidence >= min_confidence
        ).order_by(EmailPattern.confidence.desc()).all()

    def delete_pattern(self, pattern_id: str):
        """Delete learned pattern"""
        pattern = self.db.query(EmailPattern).filter(EmailPattern.id == pattern_id).first()
        if pattern:
            self.db.delete(pattern)
            self.db.commit()

    def disable_auto_apply(self, pattern_id: str):
        """Disable auto-apply for pattern"""
        pattern = self.db.query(EmailPattern).filter(EmailPattern.id == pattern_id).first()
        if pattern:
            pattern.auto_apply = False
            self.db.commit()
```

---

### 3.3: Integrate with API
**Time**: 1 hour

Add to `assistant_api/app/routers/email_actions.py`:
```python
from assistant.modules.email_assistant.pattern_learner import PatternLearner

@router.get("/suggestions/{email_id}")
def get_email_suggestions(
    email_id: str,
    db: Session = Depends(get_db)
):
    """Get suggested actions for email based on learned patterns"""
    # Get email
    email = db.query(models.Email).filter(models.Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Get suggestion
    learner = PatternLearner(db)
    suggestion = learner.suggest_action({
        "sender": email.sender,
        "subject": email.subject
    })

    return suggestion or {"message": "No suggestions available"}

@router.post("/record-action")
def record_user_action(
    email_id: str,
    action: str,
    confirmed: bool,
    db: Session = Depends(get_db)
):
    """Record user action for pattern learning"""
    email = db.query(models.Email).filter(models.Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    learner = PatternLearner(db)
    learner.record_action(
        email={"sender": email.sender, "subject": email.subject},
        action=action,
        confirmed=confirmed
    )

    return {"success": True, "message": "Action recorded"}

@router.get("/patterns")
def list_learned_patterns(
    min_confidence: float = 0.5,
    db: Session = Depends(get_db)
):
    """Get all learned patterns"""
    learner = PatternLearner(db)
    patterns = learner.get_all_patterns(min_confidence=min_confidence)

    return {
        "patterns": patterns,
        "total": len(patterns)
    }

@router.delete("/patterns/{pattern_id}")
def delete_pattern(pattern_id: str, db: Session = Depends(get_db)):
    """Delete learned pattern"""
    learner = PatternLearner(db)
    learner.delete_pattern(pattern_id)
    return {"success": True, "message": "Pattern deleted"}
```

---

## Day 4: Past Item Filtering & UI Integration (3-5 hours)

### 4.1: Implement Past Item Filtering
**Time**: 1 hour

Update `assistant_api/app/crud.py`:
```python
def get_items(
    db: Session,
    type_filter: List[str] = None,
    status: str = None,
    hide_past_low_priority: bool = True,  # ✅ New parameter
    ...
) -> Tuple[List[models.AssistantItem], int]:
    """Get items with filtering"""
    from datetime import date

    query = db.query(models.AssistantItem)

    # ... existing filters

    # Past item filtering rule:
    # Hide items that are: (1) in the past AND (2) LOW priority
    # Keep: HIGH/MEDIUM priority past items (bills, invoices)
    if hide_past_low_priority:
        today = date.today()
        query = query.filter(
            or_(
                models.AssistantItem.date >= today,  # Future/today items
                models.AssistantItem.priority.in_(['high', 'med', 'medium']),  # High priority past items
                models.AssistantItem.priority == None  # Unknown priority (keep for safety)
            )
        )

    # ... rest of function
```

Update API endpoint:
```python
@router.get("", response_model=schemas.ItemListResponse)
def list_items(
    hide_past_low_priority: bool = Query(True, description="Hide past low-priority items"),
    ...
):
    items, total = crud.get_items(
        db=db,
        hide_past_low_priority=hide_past_low_priority,
        ...
    )
    return {"items": items, "total": total}
```

---

### 4.2: Update Streamlit UI with Suggestions
**Time**: 2-3 hours

Update `render_item_card()` in `assistant/modules/voice/main.py`:
```python
def render_item_card(item, key_prefix=""):
    # ... existing code

    # For email items, show suggestions
    if item.get('source') == 'gmail' or item.get('gmail_url'):
        try:
            suggestion = client.get_email_suggestions(item['id'])

            if suggestion:
                with st.expander(f"💡 Suggested action: {suggestion['action']} ({suggestion['confidence']:.0%} confident)"):
                    st.caption(suggestion['reason'])

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(f"✅ {suggestion['action'].title()}", key=f"{key_prefix}_suggest_yes_{item['id']}"):
                            # Execute suggested action
                            if suggestion['action'] == 'archive':
                                gmail_client.archive(item['id'])
                            # ... other actions

                            # Record confirmation
                            client.record_user_action(item['id'], suggestion['action'], confirmed=True)

                            st.success(f"{suggestion['action'].title()}d!")
                            st.rerun()

                    with col2:
                        if st.button("❌ Not now", key=f"{key_prefix}_suggest_no_{item['id']}"):
                            # Record rejection
                            client.record_user_action(item['id'], suggestion['action'], confirmed=False)
                            st.info("Suggestion dismissed")
                            st.rerun()

        except:
            pass  # No suggestions available

    # ... rest of function
```

---

### 4.3: Add Patterns Management Page
**Time**: 1 hour

Add new tab to main UI:
```python
tabs = st.tabs(["📅 Today", "📆 Upcoming", "✅ All Items", "🤖 Commands", "🧠 Patterns", "➕ Add New"])

# ... existing tabs

# Patterns tab
with tabs[4]:
    st.header("🧠 Learned Patterns")

    st.markdown("""
    The assistant learns from your actions and suggests similar actions for future emails.
    """)

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        min_confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.5, 0.05)
    with col2:
        show_auto_only = st.checkbox("Show auto-apply only")

    # Get patterns
    try:
        result = client.list_learned_patterns(min_confidence=min_confidence)
        patterns = result['patterns']

        if show_auto_only:
            patterns = [p for p in patterns if p['auto_apply']]

        if not patterns:
            st.info("No patterns learned yet. The assistant will learn as you use it.")
        else:
            st.caption(f"Showing {len(patterns)} patterns")

            for pattern in patterns:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.markdown(f"**{pattern['pattern_value']}** → {pattern['suggested_action']}")
                        st.caption(f"Confirmed {pattern['times_confirmed']} times, Rejected {pattern['times_rejected']} times")

                    with col2:
                        # Confidence badge
                        confidence = pattern['confidence']
                        color = "green" if confidence > 0.9 else "orange"
                        st.markdown(f"<span style='background:{color};color:white;padding:0.25rem 0.5rem;border-radius:0.25rem'>{confidence:.0%}</span>", unsafe_allow_html=True)

                    with col3:
                        if pattern['auto_apply']:
                            st.success("Auto ✓")
                        else:
                            st.caption("Manual")

                    with col4:
                        if st.button("🗑️", key=f"delete_pattern_{pattern['id']}"):
                            client.delete_pattern(pattern['id'])
                            st.success("Pattern deleted")
                            st.rerun()

                    st.divider()

    except Exception as e:
        st.error(f"Error loading patterns: {e}")
```

---

### 4.4: Event Bus Integration
**Time**: 30 minutes

Add event publishing to action execution:
```python
from assistant.core.event_bus import publish

# In approve_and_execute_action()
if success:
    # Publish event
    publish("email.action.executed", {
        "action_type": action.action_type,
        "email_id": action.email_id,
        "sender": email.sender,
        "timestamp": datetime.utcnow()
    })

# In pattern learning
def record_action(...):
    # ... record pattern

    if new_pattern.auto_apply:
        publish("email.pattern.learned", {
            "pattern_type": pattern["type"],
            "pattern_value": pattern["value"],
            "suggested_action": action,
            "confidence": new_pattern.confidence
        })
```

---

## Acceptance Tests (Run at end of Week 3)

- [ ] Test 3.1: Unsubscribe Action
- [ ] Test 3.2: Reply Action
- [ ] Test 3.3: Pattern Learning - First Suggestion (after 5 confirmations)
- [ ] Test 3.4: Pattern Learning - Auto Action (after 10+ confirmations at 95%+ confidence)
- [ ] Test 3.5: Past Item Filtering (past LOW hidden, past HIGH visible)
- [ ] Test 3.6: Event Bus Integration

---

## Deliverables

1. ✅ Unsubscribe functionality (List-Unsubscribe header)
2. ✅ Reply functionality with AI drafting
3. ✅ Send new email functionality
4. ✅ Batch operations (archive all from sender)
5. ✅ PatternLearner implementation
6. ✅ Pattern storage and retrieval
7. ✅ Suggestion UI with confirm/reject
8. ✅ Patterns management page
9. ✅ Past item filtering (hide low-priority only)
10. ✅ Event bus integration
11. ✅ All tests pass
