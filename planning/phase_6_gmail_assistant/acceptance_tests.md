# Phase 6: Acceptance Tests

## Week 1: Storage Optimization

### Test 1.1: Database Size Reduction
**Objective**: Verify 90%+ storage reduction after migration

**Steps**:
1. Measure DB size before migration: `ls -lh assistant/data/memory.db`
2. Run migration: `python scripts/migrate_emails_week1.py`
3. Measure DB size after migration: `ls -lh assistant/data/memory.db`
4. Calculate reduction: `(before - after) / before × 100%`

**Pass Criteria**:
- Storage reduced by ≥ 90%
- Example: 1.2MB → 0.12MB or less

---

### Test 1.2: Gmail URL Correctness
**Objective**: Verify gmail_url opens specific emails

**Steps**:
1. Get 10 random emails from database
2. Copy gmail_url for each
3. Open each URL in browser
4. Verify it opens the correct specific email (not just Gmail inbox)

**Pass Criteria**:
- 10/10 URLs open correct email
- No URLs open generic inbox

---

### Test 1.3: On-Demand Fetch Speed
**Objective**: Verify fetching full email body is fast enough

**Steps**:
1. Click "View full email" button in UI
2. Measure time from click to display
3. Repeat for 10 different emails
4. Calculate average time

**Pass Criteria**:
- Average fetch time < 2 seconds
- No timeouts or errors
- Email body displays correctly with formatting

---

### Test 1.4: No Functionality Lost
**Objective**: Verify all features still work after migration

**Steps**:
1. List all emails in UI ✓
2. Search emails by sender ✓
3. Search emails by subject ✓
4. Filter by date range ✓
5. View email summary ✓
6. Click through to Gmail ✓
7. Edit email item ✓
8. Delete email item ✓

**Pass Criteria**:
- All 8 features work without errors
- Data matches pre-migration state

---

## Week 2: Natural Language Commands

### Test 2.1: Command Parsing Accuracy
**Objective**: Verify 90%+ accuracy in understanding commands

**Test Commands** (50 total, sample below):
```
Archive:
- "archive this email"
- "move to archive"
- "get rid of this"

Unsubscribe:
- "unsubscribe from beehiiv"
- "stop getting these newsletters"
- "I don't want emails from this sender"

Mark Read:
- "mark as read"
- "mark all from sender as read"
- "I've read these"

Search:
- "show me emails from john"
- "find emails about project X"
- "emails from last week"

Reply:
- "reply to this saying thanks"
- "respond with meeting confirmed"
- "tell them I'll be there"
```

**Steps**:
1. Enter each command in natural language input box
2. Check parsed action matches intent
3. Verify confidence score
4. Count correct interpretations

**Pass Criteria**:
- ≥ 45/50 commands parsed correctly (90%)
- Confidence scores > 0.8 for correct parses
- No crashes or errors

---

### Test 2.2: Confirmation Flow
**Objective**: Verify approval UI works for all action types

**Steps**:
1. Enter command that needs confirmation (e.g., "archive all from sender X")
2. Verify approval card appears showing:
   - Original command
   - Parsed action
   - Affected emails (with previews)
   - Confidence score
3. Click "Approve" → action executes
4. Click "Reject" → action cancelled, no changes
5. Verify notification appears after execution

**Pass Criteria**:
- Approval card displays all required info
- Approve executes action correctly
- Reject cancels with no side effects
- Notification shows success/failure

---

### Test 2.3: Undo Functionality
**Objective**: Verify undo works within 30-second window

**Steps**:
1. Execute action (e.g., archive email)
2. Click "Undo" within 30 seconds
3. Verify email returns to original state
4. Wait 31 seconds after action
5. Verify "Undo" button is disabled

**Pass Criteria**:
- Undo works within 30 seconds
- Undo correctly reverses action
- Undo disabled after 30 seconds

---

### Test 2.4: Batch Actions
**Objective**: Verify batch operations work correctly

**Steps**:
1. Command: "archive all emails from beehiiv"
2. Verify approval card shows all affected emails (e.g., 15 emails)
3. Approve action
4. Verify all 15 emails archived
5. Check for partial failures (some succeed, some fail)

**Pass Criteria**:
- All emails in batch processed
- Partial failures handled gracefully
- User notified of results: "14/15 archived, 1 failed"

---

## Week 3: Advanced Actions & Learning

### Test 3.1: Unsubscribe Action
**Objective**: Verify unsubscribe works via List-Unsubscribe header

**Steps**:
1. Find email with List-Unsubscribe header (e.g., newsletter)
2. Command: "unsubscribe from this"
3. Approve action
4. Verify unsubscribe executed (check Gmail settings or HTTP request log)
5. Verify notification: "Unsubscribed from [sender]"

**Pass Criteria**:
- Unsubscribe request sent successfully
- User receives confirmation
- Fallback shown if no List-Unsubscribe header

---

### Test 3.2: Reply Action
**Objective**: Verify AI can draft and send replies

