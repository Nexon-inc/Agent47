import asyncio
import os
import subprocess
import gzip
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
from enum import Enum
from sqlalchemy import text
from dataclasses import dataclass

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORING = "restoring"

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

@dataclass
class BackupInfo:
    id: str
    status: BackupStatus
    file_path: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class BackupManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.settings = get_settings()
        self.logger = logger
        self.backup_dir = Path(self.settings.upload_dir) / "database_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_retention_days = 30
        self.max_backup_size_gb = 10
        self.backup_schedule = {
            "full": "0 2 * * 0",
            "incremental": "0 2 * * 1-6"
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing BackupManager...")
            self.database = get_database()
            await self._setup_backup_tables()
            await self._cleanup_old_backups()
            self.logger.info("BackupManager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize BackupManager: {str(e)}")
            return False

    async def _setup_backup_tables(self):
        if not self.database:
            raise RuntimeError("Database not initialized")
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS database_backups (
                    id SERIAL PRIMARY KEY,
                    backup_id VARCHAR(255) UNIQUE NOT NULL,
                    backup_type VARCHAR(20) NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    size_bytes BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending',
                    checksum VARCHAR(64),
                    compression_ratio FLOAT,
                    restore_tested BOOLEAN DEFAULT FALSE,
                    notes TEXT
                )
            """))
            
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS backup_schedules (
                    id SERIAL PRIMARY KEY,
                    backup_type VARCHAR(20) NOT NULL,
                    cron_expression VARCHAR(100) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backups_created_at 
                ON database_backups(created_at)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backups_status 
                ON database_backups(status)
            """))
            
            await session.commit()

    async def create_backup(self, backup_type: BackupType = BackupType.FULL, 
                           compression: bool = True, notes: str = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{backup_type.value}"
        filename = f"{backup_id}.sql"
        filepath = self.backup_dir / filename
        
        try:
            await self._log_backup_start(backup_id, backup_type, filename, notes)
            
            db_url = self.settings.database.database_url
            db_name = self.settings.database.postgres_db
            db_user = self.settings.database.postgres_user
            db_host = self.settings.database.postgres_host
            db_port = self.settings.database.postgres_port
            
            pg_dump_cmd = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--verbose",
                "--no-password"
            ]
            
            if backup_type == BackupType.INCREMENTAL:
                pg_dump_cmd.extend(["--data-only"])
            elif backup_type == BackupType.DIFFERENTIAL:
                last_backup = await self._get_last_backup()
                if last_backup:
                    pg_dump_cmd.extend(["--since", last_backup.created_at.isoformat()])
            
            with open(filepath, 'w') as f:
                process = subprocess.Popen(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env={"PGPASSWORD": self.settings.database.postgres_password}
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
            
            if compression:
                await self._compress_backup(filepath)
                filepath = filepath.with_suffix('.sql.gz')
                filename = filepath.name
            
            file_size = filepath.stat().st_size
            checksum = await self._calculate_checksum(filepath)
            compression_ratio = await self._calculate_compression_ratio(filepath)
            
            await self._log_backup_complete(backup_id, file_size, checksum, compression_ratio)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "filename": filename,
                "size_bytes": file_size,
                "checksum": checksum,
                "compression_ratio": compression_ratio,
                "filepath": str(filepath)
            }
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            await self._log_backup_failed(backup_id, str(e))
            return {"error": str(e)}

    async def _compress_backup(self, filepath: Path):
        compressed_path = filepath.with_suffix('.sql.gz')
        with open(filepath, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        filepath.unlink()

    async def _calculate_checksum(self, filepath: Path) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def _calculate_compression_ratio(self, filepath: Path) -> float:
        if filepath.suffix == '.gz':
            with gzip.open(filepath, 'rb') as f:
                compressed_size = len(f.read())
            original_size = filepath.stat().st_size
            return (1 - compressed_size / original_size) * 100
        return 0.0

    async def restore_backup(self, backup_id: str, target_database: str = None) -> Dict[str, Any]:
        if not self.database:
            return {"error": "Database not initialized"}
        
        try:
            backup_info = await self._get_backup_info(backup_id)
            if not backup_info:
                return {"error": "Backup not found"}
            
            filepath = self.backup_dir / backup_info.filename
            if not filepath.exists():
                return {"error": "Backup file not found"}
            
            await self._log_restore_start(backup_id)
            
            db_name = target_database or self.settings.database.postgres_db
            db_user = self.settings.database.postgres_user
            db_host = self.settings.database.postgres_host
            db_port = self.settings.database.postgres_port
            
            pg_restore_cmd = [
                "psql",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--verbose",
                "--no-password"
            ]
            
            if filepath.suffix == '.gz':
                with gzip.open(filepath, 'rt') as f:
                    process = subprocess.Popen(
                        pg_restore_cmd,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env={"PGPASSWORD": self.settings.database.postgres_password}
                    )
                    stdout, stderr = process.communicate(input=f.read().encode())
            else:
                with open(filepath, 'r') as f:
                    process = subprocess.Popen(
                        pg_restore_cmd,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env={"PGPASSWORD": self.settings.database.postgres_password}
                    )
                    stdout, stderr = process.communicate(input=f.read().encode())
            
            if process.returncode != 0:
                raise RuntimeError(f"Restore failed: {stderr.decode()}")
            
            await self._log_restore_complete(backup_id)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "target_database": db_name,
                "restored_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            await self._log_restore_failed(backup_id, str(e))
            return {"error": str(e)}

    async def list_backups(self, limit: int = 50, status: BackupStatus = None) -> List[Dict[str, Any]]:
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                query = """
                    SELECT backup_id, backup_type, filename, size_bytes, created_at, 
                           completed_at, status, checksum, compression_ratio, restore_tested, notes
                    FROM database_backups 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """
                params = [limit]
                
                if status:
                    query = query.replace("LIMIT %s", "WHERE status = %s LIMIT %s")
                    params = [status.value, limit]
                
                result = await session.execute(text(query), params)
                
                backups = []
                for row in result.fetchall():
                    backups.append({
                        "backup_id": row[0],
                        "backup_type": row[1],
                        "filename": row[2],
                        "size_bytes": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "completed_at": row[5].isoformat() if row[5] else None,
                        "status": row[6],
                        "checksum": row[7],
                        "compression_ratio": row[8],
                        "restore_tested": row[9],
                        "notes": row[10]
                    })
                
                return backups
        except Exception as e:
            self.logger.error(f"Failed to list backups: {str(e)}")
            return []

    async def delete_backup(self, backup_id: str) -> bool:
        if not self.database:
            return False
        
        try:
            backup_info = await self._get_backup_info(backup_id)
            if not backup_info:
                return False
            
            filepath = self.backup_dir / backup_info.filename
            if filepath.exists():
                filepath.unlink()
            
            async with self.database.get_session() as session:
                await session.execute(text("""
                    DELETE FROM database_backups WHERE backup_id = %s
                """), (backup_id,))
                await session.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete backup: {str(e)}")
            return False

    async def test_backup_restore(self, backup_id: str) -> Dict[str, Any]:
        test_db_name = f"test_restore_{backup_id}_{int(datetime.utcnow().timestamp())}"
        
        try:
            await self._create_test_database(test_db_name)
            result = await self.restore_backup(backup_id, test_db_name)
            
            if result.get("success"):
                await self._drop_test_database(test_db_name)
                await self._mark_backup_tested(backup_id, True)
                return {"success": True, "message": "Backup restore test passed"}
            else:
                await self._drop_test_database(test_db_name)
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            await self._drop_test_database(test_db_name)
            return {"success": False, "error": str(e)}

    async def _create_test_database(self, db_name: str):
        db_user = self.settings.database.postgres_user
        db_host = self.settings.database.postgres_host
        db_port = self.settings.database.postgres_port
        
        cmd = [
            "createdb",
            f"--host={db_host}",
            f"--port={db_port}",
            f"--username={db_user}",
            db_name
        ]
        
        process = subprocess.run(
            cmd,
            env={"PGPASSWORD": self.settings.database.postgres_password},
            capture_output=True
        )
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to create test database: {process.stderr.decode()}")

    async def _drop_test_database(self, db_name: str):
        db_user = self.settings.database.postgres_user
        db_host = self.settings.database.postgres_host
        db_port = self.settings.database.postgres_port
        
        cmd = [
            "dropdb",
            f"--host={db_host}",
            f"--port={db_port}",
            f"--username={db_user}",
            "--if-exists",
            db_name
        ]
        
        subprocess.run(
            cmd,
            env={"PGPASSWORD": self.settings.database.postgres_password},
            capture_output=True
        )

    async def _cleanup_old_backups(self):
        cutoff_date = datetime.utcnow() - timedelta(days=self.backup_retention_days)
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT backup_id, filename FROM database_backups 
                    WHERE created_at < %s AND status = 'completed'
                """), (cutoff_date,))
                
                for row in result.fetchall():
                    backup_id, filename = row
                    await self.delete_backup(backup_id)
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {str(e)}")

    async def _log_backup_start(self, backup_id: str, backup_type: BackupType, filename: str, notes: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                INSERT INTO database_backups (backup_id, backup_type, filename, status, notes)
                VALUES (%s, %s, %s, %s, %s)
            """), (backup_id, backup_type.value, filename, BackupStatus.IN_PROGRESS.value, notes))
            await session.commit()

    async def _log_backup_complete(self, backup_id: str, size_bytes: int, checksum: str, compression_ratio: float):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET status = %s, size_bytes = %s, checksum = %s, compression_ratio = %s, completed_at = CURRENT_TIMESTAMP
                WHERE backup_id = %s
            """), (BackupStatus.COMPLETED.value, size_bytes, checksum, compression_ratio, backup_id))
            await session.commit()

    async def _log_backup_failed(self, backup_id: str, error: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET status = %s, notes = %s, completed_at = CURRENT_TIMESTAMP
                WHERE backup_id = %s
            """), (BackupStatus.FAILED.value, error, backup_id))
            await session.commit()

    async def _log_restore_start(self, backup_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET status = %s, notes = 'Restore in progress'
                WHERE backup_id = %s
            """), (BackupStatus.RESTORING.value, backup_id))
            await session.commit()

    async def _log_restore_complete(self, backup_id: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET status = %s, notes = 'Restore completed successfully'
                WHERE backup_id = %s
            """), (BackupStatus.COMPLETED.value, backup_id))
            await session.commit()

    async def _log_restore_failed(self, backup_id: str, error: str):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET status = %s, notes = %s
                WHERE backup_id = %s
            """), (BackupStatus.FAILED.value, f"Restore failed: {error}", backup_id))
            await session.commit()

    async def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute(text("""
                SELECT backup_id, backup_type, filename, size_bytes, created_at, status, checksum
                FROM database_backups WHERE backup_id = %s
            """), (backup_id,))
            
            row = result.fetchone()
            if row:
                return BackupInfo(
                    id=backup_id,
                    status=BackupStatus(row[5]),
                    file_path=row[2],
                    created_at=row[4],
                    completed_at=None,
                    error_message=None
                )
            return None

    async def _get_last_backup(self) -> Optional[BackupInfo]:
        if not self.database:
            return None
        
        async with self.database.get_session() as session:
            result = await session.execute(text("""
                SELECT backup_id, backup_type, filename, size_bytes, created_at, status, checksum
                FROM database_backups 
                WHERE status = 'completed' 
                ORDER BY created_at DESC 
                LIMIT 1
            """))
            
            row = result.fetchone()
            if row:
                return BackupInfo(
                    id=row[0],
                    status=BackupStatus(row[5]),
                    file_path=row[2],
                    created_at=row[4],
                    completed_at=None,
                    error_message=None
                )
            return None

    async def _mark_backup_tested(self, backup_id: str, tested: bool):
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                UPDATE database_backups 
                SET restore_tested = %s
                WHERE backup_id = %s
            """), (tested, backup_id))
            await session.commit()

    async def get_backup_statistics(self) -> Dict[str, Any]:
        if not self.database:
            return {}
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        COUNT(*) as total_backups,
                        COUNT(*) FILTER (WHERE status = 'completed') as successful_backups,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed_backups,
                        SUM(size_bytes) FILTER (WHERE status = 'completed') as total_size,
                        AVG(compression_ratio) FILTER (WHERE status = 'completed') as avg_compression,
                        MAX(created_at) FILTER (WHERE status = 'completed') as last_backup
                    FROM database_backups
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_backups": row[0],
                        "successful_backups": row[1],
                        "failed_backups": row[2],
                        "total_size_bytes": row[3] or 0,
                        "avg_compression_ratio": row[4] or 0,
                        "last_backup": row[5].isoformat() if row[5] else None
                    }
                return {}
        except Exception as e:
            self.logger.error(f"Failed to get backup statistics: {str(e)}")
            return {}

    async def shutdown(self):
        self.logger.info("Shutting down BackupManager...")
        await self._cleanup_old_backups()
        self.logger.info("BackupManager shutdown complete")
