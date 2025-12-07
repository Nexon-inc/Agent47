"""
Unit tests for Image Generation Service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.ai.image_generation_service import ImageGenerationService
from backend.core.config import settings

@pytest.mark.unit
@pytest.mark.ai
class TestImageGenerationService:
    """Test cases for ImageGenerationService"""

    @pytest_asyncio.fixture
    async def image_service(self):
        """Create image generation service instance for testing."""
        service = ImageGenerationService()
        return service

    @pytest_asyncio.mark.asyncio
    async def test_initialize_success(self, image_service):
        """Test successful initialization of image generation service."""
        with patch.object(image_service, '_validate_config') as mock_validate:
            mock_validate.return_value = True
            
            await image_service.initialize()
            
            assert image_service._initialized is True
            mock_validate.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_initialize_failure(self, image_service):
        """Test initialization failure handling."""
        with patch.object(image_service, '_validate_config') as mock_validate:
            mock_validate.side_effect = Exception("Configuration validation failed")
            
            with pytest.raises(Exception, match="Configuration validation failed"):
                await image_service.initialize()

    @pytest_asyncio.mark.asyncio
    async def test_generate_image_success(self, image_service):
        """Test successful image generation."""
        prompt = "A beautiful landscape"
        expected_response = {
            "success": True,
            "image_url": "https://example.com/image.jpg",
            "model_used": "juggernautxl",
            "generation_time": 2.5
        }
        
        with patch.object(image_service, '_initialized', True), \
             patch.object(image_service, '_call_chutes_api') as mock_api:
            mock_api.return_value = expected_response
            
            result = await image_service.generate_image(prompt)
            
            assert result == expected_response
            mock_api.assert_called_once_with(prompt)

    @pytest_asyncio.mark.asyncio
    async def test_generate_image_not_initialized(self, image_service):
        """Test image generation when service is not initialized."""
        prompt = "A beautiful landscape"
        
        with patch.object(image_service, '_initialized', False):
            result = await image_service.generate_image(prompt)
            
            assert result["success"] is False
            assert "not initialized" in result["error"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_generate_image_inactive_service(self, image_service):
        """Test image generation when service is inactive."""
        prompt = "A beautiful landscape"
        
        with patch.object(image_service, '_initialized', True), \
             patch.object(image_service, '_active', False):
            result = await image_service.generate_image(prompt)
            
            assert result["success"] is False
            assert "service is inactive" in result["error"].lower()

    @pytest_asyncio.mark.asyncio
    async def test_generate_image_api_failure(self, image_service):
        """Test image generation API failure."""
        prompt = "A beautiful landscape"
        
        with patch.object(image_service, '_initialized', True), \
             patch.object(image_service, '_active', True), \
             patch.object(image_service, '_call_chutes_api') as mock_api:
            mock_api.side_effect = Exception("API call failed")
            
            result = await image_service.generate_image(prompt)
            
            assert result["success"] is False
            assert "API call failed" in result["error"]

    @pytest_asyncio.mark.asyncio
    async def test_health_check_success(self, image_service):
        """Test successful health check."""
        with patch.object(image_service, '_initialized', True), \
             patch.object(image_service, '_call_chutes_api') as mock_api:
            mock_api.return_value = {"success": True}
            
            result = await image_service.health_check()
            
            assert result is True
            mock_api.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_health_check_failure(self, image_service):
        """Test health check failure."""
        with patch.object(image_service, '_initialized', True), \
             patch.object(image_service, '_call_chutes_api') as mock_api:
            mock_api.side_effect = Exception("Health check failed")
            
            result = await image_service.health_check()
            
            assert result is False

    @pytest_asyncio.mark.asyncio
    async def test_health_check_not_initialized(self, image_service):
        """Test health check when service is not initialized."""
        with patch.object(image_service, '_initialized', False):
            result = await image_service.health_check()
            
            assert result is False

    @pytest_asyncio.mark.asyncio
    async def test_set_active_status(self, image_service):
        """Test setting active status."""
        await image_service.set_active_status(True)
        assert image_service._active is True
        
        await image_service.set_active_status(False)
        assert image_service._active is False

    @pytest_asyncio.mark.asyncio
    async def test_close(self, image_service):
        """Test closing the service."""
        with patch.object(image_service, '_initialized', True):
            await image_service.close()
            
            assert image_service._initialized is False
            assert image_service._active is False

    @pytest_asyncio.mark.asyncio
    async def test_validate_config_success(self, image_service):
        """Test successful configuration validation."""
        with patch.object(settings, 'chutes') as mock_chutes:
            mock_chutes.chutes_api_key = "test_key"
            mock_chutes.chutes_api_url = "https://api.chutes.ai"
            mock_chutes.chutes_image_model = "juggernautxl"
            
            result = await image_service._validate_config()
            
            assert result is True

    @pytest_asyncio.mark.asyncio
    async def test_validate_config_missing_api_key(self, image_service):
        """Test configuration validation with missing API key."""
        with patch.object(settings, 'chutes') as mock_chutes:
            mock_chutes.chutes_api_key = None
            mock_chutes.chutes_api_url = "https://api.chutes.ai"
            mock_chutes.chutes_image_model = "juggernautxl"
            
            with pytest.raises(ValueError, match="Chutes API key is required"):
                await image_service._validate_config()

    @pytest_asyncio.mark.asyncio
    async def test_validate_config_missing_api_url(self, image_service):
        """Test configuration validation with missing API URL."""
        with patch.object(settings, 'chutes') as mock_chutes:
            mock_chutes.chutes_api_key = "test_key"
            mock_chutes.chutes_api_url = None
            mock_chutes.chutes_image_model = "juggernautxl"
            
            with pytest.raises(ValueError, match="Chutes API URL is required"):
                await image_service._validate_config()

    @pytest_asyncio.mark.asyncio
    async def test_validate_config_missing_model(self, image_service):
        """Test configuration validation with missing model."""
        with patch.object(settings, 'chutes') as mock_chutes:
            mock_chutes.chutes_api_key = "test_key"
            mock_chutes.chutes_api_url = "https://api.chutes.ai"
            mock_chutes.chutes_image_model = None
            
            with pytest.raises(ValueError, match="Chutes image model is required"):
                await image_service._validate_config()

    @pytest_asyncio.mark.asyncio
    async def test_call_chutes_api_success(self, image_service):
        """Test successful Chutes API call."""
        prompt = "A beautiful landscape"
        expected_response = {
            "success": True,
            "image_url": "https://example.com/image.jpg",
            "model_used": "juggernautxl"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await image_service._call_chutes_api(prompt)
            
            assert result == expected_response
            mock_post.assert_called_once()

    @pytest_asyncio.mark.asyncio
    async def test_call_chutes_api_failure(self, image_service):
        """Test Chutes API call failure."""
        prompt = "A beautiful landscape"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            result = await image_service._call_chutes_api(prompt)
            
            assert result["success"] is False
            assert "Network error" in result["error"]

    def test_initialization_state(self, image_service):
        """Test initial state of image generation service."""
        assert image_service._initialized is False
        assert image_service._active is True
