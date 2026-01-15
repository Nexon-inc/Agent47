from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from .supabase_auth import supabase_auth_manager
from .auth_manager import get_current_active_user, get_auth
from .email_verification_manager import email_verification_manager
from ..database.connection import get_supabase, get_db
from ..database.models import User, UserTier, BillingTier
from ..middleware.tier_validation import require_tier_selection, TierValidationError
from ..billing import get_billing, get_billing_plans
from ..config import settings
# from ...admin.goals import get_goal_manager, GoalManager  # Commented out for now

logger = logging.getLogger(__name__)

# Create authentication API router
auth_router = APIRouter(prefix="/api/v1")

# Pydantic models for request/response
class UserSignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetEmailRequest(BaseModel):
    email: EmailStr

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class CreateSubscriptionRequest(BaseModel):
    tier: str
    payment_method: str = "paystack"
    billing_period: str = "monthly"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    tier: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Optional[Dict[str, Any]]
    onboarding_data: Optional[Dict[str, Any]]
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime]

class OnboardingProfileData(BaseModel):
    """Profile data aligned with frontend onboarding flow."""
    # Business/profile basics
    role: Optional[str] = None
    industry: Optional[str] = None
    goals: Optional[list[str]] = []
    otherGoal: Optional[str] = None
    business_name: Optional[str] = None
    business_website: Optional[str] = None
    business_size: Optional[str] = None
    business_stage: Optional[str] = None
    country: Optional[str] = None
    continent: Optional[str] = None
    purpose: Optional[str] = None
    # Enriched from auth user in frontend payload
    name: Optional[str] = None
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None



class OnboardingData(BaseModel):
    # Only keep profile; remove social/tutorials/workflow per frontend alignment
    profile: OnboardingProfileData = OnboardingProfileData()

class OnboardingResponse(BaseModel):
    success: bool
    message: str
    onboarding_data: Optional[Dict[str, Any]] = None

class EmailVerificationRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    user_data: Optional[Dict[str, Any]] = None

