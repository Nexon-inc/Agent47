import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass, field
import json

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationType(Enum):
    SCHEMA = "schema"
    DATA = "data"
    INDEX = "index"
    CONSTRAINT = "constraint"

@dataclass
class Migration:
    id: str
    version: str
    name: str
    description: str
    migration_type: MigrationType
    status: MigrationStatus
    sql_up: str
    sql_down: str
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    checksum: str = ""

class MigrationManager(LoggerMixin):
    def __init__(self):
        self.config = get_settings()
        self.logger = logger
        self.db = get_database()
        self.migrations_dir = self.config.get("migrations_directory", "./migrations")
        
        # Ensure migrations directory exists
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Initialize migrations table
        self._init_migrations_table()
    
    async def _init_migrations_table(self):
        """Initialize migrations tracking table"""
        try:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id VARCHAR(255) PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    migration_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    sql_up TEXT NOT NULL,
                    sql_down TEXT NOT NULL,
                    dependencies JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP NULL,
                    execution_time FLOAT NULL,
                    error_message TEXT NULL,
                    checksum VARCHAR(64) NOT NULL
                )
            """)
            
            # Create index for version tracking
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_migrations_version ON migrations(version)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_migrations_status ON migrations(status)
            """)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize migrations table: {e}")
    
    async def create_migration(self, name: str, description: str, 
                             migration_type: MigrationType = MigrationType.SCHEMA,
                             dependencies: List[str] = None) -> Migration:
        """Create a new migration file"""
        try:
            # Generate version and ID
            version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            migration_id = f"{version}_{name.lower().replace(' ', '_')}"
            
            # Create migration object
            migration = Migration(
                id=migration_id,
                version=version,
                name=name,
                description=description,
                migration_type=migration_type,
                status=MigrationStatus.PENDING,
                sql_up="-- Add your UP migration SQL here\n",
                sql_down="-- Add your DOWN migration SQL here\n",
                dependencies=dependencies or [],
                checksum=self._generate_checksum(f"{version}_{name}")
            )
            
            # Create migration file
            file_path = os.path.join(self.migrations_dir, f"{migration_id}.sql")
            self._write_migration_file(file_path, migration)
            
            # Store in database
            await self._store_migration(migration)
            
            self.logger.info(f"Created migration: {migration_id}")
            return migration
            
        except Exception as e:
            self.logger.error(f"Failed to create migration: {e}")
            raise
    
    def _write_migration_file(self, file_path: str, migration: Migration):
        """Write migration SQL to file"""
        try:
            with open(file_path, 'w') as f:
                f.write(f"-- Migration: {migration.name}\n")
                f.write(f"-- Version: {migration.version}\n")
                f.write(f"-- Description: {migration.description}\n")
                f.write(f"-- Type: {migration.migration_type.value}\n")
                f.write(f"-- Dependencies: {', '.join(migration.dependencies) if migration.dependencies else 'None'}\n")
                f.write(f"-- Created: {migration.created_at.isoformat()}\n\n")
                
                f.write("-- UP Migration\n")
                f.write("-- ===========\n")
                f.write(migration.sql_up)
                f.write("\n\n")
                
                f.write("-- DOWN Migration (Rollback)\n")
                f.write("-- =======================\n")
                f.write(migration.sql_down)
                
        except Exception as e:
            self.logger.error(f"Failed to write migration file: {e}")
            raise
    
    def _generate_checksum(self, content: str) -> str:
        """Generate checksum for migration content"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    async def run_migration(self, migration_id: str) -> bool:
        """Run a specific migration"""
        try:
            # Get migration
            migration = await self._get_migration(migration_id)
            if not migration:
                self.logger.error(f"Migration not found: {migration_id}")
                return False
            
            if migration.status == MigrationStatus.COMPLETED:
                self.logger.info(f"Migration already completed: {migration_id}")
                return True
            
            # Check dependencies
            if not await self._check_dependencies(migration):
                self.logger.error(f"Migration dependencies not met: {migration_id}")
                return False
            
            # Update status to running
            migration.status = MigrationStatus.RUNNING
            await self._update_migration_status(migration)
            
            # Execute migration
            start_time = datetime.utcnow()
            success = await self._execute_migration_sql(migration.sql_up)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            if success:
                migration.status = MigrationStatus.COMPLETED
                migration.executed_at = datetime.utcnow()
                migration.execution_time = execution_time
                self.logger.info(f"Migration completed successfully: {migration_id}")
            else:
                migration.status = MigrationStatus.FAILED
                migration.error_message = "SQL execution failed"
                self.logger.error(f"Migration failed: {migration_id}")
            
            await self._update_migration_status(migration)
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to run migration: {e}")
            return False
    
    async def _check_dependencies(self, migration: Migration) -> bool:
        """Check if migration dependencies are met"""
        try:
            if not migration.dependencies:
                return True
            
            for dep_id in migration.dependencies:
                dep_migration = await self._get_migration(dep_id)
                if not dep_migration or dep_migration.status != MigrationStatus.COMPLETED:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check dependencies: {e}")
            return False
    
    async def _execute_migration_sql(self, sql: str) -> bool:
        """Execute migration SQL"""
        try:
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    await self.db.execute(statement)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute migration SQL: {e}")
            return False
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration"""
        try:
            # Get migration
            migration = await self._get_migration(migration_id)
            if not migration:
                return False
            
            if migration.status != MigrationStatus.COMPLETED:
                self.logger.error(f"Cannot rollback migration with status: {migration.status}")
                return False
            
            # Execute rollback SQL
            success = await self._execute_migration_sql(migration.sql_down)
            
            if success:
                migration.status = MigrationStatus.ROLLED_BACK
                self.logger.info(f"Migration rolled back: {migration_id}")
            else:
                migration.error_message = "Rollback SQL execution failed"
                self.logger.error(f"Migration rollback failed: {migration_id}")
            
            await self._update_migration_status(migration)
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to rollback migration: {e}")
            return False
    
    async def run_all_pending_migrations(self) -> List[str]:
        """Run all pending migrations in dependency order"""
        try:
            # Get pending migrations
            pending_migrations = await self._get_pending_migrations()
            
            if not pending_migrations:
                self.logger.info("No pending migrations")
                return []
            
            # Sort by dependencies
            sorted_migrations = self._sort_by_dependencies(pending_migrations)
            
            completed_migrations = []
            for migration in sorted_migrations:
                if await self.run_migration(migration.id):
                    completed_migrations.append(migration.id)
                else:
                    self.logger.error(f"Migration failed, stopping: {migration.id}")
                    break
            
            return completed_migrations
            
        except Exception as e:
            self.logger.error(f"Failed to run pending migrations: {e}")
            return []
    
    def _sort_by_dependencies(self, migrations: List[Migration]) -> List[Migration]:
        """Sort migrations by dependency order"""
        try:
            # Create dependency graph
            graph = {}
            for migration in migrations:
                graph[migration.id] = set(migration.dependencies)
            
            # Topological sort
            sorted_migrations = []
            visited = set()
            temp_visited = set()
            
            def visit(migration_id):
                if migration_id in temp_visited:
                    raise ValueError("Circular dependency detected")
                if migration_id in visited:
                    return
                
                temp_visited.add(migration_id)
                
                for dep_id in graph.get(migration_id, set()):
                    visit(dep_id)
                
                temp_visited.remove(migration_id)
                visited.add(migration_id)
                
                # Find migration object
                migration = next((m for m in migrations if m.id == migration_id), None)
                if migration:
                    sorted_migrations.append(migration)
            
            for migration_id in graph:
                if migration_id not in visited:
                    visit(migration_id)
            
            return sorted_migrations
            
        except Exception as e:
            self.logger.error(f"Failed to sort migrations by dependencies: {e}")
            return migrations
    
    async def _get_pending_migrations(self) -> List[Migration]:
        """Get all pending migrations"""
        try:
            rows = await self.db.fetch_all(
                "SELECT * FROM migrations WHERE status = :status ORDER BY created_at",
                {"status": MigrationStatus.PENDING.value}
            )
            
            migrations = []
            for row in rows:
                migration = Migration(
                    id=row["id"],
                    version=row["version"],
                    name=row["name"],
                    description=row["description"],
                    migration_type=MigrationType(row["migration_type"]),
                    status=MigrationStatus(row["status"]),
                    sql_up=row["sql_up"],
                    sql_down=row["sql_down"],
                    dependencies=row.get("dependencies", []),
                    created_at=row["created_at"],
                    executed_at=row["executed_at"],
                    execution_time=row["execution_time"],
                    error_message=row["error_message"],
                    checksum=row["checksum"]
                )
                migrations.append(migration)
            
            return migrations
            
        except Exception as e:
            self.logger.error(f"Failed to get pending migrations: {e}")
            return []
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get overall migration status"""
        try:
            # Get migration counts by status
            status_counts = await self.db.fetch_all(
                """
                SELECT status, COUNT(*) as count 
                FROM migrations 
                GROUP BY status
                """
            )
            
            # Get latest migrations
            latest_migrations = await self.db.fetch_all(
                """
                SELECT * FROM migrations 
                ORDER BY created_at DESC 
                LIMIT 10
                """
            )
            
            status_summary = {}
            for row in status_counts:
                status_summary[row["status"]] = row["count"]
            
            return {
                "status_counts": status_summary,
                "latest_migrations": [
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "status": row["status"],
                        "created_at": row["created_at"].isoformat()
                    }
                    for row in latest_migrations
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get migration status: {e}")
            return {}
    
    async def _store_migration(self, migration: Migration):
        """Store migration in database"""
        try:
            await self.db.execute(
                """
                INSERT INTO migrations 
                (id, version, name, description, migration_type, status, sql_up, sql_down, 
                dependencies, created_at, checksum)
                VALUES (:id, :version, :name, :description, :migration_type, :status, :sql_up, :sql_down, 
                :dependencies, :created_at, :checksum)
                """,
                {
                    "id": migration.id,
                    "version": migration.version,
                    "name": migration.name,
                    "description": migration.description,
                    "migration_type": migration.migration_type.value,
                    "status": migration.status.value,
                    "sql_up": migration.sql_up,
                    "sql_down": migration.sql_down,
                    "dependencies": migration.dependencies,
                    "created_at": migration.created_at,
                    "checksum": migration.checksum
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store migration: {e}")
    
    async def _update_migration_status(self, migration: Migration):
        """Update migration status in database"""
        try:
            await self.db.execute(
                """
                UPDATE migrations 
                SET status = :status, executed_at = :executed_at, execution_time = :execution_time, 
                error_message = :error_message
                WHERE id = :id
                """,
                {
                    "status": migration.status.value,
                    "executed_at": migration.executed_at,
                    "execution_time": migration.execution_time,
                    "error_message": migration.error_message,
                    "id": migration.id
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to update migration status: {e}")
    
    async def _get_migration(self, migration_id: str) -> Optional[Migration]:
        """Get migration by ID"""
        try:
            row = await self.db.fetch_one(
                "SELECT * FROM migrations WHERE id = :migration_id",
                {"migration_id": migration_id}
            )
            
            if row:
                return Migration(
                    id=row["id"],
                    version=row["version"],
                    name=row["name"],
                    description=row["description"],
                    migration_type=MigrationType(row["migration_type"]),
                    status=MigrationStatus(row["status"]),
                    sql_up=row["sql_up"],
                    sql_down=row["sql_down"],
                    dependencies=row.get("dependencies", []),
                    created_at=row["created_at"],
                    executed_at=row["executed_at"],
                    execution_time=row["execution_time"],
                    error_message=row["error_message"],
                    checksum=row["checksum"]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get migration: {e}")
            return None

# Singleton instance
_migration_manager = None

def get_migration_manager() -> MigrationManager:
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager

def init_migration_manager():
    """Initialize migration management system"""
    global _migration_manager
    _migration_manager = MigrationManager()
    return _migration_manager
