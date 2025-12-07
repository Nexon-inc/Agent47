"""
Integration tests for Aria Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.aria.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestAriaAgent:
    """Integration tests for Aria Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/aria/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "aria" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_generate_caption_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful caption generation."""
        request_data = {
            "content": "Just launched our new product!",
            "platform": "instagram",
            "tone": "excited",
            "hashtags": True
        }
        
        with patch('backend.agents.aria.app.services.content_service.ContentService.generate_caption') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "caption": "🚀 Just launched our new product! #innovation #launch #excited",
                "hashtags": ["#innovation", "#launch", "#excited"]
            }
            
            response = await async_client.post(
                "/aria/content/generate-caption",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "caption" in data
            assert "hashtags" in data

    @pytest_asyncio.mark.asyncio
    async def test_generate_caption_failure(self, async_client: AsyncClient, mock_user_data):
        """Test caption generation failure."""
        request_data = {
            "content": "",
            "platform": "instagram",
            "tone": "excited"
        }
        
        response = await async_client.post(
            "/aria/content/generate-caption",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest_asyncio.mark.asyncio
    async def test_suggest_hashtags_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful hashtag suggestion."""
        request_data = {
            "content": "Amazing sunset at the beach",
            "platform": "instagram",
            "count": 10
        }
        
        with patch('backend.agents.aria.app.services.content_service.ContentService.suggest_hashtags') as mock_suggest:
            mock_suggest.return_value = {
                "success": True,
                "hashtags": ["#sunset", "#beach", "#nature", "#photography", "#amazing"]
            }
            
            response = await async_client.post(
                "/aria/content/suggest-hashtags",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "hashtags" in data
            assert len(data["hashtags"]) > 0

    @pytest_asyncio.mark.asyncio
    async def test_chat_message_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful chat message processing."""
        request_data = {
            "message": "Help me create a social media strategy",
            "context": "business_owner"
        }
        
        with patch('backend.agents.aria.app.services.aria_chat_service.AriaChatService.process_chat_message') as mock_process:
            mock_process.return_value = {
                "success": True,
                "response": "I'd be happy to help you create a social media strategy! Let me start by understanding your business goals.",
                "intent": "strategy_creation",
                "suggestions": ["Define your target audience", "Choose your platforms", "Create content calendar"]
            }
            
            response = await async_client.post(
                "/aria/chat/message",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data
            assert "intent" in data

    @pytest_asyncio.mark.asyncio
    async def test_account_analysis_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful account analysis."""
        request_data = {
            "platform": "instagram",
            "username": "test_account",
            "analysis_type": "performance"
        }
        
        with patch('backend.agents.aria.app.services.account_analysis_service.AccountAnalysisService.analyze_account') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analysis": {
                    "followers": 1000,
                    "engagement_rate": 0.05,
                    "top_posts": ["post1", "post2", "post3"],
                    "recommendations": ["Post more consistently", "Use more hashtags"]
                }
            }
            
            response = await async_client.post(
                "/aria/analytics/account-analysis",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analysis" in data

    @pytest_asyncio.mark.asyncio
    async def test_generate_image_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful image generation."""
        request_data = {
            "prompt": "A modern tech startup office",
            "style": "professional",
            "size": "1024x1024"
        }
        
        with patch('backend.agents.aria.app.services.media_service.MediaService.generate_image') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "image_url": "https://example.com/generated-image.jpg",
                "model_used": "juggernautxl"
            }
            
            response = await async_client.post(
                "/aria/media/generate-image",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "image_url" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "content": "Test content",
            "platform": "instagram"
        }
        
        response = await async_client.post(
            "/aria/content/generate-caption",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_json_request(self, async_client: AsyncClient):
        """Test handling of invalid JSON requests."""
        response = await async_client.post(
            "/aria/content/generate-caption",
            data="invalid json",
            headers={"Content-Type": "application/json", "Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """Test handling of missing required fields."""
        request_data = {
            "platform": "instagram"
            # Missing required 'content' field
        }
        
        response = await async_client.post(
            "/aria/content/generate-caption",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_advanced_analytics_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful advanced analytics."""
        request_data = {
            "platform": "instagram",
            "timeframe": "30_days",
            "metrics": ["engagement_rate", "reach", "impressions"]
        }
        
        with patch('backend.agents.aria.app.services.advanced_analytics_service.AdvancedAnalyticsService.analyze_performance') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analytics": {
                    "engagement_rate": 0.05,
                    "reach": 50000,
                    "impressions": 100000,
                    "top_performing_posts": ["post1", "post2"],
                    "audience_insights": {
                        "age_groups": {"18-24": 0.4, "25-34": 0.35},
                        "locations": ["US", "UK", "Canada"]
                    }
                }
            }
            
            response = await async_client.post(
                "/aria/analytics/advanced",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analytics" in data

    @pytest_asyncio.mark.asyncio
    async def test_engagement_booster_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful engagement boosting."""
        request_data = {
            "content_id": "post_123",
            "platform": "instagram",
            "boost_type": "hashtag_optimization"
        }
        
        with patch('backend.agents.aria.app.services.engagement_booster_service.EngagementBoosterService.boost_engagement') as mock_boost:
            mock_boost.return_value = {
                "success": True,
                "suggestions": [
                    "Add trending hashtags: #viral, #trending",
                    "Post during peak hours: 6-8 PM",
                    "Use more visual content"
                ],
                "predicted_improvement": 0.25
            }
            
            response = await async_client.post(
                "/aria/engagement/boost",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "suggestions" in data

    @pytest_asyncio.mark.asyncio
    async def test_trend_alerts_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful trend alerts."""
        request_data = {
            "platform": "instagram",
            "keywords": ["sustainability", "tech"],
            "alert_frequency": "daily"
        }
        
        with patch('backend.agents.aria.app.services.trend_alerts_service.TrendAlertsService.create_alert') as mock_create:
            mock_create.return_value = {
                "success": True,
                "alert_id": "alert_123",
                "message": "New trending hashtag detected: #sustainabletech",
                "trend_data": {
                    "hashtag": "#sustainabletech",
                    "growth_rate": 0.45,
                    "related_keywords": ["green tech", "eco innovation"]
                }
            }
            
            response = await async_client.post(
                "/aria/trends/create-alert",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "alert_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_content_remix_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful content remixing."""
        request_data = {
            "original_content": "Check out our new product launch!",
            "target_platform": "twitter",
            "adaptation_style": "concise"
        }
        
        with patch('backend.agents.aria.app.services.content_remix_service.ContentRemixService.remix_content') as mock_remix:
            mock_remix.return_value = {
                "success": True,
                "remixed_content": "🚀 New product launch! Check it out 👀 #launch #innovation",
                "adaptations": {
                    "length_reduced": True,
                    "hashtags_added": True,
                    "emoji_added": True
                }
            }
            
            response = await async_client.post(
                "/aria/content/remix",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "remixed_content" in data

    @pytest_asyncio.mark.asyncio
    async def test_voice_posts_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful voice post processing."""
        request_data = {
            "audio_file": "base64_encoded_audio",
            "platform": "instagram",
            "enhancement_type": "transcription"
        }
        
        with patch('backend.agents.aria.app.services.voice_posts_service.VoicePostsService.process_voice_post') as mock_process:
            mock_process.return_value = {
                "success": True,
                "transcription": "Hey everyone, excited to share our latest update!",
                "enhanced_caption": "🎤 Hey everyone, excited to share our latest update! #voicepost #update",
                "hashtags": ["#voicepost", "#update", "#excited"]
            }
            
            response = await async_client.post(
                "/aria/voice/process",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transcription" in data

    @pytest_asyncio.mark.asyncio
    async def test_scheduling_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful content scheduling."""
        request_data = {
            "content": "Scheduled post content",
            "platform": "instagram",
            "scheduled_time": "2024-01-15T18:00:00Z",
            "timezone": "UTC"
        }
        
        with patch('backend.agents.aria.app.services.scheduling_service.SchedulingService.schedule_post') as mock_schedule:
            mock_schedule.return_value = {
                "success": True,
                "schedule_id": "schedule_123",
                "scheduled_time": "2024-01-15T18:00:00Z",
                "status": "scheduled"
            }
            
            response = await async_client.post(
                "/aria/scheduling/schedule",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "schedule_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_ab_testing_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful A/B testing."""
        request_data = {
            "test_name": "Caption A/B Test",
            "variants": [
                {"content": "Version A caption", "variant_id": "A"},
                {"content": "Version B caption", "variant_id": "B"}
            ],
            "test_duration_days": 7
        }
        
        with patch('backend.agents.aria.app.services.ab_testing_service.ABTestingService.create_test') as mock_create:
            mock_create.return_value = {
                "success": True,
                "test_id": "test_123",
                "status": "active",
                "variants": ["A", "B"],
                "expected_completion": "2024-01-22T00:00:00Z"
            }
            
            response = await async_client.post(
                "/aria/ab-testing/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "test_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_geo_campaign_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful geo-targeted campaign."""
        request_data = {
            "campaign_name": "Local Business Campaign",
            "target_locations": ["New York", "Los Angeles"],
            "content": "Local business promotion",
            "platform": "instagram"
        }
        
        with patch('backend.agents.aria.app.services.geo_campaign_service.GeoCampaignService.create_campaign') as mock_create:
            mock_create.return_value = {
                "success": True,
                "campaign_id": "campaign_123",
                "target_locations": ["New York", "Los Angeles"],
                "estimated_reach": 50000,
                "status": "active"
            }
            
            response = await async_client.post(
                "/aria/geo-campaign/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "campaign_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_rate_limiting(self, async_client: AsyncClient):
        """Test rate limiting functionality."""
        request_data = {
            "content": "Test content",
            "platform": "instagram"
        }
        
        # Make multiple requests quickly
        responses = []
        for _ in range(10):
            response = await async_client.post(
                "/aria/content/generate-caption",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            responses.append(response)
        
        # At least one should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited
