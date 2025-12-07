import json
import base64
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import logging

logger = logging.getLogger(__name__)

class PlatformCredentialManager:
    """Manages platform credentials with encryption and secure storage."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.credentials: Dict[str, Dict[str, Any]] = {}
        self._load_credentials()
    
    def _generate_encryption_key(self) -> str:
        """Generate a new encryption key."""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        return key.decode()
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def _load_credentials(self):
        """Load credentials from secure database storage."""
        try:
            from ..database.connection import get_database
            from .models import PlatformCredential
            from cryptography.fernet import Fernet
            import base64
            
            # Load credentials from database
            db = get_database()
            with db.get_session() as session:
                credentials_data = session.query(PlatformCredential).all()
                self.credentials = {}
                
                # Initialize encryption key
                encryption_key = self._get_encryption_key()
                fernet = Fernet(encryption_key)
                
                for cred in credentials_data:
                    try:
                        # Decrypt the credentials
                        decrypted_data = fernet.decrypt(cred.encrypted_credentials.encode()).decode()
                        import json
                        credentials_dict = json.loads(decrypted_data)
                        
                        self.credentials[cred.id] = {
                            "id": cred.id,
                            "platform": cred.platform,
                            "user_id": cred.user_id,
                            "credentials": credentials_dict,
                            "created_at": cred.created_at.isoformat() if cred.created_at else None,
                            "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
                            "status": cred.status
                        }
                    except Exception as decrypt_error:
                        logger.error(f"Failed to decrypt credentials for {cred.id}: {decrypt_error}")
                        continue
            
            logger.info(f"Credentials loaded successfully: {len(self.credentials)} credential sets")
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            # Fallback to empty data structure
            self.credentials = {}
    
    def _save_credentials(self):
        """Save credentials to secure database storage."""
        try:
            from ..database.connection import get_database
            from .models import PlatformCredential
            from cryptography.fernet import Fernet
            from datetime import datetime
            import json
            
            db = get_database()
            with db.get_session() as session:
                # Initialize encryption key
                encryption_key = self._get_encryption_key()
                fernet = Fernet(encryption_key)
                
                # Save credentials to database
                for cred_id, cred_data in self.credentials.items():
                    # Encrypt the credentials
                    credentials_json = json.dumps(cred_data["credentials"])
                    encrypted_credentials = fernet.encrypt(credentials_json.encode()).decode()
                    
                    existing_cred = session.query(PlatformCredential).filter(PlatformCredential.id == cred_id).first()
                    if existing_cred:
                        # Update existing credentials
                        existing_cred.platform = cred_data["platform"]
                        existing_cred.user_id = cred_data["user_id"]
                        existing_cred.encrypted_credentials = encrypted_credentials
                        existing_cred.status = cred_data["status"]
                        existing_cred.updated_at = datetime.utcnow()
                    else:
                        # Create new credentials
                        new_cred = PlatformCredential(
                            id=cred_id,
                            platform=cred_data["platform"],
                            user_id=cred_data["user_id"],
                            encrypted_credentials=encrypted_credentials,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            status=cred_data["status"]
                        )
                        session.add(new_cred)
                
                session.commit()
                logger.info("Credentials saved successfully to secure database")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
    
    def add_platform_credentials(
        self, 
        platform_name: str, 
        credentials: Dict[str, str],
        user_id: str,
        description: Optional[str] = None
    ) -> str:
        """
        Add platform credentials for a user.
        
        Args:
            platform_name: Name of the platform
            credentials: Dictionary of credential key-value pairs
            user_id: ID of the user
            description: Optional description of the credentials
            
        Returns:
            Credential ID
        """
        try:
            credential_id = self._generate_credential_id(platform_name, user_id)
            
            # Encrypt sensitive credentials
            encrypted_credentials = {}
            for key, value in credentials.items():
                if self._is_sensitive_field(key):
                    encrypted_credentials[key] = self._encrypt_data(value)
                else:
                    encrypted_credentials[key] = value
            
            credential_data = {
                "id": credential_id,
                "platform_name": platform_name,
                "credentials": encrypted_credentials,
                "user_id": user_id,
                "description": description,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            self.credentials[credential_id] = credential_data
            self._save_credentials()
            
            logger.info(f"Added credentials for platform {platform_name} for user {user_id}")
            return credential_id
            
        except Exception as e:
            logger.error(f"Failed to add platform credentials: {e}")
            raise
    
    def get_platform_credentials(self, credential_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get platform credentials by ID.
        
        Args:
            credential_id: ID of the credentials
            user_id: ID of the user (for security)
            
        Returns:
            Decrypted credentials or None if not found
        """
        try:
            if credential_id not in self.credentials:
                return None
            
            credential_data = self.credentials[credential_id]
            
            # Security check
            if credential_data["user_id"] != user_id:
                logger.warning(f"User {user_id} attempted to access credentials {credential_id} belonging to user {credential_data['user_id']}")
                return None
            
            # Decrypt sensitive credentials
            decrypted_credentials = {}
            for key, value in credential_data["credentials"].items():
                if self._is_sensitive_field(key):
                    decrypted_credentials[key] = self._decrypt_data(value)
                else:
                    decrypted_credentials[key] = value
            
            return {
                "id": credential_data["id"],
                "platform_name": credential_data["platform_name"],
                "credentials": decrypted_credentials,
                "user_id": credential_data["user_id"],
                "description": credential_data["description"],
                "created_at": credential_data["created_at"],
                "updated_at": credential_data["updated_at"],
                "is_active": credential_data["is_active"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get platform credentials: {e}")
            return None
    
    def list_user_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all credentials for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of credential metadata (without sensitive data)
        """
        try:
            user_credentials = []
            
            for credential_id, credential_data in self.credentials.items():
                if credential_data["user_id"] == user_id and credential_data["is_active"]:
                    user_credentials.append({
                        "id": credential_data["id"],
                        "platform_name": credential_data["platform_name"],
                        "description": credential_data["description"],
                        "created_at": credential_data["created_at"],
                        "updated_at": credential_data["updated_at"]
                    })
            
            return user_credentials
            
        except Exception as e:
            logger.error(f"Failed to list user credentials: {e}")
            return []
    
    def update_platform_credentials(
        self, 
        credential_id: str, 
        credentials: Dict[str, str],
        user_id: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Update platform credentials.
        
        Args:
            credential_id: ID of the credentials
            credentials: Updated credential key-value pairs
            user_id: ID of the user
            description: Optional updated description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if credential_id not in self.credentials:
                return False
            
            credential_data = self.credentials[credential_id]
            
            # Security check
            if credential_data["user_id"] != user_id:
                logger.warning(f"User {user_id} attempted to update credentials {credential_id} belonging to user {credential_data['user_id']}")
                return False
            
            # Encrypt sensitive credentials
            encrypted_credentials = {}
            for key, value in credentials.items():
                if self._is_sensitive_field(key):
                    encrypted_credentials[key] = self._encrypt_data(value)
                else:
                    encrypted_credentials[key] = value
            
            # Update credential data
            credential_data["credentials"] = encrypted_credentials
            if description is not None:
                credential_data["description"] = description
            credential_data["updated_at"] = datetime.utcnow().isoformat()
            
            self._save_credentials()
            
            logger.info(f"Updated credentials {credential_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update platform credentials: {e}")
            return False
    
    def delete_platform_credentials(self, credential_id: str, user_id: str) -> bool:
        """
        Delete platform credentials.
        
        Args:
            credential_id: ID of the credentials
            user_id: ID of the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if credential_id not in self.credentials:
                return False
            
            credential_data = self.credentials[credential_id]
            
            # Security check
            if credential_data["user_id"] != user_id:
                logger.warning(f"User {user_id} attempted to delete credentials {credential_id} belonging to user {credential_data['user_id']}")
                return False
            
            # Soft delete
            credential_data["is_active"] = False
            credential_data["updated_at"] = datetime.utcnow().isoformat()
            
            self._save_credentials()
            
            logger.info(f"Deleted credentials {credential_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete platform credentials: {e}")
            return False
    
    def validate_credentials(self, credential_id: str, user_id: str) -> bool:
        """
        Validate if credentials are still valid.
        
        Args:
            credential_id: ID of the credentials
            user_id: ID of the user
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            credentials = self.get_platform_credentials(credential_id, user_id)
            if not credentials:
                return False
            
            # In a real implementation, this would test the credentials against the platform
            # For now, we'll just check if they exist and are active
            return credentials["is_active"]
            
        except Exception as e:
            logger.error(f"Failed to validate credentials: {e}")
            return False
    
    def _generate_credential_id(self, platform_name: str, user_id: str) -> str:
        """Generate a unique credential ID."""
        data = f"{platform_name}:{user_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field contains sensitive data that should be encrypted."""
        sensitive_fields = {
            "password", "token", "secret", "key", "api_key", "access_token",
            "refresh_token", "private_key", "client_secret", "auth_token"
        }
        return field_name.lower() in sensitive_fields
    
    def get_credential_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user credentials.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with credential statistics
        """
        try:
            user_credentials = [c for c in self.credentials.values() if c["user_id"] == user_id]
            
            platform_counts = {}
            for credential in user_credentials:
                platform = credential["platform_name"]
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            return {
                "total_credentials": len(user_credentials),
                "active_credentials": len([c for c in user_credentials if c["is_active"]]),
                "platforms": list(platform_counts.keys()),
                "platform_counts": platform_counts,
                "oldest_credential": min([c["created_at"] for c in user_credentials]) if user_credentials else None,
                "newest_credential": max([c["created_at"] for c in user_credentials]) if user_credentials else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get credential statistics: {e}")
            return {}

# Global instance
platform_credentials = PlatformCredential()

def get_platform_credentials() -> PlatformCredential:
    """Get the global platform credentials instance."""
    return platform_credentials
