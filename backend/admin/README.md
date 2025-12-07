# Agent47 Admin Panel - Comprehensive Documentation

## Overview

The Agent47 Admin Panel is a comprehensive administrative system designed to provide full control and management capabilities for the Agent47 platform. It includes authentication, authorization, monitoring, analytics, and operational management tools.

## Architecture

The admin panel is built on a modular architecture with the following core components:

### Core Components

1. **AdminCore** (`admin_core.py`) - Central authentication, session management, and RBAC
2. **AdminRouter** (`admin_router.py`) - FastAPI routes for all admin endpoints
3. **Settings Manager** - System-wide configuration management
4. **Log Viewer** - Centralized log viewing and analysis
5. **Feature Flags Manager** - Dynamic feature toggling
6. **Cache Manager** - Cache management and optimization

### Module Structure

The admin panel is organized into 16 specialized modules:

```
backend/admin/
├── __init__.py                 # Module exports
├── admin_core.py              # Core admin functionality
├── admin_router.py            # API endpoints
├── README.md                  # This file
│
├── agents/                    # Agent Management
│   ├── agent_manager.py       # Agent lifecycle management
│   ├── agent_analytics.py     # Agent analytics
│   ├── agent_coordinator.py   # Inter-agent communication
│   ├── agent_integration_service.py  # Integration management
│   └── agent_monitor.py       # Real-time monitoring
│
├── alerts/                    # Alert Management
│   ├── alert_manager.py       # Alert creation and routing
│   ├── alert_analytics.py     # Alert pattern analysis
│   ├── escalation_manager.py  # Escalation workflows
│   └── notification_manager.py # Multi-channel notifications
│
├── analytics/                 # Business Intelligence
│   ├── analytics_manager.py   # Core analytics engine
│   ├── business_intelligence.py # Advanced BI
│   ├── performance_analytics.py # Performance metrics
│   └── user_insights.py       # User behavior analytics
│
├── cache/                     # Cache Management (NEW)
│   ├── cache_manager.py       # Cache operations and statistics
│
├── code/                      # Code Management
│   ├── code_manager.py        # Deployment management
│   ├── code_health.py         # Code quality monitoring
│   ├── error_monitor.py       # Error tracking
│   └── terminal_manager.py    # Terminal execution
│
├── communications/            # Communication Management
│   ├── communication_manager.py # Unified communication
│   ├── email_service.py       # Email management
│   ├── sms_service.py          # SMS management
│   ├── notification_manager.py # In-app notifications
│   └── template_manager.py    # Template management
│
├── database/                  # Database Administration
│   ├── database_manager.py    # Database operations
│   ├── backup_manager.py      # Backup/restore
│   ├── migration_manager.py   # Migration management
│   ├── performance_monitor.py # Performance monitoring
│   └── query_analyzer.py       # Query optimization
│
├── features/                  # Feature Flags (NEW)
│   ├── feature_flags_manager.py # Dynamic feature toggling
│
├── finance/                   # Financial Management
│   ├── finance_manager.py     # Financial operations
│   ├── revenue_tracking.py    # Revenue analytics
│   ├── financial_reporting.py # Financial reports
│   └── expense_management.py  # Expense tracking
│
├── goals/                     # Goal Management
│   ├── goal_manager.py        # Goal tracking
│   ├── goal_engine.py          # Goal automation
│   ├── goal_analytics.py       # Goal analytics
│   └── agent_coordinator.py    # Agent coordination
│
├── impersonate/               # User Impersonation
│   ├── impersonation_manager.py # Secure impersonation
│   ├── session_tracker.py     # Session tracking
│   └── audit_logger.py        # Audit logging
│
├── integrations/              # Integration Management
│   ├── integration_admin_manager.py # Integration admin
│   ├── integration_analytics.py # Integration analytics
│   ├── integration_health.py  # Health monitoring
│   └── integration_monitoring.py # Real-time monitoring
│
├── logs/                      # Log Viewer (NEW)
│   ├── log_viewer.py          # Centralized log viewing
│
├── security/                  # Security Management
│   ├── security_manager.py    # Threat detection
│   ├── access_control.py      # Access control
│   ├── audit_logging.py       # Security audit
│   └── threat_detection.py    # Advanced threat detection
│
├── servers/                   # Server Management
│   ├── server_manager.py       # Server operations
│   ├── deployment_manager.py  # Deployment automation
│   ├── monitoring_manager.py  # Server monitoring
│   └── scaling_manager.py     # Auto-scaling
│
├── settings/                  # Settings Management (NEW)
│   ├── settings_manager.py    # System configuration
│
├── support/                   # Customer Support
│   ├── support_manager.py     # Support operations
│   ├── ticket_manager.py      # Ticket management
│   ├── customer_service.py    # Customer service
│   └── knowledge_base.py      # Knowledge base
│
├── system/                    # System Administration
│   ├── system_manager.py      # System operations
│   ├── health_monitor.py      # Health monitoring
│   ├── performance_monitor.py # Performance monitoring
│   └── resource_monitor.py    # Resource monitoring
│
├── terminal/                  # Terminal Management
│   ├── terminal_manager.py    # Terminal sessions
│   ├── command_executor.py    # Command execution
│   └── session_manager.py     # Session management
│
└── users/                     # User Administration
    ├── user_admin_manager.py  # User management
    ├── user_analytics.py      # User analytics
    ├── user_moderation.py     # User moderation
    └── user_support.py        # User support tools
```

