import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_database, DatabaseManager
from core.cache import get_redis, RedisManager
from core.storage import get_chroma, ChromaDBManager
from core.event_bus import get_kafka, KafkaManager
from core.authentication import get_auth, AuthManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class AdminPermission(Enum):
    READ_ONLY = "read_only"
    BASIC_ADMIN = "basic_admin"
    SYSTEM_ADMIN = "system_admin"
    SUPER_ADMIN = "super_admin"

class AdminAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"

@dataclass
class AdminUser:
    user_id: str
    email: str
    permissions: List[AdminPermission]
    last_login: datetime
    is_active: bool
    session_token: str

class AdminCore(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.chroma: Optional[ChromaDBManager] = None
        self.kafka: Optional[KafkaManager] = None
        self.auth: Optional[AuthManager] = None
        self.settings = get_settings()
        
        self.active_sessions: Dict[str, AdminUser] = {}
        self.system_status = "initializing"
        self.last_health_check = datetime.utcnow()
        self.admin_metrics = {
            "total_actions": 0,
            "active_sessions": 0,
            "system_errors": 0,
            "performance_score": 100.0
        }
        
        self.logger = logger

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing AdminCore system...")
            
            self.database = get_database()
            self.redis = await get_redis()
            self.chroma = await get_chroma()
            self.kafka = await get_kafka()
            self.auth = await get_auth()
            
            await self._verify_connections()
            await self._setup_admin_tables()
            await self._initialize_default_admin()
            
            # Verify admin user was created
            await self._verify_admin_user_exists()
            
            self.system_status = "active"
            self.last_health_check = datetime.utcnow()
            
            self.logger.info("AdminCore system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AdminCore: {str(e)}")
            self.system_status = "error"
            return False

    async def _verify_connections(self):
        if self.database:
            db_healthy, db_exception = await self.database.health_check()
            if not db_healthy:
                raise Exception(f"Database connection failed: {db_exception}")
        if self.redis:
            if not await self.redis.health_check():
                raise Exception("Redis connection failed")
        if self.chroma:
            if not await self.chroma.health_check():
                raise Exception("Chroma connection failed")
        if self.kafka:
            if not await self.kafka.health_check():
                raise Exception("Kafka connection failed")

    async def _setup_admin_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            # Create admin_users table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    permissions JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    session_token VARCHAR(500)
                )
            """))
            
            # Create admin_actions table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id SERIAL PRIMARY KEY,
                    admin_user_id VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(100) NOT NULL,
                    resource_id VARCHAR(255),
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    user_agent TEXT
                )
            """))
            
            # Create admin_sessions table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id SERIAL PRIMARY KEY,
                    session_token VARCHAR(500) UNIQUE NOT NULL,
                    admin_user_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address INET,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """))
            
            await session.commit()

    async def _initialize_default_admin(self):
        """Initialize default super admin user"""
        if not self.database or not self.auth:
            self.logger.warning("Database or Auth manager not initialized, skipping admin user creation")
            return
        
        try:
            self.logger.info(f"Initializing default admin user: {self.settings.admin_default_email}")
            async with self.database.get_session() as session:
                from sqlalchemy import select
                from core.database.models import User
                
                # Check if user exists in users table
                result = await session.execute(
                    select(User).where(User.email == self.settings.admin_default_email)
                )
                user = result.scalar_one_or_none()
                self.logger.info(f"User lookup result: {'Found' if user else 'Not found'}")
                
                from core.database.models import UserTier
                
                # Create user in users table if doesn't exist
                if not user:
                    default_password = self.settings.admin_default_password or "G.z.t.i.p.0,1,0"
                    if len(default_password.encode("utf-8")) > 72:
                        self.logger.warning("Admin default password longer than 72 bytes; truncating to 72 bytes for bcrypt.")
                        # Truncate at 72 bytes to satisfy bcrypt limitation
                        default_password = default_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
                    hashed_password = self.auth.get_password_hash(default_password)
                    
                    # Check if username already exists, if so use a different one
                    username = "admin_super"
                    result = await session.execute(
                        select(User).where(User.username == username)
                    )
                    existing_username = result.scalar_one_or_none()
                    if existing_username:
                        username = f"admin_{self.settings.admin_default_email.split('@')[0]}"
                    
                    # Create user with PRO tier
                    new_user = User(
                        email=self.settings.admin_default_email,
                        username=username,
                        hashed_password=hashed_password,
                        full_name="Super Admin",
                        tier=UserTier.PRO,
                        is_active=True,
                        is_verified=True
                    )
                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    user_id = str(new_user.id)
                    self.logger.info(f"Created user in users table: {self.settings.admin_default_email} with username: {username} and PRO tier")
                else:
                    user_id = str(user.id)
                    # Always update password to ensure it matches the default
                    default_password = self.settings.admin_default_password or "G.z.t.i.p.0,1,0"
                    hashed_password = self.auth.get_password_hash(default_password)
                    
                    # Verify the password hash before updating
                    test_verify = self.auth.verify_password(default_password, hashed_password)
                    self.logger.info(f"Password hash test verification: {test_verify}")
                    
                    user.hashed_password = hashed_password
                    user.is_active = True
                    user.is_verified = True
                    if user.tier != UserTier.PRO:
                        user.tier = UserTier.PRO
                        self.logger.info(f"Updated admin user tier to PRO: {self.settings.admin_default_email}")
                    await session.commit()
                    self.logger.info(f"Updated password and status for user: {self.settings.admin_default_email} (user_id: {user_id})")
                
                # Check if admin user exists in admin_users table
                result = await session.execute(
                    text("SELECT COUNT(*) FROM admin_users WHERE email = :email"),
                    {"email": self.settings.admin_default_email}
                )
                count = result.scalar()
                
                if count == 0:
                    # Create super admin user in admin_users table
                    permissions_json = json.dumps([AdminPermission.SUPER_ADMIN.value])
                    await session.execute(
                        text("""
                            INSERT INTO admin_users (user_id, email, permissions, is_active)
                            VALUES (:user_id, :email, CAST(:permissions AS jsonb), :is_active)
                        """),
                        {
                            "user_id": user_id,
                            "email": self.settings.admin_default_email,
                            "permissions": permissions_json,
                            "is_active": True
                        }
                    )
                    await session.commit()
                    self.logger.info(f"Super admin user created in admin_users: {self.settings.admin_default_email}")
                else:
                    # Ensure existing admin has SUPER_ADMIN permission and correct user_id
                    result = await session.execute(
                        text("SELECT user_id, permissions FROM admin_users WHERE email = :email"),
                        {"email": self.settings.admin_default_email}
                    )
                    row = result.fetchone()
                    if row:
                        existing_user_id = row[0]
                        existing_perms = row[1] if isinstance(row[1], list) else json.loads(row[1]) if isinstance(row[1], str) else []
                        
                        # Update user_id if it doesn't match
                        if existing_user_id != user_id:
                            await session.execute(
                                text("UPDATE admin_users SET user_id = :user_id WHERE email = :email"),
                                {"user_id": user_id, "email": self.settings.admin_default_email}
                            )
                            await session.commit()
                            self.logger.info(f"Updated admin user_id: {self.settings.admin_default_email}")
                        
                        # Update permissions if needed
                        if AdminPermission.SUPER_ADMIN.value not in existing_perms:
                            existing_perms.append(AdminPermission.SUPER_ADMIN.value)
                            await session.execute(
                                text("UPDATE admin_users SET permissions = CAST(:permissions AS jsonb) WHERE email = :email"),
                                {
                                    "permissions": json.dumps(existing_perms),
                                    "email": self.settings.admin_default_email
                                }
                            )
                            await session.commit()
                            self.logger.info(f"Updated admin user to SUPER_ADMIN: {self.settings.admin_default_email}")
        except Exception as e:
            self.logger.error(f"Failed to initialize default admin: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Try fallback direct creation
            try:
                await self._create_admin_user_directly()
            except Exception as fallback_error:
                self.logger.error(f"Fallback user creation also failed: {fallback_error}")
    
    async def _create_admin_user_directly(self):
        """Directly create admin user using raw SQL as fallback"""
        try:
            self.logger.info("Attempting direct admin user creation with raw SQL...")
            async with self.database.get_session() as session:
                default_password = self.settings.admin_default_password or "G.z.t.i.p.0,1,0"
                if len(default_password.encode("utf-8")) > 72:
                    self.logger.warning("Admin default password longer than 72 bytes; truncating to 72 bytes for bcrypt.")
                    default_password = default_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
                hashed_password = self.auth.get_password_hash(default_password)
                
                # Check if username exists, use alternative if needed
                username = "admin_super"
                result = await session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                )
                if result.fetchone():
                    username = f"admin_{self.settings.admin_default_email.split('@')[0]}"
                
                from core.database.models import UserTier
                
                # Ensure usertier enum has 'pro' value
                try:
                    await session.execute(text("""
                        DO $$ BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_enum 
                                WHERE enumlabel = 'pro' 
                                AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'usertier')
                            ) THEN
                                ALTER TYPE usertier ADD VALUE 'pro';
                            END IF;
                        END $$;
                    """))
                    await session.commit()
                except Exception as enum_error:
                    # Enum might already exist or type might not exist yet, continue anyway
                    self.logger.warning(f"Could not add 'pro' to usertier enum (may already exist): {enum_error}")
                
                # Create user using raw SQL with ON CONFLICT handling
                tier_value = UserTier.PRO.value  # Use enum value
                await session.execute(
                    text("""
                        INSERT INTO users (email, username, hashed_password, full_name, tier, is_active, is_verified, created_at)
                        VALUES (:email, :username, :hashed_password, :full_name, CAST(:tier AS usertier), :is_active, :is_verified, CURRENT_TIMESTAMP)
                        ON CONFLICT (email) DO UPDATE SET
                            hashed_password = EXCLUDED.hashed_password,
                            tier = CAST(:tier AS usertier),
                            is_active = EXCLUDED.is_active,
                            is_verified = EXCLUDED.is_verified,
                            updated_at = CURRENT_TIMESTAMP
                    """),
                    {
                        "email": self.settings.admin_default_email,
                        "username": username,
                        "hashed_password": hashed_password,
                        "full_name": "Super Admin",
                        "tier": tier_value,
                        "is_active": True,
                        "is_verified": True
                    }
                )
                await session.commit()
                
                # Get the user_id
                result = await session.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": self.settings.admin_default_email}
                )
                user_row = result.fetchone()
                if user_row:
                    user_id = str(user_row[0])
                    
                    # Create admin_users entry
                    permissions_json = json.dumps([AdminPermission.SUPER_ADMIN.value])
                    await session.execute(
                        text("""
                            INSERT INTO admin_users (user_id, email, permissions, is_active)
                            VALUES (:user_id, :email, CAST(:permissions AS jsonb), :is_active)
                            ON CONFLICT (email) DO UPDATE SET
                                user_id = EXCLUDED.user_id,
                                permissions = EXCLUDED.permissions,
                                is_active = EXCLUDED.is_active
                        """),
                        {
                            "user_id": user_id,
                            "email": self.settings.admin_default_email,
                            "permissions": permissions_json,
                            "is_active": True
                        }
                    )
                    await session.commit()
                    self.logger.info(f"Successfully created admin user via direct SQL: {self.settings.admin_default_email}")
                else:
                    self.logger.error("Failed to retrieve user_id after creation")
        except Exception as e:
            self.logger.error(f"Direct user creation failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    async def _verify_admin_user_exists(self):
        """Verify admin user exists, create if missing"""
        try:
            async with self.database.get_session() as session:
                from sqlalchemy import select
                from core.database.models import User, UserTier
                
                result = await session.execute(
                    select(User).where(User.email == self.settings.admin_default_email)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    self.logger.warning(f"Admin user not found after initialization, attempting direct creation...")
                    await self._create_admin_user_directly()
                else:
                    if user.tier != UserTier.PRO:
                        user.tier = UserTier.PRO
                        await session.commit()
                        self.logger.info(f"Updated admin user tier to PRO during verification: {self.settings.admin_default_email}")
                    self.logger.info(f"Admin user verified: {self.settings.admin_default_email} (ID: {user.id})")
        except Exception as e:
            self.logger.error(f"Failed to verify admin user: {e}")

    async def authenticate_admin(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[AdminUser]:
        """Authenticate admin user and create session"""
        try:
            if not self.auth:
                self.logger.error("Auth manager not initialized")
                return None
            
            # Ensure auth is an AuthManager instance, not a string
            if isinstance(self.auth, str):
                self.logger.error(f"Auth manager is a string, not AuthManager instance: {self.auth}")
                return None
            
            # Authenticate user with main auth system
            user = await self.auth.authenticate_user(email, password)
            if not user:
                self.logger.warning(f"Authentication failed for email: {email}")
                return None
            
            # Check if user exists in admin_users table
            admin_user = await self._get_admin_user_by_email(email)
            if not admin_user:
                # If not in admin table, check if it's the default admin email
                if email == self.settings.admin_default_email:
                    # Create admin user on first login
                    # Ensure user.id is converted to string (it might be int)
                    user_id_str = str(user.id) if hasattr(user, 'id') and user.id is not None else None
                    if not user_id_str:
                        self.logger.error(f"Cannot create admin user: user.id is None for {email}")
                        return None
                    admin_user = await self._create_admin_user_from_email(email, user_id_str)
                    if not admin_user:
                        return None
                else:
                    self.logger.warning(f"User {email} is not an admin")
                    return None
            
            # Ensure admin user has PRO tier
            if self.database:
                try:
                    async with self.database.get_session() as session:
                        from core.database.models import User, UserTier
                        from sqlalchemy import select
                        result = await session.execute(select(User).where(User.email == email))
                        db_user = result.scalar_one_or_none()
                        if db_user and db_user.tier != UserTier.PRO:
                            db_user.tier = UserTier.PRO
                            await session.commit()
                            self.logger.info(f"Set PRO tier for admin user during authentication: {email}")
                except Exception as e:
                    self.logger.warning(f"Failed to update admin tier during auth: {e}")
            
            # Create session token with longer expiration for admin (24 hours)
            from datetime import timedelta
            session_token = self.auth.create_access_token(
                {"sub": str(user.id), "admin": True, "tier": "pro"},
                expires_delta=timedelta(hours=24)
            )
            admin_user.session_token = session_token
            
            # Create admin session
            await self._create_admin_session(admin_user, ip_address, user_agent)
            self.active_sessions[session_token] = admin_user
            
            # Update last login
            await self._update_last_login(admin_user.user_id)
            
            # Log admin action
            await self._log_admin_action(admin_user.user_id, "LOGIN", "auth", None, {
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            
            return admin_user
            
        except Exception as e:
            import traceback
            self.logger.error(f"Admin authentication failed: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _get_admin_user(self, user_id: str) -> Optional[AdminUser]:
        """Get admin user by user_id"""
        if not self.database:
            return None
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT user_id, email, permissions, last_login, is_active
                        FROM admin_users WHERE user_id = :user_id AND is_active = :is_active
                    """),
                    {"user_id": user_id, "is_active": True}
                )
                
                row = result.fetchone()
                if row:
                    perms = row[2] if isinstance(row[2], list) else json.loads(row[2]) if isinstance(row[2], str) else []
                    return AdminUser(
                        user_id=row[0],
                        email=row[1],
                        permissions=perms,
                        last_login=row[3] or datetime.utcnow(),
                        is_active=row[4],
                        session_token=""
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get admin user: {str(e)}")
            return None
    
    async def _get_admin_user_by_email(self, email: str) -> Optional[AdminUser]:
        """Get admin user by email"""
        if not self.database:
            return None
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT user_id, email, permissions, last_login, is_active
                        FROM admin_users WHERE email = :email AND is_active = :is_active
                    """),
                    {"email": email, "is_active": True}
                )
                
                row = result.fetchone()
                if row:
                    perms = row[2] if isinstance(row[2], list) else json.loads(row[2]) if isinstance(row[2], str) else []
                    return AdminUser(
                        user_id=row[0],
                        email=row[1],
                        permissions=perms,
                        last_login=row[3] or datetime.utcnow(),
                        is_active=row[4],
                        session_token=""
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get admin user by email: {str(e)}")
            return None
    
    async def _create_admin_user_from_email(self, email: str, user_id) -> Optional[AdminUser]:
        """Create admin user from email and user_id"""
        if not self.database:
            return None
        
        try:
            # Ensure user_id is a string
            user_id_str = str(user_id) if user_id is not None else None
            if not user_id_str:
                self.logger.error(f"Invalid user_id for email: {email}")
                return None
            
            async with self.database.get_session() as session:
                permissions_json = json.dumps([AdminPermission.SUPER_ADMIN.value])
                # Use CAST for proper JSONB conversion with asyncpg
                await session.execute(
                    text("""
                        INSERT INTO admin_users (user_id, email, permissions, is_active)
                        VALUES (:user_id, :email, CAST(:permissions AS jsonb), :is_active)
                        ON CONFLICT (email) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            permissions = EXCLUDED.permissions,
                            is_active = EXCLUDED.is_active
                    """),
                    {
                        "user_id": user_id_str,
                        "email": email,
                        "permissions": permissions_json,
                        "is_active": True
                    }
                )
                await session.commit()
                
                return AdminUser(
                    user_id=user_id_str,
                    email=email,
                    permissions=[AdminPermission.SUPER_ADMIN.value],
                    last_login=datetime.utcnow(),
                    is_active=True,
                    session_token=""
                )
        except Exception as e:
            self.logger.error(f"Failed to create admin user: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    async def _update_last_login(self, user_id: str):
        """Update last login timestamp"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    text("UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update last login: {str(e)}")

    async def _create_admin_session(self, admin_user: AdminUser, ip_address: str = None, user_agent: str = None):
        """Create admin session record"""
        if not self.database:
            return
        
        expires_at = datetime.utcnow() + timedelta(hours=self.settings.admin_session_timeout_hours)
        
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO admin_sessions (session_token, admin_user_id, expires_at, ip_address, user_agent)
                        VALUES (:session_token, :admin_user_id, :expires_at, :ip_address, :user_agent)
                    """),
                    {
                        "session_token": admin_user.session_token,
                        "admin_user_id": admin_user.user_id,
                        "expires_at": expires_at,
                        "ip_address": ip_address,
                        "user_agent": user_agent
                    }
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to create admin session: {str(e)}")

    async def verify_admin_session(self, session_token: str) -> Optional[AdminUser]:
        """Verify admin session token"""
        # Check in-memory cache first
        if session_token in self.active_sessions:
            admin_user = self.active_sessions[session_token]
            if admin_user.is_active:
                return admin_user
        
        if not self.database:
            return None
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT s.admin_user_id, s.expires_at, u.email, u.permissions, u.is_active
                        FROM admin_sessions s
                        JOIN admin_users u ON s.admin_user_id = u.user_id
                        WHERE s.session_token = :session_token 
                        AND s.is_active = :is_active 
                        AND s.expires_at > :now
                    """),
                    {
                        "session_token": session_token,
                        "is_active": True,
                        "now": datetime.utcnow()
                    }
                )
                
                row = result.fetchone()
                if row:
                    perms = row[3] if isinstance(row[3], list) else json.loads(row[3]) if isinstance(row[3], str) else []
                    admin_user = AdminUser(
                        user_id=row[0],
                        email=row[2],
                        permissions=perms,
                        last_login=datetime.utcnow(),
                        is_active=row[4],
                        session_token=session_token
                    )
                    self.active_sessions[session_token] = admin_user
                    return admin_user
        except Exception as e:
            self.logger.error(f"Failed to verify admin session: {str(e)}")
        
        return None

    async def check_permission(self, admin_user: AdminUser, action: AdminAction, resource_type: str) -> bool:
        if AdminPermission.SUPER_ADMIN.value in admin_user.permissions:
            return True
        
        if action == AdminAction.READ:
            return True
        
        if AdminPermission.SYSTEM_ADMIN.value in admin_user.permissions:
            return action in [AdminAction.CREATE, AdminAction.READ, AdminAction.UPDATE]
        
        if AdminPermission.BASIC_ADMIN.value in admin_user.permissions:
            return action in [AdminAction.READ, AdminAction.UPDATE] and resource_type not in ["system", "security"]
        
        return False

    async def _log_admin_action(self, admin_user_id: str, action: str, resource_type: str, resource_id: str = None, details: Dict[str, Any] = None):
        """Log admin action for audit trail"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                details_json = json.dumps(details or {})
                await session.execute(
                    text("""
                        INSERT INTO admin_actions (admin_user_id, action, resource_type, resource_id, details)
                        VALUES (:admin_user_id, :action, :resource_type, :resource_id, CAST(:details AS jsonb))
                    """),
                    {
                        "admin_user_id": admin_user_id,
                        "action": action,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "details": details_json
                    }
                )
                await session.commit()
                
                self.admin_metrics["total_actions"] += 1
                
        except Exception as e:
            self.logger.error(f"Failed to log admin action: {str(e)}")

    async def get_system_health(self) -> Dict[str, Any]:
        health_status = {
            "status": self.system_status,
            "timestamp": datetime.utcnow().isoformat(),
            "last_health_check": self.last_health_check.isoformat(),
            "components": {}
        }
        
        all_healthy = True
        
        try:
            if self.database:
                db_healthy, db_exception = await self.database.health_check()
                health_status["components"]["database"] = {"status": "healthy" if db_healthy else "unhealthy"}
                if not db_healthy:
                    all_healthy = False
                    health_status["components"]["database"]["error"] = str(db_exception)

            if self.redis:
                redis_healthy = await self.redis.health_check()
                health_status["components"]["redis"] = {"status": "healthy" if redis_healthy else "unhealthy"}
                if not redis_healthy:
                    all_healthy = False
            
            if self.chroma:
                chroma_healthy = await self.chroma.health_check()
                health_status["components"]["chroma"] = {"status": "healthy" if chroma_healthy else "unhealthy"}
                if not chroma_healthy:
                    all_healthy = False
            
            if self.kafka:
                kafka_healthy = await self.kafka.health_check()
                health_status["components"]["kafka"] = {"status": "healthy" if kafka_healthy else "unhealthy"}
                if not kafka_healthy:
                    all_healthy = False
            
            health_status["overall_status"] = "healthy" if all_healthy else "degraded"
            
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
            self.logger.error(f"Health check failed: {str(e)}")
        
        return health_status

    async def get_admin_metrics(self) -> Dict[str, Any]:
        metrics = self.admin_metrics.copy()
        metrics.update({
            "active_sessions": len(self.active_sessions),
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": self.system_status
        })
        return metrics

    async def cleanup_expired_sessions(self):
        """Clean up expired admin sessions"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        UPDATE admin_sessions 
                        SET is_active = FALSE 
                        WHERE expires_at < :now AND is_active = TRUE
                        RETURNING session_token
                    """),
                    {"now": datetime.utcnow()}
                )
                
                expired_tokens = [row[0] for row in result.fetchall()]
                await session.commit()
                
                if expired_tokens:
                    self.logger.info(f"Cleaned up {len(expired_tokens)} expired admin sessions")
                    
                    # Remove from active sessions cache
                    for token in expired_tokens:
                        if token in self.active_sessions:
                            del self.active_sessions[token]
                        
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {str(e)}")

    # =============================================================================
    # ADMIN USER MANAGEMENT (Super Admin Only)
    # =============================================================================
    
    async def create_admin_user(self, email: str, user_id: str, permissions: List[AdminPermission], admin_creator_id: str) -> Optional[AdminUser]:
        """Create a new admin user (Super Admin only)"""
        if not self.database:
            return None
        
        try:
            async with self.database.get_session() as session:
                from core.database.models import User, UserTier
                from sqlalchemy import select
                
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                
                if user and user.tier != UserTier.PRO:
                    user.tier = UserTier.PRO
                    await session.commit()
                    self.logger.info(f"Updated user tier to PRO for admin email: {email}")
                
                # Check if user already exists
                result = await session.execute(
                    text("SELECT COUNT(*) FROM admin_users WHERE email = :email OR user_id = :user_id"),
                    {"email": email, "user_id": user_id}
                )
                if result.scalar() > 0:
                    self.logger.warning(f"Admin user already exists: {email}")
                    return None
                
                # Create admin user
                permissions_list = [p.value for p in permissions]
                permissions_json = json.dumps(permissions_list)
                await session.execute(
                    text("""
                        INSERT INTO admin_users (user_id, email, permissions, is_active)
                        VALUES (:user_id, :email, CAST(:permissions AS jsonb), :is_active)
                    """),
                    {
                        "user_id": user_id,
                        "email": email,
                        "permissions": permissions_json,
                        "is_active": True
                    }
                )
                await session.commit()
                
                # Log action
                await self._log_admin_action(admin_creator_id, "CREATE_ADMIN", "admin_users", user_id, {
                    "email": email,
                    "permissions": permissions_list
                })
                
                return AdminUser(
                    user_id=user_id,
                    email=email,
                    permissions=permissions_list,
                    last_login=None,
                    is_active=True,
                    session_token=""
                )
        except Exception as e:
            self.logger.error(f"Failed to create admin user: {str(e)}")
            return None
    
    async def update_admin_permissions(self, admin_user_id: str, permissions: List[AdminPermission], admin_updater_id: str) -> bool:
        """Update admin user permissions (Super Admin only)"""
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                permissions_list = [p.value for p in permissions]
                permissions_json = json.dumps(permissions_list)
                await session.execute(
                    text("UPDATE admin_users SET permissions = CAST(:permissions AS jsonb), updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id"),
                    {"permissions": permissions_json, "user_id": admin_user_id}
                )
                await session.commit()
                
                # Log action
                await self._log_admin_action(admin_updater_id, "UPDATE_ADMIN_PERMISSIONS", "admin_users", admin_user_id, {
                    "permissions": permissions_list
                })
                
                # Update in-memory cache if exists
                for token, user in self.active_sessions.items():
                    if user.user_id == admin_user_id:
                        user.permissions = permissions_list
                
                return True
        except Exception as e:
            self.logger.error(f"Failed to update admin permissions: {str(e)}")
            return False
    
    async def deactivate_admin_user(self, admin_user_id: str, admin_deactivator_id: str) -> bool:
        """Deactivate an admin user (Super Admin only)"""
        if not self.database:
            return False
        
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    text("UPDATE admin_users SET is_active = :is_active, updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id"),
                    {"is_active": False, "user_id": admin_user_id}
                )
                await session.commit()
                
                # Log action
                await self._log_admin_action(admin_deactivator_id, "DEACTIVATE_ADMIN", "admin_users", admin_user_id, {})
                
                # Remove from active sessions
                tokens_to_remove = [token for token, user in self.active_sessions.items() if user.user_id == admin_user_id]
                for token in tokens_to_remove:
                    del self.active_sessions[token]
                
                return True
        except Exception as e:
            self.logger.error(f"Failed to deactivate admin user: {str(e)}")
            return False
    
    async def list_all_admin_users(self) -> List[Dict[str, Any]]:
        """List all admin users"""
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT user_id, email, permissions, last_login, is_active, created_at
                        FROM admin_users
                        ORDER BY created_at DESC
                    """)
                )
                
                admins = []
                for row in result.fetchall():
                    perms = row[2] if isinstance(row[2], list) else json.loads(row[2]) if isinstance(row[2], str) else []
                    admins.append({
                        "user_id": row[0],
                        "email": row[1],
                        "permissions": perms,
                        "last_login": row[3].isoformat() if row[3] else None,
                        "is_active": row[4],
                        "created_at": row[5].isoformat() if row[5] else None
                    })
                
                return admins
        except Exception as e:
            self.logger.error(f"Failed to list admin users: {str(e)}")
            return []
    
    async def shutdown(self):
        self.logger.info("Shutting down AdminCore system...")
        self.system_status = "shutting_down"
        
        if self.database:
            await self.database.close()
        if self.redis:
            await self.redis.close()
        if self.chroma:
            await self.chroma.close()
        if self.kafka:
            await self.kafka.close()
        
        self.system_status = "shutdown"
        self.logger.info("AdminCore system shutdown complete")

# Global instances and initialization functions
_admin_core: Optional[AdminCore] = None

async def init_admin_core() -> AdminCore:
    global _admin_core
    if not _admin_core:
        _admin_core = AdminCore()
        await _admin_core.initialize()
    return _admin_core

async def get_admin_core() -> AdminCore:
    global _admin_core
    if not _admin_core:
        _admin_core = await init_admin_core()
    return _admin_core
