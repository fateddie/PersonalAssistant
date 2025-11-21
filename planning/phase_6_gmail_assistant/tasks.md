# Phase 6: Task Breakdown

## Week 1: Storage Optimization (8-12 hours)

### Setup Gmail API
- [ ] Add Gmail API credentials to .env
- [ ] Install google-auth, google-auth-oauthlib, google-api-python-client
- [ ] Create OAuth consent screen in Google Cloud Console
- [ ] Test authentication flow

### Create GmailClient
- [ ] Create `assistant/modules/email_assistant/gmail_client.py`
- [ ] Implement OAuth authentication
- [ ] Implement basic operations: list, fetch, archive, mark_read
- [ ] Add rate limiting (100 calls/min)
- [ ] Add error handling and retry logic
- [ ] Write unit tests

### Migrate Database Schema
- [ ] Create migration script: `scripts/migrate_emails_week1.py`
- [ ] Drop body_text, body_html columns from emails table
- [ ] Add gmail_url, summary, category columns
- [ ] Backfill gmail_url for existing emails
- [ ] Test migration on sample data
- [ ] Run migration on production data

### Update UI
- [ ] Add "View in Gmail" button to email cards
- [ ] Add "Fetch full email" button (on-demand)
- [ ] Add loading spinner while fetching
- [ ] Cache fetched emails for 15 minutes
- [ ] Test UI with 100+ emails

### Acceptance Test
- [ ] Storage reduced by 90%+ (measure DB size before/after)
- [ ] No functionality lost (all emails accessible)
- [ ] On-demand fetch works < 2 seconds
- [ ] Gmail links open correct emails

---

## Week 2: Natural Language Commands (10-15 hours)

### Create CommandParser
- [ ] Create `assistant/modules/email_assistant/command_parser.py`
- [ ] Define OpenAI function calling schema for all actions
- [ ] Implement parse_command() method
- [ ] Add confidence scoring
- [ ] Handle ambiguous commands (ask clarifying questions)
- [ ] Write unit tests for all command types

### Implement Safe Actions
- [ ] Search emails (no confirmation needed)
- [ ] Filter by sender/subject (no confirmation)
- [ ] Archive (needs confirmation)
- [ ] Mark read/unread (needs confirmation)
- [ ] Star/unstar (needs confirmation)

### Create ApprovalUI
- [ ] Create `assistant/modules/voice/components/approval_ui.py`
- [ ] Render pending action card with preview
- [ ] Show confidence score and affected emails
- [ ] Add Approve/Reject/Edit buttons
- [ ] Implement undo buffer (30-second window)
- [ ] Test approval flow

### Create pending_email_actions Table
- [ ] Add table to database schema
- [ ] Create CRUD operations
- [ ] Add API endpoints for pending actions

### Integrate with Streamlit UI
- [ ] Add natural language input box
- [ ] Display pending actions in sidebar
- [ ] Show approval cards when actions need confirmation
- [ ] Add notifications for completed actions

### Acceptance Test
- [ ] 90%+ command interpretation accuracy (test 50 commands)
- [ ] All safe actions execute without errors
- [ ] Confirmation flow works for destructive actions
- [ ] Undo works within 30-second window

---

## Week 3: Advanced Actions & Learning (12-18 hours)

### Implement Advanced Actions
- [ ] Unsubscribe (using List-Unsubscribe header)
- [ ] Reply to email
- [ ] Send new email
- [ ] Batch operations (archive all from sender)
- [ ] Move to folder/label
- [ ] Test all actions

### Create PatternLearner
- [ ] Create `assistant/modules/email_assistant/pattern_learner.py`
- [ ] Create email_patterns table
- [ ] Implement record_action() to track confirmations
- [ ] Implement suggest_action() based on patterns
- [ ] Calculate confidence scores
- [ ] Add auto-action threshold (confidence > 0.95, confirmed > 10)
- [ ] Write unit tests

### Integrate Learning with UI
- [ ] Show "Suggested action" badge on emails
- [ ] Display reason and confidence
- [ ] Track user approval/rejection
- [ ] Update patterns in real-time
- [ ] Add "Manage patterns" page (view/edit/delete learned patterns)

### Implement Past Item Filtering
- [ ] Add filter logic: `if date < today and priority == "LOW": hide()`
- [ ] Keep high/med priority past items visible
- [ ] Add "Show past items" toggle in UI
- [ ] Test with mix of priorities

### Event Bus Integration
- [ ] Publish "email.action.executed" events
- [ ] Publish "email.pattern.learned" events
- [ ] Subscribe to calendar events for travel email detection
- [ ] Subscribe to task completion for email archival

### Acceptance Test
- [ ] All advanced actions work (test each one)
- [ ] Pattern learning suggests correct action after 5 confirmations
- [ ] Auto-actions trigger after 10+ confirmations at 95%+ confidence
- [ ] Past low-priority items hidden, high-priority visible

---

## Week 4: Cost Optimization (8-12 hours)

### Implement Batch Processing
- [ ] Create `batch_processor.py`
- [ ] Process up to 20 emails in single AI call
- [ ] Handle partial failures gracefully
- [ ] Implement queue for processing
- [ ] Add progress indicator in UI

### Add Caching Layer
- [ ] Use Redis or in-memory cache for email summaries
- [ ] Cache command parsing results (same command = same result)
- [ ] Cache pattern matches (sender → action mapping)
- [ ] Set TTL: 15 minutes for emails, 1 hour for patterns
- [ ] Measure cache hit rate

### Smart Processing Rules
- [ ] Skip AI for known patterns (confidence > 0.95)
- [ ] Skip AI for emails older than 7 days if not accessed
- [ ] Batch newsletters together (process 20 at once)
- [ ] Add "Process now" button for manual trigger

### Usage Analytics Dashboard
- [ ] Create `assistant/modules/email_assistant/analytics.py`
- [ ] Track: AI calls, cache hits, actions executed, patterns learned
- [ ] Add stats page in Streamlit UI
- [ ] Show cost estimate (AI calls × $0.002)
- [ ] Display storage savings

### Performance Optimization
- [ ] Add database indexes on commonly queried fields
- [ ] Optimize SQL queries (use EXPLAIN)
- [ ] Add pagination to all list views
- [ ] Lazy load email previews

### Acceptance Test
- [ ] 80%+ cost reduction (compare AI calls before/after)
- [ ] Cache hit rate > 60%
- [ ] Batch processing works for 100+ emails
- [ ] Analytics dashboard shows accurate metrics
- [ ] No performance degradation with 1000+ emails

---

## Post-Implementation Tasks

### Documentation
- [ ] Write user guide: "How to use Gmail Assistant"
- [ ] Document all natural language commands
- [ ] Create troubleshooting guide
- [ ] Add architecture diagrams to docs/

### Security & Privacy
- [ ] Review OAuth scope permissions (use minimal required)
- [ ] Add encryption for stored email summaries
- [ ] Implement data retention policy (delete old emails)
- [ ] Add user consent for pattern learning

### Monitoring & Alerts
- [ ] Set up error tracking (Sentry or similar)
- [ ] Add alerts for Gmail API rate limit approaching
- [ ] Monitor AI cost (alert if > $10/month)
- [ ] Track user engagement metrics

### Future Enhancements (Phase 6.5)
- [ ] Mobile UI optimization
- [ ] Voice commands (integrate with voice module)
- [ ] Email templates (quick replies)
- [ ] Smart scheduling (send email at optimal time)
- [ ] Multi-account support (personal + work Gmail)