## Authentication & Authorization

### Permission Levels

The admin panel uses a Role-Based Access Control (RBAC) system with four permission levels:

1. **READ_ONLY** - View-only access to system information
2. **BASIC_ADMIN** - Can read and update non-critical resources
3. **SYSTEM_ADMIN** - Can create, read, and update most resources (except security/system)
4. **SUPER_ADMIN** - Full access to all features and can manage other admin users

### Default Super Admin

- **Email**: `agent47assist@gmail.com`
- **Password**: `G.z.t.i.p.0,1,0`
- **Permissions**: SUPER_ADMIN (full access)

### Session Management

- Session timeout: Configurable (default: 24 hours)
- Session storage: Database + in-memory cache
- Session cleanup: Automatic cleanup of expired sessions

## New Features

### 1. Settings Manager

**Location**: `backend/admin/settings/settings_manager.py`

**Purpose**: Manage system-wide configuration settings with versioning and audit trails.

**Key Features**:
- Setting categories: General, Security, Billing, Integrations, Notifications, Performance, Features, AI Services
- Setting types: String, Integer, Float, Boolean, JSON, Array
- Change history tracking
- Value validation
- Rollback capability
- Default settings initialization

**Usage Example**:
```python
from backend.admin import get_settings_manager

settings_manager = await get_settings_manager()

# Get a setting
maintenance_mode = await settings_manager.get_setting("system.maintenance_mode", default=False)

# Update a setting
await settings_manager.update_setting(
    "system.max_login_attempts",
    value=10,
    updated_by="admin_user_id",
    change_reason="Increased security threshold"
)

# Get setting history
history = await settings_manager.get_setting_history("system.max_login_attempts", limit=50)
```

**Default Settings**:
- `system.maintenance_mode` - Enable/disable maintenance mode
- `system.max_login_attempts` - Maximum login attempts (3-10)
- `system.session_timeout_hours` - Session timeout (1-168 hours)
- `billing.free_tier_llm_tokens` - Free tier token limit
- `billing.starter_tier_llm_tokens` - Starter tier token limit
- `billing.pro_tier_llm_tokens` - Pro tier token limit
- `ai.groq_enabled` - Enable Groq AI services
- `ai.openai_enabled` - Enable OpenAI services
- `ai.ollama_enabled` - Enable Ollama services
- `notifications.email_enabled` - Enable email notifications
- `notifications.sms_enabled` - Enable SMS notifications
- `performance.rate_limit_per_minute` - API rate limit (1-1000)
- `features.user_registration_enabled` - Enable user registration
- `features.agent_intercommunication` - Enable agent intercommunication

