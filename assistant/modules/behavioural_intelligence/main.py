"""
Behavioural Intelligence Layer (BIL) – MVP Stub
===============================================
Listens for scheduled events and produces context-aware nudges.
Future: goal encoding (gym/guitar), adherence tracking, adaptive reschedule.
"""

from datetime import datetime

USER_GOALS = {
    "gym": {"target_per_week": 4, "completed": 0},
    "guitar": {"target_per_week": 4, "completed": 0},
}


def register(app, publish, subscribe):
    subscribe("morning_checkin", morning_prompt)
    subscribe("evening_reflection", evening_review)


def morning_prompt(data):
    print(f"🌅 Morning check-in ({data.get('time')}): plan your top 3 priorities today.")


def evening_review(data):
    print("🌙 Evening reflection: what went well, what blocked you?")
    for goal, meta in USER_GOALS.items():
        completion = meta["completed"] / max(1, meta["target_per_week"])
        if completion < 0.5:
            print(f"🔔 You're behind on '{goal}'. Shall we book time tomorrow?")
