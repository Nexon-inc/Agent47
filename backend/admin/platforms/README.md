# Agent47 Platform Connection System

## Overview

This system allows Agent47 (the organization) to connect its own platform accounts (Twitter, LinkedIn, Instagram, etc.) and grant all 7 agents (Aria, Clara, Eric, Joe, Jackie, Shakes, Purity) full access to post, engage, and manage content on these platforms on Agent47's behalf.

## Key Features

### 1. System-Level Platform Connections
- **Separate from user accounts**: These are Agent47's own platform accounts, not user accounts
- **Multiple accounts per platform**: Can connect multiple accounts (e.g., "Agent47 Official", "Agent47 Support")
- **Secure credential storage**: Credentials are encrypted and stored securely
- **Connection status tracking**: Monitor connection health and status

### 2. Agent-Platform Assignments
- **Automatic assignment**: All 7 agents are automatically assigned to new platform connections
- **Granular permissions**: Control what each agent can do (post, read, engage, analyze, schedule)
- **Priority system**: Set agent priorities for platform access
- **Usage tracking**: Monitor which agents use which platforms and how often

### 3. Agent Posting Service
- **Simple API**: Agents can easily post to Agent47's platforms
- **Permission checks**: Automatic permission validation before posting
- **Activity logging**: All agent activities are logged for audit purposes
- **Post tracking**: Track all posts made by agents with engagement metrics

## Architecture

### Database Models

#### `system_platform_credentials`
Stores Agent47's platform account credentials.

