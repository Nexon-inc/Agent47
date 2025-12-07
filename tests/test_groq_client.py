"""
Unit tests for Groq LLM Client
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.groq_client import GroqLLMClient


class TestGroqLLMClient:
    """Test suite for Groq LLM Client"""
    
    @pytest.fixture
    def client(self):
        """Create a Groq LLM client instance"""
        return GroqLLMClient()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, client):
        """Test successful initialization"""
        with patch('backend.core.ai.groq_client.settings') as mock_settings:
            mock_settings.groq.groq_api_key = "test_key"
            mock_settings.groq.groq_api_base_url = "https://api.groq.com/openai/v1"
            mock_settings.groq.groq_request_timeout = 60
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session.return_value)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
                
                with patch.object(client, 'health_check', return_value={"healthy": True}):
                    result = await client.initialize()
                    assert result is True
                    assert client._health_status == "healthy"
    
    @pytest.mark.asyncio
    async def test_initialize_no_api_key(self, client):
        """Test initialization without API key"""
        with patch('backend.core.ai.groq_client.settings') as mock_settings:
            mock_settings.groq.groq_api_key = ""
            
            with pytest.raises(ValueError, match="Groq API key not configured"):
                await client.initialize()
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, client):
        """Test successful text generation"""
        # Mock initialization
        client._health_status = "healthy"
        client.session = AsyncMock()
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            },
            "model": "llama-3.3-70b-versatile"
        })
        
        client.session.post = AsyncMock(return_value=mock_response)
        client.session.__aenter__ = AsyncMock(return_value=client.session)
        client.session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock rate limiter
        with patch.object(client, '_rate_limiter', None):
            with patch.object(client, '_check_rate_limits', return_value=(True, None, {})):
                result = await client.generate_text(
                    prompt="Test prompt",
                    max_tokens=100
                )
                
                assert result["success"] is True
                assert result["content"] == "Test response"
                assert result["usage"]["total_tokens"] == 30
    
    @pytest.mark.asyncio
    async def test_generate_text_rate_limit(self, client):
        """Test rate limit handling"""
        client._health_status = "healthy"
        
        with patch.object(client, '_check_rate_limits', return_value=(False, "Rate limit exceeded", {})):
            result = await client.generate_text(prompt="Test")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check"""
        client.session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": []})
        
        client.session.get = AsyncMock(return_value=mock_response)
        client.session.__aenter__ = AsyncMock(return_value=client.session)
        client.session.__aexit__ = AsyncMock(return_value=None)
        
        result = await client.health_check()
        assert result["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing the client"""
        client.session = AsyncMock()
        client.session.close = AsyncMock()
        
        await client.close()
        client.session.close.assert_called_once()
    
    def test_get_metrics(self, client):
        """Test getting metrics"""
        client._total_requests = 100
        client._successful_requests = 95
        client._failed_requests = 5
        client._daily_requests = 50
        
        metrics = client.get_metrics()
        
        assert metrics["total_requests"] == 100
        assert metrics["successful_requests"] == 95
        assert metrics["failed_requests"] == 5
        assert metrics["daily_requests"] == 50
        assert metrics["success_rate"] == 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

