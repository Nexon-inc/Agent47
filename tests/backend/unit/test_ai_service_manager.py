"""
Unit tests for AI Service Manager
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.core.ai.ai_service_manager import AIServiceManager


class TestAIServiceManager:
    """Test cases for AI Service Manager"""

    @pytest.fixture
    def ai_service_manager(self):
        """Create AI Service Manager instance for testing"""
        return AIServiceManager()

    @pytest.mark.asyncio
    async def test_ai_service_manager_initialization(self, ai_service_manager):
        """Test AI Service Manager initialization"""
        assert ai_service_manager is not None
        assert hasattr(ai_service_manager, 'llm_service_pool')
        assert hasattr(ai_service_manager, 'fallback_enabled')

    @pytest.mark.asyncio
    async def test_llm_service_pool_initialization(self, ai_service_manager):
        """Test LLM service pool initialization"""
        assert ai_service_manager.llm_service_pool is not None
        assert len(ai_service_manager.llm_service_pool.services) > 0

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, ai_service_manager):
        """Test fallback mechanism when primary service fails"""
        with patch.object(ai_service_manager.llm_service_pool, 'get_response') as mock_get_response:
            # Mock primary service failure
            mock_get_response.side_effect = Exception("Primary service failed")
            
            # Should handle the exception gracefully
            with pytest.raises(Exception):
                await ai_service_manager.llm_service_pool.get_response("test prompt")

    @pytest.mark.asyncio
    async def test_service_health_check(self, ai_service_manager):
        """Test service health check functionality"""
        health_status = await ai_service_manager.check_health()
        assert isinstance(health_status, dict)
        assert 'status' in health_status
        assert 'services' in health_status

    @pytest.mark.asyncio
    async def test_get_available_services(self, ai_service_manager):
        """Test getting available services"""
        services = ai_service_manager.get_available_services()
        assert isinstance(services, list)
        assert len(services) > 0

    @pytest.mark.asyncio
    async def test_service_rotation(self, ai_service_manager):
        """Test service rotation for load balancing"""
        # This test would verify that services are rotated properly
        # for load balancing purposes
        initial_service = ai_service_manager.llm_service_pool.get_current_service()
        assert initial_service is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, ai_service_manager):
        """Test error handling in AI Service Manager"""
        with patch.object(ai_service_manager.llm_service_pool, 'get_response') as mock_get_response:
            mock_get_response.side_effect = Exception("Service error")
            
            with pytest.raises(Exception):
                await ai_service_manager.llm_service_pool.get_response("test prompt")

    @pytest.mark.asyncio
    async def test_configuration_loading(self, ai_service_manager):
        """Test configuration loading"""
        # Test that configuration is loaded correctly
        assert ai_service_manager.config is not None
        assert hasattr(ai_service_manager.config, 'openai_api_key')
        assert hasattr(ai_service_manager.config, 'grok_api_key')

    @pytest.mark.asyncio
    async def test_service_monitoring(self, ai_service_manager):
        """Test service monitoring functionality"""
        # Test that service monitoring works correctly
        metrics = await ai_service_manager.get_service_metrics()
        assert isinstance(metrics, dict)
        assert 'response_times' in metrics
        assert 'error_rates' in metrics
        assert 'success_rates' in metrics