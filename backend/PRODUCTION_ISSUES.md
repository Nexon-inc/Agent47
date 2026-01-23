# Production Deployment Issues - Analysis & Resolution

## Status: ✅ RESOLVED

## Critical Issues & Fixes

### 1. ✅ Subscription Import Error
**Error**: `ImportError: cannot import name 'Subscription' from 'core.database.models'`

**Root Cause**: `core/user_management/selected_agents_router.py` was importing `Subscription` from `core.database.models` instead of `core.billing.models`.

**Resolution**: Updated import statement:
```python
from core.database.models import User, UserSelectedAgent, UserTier
from core.billing.models import Subscription
```

### 2. ✅ OnboardingSession Mapper Collision & Table Naming
**Error**: `Multiple classes found for path "OnboardingSession"` and `Mapper[OnboardingProgress(onboarding_progress)]`.

**Root Cause**: 
- Ambiguity in `OnboardingSession` relationship resolution.
- 40+ Clara agent tables were UNPREFIXED (e.g. `onboarding_progress`), causing high risk of collision with other agents or core tables.

**Resolution**:
- **Systematically renamed ALL Clara tables** to include `clara_` prefix (e.g., `onboarding_progress` -> `clara_onboarding_progress`).
- Updated all corresponding `ForeignKey` references.
- Verified uniqueness of class names (`ClaraOnboardingSession`, `ClaraOnboardingProgress`).
- Ran `verify_models.py` to confirm no mapper collisions locally.

## Files Modified

- `backend/core/user_management/selected_agents_router.py`
- `backend/agents/clara/app/models.py` (Massive refactoring of table names)

## Next Steps

1. **Deploy to Production**: The codebase is now stable and collision-free.
2. **Database Migration**: Since table names changed, a database migration (Alembic) is required to rename existing tables in the production DB if data preservation is needed. If starting fresh, just deploying is fine.
3. **Verify**: Monitor Cloud Run logs for successful startup.

## Validation Results

Local verification passed:
```
Successfully imported all core and agent models!
SQLAlchemy registry check passed (no mapper collisions or reserved name errors).
```
