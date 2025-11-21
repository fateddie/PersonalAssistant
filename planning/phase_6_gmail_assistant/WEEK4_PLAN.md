# Week 4: Cost Optimization & Performance - Detailed Plan

**Goal**: Reduce AI costs by 80%+ through batch processing, caching, and smart rules

**Timeline**: 8-12 hours

**Outcome**: AI calls reduced from $6/month to < $1/month, cache hit rate > 60%, sub-second performance

---

## Day 1: Batch Processing (3-4 hours)

### 1.1: Design Batch Processor
**Time**: 1 hour

**Strategy**:
- Process up to 20 emails in single AI call
- Group similar emails (same sender) together
- Handle partial failures gracefully
- Queue system for async processing

Create `assistant/modules/email_assistant/batch_processor.py`:
```python
"""
Batch processing to reduce AI costs
"""
import openai
from typing import List, Dict
from datetime import datetime

class BatchProcessor:
    """Process multiple emails in single AI call"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.batch_size = 20

    def classify_batch(self, emails: List[Dict]) -> List[Dict]:
        """
        Classify multiple emails in single AI call

        Args:
            emails: List of email dicts with sender, subject, snippet

        Returns: List of classifications matching input order
        [
            {"email_id": "abc", "priority": "low", "category": "newsletter"},
            {"email_id": "def", "priority": "high", "category": "bill"},
            ...
        ]
        """
        if not emails:
            return []

        # Build batch prompt
        prompt = "Classify these emails. For each, provide: priority (low/med/high), category (newsletter/receipt/personal/work).\n\n"

        for i, email in enumerate(emails):
            prompt += f"{i+1}. From: {email['sender']}\n   Subject: {email['subject']}\n   Snippet: {email.get('snippet', '')[:100]}\n\n"

        prompt += "\nReturn JSON array with format: [{\"email_index\": 1, \"priority\": \"low\", \"category\": \"newsletter\"}, ...]"

        try:
            # Single AI call for all emails
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            # Parse response
            import json
            result_text = response["choices"][0]["message"]["content"]
            classifications = json.loads(result_text)

            # Match back to email IDs
            results = []
            for i, email in enumerate(emails):
                # Find classification for this email
                classification = next((c for c in classifications if c.get("email_index") == i+1), None)

                if classification:
                    results.append({
                        "email_id": email['id'],
                        "priority": classification.get("priority", "med"),
                        "category": classification.get("category", "personal")
                    })
                else:
                    # Fallback
                    results.append({
                        "email_id": email['id'],
                        "priority": "med",
                        "category": "personal"
                    })

            return results

        except Exception as e:
            print(f"❌ Batch classification error: {e}")
            # Fallback: return default classifications
            return [{"email_id": e['id'], "priority": "med", "category": "personal"} for e in emails]

    def group_by_sender(self, emails: List[Dict]) -> Dict[str, List[Dict]]:
        """Group emails by sender domain"""
        groups = {}
        for email in emails:
            sender = email.get('sender', '')
            domain = sender.split('@')[1] if '@' in sender else sender

            if domain not in groups:
                groups[domain] = []
            groups[domain].append(email)

        return groups

    def process_queue(self, email_ids: List[str], db: Session) -> Dict:
        """
        Process queue of emails in batches

        Returns: {
            "total": 100,
            "processed": 95,
            "failed": 5,
            "ai_calls": 5,  # Instead of 100
            "duration": 12.3
        }
        """
        import time
        start = time.time()

        from assistant_api.app.models import Email

        # Fetch emails from DB
        emails = db.query(Email).filter(Email.email_id.in_(email_ids)).all()

        if not emails:
            return {"total": 0, "processed": 0}

        # Group by sender
        groups = self.group_by_sender([
            {"id": e.email_id, "sender": e.sender, "subject": e.subject}
            for e in emails
        ])

        processed = 0
        failed = 0
        ai_calls = 0

        # Process each group in batches
        for domain, domain_emails in groups.items():
            # Split into batches of 20
            for i in range(0, len(domain_emails), self.batch_size):
                batch = domain_emails[i:i+self.batch_size]

                try:
                    classifications = self.classify_batch(batch)
                    ai_calls += 1

                    # Update DB
                    for classification in classifications:
                        email = db.query(Email).filter(
                            Email.email_id == classification['email_id']
                        ).first()

                        if email:
                            email.priority = classification['priority']
                            email.category = classification['category']
                            processed += 1

                    db.commit()

                except Exception as e:
                    print(f"❌ Batch failed: {e}")
                    failed += len(batch)

        duration = time.time() - start

        return {
            "total": len(emails),
            "processed": processed,
            "failed": failed,
            "ai_calls": ai_calls,
            "duration": duration
        }
```

