from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.ethical_ad_scanner_service import EthicalAdScannerService

router = APIRouter(prefix="/ethical-ad-scanner", tags=["Ethical Ad Scanner"])

@router.post("/scan-ad-content")
async def scan_ad_content(ad_content: str, ad_type: str = "general", platform: str = "all"):
    try:
        service = EthicalAdScannerService()
        await service.initialize()
        return await service.scan_ad_content(ad_content, ad_type, platform)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-compliance")
async def check_compliance(ad_data: Dict[str, Any], compliance_rules: List[str]):
    try:
        service = EthicalAdScannerService()
        await service.initialize()
        return await service.check_compliance(ad_data, compliance_rules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/flag-violations")
async def flag_violations(ad_id: str, violation_type: str, violation_details: Dict[str, Any]):
    try:
        service = EthicalAdScannerService()
        await service.initialize()
        return await service.flag_violations(ad_id, violation_type, violation_details)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_ethical_scanner_analytics(timeframe: str = "30d"):
    try:
        service = EthicalAdScannerService()
        await service.initialize()
        return await service.get_ethical_scanner_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
