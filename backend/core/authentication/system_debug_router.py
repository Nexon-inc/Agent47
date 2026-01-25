from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.future import select
from typing import List, Dict, Any
from ..database import get_database
from ..database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users(key: str):
    """Emergency endpoint to list users and debug attributes"""
    if key != "fix_my_app_2026":
        raise HTTPException(status_code=403, detail="Invalid access key")
    
    try:
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "username": u.username,
                    "tier": u.tier.value if u.tier else None,
                    "is_active": u.is_active,
                    "is_verified": u.is_verified
                }
                for u in users
            ]
    except Exception as e:
        logger.error(f"System user list error: {e}")
        return [{"error": str(e)}]

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, key: str):
    """Emergency endpoint to delete a broken user"""
    if key != "fix_my_app_2026":
        raise HTTPException(status_code=403, detail="Invalid access key")
        
    try:
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            await session.delete(user)
            await session.commit()
            return {"message": f"User {user_id} deleted"}
    except Exception as e:
        logger.error(f"System user delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