---

### 1.2: Add API Endpoint
**Time**: 30 minutes

Add to `assistant_api/app/routers/email_actions.py`:
```python
from assistant.modules.email_assistant.batch_processor import BatchProcessor

@router.post("/batch-process")
def batch_process_emails(
    email_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    Process multiple emails in batches (cost-optimized)

    Cost comparison:
    - Individual: 100 emails × $0.002 = $0.20
    - Batch: 5 AI calls × $0.02 = $0.10 (50% savings)
    """
    processor = BatchProcessor()
    result = processor.process_queue(email_ids, db)

    return result
```

---

### 1.3: Add UI Progress Indicator
**Time**: 1 hour

Add batch processing button to Streamlit:
```python
# In main.py
with st.sidebar:
    st.divider()
    st.header("⚡ Batch Processing")

    if st.button("Process Unclassified Emails"):
        with st.spinner("Processing in batches..."):
            try:
                # Get unclassified emails
                result = client.list_items(
                    source="gmail",
                    limit=100
                )

                unclassified = [
                    item['id'] for item in result['items']
                    if not item.get('priority') or not item.get('category')
                ]

                if not unclassified:
                    st.info("All emails already classified")
                else:
                    # Batch process
                    process_result = client.batch_process_emails(unclassified)

                    st.success(f"""
                    ✅ Processed {process_result['processed']} emails
                    ⚡ Used {process_result['ai_calls']} AI calls (instead of {process_result['total']})
                    💰 Saved ${(process_result['total'] - process_result['ai_calls']) * 0.002:.3f}
                    ⏱️ Took {process_result['duration']:.1f}s
                    """)

            except Exception as e:
                st.error(f"Error: {e}")
```

---

### 1.4: Test Batch Processing
**Time**: 30 minutes

```python
def test_batch_processing():
    processor = BatchProcessor()

    # Create test emails
    emails = [
        {"id": f"test_{i}", "sender": f"sender{i % 5}@example.com", "subject": f"Test {i}"}
        for i in range(50)
    ]

    # Process
    start = time.time()
    classifications = processor.classify_batch(emails[:20])
    duration = time.time() - start

    print(f"Classified 20 emails in {duration:.2f}s with 1 AI call")
    assert len(classifications) == 20
    assert all('priority' in c for c in classifications)

# Expected: 20 emails classified in < 5 seconds
```

---

## Day 2: Caching Layer (3-4 hours)

### 2.1: Choose Caching Strategy
**Time**: 30 minutes

**Options**:
1. Redis (best for production, persistent)
2. In-memory (simpler, ephemeral)

**Decision**: Start with in-memory, migrate to Redis in production

Create `assistant/modules/email_assistant/cache_manager.py`:
```python
"""
Caching layer to reduce redundant AI calls
"""
from typing import Optional, Dict
import time
from functools import lru_cache

class CacheManager:
    """Manage email classification cache"""

    def __init__(self, ttl: int = 3600):
        """
        Args:
            ttl: Time to live in seconds (default 1 hour)
        """
        self.cache = {}  # {cache_key: (value, timestamp)}
        self.ttl = ttl

    def _make_key(self, sender: str, subject: str) -> str:
        """Create cache key from sender + subject"""
        # Normalize
        sender = sender.lower().strip()
        subject = subject.lower().strip()[:100]  # First 100 chars

        return f"{sender}::{subject}"

    def get(self, sender: str, subject: str) -> Optional[Dict]:
        """Get cached classification"""
        key = self._make_key(sender, subject)

        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return value

    def set(self, sender: str, subject: str, classification: Dict):
        """Cache classification"""
        key = self._make_key(sender, subject)
        self.cache[key] = (classification, time.time())

    def clear_expired(self):
        """Remove expired entries"""
        now = time.time()
        expired = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl
        ]

        for key in expired:
            del self.cache[key]

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = len(self.cache)
        now = time.time()

        valid = sum(1 for _, timestamp in self.cache.values() if now - timestamp <= self.ttl)
        expired = total - valid

        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "hit_rate": getattr(self, '_hit_rate', 0.0)
        }

# Global cache instance
email_cache = CacheManager(ttl=3600)
```