**Steps**:
1. Select email requiring reply
2. Command: "reply saying I'll attend the meeting"
3. Verify approval card shows:
   - Original email context
   - Drafted reply message
4. Edit draft if needed
5. Approve → reply sent
6. Check Gmail sent folder for reply

**Pass Criteria**:
- Reply drafted appropriately (matches intent)
- Reply sent to correct recipient
- Reply appears in Gmail sent folder
- Thread updated in Gmail

---

### Test 3.3: Pattern Learning - First Suggestion
**Objective**: Verify system suggests action after 5 confirmations

**Steps**:
1. Archive 5 emails from "newsletter@example.com"
2. Receive 6th email from same sender
3. Open email in UI
4. Verify "Suggested action" badge appears: "Archive (based on past actions)"
5. Check confidence score (should be ~0.6-0.7)

**Pass Criteria**:
- Suggestion appears after 5 confirmations
- Suggested action matches pattern (archive)
- Confidence score reasonable (0.6-0.8)

---

### Test 3.4: Pattern Learning - Auto Action
**Objective**: Verify auto-action triggers after high confidence

**Steps**:
1. Archive 15 emails from "newsletter@example.com" (all approved)
2. Receive 16th email from same sender
3. Verify system auto-archives without asking
4. Check notification: "Auto-archived (you always archive these)"
5. Check audit log for automatic action

**Pass Criteria**:
- Auto-action triggers at confidence > 0.95 and confirmations > 10
- User notified of automatic action
- Audit trail created

---

### Test 3.5: Past Item Filtering
**Objective**: Verify low-priority past items hidden, high-priority visible

**Setup**: Create test emails:
- Email A: date=7 days ago, priority=LOW, subject="Newsletter"
- Email B: date=7 days ago, priority=HIGH, subject="Invoice due"
- Email C: date=today, priority=LOW, subject="Newsletter"

**Steps**:
1. Open "Today" tab in UI
2. Verify Email C visible (today, any priority)
3. Open "All Items" tab
4. Verify Email A hidden (past + LOW priority)
5. Verify Email B visible (past + HIGH priority)
6. Toggle "Show past items" filter
7. Verify Email A now visible

**Pass Criteria**:
- Past LOW priority items hidden by default
- Past HIGH/MED priority items always visible
- Toggle filter works correctly

---

### Test 3.6: Event Bus Integration
**Objective**: Verify email assistant publishes/subscribes to events

**Test: Calendar → Email Detection**
1. Create calendar event: "Flight to NYC"
2. Verify email assistant subscribes to "calendar.event.created"
3. System searches for related emails (flight confirmation)
4. Suggests linking email to calendar event

**Test: Task → Email Archival**
1. Complete task: "Review proposal"
2. System publishes "task.completed"
3. Email assistant receives event
4. Suggests archiving related emails from proposal sender

**Pass Criteria**:
- Events published correctly (check event log)
- Subscribers receive events within 1 second
- Cross-module intelligence works (calendar ↔ email)

---

## Week 4: Cost Optimization

### Test 4.1: Batch Processing Cost Reduction
**Objective**: Verify 50%+ reduction in AI calls via batching

**Steps**:
1. Process 100 emails individually (Week 2 method)
2. Count total AI calls → Expected: ~100 calls
3. Process 100 emails with batching (Week 4 method)
4. Count total AI calls → Expected: ~5 calls (20 per batch)
5. Calculate reduction: `(100 - 5) / 100 = 95%`

**Pass Criteria**:
- Batch processing reduces AI calls by ≥ 50%
- No accuracy loss (same classification results)
- Processing time < 2 minutes for 100 emails

---

### Test 4.2: Cache Hit Rate
**Objective**: Verify cache reduces redundant AI calls

**Steps**:
1. Process 50 emails from 10 senders (5 from each)
2. First email from each sender → AI call (cache miss)
3. Next 4 emails from same sender → cache hit
4. Calculate hit rate: `cache_hits / total_requests`
5. Expected: 40/50 = 80% hit rate

**Pass Criteria**:
- Cache hit rate ≥ 60%
- Cached results accurate (matches AI classification)
- Cache expires after TTL (1 hour)

---

### Test 4.3: Smart Processing Rules
**Objective**: Verify system skips unnecessary AI calls

**Test Cases**:
1. Email from known pattern (confidence > 0.95) → skip AI ✓
2. Email older than 7 days, never accessed → skip AI ✓
3. Newsletter already classified → skip AI ✓
4. High-priority email, no pattern → use AI ✓

**Steps**:
1. Create 100-email dataset matching above cases (25 each)
2. Run smart processing
3. Count AI calls
4. Expected: ~25 calls (only case 4)

**Pass Criteria**:
- AI calls reduced to ≤ 30% of emails
- No misclassification of important emails
- Processing faster (< 30 seconds for 100 emails)

---

### Test 4.4: Cost Analytics Accuracy
**Objective**: Verify analytics dashboard shows correct metrics

