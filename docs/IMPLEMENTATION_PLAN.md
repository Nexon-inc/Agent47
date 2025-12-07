# Agent47 Feature Implementation Plan

## Overview
This document outlines the implementation plan for the requested features:
1. Agent-specific tabs cleanup and restructuring
2. Team management Discord-style interface
3. Voice input/output system with gender-specific voices
4. Phone number scraping and calling
5. Google Maps business targeting
6. Geo-location targeting features

---

## Phase 1: Voice System Implementation

### 1.1 Agent Voice Mapping
**Location:** `backend/core/ai/agent_voice_mapping.py`

**Agent Voice Assignments:**
- **Male Agents:**
  - Shakes: `adam` (professional, creative)
  - Eric: `arnold` (confident, sales-focused)
  - Joe: `josh` (analytical, research-focused)

- **Female Agents:**
  - Clara: `bella` (friendly, support-focused)
  - Jackie: `rachel` (energetic, marketing-focused)
  - Purity: `emily` (professional, business-focused)
  - Aria: `nova` (warm, social-focused)

**Implementation:**
- Create voice mapping service
- Integrate with Groq TTS
- Support language detection and voice selection
- Natural voice output based on user's language preference

### 1.2 Voice Input/Output System
**Location:** `backend/core/voice/voice_service.py`

**Features:**
- Speech-to-Text (STT) using Groq Whisper
- Text-to-Speech (TTS) using Groq TTS with agent-specific voices
- Real-time voice conversation support
- Language detection and automatic voice selection
- Voice quality optimization

**API Endpoints:**
- `POST /api/v1/voice/transcribe` - Convert audio to text
- `POST /api/v1/voice/synthesize` - Convert text to speech with agent voice
- `POST /api/v1/voice/conversation` - Full voice conversation with agent

---

## Phase 2: Team Management Discord-Style Interface

### 2.1 Database Schema
**New Tables:**
```sql
-- Team Agent Requests
CREATE TABLE team_agent_requests (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    team_member_id INTEGER REFERENCES users(id),
    agent_key VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    request_data JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Team Chat Messages (Discord-style)
CREATE TABLE team_chat_messages (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    user_id INTEGER REFERENCES users(id),
    agent_key VARCHAR(50),
    message_type VARCHAR(20) DEFAULT 'text', -- text, voice, file, agent_output
    content TEXT,
    audio_url TEXT,
    file_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 Frontend Updates
**Location:** `frontend/components/dashboard/tabs/team-management-tab.tsx`

**Features:**
- Discord-style chat interface
- Real-time message updates
- Agent output display
- Voice message support
- File attachments
- Message threading

---

## Phase 3: Agent Tabs Restructuring

### 3.1 Agent Tab Structure
Each agent tab should display:
1. **Agent Status & Health**
   - Online/offline status
   - Response time
   - Task completion rate
   - Error rate

2. **User's Agent Configuration**
   - Selected agent status
   - Custom instructions
   - Automation settings
   - Voice preferences

3. **Recent Activity**
   - Tasks completed
   - Requests processed
   - Outputs delivered
   - Errors encountered

4. **Performance Metrics**
   - Tasks per day/week/month
   - Average response time
   - Success rate
   - User satisfaction

5. **Quick Actions**
   - Start conversation
   - Create task
   - Configure agent
   - View history

**Files to Update:**
- `frontend/components/dashboard/tabs/aria-tab-new.tsx`
- `frontend/components/dashboard/tabs/clara-tab.tsx`
- `frontend/components/dashboard/tabs/eric-tab.tsx`
- `frontend/components/dashboard/tabs/jackie-tab.tsx`
- `frontend/components/dashboard/tabs/shakes-tab.tsx`
- `frontend/components/dashboard/tabs/joe-tab.tsx`
- `frontend/components/dashboard/tabs/purity-tab.tsx`

---

## Phase 4: Phone Number Scraping & Calling

### 4.1 Phone Scraping Service
**Location:** `backend/core/services/phone_scraping_service.py`

**Features:**
- Web scraping for phone numbers
- Google Maps business phone extraction
- Phone number validation
- Data storage and management

### 4.2 Phone Calling Service
**Location:** `backend/core/services/phone_calling_service.py`

**Features:**
- Twilio integration for voice calls
- Agent voice calling (using TTS)
- Call recording
- Call analytics
- Conversation transcription

**API Endpoints:**
- `POST /api/v1/phone/scrape` - Scrape phone numbers
- `POST /api/v1/phone/call` - Initiate agent call
- `GET /api/v1/phone/calls` - Get call history
- `GET /api/v1/phone/calls/{call_id}` - Get call details

---

## Phase 5: Google Maps Business Targeting

### 5.1 Google Maps Integration
**Location:** `backend/core/services/google_maps_service.py`

**Features:**
- Business search by location
- Business details extraction
- Phone number extraction
- Contact information gathering
- Geographic targeting

**API Endpoints:**
- `POST /api/v1/maps/search-businesses` - Search businesses
- `GET /api/v1/maps/business/{place_id}` - Get business details
- `POST /api/v1/maps/contact-business` - Contact business via agent

---

## Phase 6: Geo-location Targeting

### 6.1 Geo-location Service
**Location:** `backend/core/services/geolocation_service.py`

**Features:**
- User location tracking (with consent)
- Nearby users detection
- Location-based targeting
- Geographic analytics
- Reach amplification

**API Endpoints:**
- `POST /api/v1/geolocation/update` - Update user location
- `GET /api/v1/geolocation/nearby` - Get nearby users
- `POST /api/v1/geolocation/target` - Create geo-targeted campaign

---

## Implementation Order

1. ✅ Add voice settings to .env
2. Create agent voice mapping service
3. Fix agent-specific tabs
4. Update team management to Discord-style
5. Implement voice I/O system
6. Add phone scraping service
7. Add phone calling service
8. Add Google Maps integration
9. Add geo-location features
10. Create user admin panel

---

## Environment Variables Needed

```bash
# Voice Settings (already added to env.example)
GROQ_TTS_ENABLED=true
GROQ_STT_ENABLED=true
AGENT_VOICE_SHAKES=adam
AGENT_VOICE_ERIC=arnold
AGENT_VOICE_JOE=josh
AGENT_VOICE_CLARA=bella
AGENT_VOICE_JACKIE=rachel
AGENT_VOICE_PURITY=emily
AGENT_VOICE_ARIA=nova

# Phone Calling
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Google Maps
GOOGLE_MAPS_API_KEY=

# Geo-location
GEOLOCATION_ENABLED=true
GEOLOCATION_CONSENT_REQUIRED=true
```

---

## Next Steps

1. Create agent voice mapping service
2. Update agent tabs with new structure
3. Implement Discord-style team management
4. Add voice conversation endpoints
5. Implement phone scraping and calling
6. Add Google Maps integration
7. Implement geo-location features