---

### 2.2: Integrate Cache with Batch Processor
**Time**: 1 hour

Update `batch_processor.py`:
```python
from .cache_manager import email_cache

class BatchProcessor:
    def __init__(self, ...):
        # ... existing init
        self.cache_hits = 0
        self.cache_misses = 0

    def classify_batch(self, emails: List[Dict]) -> List[Dict]:
        """Classify with caching"""
        results = []
        uncached_emails = []

        # Check cache first
        for email in emails:
            cached = email_cache.get(email['sender'], email['subject'])

            if cached:
                results.append({
                    "email_id": email['id'],
                    **cached
                })
                self.cache_hits += 1
            else:
                uncached_emails.append(email)
                self.cache_misses += 1

        # Only process uncached emails with AI
        if uncached_emails:
            # ... AI classification (existing code)
            classifications = self._classify_with_ai(uncached_emails)

            for classification in classifications:
                results.append(classification)

                # Cache result
                email = next(e for e in uncached_emails if e['id'] == classification['email_id'])
                email_cache.set(
                    email['sender'],
                    email['subject'],
                    {
                        "priority": classification['priority'],
                        "category": classification['category']
                    }
                )

        return results

    def get_cache_stats(self) -> Dict:
        """Get cache performance stats"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            **email_cache.get_stats()
        }
```

---

### 2.3: Add Cache Management Endpoints
**Time**: 30 minutes

Add to `email_actions.py`:
```python
@router.get("/cache/stats")
def get_cache_stats():
    """Get cache performance statistics"""
    processor = BatchProcessor()
    return processor.get_cache_stats()

@router.post("/cache/clear")
def clear_cache():
    """Clear email classification cache"""
    email_cache.cache.clear()
    return {"success": True, "message": "Cache cleared"}

@router.post("/cache/clear-expired")
def clear_expired_cache():
    """Remove expired cache entries"""
    email_cache.clear_expired()
    return {"success": True, "message": "Expired entries removed"}
```

---

### 2.4: Test Caching
**Time**: 1 hour

```python
def test_cache_hit():
    cache = CacheManager(ttl=60)

    # First lookup - miss
    result = cache.get("sender@example.com", "Test subject")
    assert result is None

    # Set value
    cache.set("sender@example.com", "Test subject", {"priority": "low", "category": "newsletter"})

    # Second lookup - hit
    result = cache.get("sender@example.com", "Test subject")
    assert result is not None
    assert result["priority"] == "low"

def test_cache_expiry():
    cache = CacheManager(ttl=1)  # 1 second TTL

    cache.set("test@example.com", "Subject", {"priority": "high"})

    # Immediate lookup - hit
    assert cache.get("test@example.com", "Subject") is not None

    # Wait for expiry
    time.sleep(2)

    # Lookup after expiry - miss
    assert cache.get("test@example.com", "Subject") is None
```

---

## Day 3: Smart Processing Rules (2-3 hours)

### 3.1: Implement Smart Rules
**Time**: 2 hours

