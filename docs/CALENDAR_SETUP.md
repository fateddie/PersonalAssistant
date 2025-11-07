# Google Calendar Integration Setup

Complete guide to enable Google Calendar integration in AskSharon.ai.

---

## 🎯 Overview

The calendar integration allows you to:
- ✅ Automatically add detected events (from emails) to your Google Calendar
- ✅ View your upcoming calendar events
- ✅ Check for scheduling conflicts
- ✅ Create new calendar events via API

---

## 📋 Prerequisites

- Google account with Calendar access
- AskSharon.ai backend running (http://localhost:8000)
- 10-15 minutes for setup

---

## 🚀 Setup Steps

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `AskSharon Calendar`
4. Click **"Create"**
5. Wait for project creation (10-15 seconds)

### Step 2: Enable Google Calendar API

1. In the Cloud Console, select your project
2. Click **"APIs & Services"** → **"Enable APIs and Services"**
3. Search for: `Google Calendar API`
4. Click on **"Google Calendar API"**
5. Click **"Enable"**
6. Wait for activation

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** (unless you have Google Workspace)
3. Click **"Create"**
4. Fill in required fields:
   - **App name**: `AskSharon.ai`
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **"Save and Continue"**
6. **Scopes**: Click "Add or Remove Scopes"
   - Search for: `.../auth/calendar`
   - Check: `https://www.googleapis.com/auth/calendar`
   - Click **"Update"**
   - Click **"Save and Continue"**
7. **Test users**: Add your Google account email
   - Click **"Add Users"**
   - Enter your email
   - Click **"Add"**
   - Click **"Save and Continue"**
8. Review and click **"Back to Dashboard"**

### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Web application"**
4. Name: `AskSharon Local`
5. **Authorized redirect URIs**:
   - Click **"Add URI"**
   - Enter: `http://localhost:8000/calendar/oauth/callback`
   - Click **"Add URI"**
   - Enter: `http://127.0.0.1:8000/calendar/oauth/callback` (backup)
6. Click **"Create"**
7. **Save your credentials**:
   - Copy **"Client ID"** (ends with `.apps.googleusercontent.com`)
   - Copy **"Client secret"**
   - Click **"OK"**

### Step 5: Configure AskSharon.ai

1. Open `config/.env` in a text editor
2. Update these lines:

```bash
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/calendar/oauth/callback
```

3. Replace `your-client-id` and `your-client-secret` with values from Step 4
4. Save the file

### Step 6: Restart AskSharon.ai

```bash
./scripts/stop.sh
./scripts/start.sh
```

### Step 7: Authenticate with Google

1. Open your browser to: http://localhost:8000/calendar/auth
2. You'll be redirected to Google's consent screen
3. **If you see "This app isn't verified"**:
   - Click **"Advanced"**
   - Click **"Go to AskSharon.ai (unsafe)"** (it's safe, it's your app!)
4. Select your Google account
5. Review permissions and click **"Allow"**
6. You'll be redirected back to AskSharon
7. You should see: `{"status": "success", "message": "Google Calendar connected!"}`

---

## ✅ Verify Setup

Test the integration:

```bash
# Check calendar status
curl http://localhost:8000/calendar/status

# Expected response:
# {
#   "enabled": true,
#   "authenticated": true,
#   "token_expires": "2025-12-06T...",
#   "setup_url": null
# }

# List your calendars
curl http://localhost:8000/calendar/calendars

# List upcoming events
curl "http://localhost:8000/calendar/events?max_results=5"
```

---

## 🎉 Start Using Calendar Integration

### 1. Detect Events from Emails

In the Streamlit UI (http://localhost:8501), type:

```
detect events
```

This scans your recent emails for meetings, webinars, deadlines.

### 2. View Detected Events

```
show events
```

You'll see events with Event IDs.

### 3. Approve and Add to Calendar

Via API:
```bash
# Approve event #1
curl -X POST http://localhost:8000/emails/events/1/approve

# Add approved event to Google Calendar
curl -X POST http://localhost:8000/calendar/events/create-from-detected/1
```

The event is now in your Google Calendar! 🎉

---

## 🔧 Troubleshooting

### "This app isn't verified"
**Solution**: Click "Advanced" → "Go to AskSharon.ai (unsafe)". This is normal for personal apps.

### "Access blocked: This app's request is invalid"
**Solution**: Check that redirect URI exactly matches: `http://localhost:8000/calendar/oauth/callback`

### "Error 401: Not authenticated"
**Solution**: Visit http://localhost:8000/calendar/auth to re-authenticate

### "Error 403: Calendar API has not been used"
**Solution**:
1. Go to Google Cloud Console
2. Enable Google Calendar API
3. Wait 1-2 minutes for propagation

### Token expired
**Solution**: Tokens auto-refresh. If issues persist, delete `config/google_calendar_token.json` and re-authenticate.

---

## 🔒 Security Notes

- **OAuth tokens** are stored in `config/google_calendar_token.json`
- **Never commit** this file to git (already in .gitignore)
- Tokens have **read/write access** to your calendar
- **Rotate credentials** if compromised via Google Cloud Console

---

## 📚 API Reference

### Calendar Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/calendar/status` | GET | Check connection status |
| `/calendar/auth` | GET | Start OAuth flow |
| `/calendar/calendars` | GET | List user's calendars |
| `/calendar/events` | GET | List upcoming events |
| `/calendar/events/create` | POST | Create new event |
| `/calendar/events/create-from-detected/{id}` | POST | Add detected event to calendar |
| `/calendar/conflicts` | GET | Check for scheduling conflicts |

### Full API Docs

Visit: http://localhost:8000/docs

---

## 🎯 Next Steps

- **Automatic sync**: Approved email events auto-add to calendar
- **Conflict detection**: Get warned before double-booking
- **Two-way sync**: Calendar events → AskSharon tasks (Phase 4)

---

## 📞 Need Help?

- Check logs: `tail -f logs/backend.log`
- API documentation: http://localhost:8000/docs
- Verify config: `cat config/.env | grep GOOGLE`

---

**Status**: Phase 3 - Active Development ✅
