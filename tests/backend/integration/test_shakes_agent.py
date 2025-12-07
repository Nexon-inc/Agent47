"""
Integration tests for Shakes Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.shakes.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestShakesAgent:
    """Integration tests for Shakes Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/shakes/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "shakes" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_content_generation(self, async_client: AsyncClient, mock_user_data):
        """Test content generation functionality."""
        request_data = {
            "content_type": "blog_post",
            "topic": "The Future of AI in Marketing",
            "target_audience": "marketing_professionals",
            "tone": "professional",
            "length": "medium",
            "keywords": ["AI", "marketing", "automation", "future"]
        }
        
        with patch('backend.agents.shakes.app.services.content_generation_service.ContentGenerationService.generate_content') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "content": {
                    "title": "The Future of AI in Marketing: Transforming Customer Engagement",
                    "body": """
                    Artificial Intelligence is revolutionizing the marketing landscape, offering unprecedented opportunities for personalization and automation. As we look toward the future, AI-powered marketing tools are becoming essential for businesses seeking to stay competitive.

                    The integration of AI in marketing strategies enables companies to analyze vast amounts of customer data, predict consumer behavior, and deliver highly targeted campaigns. From chatbots that provide instant customer support to predictive analytics that forecast market trends, AI is reshaping how brands connect with their audiences.

                    Key trends driving this transformation include:
                    - Personalized customer experiences at scale
                    - Automated content creation and optimization
                    - Predictive customer journey mapping
                    - Real-time campaign performance analysis

                    As we move forward, businesses that embrace AI-driven marketing will gain significant competitive advantages in understanding and engaging their target markets.
                    """,
                    "meta_description": "Discover how AI is transforming marketing with personalized experiences, automated content, and predictive analytics.",
                    "tags": ["AI", "marketing", "automation", "future", "technology"],
                    "word_count": 150,
                    "readability_score": 8.5
                }
            }
            
            response = await async_client.post(
                "/shakes/content/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "content" in data

    @pytest_asyncio.mark.asyncio
    async def test_seo_optimization(self, async_client: AsyncClient, mock_user_data):
        """Test SEO optimization functionality."""
        request_data = {
            "content": "Our new AI-powered marketing platform helps businesses automate their campaigns and improve customer engagement.",
            "target_keywords": ["AI marketing", "marketing automation", "customer engagement"],
            "optimization_goals": ["search_ranking", "click_through_rate", "user_engagement"]
        }
        
        with patch('backend.agents.shakes.app.services.seo_optimization_service.SEOOptimizationService.optimize_content') as mock_optimize:
            mock_optimize.return_value = {
                "success": True,
                "optimized_content": {
                    "original_content": "Our new AI-powered marketing platform helps businesses automate their campaigns and improve customer engagement.",
                    "optimized_content": "Our innovative AI-powered marketing automation platform empowers businesses to streamline campaign management and dramatically enhance customer engagement strategies.",
                    "improvements": [
                        "Added 'innovative' for better appeal",
                        "Changed 'helps' to 'empowers' for stronger action",
                        "Added 'dramatically' for impact",
                        "Included 'strategies' for better keyword density"
                    ],
                    "seo_score": 85,
                    "keyword_density": {
                        "AI marketing": 0.02,
                        "marketing automation": 0.03,
                        "customer engagement": 0.02
                    },
                    "readability_score": 7.5
                }
            }
            
            response = await async_client.post(
                "/shakes/seo/optimize",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "optimized_content" in data

    @pytest_asyncio.mark.asyncio
    async def test_campaign_creation(self, async_client: AsyncClient, mock_user_data):
        """Test campaign creation functionality."""
        request_data = {
            "campaign_type": "email_marketing",
            "campaign_name": "AI Marketing Platform Launch",
            "target_audience": "marketing_managers",
            "campaign_goals": ["awareness", "lead_generation", "conversion"],
            "budget": 10000,
            "duration": "30_days"
        }
        
        with patch('backend.agents.shakes.app.services.campaign_creation_service.CampaignCreationService.create_campaign') as mock_create:
            mock_create.return_value = {
                "success": True,
                "campaign": {
                    "campaign_id": "CAMP-12345",
                    "campaign_name": "AI Marketing Platform Launch",
                    "strategy": {
                        "email_sequence": [
                            {
                                "day": 1,
                                "subject": "Revolutionize Your Marketing with AI",
                                "content": "Discover how AI can transform your marketing strategy...",
                                "goal": "awareness"
                            },
                            {
                                "day": 7,
                                "subject": "See AI Marketing in Action",
                                "content": "Watch our demo and see the power of AI marketing...",
                                "goal": "engagement"
                            }
                        ],
                        "social_media_posts": [
                            {
                                "platform": "linkedin",
                                "content": "AI is changing marketing forever. Here's how...",
                                "hashtags": ["#AIMarketing", "#MarketingAutomation"]
                            }
                        ]
                    },
                    "expected_metrics": {
                        "open_rate": 0.25,
                        "click_through_rate": 0.05,
                        "conversion_rate": 0.02
                    }
                }
            }
            
            response = await async_client.post(
                "/shakes/campaigns/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "campaign" in data

    @pytest_asyncio.mark.asyncio
    async def test_brand_voice_development(self, async_client: AsyncClient, mock_user_data):
        """Test brand voice development functionality."""
        request_data = {
            "brand_name": "TechFlow Solutions",
            "industry": "technology",
            "target_audience": "enterprise_decision_makers",
            "brand_values": ["innovation", "reliability", "expertise"],
            "personality_traits": ["professional", "approachable", "authoritative"]
        }
        
        with patch('backend.agents.shakes.app.services.brand_voice_service.BrandVoiceService.develop_voice') as mock_develop:
            mock_develop.return_value = {
                "success": True,
                "brand_voice": {
                    "voice_characteristics": {
                        "tone": "Professional yet approachable",
                        "style": "Clear and concise",
                        "personality": "Expert and trustworthy",
                        "language_level": "Intermediate to advanced"
                    },
                    "voice_guidelines": [
                        "Use active voice whenever possible",
                        "Avoid jargon unless necessary for clarity",
                        "Include data and evidence to support claims",
                        "Maintain a confident but not arrogant tone"
                    ],
                    "example_content": {
                        "headline": "Transform Your Business with Cutting-Edge AI Solutions",
                        "body": "At TechFlow Solutions, we understand that enterprise success requires more than just technology—it demands innovation, reliability, and expertise. Our AI-powered solutions are designed to streamline your operations while maintaining the highest standards of security and performance."
                    },
                    "do_and_dont": {
                        "do": [
                            "Use specific examples and case studies",
                            "Address customer pain points directly",
                            "Provide clear value propositions"
                        ],
                        "dont": [
                            "Use overly technical language",
                            "Make unsubstantiated claims",
                            "Use passive voice excessively"
                        ]
                    }
                }
            }
            
            response = await async_client.post(
                "/shakes/brand-voice/develop",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "brand_voice" in data

    @pytest_asyncio.mark.asyncio
    async def test_content_calendar_creation(self, async_client: AsyncClient, mock_user_data):
        """Test content calendar creation functionality."""
        request_data = {
            "calendar_type": "monthly",
            "content_themes": ["AI innovation", "customer success", "industry insights"],
            "channels": ["blog", "social_media", "email"],
            "target_audience": "tech_professionals",
            "content_frequency": "daily"
        }
        
        with patch('backend.agents.shakes.app.services.content_calendar_service.ContentCalendarService.create_calendar') as mock_create:
            mock_create.return_value = {
                "success": True,
                "content_calendar": {
                    "calendar_id": "CAL-12345",
                    "schedule": [
                        {
                            "date": "2024-01-01",
                            "theme": "AI innovation",
                            "content": {
                                "blog": "The Future of AI in Business",
                                "social_media": "AI trends to watch in 2024",
                                "email": "Monthly AI insights newsletter"
                            }
                        },
                        {
                            "date": "2024-01-02",
                            "theme": "customer success",
                            "content": {
                                "blog": "Customer Success Story: TechCorp",
                                "social_media": "How our clients achieve success",
                                "email": "Customer spotlight"
                            }
                        }
                    ],
                    "content_ideas": [
                        "AI implementation best practices",
                        "Industry trend analysis",
                        "Customer case studies",
                        "Product feature highlights"
                    ]
                }
            }
            
            response = await async_client.post(
                "/shakes/calendar/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "content_calendar" in data

    @pytest_asyncio.mark.asyncio
    async def test_social_media_management(self, async_client: AsyncClient, mock_user_data):
        """Test social media management functionality."""
        request_data = {
            "platforms": ["linkedin", "twitter", "facebook"],
            "content_type": "thought_leadership",
            "posting_schedule": "daily",
            "engagement_goals": ["likes", "shares", "comments"],
            "hashtag_strategy": "trending_and_niche"
        }
        
        with patch('backend.agents.shakes.app.services.social_media_service.SocialMediaService.manage_content') as mock_manage:
            mock_manage.return_value = {
                "success": True,
                "social_media_plan": {
                    "platform_strategies": {
                        "linkedin": {
                            "content_focus": "Professional insights and industry news",
                            "posting_frequency": "3 times per week",
                            "optimal_times": ["9 AM", "1 PM", "5 PM"],
                            "hashtags": ["#AI", "#Technology", "#Innovation"]
                        },
                        "twitter": {
                            "content_focus": "Quick insights and industry updates",
                            "posting_frequency": "Daily",
                            "optimal_times": ["8 AM", "12 PM", "6 PM"],
                            "hashtags": ["#AI", "#Tech", "#Marketing"]
                        }
                    },
                    "content_calendar": [
                        {
                            "date": "2024-01-01",
                            "platform": "linkedin",
                            "content": "The AI revolution in marketing is just beginning. Here's what businesses need to know...",
                            "hashtags": ["#AIMarketing", "#Innovation", "#Business"]
                        }
                    ],
                    "engagement_strategy": {
                        "response_time": "within_2_hours",
                        "engagement_goals": "increase_by_25%",
                        "community_building": "focus_on_thought_leadership"
                    }
                }
            }
            
            response = await async_client.post(
                "/shakes/social-media/manage",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "social_media_plan" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "content_type": "blog_post",
            "topic": "AI in marketing",
            "target_audience": "professionals"
        }
        
        response = await async_client.post(
            "/shakes/content/generate",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "content_type": "",  # Empty content type
            "topic": "",  # Empty topic
            "target_audience": "invalid_audience"
        }
        
        response = await async_client.post(
            "/shakes/content/generate",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "content_type": "blog_post",
            "topic": "AI in marketing",
            "target_audience": "professionals"
        }
        
        with patch('backend.agents.shakes.app.services.content_generation_service.ContentGenerationService.generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/shakes/content/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
