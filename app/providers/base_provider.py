from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.models.provider_models import ProviderResponse

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, endpoint: str, api_key: str, **kwargs):
        self.endpoint = endpoint
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate_response(self, message: str, model: str, temperature: float = 0.7, max_tokens: int = 150, **kwargs) -> ProviderResponse:
        """Generate a response from the LLM"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is accessible"""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass

    @abstractmethod
    def estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost for token usage"""
        pass
