"""
Unit tests for Groq TTS Client
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.groq_tts_client import GroqTTSClient


class TestGroqTTSClient:
    """Test suite for Groq TTS Client"""
    
    @pytest.fixture
    def client(self):
        """Create a Groq TTS client instance"""
        return GroqTTSClient()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, client):
        """Test successful initialization"""
        with patch('backend.core.ai.groq_tts_client.settings') as mock_settings:
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
    async def test_text_to_speech_success(self, client):
        """Test successful TTS generation"""
        client._health_status = "healthy"
        client.session = AsyncMock()
        
        # Mock audio response
        mock_audio_data = b"fake_audio_data"
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=mock_audio_data)
        
        client.session.post = AsyncMock(return_value=mock_response)
        client.session.__aenter__ = AsyncMock(return_value=client.session)
        client.session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock rate limiter
        with patch.object(client, '_rate_limiter', None):
            with patch.object(client, '_check_rate_limits', return_value=(True, None, {})):
                result = await client.text_to_speech(
                    text="Hello, world!",
                    voice="alloy",
                    language="en"
                )
                
                assert result["success"] is True
                assert result["audio_data"] == mock_audio_data
                assert result["format"] == "mp3"
    
    @pytest.mark.asyncio
    async def test_text_to_speech_rate_limit(self, client):
        """Test rate limit handling"""
        client._health_status = "healthy"
        
        with patch.object(client, '_check_rate_limits', return_value=(False, "Rate limit exceeded", {})):
            result = await client.text_to_speech(text="Test")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_available_voices(self, client):
        """Test getting available voices"""
        voices_en = client.get_available_voices("en")
        assert len(voices_en) > 0
        assert "alloy" in voices_en
        
        voices_ar = client.get_available_voices("ar")
        assert len(voices_ar) > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check"""
        client.session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        
        client.session.get = AsyncMock(return_value=mock_response)
        client.session.__aenter__ = AsyncMock(return_value=client.session)
        client.session.__aexit__ = AsyncMock(return_value=None)
        
        result = await client.health_check()
        assert result["healthy"] is True
    
    def test_get_metrics(self, client):
        """Test getting metrics"""
        client._total_requests = 50
        client._successful_requests = 48
        client._failed_requests = 2
        client._daily_requests = 25
        
        metrics = client.get_metrics()
        
        assert metrics["total_requests"] == 50
        assert metrics["successful_requests"] == 48
        assert metrics["failed_requests"] == 2
        assert metrics["daily_requests"] == 25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

