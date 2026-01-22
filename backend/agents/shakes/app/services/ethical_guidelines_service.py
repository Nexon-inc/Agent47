import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class EthicalGuidelinesService:
    """Service for ethical content guidelines and compliance"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.2
        }
    
    async def initialize(self):
        """Initialize ethical guidelines service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Ethical guidelines service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ethical guidelines service: {e}")
            raise
    
    async def check_content_ethics(
        self,
        content_piece_id: int,
        ethical_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Check content for ethical compliance"""
        if not self._initialized:
            await self.initialize()
        
        if ethical_categories is None:
            ethical_categories = ["accuracy", "bias", "privacy", "accessibility", "inclusivity", "transparency"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Perform ethical analysis
                ethical_analysis = await self._analyze_content_ethics(
                    content_piece, ethical_categories
                )
                
                # Generate ethical recommendations
                recommendations_prompt = self._create_ethical_recommendations_prompt(
                    content_piece, ethical_analysis, ethical_categories
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides ethical content recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                ethical_recommendations = ai_response.text_content if ai_response.success else ""
                
                # Calculate ethical score
                ethical_score = self._calculate_ethical_score(ethical_analysis)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "ethical_categories": ethical_categories,
                    "ethical_analysis": ethical_analysis,
                    "ethical_recommendations": ethical_recommendations,
                    "ethical_score": ethical_score,
                    "compliance_status": "compliant" if ethical_score >= 0.8 else "needs_review",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content ethics check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_ethical_guidelines(
        self,
        industry: str,
        content_type: str,
        target_audience: str,
        regulatory_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Generate ethical guidelines for specific context"""
        if not self._initialized:
            await self.initialize()
        
        if regulatory_requirements is None:
            regulatory_requirements = ["GDPR", "CCPA", "ADA", "FTC"]
        
        try:
            # Generate industry-specific guidelines
            guidelines_prompt = self._create_guidelines_prompt(
                industry, content_type, target_audience, regulatory_requirements
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            
            # Generate ethical guidelines
            messages = [{"role": "system", "content": "You are an AI assistant that creates ethical content guidelines."}, {"role": "user", "content": guidelines_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
            ethical_guidelines = ai_response.text_content if ai_response.success else ""
            
            # Generate compliance checklist
            checklist_prompt = self._create_compliance_checklist_prompt(
                industry, content_type, regulatory_requirements
            )
            messages = [{"role": "system", "content": "You are an AI assistant that creates compliance checklists."}, {"role": "user", "content": checklist_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
            compliance_checklist = ai_response.text_content if ai_response.success else ""
            
            # Generate best practices
            best_practices_prompt = self._create_best_practices_prompt(
                industry, content_type, target_audience
            )
            messages = [{"role": "system", "content": "You are an AI assistant that creates ethical best practices."}, {"role": "user", "content": best_practices_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
            best_practices = ai_response.text_content if ai_response.success else ""
            
            return {
                "success": True,
                "industry": industry,
                "content_type": content_type,
                "target_audience": target_audience,
                "regulatory_requirements": regulatory_requirements,
                "ethical_guidelines": ethical_guidelines,
                "compliance_checklist": compliance_checklist,
                "best_practices": best_practices,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ethical guidelines generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def audit_content_bias(
        self,
        content_piece_id: int,
        bias_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Audit content for bias and inclusivity issues"""
        if not self._initialized:
            await self.initialize()
        
        if bias_categories is None:
            bias_categories = ["gender", "race", "age", "religion", "socioeconomic", "cultural"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Perform bias analysis
                bias_analysis = await self._analyze_content_bias(
                    content_piece, bias_categories
                )
                
                # Generate bias mitigation recommendations
                mitigation_prompt = self._create_bias_mitigation_prompt(
                    content_piece, bias_analysis, bias_categories
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides bias mitigation strategies."}, {"role": "user", "content": mitigation_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                bias_mitigation = ai_response.text_content if ai_response.success else ""
                
                # Calculate bias score
                bias_score = self._calculate_bias_score(bias_analysis)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "bias_categories": bias_categories,
                    "bias_analysis": bias_analysis,
                    "bias_mitigation": bias_mitigation,
                    "bias_score": bias_score,
                    "bias_status": "inclusive" if bias_score >= 0.8 else "needs_review",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content bias audit failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_accessibility_compliance(
        self,
        content_piece_id: int,
        accessibility_standards: List[str] = None
    ) -> Dict[str, Any]:
        """Check content for accessibility compliance"""
        if not self._initialized:
            await self.initialize()
        
        if accessibility_standards is None:
            accessibility_standards = ["WCAG_2.1", "ADA", "Section_508"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Perform accessibility analysis
                accessibility_analysis = await self._analyze_accessibility(
                    content_piece, accessibility_standards
                )
                
                # Generate accessibility improvements
                improvements_prompt = self._create_accessibility_improvements_prompt(
                    content_piece, accessibility_analysis, accessibility_standards
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides accessibility improvements."}, {"role": "user", "content": improvements_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                accessibility_improvements = ai_response.text_content if ai_response.success else ""
                
                # Calculate accessibility score
                accessibility_score = self._calculate_accessibility_score(accessibility_analysis)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "accessibility_standards": accessibility_standards,
                    "accessibility_analysis": accessibility_analysis,
                    "accessibility_improvements": accessibility_improvements,
                    "accessibility_score": accessibility_score,
                    "compliance_status": "compliant" if accessibility_score >= 0.8 else "needs_improvement",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Accessibility compliance check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_content_accuracy(
        self,
        content_piece_id: int,
        accuracy_categories: List[str] = None
    ) -> Dict[str, Any]:
        """Validate content for accuracy and fact-checking"""
        if not self._initialized:
            await self.initialize()
        
        if accuracy_categories is None:
            accuracy_categories = ["facts", "statistics", "claims", "sources", "quotes"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Perform accuracy analysis
                accuracy_analysis = await self._analyze_content_accuracy(
                    content_piece, accuracy_categories
                )
                
                # Generate accuracy recommendations
                recommendations_prompt = self._create_accuracy_recommendations_prompt(
                    content_piece, accuracy_analysis, accuracy_categories
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that provides accuracy recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.3)
                accuracy_recommendations = ai_response.text_content if ai_response.success else ""
                
                # Calculate accuracy score
                accuracy_score = self._calculate_accuracy_score(accuracy_analysis)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "accuracy_categories": accuracy_categories,
                    "accuracy_analysis": accuracy_analysis,
                    "accuracy_recommendations": accuracy_recommendations,
                    "accuracy_score": accuracy_score,
                    "accuracy_status": "accurate" if accuracy_score >= 0.8 else "needs_verification",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content accuracy validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_content_ethics(
        self, content_piece: ShakesContentPiece, ethical_categories: List[str]
    ) -> Dict[str, Any]:
        """Analyze content for ethical compliance"""
        analysis_prompt = self._create_ethics_analysis_prompt(
            content_piece, ethical_categories
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes content for ethical compliance. Respond in JSON format."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.3)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "categories_analyzed": ethical_categories,
            "analysis_result": analysis_result,
            "potential_issues": self._extract_ethical_issues(analysis_result),
            "compliance_level": self._assess_compliance_level(analysis_result)
        }
    
    async def _analyze_content_bias(
        self, content_piece: ShakesContentPiece, bias_categories: List[str]
    ) -> Dict[str, Any]:
        """Analyze content for bias"""
        bias_prompt = self._create_bias_analysis_prompt(
            content_piece, bias_categories
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that detects bias in content. Respond in JSON format."}, {"role": "user", "content": bias_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
        bias_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "categories_analyzed": bias_categories,
            "bias_analysis": bias_result,
            "potential_bias_issues": self._extract_bias_issues(bias_result),
            "inclusivity_level": self._assess_inclusivity_level(bias_result)
        }
    
    async def _analyze_accessibility(
        self, content_piece: ShakesContentPiece, accessibility_standards: List[str]
    ) -> Dict[str, Any]:
        """Analyze content for accessibility"""
        accessibility_prompt = self._create_accessibility_analysis_prompt(
            content_piece, accessibility_standards
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes content accessibility. Respond in JSON format."}, {"role": "user", "content": accessibility_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
        accessibility_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "standards_analyzed": accessibility_standards,
            "accessibility_analysis": accessibility_result,
            "accessibility_issues": self._extract_accessibility_issues(accessibility_result),
            "compliance_level": self._assess_accessibility_compliance(accessibility_result)
        }
    
    async def _analyze_content_accuracy(
        self, content_piece: ShakesContentPiece, accuracy_categories: List[str]
    ) -> Dict[str, Any]:
        """Analyze content for accuracy"""
        accuracy_prompt = self._create_accuracy_analysis_prompt(
            content_piece, accuracy_categories
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that verifies content accuracy. Respond in JSON format."}, {"role": "user", "content": accuracy_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.3)
        accuracy_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "categories_analyzed": accuracy_categories,
            "accuracy_analysis": accuracy_result,
            "accuracy_issues": self._extract_accuracy_issues(accuracy_result),
            "accuracy_level": self._assess_accuracy_level(accuracy_result)
        }
    
    def _calculate_ethical_score(self, ethical_analysis: Dict[str, Any]) -> float:
        """Calculate overall ethical score"""
        # Simple scoring based on analysis keywords
        positive_indicators = ["compliant", "ethical", "appropriate", "inclusive", "accurate"]
        negative_indicators = ["non-compliant", "unethical", "inappropriate", "biased", "inaccurate"]
        
        analysis_text = ethical_analysis.get("analysis_result", "").lower()
        positive_count = sum(1 for indicator in positive_indicators if indicator in analysis_text)
        negative_count = sum(1 for indicator in negative_indicators if indicator in analysis_text)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral score
        
        score = positive_count / (positive_count + negative_count)
        return round(score, 3)
    
    def _calculate_bias_score(self, bias_analysis: Dict[str, Any]) -> float:
        """Calculate bias score"""
        # Simple scoring based on bias analysis
        inclusive_indicators = ["inclusive", "diverse", "unbiased", "neutral", "representative"]
        biased_indicators = ["biased", "exclusive", "discriminatory", "stereotypical", "prejudiced"]
        
        analysis_text = bias_analysis.get("bias_analysis", "").lower()
        inclusive_count = sum(1 for indicator in inclusive_indicators if indicator in analysis_text)
        biased_count = sum(1 for indicator in biased_indicators if indicator in analysis_text)
        
        if inclusive_count + biased_count == 0:
            return 0.5  # Neutral score
        
        score = inclusive_count / (inclusive_count + biased_count)
        return round(score, 3)
    
    def _calculate_accessibility_score(self, accessibility_analysis: Dict[str, Any]) -> float:
        """Calculate accessibility score"""
        # Simple scoring based on accessibility analysis
        accessible_indicators = ["accessible", "compliant", "inclusive", "readable", "navigable"]
        inaccessible_indicators = ["inaccessible", "non-compliant", "exclusive", "unreadable", "navigable"]
        
        analysis_text = accessibility_analysis.get("accessibility_analysis", "").lower()
        accessible_count = sum(1 for indicator in accessible_indicators if indicator in analysis_text)
        inaccessible_count = sum(1 for indicator in inaccessible_indicators if indicator in analysis_text)
        
        if accessible_count + inaccessible_count == 0:
            return 0.5  # Neutral score
        
        score = accessible_count / (accessible_count + inaccessible_count)
        return round(score, 3)
    
    def _calculate_accuracy_score(self, accuracy_analysis: Dict[str, Any]) -> float:
        """Calculate accuracy score"""
        # Simple scoring based on accuracy analysis
        accurate_indicators = ["accurate", "verified", "factual", "reliable", "correct"]
        inaccurate_indicators = ["inaccurate", "unverified", "factual", "unreliable", "incorrect"]
        
        analysis_text = accuracy_analysis.get("accuracy_analysis", "").lower()
        accurate_count = sum(1 for indicator in accurate_indicators if indicator in analysis_text)
        inaccurate_count = sum(1 for indicator in inaccurate_indicators if indicator in analysis_text)
        
        if accurate_count + inaccurate_count == 0:
            return 0.5  # Neutral score
        
        score = accurate_count / (accurate_count + inaccurate_count)
        return round(score, 3)
    
    def _extract_ethical_issues(self, analysis_result: str) -> List[str]:
        """Extract ethical issues from analysis"""
        issues = []
        if "bias" in analysis_result.lower():
            issues.append("Potential bias detected")
        if "inaccurate" in analysis_result.lower():
            issues.append("Accuracy concerns")
        if "inaccessible" in analysis_result.lower():
            issues.append("Accessibility issues")
        if "misleading" in analysis_result.lower():
            issues.append("Misleading content")
        return issues
    
    def _extract_bias_issues(self, analysis_result: str) -> List[str]:
        """Extract bias issues from analysis"""
        issues = []
        if "gender bias" in analysis_result.lower():
            issues.append("Gender bias detected")
        if "racial bias" in analysis_result.lower():
            issues.append("Racial bias detected")
        if "cultural bias" in analysis_result.lower():
            issues.append("Cultural bias detected")
        if "stereotypical" in analysis_result.lower():
            issues.append("Stereotypical content")
        return issues
    
    def _extract_accessibility_issues(self, analysis_result: str) -> List[str]:
        """Extract accessibility issues from analysis"""
        issues = []
        if "alt text" in analysis_result.lower():
            issues.append("Missing alt text")
        if "color contrast" in analysis_result.lower():
            issues.append("Color contrast issues")
        if "readability" in analysis_result.lower():
            issues.append("Readability concerns")
        if "navigation" in analysis_result.lower():
            issues.append("Navigation issues")
        return issues
    
    def _extract_accuracy_issues(self, analysis_result: str) -> List[str]:
        """Extract accuracy issues from analysis"""
        issues = []
        if "unverified" in analysis_result.lower():
            issues.append("Unverified claims")
        if "outdated" in analysis_result.lower():
            issues.append("Outdated information")
        if "misleading" in analysis_result.lower():
            issues.append("Misleading statements")
        if "factual" in analysis_result.lower():
            issues.append("Factual errors")
        return issues
    
    def _assess_compliance_level(self, analysis_result: str) -> str:
        """Assess overall compliance level"""
        if "compliant" in analysis_result.lower():
            return "high"
        elif "needs review" in analysis_result.lower():
            return "medium"
        else:
            return "low"
    
    def _assess_inclusivity_level(self, analysis_result: str) -> str:
        """Assess inclusivity level"""
        if "inclusive" in analysis_result.lower():
            return "high"
        elif "needs improvement" in analysis_result.lower():
            return "medium"
        else:
            return "low"
    
    def _assess_accessibility_compliance(self, analysis_result: str) -> str:
        """Assess accessibility compliance"""
        if "compliant" in analysis_result.lower():
            return "high"
        elif "needs improvement" in analysis_result.lower():
            return "medium"
        else:
            return "low"
    
    def _assess_accuracy_level(self, analysis_result: str) -> str:
        """Assess accuracy level"""
        if "accurate" in analysis_result.lower():
            return "high"
        elif "needs verification" in analysis_result.lower():
            return "medium"
        else:
            return "low"
    
    def _create_ethics_analysis_prompt(
        self, content_piece: ShakesContentPiece, ethical_categories: List[str]
    ) -> str:
        """Create prompt for ethics analysis"""
        return f"""
        Analyze this content for ethical compliance:
        
        Content: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        
        Content Text: {content_piece.content}
        
        Ethical Categories: {', '.join(ethical_categories)}
        
        Evaluate:
        1. Accuracy and truthfulness
        2. Bias and inclusivity
        3. Privacy and data protection
        4. Accessibility compliance
        5. Transparency and disclosure
        6. Harm prevention
        
        Format as comprehensive ethical analysis.
        """
    
    def _create_bias_analysis_prompt(
        self, content_piece: ShakesContentPiece, bias_categories: List[str]
    ) -> str:
        """Create prompt for bias analysis"""
        return f"""
        Analyze this content for bias and inclusivity:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        
        Bias Categories: {', '.join(bias_categories)}
        
        Evaluate:
        1. Gender representation and bias
        2. Racial and ethnic bias
        3. Age-related bias
        4. Religious bias
        5. Socioeconomic bias
        6. Cultural bias and stereotypes
        
        Format as comprehensive bias analysis.
        """
    
    def _create_accessibility_analysis_prompt(
        self, content_piece: ShakesContentPiece, accessibility_standards: List[str]
    ) -> str:
        """Create prompt for accessibility analysis"""
        return f"""
        Analyze this content for accessibility compliance:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        
        Accessibility Standards: {', '.join(accessibility_standards)}
        
        Evaluate:
        1. Readability and language clarity
        2. Color contrast and visual accessibility
        3. Alternative text for images
        4. Navigation and structure
        5. Screen reader compatibility
        6. Keyboard accessibility
        
        Format as comprehensive accessibility analysis.
        """
    
    def _create_accuracy_analysis_prompt(
        self, content_piece: ShakesContentPiece, accuracy_categories: List[str]
    ) -> str:
        """Create prompt for accuracy analysis"""
        return f"""
        Analyze this content for accuracy and fact-checking:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        
        Accuracy Categories: {', '.join(accuracy_categories)}
        
        Evaluate:
        1. Factual accuracy of claims
        2. Statistical accuracy
        3. Source verification
        4. Quote accuracy
        5. Date and time accuracy
        6. Misleading information
        
        Format as comprehensive accuracy analysis.
        """
    
    def _create_guidelines_prompt(
        self, industry: str, content_type: str, target_audience: str, regulatory_requirements: List[str]
    ) -> str:
        """Create prompt for ethical guidelines"""
        return f"""
        Create ethical guidelines for:
        
        Industry: {industry}
        Content Type: {content_type}
        Target Audience: {target_audience}
        Regulatory Requirements: {', '.join(regulatory_requirements)}
        
        Include:
        1. Industry-specific ethical standards
        2. Content accuracy requirements
        3. Bias and inclusivity guidelines
        4. Privacy and data protection
        5. Accessibility compliance
        6. Transparency and disclosure
        7. Harm prevention measures
        
        Format as comprehensive ethical guidelines.
        """
    
    def _create_compliance_checklist_prompt(
        self, industry: str, content_type: str, regulatory_requirements: List[str]
    ) -> str:
        """Create prompt for compliance checklist"""
        return f"""
        Create compliance checklist for:
        
        Industry: {industry}
        Content Type: {content_type}
        Regulatory Requirements: {', '.join(regulatory_requirements)}
        
        Include:
        1. Pre-publication checks
        2. Accuracy verification steps
        3. Bias and inclusivity review
        4. Accessibility compliance checks
        5. Privacy and data protection
        6. Regulatory compliance
        7. Post-publication monitoring
        
        Format as actionable compliance checklist.
        """
    
    def _create_best_practices_prompt(
        self, industry: str, content_type: str, target_audience: str
    ) -> str:
        """Create prompt for best practices"""
        return f"""
        Create ethical best practices for:
        
        Industry: {industry}
        Content Type: {content_type}
        Target Audience: {target_audience}
        
        Include:
        1. Content creation best practices
        2. Fact-checking procedures
        3. Bias prevention strategies
        4. Accessibility implementation
        5. Privacy protection measures
        6. Transparency practices
        7. Continuous improvement processes
        
        Format as comprehensive best practices guide.
        """
    
    def _create_ethical_recommendations_prompt(
        self, content_piece: ShakesContentPiece, ethical_analysis: Dict[str, Any], ethical_categories: List[str]
    ) -> str:
        """Create prompt for ethical recommendations"""
        return f"""
        Provide ethical recommendations for this content:
        
        Content: {content_piece.title}
        Ethical Analysis: {ethical_analysis}
        Categories: {', '.join(ethical_categories)}
        
        Provide:
        1. Specific improvement recommendations
        2. Bias mitigation strategies
        3. Accessibility enhancements
        4. Accuracy improvements
        5. Compliance actions
        6. Best practice implementations
        
        Format as actionable ethical recommendations.
        """
    
    def _create_bias_mitigation_prompt(
        self, content_piece: ShakesContentPiece, bias_analysis: Dict[str, Any], bias_categories: List[str]
    ) -> str:
        """Create prompt for bias mitigation"""
        return f"""
        Provide bias mitigation recommendations for this content:
        
        Content: {content_piece.title}
        Bias Analysis: {bias_analysis}
        Categories: {', '.join(bias_categories)}
        
        Provide:
        1. Specific bias reduction strategies
        2. Inclusivity improvements
        3. Language modifications
        4. Representation enhancements
        5. Stereotype elimination
        6. Diversity promotion
        
        Format as actionable bias mitigation recommendations.
        """
    
    def _create_accessibility_improvements_prompt(
        self, content_piece: ShakesContentPiece, accessibility_analysis: Dict[str, Any], accessibility_standards: List[str]
    ) -> str:
        """Create prompt for accessibility improvements"""
        return f"""
        Provide accessibility improvement recommendations for this content:
        
        Content: {content_piece.title}
        Accessibility Analysis: {accessibility_analysis}
        Standards: {', '.join(accessibility_standards)}
        
        Provide:
        1. Specific accessibility improvements
        2. Readability enhancements
        3. Visual accessibility fixes
        4. Navigation improvements
        5. Screen reader optimizations
        6. Compliance actions
        
        Format as actionable accessibility improvement recommendations.
        """
    
    def _create_accuracy_recommendations_prompt(
        self, content_piece: ShakesContentPiece, accuracy_analysis: Dict[str, Any], accuracy_categories: List[str]
    ) -> str:
        """Create prompt for accuracy recommendations"""
        return f"""
        Provide accuracy improvement recommendations for this content:
        
        Content: {content_piece.title}
        Accuracy Analysis: {accuracy_analysis}
        Categories: {', '.join(accuracy_categories)}
        
        Provide:
        1. Specific accuracy improvements
        2. Fact-checking recommendations
        3. Source verification steps
        4. Information updates needed
        5. Misleading content fixes
        6. Verification procedures
        
        Format as actionable accuracy improvement recommendations.
        """
