import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.utils.nlp_utils import NLPUtils
from core.cache.redis_manager import init_redis
from ..database import get_jackie_database
from ..models import EthicalAdScan, ComplianceCheck, AdViolation, EthicalGuideline

logger = logging.getLogger(__name__)

class EthicalAdScannerService:
    def __init__(self):
        self.db = None
        self.nlp_processor = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize ethical ad scanner service"""
        if self._initialized:
            return
        
        try:
            self.db = await get_jackie_database()
            self.nlp_processor = NLPUtils()
            await self.nlp_processor.initialize()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Ethical ad scanner service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ethical ad scanner service: {e}")
            raise
    
    async def scan_ad_content(self, ad_content: str, ad_type: str = "general", platform: str = "all") -> Dict[str, Any]:
        """Scan ad content for ethical compliance and potential violations"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                scan_id = str(uuid.uuid4())
                
                prompt = f"""
                Ad Content: {ad_content}
                Ad Type: {ad_type}
                Platform: {platform}
                
                Scan ad content for ethical compliance and potential violations.
                """
                
                scan_result = await self.nlp_processor.scan_ad_content(prompt)
                
                scan = EthicalAdScan(
                    id=scan_id, ad_content=ad_content, ad_type=ad_type, platform=platform,
                    scan_result=json.dumps(scan_result), created_at=datetime.utcnow()
                )
                session.add(scan)
                await session.commit()
                
                return {"scan_id": scan_id, "scan_result": scan_result}
        except Exception as e:
            logger.error(f"Failed to scan ad content: {e}")
            raise
    
    async def check_compliance(self, ad_data: Dict[str, Any], compliance_rules: List[str]) -> Dict[str, Any]:
        """Check ad compliance against specified rules and regulations"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                compliance_id = str(uuid.uuid4())
                
                prompt = f"""
                Ad Data: {ad_data}
                Compliance Rules: {compliance_rules}
                
                Check ad compliance against specified rules and regulations.
                """
                
                compliance_result = await self.nlp_processor.check_compliance(prompt)
                
                compliance = ComplianceCheck(
                    id=compliance_id, ad_data=json.dumps(ad_data), compliance_rules=json.dumps(compliance_rules),
                    compliance_result=json.dumps(compliance_result), created_at=datetime.utcnow()
                )
                session.add(compliance)
                await session.commit()
                
                return {"compliance_id": compliance_id, "compliance_result": compliance_result}
        except Exception as e:
            logger.error(f"Failed to check compliance: {e}")
            raise
    
    async def flag_violations(self, ad_id: str, violation_type: str, violation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Flag and document ad violations for review and correction"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                violation_id = str(uuid.uuid4())
                
                prompt = f"""
                Ad ID: {ad_id}
                Violation Type: {violation_type}
                Violation Details: {violation_details}
                
                Flag and document ad violations for review and correction.
                """
                
                violation_result = await self.nlp_processor.flag_violations(prompt)
                
                violation = AdViolation(
                    id=violation_id, ad_id=ad_id, violation_type=violation_type,
                    violation_details=json.dumps(violation_details), violation_result=json.dumps(violation_result),
                    created_at=datetime.utcnow()
                )
                session.add(violation)
                await session.commit()
                
                return {"violation_id": violation_id, "violation_result": violation_result}
        except Exception as e:
            logger.error(f"Failed to flag violations: {e}")
            raise
    
    async def get_ethical_scanner_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get ethical scanner analytics for specified timeframe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.db.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
                
                ads_scanned_query = select(func.count(EthicalAdScan.id)).where(EthicalAdScan.created_at >= cutoff_date)
                compliance_checks_query = select(func.count(ComplianceCheck.id)).where(ComplianceCheck.created_at >= cutoff_date)
                violations_flagged_query = select(func.count(AdViolation.id)).where(AdViolation.created_at >= cutoff_date)
                
                ads_scanned = await session.scalar(ads_scanned_query)
                compliance_checks = await session.scalar(compliance_checks_query)
                violations_flagged = await session.scalar(violations_flagged_query)
                
                return {
                    "timeframe": timeframe, "ads_scanned": ads_scanned,
                    "compliance_checks": compliance_checks, "violations_flagged": violations_flagged
                }
        except Exception as e:
            logger.error(f"Failed to get ethical scanner analytics: {e}")
            raise
