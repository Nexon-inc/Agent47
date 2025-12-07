"""
Integration tests for Eric Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.eric.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestEricAgent:
    """Integration tests for Eric Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/eric/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "eric" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_sales_pitch_generation(self, async_client: AsyncClient, mock_user_data):
        """Test sales pitch generation."""
        request_data = {
            "lead_info": "Tech startup, 50 employees, looking for automation",
            "pitch_type": "cold_email",
            "tone": "professional",
            "product_focus": "ai_agents"
        }
        
        with patch('backend.agents.eric.app.services.sales_outreach_service.SalesOutreachService.generate_pitch') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "pitch": {
                    "subject": "Transform Your Business with AI Agents",
                    "opening": "Hi [Name], I noticed your company is growing rapidly...",
                    "value_proposition": "Our AI agents can increase your productivity by 300%",
                    "call_to_action": "Schedule a demo to see how this can work for you",
                    "follow_up": "I'll follow up in 3 days if I don't hear back"
                }
            }
            
            response = await async_client.post(
                "/eric/sales/generate-pitch",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "pitch" in data

    @pytest_asyncio.mark.asyncio
    async def test_lead_scoring(self, async_client: AsyncClient, mock_user_data):
        """Test lead scoring functionality."""
        request_data = {
            "lead_data": {
                "company_name": "TechCorp Inc",
                "industry": "technology",
                "company_size": "50-100",
                "website": "https://techcorp.com",
                "contact_info": {
                    "email": "ceo@techcorp.com",
                    "phone": "+1234567890"
                }
            }
        }
        
        with patch('backend.agents.eric.app.services.lead_scoring_service.LeadScoringService.score_lead') as mock_score:
            mock_score.return_value = {
                "success": True,
                "lead_score": 85,
                "scoring_factors": {
                    "company_size": 20,
                    "industry_match": 25,
                    "contact_quality": 20,
                    "website_quality": 20
                },
                "recommendations": ["High priority lead", "Schedule demo immediately"]
            }
            
            response = await async_client.post(
                "/eric/leads/score",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["lead_score"] == 85

    @pytest_asyncio.mark.asyncio
    async def test_customer_insights_analysis(self, async_client: AsyncClient, mock_user_data):
        """Test customer insights analysis."""
        request_data = {
            "analysis_type": "behavior_patterns",
            "timeframe": "30_days",
            "customer_segment": "enterprise"
        }
        
        with patch('backend.agents.eric.app.services.customer_insights_service.CustomerInsightsService.analyze') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "insights": {
                    "engagement_trends": "Increasing",
                    "preferred_channels": ["email", "phone"],
                    "pain_points": ["integration complexity", "training needs"],
                    "upsell_opportunities": ["premium features", "additional agents"]
                }
            }
            
            response = await async_client.post(
                "/eric/insights/analyze",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "insights" in data

    @pytest_asyncio.mark.asyncio
    async def test_sales_forecasting(self, async_client: AsyncClient, mock_user_data):
        """Test sales forecasting functionality."""
        request_data = {
            "forecast_period": "90_days",
            "forecast_type": "revenue",
            "include_factors": ["seasonality", "market_trends", "pipeline_health"]
        }
        
        with patch('backend.agents.eric.app.services.sales_forecasting_service.SalesForecastingService.generate_forecast') as mock_forecast:
            mock_forecast.return_value = {
                "success": True,
                "forecast": {
                    "predicted_revenue": 150000,
                    "confidence_level": 0.85,
                    "monthly_breakdown": {
                        "month_1": 45000,
                        "month_2": 52000,
                        "month_3": 53000
                    },
                    "key_assumptions": ["Current pipeline conversion", "Market growth rate"]
                }
            }
            
            response = await async_client.post(
                "/eric/forecasting/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "forecast" in data

    @pytest_asyncio.mark.asyncio
    async def test_deal_closing_assistance(self, async_client: AsyncClient, mock_user_data):
        """Test deal closing assistance."""
        request_data = {
            "deal_id": "DEAL-12345",
            "deal_stage": "negotiation",
            "customer_concerns": ["pricing", "implementation timeline"],
            "deal_value": 50000
        }
        
        with patch('backend.agents.eric.app.services.deal_closing_assistance_service.DealClosingAssistanceService.assist_closing') as mock_assist:
            mock_assist.return_value = {
                "success": True,
                "recommendations": [
                    "Offer flexible payment terms",
                    "Provide implementation timeline",
                    "Schedule technical demo"
                ],
                "next_steps": ["Send proposal", "Schedule follow-up call"],
                "closing_probability": 0.75
            }
            
            response = await async_client.post(
                "/eric/deals/assist-closing",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "recommendations" in data

    @pytest_asyncio.mark.asyncio
    async def test_cross_selling_opportunities(self, async_client: AsyncClient, mock_user_data):
        """Test cross-selling opportunity identification."""
        request_data = {
            "customer_id": "CUST-12345",
            "current_products": ["aria", "clara"],
            "customer_usage_data": {
                "monthly_usage": "high",
                "feature_adoption": "advanced"
            }
        }
        
        with patch('backend.agents.eric.app.services.cross_selling_service.CrossSellingService.identify_opportunities') as mock_identify:
            mock_identify.return_value = {
                "success": True,
                "opportunities": [
                    {
                        "product": "eric",
                        "reason": "Sales automation needs",
                        "probability": 0.80,
                        "estimated_value": 25000
                    },
                    {
                        "product": "joe",
                        "reason": "Research capabilities",
                        "probability": 0.65,
                        "estimated_value": 15000
                    }
                ]
            }
            
            response = await async_client.post(
                "/eric/cross-selling/identify",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["opportunities"]) > 0

    @pytest_asyncio.mark.asyncio
    async def test_email_sequence_creation(self, async_client: AsyncClient, mock_user_data):
        """Test email sequence creation."""
        request_data = {
            "sequence_type": "nurture",
            "target_audience": "enterprise_leads",
            "sequence_length": 5,
            "goals": ["awareness", "consideration", "decision"]
        }
        
        with patch('backend.agents.eric.app.services.email_sequences_service.EmailSequencesService.create_sequence') as mock_create:
            mock_create.return_value = {
                "success": True,
                "sequence": {
                    "sequence_id": "SEQ-12345",
                    "emails": [
                        {
                            "day": 1,
                            "subject": "Welcome to AI-Powered Sales",
                            "content": "Hi [Name], welcome to the future of sales..."
                        },
                        {
                            "day": 3,
                            "subject": "How AI Agents Transform Sales",
                            "content": "Let me show you how our AI agents..."
                        }
                    ]
                }
            }
            
            response = await async_client.post(
                "/eric/email-sequences/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "sequence" in data

    @pytest_asyncio.mark.asyncio
    async def test_live_chat_support(self, async_client: AsyncClient, mock_user_data):
        """Test live chat support functionality."""
        request_data = {
            "customer_message": "I'm interested in your sales automation tools",
            "customer_context": {
                "company": "TechCorp",
                "role": "Sales Manager",
                "previous_interactions": 2
            }
        }
        
        with patch('backend.agents.eric.app.services.live_chat_service.LiveChatService.process_message') as mock_process:
            mock_process.return_value = {
                "success": True,
                "response": "Great! I'd love to show you how our AI agents can automate your sales process. What's your current sales volume?",
                "suggested_actions": ["Schedule demo", "Send case study", "Connect with sales rep"],
                "intent": "sales_inquiry"
            }
            
            response = await async_client.post(
                "/eric/live-chat/message",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data

    @pytest_asyncio.mark.asyncio
    async def test_performance_analytics(self, async_client: AsyncClient, mock_user_data):
        """Test performance analytics functionality."""
        request_data = {
            "analytics_type": "sales_performance",
            "timeframe": "30_days",
            "metrics": ["conversion_rate", "deal_velocity", "pipeline_health"]
        }
        
        with patch('backend.agents.eric.app.services.performance_analytics_service.PerformanceAnalyticsService.analyze') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analytics": {
                    "conversion_rate": 0.25,
                    "average_deal_velocity": 45,
                    "pipeline_health_score": 0.80,
                    "top_performing_channels": ["email", "phone"],
                    "recommendations": ["Focus on email outreach", "Improve follow-up timing"]
                }
            }
            
            response = await async_client.post(
                "/eric/analytics/performance",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analytics" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "lead_info": "Test lead",
            "pitch_type": "cold_email"
        }
        
        response = await async_client.post(
            "/eric/sales/generate-pitch",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "lead_info": "",  # Empty lead info
            "pitch_type": "invalid_type"
        }
        
        response = await async_client.post(
            "/eric/sales/generate-pitch",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "lead_info": "Test lead",
            "pitch_type": "cold_email"
        }
        
        with patch('backend.agents.eric.app.services.sales_outreach_service.SalesOutreachService.generate_pitch') as mock_generate:
            mock_generate.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/eric/sales/generate-pitch",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
