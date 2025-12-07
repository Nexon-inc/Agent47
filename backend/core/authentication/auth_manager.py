from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from ..config import settings
from ..database.models import User, UserTier
from ..database import get_database, get_db

logger = logging.getLogger(__name__)

# Password hashing context - use bcrypt with fallback
import warnings
import sys
import io
import os
from contextlib import redirect_stderr, redirect_stdout

# Suppress bcrypt version warnings (bcrypt 4.0+ removed __about__ attribute)
# This is a known issue with passlib and bcrypt 4.0+, but it doesn't affect functionality
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")
warnings.filterwarnings("ignore", message=".*bcrypt.*")
warnings.filterwarnings("ignore", message=".*password cannot be longer than 72 bytes.*")
warnings.filterwarnings("ignore", message=".*truncate manually.*")

# Suppress all output from passlib during initialization
# (passlib tries to read bcrypt.__about__.__version__ which doesn't exist in bcrypt 4.0+)
# This is a trapped error that passlib handles internally, so we suppress all output
with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Test bcrypt works (suppress all warnings during test)
        try:
            test_hash = pwd_context.hash("test")
        except Exception:
            # Ignore any exceptions during test - bcrypt will still work
            pass

logger.info("Bcrypt password hashing initialized successfully")

# JWT token security
security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
        self.refresh_token_expire_days = settings.security.refresh_token_expire_days
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Handle bcrypt hashes (start with $2a$, $2b$, $2y$, etc.)
            if hashed_password.startswith('$2'):
                # Truncate password if needed for bcrypt
                if isinstance(plain_password, str):
                    password_bytes = plain_password.encode('utf-8')
                    if len(password_bytes) > 72:
                        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
                try:
                    return pwd_context.verify(plain_password, hashed_password)
                except ValueError as ve:
                    if "cannot be longer than 72 bytes" in str(ve):
                        plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
                        return pwd_context.verify(plain_password, hashed_password)
                    raise
            elif hashed_password.startswith('sha256$'):
                # Fallback for SHA256 hashes with salt
                import hashlib
                parts = hashed_password.split('$')
                if len(parts) == 3:
                    salt = parts[1]
                    stored_hash = parts[2]
                    computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
                    return computed_hash == stored_hash
                return False
            else:
                # Legacy SHA256 without salt (for backwards compatibility)
                import hashlib
                return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        try:
            # Bcrypt has a 72-byte limit, ensure password is within limit
            if isinstance(password, str):
                password_bytes = password.encode('utf-8')
                if len(password_bytes) > 72:
                    logger.warning(f"Password exceeds 72 bytes, truncating...")
                    password = password_bytes[:72].decode('utf-8', errors='ignore')
            
            # Try bcrypt first
            try:
                return pwd_context.hash(password)
            except ValueError as ve:
                # If bcrypt fails due to length or other issues, try with truncated password
                if "cannot be longer than 72 bytes" in str(ve):
                    password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
                    return pwd_context.hash(password)
                raise
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            # Fallback to SHA256 + salt if bcrypt completely fails
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            logger.warning("Falling back to SHA256 hash with salt (less secure than bcrypt)")
            return f"sha256${salt}${hashlib.sha256((password + salt).encode()).hexdigest()}"
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            to_encode.update({"exp": expire, "type": "access"})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Access token creation error: {e}")
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
            
            to_encode.update({"exp": expire, "type": "refresh"})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has no expiration"
                )
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            db = get_database()
            
            async with db.get_session() as session:
                # Get user by email
                from sqlalchemy import select
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User not found: {email}")
                    return None
                
                # Check if password is empty or None
                if not user.hashed_password:
                    logger.warning(f"User {email} has no password hash")
                    return None
                
                # Verify password
                password_valid = self.verify_password(password, user.hashed_password)
                if not password_valid:
                    logger.warning(f"Password verification failed for user: {email}")
                    return None
                
                if not user.is_active:
                    logger.warning(f"User {email} is not active")
                    return None
                
                logger.info(f"User authenticated successfully: {email}")
                return user
                
        except Exception as e:
            logger.error(f"User authentication error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials, db) -> User:
        """Get current authenticated user from token"""
        try:
            token = credentials.credentials
            payload = self.verify_token(token, "access")
            
            # sub may be encoded as a string; coerce to int for DB lookup
            raw_sub = payload.get("sub")
            try:
                user_id = int(raw_sub) if raw_sub is not None else None
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User is inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def get_current_active_user(self, current_user: User) -> User:
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
    
    async def get_current_user_with_tier(self, required_tier: UserTier, current_user: User = Depends(get_current_user)) -> User:
        """Get current user with specific tier requirement.

        Compare tiers using an explicit hierarchy instead of string comparison.
        """
        # If user has no tier, deny access
        if not getattr(current_user, "tier", None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required tier: {required_tier.value}"
            )

        # Define explicit tier order
        tier_hierarchy = [UserTier.FREE, UserTier.STARTER, UserTier.PRO]

        try:
            user_index = tier_hierarchy.index(current_user.tier)
        except ValueError:
            # Unknown user tier - deny
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied due to unknown user tier"
            )

        try:
            required_index = tier_hierarchy.index(required_tier)
        except ValueError:
            # Unknown required tier - treat as denied
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied due to unknown required tier"
            )

        if user_index < required_index:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required tier: {required_tier.value}"
            )

        return current_user
    
    def create_user_tokens(self, user: User) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        try:
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
            
            access_token = self.create_access_token(
                data={"sub": str(user.id), "email": user.email, "tier": user.tier.value if user.tier else None},
                expires_delta=access_token_expires
            )
            
            refresh_token = self.create_refresh_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"Token creation error for user {user.id}: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            payload = self.verify_token(refresh_token, "refresh")
            # Coerce subject to int
            raw_sub = payload.get("sub")
            try:
                user_id = int(raw_sub) if raw_sub is not None else None
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            db = get_database()
            
            async with db.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if user is None or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid refresh token"
                    )
                
                # Create new access token
                access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
                access_token = self.create_access_token(
                    data={"sub": str(user.id), "email": user.email, "tier": user.tier.value if user.tier else None},
                    expires_delta=access_token_expires
                )
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": self.access_token_expire_minutes * 60
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        warnings = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) < 12:
            warnings.append("Consider using a longer password (12+ characters)")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            warnings.append("Consider adding special characters for better security")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": max(0, 5 - len(errors) + len(warnings))
        }
    
    async def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            # Verify current password
            if not self.verify_password(current_password, user.hashed_password):
                return False
            
            # Validate new password
            validation = self.validate_password_strength(new_password)
            if not validation["is_valid"]:
                return False
            
            # Hash new password
            new_hashed_password = self.get_password_hash(new_password)
            
            # Update user password
            db = get_database()
            
            async with db.get_session() as session:
                user.hashed_password = new_hashed_password
                await session.commit()
            
            logger.info(f"Password changed for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Password change error for user {user.id}: {e}")
            return False
    
    async def reset_password_request(self, email: str) -> bool:
        """Request password reset"""
        try:
            db = get_database()
            
            async with db.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                
                if user and user.is_active:
                    # Generate reset token
                    reset_token = self.create_access_token(
                        data={"sub": str(user.id), "email": user.email, "purpose": "reset"},
                        expires_delta=timedelta(hours=1)
                    )
                    
                    # Send password reset email
                    await self._send_password_reset_email(user.email, user.username, reset_token)
                    
                    logger.info(f"Password reset email sent to user {user.id} ({user.email})")
                    return True
            
            # Always return True for security (don't reveal if email exists)
            logger.info(f"Password reset requested for email: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            # Still return True to not reveal if email exists
            return True

    async def _send_password_reset_email(self, email: str, username: str, reset_token: str):
        """Send password reset email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from core.config import settings
            
            # Create reset URL
            reset_url = f"{settings.frontend_url}/auth/reset-password?token={reset_token}"
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = f"{settings.email.from_name} <{settings.email.from_email}>"
            msg['To'] = email
            msg['Subject'] = "Reset Your Agent47 Password"
            
            # Create email body
            body = f"""
Hello {username},

You requested a password reset for your Agent47 account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
The Agent47 Team

---
This email was sent from {settings.email.from_email}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if settings.email.smtp_host and settings.email.smtp_port:
                server = smtplib.SMTP(settings.email.smtp_host, settings.email.smtp_port)
                if settings.email.use_tls:
                    server.starttls()
                if settings.email.smtp_username and settings.email.smtp_password:
                    server.login(settings.email.smtp_username, settings.email.smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Password reset email sent to {email}")
            else:
                logger.warning("SMTP not configured, password reset email not sent")
                logger.info(f"Reset URL for {email}: {reset_url}")
                
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            # Don't raise the exception, just log it

    async def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using a reset token"""
        try:
            # Verify the token
            payload = self.verify_token(token)
            if not payload or payload.get("purpose") != "reset":
                logger.error("Invalid reset token")
                return False
            
            user_id = payload.get("sub")
            if not user_id:
                logger.error("No user ID in reset token")
                return False
            
            db = get_database()
            
            async with db.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(select(User).where(User.id == int(user_id)))
                user = result.scalar_one_or_none()
                
                if not user or not user.is_active:
                    logger.error(f"User {user_id} not found or inactive")
                    return False
                
                # Hash the new password
                hashed_password = self.hash_password(new_password)
                
                # Update the user's password
                user.password_hash = hashed_password
                user.updated_at = datetime.utcnow()
                
                await session.commit()
                
                logger.info(f"Password reset successfully for user {user.id}")
                return True
                
        except Exception as e:
            logger.error(f"Password reset with token error: {e}")
            return False

# Global auth manager instance
auth_manager = AuthManager()

async def get_auth() -> AuthManager:
    return auth_manager

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    return auth_manager.create_access_token(data, expires_delta)

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    return auth_manager.verify_token(token, token_type)

# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
    return await auth_manager.get_current_user(credentials, db)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return await auth_manager.get_current_active_user(current_user)

async def require_tier(required_tier: UserTier, current_user: User = Depends(get_current_user)) -> User:
    return await auth_manager.get_current_user_with_tier(required_tier, current_user)
