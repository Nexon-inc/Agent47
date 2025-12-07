"""
Integration tests for Clara Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.clara.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestClaraAgent:
    """Integration tests for Clara Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/clara/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "clara" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_chatbot_message_processing(self, async_client: AsyncClient, mock_user_data):
        """Test chatbot message processing."""
        request_data = {
            "message": "I need help with my account",
            "context": "customer_support",
            "user_id": "user123"
        }
        
        with patch('backend.agents.clara.app.services.chatbot_service.ChatbotService.process_message') as mock_process:
            mock_process.return_value = {
                "success": True,
                "response": "I'd be happy to help you with your account. What specific issue are you experiencing?",
                "intent": "account_help",
                "confidence": 0.95,
                "suggested_actions": ["Check account status", "Reset password"]
            }
            
            response = await async_client.post(
                "/clara/chatbot/message",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data
            assert "intent" in data

    @pytest_asyncio.mark.asyncio
    async def test_support_ticket_creation(self, async_client: AsyncClient, mock_user_data):
        """Test support ticket creation."""
        request_data = {
            "subject": "Account access issue",
            "description": "I cannot log into my account",
            "priority": "high",
            "category": "technical"
        }
        
        with patch('backend.agents.clara.app.services.support_service.SupportService.create_ticket') as mock_create:
            mock_create.return_value = {
                "success": True,
                "ticket_id": "TICKET-12345",
                "status": "open",
                "estimated_resolution": "24 hours"
            }
            
            response = await async_client.post(
                "/clara/support/create-ticket",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "ticket_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_voice_sentiment_analysis(self, async_client: AsyncClient, mock_user_data):
        """Test voice sentiment analysis."""
        request_data = {
            "audio_file": "base64_encoded_audio",
            "language": "en",
            "analysis_type": "sentiment"
        }
        
        with patch('backend.agents.clara.app.services.voice_service.VoiceService.analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "sentiment": "positive",
                "confidence": 0.85,
                "emotions": ["satisfaction", "happiness"],
                "transcript": "I'm very happy with the service"
            }
            
            response = await async_client.post(
                "/clara/voice/analyze-sentiment",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sentiment"] == "positive"

    @pytest_asyncio.mark.asyncio
    async def test_predictive_analytics(self, async_client: AsyncClient, mock_user_data):
        """Test predictive analytics functionality."""
        request_data = {
            "analysis_type": "customer_churn",
            "timeframe": "30_days",
            "data_source": "support_tickets"
        }
        
        with patch('backend.agents.clara.app.services.predictive_analytics_service.PredictiveAnalyticsService.analyze') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "predictions": {
                    "churn_probability": 0.15,
                    "at_risk_customers": 25,
                    "recommendations": ["Increase engagement", "Offer discounts"]
                }
            }
            
            response = await async_client.post(
                "/clara/analytics/predictive",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "predictions" in data

    @pytest_asyncio.mark.asyncio
    async def test_multilingual_support(self, async_client: AsyncClient, mock_user_data):
        """Test multilingual support functionality."""
        request_data = {
            "message": "Hola, necesito ayuda",
            "source_language": "es",
            "target_language": "en"
        }
        
        with patch('backend.agents.clara.app.services.multilingual_service.MultilingualService.translate_message') as mock_translate:
            mock_translate.return_value = {
                "success": True,
                "translated_message": "Hello, I need help",
                "confidence": 0.95
            }
            
            response = await async_client.post(
                "/clara/multilingual/translate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["translated_message"] == "Hello, I need help"

    @pytest_asyncio.mark.asyncio
    async def test_proactive_chat_engagement(self, async_client: AsyncClient, mock_user_data):
        """Test proactive chat engagement."""
        request_data = {
            "trigger_type": "page_visit",
            "page_url": "/pricing",
            "user_behavior": "high_intent"
        }
        
        with patch('backend.agents.clara.app.services.proactive_chat_service.ProactiveChatService.trigger_engagement') as mock_trigger:
            mock_trigger.return_value = {
                "success": True,
                "message": "Hi! I noticed you're looking at our pricing. Can I help you find the right plan?",
                "engagement_type": "proactive_offer"
            }
            
            response = await async_client.post(
                "/clara/proactive/trigger",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data

    @pytest_asyncio.mark.asyncio
    async def test_knowledge_base_search(self, async_client: AsyncClient, mock_user_data):
        """Test knowledge base search functionality."""
        request_data = {
            "query": "How do I reset my password?",
            "category": "account_management"
        }
        
        with patch('backend.agents.clara.app.services.knowledge_service.KnowledgeService.search') as mock_search:
            mock_search.return_value = {
                "success": True,
                "results": [
                    {
                        "title": "Password Reset Guide",
                        "content": "To reset your password, click on 'Forgot Password'...",
                        "relevance_score": 0.95
                    }
                ]
            }
            
            response = await async_client.post(
                "/clara/knowledge/search",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["results"]) > 0

    @pytest_asyncio.mark.asyncio
    async def test_crm_integration(self, async_client: AsyncClient, mock_user_data):
        """Test CRM integration functionality."""
        request_data = {
            "action": "create_contact",
            "contact_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            }
        }
        
        with patch('backend.agents.clara.app.services.crm_integration_service.CRMIntegrationService.sync_contact') as mock_sync:
            mock_sync.return_value = {
                "success": True,
                "contact_id": "CRM-12345",
                "sync_status": "completed"
            }
            
            response = await async_client.post(
                "/clara/crm/sync",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "contact_id" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "message": "Test message",
            "context": "support"
        }
        
        response = await async_client.post(
            "/clara/chatbot/message",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "message": "",  # Empty message
            "context": "support"
        }
        
        response = await async_client.post(
            "/clara/chatbot/message",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "message": "Test message",
            "context": "support"
        }
        
        with patch('backend.agents.clara.app.services.chatbot_service.ChatbotService.process_message') as mock_process:
            mock_process.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/clara/chatbot/message",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
