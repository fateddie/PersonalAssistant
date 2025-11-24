"""
AskSharon.ai Scheduler
======================
Schedules timed events (morning check-in, evening reflection, email sync).
"""

import schedule
import time
import threading
import requests
from datetime import datetime
from assistant.core.orchestrator import publish


# Track last sync time
_last_email_sync = None


def job_morning_checkin():
    publish("morning_checkin", {"time": "07:30"})


def job_evening_reflection():
    publish("evening_reflection", {"time": "21:00"})


def job_evening_planning():
    """6pm trigger for evening planning (Phase 3.5)"""
    publish("evening_planning", {"time": "18:00"})


def job_morning_fallback():
    """8am fallback if evening planning was missed (Phase 3.5)"""
    publish("morning_fallback", {"time": "08:00"})


def job_email_sync():
    """Periodic Gmail sync - fetches new emails and detects events"""
    global _last_email_sync
    try:
        print(f"📧 Scheduled email sync starting...")
        response = requests.get("http://localhost:8000/emails/detect-events?limit=50", timeout=30)
        if response.status_code == 200:
            data = response.json()
            detected = data.get("detected", 0)
            _last_email_sync = datetime.now()
            print(f"✅ Email sync complete: {detected} events detected")
        else:
            print(f"⚠️ Email sync failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Email sync error: {e}")


def get_last_sync_time():
    """Get the last email sync time"""
    return _last_email_sync


def start_scheduler():
    # Daily events - original check-ins
    schedule.every().day.at("07:30").do(job_morning_checkin)
    schedule.every().day.at("21:00").do(job_evening_reflection)

    # Phase 3.5: Evening planning (primary) + morning fallback
    schedule.every().day.at("18:00").do(job_evening_planning)
    schedule.every().day.at("08:00").do(job_morning_fallback)

    # Email sync every 30 minutes
    schedule.every(30).minutes.do(job_email_sync)

    print("🕓 Scheduler started (email sync every 30 min, evening planning 6pm, morning fallback 8am)")

    def loop():
        while True:
            schedule.run_pending()
            time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()