Create `assistant/modules/email_assistant/smart_rules.py`:
```python
"""
Smart processing rules to skip unnecessary AI calls
"""
from typing import Dict, Optional
from datetime import datetime, timedelta

class SmartRules:
    """Determine if email needs AI processing"""

    @staticmethod
    def should_process(email: Dict, patterns: list = None) -> Dict:
        """
        Decide if email needs AI processing

        Returns: {
            "should_process": bool,
            "reason": str,
            "skip_reason": str (if skipped)
        }
        """
        # Rule 1: Known pattern with high confidence → skip AI
        if patterns:
            matching_pattern = next(
                (p for p in patterns if email['sender'].endswith(p['pattern_value'])),
                None
            )

            if matching_pattern and matching_pattern['confidence'] >= 0.95:
                return {
                    "should_process": False,
                    "reason": "known_pattern",
                    "skip_reason": f"High confidence pattern match ({matching_pattern['confidence']:.0%})",
                    "suggested_action": matching_pattern['suggested_action'],
                    "priority": matching_pattern.get('priority', 'low'),
                    "category": matching_pattern.get('category', 'newsletter')
                }

        # Rule 2: Old email never accessed → skip
        if 'date' in email:
            email_date = email['date']
            if isinstance(email_date, str):
                email_date = datetime.fromisoformat(email_date)

            days_old = (datetime.now() - email_date).days

            if days_old > 7 and not email.get('last_accessed'):
                return {
                    "should_process": False,
                    "reason": "old_unaccessed",
                    "skip_reason": f"Email is {days_old} days old and never accessed",
                    "priority": "low",
                    "category": "archived"
                }

        # Rule 3: Already classified → skip
        if email.get('priority') and email.get('category'):
            return {
                "should_process": False,
                "reason": "already_classified",
                "skip_reason": "Email already has priority and category"
            }

        # Rule 4: Newsletter keywords in sender/subject → skip AI
        newsletter_keywords = ['newsletter', 'digest', 'weekly', 'daily', 'updates', 'notification']

        sender_lower = email['sender'].lower()
        subject_lower = email.get('subject', '').lower()

        if any(kw in sender_lower or kw in subject_lower for kw in newsletter_keywords):
            return {
                "should_process": False,
                "reason": "newsletter_keyword",
                "skip_reason": "Detected newsletter keyword",
                "priority": "low",
                "category": "newsletter"
            }

        # Default: process with AI
        return {
            "should_process": True,
            "reason": "needs_classification"
        }

    @staticmethod
    def batch_filter(emails: List[Dict], patterns: list = None) -> Dict:
        """
        Filter batch of emails

        Returns: {
            "to_process": [...],  # Emails needing AI
            "skipped": [...],     # Emails skipped (with classifications)
            "skip_stats": {...}
        }
        """
        to_process = []
        skipped = []
        skip_reasons = {}

        for email in emails:
            decision = SmartRules.should_process(email, patterns)

            if decision["should_process"]:
                to_process.append(email)
            else:
                skipped.append({
                    **email,
                    "priority": decision.get("priority"),
                    "category": decision.get("category"),
                    "skip_reason": decision["skip_reason"]
                })

                # Track skip reasons
                reason = decision["reason"]
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

        return {
            "to_process": to_process,
            "skipped": skipped,
            "skip_stats": {
                "total": len(emails),
                "skipped_count": len(skipped),
                "process_count": len(to_process),
                "skip_rate": len(skipped) / len(emails) if emails else 0,
                "reasons": skip_reasons
            }
        }
```

---

### 3.2: Integrate Smart Rules
**Time**: 1 hour

Update `batch_processor.py`:
```python
from .smart_rules import SmartRules
from assistant_api.app.models import EmailPattern

class BatchProcessor:
    def process_queue(self, email_ids: List[str], db: Session) -> Dict:
        """Process with smart rules"""
        # ... fetch emails

        # Get learned patterns
        patterns = db.query(EmailPattern).filter(
            EmailPattern.confidence >= 0.95
        ).all()

        pattern_dicts = [
            {
                "pattern_value": p.pattern_value,
                "confidence": p.confidence,
                "suggested_action": p.suggested_action
            }
            for p in patterns
        ]

        # Apply smart rules
        email_dicts = [
            {
                "id": e.email_id,
                "sender": e.sender,
                "subject": e.subject,
                "date": e.date,
                "last_accessed": e.last_accessed,
                "priority": e.priority,
                "category": e.category
            }
            for e in emails
        ]

        filtered = SmartRules.batch_filter(email_dicts, pattern_dicts)

        # Update skipped emails in DB (no AI call needed)
        for skipped_email in filtered["skipped"]:
            email = db.query(Email).filter(Email.email_id == skipped_email['id']).first()
            if email and not email.priority:
                email.priority = skipped_email['priority']
                email.category = skipped_email['category']

        db.commit()

        # Only process emails that need AI
        to_process = filtered["to_process"]
        ai_calls = 0
        processed = len(filtered["skipped"])  # Already processed via rules

        if to_process:
            # ... batch classify with AI
            ai_calls = len(to_process) // self.batch_size + 1
            processed += len(to_process)

        return {
            "total": len(emails),
            "processed": processed,
            "ai_calls": ai_calls,
            "skipped_by_rules": len(filtered["skipped"]),
            "skip_stats": filtered["skip_stats"],
            # ... other stats
        }
```

