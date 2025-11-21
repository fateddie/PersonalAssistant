# Week 1: Storage Optimization - Detailed Plan

**Goal**: Remove email body storage, implement on-demand fetching via Gmail API

**Timeline**: 8-12 hours

**Outcome**: 95% storage reduction, no functionality lost

---

## Day 1: Gmail API Setup (2-3 hours)

### 1.1: Google Cloud Console Setup
**Time**: 30 minutes

**Steps**:
1. Go to https://console.cloud.google.com
2. Create new project or select existing "AskSharon"
3. Enable Gmail API:
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "AskSharon Email Assistant"
   - Download credentials JSON → save as `credentials.json`

**OAuth Scopes Needed**:
```
https://www.googleapis.com/auth/gmail.readonly    # Read emails
https://www.googleapis.com/auth/gmail.modify      # Archive, mark read
https://www.googleapis.com/auth/gmail.send        # Send replies (Week 3)
```

**Output**: `credentials.json` file

---

### 1.2: Install Dependencies
**Time**: 10 minutes

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Add to `requirements.txt`:
```
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
```

---

### 1.3: Environment Configuration
**Time**: 15 minutes

Add to `.env`:
```bash
# Gmail API
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/gmail.send
```

Add to `assistant_api/app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields

    # Gmail API
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"
    gmail_scopes: str = "https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify"

    @property
    def gmail_scopes_list(self) -> List[str]:
        return self.gmail_scopes.split(",")
```

---

### 1.4: Test Authentication
**Time**: 30 minutes

Create test script: `scripts/test_gmail_auth.py`
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate():
    """Test Gmail authentication"""
    creds = None

    # Load existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Test API
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    print(f"✅ Authentication successful! Found {len(messages)} recent emails")
    return service

if __name__ == '__main__':
    authenticate()
