# Voice Commands Testing Guide

## 🎤 AI-Powered Voice Commands

Your Personal Assistant now uses OpenAI GPT-4o-mini for natural language understanding and processing.

## How to Test Voice Commands

### 1. Open the App
Navigate to **http://localhost:3000**

### 2. Authenticate
- Click "Connect Google Account" if not already logged in
- Grant necessary permissions

### 3. Use Voice Control
- Look for the large microphone button on the homepage
- Click to start listening (button turns red with pulse animation)
- Speak clearly into your microphone
- Click again to stop listening

---

## Supported Commands

### ✅ Create Task
**Examples:**
- "Add task: buy groceries"
- "Create a task to finish the report"
- "Add task: call dentist tomorrow"
- "New task: review pull requests with high priority"

**AI Extracts:**
- Task title
- Priority (if mentioned: low, medium, high)
- Due date (if mentioned: tomorrow, next week, etc.)

**Expected Response:**
- AI confirms task creation
- Text-to-speech reads confirmation
- Task appears in Task Manager immediately

---

### 💪 Create Habit
**Examples:**
- "Create a habit to exercise daily"
- "Add habit: drink 8 glasses of water"
- "New habit: meditate for 10 minutes every day"
- "Track a weekly habit to meal prep"

**AI Extracts:**
- Habit name
- Frequency (daily, weekly, monthly)

**Expected Response:**
- AI confirms habit creation
- Habit appears in Habit Tracker
- Text-to-speech confirmation

---

### 📋 Query Status
**Examples:**
- "What's on my todo list?"
- "How many tasks do I have?"
- "Show me my habits"
- "What's my status?"

**AI Response:**
- Summary of pending/completed tasks
- Active habits count
- Spoken summary via text-to-speech

---

### ⏰ Set Reminder
**Examples:**
- "Remind me to call mom tomorrow"
- "Set a reminder for the meeting at 3pm"
- "Remind me about the deadline next Friday"

**AI Extracts:**
- Task title
- Due date/time

**Expected Response:**
- Creates task with due date
- AI confirmation with text-to-speech

---

## Testing Checklist

### Basic Voice Recognition
- [ ] Microphone button appears
- [ ] Clicking activates voice recognition
- [ ] Browser requests microphone permission
- [ ] Button shows listening state (red/pulse)
- [ ] Transcript appears during speech

### AI Processing
- [ ] Voice command sent to OpenAI
- [ ] Intent correctly identified
- [ ] Entities properly extracted
- [ ] Natural language response generated

### Task Creation
- [ ] "Add task: test task" creates task
- [ ] Task appears in Task Manager
- [ ] Task has correct title
- [ ] Priority extracted if mentioned
- [ ] Due date parsed if mentioned

### Habit Creation
- [ ] "Create habit: test habit" creates habit
- [ ] Habit appears in Habit Tracker
- [ ] Frequency correctly set
- [ ] Habit marked as active

### Query Status
- [ ] "What's my status?" returns data
- [ ] Counts are accurate
- [ ] Response is natural language
- [ ] Text-to-speech works

### Error Handling
- [ ] Unknown commands handled gracefully
- [ ] Network errors show user message
- [ ] OpenAI timeout handled
- [ ] Fallback responses when API unavailable

---

## Expected AI Responses

### Successful Task Creation
```
"Great! I've added 'buy groceries' to your task list."
"Task created: finish the report. You got this!"
"Done! 'Call dentist tomorrow' is now on your todo list."
```

### Successful Habit Creation
```
"Awesome! I've added 'exercise daily' to your habit tracker."
"Habit tracked: meditate for 10 minutes. Let's build that streak!"
"Perfect! 'Drink 8 glasses of water' is now being tracked."
```

### Status Query
```
"You have 5 pending tasks and 3 active habits. You're making great progress!"
"Currently tracking: 2 pending tasks, 4 completed tasks, and 3 habits."
```

### Unknown Command
```
"I'm not sure how to help with that. Try saying 'Add task' or 'Create habit'."
"Sorry, I didn't understand. You can ask me about your tasks or habits."
```

---

## Troubleshooting

### Voice Recognition Not Working
**Issue:** Microphone button doesn't activate
**Solutions:**
1. Check browser permissions (Chrome works best)
2. Grant microphone access when prompted
3. Try Chrome if using Safari/Firefox
4. Check system microphone settings

### No AI Response
**Issue:** Command recognized but no AI processing
**Check:**
1. OpenAI API key in `.env.local`
2. Console for API errors
3. Network tab for /api/voice/process request
4. OpenAI API quota/limits

### Text-to-Speech Not Working
**Issue:** No spoken response
**Solutions:**
1. Check browser TTS support (Chrome recommended)
2. Verify system audio settings
3. Check browser console for errors
4. Ensure speakers/headphones connected

### Slow Response Times
**Issue:** Long delay before AI responds
**Expected:**
- OpenAI processing: 1-3 seconds
- Total time: 2-4 seconds end-to-end

**If slower:**
1. Check internet connection
2. Verify OpenAI API status
3. Monitor OpenAI dashboard for rate limits

---

## Development Testing

### Test OpenAI Integration Directly
```bash
curl http://localhost:3000/api/voice/process \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Add task: test API integration"}'
```

Expected response:
```json
{
  "success": true,
  "command": {
    "intent": "create_task",
    "entities": {
      "taskTitle": "test API integration"
    },
    "confidence": 0.95,
    "originalText": "Add task: test API integration"
  },
  "result": {
    "success": true,
    "task": { ... },
    "message": "Task created"
  },
  "response": "Great! I've added 'test API integration' to your task list."
}
```

### Monitor Console Logs
Key log messages to watch:
```
🎤 Voice command received: [transcript]
OpenAI processing: [intent] [confidence]
Task created: [task_id]
Cache invalidated
```

---

## Production Considerations

### Before Deploying:
1. ✅ OpenAI API key configured
2. ✅ Rate limiting implemented (built-in)
3. ✅ Error handling comprehensive
4. ✅ Fallback responses available
5. ✅ User feedback clear

### Cost Monitoring:
- **Model:** gpt-4o-mini (cost-effective)
- **Avg tokens per request:** ~200-300
- **Cost per 1M tokens:** ~$0.15 input, ~$0.60 output
- **Est. cost per command:** ~$0.0002

### Recommended Limits:
- 100 commands/day per user = ~$0.02/day
- 1000 users = ~$20/day max
- Set OpenAI usage alerts in dashboard

---

## Next Steps

1. **Test all command types** using the examples above
2. **Monitor OpenAI usage** in the API dashboard
3. **Gather user feedback** on AI response quality
4. **Iterate on prompts** to improve accuracy
5. **Add more command types** as needed

---

**Ready to Test?** Open http://localhost:3000 and try: "Add task: test the new AI voice commands!"
