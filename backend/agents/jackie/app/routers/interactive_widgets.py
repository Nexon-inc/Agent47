from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.interactive_widgets_service import InteractiveWidgetsService

router = APIRouter(prefix="/interactive-widgets", tags=["Interactive Ad Widgets"])

@router.post("/create-widget")
async def create_interactive_widget(widget_type: str, widget_config: Dict[str, Any], ad_id: str):
    try:
        service = InteractiveWidgetsService()
        await service.initialize()
        return await service.create_interactive_widget(widget_type, widget_config, ad_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-poll")
async def create_ad_poll(poll_question: str, poll_options: List[str], ad_id: str):
    try:
        service = InteractiveWidgetsService()
        await service.initialize()
        return await service.create_ad_poll(poll_question, poll_options, ad_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-cta")
async def create_call_to_action(cta_text: str, cta_type: str, action_url: str, ad_id: str):
    try:
        service = InteractiveWidgetsService()
        await service.initialize()
        return await service.create_call_to_action(cta_text, cta_type, action_url, ad_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_widget_analytics(timeframe: str = "30d"):
    try:
        service = InteractiveWidgetsService()
        await service.initialize()
        return await service.get_widget_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