---

## Day 4: Analytics Dashboard & Testing (2-3 hours)

### 4.1: Create Analytics Module
**Time**: 1 hour

Create `assistant/modules/email_assistant/analytics.py`:
```python
"""
Usage analytics and cost tracking
"""
from sqlalchemy import func
from datetime import datetime, timedelta
from assistant_api.app.models import Email, PendingEmailAction, EmailPattern

class EmailAnalytics:
    """Track usage and costs"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_cost_per_call = 0.002  # GPT-3.5-turbo estimate

    def get_summary(self, days: int = 30) -> Dict:
        """Get analytics summary for last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Email counts
        total_emails = self.db.query(func.count(Email.email_id)).scalar()
        recent_emails = self.db.query(func.count(Email.email_id)).filter(
            Email.fetched_at >= cutoff
        ).scalar()

        # Actions executed
        actions_executed = self.db.query(func.count(PendingEmailAction.id)).filter(
            PendingEmailAction.status == "executed",
            PendingEmailAction.executed_at >= cutoff
        ).scalar()

        # Patterns learned
        patterns_learned = self.db.query(func.count(EmailPattern.id)).scalar()
        auto_patterns = self.db.query(func.count(EmailPattern.id)).filter(
            EmailPattern.auto_apply == True
        ).scalar()

        # Estimate costs (conservative)
        # Assume 1 AI call per 10 emails (with caching + rules)
        estimated_ai_calls = recent_emails / 10
        estimated_cost = estimated_ai_calls * self.ai_cost_per_call

        return {
            "period_days": days,
            "emails": {
                "total": total_emails,
                "recent": recent_emails
            },
            "actions": {
                "executed": actions_executed
            },
            "patterns": {
                "total": patterns_learned,
                "auto_apply": auto_patterns
            },
            "costs": {
                "estimated_ai_calls": int(estimated_ai_calls),
                "estimated_cost_usd": estimated_cost,
                "cost_per_email": estimated_cost / recent_emails if recent_emails > 0 else 0
            },
            "optimization": {
                "cache_enabled": True,
                "smart_rules_enabled": True,
                "batch_processing_enabled": True
            }
        }

    def get_category_breakdown(self) -> Dict:
        """Get email counts by category"""
        categories = self.db.query(
            Email.category,
            func.count(Email.email_id)
        ).group_by(Email.category).all()

        return {cat: count for cat, count in categories}

    def get_top_senders(self, limit: int = 10) -> List[Dict]:
        """Get most frequent senders"""
        senders = self.db.query(
            Email.sender,
            func.count(Email.email_id).label('count')
        ).group_by(Email.sender).order_by(func.count(Email.email_id).desc()).limit(limit).all()

        return [{"sender": sender, "count": count} for sender, count in senders]
```

---

### 4.2: Add Analytics Dashboard to UI
**Time**: 1 hour