### 2. Log Viewer

**Location**: `backend/admin/logs/log_viewer.py`

**Purpose**: Centralized log viewing, filtering, and analysis.

**Key Features**:
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log sources: System, Agent, API, Database, Auth, Billing, Integration
- Advanced filtering (level, source, module, text search, user, time range)
- Log statistics and analytics
- Export capabilities (JSON, CSV)
- Automatic log cleanup (configurable retention: default 30 days)
- Buffered logging for performance

**Usage Example**:
```python
from backend.admin import get_log_viewer
from backend.admin.logs.log_viewer import LogFilter, LogLevel, LogSource

log_viewer = await get_log_viewer()

# Get error logs
error_logs = await log_viewer.get_error_logs(hours=24, limit=100)

# Search logs
filter = LogFilter(
    levels=[LogLevel.ERROR, LogLevel.CRITICAL],
    sources=[LogSource.SYSTEM, LogSource.API],
    search_text="authentication",
    start_time=datetime.utcnow() - timedelta(hours=1)
)
logs, total = await log_viewer.get_logs(filter, page=1, limit=50)

# Get log statistics
stats = await log_viewer.get_log_statistics(
    start_time=datetime.utcnow() - timedelta(days=1)
)

# Export logs
export_data = await log_viewer.export_logs(filter, format="json")
```

**Database Tables**:
- `admin_logs` - Main log storage with indexes on timestamp, level, source, module, user_id

### 3. Feature Flags Manager

**Location**: `backend/admin/features/feature_flags_manager.py`

**Purpose**: Dynamic feature toggling with user/tier-based targeting.

**Key Features**:
- Feature flag statuses: Enabled, Disabled, Rolling Out
- Targeting types:
  - All Users - Enable for everyone
  - Percentage - Gradual rollout (0-100%)
  - User IDs - Specific user targeting
  - User Tiers - Tier-based targeting (Free, Starter, Pro)
  - Custom - Custom targeting logic
- Evaluation caching (5-minute TTL)
- Evaluation logging and statistics
- Consistent user experience (hash-based percentage)

**Usage Example**:
```python
from backend.admin import get_feature_flags_manager
from backend.admin.features.feature_flags_manager import (
    FeatureFlagStatus, TargetingType
)

flags_manager = await get_feature_flags_manager()

# Create a feature flag
await flags_manager.create_feature_flag(
    key="new_dashboard_ui",
    name="New Dashboard UI",
    description="Enable the new dashboard interface",
    created_by="admin_user_id",
    status=FeatureFlagStatus.ROLLING_OUT,
    targeting_type=TargetingType.PERCENTAGE,
    targeting_config={"percentage": 25.0}
)

# Update feature flag
await flags_manager.update_feature_flag(
    "new_dashboard_ui",
    updates={"enabled_percentage": 50.0},
    updated_by="admin_user_id"
)

# Check if feature is enabled for a user
evaluation = await flags_manager.is_feature_enabled(
    "new_dashboard_ui",
    user_id="user_123",
    user_tier="pro"
)

if evaluation.enabled:
    print(f"Feature enabled: {evaluation.reason}")

# Get feature flag statistics
stats = await flags_manager.get_feature_flag_statistics("new_dashboard_ui", hours=24)
```

**Database Tables**:
- `feature_flags` - Feature flag definitions
- `feature_flag_evaluations` - Evaluation history

### 4. Cache Manager

**Location**: `backend/admin/cache/cache_manager.py`

**Purpose**: Cache management, statistics, and optimization.

**Key Features**:
- Cache statistics (keys, size, hit rate, memory usage)
- Cache key browsing by pattern
- Cache clearing (by pattern, category, or all)
- Cache health monitoring
- Cache optimization
- Historical statistics
- Category-based cache management

