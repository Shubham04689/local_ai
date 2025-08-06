import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm_service import LLMService
from app.models.provider_models import ProviderResponse

@pytest.fixture
def llm_service():
    return LLMService()

@pytest.mark.asyncio
async def test_generate_response_success(llm_service):
    with patch.object(llm_service.provider_factory, 'get_provider') as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.generate_response.return_value = ProviderResponse(
            content="Test response",
            tokens_used=50,
            estimated_cost=0.01,
            provider="test",
            model="test-model"
        )
        mock_get_provider.return_value = mock_provider

        result = await llm_service.generate_response("Hello")

        assert result["response"] == "Test response"
        assert result["status"] == "success"
        assert result["tokens_used"] == 50

@pytest.mark.asyncio
async def test_fallback_providers(llm_service):
    with patch.object(llm_service.provider_factory, 'get_provider') as mock_get_provider:
        # First provider fails
        mock_provider1 = AsyncMock()
        mock_provider1.generate_response.side_effect = Exception("Primary failed")

        # Second provider succeeds
        mock_provider2 = AsyncMock()
        mock_provider2.generate_response.return_value = ProviderResponse(
            content="Fallback response",
            tokens_used=30,
            estimated_cost=0.005,
            provider="fallback",
            model="fallback-model"
        )

        mock_get_provider.side_effect = [mock_provider1, mock_provider2]

        result = await llm_service.generate_response("Hello")

        assert result["response"] == "Fallback response"
        assert result["status"] == "success_fallback"
