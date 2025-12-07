from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.authentication.auth_manager import get_current_user
from backend.core.database.models import User
from backend.core.database.connection import get_supabase
from ..models import AccountGroup


router = APIRouter(prefix="/aria/groups", tags=["aria:groups"])


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("")
async def create_group(payload: GroupCreate, current_user: User = Depends(get_current_user)):
    db = await get_supabase()
    async with db.get_session() as session:
        grp = AccountGroup(user_id=current_user.id, name=payload.name, description=payload.description)
        session.add(grp)
        await session.commit()
        return {"id": grp.id}


@router.get("")
async def list_groups(current_user: User = Depends(get_current_user)):
    db = await get_supabase()
    async with db.get_session() as session:
        from sqlalchemy import select
        res = await session.execute(select(AccountGroup).where(AccountGroup.user_id == current_user.id))
        return [{"id": g.id, "name": g.name, "description": g.description} for g in res.scalars().all()]


