# Supabase Authentication Manager for Agent47
# This file handles authentication using Supabase Auth

from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from supabase import Client
from ..config import settings
from ..database.connection import supabase_manager
from .email_verification_manager import email_verification_manager

logger = logging.getLogger(__name__)


class SupabaseAuthManager:
    def __init__(self):
        self._client = None
    
    def _get_client(self) -> Client:
        """Get Supabase client"""
        if not self._client:
            # Use the global supabase_manager initialized at app startup
            self._client = supabase_manager.get_supabase_client()
        return self._client
    
    async def signup(self, email: str, password: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sign up a new user with Gmail email verification"""
        try:
            client = self._get_client()
            
            # Check if user already exists in Supabase Auth
            try:
                # Try to get user by email (this will fail if user doesn't exist, which is what we want)
                existing_users = client.auth.admin.list_users()
                for user in existing_users.users:
                    if user.email == email:
                        logger.warning(f"User {email} already exists in Supabase Auth")
                        # User exists in Supabase but might not be in our database
                        # Try to sign them in instead
                        try:
                            signin_result = await self.signin(email, password)
                            if signin_result.get("success"):
                                return {
                                    "user": signin_result.get("user"),
                                    "session": signin_result.get("session"),
                                    "success": True,
                                    "existing_user": True
                                }
                        except Exception:
                            pass
                        # If signin fails, raise error
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Email '{email}' is already registered. Please use a different email or try logging in."
                        )
            except HTTPException:
                raise
            except Exception as check_error:
                # If checking fails, continue with signup (user might not exist)
                logger.debug(f"Error checking existing user (non-fatal): {check_error}")
            
            # Create user with Supabase Auth (disable email confirmation)
            result = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_data or {},
                    "email_redirect_to": None  # Disable Supabase email confirmation
                }
            })
            
            if result.user:
                logger.info(f"User signed up successfully: {email}")
                
                # Send Gmail verification email instead of Supabase
                try:
                    # Initialize email verification manager if not already done
                    if not email_verification_manager.gmail_service._initialized:
                        await email_verification_manager.initialize()
                    
                    # Get the local database user ID (integer) from email
                    # Supabase Auth uses UUIDs, but our local database uses integer IDs
                    local_user_id = await self._get_local_user_id_by_email(email)
                    
                    if local_user_id:
                        # Send verification email via Gmail API
                        user_name = user_data.get('first_name', '') if user_data else ''
                        verification_sent = await email_verification_manager.send_verification_email(
                            user_id=local_user_id,
                            email=email,
                            user_name=user_name
                        )
                    else:
                        logger.warning(f"Could not find local user ID for {email}, skipping verification email")
                        verification_sent = False
                    
                    if verification_sent:
                        logger.info(f"Gmail verification email sent to {email}")
                    else:
                        logger.warning(f"Failed to send Gmail verification email to {email}")
                        
                except Exception as email_error:
                    logger.error(f"Failed to send Gmail verification email to {email}: {email_error}")
                    # Don't fail signup if email sending fails
                
                return {
                    "user": result.user,
                    "session": result.session,
                    "success": True,
                    "verification_email_sent": True
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions (like 409 Conflict)
            raise
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Signup failed for {email}: {e}")
            
            # Check if error is about user already existing in Supabase
            if 'already registered' in error_str or 'user already exists' in error_str or 'email already' in error_str or 'already been registered' in error_str or 'duplicate' in error_str:
                logger.warning(f"User {email} already exists in Supabase Auth, attempting recovery...")
                
                # Attempt to sign in to "recover" the user session 
                # if they already exist in Supabase but not in our local DB
                try:
                    signin_result = await self.signin(email, password)
                    if signin_result.get("success"):
                        logger.info(f"Recovery successful for {email}")
                        return {
                            "user": signin_result.get("user"),
                            "session": signin_result.get("session"),
                            "success": True,
                            "existing_user": True
                        }
                except Exception as recovery_error:
                    logger.warning(f"Recovery signin failed for {email}: {recovery_error}")
                
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{email}' is already registered. Please use a different email or try logging in."
                )
            # Check for password validation errors
            elif 'password' in error_str and ('weak' in error_str or 'short' in error_str or 'requirement' in error_str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password does not meet requirements. Password must be at least 6 characters long."
                )
            # Check for email validation errors
            elif 'invalid email' in error_str or 'email format' in error_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format. Please enter a valid email address."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Signup failed: {str(e)}"
                )
    
    async def signin(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user"""
        try:
            client = self._get_client()
            
            # Sign in with Supabase Auth
            result = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user and result.session:
                logger.info(f"User signed in successfully: {email}")
                return {
                    "user": result.user,
                    "session": result.session,
                    "success": True
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Signin failed for {email}: {e}", exc_info=True)
            
            # Check for specific authentication errors
            if 'invalid credentials' in error_str or 'wrong password' in error_str or 'incorrect' in error_str or 'invalid login' in error_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            elif 'user not found' in error_str or 'email not found' in error_str or 'no user found' in error_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No account found with this email address"
                )
            elif 'email not confirmed' in error_str or 'email not verified' in error_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email address before logging in"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Login failed: {str(e)}"
                )
    
    async def signout(self, access_token: str) -> bool:
        """Sign out a user"""
        try:
            client = self._get_client()
            
            # Set the session for the client
            client.auth.set_session(access_token, "")
            
            # Sign out
            result = client.auth.sign_out()
            
            logger.info("User signed out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Signout failed: {e}")
            return False
    
    async def _get_local_user_id_by_email(self, email: str) -> Optional[int]:
        """Get local database user ID (integer) from email address"""
        try:
            from ..database.models import User
            from sqlalchemy import select
            
            async with supabase_manager.get_session() as session:
                result = await session.execute(
                    select(User.id).where(User.email == email)
                )
                user_id = result.scalar_one_or_none()
                return user_id
                
        except Exception as e:
            logger.error(f"Failed to get local user ID for email {email}: {e}")
            return None
    
    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token"""
        try:
            client = self._get_client()
            
            # Set the session for the client
            client.auth.set_session(access_token, "")
            
            # Get user
            user = client.auth.get_user()
            
            if user:
                return user
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        try:
            client = self._get_client()
            
            # Refresh session
            result = client.auth.refresh_session(refresh_token)
            
            if result.session:
                logger.info("Token refreshed successfully")
                return {
                    "session": result.session,
                    "success": True
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    async def reset_password(self, email: str) -> bool:
        """Send password reset email"""
        try:
            client = self._get_client()
            
            # Send password reset email
            result = client.auth.reset_password_email(email)
            
            logger.info(f"Password reset email sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset failed for {email}: {e}")
            return False
    
    async def update_user(self, access_token: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information"""
        try:
            client = self._get_client()
            
            # Set the session for the client
            client.auth.set_session(access_token, "")
            
            # Update user
            result = client.auth.update_user(updates)
            
            if result.user:
                logger.info("User updated successfully")
                return result.user
            else:
                return None
                
        except Exception as e:
            logger.error(f"User update failed: {e}")
            return None
    
    async def change_password(self, access_token: str, new_password: str) -> bool:
        """Change user password"""
        try:
            client = self._get_client()
            
            # Set the session for the client
            client.auth.set_session(access_token, "")
            
            # Update password
            result = client.auth.update_user({
                "password": new_password
            })
            
            if result.user:
                logger.info("Password changed successfully")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return False
    
    async def verify_email(self, access_token: str) -> bool:
        """Verify user email (legacy method - now handled by Gmail verification)"""
        try:
            # This method is now deprecated in favor of Gmail verification
            # Keep for backward compatibility but log warning
            logger.warning("verify_email method called - use Gmail verification instead")
            return False
                
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return False
    
    async def resend_verification_email(self, user_id: str, email: str, user_name: str = None) -> bool:
        """Resend verification email via Gmail API"""
        try:
            # Initialize email verification manager if not already done
            if not email_verification_manager.gmail_service._initialized:
                await email_verification_manager.initialize()
            
            # Resend verification email via Gmail API
            verification_sent = await email_verification_manager.resend_verification_email(
                user_id=user_id,
                email=email,
                user_name=user_name
            )
            
            if verification_sent:
                logger.info(f"Gmail verification email resent to {email}")
                return True
            else:
                logger.error(f"Failed to resend Gmail verification email to {email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to resend verification email to {email}: {e}")
            return False
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            client = self._get_client()
            
            # Verify token
            result = client.auth.get_user(token)
            
            if result:
                return result
            else:
                return None
                
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def create_anonymous_user(self) -> Dict[str, Any]:
        """Create anonymous user"""
        try:
            client = self._get_client()
            
            # Create anonymous user
            result = client.auth.sign_in_anonymous()
            
            if result.user and result.session:
                logger.info("Anonymous user created successfully")
                return {
                    "user": result.user,
                    "session": result.session,
                    "success": True
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create anonymous user"
                )
                
        except Exception as e:
            logger.error(f"Anonymous user creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create anonymous user: {str(e)}"
            )
    
    async def get_user_metadata(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user metadata from database"""
        try:
            client = self._get_client()
            
            # Get user from database
            result = client.table('users').select('*').eq('id', user_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get user metadata: {e}")
            return None
    
    async def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata in database"""
        try:
            client = self._get_client()
            
            # Update user in database
            result = client.table('users').update(metadata).eq('id', user_id).execute()
            
            if result.data:
                logger.info(f"User metadata updated for: {user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to update user metadata: {e}")
            return False


# Global auth manager instance
supabase_auth_manager = SupabaseAuthManager()
