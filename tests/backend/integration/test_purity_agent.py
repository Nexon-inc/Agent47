"""
Integration tests for Purity Agent API endpoints
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from backend.agents.purity.app.main import app

@pytest.mark.integration
@pytest.mark.database
class TestPurityAgent:
    """Integration tests for Purity Agent"""

    @pytest_asyncio.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/purity/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "purity" in data["agent"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_generate_business_ideas_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful business idea generation."""
        request_data = {
            "skills": ["programming", "marketing"],
            "passions": ["technology", "sustainability"],
            "available_capital": 10000,
            "industry_preferences": ["tech", "green_energy"],
            "risk_tolerance": "medium"
        }
        
        with patch('backend.agents.purity.app.services.business_idea_generator_service.BusinessIdeaGeneratorService.generate_business_ideas') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "ideas": [
                    {
                        "title": "Eco-Tech Solutions",
                        "description": "Sustainable technology solutions for small businesses",
                        "market_potential": "high",
                        "startup_cost": 8000,
                        "revenue_model": "SaaS"
                    }
                ]
            }
            
            response = await async_client.post(
                "/purity/business-ideas/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "ideas" in data
            assert len(data["ideas"]) > 0

    @pytest_asyncio.mark.asyncio
    async def test_conduct_market_research_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful market research."""
        request_data = {
            "idea_id": 1,
            "research_scope": {
                "market_size": True,
                "competition": True,
                "trends": True
            }
        }
        
        with patch('backend.agents.purity.app.services.market_research_service.MarketResearchService.conduct_market_research') as mock_research:
            mock_research.return_value = {
                "success": True,
                "research_data": {
                    "market_size": 1000000,
                    "competition_level": "medium",
                    "growth_rate": 0.15,
                    "key_trends": ["AI adoption", "Remote work"]
                }
            }
            
            response = await async_client.post(
                "/purity/market-research/conduct",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "research_data" in data

    @pytest_asyncio.mark.asyncio
    async def test_generate_financial_forecast_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful financial forecast generation."""
        request_data = {
            "idea_id": 1,
            "forecast_period": 36,
            "assumptions": {
                "growth_rate": 0.20,
                "profit_margin": 0.30
            }
        }
        
        with patch('backend.agents.purity.app.services.financial_planning_service.FinancialPlanningService.generate_financial_forecast') as mock_forecast:
            mock_forecast.return_value = {
                "success": True,
                "forecast": {
                    "revenue_forecast": {
                        "year_1": 100000,
                        "year_2": 250000,
                        "year_3": 500000
                    },
                    "expense_forecast": {
                        "year_1": 80000,
                        "year_2": 150000,
                        "year_3": 300000
                    },
                    "profit_forecast": {
                        "year_1": 20000,
                        "year_2": 100000,
                        "year_3": 200000
                    }
                }
            }
            
            response = await async_client.post(
                "/purity/financial-planning/forecast",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "forecast" in data

    @pytest_asyncio.mark.asyncio
    async def test_create_brand_identity_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful brand identity creation."""
        request_data = {
            "business_idea_id": 1,
            "brand_name": "EcoTech Solutions",
            "industry": "technology",
            "target_audience": "small_businesses",
            "brand_personality": "innovative",
            "brand_values": ["sustainability", "innovation", "reliability"]
        }
        
        with patch('backend.agents.purity.app.services.brand_building_service.BrandBuildingService.create_brand_identity') as mock_create:
            mock_create.return_value = {
                "success": True,
                "brand_identity": {
                    "brand_name": "EcoTech Solutions",
                    "tagline": "Sustainable Technology for Tomorrow",
                    "color_palette": ["#2E8B57", "#FFFFFF", "#000000"],
                    "typography": "Modern Sans-serif",
                    "brand_voice": "Professional yet approachable"
                }
            }
            
            response = await async_client.post(
                "/purity/brand-building/create-identity",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "brand_identity" in data

    @pytest_asyncio.mark.asyncio
    async def test_generate_investment_pitch_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful investment pitch generation."""
        request_data = {
            "business_idea_id": 1,
            "funding_amount": 500000,
            "equity_offered": 0.20,
            "use_of_funds": ["product_development", "marketing", "hiring"],
            "investor_type": "venture_capital"
        }
        
        with patch('backend.agents.purity.app.services.investment_pitch_service.InvestmentPitchService.create_investment_pitch') as mock_create:
            mock_create.return_value = {
                "success": True,
                "pitch": {
                    "executive_summary": "EcoTech Solutions is revolutionizing sustainable technology...",
                    "market_opportunity": "The green tech market is worth $1.2B and growing...",
                    "business_model": "SaaS subscription with tiered pricing...",
                    "financial_projections": "Projected revenue of $2M by year 3...",
                    "funding_request": "Seeking $500K for 20% equity..."
                }
            }
            
            response = await async_client.post(
                "/purity/investment-pitch/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "pitch" in data

    @pytest_asyncio.mark.asyncio
    async def test_create_launch_strategy_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful launch strategy creation."""
        request_data = {
            "business_idea_id": 1,
            "target_market": "small_businesses",
            "launch_budget": 25000,
            "timeline_months": 6,
            "launch_channels": ["digital_marketing", "partnerships", "events"]
        }
        
        with patch('backend.agents.purity.app.services.launch_strategy_service.LaunchStrategyService.create_launch_strategy') as mock_create:
            mock_create.return_value = {
                "success": True,
                "strategy": {
                    "pre_launch": ["Market validation", "Beta testing", "Brand building"],
                    "launch_phase": ["Product launch", "Marketing campaign", "Sales outreach"],
                    "post_launch": ["Customer feedback", "Product iteration", "Scale operations"],
                    "timeline": "6 months",
                    "budget_allocation": {
                        "marketing": 40,
                        "product": 30,
                        "operations": 30
                    }
                }
            }
            
            response = await async_client.post(
                "/purity/launch-strategy/create",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "strategy" in data

    @pytest_asyncio.mark.asyncio
    async def test_validate_business_opportunity_success(self, async_client: AsyncClient, mock_user_data):
        """Test successful business opportunity validation."""
        request_data = {
            "business_idea": "AI-powered customer service chatbot",
            "target_market": "e-commerce",
            "market_data": {
                "market_size": 5000000,
                "growth_rate": 0.25
            }
        }
        
        with patch('backend.agents.purity.app.services.opportunity_validation_service.OpportunityValidationService.validate_business_opportunity') as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "validation": {
                    "viability_score": 85,
                    "market_potential": "high",
                    "competition_level": "medium",
                    "barriers_to_entry": "low",
                    "recommendations": ["Focus on niche markets", "Build strong partnerships"]
                }
            }
            
            response = await async_client.post(
                "/purity/opportunity-validation/validate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "validation" in data

    @pytest_asyncio.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test unauthorized access to protected endpoints."""
        request_data = {
            "skills": ["programming"],
            "passions": ["technology"],
            "available_capital": 10000
        }
        
        response = await async_client.post(
            "/purity/business-ideas/generate",
            json=request_data
            # No authorization header
        )
        
        assert response.status_code == 401

    @pytest_asyncio.mark.asyncio
    async def test_invalid_request_data(self, async_client: AsyncClient):
        """Test handling of invalid request data."""
        request_data = {
            "skills": [],  # Empty skills list
            "passions": ["technology"],
            "available_capital": -1000  # Negative capital
        }
        
        response = await async_client.post(
            "/purity/business-ideas/generate",
            json=request_data,
            headers={"Authorization": f"Bearer test_token"}
        )
        
        assert response.status_code == 422

    @pytest_asyncio.mark.asyncio
    async def test_service_unavailable(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""
        request_data = {
            "skills": ["programming"],
            "passions": ["technology"],
            "available_capital": 10000
        }
        
        with patch('backend.agents.purity.app.services.business_idea_generator_service.BusinessIdeaGeneratorService.generate_business_ideas') as mock_generate:
            mock_generate.side_effect = Exception("Service unavailable")
            
            response = await async_client.post(
                "/purity/business-ideas/generate",
                json=request_data,
                headers={"Authorization": f"Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data
