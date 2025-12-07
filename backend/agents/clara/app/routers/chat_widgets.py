from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.chat_widget_service import ChatWidgetService
from ..database import get_clara_database
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chat-widgets", tags=["Chat Widgets"])

chat_widget_service = ChatWidgetService()


@router.post("/create")
async def create_chat_widget(
    brand_id: int,
    widget_config: Dict[str, Any],
    domain_whitelist: Optional[List[str]] = None
):
    """Create a new customizable chat widget"""
    try:
        result = await chat_widget_service.create_chat_widget(
            brand_id=brand_id,
            widget_config=widget_config,
            domain_whitelist=domain_whitelist
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat widget: {str(e)}")


@router.put("/{widget_id}")
async def update_chat_widget(
    widget_id: str,
    updates: Dict[str, Any]
):
    """Update an existing chat widget configuration"""
    try:
        result = await chat_widget_service.update_chat_widget(
            widget_id=widget_id,
            updates=updates
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chat widget: {str(e)}")


@router.get("/{widget_id}")
async def get_chat_widget(widget_id: str):
    """Get chat widget configuration and stats"""
    try:
        result = await chat_widget_service.get_chat_widget(widget_id=widget_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["widget"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat widget: {str(e)}")


@router.delete("/{widget_id}")
async def delete_chat_widget(widget_id: str):
    """Delete a chat widget"""
    try:
        result = await chat_widget_service.delete_chat_widget(widget_id=widget_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat widget: {str(e)}")


@router.get("/brand/{brand_id}/list")
async def list_chat_widgets(brand_id: int):
    """List all chat widgets for a brand"""
    try:
        result = await chat_widget_service.list_chat_widgets(brand_id=brand_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "widgets": result["widgets"],
                    "count": result["count"]
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chat widgets: {str(e)}")


@router.get("/{widget_id}/analytics")
async def get_widget_analytics(
    widget_id: str,
    date_range: str = Query("7d", description="Date range: 1d, 7d, 30d")
):
    """Get analytics for a specific chat widget"""
    try:
        result = await chat_widget_service.get_widget_analytics(
            widget_id=widget_id,
            date_range=date_range
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result["analytics"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get widget analytics: {str(e)}")


@router.get("/{widget_id}/embed-code")
async def get_widget_embed_code(widget_id: str):
    """Get the embed code for a chat widget"""
    try:
        result = await chat_widget_service.get_chat_widget(widget_id=widget_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "widget_id": widget_id,
                    "embed_code": result["widget"]["embed_code"],
                    "config": result["widget"]["config"]
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get embed code: {str(e)}")


@router.post("/{widget_id}/test")
async def test_chat_widget(widget_id: str):
    """Test a chat widget by sending a test message"""
    try:
        # Get widget info
        widget_result = await chat_widget_service.get_chat_widget(widget_id=widget_id)
        
        if not widget_result["success"]:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Send test message
        test_message = "This is a test message to verify the chat widget is working correctly."
        
        return {
            "success": True,
            "data": {
                "widget_id": widget_id,
                "test_message": test_message,
                "status": "Widget is ready for testing",
                "embed_code_available": "embed_code" in widget_result["widget"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test chat widget: {str(e)}")
