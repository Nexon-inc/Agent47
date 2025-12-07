import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.event_bus import get_kafka, KafkaManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings
from backend.core.user_management import get_user_manager, UserManager
from backend.core.billing import get_billing_manager, BillingManager

logger = get_logger(__name__)

class UserAction(Enum):
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    DELETE = "delete"
    MODIFY_TIER = "modify_tier"
    RESET_PASSWORD = "reset_password"
    BLOCK_IP = "block_ip"
    WARN = "warn"

class UserStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DELETED = "deleted"
    BANNED = "banned"

@dataclass
class UserAuditLog:
    id: str
    user_id: str
    admin_id: str
    action: UserAction
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: str = ""
    user_agent: str = ""

@dataclass
class UserReport:
    id: str
    reporter_id: str
    reported_user_id: str
    reason: str
    description: str
    evidence: List[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class UserAdminManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.user_manager: Optional[UserManager] = None
        self.billing_manager: Optional[BillingManager] = None
        self.settings = get_settings()

        self.user_audit_logs: Dict[str, UserAuditLog] = {}
        self.user_reports: Dict[str, UserReport] = {}
        self.suspended_users: Dict[str, Dict[str, Any]] = {}
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing UserAdminManager...")

            self.database = get_database()
            self.redis = await get_redis()
            self.kafka = await get_kafka()
            self.user_manager = await get_user_manager()
            try:
                self.billing_manager = await get_billing_manager()
            except Exception as e:
                self.logger.warning(f"Billing manager not available: {str(e)}")
                self.billing_manager = None

            await self._setup_user_admin_tables()
            await self._load_user_reports()
            await self._load_suspended_users()

            self.logger.info("UserAdminManager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize UserAdminManager: {str(e)}")
            return False

    async def _setup_user_admin_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")

        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_audit_logs (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    admin_id VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    details JSONB NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    user_agent TEXT
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_reports (
                    id VARCHAR(255) PRIMARY KEY,
                    reporter_id VARCHAR(255) NOT NULL,
                    reported_user_id VARCHAR(255) NOT NULL,
                    reason VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    evidence JSONB NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(255)
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_suspensions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    reason TEXT NOT NULL,
                    suspended_by VARCHAR(255) NOT NULL,
                    suspended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT FALSE,
                    notes TEXT
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_warnings (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    warning_type VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    issued_by VARCHAR(255) NOT NULL,
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    severity VARCHAR(50) DEFAULT 'medium'
                )
            """)

            await session.execute("""
                CREATE TABLE IF NOT EXISTS ip_blacklist (
                    id SERIAL PRIMARY KEY,
                    ip_address INET NOT NULL,
                    reason TEXT NOT NULL,
                    blacklisted_by VARCHAR(255) NOT NULL,
                    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT FALSE
                )
            """)

            await session.commit()

    async def _load_user_reports(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT id, reporter_id, reported_user_id, reason, description, evidence,
                           status, created_at, resolved_at, resolved_by
                    FROM user_reports
                    WHERE status IN ('pending', 'investigating')
                    ORDER BY created_at DESC
                """)

                rows = result.fetchall()
                for row in rows:
                    report = UserReport(
                        id=row[0],
                        reporter_id=row[1],
                        reported_user_id=row[2],
                        reason=row[3],
                        description=row[4],
                        evidence=row[5] or [],
                        status=row[6],
                        created_at=row[7],
                        resolved_at=row[8],
                        resolved_by=row[9]
                    )
                    self.user_reports[report.id] = report

        except Exception as e:
            self.logger.error(f"Failed to load user reports: {str(e)}")

    async def _load_suspended_users(self):
        if not self.database:
            return

        try:
            async with self.database.get_session() as session:
                result = await session.execute("""
                    SELECT user_id, reason, suspended_by, suspended_at, expires_at, is_permanent, notes
                    FROM user_suspensions
                    WHERE expires_at > %s OR is_permanent = TRUE
                """, (datetime.utcnow(),))

                rows = result.fetchall()
                for row in rows:
                    self.suspended_users[row[0]] = {
                        "reason": row[1],
                        "suspended_by": row[2],
                        "suspended_at": row[3],
                        "expires_at": row[4],
                        "is_permanent": row[5],
                        "notes": row[6]
                    }

        except Exception as e:
            self.logger.error(f"Failed to load suspended users: {str(e)}")

    async def get_users(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get all users with pagination and all their data"""
        try:
            if not self.database:
                return {"users": [], "total": 0, "page": page, "limit": limit}
            
            # Try using Supabase client first (bypasses RLS with service role key)
            try:
                supabase_client = self.database.get_supabase_client()
                if supabase_client:
                    # Use Supabase client which automatically bypasses RLS with service role key
                    response = supabase_client.table('users').select('*', count='exact').order('created_at', desc=True).range((page - 1) * limit, page * limit - 1).execute()
                    
                    total = response.count if hasattr(response, 'count') else len(response.data)
                    users_data = response.data if response.data else []
                    
                    # Format users with all their data
                    users_list = []
                    for user_data in users_data:
                        user_dict = {
                            "id": str(user_data.get("id", "")),
                            "user_id": str(user_data.get("id", "")),
                            "email": user_data.get("email", ""),
                            "username": user_data.get("username") or "",
                            "full_name": user_data.get("full_name") or "",
                            "hashed_password": user_data.get("hashed_password") or "",
                            "is_active": user_data.get("is_active", False),
                            "is_verified": user_data.get("is_verified", False),
                            "tier": user_data.get("tier", "free"),
                            "status": "active" if user_data.get("is_active", False) else "inactive",
                            "created_at": user_data.get("created_at"),
                            "last_login": user_data.get("last_login"),
                            "website_url": user_data.get("website_url") or "",
                            "onboarding_completed": user_data.get("onboarding_completed", False),
                            "onboarding_completed_at": user_data.get("onboarding_completed_at"),
                            "onboarding_data": user_data.get("onboarding_data") or {},
                            "preferences": user_data.get("preferences") or {}
                        }
                        
                        # Extract onboarding data fields
                        onboarding_data = user_dict.get("onboarding_data", {})
                        if isinstance(onboarding_data, dict):
                            profile_data = onboarding_data.get("profile", {})
                            if profile_data:
                                user_dict.update({
                                    "role": profile_data.get("role"),
                                    "industry": profile_data.get("industry"),
                                    "goals": profile_data.get("goals", []),
                                    "otherGoal": profile_data.get("otherGoal"),
                                    "business_name": profile_data.get("business_name") or profile_data.get("businessName"),
                                    "business_website": profile_data.get("business_website") or profile_data.get("businessWebsite"),
                                    "business_size": profile_data.get("business_size") or profile_data.get("businessSize"),
                                    "business_stage": profile_data.get("business_stage") or profile_data.get("businessStage"),
                                    "purpose": profile_data.get("purpose"),
                                    "phone": profile_data.get("phone"),
                                    "address": profile_data.get("address"),
                                    "city": profile_data.get("city"),
                                    "country": profile_data.get("country"),
                                })
                        
                        users_list.append(user_dict)
                    
                    return {
                        "users": users_list,
                        "total": total,
                        "page": page,
                        "limit": limit,
                        "total_pages": (total + limit - 1) // limit if limit > 0 else 1
                    }
            except Exception as supabase_error:
                self.logger.warning(f"Supabase client query failed, falling back to SQLAlchemy: {supabase_error}")
            
            # Fallback to SQLAlchemy with RLS bypass
            async with self.database.get_session(bypass_rls=True) as session:
                from sqlalchemy import select, func
                from backend.core.database.models import User
                
                # Get total count
                count_result = await session.execute(select(func.count(User.id)))
                total = count_result.scalar() or 0
                
                # Get paginated users
                offset = (page - 1) * limit
                result = await session.execute(
                    select(User)
                    .order_by(User.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                users = result.scalars().all()
                
                # Format users with all their data
                users_list = []
                for user in users:
                    user_dict = {
                        "id": str(user.id),
                        "user_id": str(user.id),
                        "email": user.email,
                        "username": user.username or "",
                        "full_name": user.full_name or "",
                        "hashed_password": user.hashed_password or "",
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "tier": user.tier.value if user.tier else "free",
                        "status": "active" if user.is_active else "inactive",
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "last_login": user.last_login.isoformat() if user.last_login else None,
                        "website_url": getattr(user, 'website_url', None) or "",
                        "onboarding_completed": getattr(user, 'onboarding_completed', False),
                        "onboarding_completed_at": getattr(user, 'onboarding_completed_at', None).isoformat() if getattr(user, 'onboarding_completed_at', None) else None,
                        "onboarding_data": getattr(user, 'onboarding_data', None) or {},
                        "preferences": getattr(user, 'preferences', None) or {}
                    }
                    
                    # Extract onboarding data fields
                    onboarding_data = user_dict.get("onboarding_data", {})
                    if isinstance(onboarding_data, dict):
                        profile_data = onboarding_data.get("profile", {})
                        if profile_data:
                            user_dict.update({
                                "role": profile_data.get("role"),
                                "industry": profile_data.get("industry"),
                                "goals": profile_data.get("goals", []),
                                "otherGoal": profile_data.get("otherGoal"),
                                "business_name": profile_data.get("business_name") or profile_data.get("businessName"),
                                "business_website": profile_data.get("business_website") or profile_data.get("businessWebsite"),
                                "business_size": profile_data.get("business_size") or profile_data.get("businessSize"),
                                "business_stage": profile_data.get("business_stage") or profile_data.get("businessStage"),
                                "purpose": profile_data.get("purpose"),
                                "phone": profile_data.get("phone"),
                                "address": profile_data.get("address"),
                                "city": profile_data.get("city"),
                                "country": profile_data.get("country"),
                            })
                    
                    users_list.append(user_dict)
                
                return {
                    "users": users_list,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if limit > 0 else 1
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get users: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"users": [], "total": 0, "page": page, "limit": limit}

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get specific user with all details"""
        try:
            if not self.database:
                return {}

            # Use bypass_rls=True for admin operations to access all user data
            async with self.database.get_session(bypass_rls=True) as session:
                from sqlalchemy import select
                from backend.core.database.models import User
                
                result = await session.execute(
                    select(User).where(User.id == int(user_id))
                )
                user = result.scalar_one_or_none()
                
            if not user:
                return {}

                # Get user profile if available
                profile = None
                if self.user_manager:
                    try:
                        profile = await self.user_manager.get_user_profile(str(user.id))
                    except:
                        pass
            
            # Get subscription details
            subscription = None
            if self.billing_manager:
                try:
                    subscription = await self.billing_manager.get_user_subscription(str(user.id))
                except:
                    pass

            # Get user activities
            activities = []
            if self.user_manager:
                try:
                    activities = await self.user_manager.get_user_activities(str(user.id), limit=50)
                except:
                    pass
            
            # Get user errors
            errors = []
            if self.user_manager:
                try:
                    errors = await self.user_manager.get_user_errors(str(user.id), limit=20)
                except:
                    pass

            # Check suspension status
            suspension_info = self.suspended_users.get(str(user.id), {})

            # Build user details
            user_details = {
                "id": str(user.id),
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username or "",
                "full_name": user.full_name or "",
                "hashed_password": user.hashed_password or "",
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "tier": user.tier.value if user.tier else "free",
                "status": "active" if user.is_active else "inactive",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "website_url": getattr(user, 'website_url', None) or "",
                "onboarding_completed": getattr(user, 'onboarding_completed', False),
                "onboarding_completed_at": getattr(user, 'onboarding_completed_at', None).isoformat() if getattr(user, 'onboarding_completed_at', None) else None,
                "onboarding_data": getattr(user, 'onboarding_data', None) or {},
                "preferences": getattr(user, 'preferences', None) or {},
                "profile": profile.to_dict() if profile else {},
                "subscription": subscription.to_dict() if subscription else {},
                "activities": [activity.to_dict() if hasattr(activity, 'to_dict') else str(activity) for activity in activities],
                "errors": [error.to_dict() if hasattr(error, 'to_dict') else str(error) for error in errors],
                "suspension_info": suspension_info,
                "is_suspended": str(user.id) in self.suspended_users
            }
                
            # Extract onboarding data fields for easy access
            onboarding_data = user_details.get("onboarding_data", {})
            if isinstance(onboarding_data, dict):
                profile_data = onboarding_data.get("profile", {})
                if profile_data:
                    user_details.update({
                        "role": profile_data.get("role"),
                        "industry": profile_data.get("industry"),
                        "goals": profile_data.get("goals", []),
                        "otherGoal": profile_data.get("otherGoal"),
                        "business_name": profile_data.get("business_name") or profile_data.get("businessName"),
                        "business_website": profile_data.get("business_website") or profile_data.get("businessWebsite"),
                        "business_size": profile_data.get("business_size") or profile_data.get("businessSize"),
                        "business_stage": profile_data.get("business_stage") or profile_data.get("businessStage"),
                        "purpose": profile_data.get("purpose"),
                        "phone": profile_data.get("phone"),
                        "address": profile_data.get("address"),
                        "city": profile_data.get("city"),
                        "country": profile_data.get("country"),
                    })
                
            return user_details

        except Exception as e:
            self.logger.error(f"Failed to get user {user_id}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}

    async def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Alias for get_user for backward compatibility"""
        return await self.get_user(user_id)

    async def search_users(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            if not self.user_manager:
                return []

            users = await self.user_manager.search_users(query, filters)
            user_list = []

            for user in users:
                user_info = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "status": user.status.value,
                    "tier": user.tier.value if user.tier else "free",
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "is_suspended": user.id in self.suspended_users
                }
                user_list.append(user_info)

            return user_list

        except Exception as e:
            self.logger.error(f"Failed to search users: {str(e)}")
            return []

    async def suspend_user(self, user_id: str, reason: str, admin_id: str, 
                          duration_days: int = None, is_permanent: bool = False) -> bool:
        try:
            if not self.user_manager:
                return False

            user = await self.user_manager.get_user_by_id(user_id)
            if not user:
                return False

            # Calculate expiration date
            expires_at = None
            if not is_permanent and duration_days:
                expires_at = datetime.utcnow() + timedelta(days=duration_days)

            # Update user status
            await self.user_manager.update_user_status(user_id, "suspended")

            # Broadcast user suspension via WebSocket
            try:
                from backend.core.realtime.websocket_router import broadcast_notification
                await broadcast_notification(int(user_id), {
                    "id": f"suspension_{user_id}",
                    "type": "security_alert",
                    "title": "Account Suspended",
                    "message": f"Your account has been suspended. Reason: {reason}",
                    "metadata": {
                        "reason": reason,
                        "suspended_by": admin_id,
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "is_permanent": is_permanent
                    }
                })
            except Exception as e:
                self.logger.warning(f"Failed to broadcast user suspension: {e}")

            # Record suspension
            if not self.database:
                self.suspended_users[user_id] = {
                    "reason": reason,
                    "suspended_by": admin_id,
                    "suspended_at": datetime.utcnow(),
                    "expires_at": expires_at,
                    "is_permanent": is_permanent,
                    "notes": ""
                }
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO user_suspensions (user_id, reason, suspended_by, expires_at, is_permanent)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, reason, admin_id, expires_at, is_permanent))
                await session.commit()

            self.suspended_users[user_id] = {
                "reason": reason,
                "suspended_by": admin_id,
                "suspended_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_permanent": is_permanent,
                "notes": ""
            }

            # Log admin action
            await self._log_admin_action(user_id, admin_id, UserAction.SUSPEND, {
                "reason": reason,
                "duration_days": duration_days,
                "is_permanent": is_permanent
            })

            self.logger.info(f"User {user_id} suspended by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to suspend user: {str(e)}")
            return False

    async def activate_user(self, user_id: str, admin_id: str) -> bool:
        try:
            if not self.user_manager:
                return False

            user = await self.user_manager.get_user_by_id(user_id)
            if not user:
                return False

            # Update user status
            await self.user_manager.update_user_status(user_id, "active")

            # Broadcast user activation via WebSocket
            try:
                from backend.core.realtime.websocket_router import broadcast_notification
                await broadcast_notification(int(user_id), {
                    "id": f"activation_{user_id}",
                    "type": "system_update",
                    "title": "Account Activated",
                    "message": "Your account has been activated and is now active.",
                    "metadata": {
                        "activated_by": admin_id
                    }
                })
            except Exception as e:
                self.logger.warning(f"Failed to broadcast user activation: {e}")

            # Remove suspension record
            if not self.database:
                if user_id in self.suspended_users:
                    del self.suspended_users[user_id]
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE user_suspensions
                    SET expires_at = %s
                    WHERE user_id = %s
                """, (datetime.utcnow(), user_id))
                await session.commit()

            if user_id in self.suspended_users:
                del self.suspended_users[user_id]

            # Log admin action
            await self._log_admin_action(user_id, admin_id, UserAction.ACTIVATE, {
                "reason": "User reactivated by admin"
            })

            self.logger.info(f"User {user_id} activated by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to activate user: {str(e)}")
            return False

    async def modify_user_tier(self, user_id: str, new_tier: str, admin_id: str, 
                              reason: str = "") -> bool:
        try:
            if not self.user_manager or not self.billing_manager:
                return False

            user = await self.user_manager.get_user_by_id(user_id)
            if not user:
                return False

            # Update user tier
            await self.user_manager.update_user_tier(user_id, new_tier)

            # Log admin action
            await self._log_admin_action(user_id, admin_id, UserAction.MODIFY_TIER, {
                "old_tier": user.tier.value if user.tier else "free",
                "new_tier": new_tier,
                "reason": reason
            })

            self.logger.info(f"User {user_id} tier modified from {user.tier.value if user.tier else 'free'} to {new_tier} by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to modify user tier: {str(e)}")
            return False

    async def reset_user_password(self, user_id: str, admin_id: str) -> bool:
        try:
            if not self.user_manager:
                return False

            user = await self.user_manager.get_user_by_id(user_id)
            if not user:
                return False

            # Generate new password
            new_password = self._generate_secure_password()
            
            # Update user password
            await self.user_manager.change_user_password(user_id, new_password)

            # Log admin action
            await self._log_admin_action(user_id, admin_id, UserAction.RESET_PASSWORD, {
                "password_reset": True
            })

            self.logger.info(f"Password reset for user {user_id} by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset user password: {str(e)}")
            return False

    def _generate_secure_password(self) -> str:
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        return password

    async def block_ip_address(self, ip_address: str, reason: str, admin_id: str,
                              duration_days: int = None, is_permanent: bool = False) -> bool:
        try:
            expires_at = None
            if not is_permanent and duration_days:
                expires_at = datetime.utcnow() + timedelta(days=duration_days)

            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO ip_blacklist (ip_address, reason, blacklisted_by, expires_at, is_permanent)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (ip_address) DO UPDATE SET
                        reason = EXCLUDED.reason,
                        blacklisted_by = EXCLUDED.blacklisted_by,
                        expires_at = EXCLUDED.expires_at,
                        is_permanent = EXCLUDED.is_permanent
                """, (ip_address, reason, admin_id, expires_at, is_permanent))
                await session.commit()

            self.logger.info(f"IP address {ip_address} blocked by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to block IP address: {str(e)}")
            return False

    async def unblock_ip_address(self, ip_address: str, admin_id: str) -> bool:
        try:
            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE ip_blacklist
                    SET expires_at = %s
                    WHERE ip_address = %s
                """, (datetime.utcnow(), ip_address))
                await session.commit()

            self.logger.info(f"IP address {ip_address} unblocked by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unblock IP address: {str(e)}")
            return False

    async def create_user_report(self, reporter_id: str, reported_user_id: str, 
                                reason: str, description: str, evidence: List[str] = None) -> str:
        try:
            report_id = str(uuid.uuid4())
            
            report = UserReport(
                id=report_id,
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                reason=reason,
                description=description,
                evidence=evidence or [],
                status="pending",
                created_at=datetime.utcnow()
            )

            if not self.database:
                self.user_reports[report_id] = report
                return report_id

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO user_reports (id, reporter_id, reported_user_id, reason, description, evidence)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (report_id, reporter_id, reported_user_id, reason, description, json.dumps(evidence or [])))
                await session.commit()

            self.user_reports[report_id] = report
            self.logger.info(f"User report created: {report_id}")
            return report_id

        except Exception as e:
            self.logger.error(f"Failed to create user report: {str(e)}")
            raise

    async def get_user_reports(self, status: str = None, reported_user_id: str = None) -> List[Dict[str, Any]]:
        try:
            reports = list(self.user_reports.values())
            
            if status:
                reports = [r for r in reports if r.status == status]
                
            if reported_user_id:
                reports = [r for r in reports if r.reported_user_id == reported_user_id]

            return [report.__dict__ for report in reports]

        except Exception as e:
            self.logger.error(f"Failed to get user reports: {str(e)}")
            return []

    async def resolve_user_report(self, report_id: str, admin_id: str, resolution: str) -> bool:
        try:
            if report_id not in self.user_reports:
                return False

            report = self.user_reports[report_id]
            report.status = "resolved"
            report.resolved_at = datetime.utcnow()
            report.resolved_by = admin_id

            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE user_reports
                    SET status = %s, resolved_at = %s, resolved_by = %s
                    WHERE id = %s
                """, ("resolved", datetime.utcnow(), admin_id, report_id))
                await session.commit()

            self.logger.info(f"User report {report_id} resolved by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve user report: {str(e)}")
            return False

    async def issue_user_warning(self, user_id: str, warning_type: str, message: str,
                                admin_id: str, severity: str = "medium") -> bool:
        try:
            if not self.database:
                return True

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO user_warnings (user_id, warning_type, message, issued_by, severity)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, warning_type, message, admin_id, severity))
                await session.commit()

            self.logger.info(f"Warning issued to user {user_id} by admin {admin_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to issue user warning: {str(e)}")
            return False

    async def _log_admin_action(self, user_id: str, admin_id: str, action: UserAction, details: Dict[str, Any]):
        try:
            audit_log = UserAuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                admin_id=admin_id,
                action=action,
                details=details,
                timestamp=datetime.utcnow()
            )

            self.user_audit_logs[audit_log.id] = audit_log

            if not self.database:
                return

            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO user_audit_logs (id, user_id, admin_id, action, details)
                    VALUES (%s, %s, %s, %s, %s)
                """, (audit_log.id, user_id, admin_id, action.value, json.dumps(details)))
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to log admin action: {str(e)}")

    async def get_admin_actions(self, user_id: str = None, admin_id: str = None, 
                               hours: int = 24) -> List[Dict[str, Any]]:
        try:
            if not self.database:
                return []

            query = """
                SELECT id, user_id, admin_id, action, details, timestamp, ip_address, user_agent
                FROM user_audit_logs
                WHERE timestamp >= %s
            """
            params = [datetime.utcnow() - timedelta(hours=hours)]

            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)

            if admin_id:
                query += " AND admin_id = %s"
                params.append(admin_id)

            query += " ORDER BY timestamp DESC"

            async with self.database.get_session() as session:
                result = await session.execute(query, params)
                rows = result.fetchall()

                actions = []
                for row in rows:
                    actions.append({
                        "id": row[0],
                        "user_id": row[1],
                        "admin_id": row[2],
                        "action": row[3],
                        "details": row[4] if row[4] else {},
                        "timestamp": row[5].isoformat(),
                        "ip_address": row[6],
                        "user_agent": row[7]
                    })

                return actions

        except Exception as e:
            self.logger.error(f"Failed to get admin actions: {str(e)}")
            return []

    async def get_user_statistics(self, days: int = 30) -> Dict[str, Any]:
        try:
            if not self.database:
                return {}

            start_date = datetime.utcnow() - timedelta(days=days)

            async with self.database.get_session() as session:
                # Total users
                result = await session.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (start_date,))
                total_users = result.scalar()

                # New users today
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                result = await session.execute("SELECT COUNT(*) FROM users WHERE created_at >= %s", (today,))
                new_users_today = result.scalar()

                # Suspended users
                result = await session.execute("SELECT COUNT(*) FROM user_suspensions WHERE expires_at > %s OR is_permanent = TRUE", (datetime.utcnow(),))
                suspended_users = result.scalar()

                # Pending reports
                result = await session.execute("SELECT COUNT(*) FROM user_reports WHERE status = 'pending'")
                pending_reports = result.scalar()

                # Admin actions
                result = await session.execute("SELECT COUNT(*) FROM user_audit_logs WHERE timestamp >= %s", (start_date,))
                admin_actions = result.scalar()

                return {
                    "total_users": total_users,
                    "new_users_today": new_users_today,
                    "suspended_users": suspended_users,
                    "pending_reports": pending_reports,
                    "admin_actions": admin_actions,
                    "period_days": days
                }

        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {str(e)}")
            return {}

    async def close(self):
        self.logger.info("Closing UserAdminManager...")
        if self.database:
            await self.database.close()

# Global instances and initialization functions
_user_admin_manager: Optional[UserAdminManager] = None

async def init_user_admin_manager() -> UserAdminManager:
    global _user_admin_manager
    if not _user_admin_manager:
        _user_admin_manager = UserAdminManager()
        await _user_admin_manager.initialize()
    return _user_admin_manager

async def get_user_admin_manager() -> UserAdminManager:
    global _user_admin_manager
    if not _user_admin_manager:
        _user_admin_manager = await init_user_admin_manager()
    return _user_admin_manager
