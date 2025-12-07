"""
Unit tests for Groq STT Client
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.groq_stt_client import GroqSTTClient


class TestGroqSTTClient:
    """Test suite for Groq STT Client"""
    
    @pytest.fixture
    def client(self):
        """Create a Groq STT client instance"""
        return GroqSTTClient()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, client):
        """Test successful initialization"""
        with patch('backend.core.ai.groq_stt_client.settings') as mock_settings:
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
    async def test_transcribe_audio_success(self, client):
        """Test successful audio transcription"""
        client._health_status = "healthy"
        client.session = AsyncMock()
        
        # Mock transcription response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "text": "This is a test transcription",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "This is a test transcription"}
            ]
        })
        
        client.session.post = AsyncMock(return_value=mock_response)
        client.session.__aenter__ = AsyncMock(return_value=client.session)
        client.session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock rate limiter
        with patch.object(client, '_rate_limiter', None):
            with patch.object(client, '_check_rate_limits', return_value=(True, None, {})):
                audio_data = b"fake_audio_data"
                result = await client.transcribe_audio(
                    audio_data=audio_data,
                    audio_format="mp3",
                    language="en"
                )
                
                assert result["success"] is True
                assert result["text"] == "This is a test transcription"
                assert result["language"] == "en"
                assert len(result["segments"]) > 0
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_rate_limit(self, client):
        """Test rate limit handling"""
        client._health_status = "healthy"
        
        with patch.object(client, '_check_rate_limits', return_value=(False, "Rate limit exceeded", {})):
            result = await client.transcribe_audio(audio_data=b"test")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()
    
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
        client._total_requests = 75
        client._successful_requests = 72
        client._failed_requests = 3
        client._daily_requests = 40
        
        metrics = client.get_metrics()
        
        assert metrics["total_requests"] == 75
        assert metrics["successful_requests"] == 72
        assert metrics["failed_requests"] == 3
        assert metrics["daily_requests"] == 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

