# app/providers/ollama_provider.py
import httpx
import json
from typing import List
from app.providers.base_provider import BaseLLMProvider
from app.models.provider_models import ProviderResponse
import logging

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama Local Provider - matches your existing llama3.2:3b setup"""
    
    def __init__(self, endpoint: str, api_key: str = "", **kwargs):
        super().__init__(endpoint, api_key, **kwargs)
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_response(
        self, 
        message: str, 
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 150,
        **kwargs
    ) -> ProviderResponse:
        """Generate response using Ollama API - compatible with your llama3.2:3b"""
        
        payload = {
            "model": model,
            "prompt": message,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.endpoint}/api/generate", 
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("response", "")
            
            # Ollama doesn't provide token usage, estimate based on content
            estimated_tokens = len(content.split()) * 1.3  # Rough estimation
            
            return ProviderResponse(
                content=content,
                tokens_used=int(estimated_tokens),
                estimated_cost=0.0,  # Local model, no cost
                provider="ollama",
                model=model
            )
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is accessible - matches your current setup"""
        try:
            response = await self.client.get(
                f"{self.endpoint}/api/tags",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available Ollama models - will show your 16 models"""
        try:
            response = await self.client.get(f"{self.endpoint}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []

    def estimate_cost(self, tokens: int, model: str) -> float:
        """Local models have no cost"""
        return 0.0

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
