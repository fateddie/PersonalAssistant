"""
AskSharon.ai Orchestrator
=========================
Central brain: boots FastAPI, loads modules from registry, and provides an event bus.
"""

from fastapi import FastAPI
from importlib import import_module
import yaml
import requests
from threading import Thread
import time

app = FastAPI(title="AskSharon.ai Orchestrator")

EVENT_SUBSCRIBERS = {}


def publish(event: str, data: dict):
    """Broadcast an event and payload to all subscribers."""
    for callback in EVENT_SUBSCRIBERS.get(event, []):
        try:
            callback(data)
        except Exception as e:
            print(f"⚠️ Event '{event}' delivery error: {e}")


def subscribe(event: str, callback):
    """Allow modules to listen to system events."""
    EVENT_SUBSCRIBERS.setdefault(event, []).append(callback)


def load_modules():
    """Load enabled modules based on YAML registry."""
    with open("assistant/configs/module_registry.yaml") as f:
        registry = yaml.safe_load(f)
    for mod in registry["modules"]:
        if mod.get("enabled", False):
            module = import_module(f"assistant.modules.{mod['name']}.main")
            module.register(app, publish, subscribe)
            print(f"✅ Loaded module: {mod['name']}")


def auto_scan_emails():
    """Background task: Auto-scan emails for events on startup"""
    time.sleep(5)  # Wait for app to fully start
    try:
        print("📧 Auto-scanning emails for upcoming events...")
        response = requests.get("http://localhost:8000/emails/detect-events?limit=50", timeout=20)
        if response.status_code == 200:
            data = response.json()
            detected = data.get("detected", 0)
            print(f"✅ Auto-scan complete: {detected} events detected")
        else:
            print(f"⚠️ Auto-scan failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Auto-scan error: {e}")


# Import starts module load
load_modules()


# Start background email scanner and scheduler on startup
@app.on_event("startup")
async def startup_event():
    """Run tasks on application startup"""
    print("🚀 AskSharon.ai started - Initializing background tasks...")
    # Run email scan in background thread (non-blocking)
    Thread(target=auto_scan_emails, daemon=True).start()
    # Start scheduler for periodic tasks (email sync every 30 min)
    from assistant.core.scheduler import start_scheduler

    start_scheduler()
