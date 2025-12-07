# Agent47 Setup Instructions

## ✅ Completed Features

All backend services have been implemented and connected:

1. ✅ **Database Migration** - Team agent requests and chat messages
2. ✅ **Team Management** - Discord-style chat interface
3. ✅ **Voice I/O System** - Unified voice conversations with agents
4. ✅ **Phone Scraping** - Scrape phone numbers from URLs and Google Maps
5. ✅ **Phone Calling** - Make calls with agent voices via Twilio
6. ✅ **Google Maps Integration** - Business search and contact
7. ✅ **Geo-location Service** - User location tracking and nearby users
8. ✅ **User Admin Panel** - Comprehensive dashboard for user's agents

## 🚀 Setup Steps (Server Not Running)

### Step 1: Run Database Migration

```bash
cd backend
python migrations/add_team_agent_requests.py
```

This will create:
- `team_agent_requests` table
- `team_chat_messages` table
- All necessary indexes

### Step 2: Verify Setup

```bash
python scripts/verify_setup.py
```

This will check:
- ✅ All imports are working
- ✅ Environment variables are set
- ✅ Services are properly configured
- ⚠️  Warns about missing optional API keys

### Step 3: Configure Environment Variables (Optional)

Add to your `.env` file (copy from `env.example`):

```bash
# Google Maps (for business targeting)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_MAPS_ENABLED=true

# Twilio (for phone calling)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
TWILIO_ENABLED=true

# Phone Scraping
PHONE_SCRAPING_ENABLED=true
PHONE_SCRAPING_RATE_LIMIT=100

# Geo-location
GEOLOCATION_ENABLED=true
GEOLOCATION_CONSENT_REQUIRED=true
```

**Note:** These are optional. Features will be disabled if not configured, but the server will still run.

### Step 4: Start the Server

```bash
python backend/main.py
```

Or using uvicorn:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📋 New API Endpoints

### Team Management
- `POST /api/v1/team/agent-requests/create` - Create agent request
- `GET /api/v1/team/agent-requests` - Get team agent requests
- `GET /api/v1/team/agent-requests/{request_id}` - Get specific request
- `POST /api/v1/team/chat/message` - Send chat message
- `POST /api/v1/team/chat/message/voice` - Send voice message
- `GET /api/v1/team/chat/messages` - Get chat messages
- `POST /api/v1/team/chat/agent-output` - Post agent output

### Voice I/O
- `POST /voice/transcribe` - Transcribe audio to text
- `POST /voice/synthesize` - Convert text to speech with agent voice
- `POST /voice/conversation` - Full voice conversation

### Phone Services
- `POST /phone/scrape` - Scrape phone numbers from URL
- `POST /phone/scrape/google-maps` - Scrape from Google Maps
- `POST /phone/call` - Make agent voice call
- `GET /phone/calls` - Get call history
- `GET /phone/calls/{call_sid}` - Get call details

### Google Maps
- `POST /maps/search-businesses` - Search for businesses
- `GET /maps/business/{place_id}` - Get business details
- `POST /maps/contact-business` - Contact business via agent
- `POST /maps/nearby-businesses` - Find nearby businesses

### Geo-location
- `POST /geolocation/update-location` - Update user location
- `GET /geolocation/nearby-users` - Get nearby users

### User Admin Panel
- `GET /api/v1/user-admin/dashboard` - Get comprehensive dashboard
- `GET /api/v1/user-admin/agents/{agent_key}/details` - Get agent details
- `GET /api/v1/user-admin/tasks` - Get user tasks
- `GET /api/v1/user-admin/analytics` - Get user analytics

## 🔧 Troubleshooting

### Migration Fails
- Check database connection in `.env` (SUPABASE_DB_URL)
- Ensure database is accessible
- Check that `teams` and `users` tables exist

### Import Errors
- Run `python scripts/verify_setup.py` to check all imports
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`

### Service Not Available
- Check environment variables are set correctly
- Services will log warnings if not configured (this is normal)
- Features will be disabled but server will still run

## 📝 Notes

- All services use real implementations (no mocks)
- Services wait for dependencies (e.g., agent responses before posting to chat)
- Background processor handles team-agent requests automatically
- All routers are registered in `main.py`

## 🎯 Next Steps After Server Starts

1. Test endpoints using `/docs` (Swagger UI)
2. Connect frontend to new endpoints
3. Configure API keys for full functionality
4. Monitor logs for any initialization issues