**Usage Example**:
```python
from backend.admin import get_cache_manager

cache_manager = await get_cache_manager()

# Get cache statistics
stats = await cache_manager.get_cache_statistics()
print(f"Total keys: {stats['redis']['total_keys']}")
print(f"Hit rate: {stats['redis']['hit_rate']}%")

# Get cache keys by pattern
keys = await cache_manager.get_cache_keys(pattern="user:*", limit=100)

# Clear cache by category
deleted = await cache_manager.clear_cache_by_category("user")

# Get cache health
health = await cache_manager.get_cache_health()
print(f"Status: {health['status']}")
print(f"Memory usage: {health['memory_usage_mb']} MB")

# Optimize cache
result = await cache_manager.optimize_cache()

# Get cache history
history = await cache_manager.get_cache_history(hours=24)
```

**Cache Categories**:
- `user` - User-related cache
- `session` - Session cache
- `agent` - Agent-related cache
- `setting` - Settings cache
- `feature_flag` - Feature flag cache
- `rate_limit` - Rate limiting cache

**Database Tables**:
- `cache_statistics` - Historical cache statistics

## API Endpoints

All admin endpoints are prefixed with `/admin` and require authentication.

### Authentication
- `POST /admin/login` - Admin login
- `POST /admin/logout` - Admin logout
- `GET /admin/me` - Get current admin info

### System Health
- `GET /admin/health` - System health status
- `GET /admin/metrics` - Admin metrics

### Agent Management
- `GET /admin/agents` - List all agents
- `POST /admin/agents/{name}/restart` - Restart agent
- `GET /admin/agents/{name}/logs` - Get agent logs

### User Management
- `GET /admin/users` - List users (paginated)
- `GET /admin/users/{id}` - Get user details
- `PUT /admin/users/{id}/status` - Update user status

### Database
- `GET /admin/database/status` - Database status
- `POST /admin/database/backup` - Create backup

### Analytics
- `GET /admin/analytics/overview` - Analytics overview
- `GET /admin/analytics/users` - User analytics

### System
- `GET /admin/system/status` - System status
- `POST /admin/system/cleanup` - System cleanup

### Security
- `GET /admin/security/audit-logs` - Security audit logs
- `GET /admin/security/threats` - Security threats

### Admin Management (Super Admin Only)
- `GET /admin/admins` - List all admin users
- `POST /admin/admins/create` - Create admin user
- `PUT /admin/admins/{id}/permissions` - Update permissions
- `DELETE /admin/admins/{id}` - Deactivate admin user

## Database Schema

### Core Tables

#### `admin_users`
Stores admin user accounts and permissions.

```sql
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    session_token VARCHAR(500)
);
```

#### `admin_sessions`
Tracks active admin sessions.

```sql
CREATE TABLE admin_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    admin_user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### `admin_actions`
Audit log of all admin actions.

```sql
CREATE TABLE admin_actions (
    id SERIAL PRIMARY KEY,
    admin_user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

### New Tables

#### `system_settings`
System-wide configuration settings.

```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    validation_rules JSONB,
    default_value TEXT,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `setting_changes`
History of setting changes.

```sql
CREATE TABLE setting_changes (
    id VARCHAR(255) PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255) NOT NULL,
    change_reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reverted BOOLEAN DEFAULT FALSE
);
```

#### `admin_logs`
Centralized log storage.

```sql
CREATE TABLE admin_logs (
    id VARCHAR(255) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    module VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    user_id VARCHAR(255),
    request_id VARCHAR(255),
    ip_address INET,
    metadata JSONB,
    stack_trace TEXT
);
```

#### `feature_flags`
Feature flag definitions.

```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    targeting_type VARCHAR(50) NOT NULL,
    targeting_config JSONB NOT NULL,
    enabled_percentage DECIMAL(5,2) DEFAULT 0.0,
    enabled_user_ids JSONB DEFAULT '[]',
    enabled_tiers JSONB DEFAULT '[]',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

#### `feature_flag_evaluations`
Feature flag evaluation history.