```

**Run**:
```bash
python scripts/test_gmail_auth.py
```

**Expected**: Browser opens for OAuth consent, then "Authentication successful"

---

## Day 2: Create GmailClient (3-4 hours)

### 2.1: Module Structure
**Time**: 15 minutes

Create directory structure:
```bash
mkdir -p assistant/modules/email_assistant
touch assistant/modules/email_assistant/__init__.py
touch assistant/modules/email_assistant/gmail_client.py
touch assistant/modules/email_assistant/rate_limiter.py
```

---

### 2.2: Rate Limiter Implementation
**Time**: 30 minutes

Create `assistant/modules/email_assistant/rate_limiter.py`:
```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_calls: int = 100, period: int = 60):
        """
        Args:
            max_calls: Maximum calls allowed per period
            period: Time period in seconds (default 60 = 1 minute)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = Lock()

    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        with self.lock:
            now = time.time()

            # Remove calls older than period
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # If at limit, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.period - now
                if sleep_time > 0:
                    print(f"⏳ Rate limit: waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    self.calls.popleft()

            # Record this call
            self.calls.append(time.time())
```

---

### 2.3: GmailClient Core Implementation
**Time**: 2-3 hours

Create `assistant/modules/email_assistant/gmail_client.py`:
```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import os
from typing import Dict, List, Optional
from datetime import datetime
from .rate_limiter import RateLimiter

class GmailClient:
    """Gmail API wrapper with authentication, rate limiting, error handling"""

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        self.service = self._authenticate()
        self.rate_limiter = RateLimiter(max_calls=100, period=60)

    def _authenticate(self):
        """Authenticate and return Gmail service"""
        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def fetch_email_body(self, message_id: str) -> Dict:
        """
        Fetch full email body on-demand

        Returns: {
            'body_text': str,
            'body_html': str,
            'subject': str,
            'from': str,
            'date': datetime
        }
        """
        self.rate_limiter.wait_if_needed()

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Parse headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            # Extract body
            body_text = ''
            body_html = ''

            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif part['mimeType'] == 'text/html':
                        body_html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            else:
                # Single-part message
                if 'data' in message['payload']['body']:
                    body_text = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            return {
                'body_text': body_text,
                'body_html': body_html,
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'date': datetime.fromtimestamp(int(message['internalDate']) / 1000)
            }

        except HttpError as e:
            print(f"❌ Error fetching email {message_id}: {e}")
            raise

    def list_emails(self, query: str = '', max_results: int = 50) -> List[Dict]:
        """
        List emails matching query

        Args:
            query: Gmail search query (e.g., "from:example@gmail.com")
            max_results: Maximum emails to return

        Returns: List of email metadata (no body)
        """
        self.rate_limiter.wait_if_needed()

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Fetch metadata for each
            emails = []
            for msg in messages:
                metadata = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in metadata['payload']['headers']}

                emails.append({
                    'id': msg['id'],
                    'thread_id': msg['threadId'],
                    'subject': headers.get('Subject', ''),
                    'from': headers.get('From', ''),
                    'date': headers.get('Date', '')
                })

            return emails

        except HttpError as e:
            print(f"❌ Error listing emails: {e}")
            raise

    def archive(self, message_id: str) -> bool:
        """Archive email (remove INBOX label)"""
        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True

        except HttpError as e:
            print(f"❌ Error archiving email {message_id}: {e}")
            return False

    def mark_read(self, message_id: str) -> bool:
        """Mark email as read (remove UNREAD label)"""
        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True

        except HttpError as e:
            print(f"❌ Error marking read {message_id}: {e}")
            return False

    def mark_unread(self, message_id: str) -> bool:
        """Mark email as unread (add UNREAD label)"""
        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True

        except HttpError as e:
            print(f"❌ Error marking unread {message_id}: {e}")
            return False

    def star(self, message_id: str) -> bool:
        """Star email (add STARRED label)"""
        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['STARRED']}
            ).execute()
            return True

        except HttpError as e:
            print(f"❌ Error starring {message_id}: {e}")
            return False
```

---

### 2.4: Unit Tests
**Time**: 30 minutes

Create `tests/test_gmail_client.py`:
```python
import pytest
from assistant.modules.email_assistant.gmail_client import GmailClient

@pytest.fixture
def client():
    return GmailClient()

def test_authentication(client):
    """Test Gmail service is authenticated"""
    assert client.service is not None

def test_list_emails(client):
    """Test listing emails"""
    emails = client.list_emails(query='', max_results=5)
    assert len(emails) <= 5
    assert all('id' in email for email in emails)

def test_fetch_email_body(client):
    """Test fetching full email"""
    # Get first email ID
    emails = client.list_emails(max_results=1)
    if not emails:
        pytest.skip("No emails in inbox")

    email_id = emails[0]['id']
    body = client.fetch_email_body(email_id)

    assert 'body_text' in body or 'body_html' in body
    assert 'subject' in body

def test_rate_limiter():
    """Test rate limiter"""
    from assistant.modules.email_assistant.rate_limiter import RateLimiter
    import time

    limiter = RateLimiter(max_calls=3, period=2)

    # First 3 calls should be instant
    for _ in range(3):
        start = time.time()
        limiter.wait_if_needed()
        assert time.time() - start < 0.1

    # 4th call should wait
    start = time.time()
    limiter.wait_if_needed()
    assert time.time() - start >= 1.9  # Wait ~2 seconds
```

**Run tests**:
```bash
pytest tests/test_gmail_client.py -v
```

---

## Day 3: Database Migration (2-3 hours)

### 3.1: Plan Migration
**Time**: 30 minutes

**Current schema** (emails table):
```sql
CREATE TABLE emails (
    email_id TEXT PRIMARY KEY,
    thread_id TEXT,
    message_id TEXT,
    subject TEXT,
    sender TEXT,
    body_text TEXT,      -- ❌ Remove (avg 6KB)
    body_html TEXT,      -- ❌ Remove (avg 6KB)
    date TIMESTAMP,
    url TEXT,
    priority TEXT,
    fetched_at TIMESTAMP
);
```

**New schema**:
```sql
CREATE TABLE emails (
    email_id TEXT PRIMARY KEY,
    thread_id TEXT,
    message_id TEXT UNIQUE,
    gmail_url TEXT NOT NULL,    -- ✅ Add

    -- Metadata only
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    summary TEXT,               -- ✅ Add (AI-generated, 200 chars)

    -- Classifications
    priority TEXT,
    category TEXT,              -- ✅ Add ('newsletter', 'receipt', etc.)
    has_attachment BOOLEAN DEFAULT FALSE,  -- ✅ Add

    -- Timestamps
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP     -- ✅ Add (for lazy processing)
);
```

---

### 3.2: Create Migration Script
**Time**: 1 hour

Create `scripts/migrate_emails_week1.py`:
```python
"""
Week 1 Migration: Remove email bodies, add metadata
"""
import sqlite3
from datetime import datetime
from urllib.parse import quote

OLD_DB = "assistant/data/memory.db"

def migrate():
    conn = sqlite3.connect(OLD_DB)
    cursor = conn.cursor()

    print("=" * 60)
    print("WEEK 1 MIGRATION: Storage Optimization")
    print("=" * 60)

    # 1. Measure storage before
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    size_before = cursor.fetchone()[0]
    print(f"\n📊 DB size before: {size_before / 1024:.2f} KB")

    # 2. Create new schema
    print("\n🔧 Creating new schema...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails_new (
            email_id TEXT PRIMARY KEY,
            thread_id TEXT,
            message_id TEXT UNIQUE,
            gmail_url TEXT NOT NULL,

            subject TEXT NOT NULL,
            sender TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            summary TEXT,

            priority TEXT,
            category TEXT,
            has_attachment BOOLEAN DEFAULT FALSE,

            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP
        )
    """)

    # 3. Migrate data (without body_text, body_html)
    print("📦 Migrating data...")

    cursor.execute("SELECT email_id, thread_id, message_id, subject, sender, date, url, priority, fetched_at FROM emails")
    old_emails = cursor.fetchall()

    migrated = 0
    for email in old_emails:
        email_id, thread_id, message_id, subject, sender, date, url, priority, fetched_at = email

        # Build Gmail URL if missing
        if not url:
            if message_id:
                encoded_id = quote(message_id.strip("<>"), safe='')
                url = f"https://mail.google.com/mail/u/0/#search/rfc822msgid:{encoded_id}"
            else:
                url = "https://mail.google.com/mail/u/0/#inbox"  # Fallback

        # Auto-categorize based on sender
        category = None
        if 'newsletter' in sender.lower() or 'news' in sender.lower():
            category = 'newsletter'
        elif 'receipt' in subject.lower() or 'invoice' in subject.lower():
            category = 'receipt'

        cursor.execute("""
            INSERT INTO emails_new (
                email_id, thread_id, message_id, gmail_url,
                subject, sender, date, priority, category, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email_id, thread_id, message_id, url, subject, sender, date, priority, category, fetched_at))

        migrated += 1

    # 4. Replace old table
    cursor.execute("DROP TABLE emails")
    cursor.execute("ALTER TABLE emails_new RENAME TO emails")

    # 5. Create indexes
    print("🔍 Creating indexes...")
    cursor.execute("CREATE INDEX idx_emails_sender ON emails(sender)")
    cursor.execute("CREATE INDEX idx_emails_date ON emails(date)")
    cursor.execute("CREATE INDEX idx_emails_category ON emails(category)")

    conn.commit()

    # 6. Measure storage after
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    size_after = cursor.fetchone()[0]

    # 7. Vacuum to reclaim space
    print("🧹 Vacuuming database...")
    conn.execute("VACUUM")

    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    size_final = cursor.fetchone()[0]

    # Summary
    reduction = (size_before - size_final) / size_before * 100

    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"  Emails migrated: {migrated}")
    print(f"  Size before:     {size_before / 1024:.2f} KB")
    print(f"  Size after:      {size_final / 1024:.2f} KB")
    print(f"  Reduction:       {reduction:.1f}%")
    print("=" * 60)
    print("\n✅ Migration complete!")

    conn.close()

if __name__ == '__main__':
    migrate()
```

---

### 3.3: Test Migration
**Time**: 30 minutes

```bash
# Backup database first
cp assistant/data/memory.db assistant/data/memory.db.backup

# Run migration
python scripts/migrate_emails_week1.py

# Expected output:
# ✅ Migration complete!
# Emails migrated: 100
# Size before: 1200.00 KB
# Size after: 120.00 KB
# Reduction: 90.0%
```

---

### 3.4: Update API Models
**Time**: 30 minutes

Update `assistant_api/app/models.py`:
```python
class Email(Base):
    __tablename__ = "emails"

    email_id = Column(String, primary_key=True)
    thread_id = Column(String, nullable=True)
    message_id = Column(String, unique=True, nullable=True)
    gmail_url = Column(String, nullable=False)  # ✅ Added

    # Metadata only (no body_text, body_html)
    subject = Column(String(500), nullable=False)
    sender = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    summary = Column(String(200), nullable=True)  # ✅ Added

    # Classifications
    priority = Column(String(10), nullable=True)
    category = Column(String(50), nullable=True)  # ✅ Added
    has_attachment = Column(Boolean, default=False)  # ✅ Added

    # Timestamps
    fetched_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)  # ✅ Added
```

---

## Day 4: Update UI & Test (2-3 hours)

### 4.1: Add On-Demand Fetch to API
**Time**: 45 minutes

Create new endpoint in `assistant_api/app/routers/emails.py`:
```python
from assistant.modules.email_assistant.gmail_client import GmailClient

gmail_client = GmailClient()

@router.get("/{email_id}/body")
def fetch_email_body(email_id: str, db: Session = Depends(get_db)):
    """
    Fetch full email body on-demand from Gmail

    Returns: {
        'body_text': str,
        'body_html': str,
        'subject': str,
        'from': str
    }
    """
    # Update last_accessed timestamp
    email = db.query(models.Email).filter(models.Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.last_accessed = datetime.utcnow()
    db.commit()

    # Fetch from Gmail
    try:
        body = gmail_client.fetch_email_body(email_id)
        return body
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {e}")
```

---

### 4.2: Update Streamlit UI
**Time**: 1 hour

Update `assistant/modules/voice/main.py`:

**Add to render_item_card()** for email items:
```python
def render_item_card(item, key_prefix=""):
    # ... existing code

    # For email items, add fetch body button
    if item['type'] == 'email' or item.get('gmail_url'):
        with col4:
            if st.button("📧 View Full", key=f"{key_prefix}_view_full_{item['id']}"):
                st.session_state[f"viewing_full_{item['id']}"] = True
                st.rerun()

        # Show full email if requested
        if st.session_state.get(f"viewing_full_{item['id']}", False):
            with st.expander("Full Email", expanded=True):
                with st.spinner("Fetching from Gmail..."):
                    try:
                        body = client.fetch_email_body(item['id'])

                        st.markdown(f"**From:** {body['from']}")
                        st.markdown(f"**Subject:** {body['subject']}")
                        st.markdown(f"**Date:** {body['date']}")
                        st.divider()

                        # Show body (prefer HTML over plain text)
                        if body.get('body_html'):
                            st.markdown(body['body_html'], unsafe_allow_html=True)
                        else:
                            st.text(body.get('body_text', 'No content'))

                        if st.button("Close", key=f"{key_prefix}_close_{item['id']}"):
                            st.session_state[f"viewing_full_{item['id']}"] = False
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error fetching email: {e}")
```

**Add to API client** (`assistant/core/api_client.py`):
```python
def fetch_email_body(self, email_id: str) -> Dict:
    """Fetch full email body on-demand"""
    response = requests.get(f"{self.base_url}/emails/{email_id}/body")
    response.raise_for_status()
    return response.json()
```

---

### 4.3: Test End-to-End
**Time**: 1 hour

**Test Checklist**:
- [ ] UI loads without errors
- [ ] Email summaries display correctly
- [ ] Gmail links open correct emails
- [ ] "View Full" button fetches email body < 2 seconds
- [ ] Fetched email displays correctly (HTML + text)
- [ ] Close button works
- [ ] last_accessed timestamp updates in DB

**Run**:
```bash
# Start API
uvicorn assistant_api.app.main:app --port 8002 --reload

# Start Streamlit
streamlit run assistant/modules/voice/main.py --server.port 8501
```

---

## Acceptance Test (Run at end of Week 1)

Run acceptance tests from `planning/phase_6_gmail_assistant/acceptance_tests.md`:

- [ ] Test 1.1: Database Size Reduction (≥ 90%)
- [ ] Test 1.2: Gmail URL Correctness (10/10 correct)
- [ ] Test 1.3: On-Demand Fetch Speed (< 2 seconds)
- [ ] Test 1.4: No Functionality Lost (8/8 features work)

---

## Deliverables

1. ✅ Gmail API authenticated
2. ✅ GmailClient implemented with rate limiting
3. ✅ Database migrated (body columns removed)
4. ✅ On-demand fetch API endpoint
5. ✅ UI updated with "View Full" button
6. ✅ 90%+ storage reduction
7. ✅ All tests pass

---

## Rollback Plan

If migration fails:
```bash
# Restore backup
cp assistant/data/memory.db.backup assistant/data/memory.db

# Revert code changes
git checkout assistant_api/app/models.py
git checkout assistant/modules/voice/main.py
```