# Authentication endpoints
@auth_router.post("/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserSignupRequest):
    """User registration endpoint using Supabase Auth"""
    try:
        # Prepare user data for Supabase
        supabase_user_data = {
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
        }
        
        # Create user with Supabase Auth
        result = await supabase_auth_manager.signup(
            email=user_data.email,
            password=user_data.password,
            user_data=supabase_user_data
        )

        if result["success"]:
            user = result["user"]
            session = result.get("session")

            # Create user record in database
            supabase_client = supabase_auth_manager._get_client()
            # Insert only known columns into the users table via Supabase REST
            insert_payload = {
                # Do NOT set the DB primary key here - Supabase Auth returns a UUID user.id
                # while our Postgres users.id is an integer SERIAL. Let Postgres assign id.
                "email": user.email,
                "username": user_data.username,
                "hashed_password": "",  # Password handled by Supabase Auth
                "full_name": f"{user_data.first_name} {user_data.last_name}",
                # Don't send 'tier' via REST – there is an enum mismatch in PostgREST; set via internal DB path if needed
                "is_active": True,
                "is_verified": False
            }

            new_user_record = None
            try:
                # Add timeout and retry for Supabase insert operation
                max_retries = 3
                retry_delay = 0.5
                
                for attempt in range(max_retries):
                    try:
                        db_result = supabase_client.table('users').insert(insert_payload).execute()
                        
                        # Try to determine the integer DB id for the newly created user. Many Supabase
                        # REST setups return the inserted row in db_result.data. If not, query by email.
                        try:
                            if hasattr(db_result, 'data') and db_result.data:
                                new_user_record = db_result.data[0]
                            else:
                                sel = supabase_client.table('users').select('*').eq('email', user.email).limit(1).execute()
                                if hasattr(sel, 'data') and sel.data:
                                    new_user_record = sel.data[0]
                        except Exception as lookup_error:
                            logger.warning(f"Failed to get user record from insert result: {lookup_error}")
                            # Non-fatal: we'll fall back to querying later
                            new_user_record = None
                        
                        if new_user_record:
                            break  # Success, exit retry loop
                            
                    except Exception as insert_error:
                        if attempt < max_retries - 1:
                            error_str = str(insert_error)
                            # Don't retry on duplicate key errors
                            if '23505' in error_str or 'duplicate key' in error_str.lower():
                                raise  # Re-raise to be handled by outer exception handler
                            logger.warning(f"Supabase insert failed (attempt {attempt + 1}/{max_retries}), retrying: {insert_error}")
                            await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        else:
                            logger.error(f"Supabase insert failed after {max_retries} attempts: {insert_error}")
                            raise  # Re-raise to be handled by outer exception handler
            except Exception as db_exc:
                # Supabase REST may raise a structured error or a plain exception whose
                # string contains Postgres error details. Inspect both the exception
                # and its string form to detect unique constraint violations.
                err = None
                try:
                    err = dict(db_exc)
                except Exception:
                    # Not a mapping-like exception
                    err = None

                exc_text = ''
                try:
                    exc_text = str(db_exc)
                except Exception:
                    exc_text = ''

                is_dup = False
                if err:
                    code = err.get('code')
                    msg = str(err.get('message', ''))
                    if code == '23505' or 'duplicate key' in msg.lower():
                        is_dup = True
                if not is_dup and ('23505' in exc_text or 'duplicate key' in exc_text.lower()):
                    is_dup = True

                if is_dup:
                    logger.warning(f"Signup conflict for {user_data.email}: {exc_text}")
                    # Return specific field information
                    detail_msg = 'Duplicate value for unique field'
                    if err and err.get('message'):
                        msg = str(err.get('message'))
                        if 'email' in msg.lower():
                            detail_msg = f"Email '{user_data.email}' is already registered"
                        elif 'username' in msg.lower():
                            detail_msg = f"Username '{user_data.username}' is already taken"
                        else:
                            detail_msg = msg
                    elif 'email' in exc_text.lower():
                        detail_msg = f"Email '{user_data.email}' is already registered"
                    elif 'username' in exc_text.lower():
                        detail_msg = f"Username '{user_data.username}' is already taken"
                    
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail_msg)
                # Re-raise for unknown DB errors so outer handler logs and returns 500
                raise

            logger.info(f"New user registered: {user.email}")

            # Ensure we get the integer DB id by querying our database if needed
            response_user_id = None
            if new_user_record and 'id' in new_user_record:
                response_user_id = new_user_record.get('id')
            if response_user_id is None:
                # Retry logic for database query (connection may be unstable)
                max_retries = 3
                retry_delay = 0.5
                for attempt in range(max_retries):
                    try:
                        from ..database import get_database
                        db = get_database()
                        async with db.get_session() as session_db:
                            from sqlalchemy import select
                            result_db = await session_db.execute(select(User).where(User.email == user.email))
                            db_user = result_db.scalar_one_or_none()
                            if db_user and getattr(db_user, 'id', None) is not None:
                                response_user_id = db_user.id
                                break  # Success, exit retry loop
                    except Exception as db_query_error:
                        if attempt < max_retries - 1:
                            logger.warning(f"Database query failed (attempt {attempt + 1}/{max_retries}), retrying: {db_query_error}")
                            await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        else:
                            logger.error(f"Database query failed after {max_retries} attempts: {db_query_error}")
                            response_user_id = None
            if response_user_id is None:
                # Final fallback to Supabase Auth UUID (may break downstream int cast)
                response_user_id = user.id
            response_created_at = new_user_record.get('created_at') if new_user_record and 'created_at' in new_user_record else getattr(user, 'created_at', None)

            # Check if user should get PRO tier (whitelist or admin) and set tier in database
            resolved_tier_value = "free"
            if response_user_id:
                try:
                    from ..database import get_database
                    from .auth_manager import should_get_pro_tier
                    db = get_database()
                    async with db.get_session() as session_db:
                        from sqlalchemy import select
                        result_db = await session_db.execute(select(User).where(User.id == response_user_id))
                        db_user = result_db.scalar_one_or_none()
                        if db_user:
                            if await should_get_pro_tier(user.email):
                                db_user.tier = UserTier.PRO
                                resolved_tier_value = "pro"
                                await session_db.commit()
                                logger.info(f"Set PRO tier for new user during signup: {user.email}")
                            elif db_user.tier is None:
                                db_user.tier = UserTier.FREE
                                resolved_tier_value = "free"
                                await session_db.commit()
                            else:
                                resolved_tier_value = db_user.tier.value if db_user.tier else "free"
                except Exception as tier_error:
                    logger.debug(f"Tier check during signup failed: {tier_error}")

            # Generate backend JWT tokens instead of using Supabase tokens
            # This ensures compatibility with backend authentication middleware
            auth_manager = await get_auth()
            
            # Create backend JWT tokens with tier information
            access_token = auth_manager.create_access_token(
                data={"sub": str(response_user_id), "email": user.email, "tier": resolved_tier_value}
            )
            refresh_token = auth_manager.create_refresh_token(
                data={"sub": str(response_user_id), "email": user.email}
            )

            # Get onboarding data from database if user exists
            onboarding_completed = False
            onboarding_data = None
            try:
                from ..database import get_database
                db = get_database()
                async with db.get_session() as session_db:
                    from sqlalchemy import select
                    result_db = await session_db.execute(select(User).where(User.id == response_user_id))
                    db_user = result_db.scalar_one_or_none()
                    if db_user:
                        onboarding_completed = getattr(db_user, 'onboarding_completed', False)
                        onboarding_data = getattr(db_user, 'onboarding_data', None)
            except Exception:
                pass
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600,  # 1 hour
                user={
                    "id": response_user_id,
                    "email": user.email,
                    "username": user_data.username,
                    "full_name": f"{user_data.first_name} {user_data.last_name}",
                    "tier": resolved_tier_value,
                    "is_active": True,
                    "is_verified": False,
                    "created_at": response_created_at,
                    "last_login": None,
                    "preferences": supabase_user_data,
                    "onboarding_completed": onboarding_completed,
                    "onboarding_data": onboarding_data
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@auth_router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLoginRequest):
    """User login endpoint using Supabase Auth"""
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        
        # Authenticate user with Supabase
        result = await supabase_auth_manager.signin(
            email=login_data.email,
            password=login_data.password
        )
        
        if result["success"]:
            user = result["user"]
            session = result["session"]
            
            # Get user data from database
            user_metadata = await supabase_auth_manager.get_user_metadata(user.id)

            # Resolve integer DB user id by email for token subject and ensure tier exists
            response_user_id = None
            resolved_tier_value = None
            is_admin_user = False
            onboarding_completed = False
            onboarding_data = None
            try:
                from ..database import get_database as _get_database
                from ..database.models import UserTier as _UserTier
                _db = _get_database()
                async with _db.get_session() as _session_db:
                    from sqlalchemy import select as _select
                    _res = await _session_db.execute(_select(User).where(User.email == user.email))
                    _db_user = _res.scalar_one_or_none()
                    if _db_user and getattr(_db_user, 'id', None) is not None:
                        response_user_id = _db_user.id
                        onboarding_completed = getattr(_db_user, 'onboarding_completed', False)
                        onboarding_data = getattr(_db_user, 'onboarding_data', None)
                        
                        # Check if user should get PRO tier (whitelist or admin)
                        from .auth_manager import should_get_pro_tier
                        if await should_get_pro_tier(user.email):
                            is_admin_user = True
                            if _db_user.tier != _UserTier.PRO:
                                _db_user.tier = _UserTier.PRO
                                await _session_db.commit()
                                logger.info(f"Set PRO tier for user: {user.email}")
                            resolved_tier_value = _UserTier.PRO.value
                        elif getattr(_db_user, 'tier', None) is None:
                            _db_user.tier = _UserTier.FREE
                            await _session_db.commit()
                            resolved_tier_value = _UserTier.FREE.value
                        else:
                            resolved_tier_value = _db_user.tier.value
            except Exception as e:
                logger.debug(f"User tier resolution error: {e}")
                response_user_id = None
                resolved_tier_value = None
            if response_user_id is None:
                response_user_id = user.id
            if not resolved_tier_value:
                resolved_tier_value = "pro" if is_admin_user else "free"
            
            # Update last login
            await supabase_auth_manager.update_user_metadata(user.id, {
                "last_login": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
            
            # Generate backend JWT tokens instead of using Supabase tokens
            # This ensures compatibility with backend authentication middleware
            auth_manager = await get_auth()
            
            # Create backend JWT tokens with tier information
            access_token = auth_manager.create_access_token(
                data={"sub": str(response_user_id), "email": user.email, "tier": resolved_tier_value}
            )
            refresh_token = auth_manager.create_refresh_token(
                data={"sub": str(response_user_id), "email": user.email}
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=3600,  # 1 hour
                user={
                    "id": response_user_id,
                    "email": user.email,
                    "username": user_metadata.get("username", "") if user_metadata else "",
                    "full_name": user_metadata.get("full_name", "") if user_metadata else "",
                    "tier": resolved_tier_value,
                    "is_active": user_metadata.get("is_active", True) if user_metadata else True,
                    "is_verified": user_metadata.get("is_verified", False) if user_metadata else False,
                    "created_at": user.created_at,
                    "last_login": datetime.utcnow().isoformat(),
                    "preferences": user_metadata.get("preferences", {}) if user_metadata else {},
                    "onboarding_completed": onboarding_completed,
                    "onboarding_data": onboarding_data
                }
            )
        else:
            logger.warning(f"Login failed for email: {login_data.email} - Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for email {login_data.email}: {str(e)}")
        logger.exception("Full login error traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@auth_router.post("/auth/refresh", response_model=Dict[str, str])
async def refresh_token(refresh_token: str):
    """Refresh access token endpoint"""
    try:
        auth_manager = await get_auth()
        tokens = await auth_manager.refresh_access_token(refresh_token)
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@auth_router.post("/auth/reset-password-request")
async def reset_password_request(reset_data: PasswordResetEmailRequest):
    """Request password reset endpoint"""
    try:
        auth_manager = await get_auth()
        success = await auth_manager.reset_password_request(reset_data.email)
        
        if success:
            return {"message": "Password reset email sent successfully"}
        else:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a password reset link has been sent"}
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset request"
        )

@auth_router.post("/auth/reset-password")
async def reset_password(reset_data: PasswordResetRequest):
    """Reset password using token endpoint"""
    try:
        auth_manager = await get_auth()
        success = await auth_manager.reset_password_with_token(reset_data.token, reset_data.new_password)
        
        if success:
            return {"success": True, "message": "Password reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
            
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset"
        )

@auth_router.post("/auth/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Change password endpoint"""
    try:
        auth_manager = await get_auth()
        success = await auth_manager.change_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password or new password doesn't meet requirements"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password change"
        )

@auth_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information including onboarding flags and tier."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        tier=(current_user.tier.value if current_user.tier else "free"),
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        preferences=getattr(current_user, "preferences", {}),
        onboarding_data=getattr(current_user, "onboarding_data", {}),
        onboarding_completed=getattr(current_user, "onboarding_completed", False),
        onboarding_completed_at=getattr(current_user, "onboarding_completed_at", None)
    )

@auth_router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout endpoint (client should discard tokens)"""
    # In a more advanced implementation, you might want to blacklist the token
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}

# Onboarding endpoints
@auth_router.post("/onboarding/save", response_model=OnboardingResponse)
async def save_onboarding_data(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save user onboarding data"""
    try:
        onboarding_dict = onboarding_data.dict() if hasattr(onboarding_data, 'dict') else onboarding_data
        current_user.onboarding_data = onboarding_dict
        current_user.onboarding_completed = True
        current_user.onboarding_completed_at = datetime.utcnow()
        
        # Extract website URL from onboarding data and save to User.website_url
        # Priority: profile.website > profile.business_website > business.businessWebsite
        website_url = ""
        if isinstance(onboarding_dict, dict):
            profile_data = onboarding_dict.get("profile", {})
            business_data = onboarding_dict.get("business", {})
            
            # Check profile.website first
            if profile_data.get("website"):
                website_url = profile_data.get("website")
            # Then profile.business_website
            elif profile_data.get("business_website"):
                website_url = profile_data.get("business_website")
            # Then business.businessWebsite
            elif business_data.get("businessWebsite"):
                website_url = business_data.get("businessWebsite")
        
        # Save website URL to User.website_url for easy agent access
        if website_url:
            current_user.website_url = website_url
        
        await db.commit()
        logger.info(f"Onboarding data saved for user: {current_user.email}, website_url: {website_url}")
        return OnboardingResponse(
            success=True,
            message="Onboarding data saved successfully",
            onboarding_data=onboarding_dict
        )
            
    except Exception as e:
        logger.error(f"Save onboarding data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during onboarding save"
        )

@auth_router.get("/onboarding/data", response_model=OnboardingResponse)
async def get_onboarding_data(current_user: User = Depends(get_current_active_user)):
    """Get user onboarding data"""
    try:
        return OnboardingResponse(
            success=True,
            message="Onboarding data retrieved successfully",
            onboarding_data=current_user.onboarding_data
        )
        
    except Exception as e:
        logger.error(f"Get onboarding data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during onboarding data retrieval"
        )

@auth_router.put("/onboarding/update", response_model=OnboardingResponse)
async def update_onboarding_data(
    onboarding_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user onboarding data - accepts both nested and flat structures"""
    try:
        # Handle both OnboardingData model and flat dict from account tab
        if hasattr(onboarding_data, 'dict'):
            onboarding_dict = onboarding_data.dict()
        elif isinstance(onboarding_data, dict):
            # If flat structure (from account tab), convert to nested structure
            if "profile" not in onboarding_data and "business" not in onboarding_data:
                # Convert flat structure to nested
                onboarding_dict = {
                    "profile": {
                        "full_name": onboarding_data.get("fullName"),
                        "company": onboarding_data.get("company"),
                        "job_title": onboarding_data.get("jobTitle"),
                        "location": onboarding_data.get("location"),
                        "website": onboarding_data.get("website"),
                        "timezone": onboarding_data.get("timezone"),
                        "language": onboarding_data.get("language"),
                        "bio": onboarding_data.get("bio"),
                    },
                    "business": {
                        "role": onboarding_data.get("role"),
                        "industry": onboarding_data.get("industry"),
                        "businessName": onboarding_data.get("businessName"),
                        "businessWebsite": onboarding_data.get("businessWebsite"),
                        "businessSize": onboarding_data.get("businessSize"),
                        "businessStage": onboarding_data.get("businessStage"),
                        "primaryGoals": onboarding_data.get("primaryGoals", []),
                        "mainPurpose": onboarding_data.get("mainPurpose"),
                    }
                }
            else:
                onboarding_dict = onboarding_data
        else:
            onboarding_dict = {}
        
        # Update user onboarding data
        current_user.onboarding_data = onboarding_dict
        current_user.onboarding_completed = True
        current_user.onboarding_completed_at = datetime.utcnow()
        
        # Extract website URL from onboarding data and save to User.website_url
        # Priority: profile.website > profile.business_website > business.businessWebsite
        website_url = ""
        if isinstance(onboarding_dict, dict):
            profile_data = onboarding_dict.get("profile", {})
            business_data = onboarding_dict.get("business", {})
            
            # Check profile.website first
            if profile_data.get("website"):
                website_url = profile_data.get("website")
            # Then profile.business_website
            elif profile_data.get("business_website"):
                website_url = profile_data.get("business_website")
            # Then business.businessWebsite
            elif business_data.get("businessWebsite"):
                website_url = business_data.get("businessWebsite")
        
        # Save website URL to User.website_url for easy agent access
        if website_url:
            current_user.website_url = website_url
        
        # Also update the metadata in Supabase Auth for consistency
        await supabase_auth_manager.update_user_metadata(current_user.id, {"onboarding_data": onboarding_dict, "onboarding_completed": True})

        await db.commit()
        
        logger.info(f"Onboarding data updated for user: {current_user.email}, website_url: {website_url}")
        
        return OnboardingResponse(
            success=True,
            message="Onboarding data updated successfully",
            onboarding_data=onboarding_dict
        )
            
    except Exception as e:
        logger.error(f"Update onboarding data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during onboarding update"
        )

# Billing endpoints
@auth_router.get("/billing/plans")
async def get_billing_plans_endpoint():
    """Get all available billing plans"""
    try:
        billing_plans_mgr = await get_billing_plans()
        return await billing_plans_mgr.get_all_plans()
    except Exception as e:
        logger.error(f"Get billing plans error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/billing/subscription")
async def get_user_subscription(current_user: User = Depends(get_current_active_user)):
    """Get current user's subscription details"""
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_user_subscription(current_user.id)
    except Exception as e:
        logger.error(f"Get user subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

class CreateSubscriptionRequest(BaseModel):
    tier: str
    payment_method: str = "paystack"
    billing_period: str = "monthly"

@auth_router.post("/billing/subscribe")
async def create_subscription(
    request: CreateSubscriptionRequest,
    response: Response = None,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new subscription for the current user"""
    try:
        billing_manager = await get_billing()
        billing_tier = BillingTier(request.tier)
        result = await billing_manager.create_subscription(
            current_user.id, 
            billing_tier, 
            request.payment_method,
            request.billing_period
        )

        # Update user tier in database
        from ..user_management.user_manager import UserManager
        user_manager = UserManager()
        user_tier = UserTier(request.tier)
        await user_manager.update_user_tier(current_user.id, user_tier)

        # Set a cookie so Next.js middleware and frontend see the updated tier immediately.
        try:
            if response is not None:
                # set cookie for 24 hours (or until you prefer)
                max_age = 24 * 60 * 60
                response.set_cookie(
                    key="user_tier",
                    value=user_tier.value,
                    max_age=max_age,
                    path="/",
                    samesite="lax"
                )
        except Exception:
            # Non-fatal: cookie setting failure should not block subscription creation
            logger.exception("Failed to set user_tier cookie on subscription creation")

        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid billing tier"
        )

@auth_router.post("/billing/choose-free")
async def choose_free_plan(
    response: Response = None,
    current_user: User = Depends(get_current_active_user)
):
    """Set the user's tier to FREE without payment (14-day trial logic can be applied elsewhere)."""
    try:
        from ..user_management.user_manager import UserManager
        user_manager = UserManager()
        await user_manager.update_user_tier(current_user.id, UserTier.FREE)

        # Optional cookie to reflect immediately on frontend
        try:
            if response is not None:
                max_age = 24 * 60 * 60
                response.set_cookie(
                    key="user_tier",
                    value=UserTier.FREE.value,
                    max_age=max_age,
                    path="/",
                    samesite="lax"
                )
        except Exception:
            logger.exception("Failed to set user_tier cookie on choose-free")

        # Also return a fresh access token embedding the updated tier claim
        try:
            auth_manager = await get_auth()
            new_access = auth_manager.create_access_token(
                data={"sub": str(current_user.id), "email": current_user.email, "tier": UserTier.FREE.value}
            )
            return {"success": True, "tier": UserTier.FREE.value, "access_token": new_access}
        except Exception:
            return {"success": True, "tier": UserTier.FREE.value}
    except Exception as e:
        logger.error(f"Choose free plan error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    except Exception as e:
        logger.error(f"Create subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/billing/cancel")
async def cancel_subscription(
    reason: str = "User requested cancellation",
    current_user: User = Depends(get_current_active_user)
):
    """Cancel the current user's subscription"""
    try:
        billing_manager = await get_billing()
        success = await billing_manager.cancel_subscription(current_user.id, reason)
        if success:
            return {"message": "Subscription cancelled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel subscription"
            )
    except Exception as e:
        logger.error(f"Cancel subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/billing/payment-history")
async def get_payment_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """Get payment history for the current user"""
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_payment_history(current_user.id, limit)
    except Exception as e:
        logger.error(f"Get payment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/billing/usage")
async def get_user_usage(current_user: User = Depends(get_current_active_user)):
    """Get current user's usage statistics"""
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_user_usage(current_user.id)
    except Exception as e:
        logger.error(f"Get user usage error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Admin billing endpoints
@auth_router.get("/admin/billing/revenue")
async def get_admin_revenue(current_user: User = Depends(get_current_active_user)):
    """Get revenue analytics (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_revenue_analytics()
    except Exception as e:
        logger.error(f"Get revenue analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/admin/billing/subscriptions")
async def get_admin_subscriptions(current_user: User = Depends(get_current_active_user)):
    """Get all subscriptions (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_all_subscriptions()
    except Exception as e:
        logger.error(f"Get admin subscriptions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/admin/billing/payments")
async def get_admin_payments(current_user: User = Depends(get_current_active_user)):
    """Get all payments (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        billing_manager = await get_billing()
        return await billing_manager.get_all_payments()
    except Exception as e:
        logger.error(f"Get admin payments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/admin/billing/activity")
async def get_admin_billing_activity(current_user: User = Depends(get_current_active_user)):
    """Get recent billing activity (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        billing_manager = await get_billing()
        # Get recent payment history as activity
        recent_payments = await billing_manager.get_recent_payment_activity()
        return {"activities": recent_payments}
    except Exception as e:
        logger.error(f"Get admin billing activity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/admin/billing/analytics")
async def get_admin_billing_analytics(current_user: User = Depends(get_current_active_user)):
    """Get comprehensive billing analytics (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        billing_manager = await get_billing()
        # Get comprehensive analytics including subscription stats
        subscription_stats = await billing_manager.get_subscription_statistics()
        usage_stats = await billing_manager.get_usage_statistics()
        
        return {
            "subscription_statistics": subscription_stats,
            "usage_statistics": usage_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get admin billing analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Admin endpoints for user management
@auth_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_active_user)):
    """Get all users (admin only)"""
    # Check if user has admin privileges
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            return {
                "users": [
                    {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "full_name": user.full_name,
                        "tier": user.tier.value,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at,
                        "last_login": user.last_login,
                        "onboarding_completed": user.onboarding_completed,
                        "onboarding_completed_at": user.onboarding_completed_at,
                        "onboarding_data": user.onboarding_data
                    }
                    for user in users
                ],
                "total": len(users),
                "active_users": len([u for u in users if u.is_active]),
                "verified_users": len([u for u in users if u.is_verified]),
                "onboarding_completed_users": len([u for u in users if u.onboarding_completed])
            }
            
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/admin/stats")
async def get_admin_stats(current_user: User = Depends(get_current_active_user)):
    """Get admin statistics (admin only)"""
    # Check if user has admin privileges
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, func
            from datetime import datetime, timedelta
            
            # Get total users
            total_users = await session.execute(select(func.count(User.id)))
            total_users = total_users.scalar()
            
            # Get active users
            active_users = await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = active_users.scalar()
            
            # Get users created in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_users = await session.execute(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
            new_users = new_users.scalar()
            
            # Get users by tier
            tier_stats = {}
            for tier in UserTier:
                count = await session.execute(
                    select(func.count(User.id)).where(User.tier == tier)
                )
                tier_stats[tier.value] = count.scalar()
            
            # Get onboarding statistics
            onboarding_completed_users = await session.execute(
                select(func.count(User.id)).where(User.onboarding_completed == True)
            )
            onboarding_completed_users = onboarding_completed_users.scalar()
            
            # Get onboarding completion rate
            onboarding_completion_rate = (onboarding_completed_users / total_users * 100) if total_users > 0 else 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_30_days": new_users,
                "tier_distribution": tier_stats,
                "verification_rate": (active_users / total_users * 100) if total_users > 0 else 0,
                "onboarding_completed_users": onboarding_completed_users,
                "onboarding_completion_rate": onboarding_completion_rate
            }
            
    except Exception as e:
        logger.error(f"Get admin stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Goals endpoints
@auth_router.get("/goals")
async def get_goals(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get goals with pagination and filtering (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        goals_response = await goal_manager.get_goals_paginated(page, limit, status)
        return goals_response
    except Exception as e:
        logger.error(f"Get goals error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/goals/{goal_id}")
async def get_goal_by_id(
    goal_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get goal by ID (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        goal = await goal_manager.get_goal_by_id(goal_id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get goal by ID error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.post("/goals")
async def create_goal(
    goal_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Create a new goal (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        goal = await goal_manager.create_goal(goal_data, current_user.email)
        return goal
    except Exception as e:
        logger.error(f"Create goal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.put("/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    goal_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Update a goal (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        goal = await goal_manager.update_goal(goal_id, goal_data, current_user.email)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update goal error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.put("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    progress_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Update goal progress (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        goal = await goal_manager.update_goal_progress(goal_id, progress_data, current_user.email)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update goal progress error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/goals/{goal_id}/progress")
async def get_goal_progress(
    goal_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get goal progress history (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        progress = await goal_manager.get_goal_progress(goal_id)
        return progress
    except Exception as e:
        logger.error(f"Get goal progress error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/goals/{goal_id}/activities")
async def get_goal_activities(
    goal_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get goal activities (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        activities = await goal_manager.get_goal_activities(goal_id)
        return activities
    except Exception as e:
        logger.error(f"Get goal activities error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/goals/templates")
async def get_goal_templates(
    current_user: User = Depends(get_current_active_user)
):
    """Get goal templates (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        templates = await goal_manager.get_goal_templates()
        return templates
    except Exception as e:
        logger.error(f"Get goal templates error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@auth_router.get("/goals/analytics")
async def get_goal_analytics(
    current_user: User = Depends(get_current_active_user)
):
    """Get goal analytics (admin only)"""
    if current_user.tier != UserTier.PRO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        goal_manager = await get_goal_manager()
        analytics = await goal_manager.get_goal_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Get goal analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Email Verification Endpoints
@auth_router.post("/auth/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: EmailVerificationRequest):
    """Verify user email using Gmail verification token"""
    try:
        logger.info(f"Email verification attempt with token: {request.token[:10]}...")
        
        # Initialize email verification manager if not already done
        if not email_verification_manager.gmail_service._initialized:
            await email_verification_manager.initialize()
        
        # Verify the token
        verification_result = await email_verification_manager.verify_email_token(request.token)
        
        if verification_result:
            user_id = verification_result["user_id"]
            email = verification_result["email"]
            username = verification_result["username"]
            full_name = verification_result["full_name"]
            
            # Send welcome email
            try:
                await email_verification_manager.send_welcome_email(
                    user_id=user_id,
                    email=email,
                    user_name=full_name
                )
            except Exception as email_error:
                logger.warning(f"Failed to send welcome email to {email}: {email_error}")
            
            logger.info(f"Email verified successfully for user {user_id} ({email})")
            
            return EmailVerificationResponse(
                success=True,
                message="Email verified successfully! Welcome to Agent47.",
                user_data={
                    "user_id": user_id,
                    "email": email,
                    "username": username,
                    "full_name": full_name,
                    "verified": True
                }
            )
        else:
            logger.warning(f"Email verification failed for token: {request.token[:10]}...")
            return EmailVerificationResponse(
                success=False,
                message="Invalid or expired verification token. Please request a new verification email."
            )
            
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during email verification"
        )

@auth_router.post("/auth/resend-verification", response_model=EmailVerificationResponse)
async def resend_verification_email(request: ResendVerificationRequest):
    """Resend verification email"""
    try:
        logger.info(f"Resend verification email request for: {request.email}")
        
        # Initialize email verification manager if not already done
        if not email_verification_manager.gmail_service._initialized:
            await email_verification_manager.initialize()
        
        # Find user by email
        db = get_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == request.email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists or not for security
                return EmailVerificationResponse(
                    success=True,
                    message="If the email exists and is not verified, a verification email has been sent."
                )
            
            if user.is_verified:
                return EmailVerificationResponse(
                    success=True,
                    message="This email is already verified."
                )
            
            # Resend verification email
            verification_sent = await email_verification_manager.resend_verification_email(
                user_id=user.id,
                email=user.email,
                user_name=user.full_name
            )
            
            if verification_sent:
                logger.info(f"Verification email resent to {request.email}")
                return EmailVerificationResponse(
                    success=True,
                    message="Verification email sent successfully. Please check your inbox."
                )
            else:
                logger.error(f"Failed to resend verification email to {request.email}")
                return EmailVerificationResponse(
                    success=False,
                    message="Failed to send verification email. Please try again later."
                )
                
    except Exception as e:
        logger.error(f"Resend verification email error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during verification email resend"
        )

@auth_router.get("/auth/verification-status")
async def get_verification_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get email verification status for current user"""
    try:
        # Initialize email verification manager if not already done
        if not email_verification_manager.gmail_service._initialized:
            await email_verification_manager.initialize()
        
        # Get verification status
        status = await email_verification_manager.get_verification_status(current_user.id)
        
        if status:
            return {
                "success": True,
                "verification_status": status
            }
        else:
            return {
                "success": False,
                "message": "Unable to retrieve verification status"
            }
            
    except Exception as e:
        logger.error(f"Get verification status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving verification status"
        )

@auth_router.post("/billing/webhook/paystack")
async def paystack_webhook(
    request: Request
):
    """Handle Paystack webhook callbacks"""
    try:
        from ..billing import get_billing
        
        # Get signature from header
        signature = request.headers.get("x-paystack-signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Paystack signature"
            )
        
        # Read request body
        body = await request.body()
        
        # Process webhook
        billing_manager = await get_billing()
        result = await billing_manager.handle_webhook(body, signature, "paystack")
        
        return result
    except Exception as e:
        logger.error(f"Paystack webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
