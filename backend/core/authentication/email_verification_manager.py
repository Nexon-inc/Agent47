"""
Email Verification Manager for Agent47
Handles email verification tokens, validation, and user verification status
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status

from ..config import settings
from ..database.models import User, EmailVerificationToken
from ..database import get_database
from .gmail_auth_service import gmail_auth_service

logger = logging.getLogger(__name__)

class EmailVerificationManager:
    """Manages email verification tokens and verification process"""
    
    def __init__(self):
        self.settings = settings.gmail
        self.gmail_service = gmail_auth_service
        
    async def initialize(self) -> bool:
        """Initialize the email verification manager"""
        try:
            logger.info("Initializing Email Verification Manager...")
            
            # Initialize Gmail service
            gmail_initialized = await self.gmail_service.initialize()
            if not gmail_initialized:
                logger.error("Failed to initialize Gmail service")
                return False
            
            logger.info("Email Verification Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Email Verification Manager: {e}")
            return False
    
    def _generate_verification_token(self) -> str:
        """Generate a secure verification token"""
        # Generate a cryptographically secure random token
        token = secrets.token_urlsafe(32)
        
        # Hash the token for storage (we'll store the hash, not the plain token)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        return token, token_hash
    
    async def create_verification_token(
        self,
        user_id: int,
        email: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[str]:
        """Create a new email verification token for a user"""
        try:
            # Generate token
            plain_token, token_hash = self._generate_verification_token()
            
            # Calculate expiry time
            expiry_time = datetime.utcnow() + timedelta(hours=self.settings.verification_token_expiry_hours)
            
            # Create verification token record
            verification_token = EmailVerificationToken(
                user_id=user_id,
                token=token_hash,  # Store hash, not plain token
                email=email,
                expires_at=expiry_time,
                used=False,
                created_at=datetime.utcnow()
            )
            
            # Use provided session or create new one
            if session:
                session.add(verification_token)
                await session.flush()  # Flush to get the ID
            else:
                db = get_database()
                async with db.get_session() as new_session:
                    new_session.add(verification_token)
                    await new_session.commit()
            
            logger.info(f"Created verification token for user {user_id} ({email})")
            return plain_token
            
        except Exception as e:
            logger.error(f"Failed to create verification token for user {user_id}: {e}")
            return None
    
    async def send_verification_email(
        self,
        user_id: int,
        email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send verification email to user"""
        try:
            # Create verification token
            verification_token = await self.create_verification_token(user_id, email)
            if not verification_token:
                logger.error(f"Failed to create verification token for user {user_id}")
                return False
            
            # Send email via Gmail API
            email_sent = await self.gmail_service.send_verification_email(
                to_email=email,
                verification_token=verification_token,
                user_name=user_name
            )
            
            if email_sent:
                logger.info(f"Verification email sent to {email} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to send verification email to {email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    async def verify_email_token(
        self,
        token: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[Dict[str, Any]]:
        """Verify an email verification token"""
        try:
            # Hash the provided token
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Use provided session or create new one
            if session:
                # Find the verification token
                result = await session.execute(
                    select(EmailVerificationToken).where(
                        EmailVerificationToken.token == token_hash,
                        EmailVerificationToken.used == False,
                        EmailVerificationToken.expires_at > datetime.utcnow()
                    )
                )
                verification_token = result.scalar_one_or_none()
                
                if not verification_token:
                    logger.warning(f"Invalid or expired verification token")
                    return None
                
                # Mark token as used
                verification_token.used = True
                await session.flush()
                
                # Get user information
                user_result = await session.execute(
                    select(User).where(User.id == verification_token.user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User {verification_token.user_id} not found")
                    return None
                
                # Mark user email as verified
                user.is_verified = True
                user.updated_at = datetime.utcnow()
                await session.flush()
                
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "verified": True
                }
            else:
                db = get_database()
                async with db.get_session() as new_session:
                    return await self.verify_email_token(token, new_session)
            
        except Exception as e:
            logger.error(f"Failed to verify email token: {e}")
            return None
    
    async def resend_verification_email(
        self,
        user_id: int,
        email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Resend verification email to user"""
        try:
            # Check if user is already verified
            db = get_database()
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User {user_id} not found")
                    return False
                
                if user.is_verified:
                    logger.warning(f"User {user_id} is already verified")
                    return False
                
                # Invalidate existing tokens for this user
                await session.execute(
                    update(EmailVerificationToken).where(
                        EmailVerificationToken.user_id == user_id,
                        EmailVerificationToken.used == False
                    ).values(used=True)
                )
                await session.commit()
            
            # Send new verification email
            return await self.send_verification_email(user_id, email, user_name)
            
        except Exception as e:
            logger.error(f"Failed to resend verification email to user {user_id}: {e}")
            return False
    
    async def send_welcome_email(
        self,
        user_id: int,
        email: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send welcome email after successful verification"""
        try:
            # Send welcome email via Gmail API
            email_sent = await self.gmail_service.send_welcome_email(
                to_email=email,
                user_name=user_name
            )
            
            if email_sent:
                logger.info(f"Welcome email sent to {email} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to send welcome email to {email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired verification tokens"""
        try:
            db = get_database()
            async with db.get_session() as session:
                # Delete expired tokens
                result = await session.execute(
                    delete(EmailVerificationToken).where(
                        EmailVerificationToken.expires_at < datetime.utcnow()
                    )
                )
                deleted_count = result.rowcount
                await session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired verification tokens")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    async def get_verification_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get verification status for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                
                # Get pending verification tokens
                token_result = await session.execute(
                    select(EmailVerificationToken).where(
                        EmailVerificationToken.user_id == user_id,
                        EmailVerificationToken.used == False,
                        EmailVerificationToken.expires_at > datetime.utcnow()
                    )
                )
                pending_tokens = token_result.scalars().all()
                
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "pending_verification": len(pending_tokens) > 0,
                    "verification_expires_at": pending_tokens[0].expires_at if pending_tokens else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get verification status for user {user_id}: {e}")
            return None
    
    async def close(self):
        """Close the email verification manager"""
        await self.gmail_service.close()
        logger.info("Email Verification Manager closed")

# Global email verification manager instance
email_verification_manager = EmailVerificationManager()
