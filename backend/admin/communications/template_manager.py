import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text
import re

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class TemplateType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    GENERIC = "generic"

class TemplateStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class TemplateCategory(Enum):
    NOTIFICATION = "notification"
    ALERT = "alert"
    WELCOME = "welcome"
    REMINDER = "reminder"
    CONFIRMATION = "confirmation"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Template:
    template_id: str
    name: str
    description: str
    template_type: TemplateType
    category: TemplateCategory
    status: TemplateStatus
    subject_template: Optional[str]
    body_template: str
    variables: List[str]
    metadata: Dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str

@dataclass
class TemplateVersion:
    version_id: str
    template_id: str
    version_number: int
    subject_template: Optional[str]
    body_template: str
    variables: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: str
    change_notes: str

@dataclass
class TemplateUsage:
    usage_id: str
    template_id: str
    used_by: str
    used_at: datetime
    variables_used: Dict[str, Any]
    success: bool
    error_message: Optional[str]

class TemplateManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.templates: Dict[str, Template] = {}
        self.template_cache: Dict[str, Tuple[Template, datetime]] = {}
        self.cache_duration_minutes = 30
        self.variable_pattern = re.compile(r'\{([^}]+)\}')

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing TemplateManager...")
            self.database = get_database()
            await self._setup_template_tables()
            await self._load_templates()
            self.logger.info("TemplateManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TemplateManager: {str(e)}")
            return False

    async def _setup_template_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id SERIAL PRIMARY KEY,
                    template_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    template_type VARCHAR(50) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    subject_template TEXT,
                    body_template TEXT NOT NULL,
                    variables JSONB NOT NULL,
                    metadata JSONB,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS template_versions (
                    id SERIAL PRIMARY KEY,
                    version_id VARCHAR(255) UNIQUE NOT NULL,
                    template_id VARCHAR(255) NOT NULL,
                    version_number INTEGER NOT NULL,
                    subject_template TEXT,
                    body_template TEXT NOT NULL,
                    variables JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255) NOT NULL,
                    change_notes TEXT,
                    FOREIGN KEY (template_id) REFERENCES templates(template_id)
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS template_usage (
                    id SERIAL PRIMARY KEY,
                    usage_id VARCHAR(255) UNIQUE NOT NULL,
                    template_id VARCHAR(255) NOT NULL,
                    used_by VARCHAR(255) NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    variables_used JSONB,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (template_id) REFERENCES templates(template_id)
                )
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_type 
                ON templates(template_type);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_category 
                ON templates(category);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_templates_status 
                ON templates(status);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_template_versions_template_id 
                ON template_versions(template_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_template_usage_template_id 
                ON template_usage(template_id);
            """)
            
            await session.execute("""
                CREATE INDEX IF NOT EXISTS idx_template_usage_used_at 
                ON template_usage(used_at);
            """)
            
            await session.commit()

    async def _load_templates(self):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, description, template_type, category, status,
                       subject_template, body_template, variables, metadata, version,
                       created_at, updated_at, created_by
                FROM templates
                WHERE status = 'active'
            """)
            
            for row in result:
                template = Template(
                    template_id=row.template_id,
                    name=row.name,
                    description=row.description,
                    template_type=TemplateType(row.template_type),
                    category=TemplateCategory(row.category),
                    status=TemplateStatus(row.status),
                    subject_template=row.subject_template,
                    body_template=row.body_template,
                    variables=row.variables or [],
                    metadata=row.metadata or {},
                    version=row.version,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    created_by=row.created_by
                )
                self.templates[template.template_id] = template

    async def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        template_type: TemplateType,
        category: TemplateCategory,
        subject_template: Optional[str],
        body_template: str,
        variables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> bool:
        try:
            if not self.database:
                return False
            
            extracted_variables = self._extract_variables(subject_template, body_template)
            if variables:
                extracted_variables.extend(variables)
            variables = list(set(extracted_variables))
            
            template = Template(
                template_id=template_id,
                name=name,
                description=description,
                template_type=template_type,
                category=category,
                status=TemplateStatus.DRAFT,
                subject_template=subject_template,
                body_template=body_template,
                variables=variables,
                metadata=metadata or {},
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=created_by
            )
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO templates (
                        template_id, name, description, template_type, category, status,
                        subject_template, body_template, variables, metadata, version, created_by
                    ) VALUES (
                        :template_id, :name, :description, :template_type, :category, :status,
                        :subject_template, :body_template, :variables, :metadata, :version, :created_by
                    )
                """, {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "template_type": template.template_type.value,
                    "category": template.category.value,
                    "status": template.status.value,
                    "subject_template": template.subject_template,
                    "body_template": template.body_template,
                    "variables": template.variables,
                    "metadata": template.metadata,
                    "version": template.version,
                    "created_by": template.created_by
                })
                
                await self._save_template_version(template, "Initial version", created_by)
                await session.commit()
            
            self.templates[template_id] = template
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {str(e)}")
            return False

    def _extract_variables(self, subject_template: Optional[str], body_template: str) -> List[str]:
        variables = []
        
        if subject_template:
            variables.extend(self.variable_pattern.findall(subject_template))
        
        variables.extend(self.variable_pattern.findall(body_template))
        
        return list(set(variables))

    async def _save_template_version(
        self, 
        template: Template, 
        change_notes: str, 
        created_by: str
    ):
        if not self.database:
            return
        
        version_id = f"version_{template.template_id}_{template.version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        async with self.database.get_session() as session:
            await session.execute("""
                INSERT INTO template_versions (
                    version_id, template_id, version_number, subject_template,
                    body_template, variables, metadata, created_by, change_notes
                ) VALUES (
                    :version_id, :template_id, :version_number, :subject_template,
                    :body_template, :variables, :metadata, :created_by, :change_notes
                )
            """, {
                "version_id": version_id,
                "template_id": template.template_id,
                "version_number": template.version,
                "subject_template": template.subject_template,
                "body_template": template.body_template,
                "variables": template.variables,
                "metadata": template.metadata,
                "created_by": created_by,
                "change_notes": change_notes
            })

    async def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        subject_template: Optional[str] = None,
        body_template: Optional[str] = None,
        variables: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        change_notes: str = "Template updated",
        updated_by: str = "system"
    ) -> bool:
        try:
            if template_id not in self.templates:
                return False
            
            if not self.database:
                return False
            
            template = self.templates[template_id]
            
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if subject_template is not None:
                template.subject_template = subject_template
            if body_template is not None:
                template.body_template = body_template
            if variables is not None:
                template.variables = variables
            if metadata is not None:
                template.metadata = metadata
            
            template.version += 1
            template.updated_at = datetime.utcnow()
            
            extracted_variables = self._extract_variables(template.subject_template, template.body_template)
            template.variables = list(set(extracted_variables + template.variables))
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE templates 
                    SET name = :name, description = :description, subject_template = :subject_template,
                        body_template = :body_template, variables = :variables, metadata = :metadata,
                        version = :version, updated_at = :updated_at
                    WHERE template_id = :template_id
                """, {
                    "template_id": template_id,
                    "name": template.name,
                    "description": template.description,
                    "subject_template": template.subject_template,
                    "body_template": template.body_template,
                    "variables": template.variables,
                    "metadata": template.metadata,
                    "version": template.version,
                    "updated_at": template.updated_at
                })
                
                await self._save_template_version(template, change_notes, updated_by)
                await session.commit()
            
            self.templates[template_id] = template
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update template: {str(e)}")
            return False

    async def activate_template(self, template_id: str, activated_by: str = "system") -> bool:
        return await self._change_template_status(template_id, TemplateStatus.ACTIVE, activated_by)

    async def deactivate_template(self, template_id: str, deactivated_by: str = "system") -> bool:
        return await self._change_template_status(template_id, TemplateStatus.INACTIVE, deactivated_by)

    async def archive_template(self, template_id: str, archived_by: str = "system") -> bool:
        return await self._change_template_status(template_id, TemplateStatus.ARCHIVED, archived_by)

    async def _change_template_status(
        self, 
        template_id: str, 
        status: TemplateStatus, 
        changed_by: str
    ) -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    UPDATE templates 
                    SET status = :status, updated_at = :updated_at
                    WHERE template_id = :template_id
                """, {
                    "template_id": template_id,
                    "status": status.value,
                    "updated_at": datetime.utcnow()
                })
                await session.commit()
            
            if template_id in self.templates:
                self.templates[template_id].status = status
                self.templates[template_id].updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to change template status: {str(e)}")
            return False

    async def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        used_by: str = "system"
    ) -> Optional[Dict[str, str]]:
        try:
            template = await self._get_template(template_id)
            if not template:
                return None
            
            subject = template.subject_template
            body = template.body_template
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                if subject:
                    subject = subject.replace(placeholder, str(var_value))
                body = body.replace(placeholder, str(var_value))
            
            await self._log_template_usage(template_id, used_by, variables, True)
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            self.logger.error(f"Failed to render template: {str(e)}")
            await self._log_template_usage(template_id, used_by, variables, False, str(e))
            return None

    async def _get_template(self, template_id: str) -> Optional[Template]:
        if template_id in self.templates:
            return self.templates[template_id]
        
        cache_key = f"template_{template_id}"
        if cache_key in self.template_cache:
            template, cached_at = self.template_cache[cache_key]
            if datetime.utcnow() - cached_at < timedelta(minutes=self.cache_duration_minutes):
                return template
        
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT template_id, name, description, template_type, category, status,
                       subject_template, body_template, variables, metadata, version,
                       created_at, updated_at, created_by
                FROM templates
                WHERE template_id = :template_id AND status = 'active'
            """, {"template_id": template_id})
            
            row = result.fetchone()
            if not row:
                return None
            
            template = Template(
                template_id=row.template_id,
                name=row.name,
                description=row.description,
                template_type=TemplateType(row.template_type),
                category=TemplateCategory(row.category),
                status=TemplateStatus(row.status),
                subject_template=row.subject_template,
                body_template=row.body_template,
                variables=row.variables or [],
                metadata=row.metadata or {},
                version=row.version,
                created_at=row.created_at,
                updated_at=row.updated_at,
                created_by=row.created_by
            )
            
            self.template_cache[cache_key] = (template, datetime.utcnow())
            return template

    async def _log_template_usage(
        self,
        template_id: str,
        used_by: str,
        variables: Dict[str, Any],
        success: bool,
        error_message: Optional[str] = None
    ):
        if not self.database:
            return
        
        try:
            usage_id = f"usage_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(template_id) % 10000}"
            
            async with self.database.get_session() as session:
                await session.execute("""
                    INSERT INTO template_usage (
                        usage_id, template_id, used_by, variables_used, success, error_message
                    ) VALUES (
                        :usage_id, :template_id, :used_by, :variables_used, :success, :error_message
                    )
                """, {
                    "usage_id": usage_id,
                    "template_id": template_id,
                    "used_by": used_by,
                    "variables_used": variables,
                    "success": success,
                    "error_message": error_message
                })
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log template usage: {str(e)}")

    async def get_templates(
        self,
        template_type: Optional[TemplateType] = None,
        category: Optional[TemplateCategory] = None,
        status: Optional[TemplateStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Template]:
        if not self.database:
            return []
        
        conditions = []
        params = {"limit": limit, "offset": offset}
        
        if template_type:
            conditions.append("template_type = :template_type")
            params["template_type"] = template_type.value
        
        if category:
            conditions.append("category = :category")
            params["category"] = category.value
        
        if status:
            conditions.append("status = :status")
            params["status"] = status.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT template_id, name, description, template_type, category, status,
                       subject_template, body_template, variables, metadata, version,
                       created_at, updated_at, created_by
                FROM templates
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT :limit OFFSET :offset
            """, params)
            
            templates = []
            for row in result:
                template = Template(
                    template_id=row.template_id,
                    name=row.name,
                    description=row.description,
                    template_type=TemplateType(row.template_type),
                    category=TemplateCategory(row.category),
                    status=TemplateStatus(row.status),
                    subject_template=row.subject_template,
                    body_template=row.body_template,
                    variables=row.variables or [],
                    metadata=row.metadata or {},
                    version=row.version,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    created_by=row.created_by
                )
                templates.append(template)
            
            return templates

    async def get_template_versions(
        self,
        template_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[TemplateVersion]:
        if not self.database:
            return []
        
        async with self.database.get_session() as session:
            result = await session.execute("""
                SELECT version_id, template_id, version_number, subject_template,
                       body_template, variables, metadata, created_at, created_by, change_notes
                FROM template_versions
                WHERE template_id = :template_id
                ORDER BY version_number DESC
                LIMIT :limit OFFSET :offset
            """, {"template_id": template_id, "limit": limit, "offset": offset})
            
            versions = []
            for row in result:
                version = TemplateVersion(
                    version_id=row.version_id,
                    template_id=row.template_id,
                    version_number=row.version_number,
                    subject_template=row.subject_template,
                    body_template=row.body_template,
                    variables=row.variables or [],
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    created_by=row.created_by,
                    change_notes=row.change_notes
                )
                versions.append(version)
            
            return versions

    async def get_template_usage_stats(
        self,
        template_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        conditions = ["used_at BETWEEN :start_date AND :end_date"]
        params = {"start_date": start_date, "end_date": end_date}
        
        if template_id:
            conditions.append("template_id = :template_id")
            params["template_id"] = template_id
        
        where_clause = "WHERE " + " AND ".join(conditions)
        
        async with self.database.get_session() as session:
            result = await session.execute(f"""
                SELECT 
                    COUNT(*) as total_usage,
                    COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_usage,
                    COUNT(CASE WHEN success = FALSE THEN 1 END) as failed_usage,
                    COUNT(DISTINCT template_id) as unique_templates,
                    COUNT(DISTINCT used_by) as unique_users
                FROM template_usage
                {where_clause}
            """, params)
            
            row = result.fetchone()
            if not row:
                return {}
            
            return {
                "total_usage": row.total_usage,
                "successful_usage": row.successful_usage,
                "failed_usage": row.failed_usage,
                "unique_templates": row.unique_templates,
                "unique_users": row.unique_users,
                "success_rate": (row.successful_usage / row.total_usage * 100) if row.total_usage > 0 else 0
            }

    async def delete_template(self, template_id: str, deleted_by: str = "system") -> bool:
        try:
            if not self.database:
                return False
            
            async with self.database.get_session() as session:
                await session.execute("""
                    DELETE FROM templates WHERE template_id = :template_id
                """, {"template_id": template_id})
                await session.commit()
            
            if template_id in self.templates:
                del self.templates[template_id]
            
            cache_key = f"template_{template_id}"
            if cache_key in self.template_cache:
                del self.template_cache[cache_key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete template: {str(e)}")
            return False

    async def validate_template(self, template_id: str) -> Dict[str, Any]:
        template = await self._get_template(template_id)
        if not template:
            return {"valid": False, "errors": ["Template not found"]}
        
        errors = []
        warnings = []
        
        if not template.body_template.strip():
            errors.append("Body template is empty")
        
        if template.template_type in [TemplateType.EMAIL, TemplateType.SLACK, TemplateType.DISCORD, TemplateType.TEAMS]:
            if not template.subject_template or not template.subject_template.strip():
                warnings.append("Subject template is empty for communication template")
        
        if template.template_type == TemplateType.SMS:
            if len(template.body_template) > 160:
                warnings.append("SMS body template is longer than 160 characters")
        
        extracted_variables = self._extract_variables(template.subject_template, template.body_template)
        missing_variables = [var for var in extracted_variables if var not in template.variables]
        if missing_variables:
            warnings.append(f"Variables found in template but not declared: {missing_variables}")
        
        unused_variables = [var for var in template.variables if var not in extracted_variables]
        if unused_variables:
            warnings.append(f"Declared variables not used in template: {unused_variables}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "variables": template.variables,
            "extracted_variables": extracted_variables
        }

    async def clone_template(
        self,
        source_template_id: str,
        new_template_id: str,
        new_name: str,
        cloned_by: str = "system"
    ) -> bool:
        try:
            source_template = await self._get_template(source_template_id)
            if not source_template:
                return False
            
            return await self.create_template(
                template_id=new_template_id,
                name=new_name,
                description=f"Cloned from {source_template.name}",
                template_type=source_template.template_type,
                category=source_template.category,
                subject_template=source_template.subject_template,
                body_template=source_template.body_template,
                variables=source_template.variables,
                metadata=source_template.metadata,
                created_by=cloned_by
            )
            
        except Exception as e:
            self.logger.error(f"Failed to clone template: {str(e)}")
            return False

_template_manager: Optional[TemplateManager] = None

async def get_template_manager() -> TemplateManager:
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
        await _template_manager.initialize()
    return _template_manager

async def init_template_manager() -> TemplateManager:
    return await get_template_manager()
