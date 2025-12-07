from typing import Optional, Dict, Any
import uuid
import logging
from ..config import settings
from ..database.connection import supabase_manager

logger = logging.getLogger(__name__)


class SupabaseStorageManager:
    def __init__(self):
        self.bucket_name = settings.supabase.storage_bucket
        self.storage_url = settings.supabase.storage_url
        self._client = None
    
    def _get_client(self):
        """Get Supabase client"""
        if not self._client:
            # Use the global supabase_manager initialized at app startup
            self._client = supabase_manager.get_supabase_client()
        return self._client
    
    def put_bytes(self, data: bytes, content_type: str, key_prefix: str = "media/") -> str:
        """Upload bytes to Supabase Storage"""
        try:
            client = self._get_client()
            key = f"{key_prefix}{uuid.uuid4().hex}"
            
            # Upload file to Supabase Storage
            result = client.storage.from_(self.bucket_name).upload(
                path=key,
                file=data,
                file_options={"content-type": content_type}
            )
            
            if result.get('error'):
                raise Exception(f"Upload failed: {result['error']}")
            
            # Get public URL
            public_url = client.storage.from_(self.bucket_name).get_public_url(key)
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload to Supabase Storage: {e}")
            raise
    
    def put_file(self, file_path: str, key_prefix: str = "media/") -> str:
        """Upload file to Supabase Storage"""
        try:
            client = self._get_client()
            key = f"{key_prefix}{uuid.uuid4().hex}"
            
            # Upload file to Supabase Storage
            with open(file_path, 'rb') as f:
                result = client.storage.from_(self.bucket_name).upload(
                    path=key,
                    file=f
                )
            
            if result.get('error'):
                raise Exception(f"Upload failed: {result['error']}")
            
            # Get public URL
            public_url = client.storage.from_(self.bucket_name).get_public_url(key)
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase Storage: {e}")
            raise
    
    def get_file(self, key: str) -> bytes:
        """Download file from Supabase Storage"""
        try:
            client = self._get_client()
            result = client.storage.from_(self.bucket_name).download(key)
            
            if result.get('error'):
                raise Exception(f"Download failed: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to download from Supabase Storage: {e}")
            raise
    
    def delete_file(self, key: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            client = self._get_client()
            result = client.storage.from_(self.bucket_name).remove([key])
            
            if result.get('error'):
                raise Exception(f"Delete failed: {result['error']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from Supabase Storage: {e}")
            return False
    
    def list_files(self, prefix: str = "", limit: int = 100) -> list:
        """List files in Supabase Storage"""
        try:
            client = self._get_client()
            result = client.storage.from_(self.bucket_name).list(
                path=prefix,
                limit=limit
            )
            
            if result.get('error'):
                raise Exception(f"List failed: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list files in Supabase Storage: {e}")
            return []
    
    def get_public_url(self, key: str) -> str:
        """Get public URL for a file"""
        try:
            client = self._get_client()
            return client.storage.from_(self.bucket_name).get_public_url(key)
        except Exception as e:
            logger.error(f"Failed to get public URL: {e}")
            raise
    
    def create_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Create a signed URL for private file access"""
        try:
            client = self._get_client()
            result = client.storage.from_(self.bucket_name).create_signed_url(
                path=key,
                expires_in=expires_in
            )
            
            if result.get('error'):
                raise Exception(f"Signed URL creation failed: {result['error']}")
            
            return result.get('signedURL', '')
            
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            raise


# Global storage manager instance
storage_manager = SupabaseStorageManager()

# Legacy alias for backward compatibility
s3_manager = storage_manager


