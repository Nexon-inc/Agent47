"""
Integration tests for Joe Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.joe.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestJoeAgent:
    """Integration tests for Joe Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/joe/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "joe" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_market_research_conduct(self, async_client: AsyncClient, mock_user_data):
        """Test market research functionality."""
        request_data = {
            "research_topic": "AI-powered customer service solutions",
            "research_scope": {
                "market_size": True,
                "competitors": True,
                "trends": True,
                "customer_needs": True
            },
            "target_audience": "enterprise_customers",
            "geographic_scope": "north_america"
        }
        
        with patch('backend.agents.joe.app.services.market_research_service.MarketResearchService.conduct_research') as mock_research:
            mock_research.return_value = {
                "success": True,
                "research_results": {
                    "market_size": {
                        "total_addressable_market": 5000000000,
                        "serviceable_addressable_market": 1000000000,
                        "growth_rate": 0.25
                    },
                    "competitors": [
                        {
                            "name": "Zendesk",
                            "market_share": 0.15,
                            "strengths": ["Established brand", "Large customer base"],
                            "weaknesses": ["Limited AI capabilities", "High pricing"]
                        }
                    ],
                    "trends": [
                        "AI integration in customer service",
                        "Omnichannel support",
                        "Self-service automation"
                    ],
                    "customer_needs": [
                        "Faster response times",
                        "24/7 availability",
                        "Multilingual support"
                    ]
                }
            }
            
            response = await async_client.post(
                "/joe/research/market",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "research_results" in data

    @pytest_asyncio.mark.asyncio
    async def test_competitor_analysis(self, async_client: AsyncClient, mock_user_data):
        """Test competitor analysis functionality."""
        request_data = {
            "competitors": ["Zendesk", "Intercom", "Freshdesk"],
            "analysis_type": "comprehensive",
            "focus_areas": ["pricing", "features", "market_position"]
        }
        
        with patch('backend.agents.joe.app.services.competitor_analysis_service.CompetitorAnalysisService.analyze_competitors') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "analysis_results": {
                    "competitor_profiles": [
                        {
                            "name": "Zendesk",
                            "pricing": {"starter": 19, "professional": 49, "enterprise": 99},
                            "key_features": ["Ticketing", "Live chat", "Knowledge base"],
                            "market_position": "Market leader",
                            "strengths": ["Brand recognition", "Feature completeness"],
                            "weaknesses": ["High cost", "Complex setup"]
                        }
                    ],
                    "competitive_landscape": {
                        "market_leaders": ["Zendesk", "Intercom"],
                        "emerging_players": ["Freshdesk", "Help Scout"],
                        "market_gaps": ["AI-powered automation", "Industry-specific solutions"]
                    }
                }
            }
            
            response = await async_client.post(
                "/joe/analysis/competitors",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analysis_results" in data

    @pytest_asyncio.mark.asyncio
    async def test_keyword_research(self, async_client: AsyncClient, mock_user_data):
        """Test keyword research functionality."""
        request_data = {
            "seed_keywords": ["customer service software", "help desk", "support ticket"],
            "research_depth": "comprehensive",
            "target_region": "united_states",
            "competitor_analysis": True
        }
        
        with patch('backend.agents.joe.app.services.keyword_research_service.KeywordResearchService.research_keywords') as mock_research:
            mock_research.return_value = {
                "success": True,
                "keyword_results": {
                    "primary_keywords": [
                        {
                            "keyword": "customer service software",
                            "search_volume": 12000,
                            "competition": "high",
                            "cpc": 2.50,
                            "difficulty": 75
                        }
                    ],
                    "long_tail_keywords": [
                        {
                            "keyword": "best customer service software for small business",
                            "search_volume": 800,
                            "competition": "medium",
                            "cpc": 1.80,
                            "difficulty": 45
                        }
                    ],
                    "competitor_keywords": [
                        {
                            "competitor": "Zendesk",
                            "top_keywords": ["help desk software", "customer support platform"]
                        }
                    ]
                }
            }
            
            response = await async_client.post(
                "/joe/research/keywords",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "keyword_results" in data

    @pytest_asyncio.mark.asyncio
    async def test_consumer_behavior_analysis(self, async_client: AsyncClient, mock_user_data):
        """Test consumer behavior analysis."""
        request_data = {
            "analysis_type": "purchase_behavior",
            "target_demographic": "enterprise_decision_makers",
            "data_sources": ["surveys", "web_analytics", "social_media"],
            "timeframe": "6_months"
        }
        
        with patch('backend.agents.joe.app.services.consumer_behavior_service.ConsumerBehaviorService.analyze_behavior') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "behavior_analysis": {
                    "purchase_patterns": {
                        "decision_factors": ["price", "features", "support quality", "integration"],
                        "decision_timeline": "average_3_months",
                        "influencers": ["industry_reports", "peer_recommendations", "demos"]
                    },
                    "pain_points": [
                        "Complex implementation",
                        "High costs",
                        "Limited customization",
                        "Poor customer support"
                    ],
                    "preferences": {
                        "communication_channels": ["email", "phone", "video_calls"],
                        "information_sources": ["vendor_websites", "reviews", "demos"],
                        "pricing_preferences": ["transparent_pricing", "flexible_plans"]
                    }
                }
            }
            
            response = await async_client.post(
                "/joe/analysis/consumer-behavior",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "behavior_analysis" in data

    @pytest_asyncio.mark.asyncio
    async def test_market_trend_analysis(self, async_client: AsyncClient, mock_user_data):
        """Test market trend analysis."""
        request_data = {
            "industry": "customer_service_software",
            "trend_analysis_type": "emerging_trends",
            "timeframe": "12_months",
            "geographic_scope": "global"
        }
        
        with patch('backend.agents.joe.app.services.market_trend_analysis_service.MarketTrendAnalysisService.analyze_trends') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "trend_analysis": {
                    "emerging_trends": [
                        {
                            "trend": "AI-powered customer service",
                            "growth_rate": 0.35,
                            "adoption_rate": 0.15,
                            "impact_level": "high",
                            "description": "Integration of AI and machine learning in customer service platforms"
                        }
                    ],
                    "market_drivers": [
                        "Remote work adoption",
                        "Customer expectations for instant support",
                        "Cost reduction pressures"
                    ],
                    "future_predictions": {
                        "next_6_months": ["Increased AI adoption", "Focus on omnichannel"],
                        "next_12_months": ["Industry consolidation", "New AI features"],
                        "next_24_months": ["Voice AI integration", "Predictive analytics"]
                    }
                }
            }
            
            response = await async_client.post(
                "/joe/analysis/market-trends",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "trend_analysis" in data

    @pytest_asyncio.mark.asyncio
    async def test_survey_creation(self, async_client: AsyncClient, mock_user_data):
        """Test survey creation functionality."""
        request_data = {
            "survey_type": "customer_satisfaction",
            "target_audience": "existing_customers",
            "survey_length": "short",
            "focus_areas": ["product_satisfaction", "support_quality", "feature_requests"]
        }
        
        with patch('backend.agents.joe.app.services.survey_creation_service.SurveyCreationService.create_survey') as mock_create:
            mock_create.return_value = {
                "success": True,
                "survey": {
                    "survey_id": "SURVEY-12345",
                    "questions": [
                        {
                            "question": "How satisfied are you with our product?",
                            "type": "rating",
                            "scale": "1-10"
                        },
                        {
                            "question": "What features would you like to see added?",
                            "type": "open_text"
                        }
                    ],
                    "distribution_methods": ["email", "in_app", "website"],
                    "estimated_completion_time": "5 minutes"
                }
            }
            
            response = await async_client.post(
                "/joe/surveys/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "survey" in data

    @pytest_asyncio.mark.asyncio
    async def test_data_visualization(self, async_client: AsyncClient, mock_user_data):
        """Test data visualization functionality."""
        request_data = {
            "data_type": "market_research",
            "visualization_type": "dashboard",
            "data_points": {
                "market_size": 5000000000,
                "competitors": 15,
                "growth_rate": 0.25
            },
            "chart_types": ["bar", "pie", "line"]
        }
        
        with patch('backend.agents.joe.app.services.data_visualization_service.DataVisualizationService.create_visualization') as mock_create:
            mock_create.return_value = {
                "success": True,
                "visualization": {
                    "dashboard_id": "DASH-12345",
                    "charts": [
                        {
                            "type": "bar",
                            "title": "Market Size by Region",
                            "data": [{"region": "North America", "value": 2000000000}]
                        },
                        {
                            "type": "pie",
                            "title": "Competitor Market Share",
                            "data": [{"competitor": "Zendesk", "share": 0.15}]
                        }
                    ],
                    "export_formats": ["png", "pdf", "svg"]
                }
            }
            
            response = await async_client.post(
                "/joe/visualization/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "visualization" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "research_topic": "AI market analysis",
            "research_scope": {"market_size": True}
        }
        
        response = await async_client.post(
            "/joe/research/market",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "research_topic": "",  # Empty topic
            "research_scope": {}  # Empty scope
        }
        
        response = await async_client.post(
            "/joe/research/market",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "research_topic": "AI market analysis",
            "research_scope": {"market_size": True}
        }
        
        with patch('backend.agents.joe.app.services.market_research_service.MarketResearchService.conduct_research') as mock_research:
            mock_research.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/joe/research/market",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
