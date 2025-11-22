"""
BIL Conversational Prompts
==========================
Prompt libraries for morning, evening, and session reminders.
"""

MORNING_PROMPTS = [
    "🌅 Good morning! What are your top 3 priorities today?",
    "🌄 Rise and shine! What's the one thing that would make today great?",
    "☀️ Hey there! What are you looking forward to accomplishing today?",
    "🌞 Morning! Let's plan your day - what's most important?",
]

EVENING_PROMPTS = [
    "🌙 Evening check-in: What went well today? What got in your way?",
    "🌃 Time to reflect - what's one thing you learned today?",
    "🌆 End of day! What are you proud of from today?",
    "🌇 Let's wrap up: What would you do differently tomorrow?",
]

MISSED_SESSION_PROMPTS = [
    "I noticed you haven't done {goal} yet this week. Would tomorrow morning work?",
    "Hey, {goal} is still on the list. Want to squeeze it in this afternoon?",
    "You're usually consistent with {goal} - everything okay? Can I help reschedule?",
    "No {goal} session yet - shall we block some time for it?",
]

ENCOURAGEMENT_PROMPTS = [
    "🎉 You're {percent}% of the way to your {goal} goal! Keep it up!",
    "💪 {sessions} sessions done for {goal} - you're crushing it!",
    "🔥 On track with {goal}! That's what I like to see!",
    "✨ Your consistency with {goal} is inspiring!",
]
