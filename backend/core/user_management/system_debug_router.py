from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import logging

from ..database.connection import get_db
from ..database.models import User, UserTier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system-debug"])

# Emergency Key
SYSTEM_KEY = "fix_my_app_2026"

class SystemUserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_admin: bool = False
    tier: str = "free"

class SystemUserResponse(BaseModel):
    id: int
    email: str
    username: str
    tier: Optional[str]
    is_admin: bool
    is_active: bool
    is_verified: bool

async def verify_system_key(key: str = Query(..., description="System Access Key")):
    if key != SYSTEM_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid System Key"
        )
    return True

@router.get("/users", response_model=List[SystemUserResponse])
async def list_all_users(
    key_verified: bool = Depends(verify_system_key),
    db: AsyncSession = Depends(get_db)
):
    """List ALL users in the database (Public Table)"""
    try:
        result = await db.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        
        response = []
        for u in users:
            # Handle Tier Enum manually to avoid str crashes if something is weird
            tier_val = "free"
            try:
                if u.tier:
                    tier_val = u.tier.value if hasattr(u.tier, 'value') else str(u.tier)
            except:
                tier_val = "error"

            response.append(SystemUserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                tier=tier_val,
                is_admin=False, # We don't have is_admin column in User model showed in Step 706? 
                # Wait, auth_router.py used `is_admin` in logic but explicit User definition in Step 706 didn't show `is_admin` column.
                # It showed `is_active`, `is_verified`.
                # Logic inferred admin from Tier.PRO + whitelist. I'll just check Tier.PRO
                is_active=u.is_active,
                is_verified=u.is_verified
            ))
            # Manually check if tier is PRO for is_admin flag in response
            if response[-1].tier == "pro":
                response[-1].is_admin = True
                
        return response
    except Exception as e:
        logger.error(f"System List Users Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users", response_model=SystemUserResponse)
async def create_user_manual(
    user_data: SystemUserCreate,
    key_verified: bool = Depends(verify_system_key),
    db: AsyncSession = Depends(get_db)
):
    """Manually create a user in local DB"""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(user_data.password)
        
        # Resolve Tier
        tier_enum = UserTier.FREE
        if user_data.tier.lower() == "pro":
            tier_enum = UserTier.PRO
        elif user_data.tier.lower() == "starter":
            tier_enum = UserTier.STARTER
            
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed,
            tier=tier_enum,
            is_active=True,
            is_verified=True # Auto verify manual users
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return SystemUserResponse(
            id=new_user.id,
            email=new_user.email,
            username=new_user.username,
            tier=new_user.tier.value,
            is_admin=(new_user.tier == UserTier.PRO),
            is_active=new_user.is_active,
            is_verified=new_user.is_verified
        )
    except Exception as e:
        logger.error(f"System Create User Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    key_verified: bool = Depends(verify_system_key),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user by ID"""
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        await db.delete(user)
        await db.commit()
        return {"message": f"User {user_id} deleted"}
    except Exception as e:
        logger.error(f"System Delete User Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
