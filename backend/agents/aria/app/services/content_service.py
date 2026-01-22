from typing import Dict, Any, List, Optional
from core.ai import get_ai_service_manager, AIServiceManager
from core.storage.chroma_manager import get_chroma, ChromaDBManager
from core.integrations.integration_manager import get_integration_manager
from core.database.connection import get_supabase
from ..models import AriaBrandProfile


class ContentService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.chroma: Optional[ChromaDBManager] = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()
        self.chroma = await get_chroma()

    async def generate_caption(self, user_id: int, brief: Dict[str, Any]) -> Dict[str, Any]:
        context = await self._build_brand_context(user_id)
        tone = brief.get("tone", "brand-aligned")
        topic = brief.get("topic", "Generate a caption")
        
        # Build comprehensive prompt for social media caption generation
        system_prompt = f"""You are a professional social media content creator specializing in engaging, brand-aligned captions.

Brand Context:
- Tone: {tone}
- Constraints: {context.get('constraints', {})}
- Hashtags Policy: {context.get('hashtags_policy', [])}

Create compelling social media captions that:
1. Match the specified tone and brand voice
2. Follow all brand constraints and compliance rules
3. Include relevant hashtags based on the hashtag policy
4. Are engaging and encourage interaction
5. Are optimized for social media platforms"""
        
        user_prompt = f"Create a social media caption about: {topic}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        if result.success:
            return {
                "caption": result.text_content,
                "model": result.service_used,
                "fallback_used": result.fallback_used,
                "response_time_ms": result.response_time_ms
            }
        else:
            return {
                "caption": "",
                "error": result.error,
                "model": None
            }

    async def suggest_hashtags(self, user_id: int, topic: str, n: int = 10) -> List[str]:
        # Query Chroma hashtags_corpus; if empty, fallback to AI generation
        results = await self.chroma.similarity_search("hashtags_corpus", topic, n_results=n, threshold=0.9)
        if results:
            tags = []
            for r in results:
                doc = r.get("document", "")
                if doc.startswith("#"):
                    tags.append(doc)
            return tags[:n]
        
        # Fallback: try SEMrush via core integrations to fetch related terms, else AI
        try:
            mgr = await get_integration_manager()
            sem = await mgr.call_integration_api(user_id, "semrush", "/", "GET", params={"type": "phrase_related", "phrase": topic, "key": ""})
            candidates: List[str] = []
            data = sem.get("data")
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(k, str) and k.startswith("#"):
                        candidates.append(k)
            if candidates:
                return candidates[:n]
        except Exception:
            pass
        
        # Use AI service manager for hashtag generation
        system_prompt = f"""You are a social media hashtag expert. Generate {n} relevant, trending hashtags for the given topic.

Requirements:
- All hashtags must start with #
- Mix popular and niche hashtags
- Include trending and evergreen hashtags
- Ensure hashtags are relevant to the topic
- Return ONLY a JSON array of hashtag strings

Example format: ["#hashtag1", "#hashtag2", "#hashtag3"]"""
        
        user_prompt = f"Generate {n} relevant hashtags for: {topic}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.8
        )
        
        if result.success:
            try:
                import json
                arr = json.loads(result.text_content)
                hashtags = [t for t in arr if isinstance(t, str) and t.startswith("#")]
                return hashtags[:n]
            except Exception:
                # Fallback: extract hashtags from text
                import re
                hashtags = re.findall(r'#\w+', result.text_content)
                return hashtags[:n]
        else:
            # Last resort: return basic hashtags
            return [f"#{topic.replace(' ', '')}", f"#{topic.replace(' ', '_')}", "#socialmedia", "#content", "#marketing"][:n]

    async def _build_brand_context(self, user_id: int) -> Dict[str, Any]:
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            res = await session.execute(select(AriaBrandProfile).where(AriaBrandProfile.user_id == user_id))
            brand: Optional[AriaBrandProfile] = res.scalar_one_or_none()
            return {
                "voice": (brand.voice if brand and brand.voice else {}),
                "constraints": (brand.compliance_rules if brand and brand.compliance_rules else {}),
                "hashtags_policy": (brand.hashtags_bank if brand and brand.hashtags_bank else []),
            }


