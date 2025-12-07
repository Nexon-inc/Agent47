"""
Unit tests for LLM Service Pool
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.llm_service_pool import LLMServicePool
from backend.core.config import settings

@pytest.mark.unit
@pytest.mark.ai
class TestLLMServicePool:
    """Test cases for LLMServicePool"""

    @pytest_asyncio.fixture
    async def llm_service_pool(self):
        """Create LLM service pool instance for testing."""
        pool = LLMServicePool()
        return pool

    @pytest_asyncio.fixture
    async def mock_chutes_client(self):
        """Create mock Chutes LLM client."""
        mock_client = AsyncMock()
        mock_client.initialize = AsyncMock()
        mock_client.generate_text = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=True)
        return mock_client

    @pytest_asyncio.fixture
    async def mock_grok_client(self):
        """Create mock Grok LLM client."""
        mock_client = AsyncMock()
        mock_client.initialize = AsyncMock()
        mock_client.generate_text = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=True)
        return mock_client

    @pytest_asyncio.mark.asyncio
    async def test_initialize_success(self, llm_service_pool, mock_chutes_client, mock_grok_client):
        """Test successful initialization of LLM service pool."""
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client), \
             patch.object(llm_service_pool, 'grok_client', mock_grok_client):
            
            await llm_service_pool.initialize()
            
            mock_chutes_client.initialize.assert_called_once()
            mock_grok_client.initialize.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_initialize_failure(self, llm_service_pool):
        """Test initialization failure handling."""
        with patch.object(llm_service_pool, 'chutes_client') as mock_chutes:
            mock_chutes.initialize.side_effect = Exception("Chutes initialization failed")
            
            with pytest.raises(Exception, match="Chutes initialization failed"):
                await llm_service_pool.initialize()

    @pytest_asyncio.mark.asyncio
    async def test_generate_text_primary_success(self, llm_service_pool, mock_chutes_client):
        """Test successful text generation with primary service."""
        messages = [{"role": "user", "content": "Test message"}]
        expected_response = {
            "success": True,
            "text_content": "Generated response",
            "model_used": "chutes",
            "tokens_used": 50
        }
        
        mock_chutes_client.generate_text.return_value = expected_response
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client), \
             patch.object(llm_service_pool, '_check_chutes_health', return_value=True):
            
            result = await llm_service_pool.generate_text(messages)
            
            assert result == expected_response
            mock_chutes_client.generate_text.assert_called_once_with(messages)

    @pytest_asyncio.mark.asyncio
    async def test_generate_text_fallback_success(self, llm_service_pool, mock_chutes_client, mock_grok_client):
        """Test successful text generation with fallback service."""
        messages = [{"role": "user", "content": "Test message"}]
        chutes_response = {
            "success": False,
            "error": "Rate limit exceeded"
        }
        grok_response = {
            "success": True,
            "text_content": "Generated response from Grok",
            "model_used": "grok",
            "tokens_used": 50
        }
        
        mock_chutes_client.generate_text.return_value = chutes_response
        mock_grok_client.generate_text.return_value = grok_response
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client), \
             patch.object(llm_service_pool, 'grok_client', mock_grok_client), \
             patch.object(llm_service_pool, '_check_chutes_health', return_value=False), \
             patch.object(llm_service_pool, '_check_grok_health', return_value=True):
            
            result = await llm_service_pool.generate_text(messages)
            
            assert result == grok_response
            mock_grok_client.generate_text.assert_called_once_with(messages)

    @pytest_asyncio.mark.asyncio
    async def test_generate_text_both_fail(self, llm_service_pool, mock_chutes_client, mock_grok_client):
        """Test text generation when both services fail."""
        messages = [{"role": "user", "content": "Test message"}]
        chutes_response = {
            "success": False,
            "error": "Rate limit exceeded"
        }
        grok_response = {
            "success": False,
            "error": "Service unavailable"
        }
        
        mock_chutes_client.generate_text.return_value = chutes_response
        mock_grok_client.generate_text.return_value = grok_response
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client), \
             patch.object(llm_service_pool, 'grok_client', mock_grok_client), \
             patch.object(llm_service_pool, '_check_chutes_health', return_value=False), \
             patch.object(llm_service_pool, '_check_grok_health', return_value=False):
            
            result = await llm_service_pool.generate_text(messages)
            
            assert result["success"] is False
            assert "error" in result

    @pytest_asyncio.mark.asyncio
    async def test_health_check_chutes_success(self, llm_service_pool, mock_chutes_client):
        """Test successful Chutes health check."""
        mock_chutes_client.health_check.return_value = True
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client):
            result = await llm_service_pool._check_chutes_health()
            
            assert result is True
            mock_chutes_client.health_check.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_health_check_chutes_failure(self, llm_service_pool, mock_chutes_client):
        """Test Chutes health check failure."""
        mock_chutes_client.health_check.side_effect = Exception("Health check failed")
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client):
            result = await llm_service_pool._check_chutes_health()
            
            assert result is False

    @pytest_asyncio.mark.asyncio
    async def test_health_check_grok_success(self, llm_service_pool, mock_grok_client):
        """Test successful Grok health check."""
        mock_grok_client.health_check.return_value = True
        
        with patch.object(llm_service_pool, 'grok_client', mock_grok_client):
            result = await llm_service_pool._check_grok_health()
            
            assert result is True
            mock_grok_client.health_check.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_health_check_grok_failure(self, llm_service_pool, mock_grok_client):
        """Test Grok health check failure."""
        mock_grok_client.health_check.side_effect = Exception("Health check failed")
        
        with patch.object(llm_service_pool, 'grok_client', mock_grok_client):
            result = await llm_service_pool._check_grok_health()
            
            assert result is False

    @pytest_asyncio.mark.asyncio
    async def test_switch_to_fallback(self, llm_service_pool):
        """Test switching to fallback service."""
        await llm_service_pool._switch_to_fallback()
        
        assert llm_service_pool.is_fallback_active() is True

    @pytest_asyncio.mark.asyncio
    async def test_switch_to_primary(self, llm_service_pool):
        """Test switching to primary service."""
        # First switch to fallback
        await llm_service_pool._switch_to_fallback()
        assert llm_service_pool.is_fallback_active() is True
        
        # Then switch back to primary
        await llm_service_pool._switch_to_primary()
        assert llm_service_pool.is_fallback_active() is False

    @pytest_asyncio.mark.asyncio
    async def test_get_active_service(self, llm_service_pool):
        """Test getting active service name."""
        # Test primary service
        service = await llm_service_pool.get_active_service()
        assert service == "chutes"
        
        # Test fallback service
        await llm_service_pool._switch_to_fallback()
        service = await llm_service_pool.get_active_service()
        assert service == "grok"

    @pytest_asyncio.mark.asyncio
    async def test_get_metrics(self, llm_service_pool, mock_chutes_client, mock_grok_client):
        """Test getting service metrics."""
        mock_chutes_client.get_metrics.return_value = {
            "requests": 50,
            "success_rate": 0.95,
            "avg_response_time": 1.2
        }
        mock_grok_client.get_metrics.return_value = {
            "requests": 10,
            "success_rate": 0.90,
            "avg_response_time": 2.1
        }
        
        with patch.object(llm_service_pool, 'chutes_client', mock_chutes_client), \
             patch.object(llm_service_pool, 'grok_client', mock_grok_client):
            
            metrics = await llm_service_pool.get_metrics()
            
            assert "chutes" in metrics
            assert "grok" in metrics
            assert metrics["chutes"]["requests"] == 50
            assert metrics["grok"]["requests"] == 10

    def test_initialization_state(self, llm_service_pool):
        """Test initial state of LLM service pool."""
        assert llm_service_pool.chutes_client is None
        assert llm_service_pool.grok_client is None
        assert llm_service_pool.is_fallback_active() is False