```sql
CREATE TABLE feature_flag_evaluations (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    user_tier VARCHAR(50),
    enabled BOOLEAN NOT NULL,
    reason TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `cache_statistics`
Historical cache statistics.

```sql
CREATE TABLE cache_statistics (
    id SERIAL PRIMARY KEY,
    cache_type VARCHAR(50) NOT NULL,
    total_keys INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    hit_count BIGINT DEFAULT 0,
    miss_count BIGINT DEFAULT 0,
    eviction_count INTEGER DEFAULT 0,
    memory_usage_mb DECIMAL(10,2) DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Features

### Threat Detection
- Brute force detection (5 failed attempts in 15 minutes)
- SQL injection detection (pattern matching)
- XSS attack detection (pattern matching)
- Rate limit violations
- IP reputation tracking
- Automatic IP blocking

### Audit Logging
- All admin actions are logged
- User impersonation tracking
- Setting change history
- Feature flag evaluation logging
- Security event logging

### Access Control
- Role-based permissions
- Resource-level access control
- IP whitelisting (configurable)
- Session timeout enforcement
- Two-factor authentication support (configurable)

## Best Practices

### 1. Settings Management
- Always provide a change reason when updating settings
- Review setting history before making changes
- Test changes in a staging environment first
- Use validation rules to prevent invalid values

### 2. Feature Flags
- Use percentage-based rollout for gradual feature releases
- Monitor feature flag statistics regularly
- Clean up unused feature flags
- Document feature flag purposes

### 3. Log Management
- Set appropriate log retention periods
- Monitor error rates regularly
- Use log filters to find specific issues
- Export logs for compliance requirements

### 4. Cache Management
- Monitor cache hit rates (target: >80%)
- Clear cache by category when needed
- Optimize cache regularly
- Monitor memory usage

### 5. Security
- Review security alerts regularly
- Monitor IP reputation scores
- Keep audit logs for compliance
- Use impersonation sparingly and document reasons

## Initialization

The admin system is initialized automatically when the application starts:

```python
# In backend/main.py
from backend.admin import init_admin_core

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... other initialization ...
    
    # Initialize admin system
    await init_admin_core()
    logger.info("Admin system initialized successfully")
    
    yield
    
    # Cleanup
    admin_core = await get_admin_core()
    await admin_core.shutdown()
```

## Error Handling

All admin modules include comprehensive error handling:
- Database connection failures
- Redis unavailability (graceful degradation)
- Invalid input validation
- Permission checks
- Audit logging of errors

## Performance Considerations

- **Log Buffering**: Logs are buffered and flushed in batches (1000 entries)
- **Cache Evaluation**: Feature flag evaluations are cached for 5 minutes
- **Statistics Collection**: Cache statistics collected every 5 minutes
- **Log Cleanup**: Old logs cleaned up automatically (default: 30 days retention)
- **Database Indexes**: All frequently queried columns are indexed

## Monitoring & Alerts

The admin panel provides comprehensive monitoring:
- System health checks
- Performance metrics
- Error rates
- Cache statistics
- Security alerts
- User activity logs

## Support & Troubleshooting

### Common Issues

1. **Admin login fails**
   - Verify email and password
   - Check if user exists in `admin_users` table
   - Verify user has `is_active = TRUE`

2. **Permission denied**
   - Check user's permission level
   - Verify required permission for the action
   - Super Admin bypasses all checks

3. **Settings not updating**
   - Check validation rules
   - Verify setting exists
   - Check database connection

4. **Feature flag not working**
   - Verify flag status (ENABLED, DISABLED, ROLLING_OUT)
   - Check targeting configuration
   - Review evaluation logs

5. **Cache issues**
   - Check Redis connection
   - Verify cache keys exist
   - Check memory usage

## Future Enhancements

Potential improvements for the admin panel:
- Real-time dashboard with live metrics
- Advanced analytics with machine learning
- Automated alerting and notifications
- Bulk operations for user management
- Custom report builder
- API rate limiting configuration UI
- Integration marketplace management
- Advanced search across all resources

## License

This admin panel is part of the Agent47 platform and follows the same license terms.

---

**Last Updated**: 2025-01-07
**Version**: 1.0.0
**Maintainer**: Agent47 Development Team

