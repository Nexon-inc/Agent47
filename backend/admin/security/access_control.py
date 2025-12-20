from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from core.database import get_database
from core.logs import get_logger
from core.config import get_settings
from core.cache import get_redis

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"

class ResourceType(Enum):
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"
    DATABASE = "database"
    FILE = "file"
    API = "api"

class AccessLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class AccessPolicy:
    id: str
    name: str
    description: str
    resource_type: ResourceType
    resource_id: str
    permissions: List[Permission]
    user_roles: List[str]
    conditions: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class UserRole:
    id: str
    name: str
    description: str
    permissions: List[Permission]
    access_level: AccessLevel
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AccessLog:
    id: str
    user_id: str
    resource_type: ResourceType
    resource_id: str
    action: str
    permission: Permission
    granted: bool
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

class AccessControl:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
        self.redis = get_redis()
        self._init_default_roles()
    
    def _init_default_roles(self):
        """Initialize default user roles"""
        default_roles = [
            UserRole(
                id="basic_user",
                name="Basic User",
                description="Basic user with limited access",
                permissions=[Permission.READ],
                access_level=AccessLevel.BASIC
            ),
            UserRole(
                id="standard_user",
                name="Standard User",
                description="Standard user with normal access",
                permissions=[Permission.READ, Permission.WRITE],
                access_level=AccessLevel.STANDARD
            ),
            UserRole(
                id="premium_user",
                name="Premium User",
                description="Premium user with enhanced access",
                permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
                access_level=AccessLevel.PREMIUM
            ),
            UserRole(
                id="admin",
                name="Administrator",
                description="System administrator",
                permissions=[Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN],
                access_level=AccessLevel.ADMIN
            ),
            UserRole(
                id="super_admin",
                name="Super Administrator",
                description="Super administrator with full access",
                permissions=[Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.EXECUTE],
                access_level=AccessLevel.SUPER_ADMIN
            )
        ]
        
        for role in default_roles:
            self.create_user_role(role)
    
    async def create_user_role(self, role: UserRole) -> UserRole:
        """Create a new user role"""
        try:
            role_dict = {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": [p.value for p in role.permissions],
                "access_level": role.access_level.value,
                "created_at": role.created_at
            }
            
            await self.db.execute(
                """
                INSERT INTO user_roles 
                (id, name, description, permissions, access_level, created_at)
                VALUES (:id, :name, :description, :permissions, :access_level, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                name = :name, description = :description, permissions = :permissions,
                access_level = :access_level
                """,
                role_dict
            )
            
            self.logger.info(f"Created user role: {role.name}")
            return role
            
        except Exception as e:
            self.logger.error(f"Failed to create user role: {e}")
            raise
    
    async def get_user_role(self, role_id: str) -> Optional[UserRole]:
        """Get user role by ID"""
        try:
            row = await self.db.fetch_one(
                "SELECT * FROM user_roles WHERE id = :role_id",
                {"role_id": role_id}
            )
            
            if row:
                return UserRole(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    permissions=[Permission(p) for p in row["permissions"]],
                    access_level=AccessLevel(row["access_level"]),
                    created_at=row["created_at"]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user role: {e}")
            return None
    
    async def get_all_roles(self) -> List[UserRole]:
        """Get all user roles"""
        try:
            rows = await self.db.fetch_all("SELECT * FROM user_roles ORDER BY access_level")
            
            roles = []
            for row in rows:
                role = UserRole(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    permissions=[Permission(p) for p in row["permissions"]],
                    access_level=AccessLevel(row["access_level"]),
                    created_at=row["created_at"]
                )
                roles.append(role)
            
            return roles
            
        except Exception as e:
            self.logger.error(f"Failed to get all roles: {e}")
            return []
    
    async def create_access_policy(self, policy: AccessPolicy) -> AccessPolicy:
        """Create a new access policy"""
        try:
            policy_dict = {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "resource_type": policy.resource_type.value,
                "resource_id": policy.resource_id,
                "permissions": [p.value for p in policy.permissions],
                "user_roles": policy.user_roles,
                "conditions": policy.conditions,
                "enabled": policy.enabled,
                "created_at": policy.created_at
            }
            
            await self.db.execute(
                """
                INSERT INTO access_policies 
                (id, name, description, resource_type, resource_id, permissions, user_roles, conditions, enabled, created_at)
                VALUES (:id, :name, :description, :resource_type, :resource_id, :permissions, :user_roles, :conditions, :enabled, :created_at)
                ON CONFLICT (id) DO UPDATE SET
                name = :name, description = :description, resource_type = :resource_type,
                resource_id = :resource_id, permissions = :permissions, user_roles = :user_roles,
                conditions = :conditions, enabled = :enabled
                """,
                policy_dict
            )
            
            self.logger.info(f"Created access policy: {policy.name}")
            return policy
            
        except Exception as e:
            self.logger.error(f"Failed to create access policy: {e}")
            raise
    
    async def check_permission(self, user_id: str, resource_type: ResourceType, 
                             resource_id: str, permission: Permission, 
                             context: Dict[str, Any] = None) -> bool:
        """Check if user has permission to access resource"""
        try:
            # Get user's role
            user_role = await self._get_user_role(user_id)
            if not user_role:
                return False
            
            # Check if user has the required permission in their role
            if permission not in user_role.permissions:
                await self._log_access(user_id, resource_type, resource_id, permission.value, False, context)
                return False
            
            # Get applicable access policies
            policies = await self._get_applicable_policies(resource_type, resource_id, user_role.id)
            
            for policy in policies:
                if not policy.enabled:
                    continue
                
                # Check if policy grants the required permission
                if permission in policy.permissions:
                    # Check policy conditions
                    if await self._check_policy_conditions(policy, context):
                        await self._log_access(user_id, resource_type, resource_id, permission.value, True, context)
                        return True
            
            await self._log_access(user_id, resource_type, resource_id, permission.value, False, context)
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return False
    
    async def _get_user_role(self, user_id: str) -> Optional[UserRole]:
        """Get user's role"""
        try:
            row = await self.db.fetch_one(
                """
                SELECT ur.* FROM user_roles ur
                JOIN users u ON u.role_id = ur.id
                WHERE u.id = :user_id
                """,
                {"user_id": user_id}
            )
            
            if row:
                return UserRole(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    permissions=[Permission(p) for p in row["permissions"]],
                    access_level=AccessLevel(row["access_level"]),
                    created_at=row["created_at"]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user role: {e}")
            return None
    
    async def _get_applicable_policies(self, resource_type: ResourceType, 
                                     resource_id: str, user_role_id: str) -> List[AccessPolicy]:
        """Get applicable access policies"""
        try:
            rows = await self.db.fetch_all(
                """
                SELECT * FROM access_policies 
                WHERE resource_type = :resource_type 
                AND (resource_id = :resource_id OR resource_id = '*')
                AND :user_role_id = ANY(user_roles)
                AND enabled = true
                """,
                {
                    "resource_type": resource_type.value,
                    "resource_id": resource_id,
                    "user_role_id": user_role_id
                }
            )
            
            policies = []
            for row in rows:
                policy = AccessPolicy(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    resource_type=ResourceType(row["resource_type"]),
                    resource_id=row["resource_id"],
                    permissions=[Permission(p) for p in row["permissions"]],
                    user_roles=row["user_roles"],
                    conditions=row["conditions"],
                    enabled=row["enabled"],
                    created_at=row["created_at"]
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            self.logger.error(f"Failed to get applicable policies: {e}")
            return []
    
    async def _check_policy_conditions(self, policy: AccessPolicy, context: Dict[str, Any]) -> bool:
        """Check if policy conditions are met"""
        try:
            if not context or not policy.conditions:
                return True
            
            conditions = policy.conditions
            
            # Check time-based conditions
            if "time_restrictions" in conditions:
                current_time = datetime.utcnow().time()
                restrictions = conditions["time_restrictions"]
                
                if "start_time" in restrictions and current_time < restrictions["start_time"]:
                    return False
                if "end_time" in restrictions and current_time > restrictions["end_time"]:
                    return False
            
            # Check IP-based conditions
            if "allowed_ips" in conditions and context.get("ip_address"):
                if context["ip_address"] not in conditions["allowed_ips"]:
                    return False
            
            # Check user-based conditions
            if "user_conditions" in conditions:
                user_conditions = conditions["user_conditions"]
                
                if "min_age_days" in user_conditions and context.get("user_created_at"):
                    user_age = (datetime.utcnow() - context["user_created_at"]).days
                    if user_age < user_conditions["min_age_days"]:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check policy conditions: {e}")
            return False
    
    async def _log_access(self, user_id: str, resource_type: ResourceType, 
                         resource_id: str, action: str, granted: bool, context: Dict[str, Any]):
        """Log access attempt"""
        try:
            access_log = AccessLog(
                id=f"log_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                permission=Permission(action),
                granted=granted,
                ip_address=context.get("ip_address", "unknown") if context else "unknown",
                user_agent=context.get("user_agent", "unknown") if context else "unknown"
            )
            
            await self.db.execute(
                """
                INSERT INTO access_logs 
                (id, user_id, resource_type, resource_id, action, permission, granted, ip_address, user_agent, timestamp)
                VALUES (:id, :user_id, :resource_type, :resource_id, :action, :permission, :granted, :ip_address, :user_agent, :timestamp)
                """,
                {
                    "id": access_log.id,
                    "user_id": access_log.user_id,
                    "resource_type": access_log.resource_type.value,
                    "resource_id": access_log.resource_id,
                    "action": access_log.action,
                    "permission": access_log.permission.value,
                    "granted": access_log.granted,
                    "ip_address": access_log.ip_address,
                    "user_agent": access_log.user_agent,
                    "timestamp": access_log.timestamp
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log access: {e}")
    
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign role to user"""
        try:
            await self.db.execute(
                "UPDATE users SET role_id = :role_id WHERE id = :user_id",
                {"role_id": role_id, "user_id": user_id}
            )
            
            # Clear user cache
            await self.redis.delete(f"user:{user_id}:role")
            
            self.logger.info(f"Assigned role {role_id} to user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to assign role to user: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a user"""
        try:
            user_role = await self._get_user_role(user_id)
            if user_role:
                return user_role.permissions
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {e}")
            return []
    
    async def get_access_logs(self, user_id: Optional[str] = None, 
                            resource_type: Optional[ResourceType] = None,
                            limit: int = 100) -> List[AccessLog]:
        """Get access logs with optional filtering"""
        try:
            query = "SELECT * FROM access_logs WHERE 1=1"
            params = {}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            if resource_type:
                query += " AND resource_type = :resource_type"
                params["resource_type"] = resource_type.value
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            rows = await self.db.fetch_all(query, params)
            
            logs = []
            for row in rows:
                log = AccessLog(
                    id=row["id"],
                    user_id=row["user_id"],
                    resource_type=ResourceType(row["resource_type"]),
                    resource_id=row["resource_id"],
                    action=row["action"],
                    permission=Permission(row["permission"]),
                    granted=row["granted"],
                    ip_address=row["ip_address"],
                    user_agent=row["user_agent"],
                    timestamp=row["timestamp"]
                )
                logs.append(log)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to get access logs: {e}")
            return []

# Singleton instance
_access_control = None

def get_access_control() -> AccessControl:
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control

def init_access_control():
    """Initialize access control system"""
    global _access_control
    _access_control = AccessControl()
    return _access_control