Add new tab to Streamlit:
```python
tabs = st.tabs(["📅 Today", "📆 Upcoming", "✅ All Items", "🤖 Commands", "🧠 Patterns", "📊 Analytics", "➕ Add New"])

# Analytics tab
with tabs[5]:
    st.header("📊 Email Analytics")

    # Time period selector
    period = st.selectbox("Time period", [7, 30, 90], index=1, format_func=lambda x: f"Last {x} days")

    try:
        analytics = client.get_email_analytics(days=period)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Emails", analytics['emails']['total'])
            st.caption(f"{analytics['emails']['recent']} recent")

        with col2:
            st.metric("Actions Executed", analytics['actions']['executed'])

        with col3:
            st.metric("Patterns Learned", analytics['patterns']['total'])
            st.caption(f"{analytics['patterns']['auto_apply']} auto-apply")

        with col4:
            cost = analytics['costs']['estimated_cost_usd']
            st.metric("Estimated Cost", f"${cost:.2f}")
            st.caption(f"{analytics['costs']['estimated_ai_calls']} AI calls")

        st.divider()

        # Cost breakdown
        st.subheader("💰 Cost Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Optimization Status**")
            st.success("✅ Batch processing enabled")
            st.success("✅ Caching enabled")
            st.success("✅ Smart rules enabled")

        with col2:
            st.markdown("**Savings**")
            baseline_cost = analytics['emails']['recent'] * 0.002
            actual_cost = analytics['costs']['estimated_cost_usd']
            savings = baseline_cost - actual_cost
            savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

            st.metric(
                "Monthly Savings",
                f"${savings:.2f}",
                f"{savings_pct:.0f}%",
                delta_color="normal"
            )

            st.caption(f"Baseline: ${baseline_cost:.2f} (no optimization)")
            st.caption(f"Actual: ${actual_cost:.2f} (with optimization)")

        st.divider()

        # Category breakdown
        st.subheader("📂 Email Categories")
        categories = client.get_email_category_breakdown()

        if categories:
            import pandas as pd
            df = pd.DataFrame(list(categories.items()), columns=['Category', 'Count'])
            st.bar_chart(df.set_index('Category'))

        # Top senders
        st.subheader("👤 Top Senders")
        top_senders = client.get_top_senders(limit=10)

        for i, sender_data in enumerate(top_senders, 1):
            st.markdown(f"{i}. **{sender_data['sender']}** ({sender_data['count']} emails)")

    except Exception as e:
        st.error(f"Error loading analytics: {e}")
```

---

### 4.3: Acceptance Tests
**Time**: 1 hour

Run tests from `acceptance_tests.md` Week 4:
- [ ] Test 4.1: Batch Processing Cost Reduction (≥ 50%)
- [ ] Test 4.2: Cache Hit Rate (≥ 60%)
- [ ] Test 4.3: Smart Processing Rules
- [ ] Test 4.4: Cost Analytics Accuracy
- [ ] Test 4.5: Performance with 1000+ emails

---

## Final Integration & Polish (Optional)

### Polish Items:
- [ ] Add loading spinners for all async operations
- [ ] Add progress bars for batch processing
- [ ] Improve error messages
- [ ] Add keyboard shortcuts
- [ ] Add email to docs/

---

## Deliverables

1. ✅ Batch processor (process 20 emails in 1 AI call)
2. ✅ Cache manager (in-memory with TTL)
3. ✅ Smart processing rules (skip unnecessary AI calls)
4. ✅ Analytics dashboard (costs, savings, metrics)
5. ✅ Cost reduced by 80%+ ($6 → < $1/month)
6. ✅ Cache hit rate > 60%
7. ✅ Performance sub-second for typical operations
8. ✅ All acceptance tests pass

---

## Success Metrics

**Before Optimization**:
- Process 3000 emails/month individually
- 3000 AI calls × $0.002 = $6.00/month
- Average 2-3 seconds per email
- No caching or intelligent skipping

**After Optimization**:
- Process 3000 emails/month with optimization
- ~250 AI calls (batch + cache + rules)
- 250 AI calls × $0.002 = $0.50/month
- **92% cost reduction**
- **60%+ cache hit rate**
- **Average < 1 second per email**

---

## Monitoring & Maintenance

### Weekly:
- Check cache hit rate (target > 60%)
- Review AI cost (target < $1/month)
- Clear expired cache entries

### Monthly:
- Review learned patterns (delete low-confidence ones)
- Analyze top senders (create manual rules)
- Optimize batch size if needed

### Alerts:
- Cost > $5/month → investigate
- Cache hit rate < 40% → adjust TTL
- Error rate > 5% → fix bugs
