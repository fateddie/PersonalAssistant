#!/bin/bash
# Test Google Calendar Integration
# Usage: ./scripts/test-calendar.sh

echo "🧪 Testing Google Calendar Integration"
echo "======================================"
echo ""

# Check if backend is running
echo "1️⃣ Checking backend status..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend not running. Start with: ./scripts/start.sh"
    exit 1
fi

echo ""
echo "2️⃣ Checking calendar configuration..."
STATUS=$(curl -s http://localhost:8000/calendar/status)
ENABLED=$(echo $STATUS | grep -o '"enabled":[^,]*' | cut -d':' -f2)
AUTHENTICATED=$(echo $STATUS | grep -o '"authenticated":[^,]*' | cut -d':' -f2)

echo "Calendar enabled: $ENABLED"
echo "Authenticated: $AUTHENTICATED"

if [ "$ENABLED" = "false" ]; then
    echo ""
    echo "⚠️  Calendar not enabled. Steps to enable:"
    echo "1. Update config/.env:"
    echo "   GOOGLE_CALENDAR_ENABLED=true"
    echo "2. Add your Google credentials"
    echo "3. Restart: ./scripts/start.sh"
    exit 1
fi

if [ "$AUTHENTICATED" = "false" ]; then
    echo ""
    echo "⚠️  Not authenticated with Google. Next step:"
    echo "Visit: http://localhost:8000/calendar/auth"
    exit 1
fi

echo ""
echo "3️⃣ Testing calendar access..."
CALENDARS=$(curl -s http://localhost:8000/calendar/calendars)
if echo $CALENDARS | grep -q '"id"'; then
    CAL_COUNT=$(echo $CALENDARS | grep -o '"id"' | wc -l | tr -d ' ')
    echo "✅ Successfully connected to $CAL_COUNT calendar(s)"
else
    echo "❌ Could not access calendars"
    echo "Response: $CALENDARS"
    exit 1
fi

echo ""
echo "4️⃣ Checking detected events..."
EVENTS=$(curl -s "http://localhost:8000/emails/events?status=approved")
APPROVED_COUNT=$(echo $EVENTS | grep -o '"id"' | wc -l | tr -d ' ')
echo "Found $APPROVED_COUNT approved event(s)"

if [ "$APPROVED_COUNT" -gt 0 ]; then
    echo ""
    echo "5️⃣ Ready to create calendar events!"
    echo ""
    echo "To add first approved event to calendar:"
    echo "  curl -X POST http://localhost:8000/calendar/events/create-from-detected/1"
    echo ""
    echo "Or test in Streamlit:"
    echo "  1. Visit http://localhost:8501"
    echo "  2. Type: 'show events'"
    echo "  3. Note the Event ID"
    echo "  4. Use API to add to calendar"
fi

echo ""
echo "======================================"
echo "✅ Calendar integration test complete!"