**Steps**:
1. Process 200 emails over 3 days
2. Note actual AI calls made
3. Open analytics dashboard
4. Verify metrics match:
   - Total emails processed
   - AI calls made
   - Cache hits/misses
   - Estimated cost (calls × $0.002)
   - Storage savings (GB)

**Pass Criteria**:
- All metrics within 5% of actual values
- Cost estimate accurate
- Dashboard loads < 2 seconds

---

### Test 4.5: Performance with Large Dataset
**Objective**: Verify no degradation with 1000+ emails

**Steps**:
1. Load 1000 emails into database
2. Measure UI load time (initial page load)
3. Search for sender → measure response time
4. Filter by date range → measure response time
5. Process batch of 100 emails → measure time

**Pass Criteria**:
- UI loads < 3 seconds
- Search results < 1 second
- Filter results < 1 second
- Batch processing < 5 minutes

---

## Integration Tests

### Test I.1: End-to-End Unsubscribe Flow
**Objective**: Verify complete flow from command to Gmail state change

**Steps**:
1. User enters: "unsubscribe from all beehiiv newsletters"
2. System parses command → action: unsubscribe, sender: beehiiv.com
3. System finds 15 emails from beehiiv.com
4. Approval card shows all 15 emails
5. User approves
6. System executes unsubscribe for each (via List-Unsubscribe header)
7. System logs actions to audit trail
8. System records pattern: "beehiiv.com → unsubscribe"
9. User receives notification: "Unsubscribed from 15 beehiiv newsletters"
10. Verify Gmail settings show unsubscribe

**Pass Criteria**:
- All steps complete without errors
- Gmail state updated (unsubscribed)
- Audit trail accurate
- Pattern learned

---

### Test I.2: End-to-End Pattern Learning
**Objective**: Verify learning flow from action to auto-execution

**Steps**:
1. Days 1-3: User archives 12 emails from "daily-digest@news.com" (all confirmed)
2. Day 4: Email #13 arrives
3. System suggests: "Archive (you always archive these, confidence 92%)"
4. User approves
5. Day 5: Email #14 arrives
6. System auto-archives without asking (confidence > 95%, confirmations > 10)
7. User sees notification: "Auto-archived daily digest (you always do this)"

**Pass Criteria**:
- Suggestion appears at ~5 confirmations
- Auto-action triggers at confidence > 95% and confirmations > 10
- User can disable auto-action in patterns management page

---

### Test I.3: Multi-Module Intelligence
**Objective**: Verify cross-module event bus integration

**Scenario**: Travel email → Calendar event creation

**Steps**:
1. Email arrives: "Your flight to NYC on Dec 15"
2. Email assistant detects travel-related content
3. Publishes event: "email.travel_detected"
4. Calendar module receives event
5. Calendar suggests creating event: "Flight to NYC - Dec 15"
6. User approves
7. Calendar creates event and links to email

**Pass Criteria**:
- Travel email detected correctly
- Event published and received < 1 second
- Calendar suggestion accurate
- Email linked to calendar event

---

## Security & Privacy Tests

### Test S.1: OAuth Scope Minimization
**Objective**: Verify minimal Gmail API permissions

**Steps**:
1. Review OAuth consent screen
2. Check requested scopes
3. Verify only these scopes used:
   - `gmail.modify` (for archive, mark read)
   - `gmail.send` (for replies)
   - `gmail.readonly` (for fetching)

**Pass Criteria**:
- No excessive permissions (e.g., no `gmail.full`)
- User sees clear scope descriptions

---

### Test S.2: Data Retention
**Objective**: Verify old data is cleaned up

**Steps**:
1. Check database for emails older than 90 days
2. Verify email summaries deleted (only metadata kept)
3. Check audit logs older than 1 year
4. Verify logs archived/deleted

**Pass Criteria**:
- Data retention policy followed
- Old data removed automatically

---

### Test S.3: User Consent for Learning
**Objective**: Verify user can opt out of pattern learning

**Steps**:
1. Disable pattern learning in settings
2. Archive 10 emails from same sender
3. Verify no pattern created
4. Verify no suggestions shown
5. Re-enable pattern learning
6. Verify patterns resume

**Pass Criteria**:
- Opt-out respected (no learning when disabled)
- Opt-in resumes learning
- Existing patterns preserved when disabled

---

## Performance Benchmarks

### Benchmark 1: API Response Times
- Health check: < 100ms
- List items (50 emails): < 500ms
- Parse command: < 2s (AI call)
- Fetch email body: < 2s (Gmail API)

### Benchmark 2: Database Queries
- List emails with filters: < 200ms
- Search by sender: < 300ms
- Get learned patterns: < 100ms

### Benchmark 3: AI Costs (Monthly)
- Before optimization: $6/month (3000 emails × $0.002)
- After optimization: $0.50/month (250 AI calls)
- Target: < $1/month

### Benchmark 4: Storage
- Before: 12KB per email average
- After: 0.6KB per email average
- Target: < 1KB per email
