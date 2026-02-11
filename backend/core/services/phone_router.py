"""
Phone Scraping & Calling Router
Handles phone number scraping and agent voice calls
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import logging
from pydantic import BaseModel

from ..authentication.auth_manager import get_current_active_user
from ..database.models import User
from .phone_scraping_service import get_phone_scraping_service
from .phone_calling_service import get_phone_calling_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/phone", tags=["phone"])

class ScrapeRequest(BaseModel):
    url: str

class GoogleMapsScrapeRequest(BaseModel):
    place_id: str

class CallRequest(BaseModel):
    phone_number: str
    agent_key: str
    message: str
    language: Optional[str] = None

@router.post("/scrape")
async def scrape_phone_numbers(
    request: ScrapeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Scrape phone numbers from a URL"""
    try:
        scraping_service = await get_phone_scraping_service()
        result = await scraping_service.scrape_from_url(
            url=request.url,
            user_id=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Scraping failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phone scraping failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phone scraping failed: {str(e)}"
        )

@router.post("/scrape/google-maps")
async def scrape_from_google_maps(
    request: GoogleMapsScrapeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Scrape phone number from Google Maps place"""
    try:
        scraping_service = await get_phone_scraping_service()
        result = await scraping_service.scrape_from_google_maps(
            place_id=request.place_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Google Maps scraping failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Maps scraping failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google Maps scraping failed: {str(e)}"
        )

@router.post("/call")
async def make_agent_call(
    request: CallRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Make a phone call with agent voice"""
    try:
        calling_service = await get_phone_calling_service()
        result = await calling_service.make_agent_call(
            phone_number=request.phone_number,
            agent_key=request.agent_key,
            message=request.message,
            user_id=current_user.id,
            language=request.language
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Call failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phone call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Phone call failed: {str(e)}"
        )

@router.get("/calls")
async def get_call_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user)
):
    """Get call history for user"""
    try:
        # Query call history from database
        from ..database import get_database
        db = get_database()
        async with db.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT call_sid, phone_number, agent_key, message, status, created_at
                    FROM phone_calls
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"user_id": current_user.id, "limit": limit}
            )
            calls = result.fetchall()
            
            return {
                "calls": [
                    {
                        "call_sid": call[0],
                        "phone_number": call[1],
                        "agent_key": call[2],
                        "message": call[3],
                        "status": call[4],
                        "created_at": call[5].isoformat() if call[5] else None
                    }
                    for call in calls
                ],
                "total": len(calls)
            }
            
    except Exception as e:
        logger.error(f"Failed to get call history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call history"
        )

@router.get("/calls/{call_sid}")
async def get_call_details(
    call_sid: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a specific call"""
    try:
        # Query call details from database
        from ..database import get_database
        db = get_database()
        async with db.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT call_sid, phone_number, agent_key, message, status, 
                           duration, recording_url, created_at, completed_at
                    FROM phone_calls
                    WHERE call_sid = :call_sid AND user_id = :user_id
                """),
                {"call_sid": call_sid, "user_id": current_user.id}
            )
            call = result.fetchone()
            
            if not call:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Call not found"
                )
            
            return {
                "call_sid": call[0],
                "phone_number": call[1],
                "agent_key": call[2],
                "message": call[3],
                "status": call[4],
                "duration": call[5],
                "recording_url": call[6],
                "created_at": call[7].isoformat() if call[7] else None,
                "completed_at": call[8].isoformat() if call[8] else None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call details"
        )

@router.post("/twiml")
async def twiml_webhook(
    request: Dict[str, Any]
):
    """Twilio webhook endpoint for TwiML responses"""
    try:
        # This endpoint returns TwiML for Twilio calls
        from fastapi.responses import Response
        
        message = request.get("message", "Hello, this is an automated call.")
        agent_key = request.get("agent_key", "clara")
        
        # Generate TwiML
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">{message}</Say>
</Response>"""
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"TwiML generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TwiML generation failed"
        )