```sql
CREATE TABLE system_platform_credentials (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_handle VARCHAR(255),
    credential_type VARCHAR(50) NOT NULL,
    access_token TEXT,  -- Encrypted
    refresh_token TEXT,  -- Encrypted
    api_key VARCHAR(500),  -- Encrypted
    api_secret VARCHAR(500),  -- Encrypted
    bearer_token TEXT,  -- Encrypted
    expires_at TIMESTAMP,
    scopes JSONB,
    status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP,
    last_used_by_agent VARCHAR(50),
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `agent_platform_assignments`
Tracks which agents have access to which platform connections.

```sql
CREATE TABLE agent_platform_assignments (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    metadata JSONB
);
```

#### `system_platform_posts`
Tracks all posts made by agents on Agent47's platforms.

```sql
CREATE TABLE system_platform_posts (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    platform_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    media_urls JSONB,
    post_type VARCHAR(50),
    scheduled_time TIMESTAMP,
    posted_at TIMESTAMP,
    platform_post_id VARCHAR(255),
    platform_post_url VARCHAR(500),
    status VARCHAR(50),
    error_message TEXT,
    engagement_metrics JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `system_platform_activities`
Logs all agent activities on platforms.

```sql
CREATE TABLE system_platform_activities (
    id SERIAL PRIMARY KEY,
    credential_id INTEGER NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    platform_id INTEGER NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

## Usage

### For Admins (Admin Panel)

#### Connect a Platform

```python
# Via Admin API
POST /admin/platforms/connect
{
    "platform_name": "twitter",
    "account_name": "Agent47 Official",
    "account_handle": "@agent47",
    "credentials": {
        "type": "oauth2",
        "access_token": "...",
        "refresh_token": "...",
        "expires_at": "2025-12-31T23:59:59Z",
        "scopes": ["tweet.read", "tweet.write"]
    }
}
```

#### View All Connections

```python
GET /admin/platforms/connections?active_only=true
```

#### Assign Agent to Platform

```python
POST /admin/platforms/{credential_id}/assign-agent
{
    "agent_name": "aria",
    "permissions": {
        "can_post": true,
        "can_read": true,
        "can_engage": true,
        "can_analyze": true,
        "can_schedule": true
    },
    "priority": 10
}
```

#### Get Agent Platforms

```python
GET /admin/platforms/agents/aria
```

### For Agents (In Agent Code)

#### Get Available Platforms

```python
from backend.core.platforms import get_agent_platform_service

# In an agent's service
platform_service = await get_agent_platform_service("aria")
platforms = await platform_service.get_available_platforms()

# Returns:
# [
#     {
#         "credential_id": 1,
#         "platform_name": "twitter",
#         "platform_display_name": "Twitter (X)",
#         "account_name": "Agent47 Official",
#         "account_handle": "@agent47",
#         "permissions": {
#             "can_post": true,
#             "can_read": true,
#             "can_engage": true,
#             "can_analyze": true,
#             "can_schedule": true
#         },
#         "priority": 0,
#         "usage_count": 5
#     },
#     ...
# ]
```

#### Post to Platform

```python
from backend.core.platforms import get_agent_platform_service
from datetime import datetime

platform_service = await get_agent_platform_service("aria")

# Post immediately
result = await platform_service.post(
    platform_name="twitter",
    content="Exciting news! Agent47 is now live! 🚀 #AI #Automation",
    media_urls=["https://example.com/image.jpg"]
)

# Schedule a post
scheduled_time = datetime(2025, 1, 15, 10, 0, 0)
result = await platform_service.post(
    platform_name="linkedin",
    content="Join us for our product launch webinar!",
    scheduled_time=scheduled_time
)

# Check if agent can post
can_post = await platform_service.can_post_to("twitter")
```

## Admin Panel Endpoints

All endpoints require Super Admin authentication.

### Platform Management
- `GET /admin/platforms/available` - Get all available platforms
- `GET /admin/platforms/connections` - Get all Agent47 platform connections
- `POST /admin/platforms/connect` - Connect Agent47 to a platform
- `POST /admin/platforms/{credential_id}/disconnect` - Disconnect a platform

### Agent Assignment
- `GET /admin/platforms/agents` - Get platforms for all agents
- `GET /admin/platforms/agents/{agent_name}` - Get platforms for a specific agent
- `POST /admin/platforms/{credential_id}/assign-agent` - Assign agent to platform
- `DELETE /admin/platforms/{credential_id}/agents/{agent_name}` - Remove agent from platform
- `PUT /admin/platforms/{credential_id}/agents/{agent_name}/permissions` - Update agent permissions

### Statistics
- `GET /admin/platforms/statistics` - Get platform usage statistics

## Agent Integration Examples

### Aria (Social Media Agent)

```python
# In aria_chat_service.py or aria's posting service
from backend.core.platforms import get_agent_platform_service

async def post_to_agent47_accounts(self, content: str, platforms: List[str] = None):
    """Post content to Agent47's social media accounts"""
    platform_service = await get_agent_platform_service("aria")
    
    # Get available platforms
    available = await platform_service.get_available_platforms()
    
    # Filter by requested platforms or use all
    target_platforms = platforms or [p["platform_name"] for p in available]
    
    results = []
    for platform_name in target_platforms:
        if await platform_service.can_post_to(platform_name):
            result = await platform_service.post(
                platform_name=platform_name,
                content=content
            )
            results.append(result)
    
    return results
```

### Eric (Sales Agent)

```python
# In eric's outreach service
from backend.core.platforms import get_agent_platform_service

async def post_sales_content(self, content: str):
    """Post sales content to Agent47's LinkedIn"""
    platform_service = await get_agent_platform_service("eric")
    
    result = await platform_service.post(
        platform_name="linkedin",
        content=content
    )
    
    return result
```

### Jackie (Marketing Agent)

```python
# In jackie's marketing service
from backend.core.platforms import get_agent_platform_service

async def launch_campaign(self, content: str, platforms: List[str]):
    """Launch marketing campaign across multiple platforms"""
    platform_service = await get_agent_platform_service("jackie")
    
    results = []
    for platform in platforms:
        result = await platform_service.post(
            platform_name=platform,
            content=content
        )
        results.append(result)
    
    return results
```

## Security Features

1. **Credential Encryption**: All platform credentials are encrypted at rest
2. **Permission-Based Access**: Agents can only perform actions they have permission for
3. **Activity Logging**: All agent activities are logged for audit purposes
4. **Super Admin Only**: Only Super Admins can manage platform connections
5. **Usage Tracking**: Monitor which agents use which platforms

## Default Behavior

When a new platform is connected:
1. All 7 agents are automatically assigned with full permissions
2. Agents can immediately start posting
3. All activities are logged
4. Usage statistics are tracked

## Permissions

Each agent can have different permissions per platform:

- `can_post`: Post content to the platform
- `can_read`: Read content from the platform
- `can_engage`: Like, comment, share content
- `can_analyze`: Access analytics and metrics
- `can_schedule`: Schedule posts
- `can_moderate`: Moderate content (restricted)
- `can_delete`: Delete posts (restricted)

## Statistics & Monitoring

The system tracks:
- Total platform connections
- Total posts made by agents
- Agent usage per platform
- Post engagement metrics
- Activity logs
- Error rates

## Integration with Existing Platform System

This system works alongside the existing user platform connection system:
- **User Platform Connections**: Users connect their own accounts (via `platform_credentials` table)
- **System Platform Connections**: Agent47 connects its own accounts (via `system_platform_credentials` table)
- **Agents can use both**: Agents can post to both user accounts and Agent47's accounts

## Next Steps

1. **Frontend Admin Panel**: Connect the admin panel frontend to these endpoints
2. **OAuth Flow**: Implement OAuth flow for connecting platforms through the admin panel
3. **Platform API Integration**: Complete the actual platform API integration in `_make_platform_post`
4. **Analytics Dashboard**: Build analytics dashboard for platform performance
5. **Automated Posting**: Implement automated posting based on triggers/events

---

**Last Updated**: 2025-01-07
**Version**: 1.0.0

