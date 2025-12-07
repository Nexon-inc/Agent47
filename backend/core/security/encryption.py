import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CredentialEncryption:
    """Handles encryption and decryption of sensitive user credentials"""
    
    def __init__(self):
        self._master_key = None
        self._fernet = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize encryption system with master key"""
        if self._initialized:
            return
        
        try:
            # Get master key from environment or generate if not exists
            master_key_hex = os.getenv("CREDENTIAL_MASTER_KEY")
            if not master_key_hex:
                # Generate new master key (should be done once and stored securely)
                master_key = Fernet.generate_key()
                master_key_hex = master_key.hex()
                logger.warning(f"Generated new master key: {master_key_hex}")
                logger.warning("Store this key securely in CREDENTIAL_MASTER_KEY environment variable")
            else:
                master_key = bytes.fromhex(master_key_hex)
            
            self._master_key = master_key
            self._fernet = Fernet(master_key)
            self._initialized = True
            logger.info("Credential encryption system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption system: {e}")
            raise
    
    def _derive_user_key(self, user_id: int, platform: str) -> bytes:
        """Derive user-specific encryption key"""
        if not self._initialized:
            raise RuntimeError("Encryption system not initialized")
        
        # Create salt from user_id and platform
        salt = f"{user_id}_{platform}".encode('utf-8')
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
        return key
    
    def encrypt_credential(self, user_id: int, platform: str, credential: str) -> str:
        """Encrypt a credential for a specific user and platform"""
        if not self._initialized:
            raise RuntimeError("Encryption system not initialized")
        
        if not credential:
            return ""
        
        try:
            # Derive user-specific key
            user_key = self._derive_user_key(user_id, platform)
            user_fernet = Fernet(user_key)
            
            # Encrypt the credential
            encrypted_data = user_fernet.encrypt(credential.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to encrypt credential for user {user_id}, platform {platform}: {e}")
            raise
    
    def decrypt_credential(self, user_id: int, platform: str, encrypted_credential: str) -> str:
        """Decrypt a credential for a specific user and platform"""
        if not self._initialized:
            raise RuntimeError("Encryption system not initialized")
        
        if not encrypted_credential:
            return ""
        
        try:
            # Derive user-specific key
            user_key = self._derive_user_key(user_id, platform)
            user_fernet = Fernet(user_key)
            
            # Decrypt the credential
            encrypted_data = base64.urlsafe_b64decode(encrypted_credential.encode('utf-8'))
            decrypted_data = user_fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to decrypt credential for user {user_id}, platform {platform}: {e}")
            raise
    
    def encrypt_credentials_dict(self, user_id: int, platform: str, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt all credentials in a dictionary"""
        if not self._initialized:
            raise RuntimeError("Encryption system not initialized")
        
        encrypted = {}
        sensitive_fields = ['access_token', 'refresh_token', 'api_key', 'api_secret', 'bearer_token']
        
        for key, value in credentials.items():
            if key in sensitive_fields and value:
                encrypted[key] = self.encrypt_credential(user_id, platform, str(value))
            else:
                encrypted[key] = value
        
        return encrypted
    
    def decrypt_credentials_dict(self, user_id: int, platform: str, encrypted_credentials: Dict[str, Any]) -> Dict[str, str]:
        """Decrypt all credentials in a dictionary"""
        if not self._initialized:
            raise RuntimeError("Encryption system not initialized")
        
        decrypted = {}
        sensitive_fields = ['access_token', 'refresh_token', 'api_key', 'api_secret', 'bearer_token']
        
        for key, value in encrypted_credentials.items():
            if key in sensitive_fields and value:
                decrypted[key] = self.decrypt_credential(user_id, platform, str(value))
            else:
                decrypted[key] = value
        
        return decrypted
    
    def validate_encryption_key(self) -> bool:
        """Validate that the encryption system is properly configured"""
        if not self._initialized:
            return False
        
        try:
            # Test encryption/decryption
            test_data = "test_credential_123"
            encrypted = self.encrypt_credential(1, "test_platform", test_data)
            decrypted = self.decrypt_credential(1, "test_platform", encrypted)
            return decrypted == test_data
        except Exception as e:
            logger.error(f"Encryption validation failed: {e}")
            return False

# Global instance
credential_encryption = CredentialEncryption()

async def get_credential_encryption() -> CredentialEncryption:
    """Get the global credential encryption instance"""
    if not credential_encryption._initialized:
        await credential_encryption.initialize()
    return credential_encryption
